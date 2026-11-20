"""Recall on past changes: does the finder find the articles writers actually updated?

A cases file lists past changes: each with its change note (old strings, terms; written or checked by a
person) and the docs paths writers changed for it. `propose_cases` drafts such a file from the docs
repository's history (commits grouped by a Jira key or pull request reference in the message); a person
fills in each change note and checks the expected pages.

Scoring is free for the shortlist (no model). Verdict recall is scored only for cases that point to a merged
`outdated.json` (from a run with the passes done by the backend or by sessions).
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

from docforge.config import DocCollection

from .note import ChangeNote
from .shortlist import build_shortlist

KEY = re.compile(r"\b([A-Z][A-Z0-9]{1,9}-[1-9][0-9]*)\b|#([1-9][0-9]*)\b")


class EvalError(Exception):
    pass


def propose_cases(docs_checkout: Path, out: Path, *, collection: DocCollection | None = None, limit: int = 300) -> dict:
    """Draft a cases file from the docs history. Never overwrites a file someone may have edited."""
    if out.exists():
        raise EvalError(f"{out} already exists; it may hold someone's cases")
    result = subprocess.run(["git", "-C", str(docs_checkout), "log", f"-{limit}", "--name-only", "--format=%x00%H%x09%s"],
                            capture_output=True, text=True, timeout=120, check=False)
    if result.returncode != 0:
        raise EvalError(f"git log failed: {result.stderr.strip()[:200]}")
    groups: dict[str, dict] = {}
    for block in result.stdout.split("\x00")[1:]:
        header, _, files = block.partition("\n")
        sha, _, subject = header.partition("\t")
        match = KEY.search(subject)
        if not match:
            continue
        key = match.group(1) or f"#{match.group(2)}"
        paths = [p for p in files.splitlines() if p.endswith(".md") and (collection is None or collection.allows(p))]
        if not paths:
            continue
        case = groups.setdefault(key, {"id": key, "commits": [], "subjects": [], "expected": [],
                                       "note": {"strings": [], "terms": [], "spec_changes": [], "behaviour": []}})
        case["commits"].append(sha)
        case["subjects"].append(subject)
        case["expected"] = sorted(set(case["expected"]) | set(paths))
    data = {"instructions": "For each case, fill note.strings (old and new UI wording, as {\"old\", \"new\", "
                            "\"where\"}) and note.terms from the product change, check expected (the pages writers "
                            "updated for it), and remove cases that are not product changes. Set checked_by.",
            "checked_by": None, "cases": list(groups.values())}
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def evaluate(cases_path: Path, docs: Path, *, collection: DocCollection | None = None, must_review=(), cap: int = 25) -> dict:
    data = json.loads(cases_path.read_text(encoding="utf-8"))
    rows, found_total, expected_total, verdict_hits, verdict_expected = [], 0, 0, 0, 0
    for case in data.get("cases", []):
        expected = set(case.get("expected", []))
        if not expected:
            continue
        note = ChangeNote.from_dict(case.get("note", {}))
        shortlist = build_shortlist(docs, note, collection=collection, must_review=list(must_review), cap=cap)
        listed = {p["path"] for p in shortlist["pages"]}
        found = expected & listed
        row = {"id": case.get("id"), "expected": sorted(expected), "found": sorted(found),
               "missed": sorted(expected - listed), "shortlisted": len(listed),
               "must_review": sorted(expected & set(shortlist["must_review"]))}
        if case.get("outdated"):
            merged = json.loads((cases_path.parent / case["outdated"]).read_text(encoding="utf-8"))
            flagged = {p["path"] for p in merged.get("pages", []) if p.get("verdict") in ("affected", "unsure")}
            row["verdict_found"] = sorted(expected & flagged)
            verdict_hits += len(expected & flagged)
            verdict_expected += len(expected)
        found_total += len(found)
        expected_total += len(expected)
        rows.append(row)
    checked = data.get("checked_by")
    report = {
        "evaluated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "cases": len(rows), "checked_by": checked,
        "shortlist_recall": f"{found_total}/{expected_total}" if expected_total else "n/a",
        "verdict_recall": f"{verdict_hits}/{verdict_expected}" if verdict_expected else "n/a (no case has verdicts)",
        "rows": rows,
        "note": ("Cases checked by a person; recall is measured against what writers actually updated."
                 if checked else "No one has checked these cases yet: treat the numbers as a dry run, not a measure."),
    }
    return report


def render_eval(report: dict) -> str:
    lines = ["# Outdated content finder: recall on past changes", "", report["note"], "",
             f"Cases: {report['cases']}. Shortlist recall: {report['shortlist_recall']}. "
             f"Verdict recall: {report['verdict_recall']}.", "",
             "| Case | Expected | Found | Missed | Shortlisted |", "| --- | --- | --- | --- | --- |"]
    for r in report["rows"]:
        lines.append(f"| {r['id']} | {len(r['expected'])} | {len(r['found'])} | "
                     f"{', '.join(f'`{m}`' for m in r['missed']) or 'none'} | {r['shortlisted']} |")
    return "\n".join(lines) + "\n"
