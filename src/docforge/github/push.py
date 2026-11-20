"""Push a DocForge suggestion branch, and nothing else.

- Only branches under `docforge/` are pushed, to the same name, never forced (no `+` in the refspec), so a
  branch someone else moved is refused by Git instead of overwritten.
- The local branch tip must be the commit DocForge recorded, so unreviewed local commits never travel.
- The token reaches Git through a short askpass helper that reads it from the child's environment; it is
  never in the command line, the URL, a file or an error message. Stored credential helpers are switched
  off for the push, so the push uses that token only.
- A `file:///` URL (a local bare repository, for tests and demos) needs no token.
"""

from __future__ import annotations

import os
from pathlib import Path
import stat
import subprocess
import tempfile

from docforge.publish.branch import BRANCH_PREFIX, GIT_TIMEOUT_SECONDS, PublishError

ASKPASS = """#!/bin/sh
case "$1" in
  Username*) echo x-access-token ;;
  *) printf '%s\\n' "$DOCFORGE_PUSH_TOKEN" ;;
esac
"""


def _scrub(text: str, token: str | None) -> str:
    return text.replace(token, "***") if token else text


def _git_env(tmp: str, local: bool, token: str | None) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_TERMINAL_PROMPT"] = "0"
    if not local:
        helper = Path(tmp) / "askpass.sh"
        helper.write_text(ASKPASS, encoding="utf-8")
        helper.chmod(stat.S_IRWXU)
        env["GIT_ASKPASS"] = str(helper)
        env["DOCFORGE_PUSH_TOKEN"] = token
    return env


def fetch_branch(checkout: Path, branch: str, git_url: str, token: str | None) -> str:
    """Fetch a DocForge branch from the remote into refs/docforge-remote/<branch>; return its tip commit.

    Reads only: the checkout's branches, index and working tree are not changed."""
    if not branch.startswith(BRANCH_PREFIX) or ".." in branch:
        raise PublishError(f"only DocForge branches ({BRANCH_PREFIX}...) are fetched: {branch!r}")
    local = git_url.startswith("file:///")
    if not local and not token:
        raise PublishError("no GitHub token: cannot fetch")
    ref = f"refs/docforge-remote/{branch}"
    with tempfile.TemporaryDirectory(prefix="docforge-fetch-") as tmp:
        try:
            result = subprocess.run(
                ["git", "-C", str(checkout), "-c", "credential.helper=", "fetch", "--quiet", "--no-tags", git_url,
                 f"+refs/heads/{branch}:{ref}"], capture_output=True, text=True, timeout=GIT_TIMEOUT_SECONDS * 2,
                check=False, env=_git_env(tmp, local, token))
        except (OSError, subprocess.SubprocessError) as exc:
            raise PublishError(f"git fetch failed: {type(exc).__name__}") from None
    if result.returncode != 0:
        lines = _scrub((result.stderr or result.stdout).strip(), token).splitlines()
        raise PublishError(f"git fetch of {branch} failed: {lines[-1] if lines else 'unknown error'}")
    tip = subprocess.run(["git", "-C", str(checkout), "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
                         capture_output=True, text=True, timeout=GIT_TIMEOUT_SECONDS, check=False).stdout.strip()
    if not tip:
        raise PublishError(f"branch {branch} was not found on the remote")
    return tip


def show_file(checkout: Path, commit: str, path: str) -> str:
    """The text of `path` at `commit` in the checkout (the commit must have been fetched)."""
    result = subprocess.run(["git", "-C", str(checkout), "show", f"{commit}:{path}"], capture_output=True, text=True,
                            timeout=GIT_TIMEOUT_SECONDS, check=False)
    if result.returncode != 0:
        raise PublishError(f"{path} is not in commit {commit[:12]}")
    return result.stdout


def is_ancestor(checkout: Path, older: str, newer: str) -> bool:
    return subprocess.run(["git", "-C", str(checkout), "merge-base", "--is-ancestor", older, newer],
                          capture_output=True, timeout=GIT_TIMEOUT_SECONDS, check=False).returncode == 0


def push_branch(checkout: Path, branch: str, expected_commit: str, git_url: str, token: str | None) -> None:
    if not branch.startswith(BRANCH_PREFIX) or ".." in branch or branch.endswith("/"):
        raise PublishError(f"only DocForge branches ({BRANCH_PREFIX}...) are pushed: {branch!r}")
    local = git_url.startswith("file:///")
    if not local and not token:
        raise PublishError("no GitHub token: cannot push")
    try:
        tip = subprocess.run(["git", "-C", str(checkout), "rev-parse", "--verify", "--quiet",
                              f"refs/heads/{branch}^{{commit}}"], capture_output=True, text=True,
                             timeout=GIT_TIMEOUT_SECONDS, check=False).stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        raise PublishError(f"git rev-parse failed: {type(exc).__name__}") from None
    if not tip:
        raise PublishError(f"branch {branch} is not in the docs checkout")
    if tip != expected_commit:
        raise PublishError(f"branch {branch} has commits DocForge did not record ({tip[:12]} is not "
                           f"{expected_commit[:12]}); nothing was pushed")
    with tempfile.TemporaryDirectory(prefix="docforge-push-") as tmp:
        env = _git_env(tmp, local, token)
        command = ["git", "-C", str(checkout), "-c", "credential.helper=", "push", "--porcelain", git_url,
                   f"refs/heads/{branch}:refs/heads/{branch}"]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=GIT_TIMEOUT_SECONDS * 2,
                                    check=False, env=env)
        except (OSError, subprocess.SubprocessError) as exc:
            raise PublishError(f"git push failed: {type(exc).__name__}") from None
    if result.returncode != 0:
        lines = _scrub((result.stderr or result.stdout).strip(), token).splitlines()
        reason = next((l for l in lines if "rejected" in l or "error" in l.lower()), lines[-1] if lines else "unknown")
        raise PublishError(f"git push of {branch} failed: {reason.strip()}")
