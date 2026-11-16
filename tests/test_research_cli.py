import json
from pathlib import Path
import shutil

import pytest
from conftest import CODE_REPO, materialize_claims

from docforge.cli import main
from docforge.run import RunError, next_stage, run_checks, run_status, start_run

REPO = Path(__file__).resolve().parent.parent
PRD = REPO / "demo" / "mock-prd.md"
EXAMPLE = REPO / "output" / "quiet-hours"
ANALYSIS = ["analysis/HANDOVER.md", "analysis/clarifications-and-assumptions.md", "analysis/CONTENT-PLAN.md"]
REST = ["feature/feature-guide.md", "how-to/how-to.md", "release-note/release-note.md", "analysis/COVERAGE.md",
        "qa/QA-REPORT.md"]


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    (root / "demo").mkdir(parents=True)
    shutil.copy(PRD, root / "demo" / "mock-prd.md")
    return root


def copy(out, files):
    for rel in files:
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(EXAMPLE / rel, out / rel)


def start(repo, research_repo, **kwargs):
    _, base, head = research_repo
    return start_run(repo=repo, prds=["demo/mock-prd.md"], out=repo / "output" / "qh", audience="members",
                     code_repo=CODE_REPO, base=base, head=head, **kwargs)


# --- run start with code -------------------------------------------------------


def test_start_with_code_adds_research_stage(repo, research_repo):
    _, base, head = research_repo
    out = start(repo, research_repo)
    manifest = json.loads((out / "run.json").read_text(encoding="utf-8"))
    assert manifest["code"] == {"repo": CODE_REPO, "base": base, "head": head}
    assert sorted(p.name for p in (out / "prompts").iterdir()) == [
        "1-analyzer.md", "2-research.md", "3-drafter.md", "4-proofreader.md"]
    research = (out / "prompts" / "2-research.md").read_text(encoding="utf-8")
    assert research.startswith("# Stage 2 of 4: Research")
    assert "docforge research packet output/qh" in research
    assert "`analysis/claims.json`" in research and "`analysis/CROSS-SOURCE.md`" in research
    drafter = (out / "prompts" / "3-drafter.md").read_text(encoding="utf-8")
    assert "- `analysis/CROSS-SOURCE.md`" in drafter  # listed as an earlier stage output


def test_start_without_code_keeps_three_stages(repo):
    out = start_run(repo=repo, prds=["demo/mock-prd.md"], out=repo / "output" / "plain", audience="members")
    assert "code" not in json.loads((out / "run.json").read_text(encoding="utf-8"))
    assert sorted(p.name for p in (out / "prompts").iterdir()) == ["1-analyzer.md", "2-drafter.md", "3-proofreader.md"]


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"code_repo": CODE_REPO, "base": None, "head": "a" * 40}, "needs --base and --head"),
        ({"code_repo": "pulseboard", "base": "a" * 40, "head": "b" * 40}, "owner/repo"),
        ({"code_repo": CODE_REPO, "base": "abc123", "head": "b" * 40}, "full 40-character"),
    ],
)
def test_start_code_validation(repo, kwargs, message):
    with pytest.raises(RunError, match=message):
        start_run(repo=repo, prds=["demo/mock-prd.md"], out=repo / "output" / "bad", audience="members", **kwargs)
    assert not (repo / "output" / "bad").exists()


def test_status_walks_four_stages(repo, research_repo):
    root, _, head = research_repo
    out = start(repo, research_repo)
    assert next_stage(run_status(out)).stage.key == "analyzer"
    copy(out, ANALYSIS)
    assert next_stage(run_status(out)).stage.key == "research"
    (out / "analysis" / "claims.json").write_text(json.dumps(materialize_claims(root, head)), encoding="utf-8")
    assert next_stage(run_status(out)).missing == ["analysis/CROSS-SOURCE.md"]
    assert main(["research", "check", str(out), "--repo", str(repo), "--code-root", f"{CODE_REPO}={root}"]) == 0
    assert next_stage(run_status(out)).stage.key == "drafter"


# --- CLI ------------------------------------------------------------------------


def test_cli_research_packet(repo, research_repo, capsys):
    root, _, _ = research_repo
    out = start(repo, research_repo)
    assert main(["research", "packet", str(out), "--checkout", str(root)]) == 0
    assert "2 changed file(s), 2 cited hunk(s)" in capsys.readouterr().out
    packet = json.loads((out / "research" / "changes.json").read_text(encoding="utf-8"))
    assert [h["ref"]["lines"] for h in packet["hunks"]] == ["L9-L12", "L1-L28"]


def test_cli_research_packet_needs_code(repo, capsys):
    out = start_run(repo=repo, prds=["demo/mock-prd.md"], out=repo / "output" / "plain", audience="members")
    assert main(["research", "packet", str(out), "--checkout", "."]) == 1
    assert "has no product code" in capsys.readouterr().err


def test_cli_research_check_prints_statuses(repo, research_repo, capsys):
    root, _, head = research_repo
    out = start(repo, research_repo)
    copy(out, ANALYSIS)
    (out / "analysis" / "claims.json").write_text(json.dumps(materialize_claims(root, head)), encoding="utf-8")
    assert main(["research", "check", str(out), "--repo", str(repo), "--code-root", f"{CODE_REPO}={root}"]) == 0
    text = capsys.readouterr().out
    assert "  C03  conflicting        X1" in text
    assert "  C11  unknown" in text


def test_cli_research_check_fails_on_bad_evidence(repo, research_repo, capsys):
    root, _, head = research_repo
    out = start(repo, research_repo)
    copy(out, ANALYSIS)
    data = materialize_claims(root, head)
    data["claims"][0]["code"][0]["excerpt_sha256"] = "0" * 64
    (out / "analysis" / "claims.json").write_text(json.dumps(data), encoding="utf-8")
    assert main(["research", "check", str(out), "--repo", str(repo), "--code-root", f"{CODE_REPO}={root}"]) == 1
    assert "nothing was written" in capsys.readouterr().out


def test_cli_evidence_code_ref(research_repo, capsys):
    root, _, head = research_repo
    assert main(["evidence", "code-ref", "--checkout", str(root), "--repo", CODE_REPO, "--commit", head[:7],
                 "--path", "src/pulseboard/quiet_hours.py", "--lines", "L11"]) == 0
    ref = json.loads(capsys.readouterr().out)
    assert (ref["commit"], ref["lines"]) == (head, "L11")
    assert main(["evidence", "code-ref", "--checkout", str(root), "--repo", CODE_REPO, "--commit", head,
                 "--path", "src/pulseboard/quiet_hours.py", "--lines", "L2"]) == 1
    assert "out of range or blank" in capsys.readouterr().err


def test_run_check_includes_research_and_existing_checker(repo, research_repo, capsys):
    root, _, head = research_repo
    out = start(repo, research_repo)
    copy(out, ANALYSIS + REST)
    (out / "analysis" / "claims.json").write_text(json.dumps(materialize_claims(root, head)), encoding="utf-8")
    record = run_checks(out, repo, {CODE_REPO: root})
    # The register block mentions handover claim IDs only, so the existing checker still passes.
    assert record["structural"]["passed"] is True, record["structural"]["errors"]
    assert record["research"]["passed"] is True
    assert record["research"]["statuses"]["C03"] == "conflicting"
    assert main(["run", "check", str(out), "--repo", str(repo), "--code-root", f"{CODE_REPO}={root}"]) == 0
    text = capsys.readouterr().out
    assert "Cross-source: code_only 1, confirmed 2, conflicting 1, needs_engineering 1, prd_only 1, unknown 1" in text


def test_run_check_fails_when_research_fails(repo, research_repo, capsys):
    out = start(repo, research_repo)
    copy(out, ANALYSIS + REST)
    record = run_checks(out, repo)
    assert record["structural"]["passed"] is True
    assert record["research"]["passed"] is False
    assert "missing claims.json" in record["research"]["errors"][0]
    assert main(["run", "check", str(out), "--repo", str(repo)]) == 1
