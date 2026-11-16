import json
from pathlib import Path
import shutil

import pytest
from conftest import CODE_REPO, materialize_claims

from docforge.research import (
    BLOCK_END,
    BLOCK_START,
    Claim,
    ClaimsFile,
    ResearchError,
    check_claims,
    classify,
    evaluate,
    load_claims,
    research_check,
    update_register,
)
from docforge.run import start_run

REPO = Path(__file__).resolve().parent.parent
PRD = REPO / "demo" / "mock-prd.md"
EXAMPLE = REPO / "output" / "quiet-hours"
SOURCES = {"S1": PRD}

EXPECTED_STATUSES = {
    "C02": "confirmed",
    "C03": "conflicting",
    "C05": "needs_engineering",
    "C06": "prd_only",
    "C07": "confirmed",
    "C08": "code_only",
    "C11": "unknown",
}


@pytest.fixture
def claims(research_repo):
    root, _, head = research_repo
    return ClaimsFile.model_validate(materialize_claims(root, head))


# --- the M5 acceptance case ---------------------------------------------------


def test_fixture_prd_and_code_give_expected_statuses(claims, research_repo):
    root, _, _ = research_repo
    assert check_claims(claims, SOURCES, {CODE_REPO: root}) == ([], [])
    results = evaluate(claims)
    assert {r.claim_id: r.status for r in results} == EXPECTED_STATUSES


def test_fixture_raises_expected_questions(claims):
    results = {r.claim_id: r for r in evaluate(claims)}
    assert {cid: r.question_id for cid, r in results.items() if r.question_id} == {
        "C03": "X1", "C05": "X2", "C08": "X3"}
    assert "disagree about \"The pause options are 1 hour and Until tomorrow.\"" in results["C03"].question
    assert "src/pulseboard/quiet_hours.py L5-L8" in results["C03"].question
    assert "(the code offers 2 hours, not 1 hour)" in results["C03"].question
    assert results["C05"].question == (
        "C05: Does the notification service resume in-app alerts exactly at the end time, "
        "including when the member is offline?")
    assert "but the PRD does not state it" in results["C08"].question
    assert results["C08"].supporting_code[0].startswith("src/pulseboard/quiet_hours.py L9 @ ")


# --- status rules -------------------------------------------------------------


def claim(**kwargs):
    code = []
    for relation in kwargs.pop("code", []):
        code.append({"repo": CODE_REPO, "commit": "a" * 40, "path": "x.py", "lines": "L1",
                     "excerpt_sha256": "b" * 64, "relation": relation})
    prd = [{"source_id": "S1", "quote": "q"}] if kwargs.pop("prd", False) else []
    return Claim(claim_id="C01", statement="s", prd=prd, code=code, **kwargs)


@pytest.mark.parametrize(
    "kwargs, status",
    [
        ({"prd": True, "code": ["supports", "contradicts"]}, "conflicting"),
        ({"prd": True, "code": ["contradicts"], "needs_engineering": "q?"}, "conflicting"),
        ({"prd": True, "code": ["supports"], "needs_engineering": "q?"}, "needs_engineering"),
        ({"needs_engineering": "q?"}, "needs_engineering"),
        ({"prd": True, "code": ["supports"]}, "confirmed"),
        ({"prd": True, "code": ["context"]}, "prd_only"),
        ({"prd": True}, "prd_only"),
        ({"code": ["supports"]}, "code_only"),
        ({"code": ["contradicts"]}, "unknown"),
        ({"code": ["context"]}, "unknown"),
        ({}, "unknown"),
    ],
)
def test_status_rules(kwargs, status):
    assert classify(claim(**kwargs)) == status


# --- evidence checks ----------------------------------------------------------


def test_fabricated_quote_and_unknown_source(claims):
    claims.claims[0].prd[0].quote = "Quiet Hours also pauses email alerts."
    claims.claims[1].prd[0].source_id = "S9"
    errors, _ = check_claims(claims, SOURCES)
    assert errors == ["C02: quotation not found in S1", "C03: unknown source S9"]


def test_code_not_verified_without_checkout(claims):
    errors, warnings = check_claims(claims, SOURCES)
    assert errors == []
    assert warnings[0] == f"C02: code evidence not verified (no local checkout for {CODE_REPO})"
    assert len(warnings) == 6


def test_code_hash_mismatch(claims, research_repo):
    root, _, _ = research_repo
    claims.claims[0].code[0].excerpt_sha256 = "0" * 64
    errors, _ = check_claims(claims, SOURCES, {CODE_REPO: root})
    assert errors == ["C02: code excerpt hash mismatch for src/pulseboard/quiet_hours.py L11"]


def test_code_at_unknown_commit(claims, research_repo):
    root, _, _ = research_repo
    claims.claims[0].code[0].commit = "c" * 40
    errors, _ = check_claims(claims, SOURCES, {CODE_REPO: root})
    assert errors == [f"C02: commit {'c' * 12} not found in local checkout of {CODE_REPO}"]


def test_duplicate_claim_ids(claims):
    claims.claims[1].claim_id = "C02"
    errors, _ = check_claims(claims, SOURCES)
    assert errors == ["duplicate claim C02"]


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda d: d.update(extra=1), "Extra inputs are not permitted"),
        (lambda d: d["claims"][0].update(claim_id="X1"), "claim_id must look like"),
        (lambda d: d["claims"][0]["code"][0].update(relation="maybe"), "relation"),
        (lambda d: d["claims"][0]["code"][0].update(path="../secret.py"), "stay inside the repository"),
        (lambda d: d["claims"][0]["code"][0].update(commit="abc"), "commit"),
        (lambda d: d.update(claims=[]), "at least 1 item"),
    ],
)
def test_claims_file_is_strict(tmp_path, research_repo, mutate, message):
    root, _, head = research_repo
    data = materialize_claims(root, head)
    mutate(data)
    path = tmp_path / "claims.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ResearchError, match=message):
        load_claims(path)


def test_claims_file_must_exist_and_be_json(tmp_path):
    with pytest.raises(ResearchError, match="missing claims.json"):
        load_claims(tmp_path / "claims.json")
    (tmp_path / "claims.json").write_text("{", encoding="utf-8")
    with pytest.raises(ResearchError, match="not valid JSON"):
        load_claims(tmp_path / "claims.json")


# --- clarification register block ----------------------------------------------


def test_register_block_is_added_then_replaced(tmp_path, claims):
    register = tmp_path / "clarifications-and-assumptions.md"
    register.write_text("# Clarifications\n\nQ01 stays.\n", encoding="utf-8")
    results = evaluate(claims)
    update_register(register, results)
    first = register.read_text(encoding="utf-8")
    assert first.startswith("# Clarifications\n\nQ01 stays.\n\n" + BLOCK_START)
    assert "- **X1** (conflicting) C03:" in first
    update_register(register, results)
    assert register.read_text(encoding="utf-8") == first
    update_register(register, results[:1])
    text = register.read_text(encoding="utf-8")
    assert "Q01 stays." in text and "None." in text and "X1" not in text
    assert text.count(BLOCK_START) == text.count(BLOCK_END) == 1


def test_register_errors(tmp_path, claims):
    with pytest.raises(ResearchError, match="Analyzer stage writes it"):
        update_register(tmp_path / "missing.md", evaluate(claims))
    damaged = tmp_path / "register.md"
    damaged.write_text(f"# R\n\n{BLOCK_START}\n", encoding="utf-8")
    with pytest.raises(ResearchError, match="damaged cross-source block"):
        update_register(damaged, evaluate(claims))


# --- research_check on a run folder ----------------------------------------------


@pytest.fixture
def run(tmp_path, research_repo):
    root, base, head = research_repo
    repo = tmp_path / "repo"
    (repo / "demo").mkdir(parents=True)
    shutil.copy(PRD, repo / "demo" / "mock-prd.md")
    out = start_run(repo=repo, prds=["demo/mock-prd.md"], out=repo / "output" / "qh", audience="members",
                    code_repo=CODE_REPO, base=base, head=head)
    for rel in ("analysis/HANDOVER.md", "analysis/clarifications-and-assumptions.md", "analysis/CONTENT-PLAN.md"):
        shutil.copy(EXAMPLE / rel, out / rel)
    (out / "analysis" / "claims.json").write_text(json.dumps(materialize_claims(root, head)), encoding="utf-8")
    return repo, out, root


def test_research_check_writes_report_results_and_register(run):
    repo, out, root = run
    record = research_check(out, repo, {CODE_REPO: root})
    assert (record["errors"], record["warnings"]) == ([], [])
    assert {r["claim_id"]: r["status"] for r in record["results"]} == EXPECTED_STATUSES
    report = (out / "analysis" / "CROSS-SOURCE.md").read_text(encoding="utf-8")
    assert "Code evidence: verified against a local checkout." in report
    assert "| conflicting | 1 |" in report and "| confirmed | 2 |" in report
    saved = json.loads((out / "analysis" / "cross-source.json").read_text(encoding="utf-8"))
    assert [r["question_id"] for r in saved if r["question_id"]] == ["X1", "X2", "X3"]
    register = (out / "analysis" / "clarifications-and-assumptions.md").read_text(encoding="utf-8")
    assert register.startswith((EXAMPLE / "analysis/clarifications-and-assumptions.md").read_text(encoding="utf-8").rstrip("\n"))
    assert "- **X3** (code_only) C08:" in register


def test_research_check_without_checkout_says_not_verified(run):
    repo, out, _ = run
    record = research_check(out, repo)
    assert record["errors"] == []
    assert "NOT verified" in (out / "analysis" / "CROSS-SOURCE.md").read_text(encoding="utf-8")


def test_research_check_writes_nothing_on_errors(run):
    repo, out, root = run
    data = json.loads((out / "analysis" / "claims.json").read_text(encoding="utf-8"))
    data["claims"][0]["prd"][0]["quote"] = "Invented sentence."
    (out / "analysis" / "claims.json").write_text(json.dumps(data), encoding="utf-8")
    before = (out / "analysis" / "clarifications-and-assumptions.md").read_text(encoding="utf-8")
    record = research_check(out, repo, {CODE_REPO: root})
    assert record["errors"] == ["C02: quotation not found in S1"]
    assert record["written"] == []
    assert not (out / "analysis" / "CROSS-SOURCE.md").exists()
    assert (out / "analysis" / "clarifications-and-assumptions.md").read_text(encoding="utf-8") == before
