"""Fetch past pull requests with the GitHub CLI, read-only.

Each PR becomes a recorded webhook-style event (closing event for closed PRs,
opening event for open ones) plus its diff, saved in a new evaluation folder.
Only `gh api` GET requests are made; nothing is posted.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
GH_TIMEOUT_SECONDS = 60


class BackfillError(Exception):
    """Raised when a backfill step cannot run."""


def find_gh() -> str | None:
    override = os.environ.get("DOCFORGE_GH")
    if override:
        return override if Path(override).is_file() else None
    found = shutil.which("gh")
    if found:
        return found
    local = Path.home() / ".local" / "bin" / "gh"
    return str(local) if local.is_file() else None


def _gh(binary: str, *args: str) -> str:
    try:
        result = subprocess.run([binary, "api", *args], capture_output=True, text=True,
                                timeout=GH_TIMEOUT_SECONDS, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise BackfillError(f"gh failed: {exc}") from None
    if result.returncode != 0:
        message = (result.stderr or result.stdout).strip().splitlines()
        raise BackfillError(f"gh api {args[0]} failed: {message[-1] if message else 'unknown error'}")
    return result.stdout


def _event(pr: dict, repo: dict) -> dict:
    closed = pr.get("state") == "closed"
    pull = {
        "number": pr["number"], "state": pr.get("state"), "title": pr.get("title", ""), "draft": bool(pr.get("draft")),
        "merged": bool(pr.get("merged_at")), "user": {"login": (pr.get("user") or {}).get("login", "")},
        "base": {"ref": pr["base"]["ref"], "sha": pr["base"]["sha"]},
        "head": {"ref": pr["head"]["ref"], "sha": pr["head"]["sha"]},
    }
    return {
        "action": "closed" if closed else "opened",
        "number": pr["number"],
        "pull_request": pull,
        "repository": {"full_name": repo["full_name"], "owner": {"login": repo["owner"]["login"]},
                       "topics": repo.get("topics") or []},
    }


def fetch_prs(repo: str, out: Path, *, state: str = "closed", limit: int = 30) -> dict:
    """Save up to `limit` PRs of `repo` as events and diffs in the new folder `out`."""
    if not REPO_RE.match(repo):
        raise BackfillError(f"repo must be owner/repo: {repo!r}")
    if state not in ("open", "closed", "all"):
        raise BackfillError("state must be open, closed or all")
    if not 1 <= limit <= 100:
        raise BackfillError("limit must be between 1 and 100")
    if out.exists():
        raise BackfillError(f"{out} already exists; choose a new evaluation folder")
    binary = find_gh()
    if binary is None:
        raise BackfillError("the GitHub CLI (gh) is needed; install it or set DOCFORGE_GH")
    try:
        repo_info = json.loads(_gh(binary, f"repos/{repo}"))
        pulls = json.loads(_gh(binary, f"repos/{repo}/pulls?state={state}&per_page={limit}&sort=created&direction=asc"))
    except ValueError as exc:
        raise BackfillError(f"gh returned something that is not JSON: {exc}") from None
    if not isinstance(pulls, list):
        raise BackfillError("gh did not return a list of pull requests")

    (out / "events").mkdir(parents=True)
    (out / "diffs").mkdir()
    records = []
    for pr in pulls[:limit]:
        number = pr["number"]
        diff = _gh(binary, f"repos/{repo}/pulls/{number}", "-H", "Accept: application/vnd.github.diff")
        (out / "events" / f"{number}.json").write_text(json.dumps(_event(pr, repo_info), indent=2) + "\n",
                                                      encoding="utf-8")
        (out / "diffs" / f"{number}.diff").write_text(diff, encoding="utf-8")
        records.append({"number": number, "title": pr.get("title", ""), "author": (pr.get("user") or {}).get("login"),
                        "state": pr.get("state"), "merged": bool(pr.get("merged_at")), "draft": bool(pr.get("draft"))})
    manifest = {"repo": repo, "state": state, "fetched_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                "prs": records}
    (out / "fetch.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
