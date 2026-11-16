"""Read a pull request's changes from a unified diff.

The diff comes from a saved `.diff` file or from `git diff base...head` in a
local checkout. Read-only: never fetches, checks out or writes.
"""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
from typing import Literal

from pydantic import BaseModel, Field

FileStatus = Literal["added", "modified", "deleted", "renamed"]
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
GIT_REF_RE = re.compile(r"[0-9a-f]{7,40}")
GIT_TIMEOUT_SECONDS = 60


class DiffError(Exception):
    """Raised when a diff cannot be read."""


class ChangedFile(BaseModel):
    path: str
    old_path: str | None = None
    status: FileStatus = "modified"
    binary: bool = False
    additions: int = 0
    deletions: int = 0
    # Line ranges (first, last) in the new file for added lines, and in the old file for removed lines.
    added_ranges: list[tuple[int, int]] = Field(default_factory=list)
    removed_ranges: list[tuple[int, int]] = Field(default_factory=list)


def _strip_prefix(path: str) -> str:
    if path.startswith('"') and path.endswith('"'):
        path = path[1:-1].encode("utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8")
    return path[2:] if path[:2] in ("a/", "b/") else path


def _add(ranges: list[tuple[int, int]], line: int) -> None:
    if ranges and ranges[-1][1] == line - 1:
        ranges[-1] = (ranges[-1][0], line)
    else:
        ranges.append((line, line))


def parse_unified_diff(text: str) -> list[ChangedFile]:
    files: list[ChangedFile] = []
    current: ChangedFile | None = None
    old_line = new_line = 0
    in_hunk = False
    for raw in text.splitlines():
        if raw.startswith("diff --git "):
            parts = raw[len("diff --git "):].split(" b/", 1)
            path = parts[1] if len(parts) == 2 else _strip_prefix(raw.split()[-1])
            current = ChangedFile(path=path)
            files.append(current)
            in_hunk = False
            continue
        if current is None:
            continue
        if raw.startswith("new file mode"):
            current.status = "added"
        elif raw.startswith("deleted file mode"):
            current.status = "deleted"
        elif raw.startswith("rename from "):
            current.old_path = raw[len("rename from "):]
            current.status = "renamed"
        elif raw.startswith("rename to "):
            current.path = raw[len("rename to "):]
        elif raw.startswith("Binary files ") or raw == "GIT binary patch":
            current.binary = True
        elif raw.startswith("--- ") and not in_hunk:
            pass  # the old path is known from "diff --git" or "rename from"
        elif raw.startswith("+++ ") and not in_hunk:
            new = raw[4:].split("\t", 1)[0]
            if new != "/dev/null":
                current.path = _strip_prefix(new)
        elif (match := HUNK_RE.match(raw)):
            old_line, new_line = int(match.group(1)), int(match.group(3))
            in_hunk = True
        elif in_hunk:
            if raw.startswith("+"):
                current.additions += 1
                _add(current.added_ranges, new_line)
                new_line += 1
            elif raw.startswith("-"):
                current.deletions += 1
                _add(current.removed_ranges, old_line)
                old_line += 1
            elif raw.startswith(" ") or raw == "":
                old_line += 1
                new_line += 1
            # "\ No newline at end of file" and anything else: no line movement.
    return files


def read_diff_file(path: Path) -> list[ChangedFile]:
    try:
        return parse_unified_diff(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        raise DiffError(f"cannot read diff {path}: {exc}") from None


def git_diff(checkout: Path, base: str, head: str) -> list[ChangedFile]:
    """Changes between `base` and `head` (merge-base diff) in a local checkout."""
    for ref in (base, head):
        if not GIT_REF_RE.fullmatch(ref or ""):
            raise DiffError(f"expected a commit SHA (7-40 lowercase hex), got {ref!r}")
    try:
        result = subprocess.run(
            ["git", "-C", str(checkout), "diff", "--no-color", "--no-ext-diff", "-M", f"{base}...{head}"],
            capture_output=True, timeout=GIT_TIMEOUT_SECONDS, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise DiffError(f"git diff failed: {exc}") from None
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", "replace").strip().splitlines()
        raise DiffError(f"git diff failed: {message[-1] if message else 'unknown error'}")
    return parse_unified_diff(result.stdout.decode("utf-8", "replace"))


def changes_for_event(
    base_sha: str, head_sha: str, *, diff_file: Path | None = None, checkout: Path | None = None
) -> tuple[list[ChangedFile] | None, str | None]:
    """Changed files from a saved diff or a local checkout, plus a label for the source.

    Returns (None, None) when neither is given. Raises DiffError when the source cannot be read.
    """
    if diff_file is not None:
        return read_diff_file(diff_file), f"diff file {diff_file.name}"
    if checkout is not None:
        return git_diff(checkout, base_sha, head_sha), f"git diff {base_sha[:12]}...{head_sha[:12]}"
    return None, None
