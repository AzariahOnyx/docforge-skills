"""`ia-plan.md`: the documentation plan a writer reviews and approves as a pull request.

The file has YAML front matter and five sections, each a table with fixed columns (or the line "None.").
DocForge writes it, a writer may edit it, and DocForge reads the approved version back, so the format is
checked strictly: `parse_plan` reads it and `check_plan` lists every problem.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath
import re

import yaml

FRONT_KEYS = ("feature", "mode", "product", "category", "owner", "source_prs", "engineering_spec", "release")
OPTIONAL_KEYS = ("jira", "docforge_run")
MODES = ("Net-New", "Enhancement")
CHANGES = ("update", "deprecate", "remove")
DEFAULT_TYPES = ("overview", "procedural", "release-notes")
SECTIONS = {
    "Existing articles - impact": ("Article", "Docs path", "Change", "Why", "Claims"),
    "New articles": ("Title", "Type", "Docs path", "Why", "Claims"),
    "Out of scope": ("Topic", "Reason"),
    "Open questions": ("ID", "Question", "Why it matters"),
    "Spec-versus-code conflicts": ("ID", "Claim", "Spec says", "Code says", "Question"),
}
CLAIM_RE = re.compile(r"^C\d+[A-Z]?$")
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

    def articles(self) -> list[dict]:
        """Every article the plan touches: {title, type, path, change} (change "create" for new articles)."""
        return ([{"title": a["Title"], "type": a["Type"], "path": a["Docs path"], "change": "create"} for a in self.new]
                + [{"title": a["Article"], "type": None, "path": a["Docs path"], "change": a["Change"].casefold()}
                   for a in self.existing])


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
        header = _cells(table[0])
        if tuple(header) != columns:
            errors.append(f"## {name}: the columns must be {' | '.join(columns)} (found {' | '.join(header)})")
            plan.sections[name] = []
            continue
        rows = []
        for line in table[1:]:
            cells = _cells(line)
            if all(set(c) <= set("-: ") for c in cells):
                continue
            if len(cells) != len(columns):
                errors.append(f"## {name}: a row has {len(cells)} cells instead of {len(columns)}: {line.strip()[:80]}")
                continue
            rows.append(dict(zip(columns, cells)))
        plan.sections[name] = rows
    return plan, errors


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

    allowed_types = list(types or DEFAULT_TYPES)
    paths: list[str] = []
    for row in plan.new:
        if not row["Title"]:
            errors.append("## New articles: a row has no title")
        if row["Type"] not in allowed_types:
            errors.append(f"## New articles: type {row['Type']!r} is not one of {', '.join(allowed_types)}")
        paths.append(row["Docs path"])
    for row in plan.existing:
        if row["Change"].casefold() not in CHANGES:
            errors.append(f"## Existing articles - impact: change {row['Change']!r} must be {', '.join(CHANGES)}")
        paths.append(row["Docs path"])
    for row in plan.new + plan.existing:
        bad = [c for c in _claims(row["Claims"]) if not CLAIM_RE.match(c)]
        if bad:
            errors.append(f"claims {', '.join(bad)} are not claim IDs like C03 (or write none)")
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
        if not CLAIM_RE.match(row["Claim"]):
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
