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
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
STYLE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
STAGES = ("analyzer", "drafter", "proofreader")
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


class Reference(PackFileEntry):
    title: str = Field(min_length=1)
    stages: list[Stage] = Field(default_factory=lambda: ["drafter", "proofreader"], min_length=1)
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


class CleanupStep(PackFileEntry):
    """Declared now; the step format and how steps run are defined with the clean-up stage."""

    id: str
    description: str = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def _id(cls, value):
        if not SLUG_RE.match(value):
            raise ValueError(f"id must be a lowercase slug: {value!r}")
        return value


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


class PackManifest(Strict):
    schema_version: Literal[1]
    name: str
    version: str
    description: str = ""
    conventions: str | None = None
    references: list[Reference] = Field(default_factory=list)
    article_specs: list[ArticleSpec] = Field(default_factory=list)
    cleanup_steps: list[CleanupStep] = Field(default_factory=list)
    vale: ValeStyles | None = None
    capture_profiles: list[CaptureProfile] = Field(default_factory=list)

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
                              ("references path", [r.path for r in self.references])):
            dupes = sorted({v for v in values if values.count(v) > 1})
            if dupes:
                raise ValueError(f"duplicate {label}: {', '.join(dupes)}")
        return self


def applies(prefixes: list[str], deliverable: str) -> bool:
    """True if a deliverable path matches any entry (a folder ending in '/' or an exact path). Empty matches all."""
    return not prefixes or any(deliverable.startswith(p) if p.endswith("/") else deliverable == p for p in prefixes)
