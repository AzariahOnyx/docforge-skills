"""The "docs needed?" decision and its research trail.

Every event produces a decision record, including when the answer is no, and
the record lists each read step taken to reach it. Triggers decide which
events are looked at; for a triggered pull request (or any pull request in a
mapped repo when no github_pr trigger is configured), the triage decides the
outcome: quiet, act, or act but a person confirms (see docforge.triage).
`docs_needed` stays for older readers: act and confirm are "needs_research".
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Literal
import uuid

from pydantic import BaseModel, Field

from docforge.config import DocForgeConfig, GithubPrTrigger
from docforge.sources import ChangedFile, PrEvent
from docforge.triggers import TriggerCheck, check_trigger

DocsNeeded = Literal["needs_research", "no"]
DEFAULT_LOG = Path(".docforge") / "decisions.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class ResearchStep(BaseModel):
    step: str
    at: str = Field(default_factory=_now)
    detail: dict[str, Any] = Field(default_factory=dict)


class DocsDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    decided_at: str = Field(default_factory=_now)
    docs_needed: DocsNeeded
    summary: str
    outcome: Literal["quiet", "act", "confirm"] | None = None
    category: str | None = None
    reasons: list[str] = Field(default_factory=list)
    triage: dict[str, Any] | None = None
    feedback: dict[str, Any] | None = None  # the advisory status and comment posted (or why not)
    event: dict[str, Any]
    triggers: list[TriggerCheck]
    changed_files: list[str] | None
    research_trail: list[ResearchStep]


def decide(
    config: DocForgeConfig,
    event: PrEvent,
    changed: list[ChangedFile] | None,
    *,
    diff_source: str | None = None,
    diff_error: str | None = None,
    diff_text: str = "",
    ledger: Path | None = None,
    config_path: Path | None = None,
    client=None,
) -> DocsDecision:
    trail = [ResearchStep(step="read_event", detail={
        "github_event": event.github_event, "action": event.action, "kind": event.kind,
        "ignored_reason": event.ignored_reason, "repo": event.repo, "number": event.number,
        "draft": event.draft, "base_branch": event.base_branch, "head_branch": event.head_branch,
    })]
    if changed is None:
        note = f"diff could not be read: {diff_error}" if diff_error else "no diff supplied"
        trail.append(ResearchStep(step="read_diff", detail={"source": diff_source, "note": note}))
    else:
        trail.append(ResearchStep(step="read_diff", detail={
            "source": diff_source, "files": len(changed),
            "additions": sum(f.additions for f in changed), "deletions": sum(f.deletions for f in changed),
        }))

    checks: list[TriggerCheck] = []
    for name, trigger in config.triggers.items():
        if isinstance(trigger, GithubPrTrigger):
            check = check_trigger(name, trigger, event, changed)
            checks.append(check)
            trail.append(ResearchStep(step="check_trigger", detail=check.model_dump()))

    triggered = [c.trigger for c in checks if c.outcome == "triggered"]
    if triggered:
        needed: DocsNeeded = "needs_research"
        summary = f"matched trigger(s) {', '.join(triggered)}; research the change before drafting"
    elif not checks:
        needed, summary = "no", "no github_pr triggers are configured"
    else:
        needed = "no"
        summary = "; ".join(f"{c.trigger}: {c.outcome} ({c.reasons[0]})" for c in checks)

    outcome = category = triaged = None
    reasons: list[str] = []
    mapped = any(name.casefold() == event.repo.casefold() for name in config.code_repos)
    if event.kind in ("opened", "updated") and (triggered or (not checks and mapped)):
        from docforge.triage import triage

        result = triage(config, event, changed, diff_text=diff_text, config_path=config_path, client=client,
                        ledger=ledger or DEFAULT_LOG.with_name("triage-costs.jsonl"))
        trail.append(ResearchStep(step="triage", detail={"layer": result.layer, "outcome": result.outcome,
                                                         "category": result.category}))
        outcome, category, reasons, triaged = result.outcome, result.category, result.reasons, result.to_dict()
        needed = "no" if outcome == "quiet" else "needs_research"
        summary = f"{outcome}: " + "; ".join(reasons)
    elif needed == "no":
        outcome, reasons = "quiet", [summary]

    return DocsDecision(
        docs_needed=needed,
        summary=summary,
        outcome=outcome,
        category=category,
        reasons=reasons,
        triage=triaged,
        event={"repo": event.repo, "number": event.number, "github_event": event.github_event,
               "action": event.action, "kind": event.kind, "head_sha": event.head_sha, "title": event.title},
        triggers=checks,
        changed_files=None if changed is None else [f.path for f in changed],
        research_trail=trail,
    )


def append_decision(log: Path, decision: DocsDecision) -> None:
    """Append one decision as a JSON line. Never rewrites earlier entries."""
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(decision.model_dump(), sort_keys=True) + "\n")
