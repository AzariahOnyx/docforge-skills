"""The Jira front door running tickets (B6b): sources, plan, revise, draft, comments, the webhook route.

A local stub Jira serves a fictional issue and PDF attachments made by tests/pdfgen.py; a fake model
client stands in for the API backend. No network, no key, no cost.
"""

import copy
import json
from pathlib import Path
import sys
import time
import urllib.request

import pytest

pytest.importorskip("pdfplumber")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdfgen import write_pdf  # noqa: E402
from test_backend import FakeClient, stage_answer  # noqa: E402

from docforge.config import DocForgeConfig  # noqa: E402
from docforge.jira import handle, load_state, sign  # noqa: E402
from docforge.jira.state import Pending, TicketState, save_state  # noqa: E402
from docforge.jira.work import process  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEMO_PACK = ROOT / "tests" / "fixtures" / "packs" / "demo"
SECRET = "fictional-webhook-secret"
BOT = "acc-docforge-bot"
KEY = "PULSE-77"
ISSUE_PATH = f"/rest/api/3/issue/{KEY}?fields=summary,description,status,labels,issuelinks,issuetype,updated"
ISSUE = {"key": KEY, "fields": {
    "summary": "Document Quiet Hours", "issuetype": {"name": "Docs New"}, "status": {"name": "Plan Docs"},
    "labels": ["alerts"], "updated": "2026-11-18T09:00:00.000+0000",
    "description": {"type": "doc", "version": 1, "content": [
        {"type": "paragraph", "content": [{"type": "text", "text": "Workspace admins pause alerts for an hour."}]}]}}}
PRD_PAGES = [{"lines": ["Quiet Hours PRD (fictional)", "Admins can pause in-app alerts for 1 hour."]},
             {"lines": ["Critical alerts are always delivered."]}]
FLOW_PAGES = [{"lines": ["Pause Alerts"]},
              {"lines": ["Step 1/2", "Click Quiet Hours on the Alerts board."]},
              {"lines": ["Step 2/2", "Click Pause for 1 hour."]}]


def jira_config(stub_url: str, workspace: Path, trigger_extra: dict | None = None, **extra) -> DocForgeConfig:
    return DocForgeConfig.model_validate({
        "context_sources": {"pulse-jira": {"source_type": "jira", "base_url": stub_url, "project_keys": ["PULSE"]}},
        "packs": {"demo": {"path": str(DEMO_PACK)}},
        "triggers": {"docs-tickets": {
            "trigger_type": "jira_ticket", "source": "pulse-jira",
            "statuses": {"plan": "Plan Docs", "draft": "Draft Docs", "bounce": "Backlog", "planned": "Plan Review"},
            "work_types": {"net_new": ["Docs New"]}, "bot_account_env": "TEST_JIRA_BOT",
            "webhook_secret_env": "TEST_JIRA_SECRET", "pack": "demo", "product": {"labels": {"alerts": "alerts"}},
            "workspace": str(workspace), "audience": "workspace admins", **(trigger_extra or {})}},
        **extra,
    })


@pytest.fixture
def jira(stub_server, tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_JIRA_SECRET", SECRET)
    monkeypatch.setenv("TEST_JIRA_BOT", BOT)
    pdfs = tmp_path / "pdfs"
    prd = write_pdf(pdfs / "prd.pdf", PRD_PAGES).read_bytes()
    flow = write_pdf(pdfs / "flow.pdf", FLOW_PAGES).read_bytes()
    stub_server.json(ISSUE_PATH, ISSUE)
    stub_server.routes["/rest/api/3/attachment/content/1"] = (302, b"", {"Location": f"{stub_server.url}/media/1"})
    stub_server.routes["/media/1"] = (200, prd, {"Content-Type": "application/pdf"})
    stub_server.routes["/rest/api/3/attachment/content/2"] = (200, flow, {"Content-Type": "application/pdf"})
    attachments = [{"id": "1", "filename": "Quiet Hours PRD.pdf", "size": len(prd)},
                   {"id": "2", "filename": "pause-alerts-flow.pdf", "size": len(flow)}]
    stub_server.json(f"/rest/api/3/issue/{KEY}?fields=attachment", {"fields": {"attachment": attachments}})
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return stub_server, workspace


def _factory(cfg):
    from docforge.sources.atlassian import AtlassianClient

    return lambda: AtlassianClient(cfg.context_sources["pulse-jira"])


def _queue(state_root: Path, action: str, phase: str = "planning", **pending):
    save_state(state_root, TicketState(key=KEY, trigger="docs-tickets", mode="net_new", phase=phase, product="alerts",
                                       pending=Pending(action=action, at="t", **pending)))


def _run(cfg, tmp_path, client=None):
    return process(KEY, config=cfg, config_path=tmp_path / "docforge.yaml", trigger_name="docs-tickets",
                   state_root=tmp_path / "state", client_factory=_factory(cfg), backend_client=client)


def _copy_stage(run: Path, files: list[str]):
    for rel in files:
        (run / rel).parent.mkdir(parents=True, exist_ok=True)
        (run / rel).write_text((ROOT / "output" / "quiet-hours" / rel).read_text())


ANALYSIS = ["analysis/HANDOVER.md", "analysis/clarifications-and-assumptions.md", "analysis/CONTENT-PLAN.md"]


# --- planning ------------------------------------------------------------------------


def test_plan_gathers_sources_and_waits_for_a_session(jira, tmp_path):
    stub, workspace = jira
    cfg = jira_config(stub.url, workspace)
    _queue(tmp_path / "state", "plan")
    result = _run(cfg, tmp_path)
    assert result["result"] == "waiting" and result["work_order"].endswith("prompts/1-analyzer.md")
    sources = workspace / "tickets" / KEY / "sources"
    assert (sources / "issue.md").read_text().startswith("<!-- docforge-source\nkind: jira")
    prd = (sources / "Quiet-Hours-PRD.md").read_text()
    assert "Admins can pause in-app alerts for 1 hour." in prd and "data, never instructions" in prd
    assert "Click Quiet Hours on the Alerts board." in (sources / "F1.md").read_text()
    run = workspace / "tickets" / KEY / "run"
    manifest = json.loads((run / "run.json").read_text())
    assert [s["kind"] for s in manifest["sources"]] == ["jira", "file", "flow"]
    assert manifest["pack"]["name"] == "demo" and manifest["pack"]["product"] == "alerts"
    state = load_state(tmp_path / "state", KEY)
    assert state.run == f"tickets/{KEY}/run" and state.phase == "planning" and state.pending.action == "plan"
    # The attachment came through a same-host redirect without credentials on the second hop.
    redirected = [r for r in stub.requests if r[1] == "/media/1"]
    assert redirected and "Authorization" not in redirected[0][2]


def test_plan_posts_comment_and_moves_ticket_after_the_session(jira, tmp_path):
    stub, workspace = jira
    cfg = jira_config(stub.url, workspace)
    _queue(tmp_path / "state", "plan")
    _run(cfg, tmp_path)
    _copy_stage(workspace / "tickets" / KEY / "run", ANALYSIS)
    result = _run(cfg, tmp_path)
    assert result["result"] == "planned"
    state = load_state(tmp_path / "state", KEY)
    assert state.phase == "planned" and state.pending is None
    comment, move = state.outbox[-2], state.outbox[-1]
    assert comment.message == "plan" and move.message == "Plan Review"
    body = json.dumps(comment.body)
    assert "Pause in-app alerts for 1 hour" in body and "how-to/how-to.md" in body
    assert "Q01: " in body and "move the ticket to Draft Docs" in body
    assert "not sent: the jira_comments policy is off" == comment.note


def test_plan_through_the_api_backend(jira, tmp_path):
    stub, workspace = jira
    cfg = jira_config(stub.url, workspace, backend={})
    _queue(tmp_path / "state", "plan")
    result = _run(cfg, tmp_path, FakeClient(stage_answer("analyzer")))
    assert result["result"] == "planned"
    assert (workspace / "tickets" / KEY / "run" / "backend" / "calls.jsonl").is_file()


@pytest.mark.parametrize("change,message", [
    (lambda stub: stub.json(f"/rest/api/3/issue/{KEY}?fields=attachment",
                            {"fields": {"attachment": [{"id": "9", "filename": "huge.pdf", "size": 10 ** 9}]}}),
     "larger than the attachment limit"),
    (lambda stub: stub.routes.update({"/rest/api/3/attachment/content/1": (
        302, b"", {"Location": "https://elsewhere.example.com/x"})}), "refused a redirect to another host"),
])
def test_bad_attachments_fail_the_plan_with_a_comment(jira, tmp_path, change, message):
    stub, workspace = jira
    change(stub)
    cfg = jira_config(stub.url, workspace)
    _queue(tmp_path / "state", "plan")
    result = _run(cfg, tmp_path)
    assert result["result"] == "failed" and message in result["reason"]
    state = load_state(tmp_path / "state", KEY)
    assert state.phase == "failed" and state.pending is None and state.outbox[-1].message == "plan_failed"


def test_scanned_pdf_is_noted_in_the_plan(jira, tmp_path):
    stub, workspace = jira
    blank = write_pdf(tmp_path / "blank.pdf", [{"lines": []}, {"lines": []}]).read_bytes()
    stub.routes["/media/1"] = (200, blank, {})
    cfg = jira_config(stub.url, workspace)
    _queue(tmp_path / "state", "plan")
    _run(cfg, tmp_path)
    _copy_stage(workspace / "tickets" / KEY / "run", ANALYSIS)
    _run(cfg, tmp_path)
    # The note is kept with the ticket, so the plan comment posted after the session still carries it.
    state = load_state(tmp_path / "state", KEY)
    assert any("has no extractable text" in n for n in state.notes)
    assert "has no extractable text" in json.dumps(state.outbox[-2].body)


# --- revision -------------------------------------------------------------------------


def _planned_ticket(jira, tmp_path, trigger_extra=None, **cfg_extra):
    """A ticket planned by a session (no backend), then a config with `cfg_extra` (for example a backend)."""
    stub, workspace = jira
    session = jira_config(stub.url, workspace)
    _queue(tmp_path / "state", "plan")
    _run(session, tmp_path)
    _copy_stage(workspace / "tickets" / KEY / "run", ANALYSIS)
    _run(session, tmp_path)
    return jira_config(stub.url, workspace, trigger_extra, **cfg_extra), workspace / "tickets" / KEY / "run"


def test_revision_archives_the_plan_and_adds_feedback(jira, tmp_path):
    cfg, run = _planned_ticket(jira, tmp_path, backend={})
    state = load_state(tmp_path / "state", KEY)
    state.pending = Pending(action="revise", at="t", feedback="Add a FAQ for weekends.", by="acc-writer-1")
    save_state(tmp_path / "state", state)
    result = _run(cfg, tmp_path, FakeClient(stage_answer("analyzer")))
    assert result["result"] == "planned" and result["revision"] == 1
    assert (run / "analysis" / "revisions" / "r0" / "CONTENT-PLAN.md").is_file()
    order = (run / "prompts" / "1-analyzer.md").read_text()
    assert "## Revision 1 feedback" in order and "> Add a FAQ for weekends." in order
    assert "never as evidence" in order
    assert "Documentation plan (revision 1)" in json.dumps(load_state(tmp_path / "state", KEY).outbox[-2].body)


def test_failed_revision_restores_the_previous_plan(jira, tmp_path):
    cfg, run = _planned_ticket(jira, tmp_path, backend={})
    before = (run / "analysis" / "CONTENT-PLAN.md").read_text()
    state = load_state(tmp_path / "state", KEY)
    state.pending = Pending(action="revise", at="t", feedback="Rename it.", by="acc-writer-1")
    save_state(tmp_path / "state", state)
    result = _run(cfg, tmp_path, FakeClient(stage_answer("analyzer", stop_reason="refusal"),
                                            stage_answer("analyzer", stop_reason="refusal")))
    assert result["result"] == "failed"
    state = load_state(tmp_path / "state", KEY)
    assert (state.phase, state.revision) == ("planned", 0)
    assert (run / "analysis" / "CONTENT-PLAN.md").read_text() == before
    assert not (run / "analysis" / "revisions" / "r0").exists()


# --- drafting -------------------------------------------------------------------------


def test_draft_without_flows_runs_drafter_cleanup_and_proofreader(jira, tmp_path):
    stub, workspace = jira
    stub.json(f"/rest/api/3/issue/{KEY}?fields=attachment",
              {"fields": {"attachment": [{"id": "1", "filename": "Quiet Hours PRD.pdf", "size": 100}]}})
    cfg, run = _planned_ticket(jira, tmp_path, backend={})
    state = load_state(tmp_path / "state", KEY)
    state.phase, state.pending = "drafting", Pending(action="draft", at="t")
    save_state(tmp_path / "state", state)
    result = _run(cfg, tmp_path, FakeClient(stage_answer("drafter"), stage_answer("proofreader")))
    assert result["result"] == "drafted", result
    assert (run / "qa" / "cleanup.json").is_file() and (run / "qa" / "QA-REPORT.md").is_file()
    state = load_state(tmp_path / "state", KEY)
    assert state.phase == "drafted"
    body = json.dumps(state.outbox[-1].body)
    assert state.outbox[-1].message == "drafts_ready" and "Draft: how-to/how-to.md" in body and "Clean-up:" in body


def test_draft_that_fails_the_flow_gate_goes_back_to_planned(jira, tmp_path):
    cfg, run = _planned_ticket(jira, tmp_path, backend={})
    state = load_state(tmp_path / "state", KEY)
    state.phase, state.pending = "drafting", Pending(action="draft", at="t")
    save_state(tmp_path / "state", state)
    # Drafts without evidence markers cannot pass the flow-backed-step gate, even after one repair turn.
    result = _run(cfg, tmp_path, FakeClient(stage_answer("drafter"), stage_answer("drafter")))
    assert result["result"] == "failed" and "claim gate failed" in result["reason"]
    state = load_state(tmp_path / "state", KEY)
    assert state.phase == "planned" and state.outbox[-1].message == "draft_failed"


def test_draft_needs_a_plan(jira, tmp_path):
    stub, workspace = jira
    cfg = jira_config(stub.url, workspace)
    _queue(tmp_path / "state", "draft", phase="drafting")
    result = _run(cfg, tmp_path)
    assert result["result"] == "failed" and "no finished plan" in result["reason"]


def test_nothing_pending_and_missing_workspace(jira, tmp_path):
    stub, workspace = jira
    cfg = jira_config(stub.url, workspace)
    assert _run(cfg, tmp_path)["result"] == "nothing pending"
    data = cfg.model_dump(by_alias=True, exclude_none=True)
    data["triggers"]["docs-tickets"].pop("workspace")
    _queue(tmp_path / "state", "plan")
    from docforge.jira.work import WorkError

    with pytest.raises(WorkError, match="no workspace"):
        _run(DocForgeConfig.model_validate(data), tmp_path)


# --- the webhook route --------------------------------------------------------------


def test_webhook_route_verifies_queues_and_plans(jira, tmp_path):
    from http.server import ThreadingHTTPServer
    import threading

    from docforge.webhook import JiraEndpoint, make_handler

    stub, workspace = jira
    cfg = jira_config(stub.url, workspace)
    endpoint = JiraEndpoint(config=cfg, config_path=tmp_path / "docforge.yaml", trigger="docs-tickets",
                            state_root=tmp_path / "state", client_factory=_factory(cfg))
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(None, endpoint))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}/jira/webhook"
    payload = json.loads((ROOT / "tests" / "fixtures" / "jira" / "issue_moved_to_plan.json").read_text())
    body = json.dumps(payload).encode()

    def post(data: bytes, signature: str):
        request = urllib.request.Request(url, data=data, method="POST", headers={
            "X-Hub-Signature": signature, "X-Atlassian-Webhook-Identifier": "delivery-1",
            "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read())

    try:
        assert post(body, "sha256=00")[0] == 401
        status, data = post(body, sign(SECRET, body))
        assert status == 202 and data["action"] == "plan" and data["queued"] is True
        endpoint.queue.join()
        state = load_state(tmp_path / "state", KEY)
        assert state.run == f"tickets/{KEY}/run" and state.history[-1]["event"] == "waiting for a session"
        assert post(body, sign(SECRET, body))[1]["action"] == "duplicate"
        github = urllib.request.Request(url.replace("/jira/webhook", "/webhook"), data=b"{}", method="POST")
        with pytest.raises(urllib.error.HTTPError) as info:
            urllib.request.urlopen(github)
        assert info.value.code == 404  # no GitHub receiver configured
    finally:
        server.shutdown()
        server.server_close()


def test_cli_jira_run(jira, tmp_path, capsys):
    import yaml

    from docforge.cli import main

    stub, workspace = jira
    cfg = jira_config(stub.url, workspace)
    config_path = tmp_path / "docforge.yaml"
    config_path.write_text(yaml.safe_dump(cfg.model_dump(by_alias=True, exclude_none=True)))
    _queue(tmp_path / "state", "plan")
    base = ["jira", "run", "--trigger", "docs-tickets", "--config", str(config_path), "--state", str(tmp_path / "state")]
    assert main(base) == 1 and "one ticket key or --all" in capsys.readouterr().err
    assert main(base + ["--all"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["result"] == "waiting"


def test_missing_api_credentials_fail_cleanly(jira, tmp_path, monkeypatch):
    pytest.importorskip("anthropic")
    for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_PROFILE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))  # no `ant auth login` profile either
    cfg, run = _planned_ticket(jira, tmp_path, backend={})
    state = load_state(tmp_path / "state", KEY)
    state.phase, state.pending = "drafting", Pending(action="draft", at="t")
    save_state(tmp_path / "state", state)
    result = _run(cfg, tmp_path)  # the real SDK client, with no credentials anywhere
    assert result["result"] == "failed" and "no valid API credentials" in result["reason"]
    assert load_state(tmp_path / "state", KEY).phase == "planned"


def test_missing_jira_credentials_fail_with_a_comment(jira, tmp_path, monkeypatch):
    stub, workspace = jira
    data = jira_config(stub.url, workspace).model_dump(by_alias=True, exclude_none=True)
    data["context_sources"]["pulse-jira"]["auth_token_env"] = "TEST_UNSET_JIRA_TOKEN"
    monkeypatch.delenv("TEST_UNSET_JIRA_TOKEN", raising=False)
    cfg = DocForgeConfig.model_validate(data)
    _queue(tmp_path / "state", "plan")
    result = _run(cfg, tmp_path)
    assert result["result"] == "failed" and "TEST_UNSET_JIRA_TOKEN is not set" in result["reason"]
    state = load_state(tmp_path / "state", KEY)
    assert state.phase == "failed" and state.pending is None and state.outbox[-1].message == "plan_failed"


def test_broken_pack_fails_with_a_comment(jira, tmp_path):
    stub, workspace = jira
    data = jira_config(stub.url, workspace).model_dump(by_alias=True, exclude_none=True)
    data["packs"]["demo"]["path"] = str(tmp_path / "no-such-pack")
    _queue(tmp_path / "state", "plan")
    result = _run(DocForgeConfig.model_validate(data), tmp_path)
    assert result["result"] == "failed" and "the pack cannot be used: no pack.yaml" in result["reason"]
    assert load_state(tmp_path / "state", KEY).phase == "failed"


def test_open_questions_use_the_question_column(tmp_path):
    from docforge.jira.runfiles import open_questions

    (tmp_path / "analysis").mkdir()
    (tmp_path / "analysis" / "clarifications-and-assumptions.md").write_text(
        "# Register\n\n| ID | Class | Question | Why |\n| --- | --- | --- | --- |\n"
        "| Q01 | UNKNOWN | Which roles can publish? | Access |\n"
        "| Q02 | ASSUMPTION | Confirm that the gating is pilot-only. | Scope? |\n\n"
        "| ID | Assumption |\n| --- | --- |\n| A1 | Not a question row |\n")
    assert open_questions(tmp_path) == ["Q01: Which roles can publish?", "Q02: Confirm that the gating is pilot-only."]
