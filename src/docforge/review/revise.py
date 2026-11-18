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
    learned = _learned([p["src"] for p in plan.placements])
    if learned:
        insert = lines.index("## Pages")
        lines[insert:insert] = ["## Learned guidance", "",
                                "Approved from earlier review feedback; it never overrides the sources.", "",
                                *learned, ""]
    pack_lines = _pack(run, [p["src"] for p in plan.placements])
    if pack_lines:
        insert = lines.index("## Pages")
        lines[insert:insert] = [*pack_lines[1:], ""]
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


def _learned(pages: list[str]) -> list[str]:
    from docforge.rules import RuleError, guidance_lines, rules_dir

    try:
        return guidance_lines(rules_dir(), pages)
    except RuleError:
        return []


def _pack(run: Path, pages: list[str]) -> list[str]:
    """The house pack section for a revision, from the copy inside the run. A broken copy is reported, not hidden."""
    import json

    from docforge.packs import PackError, run_manifest, stage_lines

    try:
        record = json.loads((run / "run.json").read_text(encoding="utf-8")).get("pack")
    except (OSError, ValueError):
        return []
    if not record:
        return []
    try:
        manifest = run_manifest(run, record)
    except (PackError, ValueError) as exc:
        return ["", "## House pack", "", f"The run's pack copy cannot be used: {exc}. Ask a person before revising."]
    return stage_lines(manifest, record, "revision", pages, run.name)
