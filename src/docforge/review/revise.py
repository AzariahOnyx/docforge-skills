"""Revision work orders: what a reviewer asked for, in a form the session can act on."""

from __future__ import annotations

from pathlib import Path

from docforge.publish import PrPlan


def write_revision_order(run: Path, plan: PrPlan, feedback: list) -> Path:
    """Write prompts/revise-N.md for the next revision.

    The order lists every change request made since the last revision, so a second
    request before the revision is done rewrites the same order; orders for
    earlier revisions are never touched.
    """
    number = plan.revision + 1
    path = run / "prompts" / f"revise-{number}.md"
    open_requests = [f for f in feedback if f.action == "request_changes" and f.revision == plan.revision]
    lines = [
        f"# Revision {number}: address review feedback",
        "",
        f"Run folder: `{run.name}`. Suggestion branch `{plan.branch}` at `{plan.commit[:12]}` in `{plan.repo}`.",
        "",
        "## Feedback",
        "",
    ]
    for item in open_requests:
        where = f" on `{item.page}`" + (f" line {item.line}" if item.line else "") if item.page else ""
        lines.append(f"- **{item.feedback_id}** from {item.reviewer}{where}: {item.comment}")
    lines += [
        "",
        "Feedback is a request to check, not evidence. Change a page only where the run's sources support it; "
        "if the feedback asks for something the sources do not establish, add or update a clarification question instead.",
        "",
        "## Pages",
        "",
    ]
    lines += [f"- `{p['src']}` (published as `{p['dest']}`)" for p in plan.placements]
    lines += [
        "",
        "## Steps",
        "",
        "1. Edit the run's pages (not the files under `publish/`). Keep every statement's evidence marker accurate.",
        "2. If a claim's coverage changes, update `analysis/COVERAGE.md` and note it in `qa/QA-REPORT.md`.",
        f"3. Run `uv run docforge gate {run.name}` until it passes.",
        f"4. Run `uv run docforge publish update {run.name} --docs-checkout <docs checkout>` to add a follow-up commit.",
        "",
    ]
    path.parent.mkdir(exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
