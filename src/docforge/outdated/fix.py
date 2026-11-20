"""Paragraph-level fixes to existing articles (B12b), applied by the engine and checked.

The Drafter writes `analysis/fixes.json`: `{"fixes": [{"path": <docs path>, "find": <exact text from one
paragraph>, "replace": <new text, with evidence markers>, "reason": ...}]}`. The engine applies them to the
copy of the published article (`existing/original/<path>` -> `existing/edited/<path>`) and checks:

- each `find` is in the article exactly once and stays inside one paragraph;
- old wording gone: the plan's outdated passage and the change note's old UI strings no longer appear
  (an old string inside its own new wording, "Schedule" in "Schedule to Production", does not count);
- formatting intact: the same front matter, the same headings in the same order, no fewer list items or
  table rows;
- no image lost; not shrunk (at least 90% of the words remain);
- only the targeted paragraphs changed, each by a bounded amount.

The changed line ranges go to `analysis/edits.json`; the claim gate checks only those statements.
An archived article only gains `status: archived` in its front matter.
"""

from __future__ import annotations

import json
from pathlib import Path
import re

from .shortlist import IMAGE

FIXES = "analysis/fixes.json"
EDITS = "analysis/edits.json"
MIN_WORDS = 0.9
HEADING = re.compile(r"^#{1,6}\s+\S.*$", re.M)
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\S", re.M)
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$", re.M)


def _front(text: str) -> tuple[str, str]:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end > 0:
            return text[: end + 4], text[end + 4:]
    return "", text


def mark_archived(text: str) -> str:
    """The article with `status: archived` in its front matter (added, or replacing another status)."""
    front, body = _front(text)
    if not front:
        return "---\nstatus: archived\n---\n\n" + text
    inner = front[4:-4]
    if re.search(r"^status:", inner, re.M):
        inner = re.sub(r"^status:.*$", "status: archived", inner, count=1, flags=re.M)
    else:
        inner = inner.rstrip("\n") + "\nstatus: archived"
    return "---\n" + inner + "\n---" + body


def _words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+", re.sub(r"<!--.*?-->", "", _front(text)[1], flags=re.S)))


def _normal(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[*_`]", "", text)).strip().casefold()


def _old_gone(text: str, old: list[str], new: list[str]) -> list[str]:
    body = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    for wording in sorted(new, key=len, reverse=True):
        body = body.replace(wording, " ")
    return [o for o in old if re.search(rf"(?<![\w-]){re.escape(o)}(?![\w-])", body)]


def _changed_ranges(before: str, after: str) -> list[list[int]]:
    import difflib

    ranges = []
    a, b = before.splitlines(), after.splitlines()
    for tag, _, _, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag in ("replace", "insert") and j2 > j1:
            ranges.append([j1 + 1, j2])
    return ranges


def check_edit(before: str, after: str, *, passage: str, old_strings: list[str], new_strings: list[str],
               archive: bool = False) -> list[str]:
    problems = []
    front_before, body_before = _front(before)
    front_after, body_after = _front(after)
    if archive:
        if mark_archived(before) != after:
            problems.append("an archived article may only gain status: archived in its front matter")
        return problems
    if front_before != front_after:
        problems.append("the front matter changed")
    if HEADING.findall(body_before) != HEADING.findall(body_after):
        problems.append("the headings changed")
    if len(LIST_ITEM.findall(body_after)) < len(LIST_ITEM.findall(body_before)):
        problems.append("list items were removed")
    if len(TABLE_ROW.findall(body_after)) < len(TABLE_ROW.findall(body_before)):
        problems.append("table rows were removed")
    lost = sorted(set(IMAGE.findall(before)) - set(IMAGE.findall(after)))
    if lost:
        problems.append(f"images were lost: {', '.join(lost)}")
    if _words(after) < MIN_WORDS * _words(before):
        problems.append(f"the article shrank ({_words(before)} -> {_words(after)} words)")
    if passage and _normal(passage) in _normal(re.sub(r"<!--.*?-->", "", after, flags=re.S)):
        problems.append("the outdated passage is still in the article")
    remaining = _old_gone(after, old_strings, new_strings)
    if remaining:
        problems.append(f"old wording is still in the article: {', '.join(remaining)}")
    return problems


def _apply(text: str, fixes: list[dict]) -> tuple[str, list[str]]:
    problems = []
    for fix in fixes:
        find, replace = str(fix.get("find") or ""), str(fix.get("replace") or "")
        if not find.strip():
            problems.append("a fix has no find text")
            continue
        if "\n\n" in find.strip("\n"):
            problems.append(f"a fix spans more than one paragraph: {find[:60]!r}")
            continue
        count = text.count(find)
        if count != 1:
            problems.append(f"the find text appears {count} times (it must appear once): {find[:60]!r}")
            continue
        if HEADING.search(replace) and not HEADING.search(find):
            problems.append(f"a fix adds a heading: {replace[:60]!r}")
            continue
        if len(replace) > 3 * len(find) + 400:
            problems.append(f"a fix rewrites far more than it replaces: {find[:60]!r}")
            continue
        text = text.replace(find, replace, 1)
    return text, problems


def apply_fixes(run: Path) -> dict:
    """Apply analysis/fixes.json to the run's existing articles and check them. Writes existing/edited/ and
    analysis/edits.json. Returns {"problems": [...], "edits": {dest: {...}}}."""
    from docforge.plan.review import EDITED, ORIGINAL

    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    edits = manifest.get("edits", [])
    note_file = run / "analysis" / "change-note.json"
    note = json.loads(note_file.read_text(encoding="utf-8")) if note_file.is_file() else {}
    old = [s["old"] for s in note.get("strings", []) if s.get("old")]
    new = [s["new"] for s in note.get("strings", []) if s.get("new")]
    fixes_data = json.loads((run / FIXES).read_text(encoding="utf-8")) if (run / FIXES).is_file() else {"fixes": []}
    fixes = fixes_data.get("fixes", []) if isinstance(fixes_data, dict) else []
    known = {e["dest"] for e in edits}
    problems = [f"a fix names {f.get('path')!r}, which the approved plan does not edit"
                for f in fixes if f.get("path") not in known]
    report = {}
    for edit in edits:
        dest = edit["dest"]
        before = (run / ORIGINAL / dest).read_text(encoding="utf-8")
        if edit["action"] == "archive":
            after = (run / EDITED / dest).read_text(encoding="utf-8")
            found = check_edit(before, after, passage="", old_strings=[], new_strings=[], archive=True)
            report[dest] = {"action": "archive", "ranges": [], "problems": found, "fixes": 0}
        else:
            mine = [f for f in fixes if f.get("path") == dest]
            after, found = _apply(before, mine)
            if not mine:
                found.append("no fix was written for this article")
            found += check_edit(before, after, passage=edit.get("passage", ""), old_strings=old, new_strings=new)
            target = run / EDITED / dest
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(after, encoding="utf-8")
            report[dest] = {"action": "update", "ranges": _changed_ranges(before, after), "problems": found,
                            "fixes": len(mine), "changes": [{"find": f.get("find"), "replace": f.get("replace"),
                                                             "reason": f.get("reason", "")} for f in mine]}
        problems += [f"{dest}: {p}" for p in report[dest]["problems"]]
    (run / EDITS).write_text(json.dumps({"edits": report}, indent=2) + "\n", encoding="utf-8")
    return {"problems": problems, "edits": report}
