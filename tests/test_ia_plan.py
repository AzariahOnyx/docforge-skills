"""The plan as ia-plan.md (B7c-1): format checks, the Analyzer output, the plan pull request, Jira links.

Stub Jira, fake model client, fake GitHub API and a local bare repository. No network, no key, no cost.
"""

import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

pytest.importorskip("pdfplumber")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conftest import git  # noqa: E402
from github_stub import FakeGithub  # noqa: E402
from test_backend import DONE, FakeClient, answer  # noqa: E402
from test_jira_work import ANALYSIS, KEY, _copy_stage, _factory, _queue, jira, jira_config  # noqa: E402,F401

from docforge.cli import main  # noqa: E402
from docforge.jira import load_state  # noqa: E402
from docforge.jira.work import process  # noqa: E402
from docforge.plan import parse_plan, read_plan  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "plan" / "ia-plan.md"
TOKEN = "fictional-github-token"
COLLECTION = "example-org/docs-site"


def text(**changes) -> str:
    body = FIXTURE.read_text()
    for old, new in changes.items():
        body = body.replace(old.replace("_", " "), new) if " " in old.replace("_", " ") else body.replace(old, new)
    return body


# --- format -------------------------------------------------------------------------------


def test_fixture_plan_reads_back():
    plan, errors = read_plan(FIXTURE.read_text(), types=["overview", "procedural", "faq"],
                             allows=lambda p: p.startswith("site/"))
    assert errors == []
    assert plan.front["feature"] == "Quiet Hours" and plan.existing == [] and len(plan.new) == 2
    assert [a["path"] for a in plan.articles()] == ["site/alerts/notifications/quiet-hours.md",
                                                     "site/alerts/notifications/pause-for-1-hour.md"]
    assert [q["ID"] for q in plan.questions] == ["Q01", "Q02"] and plan.conflicts == []


@pytest.mark.parametrize("old, new, message", [
    ("mode: Net-New", "mode: New", "mode must be Net-New or Enhancement"),
    ("owner: unknown\n", "", "owner is missing"),
    ("release: unknown", "release: unknown\nteam: docs", "unknown key team"),
    ("| overview |", "| tutorial |", "type 'tutorial' is not one of"),
    ("site/alerts/notifications/pause-for-1-hour.md", "site/alerts/notifications/quiet-hours.md", "used twice"),
    ("site/alerts/notifications/quiet-hours.md", "../secret.md", "relative .md path"),
    ("| Q02 |", "| Question 2 |", "must look like Q01"),
    ("| C01, C02, C04 |", "| claims 1 and 2 |", "are not claim IDs"),
    ("| Title | Type | Docs path | Why | Claims |", "| Title | Kind | Docs path | Why | Claims |", "columns must be"),
    ("## Out of scope", "## Not in scope", "missing section: ## Out of scope"),
    ("source_prs: []", "source_prs: [main]", "source_prs must be a list"),
])
def test_plan_problems_are_reported(old, new, message):
    body = FIXTURE.read_text().replace(old, new)
    _, errors = read_plan(body, types=["overview", "procedural", "faq"], allows=lambda p: p.startswith("site/"))
    assert any(message in e for e in errors), errors


def test_filter_and_unreadable_plans():
    _, errors = read_plan(FIXTURE.read_text(), types=["overview", "procedural"], allows=lambda p: p.startswith("docs/"))
    assert any("outside the doc collection's filter" in e for e in errors)
    assert parse_plan("# no front matter")[0] is None
    body = FIXTURE.read_text().split("## New articles")[0] + "## New articles\n\nNone.\n"
    _, errors = read_plan(body)
    assert "the plan has no article to create or update" in errors


def test_cli_plan_check(capsys, tmp_path):
    assert main(["plan", "check", str(FIXTURE), "--config", str(tmp_path / "none.yaml")]) == 0
    assert "PASS: Quiet Hours: 2 new" in capsys.readouterr().out
    bad = tmp_path / "ia-plan.md"
    bad.write_text(FIXTURE.read_text().replace("mode: Net-New", "mode: Later"))
    assert main(["plan", "check", str(bad), "--config", str(tmp_path / "none.yaml")]) == 1
    assert "FAIL: front matter: mode" in capsys.readouterr().out


# --- the Jira route -------------------------------------------------------------------------


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


def plan_config(jira, github, docs, *, auto=True, **extra):
    stub, workspace = jira
    root, bare = docs
    cfg = {"doc_collections": {COLLECTION: {"filter": ["site/"], "api_url": github.url, "git_url": f"file://{bare}"}},
           **extra}
    if auto:
        cfg["policies"] = {"default": {"publishing": {"auto_create_pr": True}}}
    return jira_config(stub.url, workspace, {"publish": {"collection": COLLECTION, "checkout": str(root),
                                                          "plan_pr": True}}, **cfg)


def run_ticket(cfg, tmp_path, client=None, github_client=None):
    return process(KEY, config=cfg, config_path=tmp_path / "docforge.yaml", trigger_name="docs-tickets",
                   state_root=tmp_path / "state", client_factory=_factory(cfg), backend_client=client,
                   github_client=github_client)


def _session_plan(run: Path, plan_text: str):
    _copy_stage(run, ANALYSIS)
    (run / "analysis" / "ia-plan.md").write_text(plan_text)


def test_ticket_plan_becomes_a_plan_pr_linked_from_jira(jira, tmp_path, github, docs):
    cfg = plan_config(jira, github, docs)
    _queue(tmp_path / "state", "plan")
    waiting = run_ticket(cfg, tmp_path)
    assert waiting["result"] == "waiting"
    run = jira[1] / "tickets" / KEY / "run"
    manifest = json.loads((run / "run.json").read_text())
    assert manifest["ia_plan"] == {"mode": "Net-New", "product": "alerts", "jira": KEY, "docforge_run": "pulse-77"}
    order = (run / "prompts" / "1-analyzer.md").read_text()
    assert "## IA plan" in order and "`analysis/ia-plan.md`" in order and "templates/ia-plan.md" in order
    assert "mode: Net-New; product: alerts; jira: PULSE-77" in order
    assert "site/{product}/{category}/{slug}.md" in order  # the pack's placement templates
    assert "Article types: procedural, overview, faq." in order

    _session_plan(run, FIXTURE.read_text())
    result = run_ticket(cfg, tmp_path)
    assert result["result"] == "planned", result
    pr = github.pulls[1]
    assert not pr["draft"] and pr["head"]["ref"] == "docforge/plan-quiet-hours"
    assert pr["title"] == "docs plan: Quiet Hours (DocForge)" and "approves the plan" in pr["body"]
    assert git(docs[1], "show", "docforge/plan-quiet-hours:plans/quiet-hours/ia-plan.md") == \
        FIXTURE.read_text().rstrip("\n")
    state = load_state(tmp_path / "state", KEY)
    assert state.plan_pr == pr["html_url"] and state.phase == "planned"
    comment, move = state.outbox[-2], state.outbox[-1]
    assert comment.message == "plan_pr" and pr["html_url"] in json.dumps(comment.body)
    assert "approving the pull request approves the plan" in json.dumps(comment.body)
    assert move.kind == "transition" and move.message == "Plan Review"


def test_without_the_policy_the_comment_gives_the_command(jira, tmp_path, github, docs):
    cfg = plan_config(jira, github, docs, auto=False)
    _queue(tmp_path / "state", "plan")
    run_ticket(cfg, tmp_path)
    _session_plan(jira[1] / "tickets" / KEY / "run", FIXTURE.read_text())
    assert run_ticket(cfg, tmp_path)["result"] == "planned"
    assert not github.requests
    state = load_state(tmp_path / "state", KEY)
    assert state.plan_pr == "docforge/plan-quiet-hours"
    assert "docforge plan open tickets/PULSE-77/run" in json.dumps(state.outbox[-2].body)
    assert git(docs[0], "rev-parse", "--verify", "docforge/plan-quiet-hours")


def test_a_broken_plan_file_fails_the_plan(jira, tmp_path, github, docs):
    cfg = plan_config(jira, github, docs)
    _queue(tmp_path / "state", "plan")
    run_ticket(cfg, tmp_path)
    _session_plan(jira[1] / "tickets" / KEY / "run", FIXTURE.read_text().replace("mode: Net-New", "mode: Soon"))
    result = run_ticket(cfg, tmp_path)
    assert result["result"] == "failed" and "ia-plan.md has problems: front matter: mode" in result["reason"]
    assert not github.pulls and load_state(tmp_path / "state", KEY).phase == "failed"


def test_backend_repairs_a_broken_plan(jira, tmp_path, github, docs):
    cfg = plan_config(jira, github, docs, backend={})
    _queue(tmp_path / "state", "plan")
    files = {p: (DONE / p).read_text() for p in ANALYSIS}
    broken = answer({**files, "analysis/ia-plan.md": FIXTURE.read_text().replace("mode: Net-New", "mode: Soon")})
    fixed = answer({**files, "analysis/ia-plan.md": FIXTURE.read_text()})
    client = FakeClient(broken, fixed)
    assert run_ticket(cfg, tmp_path, client)["result"] == "planned"
    repair = client.requests[1]["messages"][-1]["content"]
    assert "ia-plan.md: front matter: mode must be Net-New or Enhancement" in repair
    assert "templates/ia-plan.md" in client.requests[0]["system"][1]["text"]


def test_drafting_waits_for_plan_pr_approval(jira, tmp_path, github, docs):
    from test_jira_front_door import MOVE, MENTION

    from docforge.jira import handle, sign

    cfg = plan_config(jira, github, docs)
    _queue(tmp_path / "state", "plan")
    run_ticket(cfg, tmp_path)
    _session_plan(jira[1] / "tickets" / KEY / "run", FIXTURE.read_text())
    run_ticket(cfg, tmp_path)
    secret = "fictional-webhook-secret"
    move = json.loads(json.dumps(MOVE))
    move["changelog"]["items"][0].update(fromString="Plan Review", toString="Draft Docs")
    body = json.dumps(move).encode()
    result = handle(body, config=cfg, trigger_name="docs-tickets", state_root=tmp_path / "state",
                    signature=sign(secret, body))
    assert result["action"] == "reply" and "approved in its pull request" in result["reason"]
    state = load_state(tmp_path / "state", KEY)
    assert state.phase == "planned" and state.pending is None
    assert state.outbox[-1].message == "approve_plan_pr" and github.pulls[1]["html_url"] in json.dumps(
        state.outbox[-1].body)
    mention = json.dumps(MENTION).encode()
    result = handle(mention, config=cfg, trigger_name="docs-tickets", state_root=tmp_path / "state",
                    signature=sign(secret, mention))
    assert result["action"] == "reply" and load_state(tmp_path / "state", KEY).outbox[-1].message == "review_on_plan_pr"


def test_plan_prepare_and_open_cli(tmp_path, github, docs, capsys, monkeypatch):
    from docforge.run import start_run

    repo = tmp_path / "repo"
    (repo / "demo").mkdir(parents=True)
    shutil.copy(Path(__file__).resolve().parents[1] / "demo" / "mock-prd.md", repo / "demo" / "mock-prd.md")
    run = start_run(repo=repo, prds=["demo/mock-prd.md"], out=repo / "output" / "qh", audience="members",
                    publish_to=COLLECTION, ia_plan={"jira": "none"})
    (run / "analysis" / "ia-plan.md").write_text(FIXTURE.read_text())
    root, bare = docs
    cfg = tmp_path / "docforge.yaml"
    cfg.write_text(f"doc_collections:\n  {COLLECTION}:\n    filter: [site/]\n    api_url: {github.url}\n"
                   f"    git_url: file://{bare}\n    plan_path: site/_plans/{{slug}}.md\n")
    assert main(["plan", "prepare", str(run), "--docs-checkout", str(root), "--config", str(cfg)]) == 0
    assert "site/_plans/quiet-hours.md" in capsys.readouterr().out
    assert main(["plan", "prepare", str(run), "--docs-checkout", str(root), "--config", str(cfg)]) == 1
    assert "already prepared" in capsys.readouterr().err
    assert main(["plan", "open", str(run), "--docs-checkout", str(root), "--config", str(cfg)]) == 0
    assert "plan pull request #1" in capsys.readouterr().out and not github.pulls[1]["draft"]
    assert (run / "publish" / "plan-pr.json").is_file() and not (run / "publish" / "pr.json").exists()


def test_plan_path_setting_is_checked():
    from docforge.config import DocForgeConfig

    for bad in ("plans/ia-plan.md", "/plans/{slug}.md", "plans/{slug}/{team}.md", "plans/{slug}.txt"):
        with pytest.raises(ValueError, match="plan_path"):
            DocForgeConfig.model_validate({"doc_collections": {"o/r": {"plan_path": bad}}})
