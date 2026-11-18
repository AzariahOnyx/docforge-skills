"""Safe automatic fixes for Vale alerts that offer exactly one replacement.

A fix is applied only when:
- the alert has a single replacement and its span still holds the matched text;
- the span is in page prose, not in front matter, an HTML comment (evidence
  markers), inline code, a link target, or an HTML tag;
- no other alert on the same line overlaps it (that needs a person).

Fixes keep the matched word's capitalisation. For pages meant for publishing,
the claim gate runs again after applying; if it fails, every page is restored.
"""

from __future__ import annotations

import difflib
from pathlib import Path

from pydantic import BaseModel

from docforge.docs_index.build import split_front_matter
from docforge.textguard import gate_or_restore, protected_spans

from .vale import Alert, LintError, LintResult


class Fix(BaseModel):
    page: str
    line: int
    start: int
    end: int
    check: str
    before: str
    after: str


class FixPlan(BaseModel):
    fixes: list[Fix]
    skipped: list[str]
    diff: str


def _match_case(original: str, replacement: str) -> str:
    if original.isupper() and len(original) > 1:
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def plan_fixes(run: Path, result: LintResult) -> FixPlan:
    fixes: list[Fix] = []
    skipped: list[str] = []
    by_page: dict[str, list[Alert]] = {}
    for alert in result.alerts:
        by_page.setdefault(alert.page, []).append(alert)
    diffs: list[str] = []
    for page, alerts in sorted(by_page.items()):
        path = run / page
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        _, body_start = split_front_matter([l.rstrip("\n") for l in lines], [])
        new_lines = list(lines)
        page_fixes: list[Fix] = []
        for alert in sorted(alerts, key=lambda a: (a.line, -a.start)):
            where = f"{page}:{alert.line}:{alert.start} {alert.check}"
            if alert.replacement is None:
                continue
            if alert.line <= body_start:
                skipped.append(f"{where}: in front matter")
                continue
            text = lines[alert.line - 1].rstrip("\n")
            start, end = alert.start - 1, alert.end  # 0-based, end exclusive
            if text[start:end].casefold() != alert.match.casefold():
                skipped.append(f"{where}: text no longer matches '{alert.match}'")
                continue
            if any(s < end and start < e for s, e in protected_spans(text)):
                skipped.append(f"{where}: inside a marker, code, link target or tag")
                continue
            overlaps = [o for o in alerts if o is not alert and o.line == alert.line and o.start <= alert.end
                        and alert.start <= o.end and o.replacement is None]
            if overlaps:
                skipped.append(f"{where}: overlaps {overlaps[0].check}, which needs a person")
                continue
            page_fixes.append(Fix(page=page, line=alert.line, start=alert.start, end=alert.end, check=alert.check,
                                  before=text[start:end], after=_match_case(text[start:end], alert.replacement)))
        # Apply right to left on each line so earlier columns stay valid; drop overlapping fixes.
        last_start: dict[int, int] = {}
        for fix in sorted(page_fixes, key=lambda f: (f.line, -f.start)):
            if fix.line in last_start and fix.end >= last_start[fix.line]:
                skipped.append(f"{page}:{fix.line}:{fix.start} {fix.check}: overlaps another fix")
                continue
            line = new_lines[fix.line - 1]
            new_lines[fix.line - 1] = line[: fix.start - 1] + fix.after + line[fix.end:]
            last_start[fix.line] = fix.start
            fixes.append(fix)
        if new_lines != lines:
            diffs.append("".join(difflib.unified_diff(lines, new_lines, fromfile=f"a/{page}", tofile=f"b/{page}")))
    fixes.sort(key=lambda f: (f.page, f.line, f.start))
    return FixPlan(fixes=fixes, skipped=skipped, diff="".join(diffs))


def apply_fixes(run: Path, plan: FixPlan) -> None:
    """Write the fixes, re-run the claim gate, and restore every page if it fails."""
    from docforge.publish import gate_run

    pages = sorted({f.page for f in plan.fixes})
    originals = {p: (run / p).read_text(encoding="utf-8") for p in pages}
    for page in pages:
        lines = originals[page].splitlines(keepends=True)
        for fix in sorted((f for f in plan.fixes if f.page == page), key=lambda f: (f.line, -f.start)):
            line = lines[fix.line - 1]
            if line[fix.start - 1: fix.end] != fix.before:
                raise LintError(f"{page}:{fix.line} changed since the fixes were planned; lint again")
            lines[fix.line - 1] = line[: fix.start - 1] + fix.after + line[fix.end:]
        (run / page).write_text("".join(lines), encoding="utf-8")
    gate_or_restore(run, originals, LintError, "fixing")
