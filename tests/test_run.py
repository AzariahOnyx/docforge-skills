import hashlib
import json
from pathlib import Path
import shutil

import pytest

from docforge.cli import main
from docforge.evidence import parse_manifest
from docforge.run import RunError, next_stage, run_checks, run_status, start_run

REPO = Path(__file__).resolve().parent.parent
PRD = REPO / "demo" / "mock-prd.md"
DOCS = Path(__file__).resolve().parent / "fixtures" / "docs-repo"
EXAMPLE = REPO / "output" / "quiet-hours"


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    (root / "demo").mkdir(parents=True)
    shutil.copy(PRD, root / "demo" / "mock-prd.md")
    return root


def start(repo, **kwargs):
    args = dict(repo=repo, prds=["demo/mock-prd.md"], out=repo / "output" / "run1", audience="signed-in members")
    args.update(kwargs)
    return start_run(**args)


def copy_outputs(out: Path, files):
    for rel in files:
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(EXAMPLE / rel, out / rel)


ANALYSIS = ["analysis/HANDOVER.md", "analysis/clarifications-and-assumptions.md", "analysis/CONTENT-PLAN.md"]
DRAFTS = ["feature/feature-guide.md", "how-to/how-to.md", "release-note/release-note.md", "analysis/COVERAGE.md"]
QA = ["qa/QA-REPORT.md"]


# --- start -----------------------------------------------------------------


def test_start_creates_manifest_matches_and_work_orders(repo):
    out = start(repo, docs=DOCS)
    manifest = json.loads((out / "run.json").read_text(encoding="utf-8"))
    parsed, errors = parse_manifest(manifest)
    assert errors == []
    assert manifest["profile"] == "default"
    assert manifest["sources"] == [{
        "id": "S1", "path": "demo/mock-prd.md",
        "sha256": hashlib.sha256(PRD.read_bytes()).hexdigest(), "authority": "unconfirmed", "kind": "file",
    }]
    assert manifest["deliverables"] == ["feature/feature-guide.md", "how-to/how-to.md", "release-note/release-note.md"]
    assert manifest["review"]["human_approval"] == "pending"

    existing = json.loads((out / "analysis" / "existing-docs.json").read_text(encoding="utf-8"))
    assert existing["pages"] == 6
    assert [q["query"] for q in existing["queries"]][:2] == ["Fictional PRD: Quiet Hours", "Product context"]
    assert (out / "analysis" / "docs-index.json").is_file()

    orders = sorted(p.name for p in (out / "prompts").iterdir())
    assert orders == ["1-analyzer.md", "2-drafter.md", "3-proofreader.md"]
    analyzer = (out / "prompts" / "1-analyzer.md").read_text(encoding="utf-8")
    assert ".agents/skills/analyzer/SKILL.md" in analyzer
    assert "analysis/existing-docs.json" in analyzer
    assert "`output/run1`" in analyzer
    proofreader = (out / "prompts" / "3-proofreader.md").read_text(encoding="utf-8")
    assert "same_agent_second_pass" in proofreader
    assert "`qa/QA-REPORT.md`" in proofreader


def test_start_without_docs_marks_existing_docs_unknown(repo):
    out = start(repo)
    existing = json.loads((out / "analysis" / "existing-docs.json").read_text(encoding="utf-8"))
    assert existing["docs_path"] is None
    assert not (out / "analysis" / "docs-index.json").exists()
    assert "UNKNOWN" in (out / "prompts" / "1-analyzer.md").read_text(encoding="utf-8")


def test_start_never_overwrites(repo):
    out = repo / "output" / "run1"
    out.mkdir(parents=True)
    (out / "keep.md").write_text("earlier work", encoding="utf-8")
    with pytest.raises(RunError, match="already exists"):
        start(repo)
    assert sorted(p.name for p in out.iterdir()) == ["keep.md"]


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"prds": ["../outside.md"]}, "inside the repository"),
        ({"prds": ["demo/missing.md"]}, "not found"),
        ({"prds": []}, "at least one"),
        ({"audience": "  "}, "audience is required"),
        ({"profile": "custom"}, "at least one --deliverable"),
        ({"deliverables": ["x.md"]}, "only for the custom profile"),
        ({"docs": Path("/nonexistent-docs")}, "docs folder not found"),
    ],
)
def test_start_rejects_bad_input_without_creating_folder(repo, kwargs, message):
    with pytest.raises(RunError, match=message):
        start(repo, **kwargs)
    assert not (repo / "output" / "run1").exists()


# --- status ----------------------------------------------------------------


def test_status_moves_through_stages(repo):
    out = start(repo)
    statuses = run_status(out)
    assert next_stage(statuses).stage.key == "analyzer"
    assert statuses[0].missing == ANALYSIS

    copy_outputs(out, ANALYSIS)
    assert next_stage(run_status(out)).stage.key == "drafter"

    copy_outputs(out, DRAFTS)
    assert next_stage(run_status(out)).stage.key == "proofreader"

    copy_outputs(out, QA)
    assert next_stage(run_status(out)) is None


def test_status_treats_near_empty_file_as_missing(repo):
    out = start(repo)
    copy_outputs(out, ANALYSIS)
    (out / "analysis" / "HANDOVER.md").write_text("# Handover\n", encoding="utf-8")
    statuses = run_status(out)
    assert statuses[0].missing == ["analysis/HANDOVER.md"]


def test_status_needs_run_folder(tmp_path):
    with pytest.raises(RunError, match="no run.json"):
        run_status(tmp_path)


# --- check -----------------------------------------------------------------


def test_check_default_profile_passes_on_complete_run(repo):
    out = start(repo)
    copy_outputs(out, ANALYSIS + DRAFTS + QA)
    record = run_checks(out, REPO)
    assert record["structural"]["checker"] == "scripts/check_outputs.py"
    assert record["structural"]["passed"] is True
    assert record["structural"]["errors"] == []
    saved = json.loads((out / "qa" / "checks.json").read_text(encoding="utf-8"))
    assert saved["structural"]["passed"] is True
    assert "human approval" in saved["note"]


def test_check_default_profile_fails_on_broken_run(repo):
    out = start(repo)
    copy_outputs(out, ANALYSIS + DRAFTS + QA)
    how_to = out / "how-to" / "how-to.md"
    how_to.write_text(how_to.read_text(encoding="utf-8").replace("## Expected result", "## Result"), encoding="utf-8")
    record = run_checks(out, REPO)
    assert record["structural"]["passed"] is False
    assert "how-to/how-to.md: missing ## Expected result" in record["structural"]["errors"]


def test_check_custom_profile_uses_evidence_validator(repo):
    out = start(repo, profile="custom", deliverables=["api/reference.md"])
    (out / "api").mkdir()
    (out / "api" / "reference.md").write_text(
        "# Quiet Hours reference\n\nThis fictional overview says Quiet Hours pauses a member's own "
        "in-app alerts. Source: [S1#L9].\n", encoding="utf-8")
    (out / "analysis" / "evidence.json").write_text(json.dumps([{
        "claim_id": "C01", "source_id": "S1",
        "quote": "Quiet Hours lets a member pause their own in-app alerts for a selected period.",
        "status": "included", "destinations": ["api/reference.md"],
    }]), encoding="utf-8")
    record = run_checks(out, repo)
    assert record["structural"]["checker"] == "docforge.evidence.validate"
    assert record["structural"]["errors"] == []
    assert record["structural"]["passed"] is True


# --- CLI -------------------------------------------------------------------


def test_cli_run_start_status_check(repo, capsys):
    out = repo / "output" / "run1"
    assert main(["run", "start", "--repo", str(repo), "--prd", "demo/mock-prd.md",
                 "--out", str(out), "--audience", "signed-in members"]) == 0
    assert "1-analyzer.md" in capsys.readouterr().out

    assert main(["run", "status", str(out)]) == 0
    text = capsys.readouterr().out
    assert "Stage 1 Analyzer: 0/3 files" in text
    assert "missing analysis/HANDOVER.md" in text

    copy_outputs(out, ANALYSIS + DRAFTS + QA)
    assert main(["run", "status", str(out)]) == 0
    assert "All stages have their files" in capsys.readouterr().out

    assert main(["run", "check", str(out), "--repo", str(REPO)]) == 0
    assert "PASS: scripts/check_outputs.py" in capsys.readouterr().out


def test_cli_run_start_refuses_existing_folder(repo, capsys):
    out = repo / "output" / "run1"
    out.mkdir(parents=True)
    assert main(["run", "start", "--repo", str(repo), "--prd", "demo/mock-prd.md",
                 "--out", str(out), "--audience", "x"]) == 1
    assert "already exists" in capsys.readouterr().err


def test_start_docs_include_limits_index_and_matches(repo):
    out = start(repo, docs=DOCS, docs_include=["docs/guides/"])
    existing = json.loads((out / "analysis" / "existing-docs.json").read_text(encoding="utf-8"))
    assert existing["include"] == ["docs/guides/"]
    assert existing["pages"] == 3
    index = json.loads((out / "analysis" / "docs-index.json").read_text(encoding="utf-8"))
    assert all(p["path"].startswith("docs/guides/") for p in index["pages"])
    hits = [h["path"] for q in existing["queries"] for h in q["hits"]]
    assert all(p.startswith("docs/guides/") for p in hits)


def test_start_docs_include_needs_docs(repo):
    with pytest.raises(RunError, match="--docs-include needs --docs"):
        start(repo, docs_include=["docs/"])
    assert not (repo / "output" / "run1").exists()
