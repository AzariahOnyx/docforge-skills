"""Read Jira webhook deliveries: signature, status moves and comments that mention the bot.

Jira signs a delivery with HMAC-SHA256 of the exact body, sent as
`X-Hub-Signature: sha256=<hex>`; the secret itself never travels. A delivery is
verified before it is parsed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import hmac
import json
import re

ISSUE_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,31}-[1-9][0-9]{0,9}$")
WIKI_MENTION = re.compile(r"\[~accountid:([^\]]+)\]")
MAX_BODY_BYTES = 1024 * 1024


class EventError(Exception):
    """Raised when a delivery cannot be read."""


def verify_signature(secret: str, body: bytes, header: str | None) -> bool:
    if not secret or not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header[len("sha256="):].strip().lower())


def sign(secret: str, body: bytes) -> str:
    """The header value Jira would send; used by tests and for replaying recorded deliveries."""
    return "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


@dataclass
class Attachment:
    id: str
    filename: str
    size: int
    mime_type: str


@dataclass
class TicketEvent:
    delivery_id: str
    kind: str  # status, comment, other
    issue_key: str
    project: str
    summary: str
    work_type: str
    status: str  # the ticket's status as the payload reports it
    status_from: str | None = None
    status_to: str | None = None
    owners: list[str] = field(default_factory=list)  # reporter, creator, assignee account IDs
    labels: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)
    attachments: list[Attachment] = field(default_factory=list)
    comment_author: str | None = None
    comment_mentions: list[str] = field(default_factory=list)
    comment_text: str = ""  # the comment as prose, one line per paragraph, without mentions
    comment_id: str | None = None
    comment_created: str | None = None


def _name(value) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("value") or "")
    return str(value or "")


def _account(value) -> str | None:
    return value.get("accountId") if isinstance(value, dict) and value.get("accountId") else None


def _adf_text(node, mentions: list[str]) -> str:
    """Flatten an ADF comment body to prose; mentions are collected, not included."""
    if isinstance(node, list):
        return "".join(_adf_text(n, mentions) for n in node)
    if not isinstance(node, dict):
        return ""
    kind = node.get("type")
    if kind == "mention":
        account = (node.get("attrs") or {}).get("id")
        if account:
            mentions.append(account)
        return ""
    if kind == "text":
        return node.get("text", "")
    if kind == "hardBreak":
        return "\n"
    inner = _adf_text(node.get("content", []), mentions)
    return inner + ("\n" if kind in ("paragraph", "heading", "listItem") else "")


def comment_body(body) -> tuple[str, list[str]]:
    """(prose, mentioned account IDs) for an ADF (v3) or wiki-markup (v2) comment body."""
    mentions: list[str] = []
    if isinstance(body, str):
        mentions = WIKI_MENTION.findall(body)
        text = WIKI_MENTION.sub("", body)
    else:
        text = _adf_text(body, mentions)
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line), list(dict.fromkeys(mentions))


def parse(body: bytes, delivery_id: str | None = None) -> TicketEvent:
    if len(body) > MAX_BODY_BYTES:
        raise EventError("delivery is larger than 1 MB")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise EventError("delivery is not JSON") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("issue"), dict):
        raise EventError("delivery has no issue")
    issue = payload["issue"]
    key = str(issue.get("key") or "")
    if not ISSUE_KEY_RE.match(key):
        raise EventError(f"not a Jira issue key: {key!r}")
    fields = issue.get("fields") or {}
    owners = [a for a in (_account(fields.get("reporter")), _account(fields.get("creator")),
                          _account(fields.get("assignee"))) if a]
    attachments = [Attachment(str(a.get("id", "")), str(a.get("filename", "")), int(a.get("size") or 0),
                              str(a.get("mimeType", ""))) for a in fields.get("attachment") or [] if isinstance(a, dict)]
    event = TicketEvent(
        delivery_id=delivery_id or hashlib.sha256(body).hexdigest()[:32],
        kind="other", issue_key=key, project=key.split("-", 1)[0], summary=str(fields.get("summary") or ""),
        work_type=_name(fields.get("issuetype")), status=_name(fields.get("status")),
        owners=list(dict.fromkeys(owners)), labels=[str(l) for l in fields.get("labels") or []],
        components=[_name(c) for c in fields.get("components") or []], attachments=attachments,
    )
    webhook = str(payload.get("webhookEvent") or "")
    if webhook == "comment_created" and isinstance(payload.get("comment"), dict):
        comment = payload["comment"]
        event.kind = "comment"
        event.comment_author = _account(comment.get("author"))
        event.comment_id = str(comment["id"]) if comment.get("id") is not None else None
        event.comment_created = str(comment["created"]) if comment.get("created") else None
        event.comment_text, event.comment_mentions = comment_body(comment.get("body"))
    elif webhook == "jira:issue_updated":
        for item in (payload.get("changelog") or {}).get("items") or []:
            if isinstance(item, dict) and item.get("field") == "status":
                event.kind = "status"
                event.status_from = item.get("fromString")
                event.status_to = item.get("toString")
    return event
