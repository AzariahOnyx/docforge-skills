"""Per-ticket state: one JSON file per issue key, written atomically.

The state records where a ticket is (phase), its run and revisions, the
deliveries already handled (so a repeated webhook does nothing), work waiting to
run, and an outbox of every comment and ticket move DocForge made or would have
made.
"""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import tempfile
from typing import Literal

from pydantic import BaseModel, Field

from .events import ISSUE_KEY_RE

Phase = Literal["new", "planning", "planned", "drafting", "drafted", "failed"]
MAX_PROCESSED = 500


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class OutboxEntry(BaseModel):
    at: str
    kind: Literal["comment", "transition"]
    message: str  # comment kind (for example plan, bounce_no_attachments) or the target status
    body: dict | None = None  # the comment (Atlassian Document Format)
    sent: bool = False
    note: str = ""  # why it was not sent, or the error


class Pending(BaseModel):
    action: Literal["plan", "draft", "revise", "ship"]
    at: str
    feedback: str = ""
    by: str | None = None
    answers: dict[int, str] = Field(default_factory=dict)  # question number -> the owner's answer
    comment_id: str | None = None
    comment_created: str | None = None


class TicketState(BaseModel):
    key: str
    trigger: str
    mode: Literal["net_new", "enhancement"]
    phase: Phase = "new"
    run: str | None = None
    revision: int = 0
    product: str | None = None
    notes: list[str] = Field(default_factory=list)  # about the ticket's sources, repeated in the plan comment
    answered: dict[str, str] = Field(default_factory=dict)  # question label (Q03) -> answer source ID (A1)
    pull_request: str | None = None  # the docs pull request's link, once opened
    shipped: bool = False
    pending: Pending | None = None
    processed: list[str] = Field(default_factory=list)
    outbox: list[OutboxEntry] = Field(default_factory=list)
    history: list[dict] = Field(default_factory=list)

    def note(self, event: str, **detail) -> None:
        self.history.append({"at": now(), "event": event, **{k: v for k, v in detail.items() if v not in (None, "")}})


class StateError(Exception):
    """Raised when a ticket's state cannot be read or written."""


def _path(root: Path, key: str) -> Path:
    if not ISSUE_KEY_RE.match(key):
        raise StateError(f"not a Jira issue key: {key!r}")
    return root / f"{key}.json"


def load_state(root: Path, key: str) -> TicketState | None:
    path = _path(root, key)
    if not path.is_file():
        return None
    try:
        return TicketState.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise StateError(f"cannot read {path}: {exc}") from None


def save_state(root: Path, state: TicketState) -> Path:
    path = _path(root, state.key)
    root.mkdir(parents=True, exist_ok=True)
    state.processed = state.processed[-MAX_PROCESSED:]
    fd, tmp = tempfile.mkstemp(dir=root, prefix=f".{state.key}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(state.model_dump_json(indent=2) + "\n")
        os.replace(tmp, path)
    except OSError as exc:
        Path(tmp).unlink(missing_ok=True)
        raise StateError(f"cannot write {path}: {exc}") from None
    return path
