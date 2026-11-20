"""Read GitHub webhooks about DocForge's own docs pull requests.

Handled: a review that requests changes or mentions DocForge, a comment on a line, a comment on the pull
request that mentions DocForge, and the pull request being merged or closed. Everything else, including
edits and deletions, is ignored. Who may ask for changes is decided later, from `author_association`.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

DOCS_EVENTS = ("pull_request", "pull_request_review", "pull_request_review_comment", "issue_comment")
MAX_TEXT = 4000


@dataclass
class DocsPrEvent:
    github_event: str
    kind: str  # review, line_comment, comment, merged, closed, pushed, ignore
    repo: str
    number: int
    branch: str | None = None  # absent on issue_comment payloads
    author: str = ""
    author_type: str = ""  # User or Bot
    association: str = ""
    body: str = ""
    review_id: int | None = None
    review_state: str = ""  # changes_requested, commented, approved
    comment_id: int | None = None
    path: str | None = None
    line: int | None = None
    created: str | None = None
    commit: str | None = None  # the commit a review was made on, or the head of a closed pull request
    reason: str = ""


def _get(data, *keys, default=None):
    for key in keys:
        if not isinstance(data, dict):
            return default
        data = data.get(key)
    return default if data is None else data


def mentions(text: str, login: str | None) -> bool:
    return bool(login) and re.search(rf"(?<![\w/-])@{re.escape(login)}\b", text, re.I) is not None


def strip_mention(text: str, login: str | None) -> str:
    if login:
        text = re.sub(rf"(?<![\w/-])@{re.escape(login)}\b[,:]?", "", text, flags=re.I)
    return "\n".join(line.strip() for line in text.strip().splitlines()).strip()


def parse_docs_event(github_event: str, payload) -> DocsPrEvent | None:
    """A DocsPrEvent for a pull request event, or None when the payload is not about a pull request."""
    if github_event not in DOCS_EVENTS or not isinstance(payload, dict):
        return None
    repo = _get(payload, "repository", "full_name")
    action = str(payload.get("action") or "")
    if github_event == "issue_comment":
        issue = payload.get("issue")
        if not isinstance(issue, dict) or not issue.get("pull_request"):
            return None  # a comment on an ordinary issue
        number, branch = issue.get("number"), None
    else:
        pr = payload.get("pull_request")
        if not isinstance(pr, dict):
            return None
        number, branch = pr.get("number"), _get(pr, "head", "ref")
    if not isinstance(repo, str) or "/" not in repo or not isinstance(number, int):
        return None
    event = DocsPrEvent(github_event, "ignore", repo, number, branch if isinstance(branch, str) else None)

    if github_event == "pull_request":
        sha = _get(payload, "pull_request", "head", "sha")
        event.commit = sha if isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{40}", sha) else None
        event.author = str(_get(payload, "sender", "login", default=""))
        if action == "closed":
            event.kind = "merged" if _get(payload, "pull_request", "merged") is True else "closed"
        elif action == "synchronize":
            event.kind = "pushed"  # new commits on the pull request's branch
        else:
            event.reason = f"pull_request {action!r} needs nothing from DocForge"
        return event

    item = payload.get("review") if github_event == "pull_request_review" else payload.get("comment")
    if not isinstance(item, dict):
        event.reason = "payload has no review or comment"
        return event
    wanted = "submitted" if github_event == "pull_request_review" else "created"
    if action != wanted:
        event.reason = f"{github_event} {action!r} is not handled (edits and deletions are ignored)"
        return event
    event.author = str(_get(item, "user", "login", default=""))
    event.author_type = str(_get(item, "user", "type", default=""))
    event.association = str(item.get("author_association") or "")
    event.body = str(item.get("body") or "")[:MAX_TEXT]
    event.created = item.get("submitted_at") or item.get("created_at")
    if github_event == "pull_request_review":
        event.kind = "review"
        event.review_id = item.get("id") if isinstance(item.get("id"), int) else None
        event.review_state = str(item.get("state") or "").lower()
        sha = item.get("commit_id")
        event.commit = sha if isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{40}", sha) else None
    elif github_event == "pull_request_review_comment":
        event.kind = "line_comment"
        event.comment_id = item.get("id") if isinstance(item.get("id"), int) else None
        event.review_id = item.get("pull_request_review_id") if isinstance(item.get("pull_request_review_id"), int) else None
        event.path = item.get("path") if isinstance(item.get("path"), str) else None
        line = item.get("line") or item.get("original_line")
        event.line = line if isinstance(line, int) and line > 0 else None
    else:
        event.kind = "comment"
        event.comment_id = item.get("id") if isinstance(item.get("id"), int) else None
    return event
