"""Turn GitHub webhook payloads into one normalised pull request event.

Reads only the payload it is given. Fields a webhook does not carry (the
changed files, whether an approval is the first) come from elsewhere: a diff,
or a caller-supplied approval count.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

EventKind = Literal["opened", "updated", "merge", "first_approval"]
SUPPORTED_EVENTS = ("pull_request", "pull_request_review")


class EventError(Exception):
    """Raised when a payload is not a usable pull request event."""


class PrEvent(BaseModel):
    github_event: str
    action: str
    kind: EventKind | None = None
    # Why the event does not start work, when kind is None.
    ignored_reason: str | None = None
    repo: str
    owner: str
    topics: list[str] = Field(default_factory=list)
    number: int
    title: str = ""
    author: str = ""
    draft: bool = False
    merged: bool = False
    base_branch: str
    head_branch: str
    base_sha: str = ""
    head_sha: str = ""
    prior_approvals: int | None = None


def _get(data: Any, *keys: str, default: Any = None) -> Any:
    for key in keys:
        if not isinstance(data, dict):
            return default
        data = data.get(key)
    return default if data is None else data


def _classify(github_event: str, payload: dict, prior_approvals: int | None) -> tuple[EventKind | None, str | None]:
    action = payload.get("action")
    pr = payload["pull_request"]
    if github_event == "pull_request":
        if action in ("opened", "reopened", "ready_for_review"):
            return "opened", None
        if action == "synchronize":
            return "updated", None
        if action == "closed":
            if pr.get("merged") is True:
                return "merge", None
            return None, "closed without merging"
        return None, f"pull_request action {action!r} does not start work"
    # pull_request_review
    state = str(_get(payload, "review", "state", default="")).lower()
    if action != "submitted" or state != "approved":
        return None, f"review {action!r} with state {state!r} is not an approval"
    if prior_approvals is None:
        return None, "cannot confirm this is the first approval without a GitHub lookup"
    if prior_approvals > 0:
        return None, f"not the first approval ({prior_approvals} earlier)"
    return "first_approval", None


def parse_event(github_event: str, payload: Any, *, prior_approvals: int | None = None) -> PrEvent:
    """Normalise a `pull_request` or `pull_request_review` webhook payload."""
    if github_event not in SUPPORTED_EVENTS:
        raise EventError(f"unsupported GitHub event {github_event!r}; expected one of {', '.join(SUPPORTED_EVENTS)}")
    if not isinstance(payload, dict) or not isinstance(payload.get("pull_request"), dict):
        raise EventError("payload has no pull_request object")
    if prior_approvals is not None and prior_approvals < 0:
        raise EventError("prior approvals cannot be negative")
    repo = _get(payload, "repository", "full_name")
    number = _get(payload, "pull_request", "number")
    base = _get(payload, "pull_request", "base", "ref")
    head = _get(payload, "pull_request", "head", "ref")
    missing = [name for name, value in (("repository.full_name", repo), ("pull_request.number", number),
                                        ("pull_request.base.ref", base), ("pull_request.head.ref", head))
               if value in (None, "")]
    if missing:
        raise EventError(f"payload is missing {', '.join(missing)}")
    if not isinstance(repo, str) or "/" not in repo or not isinstance(number, int):
        raise EventError("payload has an invalid repository name or pull request number")

    kind, reason = _classify(github_event, payload, prior_approvals)
    pr = payload["pull_request"]
    topics = _get(payload, "repository", "topics", default=[])
    return PrEvent(
        github_event=github_event,
        action=str(payload.get("action", "")),
        kind=kind,
        ignored_reason=reason,
        repo=repo,
        owner=str(_get(payload, "repository", "owner", "login", default=repo.split("/", 1)[0])),
        topics=[t for t in topics if isinstance(t, str)] if isinstance(topics, list) else [],
        number=number,
        title=str(pr.get("title") or ""),
        author=str(_get(pr, "user", "login", default="")),
        draft=pr.get("draft") is True,
        merged=pr.get("merged") is True,
        base_branch=str(base),
        head_branch=str(head),
        base_sha=str(_get(pr, "base", "sha", default="")),
        head_sha=str(_get(pr, "head", "sha", default="")),
        prior_approvals=prior_approvals,
    )
