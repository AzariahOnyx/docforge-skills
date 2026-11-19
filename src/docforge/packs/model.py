"""The pack.yaml schema. Strict: unknown keys and unsafe paths are errors.

A pack is a folder of house material that shapes drafts without being a source:
output conventions, references, article structure specs, clean-up steps,
Vale styles and capture profiles. Pack material governs format, structure and
style. It never overrides the run's sources and is never evidence for product
behavior.
"""

from __future__ import annotations

from pathlib import PurePosixPath
import re
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
STYLE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
STAGES = ("analyzer", "drafter", "proofreader")
RESERVED_STYLES = frozenset({"DocForge", "DocForgeLearned", "Vale"})
Stage = Literal["analyzer", "drafter", "proofreader"]


def check_relative(value: str) -> str:
    """A forward-slash path inside the pack: not absolute, no '..', no empty or '.' parts."""
    if not value or "\\" in value or value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise ValueError(f"must be a relative path inside the pack: {value!r}")
    parts = PurePosixPath(value).parts
    if any(part in ("..", ".", "") for part in value.rstrip("/").split("/")) or not parts:
        raise ValueError(f"must be a relative path inside the pack: {value!r}")
    return value


def check_prefixes(value: list[str]) -> list[str]:
    for prefix in value:
        if not prefix or prefix.startswith("/") or ".." in prefix.split("/"):
            raise ValueError(f"applies_to entries are run-relative deliverable paths or folders: {prefix!r}")
    return value


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PackFileEntry(Strict):
    path: str

    @field_validator("path")
    @classmethod
    def _path(cls, value):
        return check_relative(value)


class Product(Strict):
    """A product or product line a run can be about; references can be limited to some products."""

    key: str
    title: str = Field(min_length=1)

    @field_validator("key")
    @classmethod
    def _key(cls, value):
        if not SLUG_RE.match(value):
            raise ValueError(f"key must be a lowercase slug: {value!r}")
        return value


class Reference(PackFileEntry):
    title: str = Field(min_length=1)
    stages: list[Stage] = Field(default_factory=lambda: ["drafter", "proofreader"], min_length=1)
    # Product keys this reference is for. Empty means every run.
    products: list[str] = Field(default_factory=list)
    # Deliverable paths or folders (ending in "/") this reference is for. Empty means all.
    applies_to: list[str] = Field(default_factory=list)

    @field_validator("applies_to")
    @classmethod
    def _prefixes(cls, value):
        return check_prefixes(value)


class ArticleSpec(PackFileEntry):
    type: str
    title: str | None = None
    # Deliverables that follow this spec. Empty means the Analyzer chooses where it applies.
    applies_to: list[str] = Field(default_factory=list)

    @field_validator("applies_to")
    @classmethod
    def _prefixes(cls, value):
        return check_prefixes(value)

    @field_validator("type")
    @classmethod
    def _type(cls, value):
        if not SLUG_RE.match(value):
            raise ValueError(f"type must be a lowercase slug: {value!r}")
        return value


def _regex(value: str, flags: int = 0) -> str:
    try:
        re.compile(value, flags)
    except re.error as exc:
        raise ValueError(f"invalid regular expression {value!r}: {exc}") from None
    return value


class StepBase(Strict):
    """A clean-up step: data the engine interprets. A pack never supplies code."""

    id: str
    description: str = Field(min_length=1)
    # Deliverable paths or folders this step runs on. Empty means all.
    applies_to: list[str] = Field(default_factory=list)
    # Deliverable paths or folders this step never runs on.
    skip: list[str] = Field(default_factory=list)
    # Optional documentation file inside the pack.
    path: str | None = None

    @field_validator("id")
    @classmethod
    def _id(cls, value):
        if not SLUG_RE.match(value):
            raise ValueError(f"id must be a lowercase slug: {value!r}")
        return value

    @field_validator("applies_to", "skip")
    @classmethod
    def _prefixes(cls, value):
        return check_prefixes(value)

    def runs_on(self, deliverable: str) -> bool:
        return applies(self.applies_to, deliverable) and not (self.skip and applies(self.skip, deliverable))

    @field_validator("path")
    @classmethod
    def _path(cls, value):
        return None if value is None else check_relative(value)


class ReplaceStep(StepBase):
    """Replace every match in prose. `replacement` may use \\1 group references."""

    kind: Literal["replace"]
    pattern: str
    replacement: str
    ignorecase: bool = False

    @field_validator("pattern")
    @classmethod
    def _pattern(cls, value):
        return _regex(value)


class DropSentencesStep(StepBase):
    """Remove every prose sentence that matches. Matches in code, and a table cell that is only the match, stay."""

    kind: Literal["drop_sentences"]
    pattern: str
    ignorecase: bool = False

    @field_validator("pattern")
    @classmethod
    def _pattern(cls, value):
        return _regex(value)


class LinkTemplate(Strict):
    subject: str = Field(min_length=1)
    line: str = Field(min_length=1)


class MarkerLinkStep(StepBase):
    """Turn markers such as [SUPPORT INQUIRY: phrase] into pre-filled mailto links.

    `pattern` needs the named groups `type` and `phrase`. `{phrase}` in a template is
    the cleaned phrase; `{line}` in `body` is the template's line.
    """

    kind: Literal["marker_link"]
    pattern: str
    address: str = Field(pattern=r"^[^@\s<>()]+@[^@\s<>()]+\.[A-Za-z]{2,}$")
    link_text: str | None = None
    templates: dict[str, LinkTemplate] = Field(min_length=1)
    default_type: str
    body: str = "{line}"

    @field_validator("pattern")
    @classmethod
    def _pattern(cls, value):
        _regex(value)
        groups = re.compile(value).groupindex
        if "type" not in groups or "phrase" not in groups:
            raise ValueError("marker_link pattern needs named groups 'type' and 'phrase'")
        return value

    @model_validator(mode="after")
    def _default(self):
        if self.default_type not in self.templates:
            raise ValueError(f"default_type {self.default_type!r} has no template")
        if "{line}" not in self.body:
            raise ValueError("body must contain {line}")
        return self


class MergeAlertsStep(StepBase):
    """Merge GitHub alerts of the same type that follow each other into one alert with a list."""

    kind: Literal["merge_alerts"]
    types: list[Literal["NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION"]] = Field(default_factory=list)


class MoveToTopStep(StepBase):
    """Move the first alert block whose text matches `match` to just below the page title."""

    kind: Literal["move_to_top"]
    match: str

    @field_validator("match")
    @classmethod
    def _match(cls, value):
        return _regex(value)


class CheckStep(StepBase):
    """Report matches in prose without changing anything."""

    kind: Literal["check"]
    pattern: str
    message: str = Field(min_length=1)
    ignorecase: bool = False
    # Report only matches that are not already link text.
    unless_linked: bool = False

    @field_validator("pattern")
    @classmethod
    def _pattern(cls, value):
        return _regex(value)


CleanupStep = Annotated[
    Union[ReplaceStep, DropSentencesStep, MarkerLinkStep, MergeAlertsStep, MoveToTopStep, CheckStep],
    Field(discriminator="kind"),
]


class ValeStyles(Strict):
    styles_path: str
    based_on: list[str] = Field(min_length=1)

    @field_validator("styles_path")
    @classmethod
    def _path(cls, value):
        return check_relative(value)

    @field_validator("based_on")
    @classmethod
    def _styles(cls, value):
        for name in value:
            if not STYLE_RE.match(name):
                raise ValueError(f"not a Vale style name: {name!r}")
        return value


class CaptureProfile(PackFileEntry):
    """Declared now; the profile format is defined with screenshot capture."""

    name: str

    @field_validator("name")
    @classmethod
    def _name(cls, value):
        if not SLUG_RE.match(value):
            raise ValueError(f"name must be a lowercase slug: {value!r}")
        return value


class FlowProfileSpec(Strict):
    """How this house's flow PDFs mark steps. `header` needs two groups: step number and total."""

    header: str = Field(min_length=1)
    noise: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _compiles(self):
        try:
            header = re.compile(self.header)
            for pattern in self.noise:
                re.compile(pattern)
        except re.error as exc:
            raise ValueError(f"flow_profile: invalid pattern: {exc}") from None
        if header.groups < 2:
            raise ValueError("flow_profile: header needs two groups (step number, total)")
        return self


PLACEMENT_FIELDS = ("product", "category", "slug", "month")
PLACEMENT_FIELD_RE = re.compile(r"\{([^{}]*)\}")


class Placement(Strict):
    """Where drafts go in the docs repository: a path template filled from the run's product key, the draft's
    front matter (`category`, `slug`, else a slug of `title`) and `month` (front matter `release_month`, else
    the month the pull request is prepared, as YYYY-MM)."""

    applies_to: list[str] = Field(min_length=1)
    path: str

    @field_validator("applies_to")
    @classmethod
    def _applies(cls, value):
        return check_prefixes(value)

    @field_validator("path")
    @classmethod
    def _path(cls, value):
        names = PLACEMENT_FIELD_RE.findall(value)
        unknown = sorted(set(names) - set(PLACEMENT_FIELDS))
        if unknown:
            raise ValueError(f"placement path: unknown field(s) {', '.join(unknown)}; use {', '.join(PLACEMENT_FIELDS)}")
        if "slug" not in names:
            raise ValueError(f"placement path needs {{slug}} so pages do not collide: {value!r}")
        if not value.endswith(".md"):
            raise ValueError(f"placement path must end in .md: {value!r}")
        check_relative(PLACEMENT_FIELD_RE.sub("x", value))
        return value


class PackManifest(Strict):
    schema_version: Literal[1]
    name: str
    version: str
    description: str = ""
    conventions: str | None = None
    products: list[Product] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)
    article_specs: list[ArticleSpec] = Field(default_factory=list)
    cleanup_steps: list[CleanupStep] = Field(default_factory=list)
    vale: ValeStyles | None = None
    capture_profiles: list[CaptureProfile] = Field(default_factory=list)
    flow_profile: FlowProfileSpec | None = None
    placement: list[Placement] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def _name(cls, value):
        if not SLUG_RE.match(value):
            raise ValueError(f"name must be a lowercase slug: {value!r}")
        return value

    @field_validator("version")
    @classmethod
    def _version(cls, value):
        if not VERSION_RE.match(value):
            raise ValueError(f"version must look like 1.2.3: {value!r}")
        return value

    @field_validator("conventions")
    @classmethod
    def _conventions(cls, value):
        return None if value is None else check_relative(value)

    @model_validator(mode="after")
    def _unique(self):
        for label, values in (("article_specs type", [s.type for s in self.article_specs]),
                              ("cleanup_steps id", [s.id for s in self.cleanup_steps]),
                              ("capture_profiles name", [c.name for c in self.capture_profiles]),
                              ("references path", [r.path for r in self.references]),
                              ("products key", [p.key for p in self.products])):
            dupes = sorted({v for v in values if values.count(v) > 1})
            if dupes:
                raise ValueError(f"duplicate {label}: {', '.join(dupes)}")
        keys = {p.key for p in self.products}
        for ref in self.references:
            unknown = sorted(set(ref.products) - keys)
            if unknown:
                raise ValueError(f"references {ref.path}: unknown product(s) {', '.join(unknown)}")
        if self.vale:
            for name in self.vale.based_on:
                if name in RESERVED_STYLES:
                    raise ValueError(f"vale: style name {name} is reserved by DocForge")
        return self


def applies(prefixes: list[str], deliverable: str) -> bool:
    """True if a deliverable path matches any entry (a folder ending in '/' or an exact path). Empty matches all."""
    return not prefixes or any(deliverable.startswith(p) if p.endswith("/") else deliverable == p for p in prefixes)
