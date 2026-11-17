"""Shared fixtures: a made-up product repo with a base and a head commit."""

import json
from pathlib import Path
import shutil
import subprocess

import pytest

RESEARCH = Path(__file__).resolve().parent / "fixtures" / "research"
CODE_REPO = "example-org/pulseboard-web"


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=Test", "-c", "user.email=test@example.com",
         "-c", "commit.gpgsign=false", *args],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def _commit_tree(root: Path, tree: Path, message: str) -> str:
    for item in root.iterdir():
        if item.name != ".git":
            shutil.rmtree(item) if item.is_dir() else item.unlink()
    shutil.copytree(tree, root, dirs_exist_ok=True)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message)
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def research_repo(tmp_path):
    """(checkout path, base SHA, head SHA) for example-org/pulseboard-web."""
    root = tmp_path / "pulseboard-web"
    root.mkdir()
    git(root, "init", "-q")
    base = _commit_tree(root, RESEARCH / "base", "base")
    head = _commit_tree(root, RESEARCH / "head", "Add Quiet Hours")
    return root, base, head


def materialize_claims(root: Path, head: str) -> dict:
    """claims.template.json with each code entry's commit and excerpt hash filled in."""
    from docforge.research import code_ref

    data = json.loads((RESEARCH / "claims.template.json").read_text(encoding="utf-8"))
    data.pop("_comment", None)
    for claim in data["claims"]:
        for entry in claim.get("code", []):
            ref = code_ref(root, CODE_REPO, head, entry["path"], entry["lines"])
            entry.update(repo=ref.repo, commit=ref.commit, lines=ref.lines, excerpt_sha256=ref.excerpt_sha256)
    return data


@pytest.fixture(autouse=True)
def isolated_rules(tmp_path, monkeypatch):
    """Every test sees an empty learned-rules folder unless it sets one up."""
    folder = tmp_path / "learned-rules"
    monkeypatch.setenv("DOCFORGE_RULES_DIR", str(folder))
    return folder
