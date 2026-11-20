"""`ia-plan.md`: the documentation plan a writer reviews and approves as a pull request.

One format for every route (the engine and the docs-writer agent; B12a-0). The file has YAML front
matter and five sections, each a table with fixed columns (or the line "None."). The first engine
format's columns are still read and converted, so earlier plans keep working.
DocForge writes it, a writer may edit it, and DocForge reads the approved version back, so the format is
checked strictly: `parse_plan` reads it and `check_plan` lists every problem.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath
import re

import yaml

FRONT_KEYS = ("feature", "mode", "product", "category", "owner", "source_prs", "engineering_spec", "release")
OPTIONAL_KEYS = ("jira", "docforge_run", "decision", "decision_reason", "status")
MODES = ("Net-New", "Enhancement")
ACTIONS = ("update", "archive", "none")
STATUSES = ("proposed", "approved")
DECISIONS = ("act", "confirm", "quiet")
DEFAULT_TYPES = ("overview", "procedural", "release-notes")
# The unified format (B12a-0): one plan format for the engine and the docs-writer agent.
SECTIONS = {
    "Existing articles - impact": ("Article", "Docs path", "Action", "Change needed", "Outdated passage", "Evidence"),
    "New articles": ("Title", "Type", "Docs path", "Why", "Evidence"),
    "Out of scope": ("Topic", "Reason"),
    "Open questions": ("ID", "Question", "Why it matters"),
    "Spec-versus-code conflicts": ("ID", "Spec says", "Code says", "Where", "Question"),
}
# The first engine format (B7c) is still read; its rows are converted to the unified columns.
FIRST_FORMAT = {
    "Existing articles - impact": ("Article", "Docs path", "Change", "Why", "Claims"),
    "New articles": ("Title", "Type", "Docs path", "Why", "Claims"),
    "Spec-versus-code conflicts": ("ID", "Claim", "Spec says", "Code says", "Question"),
}
FIRST_ACTIONS = {"update": "update", "deprecate": "archive", "remove": "archive"}
CLAIM_RE = re.compile(r"^C\d+[A-Z]?$")
# Evidence: claim IDs (the engine) or source tags (the agent: SPEC:<section>, CODE:<path>:<line>, ...).
TAG_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,15}:\S.*$")
SOURCE_PR_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[1-9][0-9]*$")
FRONT_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)


@dataclass
class IaPlan:
    front: dict
    sections: dict[str, list[dict]] = field(default_factory=dict)

    @property
    def existing(self) -> list[dict]:
        return self.sections.get("Existing articles - impact", [])

    @property
    def new(self) -> list[dict]:
        return self.sections.get("New articles", [])

    @property
    def questions(self) -> list[dict]:
        return self.sections.get("Open questions", [])

    @property
    def conflicts(self) -> list[dict]:
        return self.sections.get("Spec-versus-code conflicts", [])

    @property
    def approved(self) -> bool:
        return str(self.front.get("status", "")).casefold() == "approved"

    def articles(self) -> list[dict]:
        """Every article the plan touches: {title, type, path, change} ("create" for new articles; "update" or
        "archive" for existing ones; rows with action "none" are listed but need no work)."""
        return ([{"title": a["Title"], "type": a["Type"], "path": a["Docs path"], "change": "create"} for a in self.new]
                + [{"title": a["Article"], "type": None, "path": a["Docs path"], "change": a["Action"].casefold()}
                   for a in self.existing if a["Action"].casefold() != "none"])


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_plan(text: str) -> tuple[IaPlan | None, list[str]]:
    """(plan, problems reading it). The plan is None when the file cannot be read at all."""
    errors: list[str] = []
    text = text.replace("\r\n", "\n")
    match = FRONT_RE.match(text)
    if not match:
        return None, ["ia-plan.md must start with YAML front matter between --- lines"]
    try:
        front = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        return None, [f"front matter is not valid YAML: {str(exc).splitlines()[0]}"]
    if not isinstance(front, dict):
        return None, ["front matter must be a mapping of keys to values"]
    plan = IaPlan(front=front)
    body = re.sub(r"<!--.*?-->", "", text[match.end():], flags=re.S)
    headings = list(re.finditer(r"^##\s+(.+?)\s*$", body, re.M))
    found = {}
    for i, heading in enumerate(headings):
        end = headings[i + 1].start() if i + 1 < len(headings) else len(body)
        found[heading.group(1)] = body[heading.end():end]
    for name, columns in SECTIONS.items():
        if name not in found:
            errors.append(f"missing section: ## {name}")
            continue
        lines = [l for l in found[name].splitlines() if l.strip() and not l.strip().startswith(">")]
        table = [l for l in lines if l.strip().startswith("|")]
        if not table:
            if not lines or not lines[0].strip().startswith("None."):
                errors.append(f"## {name}: give a table or the line \"None.\"")
            plan.sections[name] = []
            continue
        header = tuple(_cells(table[0]))
        first = FIRST_FORMAT.get(name)
        if header != columns and header != first:
            errors.append(f"## {name}: the columns must be {' | '.join(columns)} (found {' | '.join(header)})")
            plan.sections[name] = []
            continue
        rows = []
        for line in table[1:]:
            cells = _cells(line)
            if all(set(c) <= set("-: ") for c in cells):
                continue
            if len(cells) != len(header):
                errors.append(f"## {name}: a row has {len(cells)} cells instead of {len(header)}: {line.strip()[:80]}")
                continue
            row = dict(zip(header, cells))
            rows.append(_unify(name, row) if header == first else row)
        plan.sections[name] = rows
    return plan, errors


def _unify(section: str, row: dict) -> dict:
    """A row of the first engine format, in the unified columns."""
    if section == "Existing articles - impact":
        return {"Article": row["Article"], "Docs path": row["Docs path"],
                "Action": FIRST_ACTIONS.get(row["Change"].casefold(), row["Change"]), "Change needed": row["Why"],
                "Outdated passage": "", "Evidence": row["Claims"]}
    if section == "New articles":
        return {"Title": row["Title"], "Type": row["Type"], "Docs path": row["Docs path"], "Why": row["Why"],
                "Evidence": row["Claims"]}
    return {"ID": row["ID"], "Spec says": row["Spec says"], "Code says": row["Code says"], "Where": "",
            "Question": row["Question"], "Claim": row["Claim"]}


def _claims(cell: str) -> list[str]:
    return [] if cell.strip().casefold() in ("none", "") else [c.strip() for c in re.split(r"[,;]\s*", cell)]


def check_plan(plan: IaPlan, *, types: list[str] | None = None, allows=None) -> list[str]:
    """Every problem in a parsed plan. `allows(path)` checks a docs path against the doc collection's filter."""
    errors: list[str] = []
    front = plan.front
    for key in FRONT_KEYS:
        if key not in front:
            errors.append(f"front matter: {key} is missing")
    for key in front:
        if key not in FRONT_KEYS + OPTIONAL_KEYS:
            errors.append(f"front matter: unknown key {key}")
    for key in ("feature", "product", "category", "owner", "release"):
        if key in front and (not isinstance(front[key], str) or not front[key].strip()):
            errors.append(f"front matter: {key} must be text (write unknown when it is not known)")
    if "mode" in front and front["mode"] not in MODES:
        errors.append(f"front matter: mode must be {' or '.join(MODES)}, not {front['mode']!r}")
    prs = front.get("source_prs", [])
    if not isinstance(prs, list) or any(not isinstance(p, str) or not SOURCE_PR_RE.match(p) for p in prs):
        errors.append("front matter: source_prs must be a list of owner/repo#123 entries")
    if "engineering_spec" in front and not isinstance(front["engineering_spec"], str):
        errors.append("front matter: engineering_spec must be a path, a link or none")
    if "status" in front and str(front["status"]).casefold() not in STATUSES:
        errors.append(f"front matter: status must be {' or '.join(STATUSES)}, not {front['status']!r}")
    if "decision" in front and str(front["decision"]).casefold() not in DECISIONS:
        errors.append(f"front matter: decision must be {', '.join(DECISIONS)}, not {front['decision']!r}")

    allowed_types = list(types or DEFAULT_TYPES)
    paths: list[str] = []
    for row in plan.new:
        if not row["Title"]:
            errors.append("## New articles: a row has no title")
        if row["Type"] not in allowed_types:
            errors.append(f"## New articles: type {row['Type']!r} is not one of {', '.join(allowed_types)}")
        paths.append(row["Docs path"])
    for row in plan.existing:
        if row["Action"].casefold() not in ACTIONS:
            errors.append(f"## Existing articles - impact: action {row['Action']!r} must be {', '.join(ACTIONS)}")
        paths.append(row["Docs path"])
    for row in plan.new + plan.existing:
        bad = [c for c in _claims(row["Evidence"]) if not CLAIM_RE.match(c) and not TAG_RE.match(c)]
        if bad:
            errors.append(f"evidence {', '.join(bad)} is neither a claim ID like C03 nor a source tag like "
                          "SPEC:<section> (or write none)")
    for path in paths:
        parts = PurePosixPath(path).parts
        if not path.endswith(".md") or path.startswith("/") or ".." in parts or "\\" in path or "`" in path:
            errors.append(f"docs path {path!r} must be a relative .md path without backticks")
        elif allows is not None and not allows(path):
            errors.append(f"docs path {path} is outside the doc collection's filter")
    dupes = sorted({p for p in paths if paths.count(p) > 1})
    if dupes:
        errors.append(f"docs paths used twice: {', '.join(dupes)}")
    for row in plan.questions:
        if not re.fullmatch(r"Q\d+", row["ID"]):
            errors.append(f"## Open questions: ID {row['ID']!r} must look like Q01")
    for row in plan.conflicts:
        if not re.fullmatch(r"X\d+", row["ID"]):
            errors.append(f"## Spec-versus-code conflicts: ID {row['ID']!r} must look like X1")
        if "Claim" in row and not CLAIM_RE.match(row["Claim"]):
            errors.append(f"## Spec-versus-code conflicts: claim {row['Claim']!r} must look like C05")
    if not plan.new and not plan.existing:
        errors.append("the plan has no article to create or update")
    return errors


def read_plan(text: str, *, types: list[str] | None = None, allows=None) -> tuple[IaPlan | None, list[str]]:
    plan, errors = parse_plan(text)
    if plan is None:
        return None, errors
    return plan, errors + check_plan(plan, types=types, allows=allows)


def plan_slug(plan: IaPlan) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(plan.front.get("feature", "")).casefold()).strip("-")[:60] or "plan"
