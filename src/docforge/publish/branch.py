"""Create a suggestion branch in a local docs checkout without touching it.

The commit is built with Git plumbing in a temporary index: the checkout's
working tree, index and current branch are never changed. The branch is only
created locally; nothing is pushed or fetched.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile

from pydantic import BaseModel

BRANCH_PREFIX = "docforge/"
ZERO_SHA = "0" * 40
GIT_TIMEOUT_SECONDS = 60


class PublishError(Exception):
    """Raised when a suggestion branch or pull request cannot be prepared."""


class FileChange(BaseModel):
    path: str
    change: str  # added, modified


class BranchResult(BaseModel):
    branch: str
    base_ref: str
    base_commit: str
    commit: str
    changes: list[FileChange]


def _git(root: Path, *args: str, env: dict | None = None) -> str:
    try:
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                                timeout=GIT_TIMEOUT_SECONDS, check=False, env=env)
    except (OSError, subprocess.SubprocessError) as exc:
        raise PublishError(f"git {args[0]} failed: {exc}") from None
    if result.returncode != 0:
        message = (result.stderr or result.stdout).strip().splitlines()
        raise PublishError(f"git {args[0]} failed: {message[-1] if message else 'unknown error'}")
    return result.stdout.strip()


def _exists(root: Path, *args: str) -> bool:
    try:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                              timeout=GIT_TIMEOUT_SECONDS, check=False).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def resolve_base(root: Path, base: str) -> tuple[str, str]:
    """(ref used, commit SHA): prefer origin/<base>, then <base>."""
    for ref in (f"refs/remotes/origin/{base}", f"refs/heads/{base}"):
        if _exists(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"):
            return ref, _git(root, "rev-parse", f"{ref}^{{commit}}")
    raise PublishError(f"base branch {base!r} not found locally (checked origin/{base} and {base})")


def create_branch(root: Path, branch: str, base: str, files: list[tuple[Path, str]], message: str) -> BranchResult:
    """Commit `files` (source path, repo-relative destination) on a new branch from `base`."""
    if not branch.startswith(BRANCH_PREFIX):
        raise PublishError(f"suggestion branches must start with {BRANCH_PREFIX!r}")
    if not _exists(root, "rev-parse", "--git-dir"):
        raise PublishError(f"not a Git checkout: {root}")
    if not _exists(root, "check-ref-format", "--branch", branch):
        raise PublishError(f"invalid branch name: {branch}")
    if _exists(root, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"):
        raise PublishError(f"branch {branch} already exists; DocForge never reuses a branch")
    if not files:
        raise PublishError("nothing to commit")
    base_ref, base_commit = resolve_base(root, base)

    changes: list[FileChange] = []
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(tmp) / "index")}
        _git(root, "read-tree", base_commit, env=env)
        for source, dest in files:
            blob = _git(root, "hash-object", "-w", "--", str(source))
            existed = _exists(root, "cat-file", "-e", f"{base_commit}:{dest}")
            _git(root, "update-index", "--add", "--cacheinfo", f"100644,{blob},{dest}", env=env)
            changes.append(FileChange(path=dest, change="modified" if existed else "added"))
        tree = _git(root, "write-tree", env=env)
    if tree == _git(root, "rev-parse", f"{base_commit}^{{tree}}"):
        raise PublishError(f"the files are identical to {base}; nothing to propose")
    commit = _git(root, "commit-tree", tree, "-p", base_commit, "-m", message)
    # Creating with an all-zero old value fails if the branch appeared meanwhile.
    _git(root, "update-ref", f"refs/heads/{branch}", commit, ZERO_SHA)
    return BranchResult(branch=branch, base_ref=base_ref, base_commit=base_commit, commit=commit, changes=changes)


def update_branch(root: Path, branch: str, expected_tip: str, files: list[tuple[Path, str]], message: str) -> BranchResult:
    """Add a follow-up commit on `branch`, only if its tip is still `expected_tip`."""
    if not branch.startswith(BRANCH_PREFIX):
        raise PublishError(f"suggestion branches must start with {BRANCH_PREFIX!r}")
    if not _exists(root, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"):
        raise PublishError(f"branch {branch} not found in {root}")
    tip = _git(root, "rev-parse", f"refs/heads/{branch}")
    if tip != expected_tip:
        raise PublishError(f"branch {branch} moved since DocForge last committed ({tip[:12]} != {expected_tip[:12]}); "
                           "reconcile it by hand")
    changes: list[FileChange] = []
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(tmp) / "index")}
        _git(root, "read-tree", tip, env=env)
        for source, dest in files:
            blob = _git(root, "hash-object", "-w", "--", str(source))
            existed = _exists(root, "cat-file", "-e", f"{tip}:{dest}")
            _git(root, "update-index", "--add", "--cacheinfo", f"100644,{blob},{dest}", env=env)
            changes.append(FileChange(path=dest, change="modified" if existed else "added"))
        tree = _git(root, "write-tree", env=env)
    if tree == _git(root, "rev-parse", f"{tip}^{{tree}}"):
        raise PublishError("nothing changed since the last suggestion commit")
    commit = _git(root, "commit-tree", tree, "-p", tip, "-m", message)
    _git(root, "update-ref", f"refs/heads/{branch}", commit, tip)
    return BranchResult(branch=branch, base_ref=f"refs/heads/{branch}", base_commit=tip, commit=commit, changes=changes)


def diff_commits(root: Path, base: str, head: str) -> str:
    """Unified diff of the files changed between two commits."""
    return _git(root, "diff", "--no-color", "--no-ext-diff", f"{base}..{head}") + "\n"
