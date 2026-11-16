from pathlib import Path
import subprocess

import pytest

from docforge.sources import DiffError, changes_for_event, git_diff, parse_unified_diff, read_diff_file

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "github"


def by_path(files):
    return {f.path: f for f in files}


def test_product_change_diff():
    files = by_path(read_diff_file(FIXTURES / "product_change.diff"))
    assert list(files) == ["src/settings/quiet_hours.py", "src/settings/panel.py", "tests/test_quiet_hours.py"]

    new = files["src/settings/quiet_hours.py"]
    assert (new.status, new.additions, new.deletions, new.added_ranges) == ("added", 4, 0, [(1, 4)])

    panel = files["src/settings/panel.py"]
    assert (panel.status, panel.additions, panel.deletions) == ("modified", 3, 3)
    # Hunk 1 replaces new lines 13-14; hunk 2 removes old lines 40-41 and adds new line 41.
    assert panel.added_ranges == [(13, 14), (41, 41)]
    assert panel.removed_ranges == [(13, 13), (40, 41)]


def test_rename_and_binary():
    files = by_path(read_diff_file(FIXTURES / "rename_and_binary.diff"))
    renamed = files["src/new_name.py"]
    assert (renamed.status, renamed.old_path, renamed.additions, renamed.deletions) == (
        "renamed", "src/old_name.py", 1, 1)
    logo = files["assets/logo.png"]
    assert (logo.status, logo.binary, logo.additions) == ("deleted", True, 0)


def test_empty_diff():
    assert parse_unified_diff("") == []


def test_missing_diff_file():
    with pytest.raises(DiffError, match="cannot read diff"):
        read_diff_file(FIXTURES / "nope.diff")


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=Test", "-c", "user.email=test@example.com",
         "-c", "commit.gpgsign=false", *args],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


@pytest.fixture
def checkout(tmp_path):
    root = tmp_path / "product-web"
    (root / "src").mkdir(parents=True)
    git(root, "init", "-q")
    (root / "src" / "app.py").write_text("A = 1\nB = 2\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "base")
    base = git(root, "rev-parse", "HEAD")
    (root / "src" / "app.py").write_text("A = 1\nB = 3\nC = 4\n", encoding="utf-8")
    (root / ".editorconfig").write_text("root = true\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "head")
    return root, base, git(root, "rev-parse", "HEAD")


def test_git_diff_in_local_checkout(checkout):
    root, base, head = checkout
    files = by_path(git_diff(root, base, head))
    assert set(files) == {".editorconfig", "src/app.py"}
    app = files["src/app.py"]
    assert (app.additions, app.deletions, app.added_ranges) == (2, 1, [(2, 3)])


def test_git_diff_rejects_non_sha_refs(checkout):
    root, base, _ = checkout
    with pytest.raises(DiffError, match="expected a commit SHA"):
        git_diff(root, base, "--output=/tmp/x")


def test_git_diff_unknown_commit(checkout):
    root, base, _ = checkout
    with pytest.raises(DiffError, match="git diff failed"):
        git_diff(root, base, "f" * 40)


def test_changes_for_event_sources(checkout):
    root, base, head = checkout
    assert changes_for_event(base, head) == (None, None)
    files, label = changes_for_event(base, head, diff_file=FIXTURES / "dotfiles_only.diff")
    assert (len(files), label) == (2, "diff file dotfiles_only.diff")
    files, label = changes_for_event(base, head, checkout=root)
    assert label == f"git diff {base[:12]}...{head[:12]}"
    assert len(files) == 2
