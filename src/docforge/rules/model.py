"""Learned rules: schema, storage and lifecycle.

A rule is one YAML file in the rules folder and moves through:

    proposed -> tested -> live          (or rejected / retired)

`approve` needs a test report whose content hash matches the rule as it is
now. Editing a rule's content after it was tested or approved makes it
`proposed` again, so no approval applies to wording nobody tested.

The rules folder is `--rules-dir`, else $DOCFORGE_RULES_DIR, else
knowledge/rules in the DocForge repository. Keep rules learned from private
feedback in a private repository.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
import yaml

TOOLS_ROOT = Path(__file__).resolve().parents[3]
RULE_ID_RE = re.compile(r"^R\d{3,}$")
MAX_PATTERN = 200
# Vale uses Go's RE2 syntax: no lookaround or backreferences.
UNSUPPORTED_REGEX = re.compile(r"\(\?<?[=!]|\\[1-9]")
CONTENT_FIELDS = ("kind", "title", "message", "pattern", "replace", "ignorecase", "level", "guidance", "applies_to")

Kind = Literal["avoid", "guidance"]
Status = Literal["proposed", "tested", "live", "rejected", "retired"]


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class RuleError(Exception):
    """Raised when a rule is invalid or an action is not allowed."""


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Origin(Strict):
    run: str
    feedback_id: str


class Hit(Strict):
    run: str
    page: str
    line: int
    match: str
    text: str


class TrialReport(Strict):
    at: str
    content_hash: str
    runs: list[str]
    pages_checked: int
    hits: list[Hit] = Field(default_factory=list)
    feedback: list[str] = Field(default_factory=list)  # the origin feedback, quoted, for guidance rules
    note: str = ""


class Approval(Strict):
    by: str
    at: str
    content_hash: str


class Closure(Strict):
    by: str
    at: str
    reason: str


class Rule(Strict):
    id: str
    kind: Kind
    title: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=300)
    pattern: str | None = None
    replace: str | None = None
    ignorecase: bool = True
    level: Literal["suggestion", "warning", "error"] = "warning"
    guidance: str | None = None
    applies_to: list[str] = Field(default_factory=list)  # run page paths containing any of these; empty = all
    origins: list[Origin] = Field(default_factory=list)
    proposed_by: str
    proposed_at: str
    status: Status = "proposed"
    test: TrialReport | None = None
    approval: Approval | None = None
    closed: Closure | None = None

    @field_validator("id")
    @classmethod
    def _id(cls, value: str) -> str:
        if not RULE_ID_RE.match(value):
            raise ValueError("rule IDs look like R001")
        return value

    @model_validator(mode="after")
    def _kind_fields(self):
        if self.kind == "avoid":
            if not self.pattern:
                raise ValueError("an avoid rule needs a pattern")
            check_pattern(self.pattern)
            if self.guidance:
                raise ValueError("an avoid rule has no guidance text")
        else:
            if not self.guidance or not self.guidance.strip():
                raise ValueError("a guidance rule needs guidance text")
            if self.pattern or self.replace:
                raise ValueError("a guidance rule has no pattern or replacement")
        if self.replace is not None and not self.replace.strip():
            raise ValueError("replace cannot be empty")
        return self

    def content_hash(self) -> str:
        content = {name: getattr(self, name) for name in CONTENT_FIELDS}
        return hashlib.sha256(json.dumps(content, sort_keys=True).encode("utf-8")).hexdigest()

    def effective_status(self) -> str:
        """The status, or 'proposed (changed since test)' when edited after testing or approval."""
        if self.status in ("tested", "live"):
            reference = self.approval.content_hash if self.status == "live" and self.approval else (
                self.test.content_hash if self.test else "")
            if reference != self.content_hash():
                return "proposed (changed since test)"
        return self.status


def check_pattern(pattern: str) -> None:
    if len(pattern) > MAX_PATTERN:
        raise ValueError(f"pattern is longer than {MAX_PATTERN} characters")
    if UNSUPPORTED_REGEX.search(pattern):
        raise ValueError("pattern uses lookaround or a backreference, which Vale does not support")
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        raise ValueError(f"pattern is not a valid regular expression: {exc}") from None
    if compiled.fullmatch(""):
        raise ValueError("pattern matches empty text")


def rules_dir(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit
    env = os.environ.get("DOCFORGE_RULES_DIR")
    return Path(env) if env else TOOLS_ROOT / "knowledge" / "rules"


def load_rules(folder: Path) -> list[Rule]:
    rules = []
    for path in sorted(folder.glob("R*.yml")) if folder.is_dir() else []:
        try:
            rules.append(Rule.model_validate(yaml.safe_load(path.read_text(encoding="utf-8"))))
        except (ValueError, yaml.YAMLError) as exc:
            raise RuleError(f"{path.name} is invalid: {exc}") from None
    return rules


def load_rule(folder: Path, rule_id: str) -> Rule:
    if not RULE_ID_RE.match(rule_id or ""):
        raise RuleError(f"rule IDs look like R001, not {rule_id!r}")
    path = folder / f"{rule_id}.yml"
    if not path.is_file():
        raise RuleError(f"no rule {rule_id} in {folder}")
    try:
        return Rule.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    except (ValueError, yaml.YAMLError) as exc:
        raise RuleError(f"{path.name} is invalid: {exc}") from None


def save_rule(folder: Path, rule: Rule) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{rule.id}.yml"
    data = rule.model_dump(mode="json", exclude_none=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100), encoding="utf-8")
    return path


def next_id(folder: Path) -> str:
    numbers = [int(p.stem[1:]) for p in folder.glob("R*.yml") if p.stem[1:].isdigit()] if folder.is_dir() else []
    return f"R{(max(numbers) + 1 if numbers else 1):03d}"


def propose(folder: Path, *, kind: str, title: str, message: str, proposed_by: str, pattern: str | None = None,
            replace: str | None = None, level: str = "warning", guidance: str | None = None,
            applies_to: list[str] | None = None, origins: list[tuple[str, str]] | None = None,
            ignorecase: bool = True) -> Rule:
    if not proposed_by.strip():
        raise RuleError("proposed_by is required")
    try:
        rule = Rule(id=next_id(folder), kind=kind, title=title, message=message, pattern=pattern, replace=replace,
                    level=level, guidance=guidance, applies_to=applies_to or [], ignorecase=ignorecase,
                    origins=[Origin(run=r, feedback_id=f) for r, f in (origins or [])],
                    proposed_by=proposed_by.strip(), proposed_at=now())
    except ValueError as exc:
        raise RuleError(str(exc)) from None
    save_rule(folder, rule)
    return rule


def approve(folder: Path, rule_id: str, *, by: str) -> Rule:
    rule = load_rule(folder, rule_id)
    if not by.strip():
        raise RuleError("approver name is required")
    if rule.status in ("rejected", "retired"):
        raise RuleError(f"{rule_id} is {rule.status}")
    if rule.test is None:
        raise RuleError(f"{rule_id} has not been tested; run docforge rules test {rule_id} first")
    if rule.test.content_hash != rule.content_hash():
        raise RuleError(f"{rule_id} changed after its last test; test it again before approving")
    if rule.effective_status() == "live":
        raise RuleError(f"{rule_id} is already live")
    rule.status = "live"
    rule.approval = Approval(by=by.strip(), at=now(), content_hash=rule.content_hash())
    save_rule(folder, rule)
    from .live import sync_live

    sync_live(folder)
    return rule


def close(folder: Path, rule_id: str, *, status: str, by: str, reason: str) -> Rule:
    rule = load_rule(folder, rule_id)
    if not reason.strip() or not by.strip():
        raise RuleError("a name and a reason are required")
    if rule.status in ("rejected", "retired"):
        raise RuleError(f"{rule_id} is already {rule.status}")
    if status == "retired" and rule.status != "live":
        raise RuleError(f"only live rules are retired; reject {rule_id} instead")
    if status == "rejected" and rule.status == "live":
        raise RuleError(f"{rule_id} is live; retire it instead")
    rule.status = status
    rule.closed = Closure(by=by.strip(), at=now(), reason=reason.strip())
    save_rule(folder, rule)
    from .live import sync_live

    sync_live(folder)
    return rule
