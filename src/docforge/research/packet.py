"""Prepare a pull request's changed code for the research stage.

`build_packet` lists every changed hunk with its text and a ready-made code
citation (repo, commit, path, lines, excerpt_sha256) that verifies with the
evidence core. Added lines are cited at the head commit; removed lines at the
base commit. `code_ref` makes the same citation for any lines. Read-only.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Literal

from pydantic import BaseModel, Field

from docforge.evidence.code import CodeReadError, excerpt_sha256, read_file_at_commit, resolve_commit
from docforge.evidence.models import parse_line_range
from docforge.sources import DiffError, git_diff

REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class ResearchError(Exception):
    """Raised when research inputs cannot be prepared or checked."""


class CodeRef(BaseModel):
    """A code citation in the shape evidence.json and claims.json use."""

    repo: str
    commit: str
    path: str
    lines: str
    excerpt_sha256: str


class Hunk(BaseModel):
    path: str
    side: Literal["added", "removed"]
    ref: CodeRef
    text: str


class ChangedFileSummary(BaseModel):
    path: str
    old_path: str | None = None
    status: str
    binary: bool = False
    additions: int = 0
    deletions: int = 0


class Packet(BaseModel):
    repo: str
    base: str
    head: str
    files: list[ChangedFileSummary]
    hunks: list[Hunk]
    notes: list[str] = Field(default_factory=list)


def _lines_label(first: int, last: int) -> str:
    return f"L{first}" if first == last else f"L{first}-L{last}"


def code_ref(checkout: Path, repo: str, commit: str, path: str, lines: str) -> CodeRef:
    """A verified code citation for `lines` of `path` at `commit`."""
    if not REPO_RE.match(repo):
        raise ResearchError(f"repo must be owner/repo: {repo!r}")
    line_range = parse_line_range(lines)
    if line_range is None:
        raise ResearchError(f"lines must look like L10 or L10-L24: {lines!r}")
    try:
        full = resolve_commit(checkout, commit)
        text = read_file_at_commit(checkout, full, path)
    except CodeReadError as exc:
        raise ResearchError(str(exc)) from None
    first, last = line_range
    file_lines = text.splitlines()
    if last > len(file_lines) or not any(l.strip() for l in file_lines[first - 1 : last]):
        raise ResearchError(f"lines {lines} of {path} are out of range or blank")
    return CodeRef(repo=repo, commit=full, path=path, lines=_lines_label(first, last),
                   excerpt_sha256=excerpt_sha256(text, first, last))


def build_packet(checkout: Path, repo: str, base: str, head: str) -> Packet:
    if not REPO_RE.match(repo):
        raise ResearchError(f"repo must be owner/repo: {repo!r}")
    try:
        base_sha, head_sha = resolve_commit(checkout, base), resolve_commit(checkout, head)
        changed = git_diff(checkout, base_sha, head_sha)
    except (CodeReadError, DiffError) as exc:
        raise ResearchError(str(exc)) from None

    hunks: list[Hunk] = []
    notes: list[str] = []
    for f in changed:
        if f.binary:
            notes.append(f"{f.path}: binary file, not cited")
            continue
        sides = (("added", head_sha, f.path, f.added_ranges), ("removed", base_sha, f.old_path or f.path, f.removed_ranges))
        for side, commit, path, ranges in sides:
            if not ranges:
                continue
            text = read_file_at_commit(checkout, commit, path)
            lines = text.splitlines()
            for first, last in ranges:
                if not any(l.strip() for l in lines[first - 1 : last]):
                    continue  # blank-only change; nothing to cite
                ref = CodeRef(repo=repo, commit=commit, path=path, lines=_lines_label(first, last),
                              excerpt_sha256=excerpt_sha256(text, first, last))
                hunks.append(Hunk(path=path, side=side, ref=ref, text="\n".join(lines[first - 1 : last])))
    return Packet(
        repo=repo, base=base_sha, head=head_sha,
        files=[ChangedFileSummary(**f.model_dump(include={"path", "old_path", "status", "binary", "additions",
                                                          "deletions"})) for f in changed],
        hunks=hunks,
        notes=notes,
    )
