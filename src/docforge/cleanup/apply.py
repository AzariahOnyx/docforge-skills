"""`docforge cleanup`: run a pack's clean-up steps over a run's deliverables.

Without `apply`, nothing is written: the result holds the diff and every planned
change. With `apply`, pages are written, the claim gate runs again for gated runs
(every page is restored if it fails), and qa/cleanup.json and
qa/CLEANUP-REPORT.md list every change and finding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import difflib
import json
from pathlib import Path

from docforge.textguard import gate_or_restore

from .steps import RUNNERS, Change, Finding


class CleanupError(Exception):
    """Raised when clean-up cannot run or its result fails the gate."""


@dataclass
class CleanupResult:
    pack: str | None
    steps: list[dict] = field(default_factory=list)
    changes: list[Change] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    diff: str = ""
    pages: dict[str, str] = field(default_factory=dict)  # page -> new text
    applied: bool = False

    def to_dict(self) -> dict:
        return {"cleaned_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "pack": self.pack,
                "applied": self.applied, "steps": self.steps,
                "changes": [c.to_dict() for c in self.changes], "findings": [f.to_dict() for f in self.findings]}


def _steps(run: Path, manifest: dict):
    record = manifest.get("pack")
    if not record:
        return None, []
    from docforge.packs import PackError, run_manifest

    try:
        pack = run_manifest(run, record)
    except (PackError, ValueError) as exc:
        raise CleanupError(f"the run's pack copy cannot be used: {exc}") from None
    return f"{record['name']} {record['version']}", list(pack.cleanup_steps)


def plan_cleanup(run: Path) -> CleanupResult:
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    name, steps = _steps(run, manifest)
    result = CleanupResult(pack=name)
    originals = {d: (run / d).read_text(encoding="utf-8") for d in manifest.get("deliverables", []) if (run / d).is_file()}
    pages = dict(originals)
    for step in steps:
        counts = {"id": step.id, "kind": step.kind, "description": step.description, "changes": 0, "findings": 0}
        for page in sorted(pages):
            if not step.runs_on(page):
                continue
            new, changes, findings = RUNNERS[step.kind](step, page, pages[page])
            pages[page] = new
            result.changes += changes
            result.findings += findings
            counts["changes"] += len(changes)
            counts["findings"] += len(findings)
        result.steps.append(counts)
    result.pages = {p: t for p, t in pages.items() if t != originals[p]}
    result.diff = "".join(
        "".join(difflib.unified_diff(originals[p].splitlines(keepends=True), t.splitlines(keepends=True),
                                     fromfile=f"a/{p}", tofile=f"b/{p}"))
        for p, t in sorted(result.pages.items()))
    return result


def render_report(result: CleanupResult) -> str:
    lines = ["# Clean-up report", "",
             f"Pack: {result.pack or 'none'}. {len(result.changes)} change(s), {len(result.findings)} finding(s). "
             "Every automatic change is listed; check each one before approving. Line numbers are as each step "
             "saw the page, so a step after a move or removal may name a different line than the final page.", "",
             "| Step | Kind | Changes | Findings |", "| --- | --- | --- | --- |"]
    lines += [f"| {s['id']} | {s['kind']} | {s['changes']} | {s['findings']} |" for s in result.steps]
    if result.changes:
        lines += ["", "## Changes", "", "| Step | Page | Line | Action | Before | After |",
                  "| --- | --- | --- | --- | --- | --- |"]
        lines += [f"| {c.step} | `{c.page}` | {c.line} | {c.action} | {_cell(c.before)} | {_cell(c.after)} |"
                  for c in result.changes]
    if result.findings:
        lines += ["", "## Findings (nothing changed)", "", "| Step | Page | Line | Finding | Text |",
                  "| --- | --- | --- | --- | --- |"]
        lines += [f"| {f.step} | `{f.page}` | {f.line} | {_cell(f.message)} | {_cell(f.text)} |" for f in result.findings]
    return "\n".join(lines) + "\n"


def _cell(text: str) -> str:
    text = text.replace("|", "\\|").replace("<!--", "&lt;!--")
    return f"`{text}`" if text and "`" not in text else (text or "")


def apply_cleanup(run: Path, result: CleanupResult) -> CleanupResult:
    originals = {p: (run / p).read_text(encoding="utf-8") for p in result.pages}
    for page, text in result.pages.items():
        (run / page).write_text(text, encoding="utf-8")
    gate_or_restore(run, originals, CleanupError, "clean-up")
    result.applied = True
    (run / "qa").mkdir(exist_ok=True)
    (run / "qa" / "cleanup.json").write_text(json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8")
    (run / "qa" / "CLEANUP-REPORT.md").write_text(render_report(result), encoding="utf-8")
    return result
