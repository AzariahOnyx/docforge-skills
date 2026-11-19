"""Read what a ticket's comments need from its run: planned articles, open questions, a drafts summary."""

from __future__ import annotations

import json
from pathlib import Path
import re

ACTIONS = ("CREATE", "UPDATE", "DEFER")


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _table(text: str, heading: str) -> list[dict]:
    """Rows of the first table under `## heading`, keyed by header cell."""
    match = re.search(rf"^##\s+{re.escape(heading)}\s*$", text, re.M | re.I)
    if not match:
        return []
    rows, header = [], None
    for line in text[match.end():].splitlines():
        if line.startswith("## "):
            break
        if not line.strip().startswith("|"):
            if header and rows:
                break
            continue
        cells = _cells(line)
        if header is None:
            header = [c.casefold() for c in cells]
        elif not all(set(c) <= set("-: ") for c in cells):
            rows.append(dict(zip(header, cells)))
    return rows


def plan_articles(run: Path) -> list[dict]:
    """{title, action, type} for each row of the content plan's scope decisions."""
    path = run / "analysis" / "CONTENT-PLAN.md"
    if not path.is_file():
        return []
    articles = []
    for row in _table(path.read_text(encoding="utf-8"), "Scope decisions"):
        topic = row.get("topic / reader goal") or next(iter(row.values()), "")
        action_cell = row.get("action", "").upper()
        action = next((a for a in ACTIONS if a in action_cell), "")
        if not topic or not action:
            continue
        destination = next((v for k, v in row.items() if k.startswith("destination")), "")
        where = re.search(r"`([^`]+\.md)`", destination) or re.search(r"([\w./-]+\.md)\b", destination)
        articles.append({"title": re.sub(r"[*`]", "", topic), "action": action.lower(),
                         "type": where.group(1) if where else (destination.split(";")[0][:80] or "not placed")})
    return articles


def open_questions(run: Path) -> list[str]:
    """Open questions from the clarification register (table rows or Qn headings)."""
    path = run / "analysis" / "clarifications-and-assumptions.md"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    questions, header = [], None
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            header = None
            continue
        cells = _cells(line)
        if header is None:
            header = [c.casefold() for c in cells]
            continue
        if not re.match(r"^Q\d+$", cells[0]):
            continue
        column = header.index("question") if "question" in header else None
        question = (cells[column] if column is not None and column < len(cells) and cells[column] else
                    next((c for c in cells[1:] if c.rstrip().endswith("?")), None))
        if question:
            questions.append(f"{cells[0]}: {re.sub(r'[*`]', '', question)}")
    if not questions:
        from docforge.publish.pr_body import QUESTION_HEADING

        questions = [f"{q}: {t.strip()}" for q, t in QUESTION_HEADING.findall(text)]
    return questions


def drafts_summary(run: Path) -> list[str]:
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    lines = [f"Draft: {d}" for d in manifest.get("deliverables", []) if (run / d).is_file()]
    gate = run / "qa" / "gate.json"
    if gate.is_file():
        g = json.loads(gate.read_text(encoding="utf-8"))
        flow = (f", numbered steps backed by flow steps {g['flow_backed_steps']}/{g['flow_steps']}"
                if g.get("flow_steps") is not None else "")
        lines.append(f"Claim gate: {'PASS' if g['passed'] else 'FAIL'} ({g['statements']} statements, "
                     f"{len(g['errors'])} errors{flow})")
    cleanup = run / "qa" / "cleanup.json"
    if cleanup.is_file():
        c = json.loads(cleanup.read_text(encoding="utf-8"))
        lines.append(f"Clean-up: {len(c['changes'])} automatic change(s), {len(c['findings'])} finding(s), "
                     "listed in qa/CLEANUP-REPORT.md")
    qa = run / "qa" / "QA-REPORT.md"
    if qa.is_file():
        from docforge.publish.pr_body import _readiness

        readiness = _readiness(qa.read_text(encoding="utf-8"))
        if readiness:
            lines.append("Proofreader: " + re.sub(r"[*`]", "", readiness[0])[:300])
    return lines
