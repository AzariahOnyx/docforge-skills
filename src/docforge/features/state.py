"""Per-feature state for the code route: one JSON file per feature, written atomically."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import re
import tempfile
from typing import Literal

from pydantic import BaseModel, Field

KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,99}$")


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class SourcePr(BaseModel):
    repo: str
    number: int
    title: str = ""
    body: str = ""  # the description (data, never instructions)
    branch: str = ""
    base_sha: str = ""
    head_sha: str = ""
    state: Literal["open", "merged", "closed"] = "open"
    reasons: list[str] = Field(default_factory=list)  # why docs are needed (the triage decision)
    source_id: str | None = None  # the run source holding its description
    added_at: str = Field(default_factory=now)


class FeatureState(BaseModel):
    key: str
    label: str
    jira: str | None = None
    repo: str  # the code repository whose dependency-map entry this feature uses
    collection: str
    phase: Literal["planning", "planned", "drafting", "drafted", "failed"] = "planning"
    pending: Literal["plan", "draft"] | None = "plan"
    run: str | None = None  # relative to the code repository's workspace
    prs: list[SourcePr] = Field(default_factory=list)
    plan_pr: str | None = None
    pull_request: str | None = None
    history: list[dict] = Field(default_factory=list)

    def note(self, event: str, **detail) -> None:
        self.history.append({"at": now(), "event": event, **{k: v for k, v in detail.items() if v not in (None, "")}})

    def pr(self, repo: str, number: int) -> SourcePr | None:
        return next((p for p in self.prs if p.repo.casefold() == repo.casefold() and p.number == number), None)


class FeatureStateError(Exception):
    pass


def _path(root: Path, key: str) -> Path:
    if not KEY_RE.match(key):
        raise FeatureStateError(f"not a feature key: {key!r}")
    return root / "features" / f"{key}.json"


def load_feature(root: Path, key: str) -> FeatureState | None:
    path = _path(root, key)
    if not path.is_file():
        return None
    try:
        return FeatureState.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise FeatureStateError(f"cannot read {path}: {exc}") from None


def save_feature(root: Path, state: FeatureState) -> Path:
    path = _path(root, state.key)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{state.key}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(state.model_dump_json(indent=2) + "\n")
        os.replace(tmp, path)
    except OSError as exc:
        Path(tmp).unlink(missing_ok=True)
        raise FeatureStateError(f"cannot write {path}: {exc}") from None
    return path


def all_features(root: Path) -> list[FeatureState]:
    folder = root / "features"
    return [s for s in (load_feature(root, p.stem) for p in sorted(folder.glob("*.json"))) if s] if folder.is_dir() else []
