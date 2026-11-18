"""The Jira front door (B6a): deliveries, decisions, state and outbox. Fictional recordings; no network."""

import copy
import json
from pathlib import Path

import pytest

from docforge.cli import main
from docforge.config import DocForgeConfig
from docforge.jira import HandleError, handle, load_state, parse, sign, verify_signature
from docforge.jira.events import comment_body
from docforge.jira.state import TicketState, save_state

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "jira"
MOVE = json.loads((FIXTURES / "issue_moved_to_plan.json").read_text())
MENTION = json.loads((FIXTURES / "comment_mention.json").read_text())
SECRET = "fictional-webhook-secret"
BOT = "acc-docforge-bot"
STATUSES = {"plan": "Plan Docs", "draft": "Draft Docs", "bounce": "Backlog", "planned": "Plan Review"}


def config(**publishing) -> DocForgeConfig:
    return DocForgeConfig.model_validate({
        "context_sources": {"pulse-jira": {"source_type": "jira", "base_url": "https://example.atlassian.net",
                                           "project_keys": ["PULSE"]}},
        "triggers": {"docs-tickets": {
            "trigger_type": "jira_ticket", "source": "pulse-jira", "statuses": STATUSES,
            "work_types": {"net_new": ["Docs New"], "enhancement": ["Docs Update"]},
            "bot_account_env": "TEST_JIRA_BOT", "webhook_secret_env": "TEST_JIRA_SECRET",
            "product": {"labels": {"alerts": "alerts"}, "default": "boards"}}},
        "policies": {"default": {"publishing": publishing}} if publishing else {},
    })


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("TEST_JIRA_SECRET", SECRET)
    monkeypatch.setenv("TEST_JIRA_BOT", BOT)


def move(to: str, *, frm: str = "Backlog", attachments=None, key="PULSE-77", work_type="Docs New") -> bytes:
    payload = copy.deepcopy(MOVE)
    payload["issue"]["key"] = key
    payload["issue"]["fields"]["issuetype"]["name"] = work_type
    payload["changelog"]["items"][0].update(fromString=frm, toString=to)
    if attachments is not None:
        payload["issue"]["fields"]["attachment"] = attachments
    return json.dumps(payload).encode()


def mention(text: str = " please add a troubleshooting article.", *, author="acc-writer-1") -> bytes:
    payload = copy.deepcopy(MENTION)
    payload["comment"]["author"]["accountId"] = author
    payload["comment"]["body"]["content"][0]["content"][1]["text"] = text
    return json.dumps(payload).encode()


def deliver(tmp_path, body: bytes, cfg=None, delivery=None, **kw) -> dict:
    return handle(body, config=cfg or config(), trigger_name="docs-tickets", state_root=tmp_path / "state",
                  signature=sign(SECRET, body), delivery_id=delivery, **kw)


def state(tmp_path):
    return load_state(tmp_path / "state", "PULSE-77")


# --- events --------------------------------------------------------------------------


def test_parse_status_move_and_comment():
    event = parse(json.dumps(MOVE).encode())
    assert (event.kind, event.issue_key, event.project, event.work_type) == ("status", "PULSE-77", "PULSE", "Docs New")
    assert (event.status_from, event.status_to) == ("Backlog", "Plan Docs")
    assert event.owners == ["acc-writer-1", "acc-writer-2"]
    assert [a.filename for a in event.attachments] == ["quiet-hours-prd.pdf", "create-quiet-hours-flow.pdf", "mockup.png"]
    comment = parse(json.dumps(MENTION).encode())
    assert comment.kind == "comment" and comment.comment_author == "acc-writer-1"
    assert comment.comment_mentions == [BOT]
    assert comment.comment_text == "please add a troubleshooting article for alerts that still notify during Quiet Hours."


def test_wiki_markup_comments_and_bad_payloads():
    text, mentions = comment_body("[~accountid:acc-docforge-bot] add a FAQ")
    assert (text, mentions) == ("add a FAQ", [BOT])
    for body in (b"not json", b"{}", json.dumps({"issue": {"key": "../etc"}}).encode()):
        with pytest.raises(Exception):
            parse(body)


def test_signatures():
    body = move("Plan Docs")
    assert verify_signature(SECRET, body, sign(SECRET, body))
    assert not verify_signature(SECRET, body + b" ", sign(SECRET, body))
    assert not verify_signature(SECRET, body, "sha1=abc") and not verify_signature("", body, sign(SECRET, body))


def test_bad_or_missing_signature_is_refused(tmp_path, monkeypatch):
    body = move("Plan Docs")
    with pytest.raises(HandleError, match="signature does not match"):
        handle(body, config=config(), trigger_name="docs-tickets", state_root=tmp_path, signature="sha256=00")
    monkeypatch.delenv("TEST_JIRA_SECRET")
    with pytest.raises(HandleError, match="TEST_JIRA_SECRET is not set"):
        deliver(tmp_path, body)
    assert not (tmp_path / "state").exists()


# --- status moves --------------------------------------------------------------------


def test_move_to_plan_queues_planning(tmp_path):
    result = deliver(tmp_path, move("Plan Docs"))
    assert (result["action"], result["phase"]) == ("plan", "planning")
    s = state(tmp_path)
    assert s.mode == "net_new" and s.product == "alerts" and s.pending.action == "plan" and s.outbox == []


def test_other_projects_work_types_and_statuses_are_ignored_silently(tmp_path):
    assert deliver(tmp_path, move("Plan Docs", key="OTHER-1"))["action"] == "ignore"
    assert deliver(tmp_path, move("Plan Docs", work_type="Bug"))["reason"].startswith("Work Type 'Bug'")
    assert deliver(tmp_path, move("Done"))["action"] == "ignore"
    # DocForge's own moves land on unwatched statuses and are ignored: no loop.
    assert deliver(tmp_path, move("Plan Review", frm="Plan Docs"))["action"] == "ignore"
    assert deliver(tmp_path, move("Backlog", frm="Plan Docs"))["action"] == "ignore"
    assert not (tmp_path / "state").exists()


def test_enhancement_work_type_and_default_product(tmp_path):
    payload = json.loads(move("Plan Docs", work_type="Docs Update"))
    payload["issue"]["fields"]["labels"] = []
    deliver(tmp_path, json.dumps(payload).encode())
    assert (state(tmp_path).mode, state(tmp_path).product) == ("enhancement", "boards")


def test_bounce_without_usable_attachment(tmp_path):
    result = deliver(tmp_path, move("Plan Docs", attachments=[{"id": "1", "filename": "mockup.png", "size": 10}]))
    assert result["action"] == "bounce" and result["comment"]["message"] == "bounce_no_attachments"
    assert result["move"] == {**result["move"], "kind": "transition", "message": "Backlog", "sent": False}
    assert "jira_transitions policy is off" in result["move"]["note"]
    s = state(tmp_path)
    assert s.phase == "new" and s.pending is None
    assert [e.kind for e in s.outbox] == ["comment", "transition"]
    body = json.dumps(s.outbox[0].body)
    assert "no PDF or MD attachment" in body and "Posted by DocForge" in body


def test_bounce_for_oversized_attachments_names_them(tmp_path):
    big = [{"id": "1", "filename": "huge-prd.pdf", "size": 50 * 1024 * 1024}]
    result = deliver(tmp_path, move("Plan Docs", attachments=big))
    assert result["comment"]["message"] == "bounce_oversized"
    assert "huge-prd.pdf" in json.dumps(result["comment"]["body"])


def test_draft_before_plan_pulls_back_then_plans(tmp_path):
    result = deliver(tmp_path, move("Draft Docs", frm="Backlog"))
    assert result["action"] == "pull_back" and result["move"]["message"] == "Plan Docs"
    assert state(tmp_path).phase == "new"
    # The pull-back fires a move into the plan status, which plans (one hop, no loop).
    assert deliver(tmp_path, move("Plan Docs", frm="Draft Docs"))["action"] == "plan"


def test_lifecycle_replies(tmp_path):
    root = tmp_path / "state"
    deliver(tmp_path, move("Plan Docs"))
    assert deliver(tmp_path, move("Plan Docs", frm="Backlog"), delivery="again")["reason"] == "already planning"
    pull = deliver(tmp_path, move("Draft Docs", frm="Plan Docs"))
    assert pull["action"] == "pull_back" and "still being prepared" in json.dumps(pull["comment"]["body"])
    s = state(tmp_path)
    s.phase = "planned"
    save_state(root, s)
    assert deliver(tmp_path, move("Plan Docs", frm="Plan Review"))["comment"]["message"] == "already_planned"
    draft = deliver(tmp_path, move("Draft Docs", frm="Plan Review"))
    assert (draft["action"], draft["phase"]) == ("draft", "drafting") and state(tmp_path).pending.action == "draft"
    assert deliver(tmp_path, move("Draft Docs", frm="Plan Review"), delivery="d2")["reason"] == "drafting in progress"
    s = state(tmp_path)
    s.phase, s.run = "drafted", "runs/PULSE-77"
    save_state(root, s)
    assert deliver(tmp_path, move("Plan Docs", frm="Draft Docs"))["comment"]["message"] == "drafts_exist"
    assert deliver(tmp_path, move("Draft Docs", frm="Plan Review"), delivery="d3")["comment"]["message"] == "drafts_ready"


def test_repeated_delivery_is_ignored(tmp_path):
    body = move("Plan Docs")
    deliver(tmp_path, body, delivery="abc")
    assert deliver(tmp_path, body, delivery="abc")["action"] == "duplicate"
    assert len(state(tmp_path).processed) == 1


# --- mentions ------------------------------------------------------------------------


def _planned(tmp_path):
    save_state(tmp_path / "state", TicketState(key="PULSE-77", trigger="docs-tickets", mode="net_new", phase="planned"))


def test_owner_mention_queues_a_revision(tmp_path):
    _planned(tmp_path)
    result = deliver(tmp_path, mention())
    assert result["action"] == "revise"
    pending = state(tmp_path).pending
    assert (pending.action, pending.by, pending.feedback) == ("revise", "acc-writer-1",
                                                             "please add a troubleshooting article.")
    # The assignee is an owner too.
    assert deliver(tmp_path, mention(" and a FAQ.", author="acc-writer-2"))["action"] == "revise"


def test_mentions_that_cannot_revise(tmp_path):
    _planned(tmp_path)
    assert deliver(tmp_path, mention(author="acc-stranger"))["reason"].startswith("mention by someone who is not")
    assert deliver(tmp_path, mention(author=BOT))["reason"] == "comment by DocForge itself"
    bare = deliver(tmp_path, mention("   "))
    assert bare["comment"]["message"] == "ask_specifics" and state(tmp_path).pending is None
    no_mention = json.loads(mention())
    no_mention["comment"]["body"]["content"][0]["content"].pop(0)
    assert deliver(tmp_path, json.dumps(no_mention).encode())["reason"] == "comment does not mention DocForge"
    s = state(tmp_path)
    s.phase = "drafted"
    save_state(tmp_path / "state", s)
    assert deliver(tmp_path, mention(" rename it."))["comment"]["message"] == "revision_refused"


def test_mention_without_a_plan(tmp_path):
    result = deliver(tmp_path, mention())
    assert result["comment"]["message"] == "no_plan_yet"


def test_unset_bot_account_never_matches(tmp_path, monkeypatch):
    monkeypatch.delenv("TEST_JIRA_BOT")
    _planned(tmp_path)
    assert deliver(tmp_path, mention())["reason"] == "comment does not mention DocForge"


# --- writing to Jira (local stub only) -------------------------------------------------


def test_policy_on_posts_comment_and_moves_ticket(tmp_path, stub_server):
    stub_server.json("/rest/api/3/issue/PULSE-77/comment", {"id": "50001"}, status=201)
    stub_server.json("/rest/api/3/issue/PULSE-77/transitions",
                     {"transitions": [{"id": "11", "to": {"name": "Backlog"}}, {"id": "21", "to": {"name": "Plan Docs"}}]})
    cfg = DocForgeConfig.model_validate({**config(jira_comments=True, jira_transitions=True).model_dump(
        by_alias=True, exclude_none=True)})
    cfg.context_sources["pulse-jira"].base_url = stub_server.url

    def factory():
        from docforge.sources.atlassian import AtlassianClient

        return AtlassianClient(cfg.context_sources["pulse-jira"])

    result = deliver(tmp_path, move("Plan Docs", attachments=[]), cfg=cfg, client_factory=factory)
    assert result["comment"]["sent"] is True and result["move"]["sent"] is True
    posts = [(m, p, json.loads(b)) for m, p, _, b in stub_server.requests if m == "POST"]
    assert posts[0][1] == "/rest/api/3/issue/PULSE-77/comment" and posts[0][2]["body"]["type"] == "doc"
    assert posts[1] == ("POST", "/rest/api/3/issue/PULSE-77/transitions", {"transition": {"id": "11"}})


def test_missing_transition_and_write_errors_are_recorded(tmp_path, stub_server):
    stub_server.json("/rest/api/3/issue/PULSE-77/transitions", {"transitions": []})
    stub_server.json("/rest/api/3/issue/PULSE-77/comment", {"errorMessages": ["no"]}, status=403)
    cfg = config(jira_comments=True, jira_transitions=True)
    cfg.context_sources["pulse-jira"].base_url = stub_server.url
    from docforge.sources.atlassian import AtlassianClient

    result = deliver(tmp_path, move("Plan Docs", attachments=[]), cfg=cfg,
                     client_factory=lambda: AtlassianClient(cfg.context_sources["pulse-jira"]))
    assert result["comment"]["sent"] is False and "HTTP 403" in result["comment"]["note"]
    assert result["move"]["note"] == "not moved: the workflow has no transition to Backlog"


# --- config and CLI -------------------------------------------------------------------


@pytest.mark.parametrize("change,message", [
    (lambda t: t.update(source="nope"), "not a jira context source"),
    (lambda t: t["statuses"].update(draft="Plan Docs"), "must be different"),
    (lambda t: t.update(work_types={}), "at least one Work Type"),
    (lambda t: t.update(work_types={"net_new": ["A"], "enhancement": ["a"]}), "both net_new and enhancement"),
    (lambda t: t.update(bot_account_env="acc-123"), "environment variable name"),
    (lambda t: t.update(pack="missing"), "not in packs"),
])
def test_trigger_config_is_strict(change, message):
    data = config().model_dump(by_alias=True, exclude_none=True)
    change(data["triggers"]["docs-tickets"])
    with pytest.raises(ValueError, match=message):
        DocForgeConfig.model_validate(data)


def test_writes_are_off_by_default():
    publishing = config().resolve_policy(trigger="docs-tickets", doc_collection=None)["publishing"]
    assert publishing["jira_comments"] is False and publishing["jira_transitions"] is False


def test_cli_handle_and_state(tmp_path, capsys):
    import yaml

    cfg_path = tmp_path / "docforge.yaml"
    cfg_path.write_text(yaml.safe_dump(config().model_dump(by_alias=True, exclude_none=True)))
    payload = tmp_path / "delivery.json"
    payload.write_bytes(move("Plan Docs", attachments=[]))
    state_dir = tmp_path / "state"
    base = ["jira", "handle", str(payload), "--trigger", "docs-tickets", "--config", str(cfg_path), "--state", str(state_dir)]
    assert main(base) == 1
    assert "--signature" in capsys.readouterr().err
    assert main(base + ["--signature", sign(SECRET, payload.read_bytes())]) == 0
    assert json.loads(capsys.readouterr().out)["action"] == "bounce"
    assert main(["jira", "state", "PULSE-77", "--state", str(state_dir)]) == 0
    out = capsys.readouterr().out
    assert "PULSE-77: phase new" in out and "comment bounce_no_attachments: not sent" in out
    assert main(["jira", "state", "../x", "--state", str(state_dir)]) == 1
