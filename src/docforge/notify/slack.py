"""Slack notifications for suggestions: dry run by default.

The message holds only the suggestion's title, event, repository, branch,
status, an optional PR link and the number of open questions. It never
includes source (PRD, Jira or Confluence) text.

Sending needs all of: `--send`, a policy whose notification block sets
`slack_channel` and `slack_webhook_env`, and that environment variable holding
an incoming-webhook URL. The URL is a secret: it is never printed, logged or
included in errors. Every attempt (dry run or sent) is appended to
`<run>/notify/slack.jsonl`.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from docforge.config import LOOPBACK_HOSTS, DocForgeConfig
from docforge.publish.pr_body import QUESTION_HEADING, default_title

EVENTS = {"prepared": "Docs suggestion prepared", "revised": "Docs suggestion revised",
          "closed": "Docs suggestion closed", "ready": "Docs suggestion ready for review"}
PR_URL_RE = re.compile(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/pull/[1-9][0-9]*$")
TIMEOUT_SECONDS = 15
LOG = Path("notify") / "slack.jsonl"


class NotifyError(Exception):
    """Raised when a notification cannot be built or sent. Never contains the webhook URL."""


@dataclass
class Outcome:
    text: str
    sent: bool
    channel: str | None
    reason: str


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def open_questions(run: Path) -> int:
    register = run / "analysis" / "clarifications-and-assumptions.md"
    count = len(QUESTION_HEADING.findall(register.read_text(encoding="utf-8"))) if register.is_file() else 0
    cross = run / "analysis" / "cross-source.json"
    if cross.is_file():
        try:
            count += sum(1 for r in json.loads(cross.read_text(encoding="utf-8")) if r.get("question_id"))
        except (ValueError, AttributeError):
            pass
    return count


def build_message(run: Path, event: str, *, pr_url: str | None = None) -> str:
    if event not in EVENTS:
        raise NotifyError(f"event must be one of: {', '.join(EVENTS)}")
    if pr_url is not None and not PR_URL_RE.match(pr_url):
        raise NotifyError("--pr-url must be a GitHub pull request URL")
    plan_path = run / "publish" / "pr.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8")) if plan_path.is_file() else {}
    title = plan.get("title") or default_title(run)
    lines = [f"*{EVENTS[event]}:* {_escape(title)}"]
    if plan:
        lines.append(f"Docs repo `{_escape(plan.get('repo', '?'))}`, branch `{_escape(plan.get('branch', '?'))}`, "
                     f"status {_escape(plan.get('status', 'open'))}, revision {plan.get('revision', 0)}.")
    else:
        lines.append("Not prepared for publishing yet.")
    lines.append(f"Open questions: {open_questions(run)}. Run: `{_escape(run.name)}`.")
    if pr_url:
        lines.append(f"<{pr_url}|Open the pull request>")
    lines.append("A person must review and approve this suggestion.")
    return "\n".join(lines)


def _policy(run: Path, config: DocForgeConfig, trigger: str | None) -> dict:
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    collection = (manifest.get("publish") or {}).get("collection")
    return config.resolve_policy(trigger=trigger, doc_collection=collection)["notification"]


def _webhook(env_name: str) -> str:
    url = os.environ.get(env_name, "").strip()
    if not url:
        raise NotifyError(f"environment variable {env_name} is not set")
    parts = urlsplit(url)
    slack = parts.scheme == "https" and parts.hostname == "hooks.slack.com"
    local = parts.scheme in ("http", "https") and parts.hostname in LOOPBACK_HOSTS
    if not (slack or local) or parts.username or parts.password:
        raise NotifyError(f"{env_name} must hold a https://hooks.slack.com/ incoming-webhook URL")
    return url


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise NotifyError("the webhook answered with a redirect; refused")


def _post(url: str, text: str) -> None:
    request = Request(url, method="POST", data=json.dumps({"text": text}).encode("utf-8"),
                      headers={"Content-Type": "application/json", "User-Agent": "docforge-notify"})
    try:
        with build_opener(_NoRedirects()).open(request, timeout=TIMEOUT_SECONDS) as response:
            response.read(4096)
    except NotifyError:
        raise
    except HTTPError as exc:
        raise NotifyError(f"Slack returned HTTP {exc.code}") from None
    except (URLError, OSError) as exc:
        raise NotifyError(f"could not reach Slack: {type(getattr(exc, 'reason', exc)).__name__}") from None


def _log(run: Path, entry: dict) -> None:
    path = run / LOG
    path.parent.mkdir(exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def notify(run: Path, event: str, *, config: DocForgeConfig | None, trigger: str | None = None,
           pr_url: str | None = None, send: bool = False) -> Outcome:
    from docforge.sources.provenance import now

    if not (run / "run.json").is_file():
        raise NotifyError(f"not a run folder: {run}")
    text = build_message(run, event, pr_url=pr_url)
    policy = _policy(run, config, trigger) if config else {"slack_channel": None, "slack_webhook_env": None}
    channel, env_name = policy.get("slack_channel"), policy.get("slack_webhook_env")
    if not send:
        reason = "dry run (add --send to post)"
    elif config is None:
        reason = "not sent: no docforge.yaml given"
    elif not channel or not env_name:
        reason = "not sent: the policy for this run sets no slack_channel and slack_webhook_env"
    else:
        _post(_webhook(env_name), text)
        _log(run, {"at": now(), "event": event, "sent": True, "channel": channel})
        return Outcome(text, True, channel, f"sent to {channel}")
    _log(run, {"at": now(), "event": event, "sent": False, "channel": channel, "reason": reason})
    return Outcome(text, False, channel, reason)
