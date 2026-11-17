"""Review actions on a suggestion, stored as structured feedback.

Every action appends one JSON line to review/feedback.jsonl (never rewritten)
and updates the suggestion's status in publish/pr.json:

    open -> changes_requested -> revised -> ... -> closed

Closing needs one of six fixed reasons, so feedback can later be counted and
learned from. Actions only write local files; the matching `gh` command is
returned for a person to run.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import uuid

from pydantic import BaseModel, Field

from docforge.publish import PrPlan, PublishError, load_plan, save_plan

FEEDBACK = Path("review") / "feedback.jsonl"

CLOSE_REASONS: dict[str, str] = {
    "inaccurate": "States behavior the product does not have",
    "not_needed": "The change does not need documentation",
    "already_documented": "Existing documentation already covers it",
    "wrong_place": "Right content, wrong page or docs repository",
    "quality": "Does not meet the style or quality bar",
    "source_changed": "The product change was reworked or abandoned",
}
MAX_TEXT = 4000


class ReviewError(Exception):
    """Raised when a review action is not allowed."""


class Feedback(BaseModel):
    feedback_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    at: str = Field(default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat())
    run: str
    action: str  # request_changes, close
    reviewer: str
    comment: str = ""
    reason: str | None = None
    page: str | None = None
    line: int | None = None
    commit: str
    revision: int


def _clean(text: str, field: str, *, required: bool) -> str:
    text = (text or "").strip()
    if required and not text:
        raise ReviewError(f"{field} is required")
    if len(text) > MAX_TEXT:
        raise ReviewError(f"{field} is longer than {MAX_TEXT} characters")
    return text


def load_feedback(run: Path) -> list[Feedback]:
    path = run / FEEDBACK
    if not path.is_file():
        return []
    return [Feedback.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _append(run: Path, feedback: Feedback) -> None:
    path = run / FEEDBACK
    path.parent.mkdir(exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(feedback.model_dump_json() + "\n")


def _plan(run: Path) -> PrPlan:
    try:
        plan = load_plan(run)
    except PublishError as exc:
        raise ReviewError(str(exc)) from None
    if plan.status == "closed":
        raise ReviewError("this suggestion is already closed")
    return plan


def request_changes(run: Path, *, comment: str, reviewer: str, page: str | None = None,
                    line: int | None = None) -> tuple[Feedback, Path, list[str]]:
    """Record a change request and write the revision work order. Returns (feedback, work order, commands)."""
    from .revise import write_revision_order

    plan = _plan(run)
    comment = _clean(comment, "comment", required=True)
    reviewer = _clean(reviewer, "reviewer", required=True)
    pages = {p["dest"] for p in plan.placements} | {p["src"] for p in plan.placements}
    if page is not None:
        page = page.strip() or None
    if page is not None and page not in pages:
        raise ReviewError(f"{page} is not one of this suggestion's pages")
    if line is not None and line < 1:
        raise ReviewError("line must be 1 or more")
    feedback = Feedback(run=run.name, action="request_changes", reviewer=reviewer, comment=comment, page=page,
                        line=line, commit=plan.commit, revision=plan.revision)
    _append(run, feedback)
    plan.status = "changes_requested"
    plan.history.append({"at": feedback.at, "event": "changes_requested", "feedback_id": feedback.feedback_id})
    save_plan(run, plan)
    order = write_revision_order(run, plan, load_feedback(run))
    commands = [shlex.join(["gh", "pr", "comment", plan.branch, "--repo", plan.repo, "--body",
                            f"Changes requested ({reviewer}): {comment}"])]
    return feedback, order, commands


def close_suggestion(run: Path, *, reason: str, note: str, reviewer: str) -> tuple[Feedback, list[str]]:
    plan = _plan(run)
    if reason not in CLOSE_REASONS:
        raise ReviewError(f"reason must be one of: {', '.join(CLOSE_REASONS)}")
    note = _clean(note, "note", required=False)
    reviewer = _clean(reviewer, "reviewer", required=True)
    feedback = Feedback(run=run.name, action="close", reviewer=reviewer, comment=note, reason=reason,
                        commit=plan.commit, revision=plan.revision)
    _append(run, feedback)
    plan.status = "closed"
    plan.history.append({"at": feedback.at, "event": "closed", "reason": reason, "feedback_id": feedback.feedback_id})
    save_plan(run, plan)
    message = f"Closed: {reason} ({CLOSE_REASONS[reason]})." + (f" {note}" if note else "")
    return feedback, [shlex.join(["gh", "pr", "close", plan.branch, "--repo", plan.repo, "--comment", message])]


def suggestions(root: Path) -> list[tuple[Path, PrPlan]]:
    """Run folders under `root` (or `root` itself) that have publish/pr.json."""
    found = []
    candidates = [root] + sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []
    for run in candidates:
        if (run / "publish" / "pr.json").is_file():
            try:
                found.append((run, load_plan(run)))
            except (PublishError, ValueError):
                continue
    return found


def feedback_summary(root: Path) -> dict[str, int]:
    """Count close reasons across runs, for later rule learning."""
    counts = {reason: 0 for reason in CLOSE_REASONS}
    for run, _ in suggestions(root):
        for item in load_feedback(run):
            if item.action == "close" and item.reason in counts:
                counts[item.reason] += 1
    return counts


def dump_feedback(run: Path) -> str:
    return json.dumps([f.model_dump() for f in load_feedback(run)], indent=2)
