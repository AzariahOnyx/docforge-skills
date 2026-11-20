"""Put the outdated content finder's results into ia-plan.md's "Existing articles - impact" table.

Affected and unsure pages become rows (edit -> update, archive -> archive; unsure rows say "(check)").
Rows the Analyzer wrote are kept; for the same docs path, an empty outdated passage, or one that is not in
the article word for word, takes the finder's checked passage. The section is written back in the unified
columns.
"""

from __future__ import annotations

import re

from docforge.plan.model import SECTIONS, parse_plan

HEADING = "## Existing articles - impact"


def _cell(text: str) -> str:
    return str(text or "").replace("|", "\\|").replace("\n", " ").strip()


def merge_into_plan(text: str, merged: list[dict], docs=None) -> tuple[str, int]:
    """(new plan text, rows added or filled). The plan must parse. With `docs`, an existing row's passage
    that is not in the article word for word is replaced by the finder's checked passage."""
    from .verdicts import _normal

    plan, _ = parse_plan(text)
    if plan is None or HEADING not in text:
        return text, 0
    rows = [dict(r) for r in plan.existing]
    by_path = {r["Docs path"]: r for r in rows}
    changed = 0
    for item in merged:
        if item["verdict"] == "not_affected":
            continue
        action = "archive" if item["action"] == "archive" else "update"
        why = item["reason"] or "the change makes this page outdated"
        if item["verdict"] == "unsure":
            why = f"(check) {why}"
        existing = by_path.get(item["path"])
        if existing is not None:
            quoted = existing["Outdated passage"]
            wrong = bool(quoted) and docs is not None and (docs / item["path"]).is_file() and \
                _normal(quoted) not in _normal((docs / item["path"]).read_text(encoding="utf-8"))
            if item["passage"] and item["verdict"] == "affected" and (not quoted or wrong):
                existing["Outdated passage"] = item["passage"]
                changed += 1
            if item["verdict"] == "unsure" and not existing["Change needed"].startswith("(check)"):
                existing["Change needed"] = f"(check: {item['reason']}) {existing['Change needed']}".strip()
                changed += 1
            continue
        row = {"Article": item["title"], "Docs path": item["path"], "Action": action, "Change needed": why,
               "Outdated passage": item["passage"], "Evidence": "none"}
        rows.append(row)
        by_path[item["path"]] = row
        changed += 1
    if not changed:
        return text, 0
    columns = SECTIONS["Existing articles - impact"]
    table = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    table += ["| " + " | ".join(_cell(r[c]) for c in columns) + " |" for r in rows]
    start = text.index(HEADING) + len(HEADING)
    following = re.search(r"^## ", text[start:], re.M)
    end = start + following.start() if following else len(text)
    return text[:start] + "\n\n" + "\n".join(table) + "\n\n" + text[end:], changed
