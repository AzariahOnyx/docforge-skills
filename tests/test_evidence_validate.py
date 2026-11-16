import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from docforge.evidence import excerpt_sha256, validate

REPO = Path(__file__).resolve().parent.parent
QUOTE = "Quiet Hours lets a member pause their own in-app alerts for a selected period."
CODE_REPO = "example-org/product-web"

# Fictional product code for the throwaway Git repository.
CODE_V1 = """\
\"\"\"Quiet Hours for the fictional Pulseboard app.\"\"\"

def pause_alerts(member, until):
    member.alerts_paused_until = until
    return member


"""
CODE_V2 = CODE_V1.replace("return member", "return None")


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=Test", "-c", "user.email=test@example.com",
         "-c", "commit.gpgsign=false", *args],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


@pytest.fixture
def code_repo(tmp_path):
    """A local Git repo with two commits of src/quiet_hours.py."""
    root = tmp_path / "product-web"
    (root / "src").mkdir(parents=True)
    git(root, "init", "-q")
    (root / "src" / "quiet_hours.py").write_text(CODE_V1, encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "v1")
    v1 = git(root, "rev-parse", "HEAD")
    (root / "src" / "quiet_hours.py").write_text(CODE_V2, encoding="utf-8")
    git(root, "commit", "-q", "-am", "v2")
    return root, v1


class Run:
    """A custom-profile run folder using the fictional demo PRD as its source."""

    def __init__(self, base: Path, repo: Path = REPO, source: str = "demo/mock-prd.md"):
        self.dir = base / "run"
        (self.dir / "analysis").mkdir(parents=True)
        (self.dir / "api").mkdir()
        self.repo = repo
        self.manifest = {
            "schema_version": 1, "profile": "custom", "audience": "developers",
            "sources": [{"id": "S1", "path": source,
                         "sha256": hashlib.sha256((repo / source).read_bytes()).hexdigest()}],
            "deliverables": ["api/reference.md"],
            "review": {"method": "independent_reviewer", "source_fidelity": "pending",
                       "product_verification": "pending", "human_approval": "pending"},
        }
        self.evidence = [{"claim_id": "C01", "source_id": "S1", "quote": QUOTE,
                          "status": "included", "destinations": ["api/reference.md"]}]
        self.body = ("# Quiet Hours reference\n\nThis is a fictional integration overview. Quiet Hours "
                     "pauses a member's own in-app alerts. Source: [S1#L8].\n")

    def validate(self, code_roots=None):
        (self.dir / "run.json").write_text(json.dumps(self.manifest), encoding="utf-8")
        (self.dir / "analysis" / "evidence.json").write_text(json.dumps(self.evidence), encoding="utf-8")
        (self.dir / "api" / "reference.md").write_text(self.body, encoding="utf-8")
        return validate(self.dir, self.repo, code_roots)


@pytest.fixture
def run(tmp_path):
    return Run(tmp_path)


def code_row(commit, **overrides):
    text = CODE_V1
    row = {
        "claim_id": "C02", "kind": "code", "repo": CODE_REPO, "commit": commit,
        "path": "src/quiet_hours.py", "lines": "L3-L5",
        "excerpt_sha256": excerpt_sha256(text, 3, 5),
        "status": "included", "destinations": ["api/reference.md"],
    }
    row.update(overrides)
    return row


# --- existing behaviour ----------------------------------------------------


def test_existing_quote_evidence_still_valid(run):
    errors, warnings = run.validate()
    assert errors == []
    assert warnings == ["not approved for publication"]


def test_source_hash_mismatch_when_source_changes(tmp_path):
    repo = tmp_path / "repo"
    (repo / "demo").mkdir(parents=True)
    shutil.copy(REPO / "demo" / "mock-prd.md", repo / "demo" / "mock-prd.md")
    run = Run(tmp_path, repo=repo)
    assert run.validate()[0] == []
    with (repo / "demo" / "mock-prd.md").open("a", encoding="utf-8") as f:
        f.write("\nA late edit after the manifest was created.\n")
    errors, _ = run.validate()
    assert errors == ["S1: source hash mismatch"]


def test_source_hash_mismatch_when_manifest_is_wrong(run):
    run.manifest["sources"][0]["sha256"] = "0" * 64
    errors, _ = run.validate()
    assert errors == ["S1: source hash mismatch"]


def test_unknown_class_cannot_be_included(run):
    run.evidence[0]["claim_class"] = "UNKNOWN"
    errors, _ = run.validate()
    assert errors == ["C01: UNKNOWN claim cannot be included"]


# --- code evidence ---------------------------------------------------------


def test_code_evidence_verified(run, code_repo):
    root, v1 = code_repo
    run.evidence.append(code_row(v1))
    errors, warnings = run.validate({CODE_REPO: root})
    assert errors == []
    assert not any("not verified" in w for w in warnings)


def test_code_evidence_pinned_to_old_commit_survives_later_change(run, code_repo):
    # v2 changed line 5, but the evidence cites v1, so it still verifies.
    root, v1 = code_repo
    run.evidence.append(code_row(v1))
    assert run.validate({CODE_REPO: root})[0] == []


def test_code_excerpt_hash_mismatch(run, code_repo):
    root, _ = code_repo
    head = git(root, "rev-parse", "HEAD")  # v2: line 5 differs from the recorded excerpt
    run.evidence.append(code_row(head))
    errors, _ = run.validate({CODE_REPO: root})
    assert errors == ["C02: code excerpt hash mismatch for src/quiet_hours.py L3-L5"]


def test_code_evidence_without_checkout_is_a_warning(run, code_repo):
    _, v1 = code_repo
    run.evidence.append(code_row(v1))
    errors, warnings = run.validate()
    assert errors == []
    assert f"C02: code evidence not verified (no local checkout for {CODE_REPO})" in warnings


def test_unknown_commit(run, code_repo):
    root, _ = code_repo
    run.evidence.append(code_row("c" * 40))
    errors, _ = run.validate({CODE_REPO: root})
    assert errors == [f"C02: commit {'c' * 12} not found in local checkout of {CODE_REPO}"]


def test_missing_file_at_commit(run, code_repo):
    root, v1 = code_repo
    run.evidence.append(code_row(v1, path="src/missing.py"))
    errors, _ = run.validate({CODE_REPO: root})
    assert errors == [f"C02: src/missing.py does not exist at commit {v1[:12]}"]


def test_lines_out_of_range(run, code_repo):
    root, v1 = code_repo
    run.evidence.append(code_row(v1, lines="L5-L99"))
    errors, _ = run.validate({CODE_REPO: root})
    assert errors == ["C02: invalid or blank code lines L5-L99 in src/quiet_hours.py"]


def test_blank_lines(run, code_repo):
    root, v1 = code_repo
    run.evidence.append(code_row(v1, lines="L6-L7"))
    errors, _ = run.validate({CODE_REPO: root})
    assert errors == ["C02: invalid or blank code lines L6-L7 in src/quiet_hours.py"]


def test_code_root_must_be_git_checkout(run, code_repo, tmp_path):
    _, v1 = code_repo
    run.evidence.append(code_row(v1))
    plain = tmp_path / "not-git"
    plain.mkdir()
    errors, _ = run.validate({CODE_REPO: plain})
    assert errors == [f"code root for {CODE_REPO} is not a Git checkout"]


def test_code_evidence_destination_rules(run, code_repo):
    root, v1 = code_repo
    run.evidence.append(code_row(v1, destinations=["api/missing.md"]))
    errors, _ = run.validate({CODE_REPO: root})
    assert errors == ["C02: included claim lacks an existing deliverable"]


def test_excerpt_hash_ignores_trailing_newline():
    assert excerpt_sha256("a\nb\n", 1, 2) == excerpt_sha256("a\nb", 1, 2)
    assert excerpt_sha256("a\nb\n", 1, 2) == hashlib.sha256(b"a\nb").hexdigest()


# --- scripts/validate_run.py wrapper ---------------------------------------


def run_script(*args):
    return subprocess.run(
        [sys.executable, str(REPO / "scripts" / "validate_run.py"), *args],
        capture_output=True, text=True, check=False,
    )


def test_wrapper_verifies_code_evidence(run, code_repo):
    root, v1 = code_repo
    run.evidence.append(code_row(v1))
    run.validate()  # writes the files
    result = run_script(str(run.dir), "--code-root", f"{CODE_REPO}={root}")
    assert result.returncode == 0, result.stdout
    assert "PASS: 0 errors" in result.stdout
    assert "not verified" not in result.stdout


def test_wrapper_reports_failures(run):
    run.manifest["sources"][0]["sha256"] = "0" * 64
    run.validate()
    result = run_script(str(run.dir))
    assert result.returncode == 1
    assert "FAIL: S1: source hash mismatch" in result.stdout


def test_wrapper_rejects_bad_code_root(run):
    run.validate()
    result = run_script(str(run.dir), "--code-root", "not-a-repo")
    assert result.returncode == 2
    assert "owner/repo=PATH" in result.stderr
