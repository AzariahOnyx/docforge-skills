"""Verify code evidence against a local Git checkout.

Read-only and offline: runs `git cat-file` and `git show` in a checkout the
user supplies. Never fetches, checks out, or writes anything.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess

from .models import CodeEvidence

GIT_TIMEOUT_SECONDS = 30


def excerpt_sha256(text: str, start_line: int, end_line: int) -> str:
    """SHA-256 of the cited lines joined with "\\n" (no trailing newline)."""
    lines = text.splitlines()[start_line - 1 : end_line]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        timeout=GIT_TIMEOUT_SECONDS,
        check=False,
    )


def is_git_checkout(root: Path) -> bool:
    try:
        return root.is_dir() and _git(root, "rev-parse", "--git-dir").returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def verify_code_evidence(evidence: CodeEvidence, root: Path) -> list[str]:
    """Return errors for one code evidence row checked against `root`."""
    cid, short = evidence.claim_id, evidence.commit[:12]
    try:
        # Commit and path were validated by the parser: a 40-hex SHA and a
        # relative path, so neither can be read as a git option.
        if _git(root, "cat-file", "-e", f"{evidence.commit}^{{commit}}").returncode != 0:
            return [f"{cid}: commit {short} not found in local checkout of {evidence.repo}"]
        shown = _git(root, "show", f"{evidence.commit}:{evidence.path}")
    except (OSError, subprocess.SubprocessError) as exc:
        return [f"{cid}: could not read local checkout of {evidence.repo}: {exc}"]
    if shown.returncode != 0:
        return [f"{cid}: {evidence.path} does not exist at commit {short}"]
    try:
        text = shown.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return [f"{cid}: {evidence.path} at commit {short} is not UTF-8 text"]
    lines = text.splitlines()
    if evidence.end_line > len(lines) or not any(
        line.strip() for line in lines[evidence.start_line - 1 : evidence.end_line]
    ):
        return [f"{cid}: invalid or blank code lines {evidence.lines} in {evidence.path}"]
    if excerpt_sha256(text, evidence.start_line, evidence.end_line) != evidence.excerpt_sha256:
        return [f"{cid}: code excerpt hash mismatch for {evidence.path} {evidence.lines}"]
    return []
