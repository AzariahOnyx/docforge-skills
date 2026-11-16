import json
from pathlib import Path

from docforge.agent import append_decision, decide
from docforge.cli import main
from docforge.config import DocForgeConfig, load_config
from docforge.sources import parse_event, read_diff_file

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "github"
CONFIG = load_config(FIXTURES / "triggers.yaml")
CHANGES = read_diff_file(FIXTURES / "product_change.diff")


def event(name, github_event="pull_request", **kwargs):
    return parse_event(github_event, json.loads((FIXTURES / name).read_text(encoding="utf-8")), **kwargs)


def test_triggered_event_needs_research():
    decision = decide(CONFIG, event("pr_merged.json"), CHANGES, diff_source="diff file product_change.diff")
    assert decision.docs_needed == "needs_research"
    assert decision.summary == "matched trigger(s) product-prs; research the change before drafting"
    assert decision.changed_files == [
        "src/settings/quiet_hours.py", "src/settings/panel.py", "tests/test_quiet_hours.py"]
    assert decision.event["kind"] == "merge"
    assert [step.step for step in decision.research_trail] == [
        "read_event", "read_diff", "check_trigger", "check_trigger"]
    assert decision.research_trail[1].detail == {
        "source": "diff file product_change.diff", "files": 3, "additions": 9, "deletions": 3}


def test_no_is_recorded_with_reasons():
    decision = decide(CONFIG, event("pr_opened_draft.json"), CHANGES)
    assert decision.docs_needed == "no"
    assert decision.summary == ("product-prs: skipped (draft pull request); "
                                "topic-prs: skipped (draft pull request)")
    assert [c.outcome for c in decision.triggers] == ["skipped", "skipped"]


def test_ignored_event_is_still_a_decision():
    decision = decide(CONFIG, event("pr_closed_unmerged.json"), None)
    assert decision.docs_needed == "no"
    assert decision.changed_files is None
    assert decision.research_trail[1].detail == {"source": None, "note": "no diff supplied"}
    assert all(c.reasons == ["closed without merging"] for c in decision.triggers)


def test_diff_error_is_recorded():
    decision = decide(CONFIG, event("pr_opened.json"), None, diff_source="local checkout", diff_error="boom")
    assert decision.research_trail[1].detail == {"source": "local checkout", "note": "diff could not be read: boom"}


def test_no_triggers_configured():
    decision = decide(DocForgeConfig(), event("pr_opened.json"), CHANGES)
    assert (decision.docs_needed, decision.summary, decision.triggers) == (
        "no", "no github_pr triggers are configured", [])


def test_log_appends_json_lines(tmp_path):
    log = tmp_path / "logs" / "decisions.jsonl"
    first = decide(CONFIG, event("pr_opened.json"), CHANGES)
    second = decide(CONFIG, event("pr_labeled.json"), CHANGES)
    append_decision(log, first)
    append_decision(log, second)
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert [r["decision_id"] for r in rows] == [first.decision_id, second.decision_id]
    assert [r["docs_needed"] for r in rows] == ["needs_research", "no"]


# --- CLI -------------------------------------------------------------------


def run_cli(tmp_path, *args):
    return main(["trigger", "check", *args, "--config", str(FIXTURES / "triggers.yaml"),
                 "--log", str(tmp_path / "decisions.jsonl")])


def test_cli_trigger_check_logs_decision(tmp_path, capsys):
    code = run_cli(tmp_path, str(FIXTURES / "pr_opened.json"), "--event", "pull_request",
                   "--diff", str(FIXTURES / "product_change.diff"))
    out, err = capsys.readouterr()
    assert code == 0
    assert json.loads(out)["docs_needed"] == "needs_research"
    assert "Logged decision" in err
    assert len((tmp_path / "decisions.jsonl").read_text(encoding="utf-8").splitlines()) == 1


def test_cli_trigger_check_first_approval(tmp_path, capsys):
    code = run_cli(tmp_path, str(FIXTURES / "review_approved.json"), "--event", "pull_request_review",
                   "--prior-approvals", "0", "--diff", str(FIXTURES / "product_change.diff"))
    assert code == 0
    assert json.loads(capsys.readouterr().out)["event"]["kind"] == "first_approval"


def test_cli_trigger_check_no_log(tmp_path, capsys):
    code = run_cli(tmp_path, str(FIXTURES / "pr_labeled.json"), "--event", "pull_request", "--no-log")
    assert code == 0
    assert json.loads(capsys.readouterr().out)["docs_needed"] == "no"
    assert not (tmp_path / "decisions.jsonl").exists()


def test_cli_trigger_check_bad_payload(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{}", encoding="utf-8")
    assert run_cli(tmp_path, str(bad), "--event", "pull_request") == 1
    assert "no pull_request object" in capsys.readouterr().err
