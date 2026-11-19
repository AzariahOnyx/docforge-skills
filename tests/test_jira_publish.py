"""The Jira route to a docs pull request (B7a): prepare after drafting, open when the policy allows,
mark ready when the ticket reaches a shipped status.

Stub Jira, fake model client, fake GitHub API and a local bare repository. No network, no key, no cost.
"""

import json
from pathlib import Path
import subprocess
import sys

import pytest

pytest.importorskip("pdfplumber")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conftest import git  # noqa: E402
from github_stub import FakeGithub  # noqa: E402
from test_backend import DONE, FakeClient, answer, stage_answer  # noqa: E402
from test_gate import MARKED, PAGES  # noqa: E402
from test_jira_work import KEY, _planned_ticket, _run, jira  # noqa: E402,F401

from docforge.config import DocForgeConfig  # noqa: E402
from docforge.jira import load_state  # noqa: E402
from docforge.jira.events import parse  # noqa: E402
from docforge.jira.flow import decide  # noqa: E402
from docforge.jira.state import Pending, save_state  # noqa: E402

TOKEN = "fictional-github-token"
COLLECTION = "example-org/docs-site"
FRONT = {
    "feature/feature-guide.md": "---\ntitle: Pause in-app alerts with Quiet Hours\ncategory: Notifications\n---\n\n",
    "how-to/how-to.md": "---\ntitle: Pause your in-app alerts for 1 hour\ncategory: Notifications\n---\n\n",
    "release-note/release-note.md": "---\ntitle: 'Quiet Hours: pause in-app alerts'\n---\n\n",
}


@pytest.fixture
def github(monkeypatch):
    server = FakeGithub(TOKEN)
    monkeypatch.setenv("GITHUB_TOKEN", TOKEN)
    yield server
    server.close()


@pytest.fixture
def docs(tmp_path):
    root = tmp_path / "docs-site"
    (root / "site").mkdir(parents=True)
    git(root, "init", "-q", "-b", "main")
    (root / "site" / "index.md").write_text("# Docs\n")
    git(root, "add", ".")
    git(root, "-c", "user.name=T", "-c", "user.email=t@example.com", "commit", "-q", "-m", "init")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.com")
    bare = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    git(root, "push", "-q", str(bare), "main:main")
    return root, bare


def _drafted(jira, tmp_path, github, docs, *, auto=False, front=FRONT):
    root, bare = docs
    stub, _ = jira
    stub.json(f"/rest/api/3/issue/{KEY}?fields=attachment",  # the PRD only: drafts need no flow-backed steps
              {"fields": {"attachment": [{"id": "1", "filename": "Quiet Hours PRD.pdf", "size": 100}]}})
    extra = {"doc_collections": {COLLECTION: {"filter": ["site/"], "api_url": github.url, "git_url": f"file://{bare}"}},
             "backend": {}}
    if auto:
        extra["policies"] = {"default": {"publishing": {"auto_create_pr": True}}}
    trigger = {"publish": {"collection": COLLECTION, "checkout": str(root)},
               "statuses": {"plan": "Plan Docs", "draft": "Draft Docs", "bounce": "Backlog", "planned": "Plan Review",
                            "shipped": ["Released"]}}
    cfg, run = _planned_ticket(jira, tmp_path, trigger, **extra)
    state = load_state(tmp_path / "state", KEY)
    state.phase, state.pending = "drafting", Pending(action="draft", at="t")
    save_state(tmp_path / "state", state)
    drafts = {p: front.get(p, "") + (MARKED / p).read_text() for p in PAGES}
    drafts["analysis/COVERAGE.md"] = (DONE / "analysis" / "COVERAGE.md").read_text()
    result = process_draft(cfg, tmp_path, FakeClient(answer(drafts), stage_answer("proofreader")), github)
    return cfg, run, result


def process_draft(cfg, tmp_path, client, github):
    from docforge.jira.work import process
    from test_jira_work import _factory

    return process(KEY, config=cfg, config_path=tmp_path / "docforge.yaml", trigger_name="docs-tickets",
                   state_root=tmp_path / "state", client_factory=_factory(cfg), backend_client=client)


def _comment(tmp_path, index=-1) -> tuple[str, str]:
    entry = load_state(tmp_path / "state", KEY).outbox[index]
    return entry.message, json.dumps(entry.body)


def test_drafting_prepares_the_branch_and_says_how_to_open_it(jira, tmp_path, github, docs):
    _, run, result = _drafted(jira, tmp_path, github, docs)
    assert result["result"] == "drafted", result
    root, bare = docs
    assert git(root, "rev-parse", "--verify", "docforge/pulse-77")
    files = git(root, "show", "--name-only", "--format=", "docforge/pulse-77").splitlines()
    assert "site/alerts/notifications/pause-your-in-app-alerts-for-1-hour.md" in files
    assert "site/_docforge/pulse-77.evidence.json" in files
    message, body = _comment(tmp_path)
    assert message == "drafts_ready" and "Docs branch: docforge/pulse-77" in body
    assert "not opened automatically" in body and "docforge publish open" in body
    assert not github.requests  # nothing was pushed or opened
    assert subprocess.run(["git", "-C", str(bare), "rev-parse", "--verify", "--quiet", "docforge/pulse-77"],
                          capture_output=True).returncode != 0


def test_policy_opens_a_draft_pr_and_shipping_marks_it_ready(jira, tmp_path, github, docs):
    cfg, run, result = _drafted(jira, tmp_path, github, docs, auto=True)
    assert result["result"] == "drafted", result
    pr = github.pulls[1]
    assert pr["draft"] and pr["head"]["ref"] == "docforge/pulse-77"
    assert "from run `pulse-77`" in pr["body"] and "stays a **draft** until the feature ships" in pr["body"]
    state = load_state(tmp_path / "state", KEY)
    assert state.pull_request == pr["html_url"]
    _, body = _comment(tmp_path)
    assert f"Draft pull request: {pr['html_url']}" in body

    state.pending = Pending(action="ship", at="t")
    save_state(tmp_path / "state", state)
    shipped = process_draft(cfg, tmp_path, None, github)
    assert shipped["result"] == "shipped" and not github.pulls[1]["draft"]
    message, body = _comment(tmp_path)
    assert message == "shipped" and "ready for review" in body
    assert load_state(tmp_path / "state", KEY).shipped


def test_shipping_without_the_policy_only_records_it(jira, tmp_path, github, docs):
    cfg, run, _ = _drafted(jira, tmp_path, github, docs)
    state = load_state(tmp_path / "state", KEY)
    state.pending = Pending(action="ship", at="t")
    save_state(tmp_path / "state", state)
    assert process_draft(cfg, tmp_path, None, github)["result"] == "shipped"
    _, body = _comment(tmp_path)
    assert "may leave draft" in body and "docforge publish ready" in body
    assert not json.loads((run / "publish" / "pr.json").read_text())["draft"]
    assert not github.requests


def test_missing_front_matter_keeps_the_drafts_and_reports_it(jira, tmp_path, github, docs):
    front = {**FRONT, "how-to/how-to.md": "---\ntitle: Pause your in-app alerts\n---\n\n"}
    _, run, result = _drafted(jira, tmp_path, github, docs, auto=True, front=front)
    assert result["result"] == "drafted", result
    _, body = _comment(tmp_path)
    assert "could not be opened" in body and "no category" in body
    assert not github.pulls and load_state(tmp_path / "state", KEY).phase == "drafted"


def test_shipped_status_starts_work_only_after_drafting():
    from test_jira_front_door import MOVE, config

    trigger = config().triggers["docs-tickets"]
    trigger = trigger.model_copy(update={"statuses": trigger.statuses.model_copy(update={"shipped": ["Released"]})})
    payload = json.loads(json.dumps(MOVE))
    payload["changelog"]["items"][0].update(fromString="Plan Review", toString="Released")
    event = parse(json.dumps(payload).encode())
    from docforge.jira.state import TicketState

    drafted = TicketState(key="PULSE-77", trigger="docs-tickets", mode="net_new", phase="drafted")
    planned = drafted.model_copy(update={"phase": "planned"})
    assert decide(event, drafted, trigger, ["PULSE"], "bot").action == "ship"
    assert decide(event, planned, trigger, ["PULSE"], "bot").action == "ignore"


def test_config_checks_publish_and_shipped():
    from test_jira_work import jira_config

    with pytest.raises(ValueError, match="publish collection 'o/r' is not in doc_collections"):
        jira_config("http://127.0.0.1:1", Path("ws"), {"publish": {"collection": "o/r", "checkout": "docs"}})
    with pytest.raises(ValueError, match="shipped status cannot also be"):
        jira_config("http://127.0.0.1:1", Path("ws"), {"statuses": {
            "plan": "A", "draft": "B", "bounce": "C", "planned": "D", "shipped": ["a"]}})
    assert isinstance(jira_config("http://127.0.0.1:1", Path("ws")), DocForgeConfig)


def test_webhook_worker_runs_ship_work(tmp_path, monkeypatch):
    """A shipped status arriving by webhook is queued for the worker (it was dropped before B7b)."""
    import threading

    from test_jira_front_door import MOVE, SECRET, config

    from docforge.jira import sign
    from docforge.jira.state import TicketState
    from docforge.webhook import JiraEndpoint

    monkeypatch.setenv("TEST_JIRA_SECRET", SECRET)
    monkeypatch.setenv("TEST_JIRA_BOT", "bot")
    ran = threading.Event()
    monkeypatch.setattr("docforge.jira.work.process", lambda key, **kw: ran.set())
    cfg = config()
    trigger = cfg.triggers["docs-tickets"]
    cfg.triggers["docs-tickets"] = trigger.model_copy(update={
        "statuses": trigger.statuses.model_copy(update={"shipped": ["Released"]})})
    save_state(tmp_path / "state", TicketState(key="PULSE-77", trigger="docs-tickets", mode="net_new", phase="drafted"))
    payload = json.loads(json.dumps(MOVE))
    payload["changelog"]["items"][0].update(fromString="Plan Review", toString="Released")
    body = json.dumps(payload).encode()
    endpoint = JiraEndpoint(config=cfg, config_path=tmp_path / "docforge.yaml", trigger="docs-tickets",
                            state_root=tmp_path / "state")
    status, result = endpoint.handle({"X-Hub-Signature": sign(SECRET, body)}, body)
    assert status == 202 and result["action"] == "ship" and result["queued"]
    assert ran.wait(5)
