import json
from pathlib import Path
import shutil

import pytest

from docforge.cli import main
from docforge.publish import gate_run, read_marker, statements
from docforge.run import start_run

REPO = Path(__file__).resolve().parent.parent
PRD = REPO / "demo" / "mock-prd.md"
EXAMPLE = REPO / "output" / "quiet-hours"
MARKED = Path(__file__).resolve().parent / "fixtures" / "publish"
PAGES = ["feature/feature-guide.md", "how-to/how-to.md", "release-note/release-note.md"]
ANALYSIS = ["analysis/HANDOVER.md", "analysis/clarifications-and-assumptions.md", "analysis/CONTENT-PLAN.md",
            "analysis/COVERAGE.md", "qa/QA-REPORT.md"]


def make_run(tmp_path, **kwargs) -> Path:
    repo = tmp_path / "repo"
    (repo / "demo").mkdir(parents=True, exist_ok=True)
    shutil.copy(PRD, repo / "demo" / "mock-prd.md")
    out = start_run(repo=repo, prds=["demo/mock-prd.md"], out=repo / "output" / "qh-docs", audience="members",
                    publish_to="example-org/docs-site", source_pr="example-org/pulseboard-web#42", **kwargs)
    for rel in ANALYSIS:
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(EXAMPLE / rel, out / rel)
    for rel in PAGES:
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(MARKED / rel, out / rel)
    return out


def edit(out: Path, rel: str, old: str, new: str) -> None:
    path = out / rel
    text = path.read_text(encoding="utf-8")
    assert old in text, old
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# --- statements and markers ------------------------------------------------------


def test_statement_kinds_and_exemptions():
    md = (
        "---\ntitle: T\n---\n# Heading\n\nFirst line\ncontinues here. <!-- evidence: C01 -->\n\n"
        "- item one <!-- evidence: C02 -->\n  continued\n- item two\n\n"
        "| Option | Effect |\n| --- | --- |\n| 1 hour | Pauses alerts <!-- evidence: C03 --> |\n\n"
        "```md\nNot a statement\n```\n\n<!-- just a comment -->\n\n> Quoted text\n<!-- evidence: none (example) -->\n"
    )
    found = statements(md)
    assert [(s.kind, s.line, s.claims, s.exempt) for s in found] == [
        ("paragraph", 6, ["C01"], None),
        ("list", 9, ["C02"], None),
        ("list", 11, None, None),
        ("table", 15, ["C03"], None),
        ("paragraph", 23, None, "example"),
    ]
    assert found[0].text == "First line continues here."


@pytest.mark.parametrize(
    "text, expected",
    [
        ("x <!-- evidence: C01, C02 , C01 -->", (["C01", "C02"], None, None)),
        ("x <!-- Evidence:none (navigation) -->", (None, "navigation", None)),
        ("x", (None, None, None)),
        ("x <!-- evidence: none -->", (None, None, "write an exemption as 'evidence: none (reason)'")),
        ("x <!-- evidence: maybe -->", (None, None, "invalid claim ID(s) in marker: maybe")),
        ("x <!-- evidence: C01 --> <!-- evidence: C02 -->", (None, None, "more than one evidence marker")),
    ],
)
def test_read_marker(text, expected):
    assert read_marker(text) == expected


def test_orphan_marker():
    found = statements("# Title\n\n<!-- evidence: C01 -->\n")
    assert [(s.kind, s.error) for s in found] == [("marker", "evidence marker is not attached to a statement")]


# --- gate on a run -----------------------------------------------------------------


def test_marked_demo_passes(tmp_path):
    out = make_run(tmp_path)
    result = gate_run(out)
    assert result.passed, result.errors
    assert (result.statements, result.cited, len(result.exemptions)) == (17, 16, 1)
    assert result.exemptions[0].reason == "navigation link"
    assert result.claims_cited["how-to/how-to.md"] == ["C02", "C03", "C04", "C05", "C06", "C07"]
    saved = json.loads((out / "qa" / "gate.json").read_text(encoding="utf-8"))
    assert saved["passed"] is True


@pytest.mark.parametrize(
    "rel, old, new, message",
    [
        ("how-to/how-to.md", " <!-- evidence: C07 -->", "", "statement has no evidence marker: \"Sign in to Pulseboard.\""),
        ("how-to/how-to.md", "<!-- evidence: C07 -->", "<!-- evidence: C01 -->",
         "C01 is not INCLUDED for how-to/how-to.md in the coverage ledger"),
        ("release-note/release-note.md", "<!-- evidence: C06 -->", "<!-- evidence: C08 -->",
         "C08 is not INCLUDED for release-note/release-note.md"),
        ("feature/feature-guide.md", "<!-- evidence: C06, C07 -->", "<!-- evidence: C06, C99 -->",
         "C99 is not a known claim"),
        ("feature/feature-guide.md", "<!-- evidence: none (navigation link) -->", "<!-- evidence: none -->",
         "write an exemption as 'evidence: none (reason)'"),
    ],
)
def test_gate_failures(tmp_path, rel, old, new, message):
    out = make_run(tmp_path)
    edit(out, rel, old, new)
    result = gate_run(out)
    assert not result.passed
    assert len(result.errors) == 1
    assert message in result.errors[0].message
    assert result.errors[0].path == rel


def test_cross_source_status_blocks_claim(tmp_path):
    out = make_run(tmp_path)
    (out / "analysis" / "cross-source.json").write_text(json.dumps([
        {"claim_id": "C03", "status": "conflicting"}, {"claim_id": "C02", "status": "confirmed"}]), encoding="utf-8")
    result = gate_run(out)
    assert not result.passed
    assert {e.message.split(":")[0] for e in result.errors} == {"C03 is conflicting and cannot back a published statement"}
    assert len(result.errors) == 8  # every statement that cites C03


def test_missing_deliverable_and_coverage(tmp_path):
    out = make_run(tmp_path)
    (out / "release-note" / "release-note.md").unlink()
    result = gate_run(out)
    assert [(e.path, e.message) for e in result.errors] == [("release-note/release-note.md", "deliverable is missing")]
    (out / "analysis" / "COVERAGE.md").unlink()
    from docforge.publish import GateError

    with pytest.raises(GateError, match="missing analysis/COVERAGE.md"):
        gate_run(out)


def test_custom_profile_uses_evidence_ledger(tmp_path):
    repo = tmp_path / "repo"
    (repo / "demo").mkdir(parents=True)
    shutil.copy(PRD, repo / "demo" / "mock-prd.md")
    out = start_run(repo=repo, prds=["demo/mock-prd.md"], out=repo / "output" / "api", audience="developers",
                    profile="custom", deliverables=["api/reference.md"])
    (out / "api").mkdir()
    (out / "api" / "reference.md").write_text(
        "# Reference\n\nQuiet Hours pauses in-app alerts. <!-- evidence: C01 -->\n\nIt is fast. <!-- evidence: C02 -->\n",
        encoding="utf-8")
    (out / "analysis" / "evidence.json").write_text(json.dumps([
        {"claim_id": "C01", "source_id": "S1", "quote": "q", "status": "included", "destinations": ["api/reference.md"]},
        {"claim_id": "C02", "source_id": "S1", "quote": "q", "status": "blocked", "destinations": []},
    ]), encoding="utf-8")
    result = gate_run(out)
    assert [e.message.split(":")[0] for e in result.errors] == [
        "C02 is not INCLUDED for api/reference.md in the evidence ledger"]


# --- CLI ---------------------------------------------------------------------------


def test_cli_gate(tmp_path, capsys):
    out = make_run(tmp_path)
    assert main(["gate", str(out)]) == 0
    assert "PASS: 17 statement(s) in 3 page(s); 16 backed by claims, 1 exempt, 0 error(s)." in capsys.readouterr().out
    edit(out, "how-to/how-to.md", " <!-- evidence: C07 -->", "")
    assert main(["gate", str(out)]) == 1
    assert "FAIL: how-to/how-to.md:7: statement has no evidence marker" in capsys.readouterr().out


def test_cli_gate_needs_input(capsys):
    assert main(["gate"]) == 2
