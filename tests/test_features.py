"""The code route (B7d-2): a code pull request that needs docs becomes a feature with a plan pull request,
later pull requests revise the plan or are reported after approval, approval drafts, merges mark drafts ready.

A local code repository, fake GitHub API, local bare docs repository and fake model client. No network, no cost.
"""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conftest import git  # noqa: E402
from test_backend import DONE, FakeClient, stage_answer  # noqa: E402
from test_ia_plan import FIXTURE, docs, github  # noqa: E402,F401
from test_jira_work import ANALYSIS  # noqa: E402
from test_plan_review import approve, drafts  # noqa: E402

from docforge.config import DocForgeConfig  # noqa: E402
from docforge.features import (  # noqa: E402
    feature_key,
    list_features,
    load_feature,
    on_comment,
    on_decision,
    on_merged,
    process_feature,
    queue_draft_after_approval,
    start_or_add,
)
from docforge.github.events import parse_docs_event  # noqa: E402
from docforge.plan.review import handle_plan_event, process_plan_pr  # noqa: E402
from docforge.publish import load_plan  # noqa: E402

CODE = "example-org/pulseboard-web"
DOCS = "example-org/docs-site"
BOT = "docforge-bot"
ROOT = Path(__file__).resolve().parents[1]
LATER = datetime.now(timezone.utc) + timedelta(days=1)


@pytest.fixture
def code(tmp_path):
    """A local code repository: base commit, then a head commit changing the spec and the alerts code."""
    root = tmp_path / "pulseboard-web"
    (root / "src" / "alerts").mkdir(parents=True)
    (root / "specs" / "quiet-hours").mkdir(parents=True)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.name", "Dev")
    git(root, "config", "user.email", "dev@example.com")
    (root / "src" / "alerts" / "pause.ts").write_text("export const pause = () => {};\n")
    (root / "specs" / "quiet-hours" / "spec.md").write_text("# Quiet Hours spec\n\nDraft.\n")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "base")
    base = git(root, "rev-parse", "HEAD")
    (root / "specs" / "quiet-hours" / "spec.md").write_text(
        "# Quiet Hours spec\n\nMembers can pause in-app alerts for 1 hour.\n")
    (root / "src" / "alerts" / "pause.ts").write_text("export const pause = (hours = 1) => hours;\n")
    git(root, "commit", "-q", "-am", "Quiet Hours")
    head = git(root, "rev-parse", "HEAD")
    (root / "src" / "alerts" / "resume.ts").write_text("export const resume = () => true;\n")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "Resume now")
    later = git(root, "rev-parse", "HEAD")
    return root, base, head, later


def make_config(tmp_path, code, docs, github, *, backend=False, auto=True, jira=False) -> DocForgeConfig:  # noqa: F811
    root, bare = docs
    data = {
        "doc_collections": {DOCS: {"filter": ["site/"], "api_url": github.url, "git_url": f"file://{bare}",
                                   "checkout": str(root), "bot_login": BOT, "revision_delay_seconds": 0}},
        "packs": {"demo": {"path": str(ROOT / "tests" / "fixtures" / "packs" / "demo")}},
        "code_repos": {CODE: {
            "doc_collection": DOCS, "workspace": "ws", "checkout": str(code[0]), "pack": "demo",
            "audience": "workspace members", "api_url": github.url, "spec_paths": ["specs/**/spec.md"],
            "areas": [{"path": "", "products": ["boards"]},
                      {"path": "src/alerts/", "products": ["alerts"], "feature": "Quiet Hours", "owner": "writer-1",
                       "spec": "specs/quiet-hours/spec.md"}]}},
        "policies": {"default": {"publishing": {"auto_create_pr": auto, "source_pr_feedback": True}}},
    }
    if backend:
        data["backend"] = {}
    if jira:
        data["context_sources"] = {"pulse": {"source_type": "jira", "base_url": "https://example.atlassian.net",
                                             "project_keys": ["PULSE"]}}
    return DocForgeConfig.model_validate(data)


def info(code, number=11, *, head=None, base=None, branch="feature/quiet-hours", title="Add Quiet Hours", **extra):
    _, b, h, _ = code
    return {"repo": CODE, "number": number, "title": title, "body": "Members can pause alerts.", "branch": branch,
            "base_sha": base or b, "head_sha": head or h, "reasons": ["spec.md changed"], "features": ["Quiet Hours"],
            "products": ["alerts"], "owners": ["writer-1"], **extra}


def ws(tmp_path) -> Path:
    return tmp_path / "ws"


def planned_feature(tmp_path, cfg, code):
    config_path = tmp_path / "docforge.yaml"
    assert start_or_add(cfg, config_path, info(code))["result"] == "started"
    waiting = process_feature(cfg, config_path, CODE, "quiet-hours")
    assert waiting["result"] == "waiting", waiting
    run = ws(tmp_path) / "features" / "quiet-hours" / "run"
    for rel in ANALYSIS:
        (run / rel).write_text((DONE / rel).read_text())
    (run / "analysis" / "ia-plan.md").write_text(FIXTURE.read_text())
    return config_path, run


# --- grouping ------------------------------------------------------------------------------


def test_feature_keys():
    key = feature_key(repo=CODE, number=5, branch="pulse-77-quiet-hours", title="Quiet Hours", features=[],
                      project_keys={"PULSE"})
    assert (key.key, key.label, key.jira, key.how) == ("pulse-77", "PULSE-77", "PULSE-77", "jira")
    assert feature_key(repo=CODE, number=5, branch="x", title="Fix UTF-8 handling", features=[],
                       project_keys={"PULSE"}).how == "pull_request"
    assert feature_key(repo=CODE, number=5, branch="x", title="Fix UTF-8 handling", features=["Quiet Hours"],
                       project_keys=set()).key == "quiet-hours"  # lower or mixed case only counts at a branch start
    assert feature_key(repo=CODE, number=5, branch="pulse-77-x", title="", features=[], project_keys=set()).key == "pulse-77"
    solo = feature_key(repo=CODE, number=5, branch="x", title="Tidy", features=["A", "B"], project_keys=set())
    assert (solo.key, solo.label) == ("pulseboard-web-pr-5", f"{CODE}#5")


# --- planning ------------------------------------------------------------------------------


def test_spec_pr_becomes_a_plan_pr(tmp_path, code, docs, github):  # noqa: F811
    cfg = make_config(tmp_path, code, docs, github)
    config_path, run = planned_feature(tmp_path, cfg, code)
    manifest = json.loads((run / "run.json").read_text())
    kinds = {s["id"]: s["kind"] for s in manifest["sources"]}
    assert kinds == {"S1": "github_pr", "S2": "spec"}  # file names match the IDs run start gives
    spec = (run.parent / "sources" / "S2.md").read_text()
    assert "Members can pause in-app alerts for 1 hour." in spec and f"id: {CODE}:specs/quiet-hours/spec.md" in spec
    assert manifest["code"] == {"repo": CODE, "base": code[1], "head": code[2]}
    assert manifest["feature_run"] == {"key": "quiet-hours", "repo": CODE}
    assert manifest["ia_plan"] == {"feature": "Quiet Hours", "product": "alerts", "owner": "writer-1",
                                   "source_prs": [f"{CODE}#11"], "engineering_spec": f"{CODE}:specs/quiet-hours/spec.md",
                                   "jira": "none", "docforge_run": "quiet-hours"}
    existing = json.loads((run / "analysis" / "existing-docs.json").read_text())
    assert existing["docs_path"] == "<docs checkout>"  # outside the workspace: never a local absolute path
    assert str(tmp_path) not in (run / "analysis" / "existing-docs.json").read_text()

    result = process_feature(cfg, config_path, CODE, "quiet-hours")
    assert result["result"] == "planned" and github.pulls[1]["head"]["ref"] == "docforge/plan-quiet-hours"
    state = load_feature(ws(tmp_path) / "state", "quiet-hours")
    assert state.phase == "planned" and state.plan_pr == github.pulls[1]["html_url"]
    status = [s for s in github.statuses if s["repo"] == CODE][-1]
    assert status["state"] == "success"
    assert any(f"Docs plan: {state.plan_pr}" in c["body"] for c in github.comments if c["issue"] == 11)


def test_a_second_pr_revises_the_plan_before_approval(tmp_path, code, docs, github):  # noqa: F811
    cfg = make_config(tmp_path, code, docs, github)
    config_path, run = planned_feature(tmp_path, cfg, code)
    process_feature(cfg, config_path, CODE, "quiet-hours")
    joined = start_or_add(cfg, config_path, info(code, 12, base=code[2], head=code[3], title="Resume now"))
    assert joined == {"result": "joined", "feature": "quiet-hours", "phase": "planned",
                      "plan_pr": github.pulls[1]["html_url"]}
    assert process_feature(cfg, config_path, CODE, "quiet-hours")["result"] == "nothing pending"
    ids = [s["id"] for s in json.loads((run / "run.json").read_text())["sources"]]
    assert ids == ["S1", "S2", "P1"]  # the unchanged spec is not added again
    record = load_plan(run, "plan-pr")
    assert record.status == "changes_requested"
    assert "Code change example-org/pulseboard-web#12 (Resume now) added as source(s) P1." in record.requests[-1]["body"]
    assert "Sources added after the run started" in (run / "prompts" / "1-analyzer.md").read_text()
    assert start_or_add(cfg, config_path, info(code, 12, base=code[2], head=code[3]))["result"] == "already recorded"


def test_approval_drafts_and_merges_make_them_ready(tmp_path, code, docs, github):  # noqa: F811
    cfg = make_config(tmp_path, code, docs, github, backend=True)
    session = make_config(tmp_path, code, docs, github)
    config_path, run = planned_feature(tmp_path, session, code)
    process_feature(session, config_path, CODE, "quiet-hours")
    plan_record = load_plan(run, "plan-pr")
    handle_plan_event(parse_docs_event(*approve(plan_record.commit)), run=run, config=cfg)
    queued = []
    process_plan_pr(run, config=cfg, checkout=docs[0], on_approved=queued.append)
    assert queued == [run]
    assert queue_draft_after_approval(cfg, config_path, run) == (CODE, "quiet-hours")
    waiting = process_feature(cfg, config_path, CODE, "quiet-hours")
    assert waiting["result"] == "waiting" and "Research stage" in waiting["reason"]
    (run / "analysis" / "claims.json").write_text("{}\n")  # the session's research (placeholder)
    (run / "analysis" / "CROSS-SOURCE.md").write_text("# Cross-source check\n\n" + "Placeholder research output for "
                                                      "the test; the session compares claims with the code. " * 2)
    client = FakeClient(drafts(), stage_answer("proofreader"))
    result = process_feature(cfg, config_path, CODE, "quiet-hours", backend_client=client)
    assert result["result"] == "drafted", result
    drafts_pr = github.pulls[2]
    assert drafts_pr["head"]["ref"] == "docforge/quiet-hours" and drafts_pr["draft"]
    assert "Drafted from the plan approved in" in drafts_pr["body"]

    start_or_add(cfg, config_path, info(code, 12, base=code[2], head=code[3], title="Resume now"))
    process_feature(cfg, config_path, CODE, "quiet-hours")
    late = [c["body"] for c in github.comments if "already approved" in c["body"]]
    assert len(late) == 2  # on the plan PR and on the drafts PR; no revision is requested
    assert load_plan(run, "plan-pr").status == "drafting"

    assert on_merged(cfg, config_path, CODE, 11)[0]["open"] == [f"{CODE}#12"]
    assert github.pulls[2]["draft"]  # one pull request of the feature is still open
    [done] = on_merged(cfg, config_path, CODE, 12)
    assert done["result"] == "ready" and not github.pulls[2]["draft"]


# --- confirm, skip, routing ------------------------------------------------------------------


def decision(outcome):
    from types import SimpleNamespace

    return SimpleNamespace(outcome=outcome, category="unsure", reasons=["product code changed"],
                           triage={"features": ["Quiet Hours"], "products": ["alerts"], "owners": ["writer-1"]})


def event(code, number=11):
    from types import SimpleNamespace

    _, base, head, _ = code
    return SimpleNamespace(repo=CODE, number=number, title="Add Quiet Hours", body="", head_branch="quiet-hours",
                           base_sha=base, head_sha=head)


def comment(body, number=11, association="MEMBER"):
    return parse_docs_event("issue_comment", {
        "action": "created", "repository": {"full_name": CODE},
        "issue": {"number": number, "pull_request": {"url": "x"}},
        "comment": {"id": 9, "body": body, "user": {"login": "lead-1", "type": "User"},
                    "author_association": association}})


def test_confirm_then_plan_or_skip(tmp_path, code, docs, github):  # noqa: F811
    cfg = make_config(tmp_path, code, docs, github)
    config_path = tmp_path / "docforge.yaml"
    assert on_decision(cfg, config_path, event(code), decision("confirm"))["result"] == "awaiting confirmation"
    assert list_features(cfg, config_path) == []
    assert on_comment(cfg, config_path, comment(f"@{BOT} plan", association="NONE"))["result"] == "ignore"
    assert on_comment(cfg, config_path, comment("plan this please"))["reason"] == "does not mention DocForge"
    result = on_comment(cfg, config_path, comment(f"@{BOT} plan"))
    assert result["result"] == "started" and result["confirmed_by"] == "lead-1"
    assert "Confirmed by @lead-1" in github.comments[-1]["body"]
    assert on_comment(cfg, config_path, comment(f"@{BOT} plan"))["reason"].startswith("this pull request is not waiting")

    on_decision(cfg, config_path, event(code, 13), decision("confirm"))
    skipped = on_comment(cfg, config_path, comment(f"@{BOT} skip internal refactor only", number=13))
    assert skipped == {"result": "skipped", "by": "lead-1", "reason": "internal refactor only"}
    record = json.loads((ws(tmp_path) / "state" / "skipped" / "example-org-pulseboard-web-13.json").read_text())
    assert record["skipped_by"] == "lead-1" and record["reason"] == "internal refactor only"
    assert github.statuses[-1]["description"].startswith("No docs needed: Skipped by @lead-1")
    assert [s.key for _, s in list_features(cfg, config_path)] == ["quiet-hours"]


def test_receiver_routes_code_prs(tmp_path, code, docs, github):  # noqa: F811
    from docforge.webhook import FeatureEndpoint, Receiver, sign

    cfg = make_config(tmp_path, code, docs, github, jira=True)
    features = FeatureEndpoint(config=cfg, config_path=tmp_path / "docforge.yaml", run_work=False)
    secret = b"fictional-webhook-secret"
    receiver = Receiver(config=cfg, secret=secret, log=tmp_path / "decisions.jsonl", checkouts={CODE.casefold(): code[0]},
                        config_path=tmp_path / "docforge.yaml", features=features)
    payload = json.loads((ROOT / "tests" / "fixtures" / "github" / "pr_opened.json").read_text())
    payload["repository"]["full_name"] = CODE
    payload["pull_request"].update(number=21, title="PULSE-77 Quiet Hours spec",
                                   head={"ref": "pulse-77-spec", "sha": code[2]}, base={"ref": "main", "sha": code[1]})
    body = json.dumps(payload).encode()
    status, data = receiver.handle({"X-Hub-Signature-256": sign(secret, body), "X-GitHub-Event": "pull_request"}, body)
    assert status == 200 and data["docs_needed"] == "needs_research"
    state = load_feature(ws(tmp_path) / "state", "pulse-77")
    assert state.label == "PULSE-77" and state.jira == "PULSE-77" and state.prs[0].number == 21
    assert features.wake.is_set()

    note = json.dumps({"action": "created", "repository": {"full_name": CODE},
                       "issue": {"number": 21, "pull_request": {"url": "x"}},
                       "comment": {"id": 1, "body": f"@{BOT} plan", "user": {"login": "lead-1", "type": "User"},
                                   "author_association": "MEMBER"}}).encode()
    status, data = receiver.handle({"X-Hub-Signature-256": sign(secret, note), "X-GitHub-Event": "issue_comment"}, note)
    assert status == 202 and data["result"] == "ignore"  # #21 acted at once: nothing waits for confirmation


def test_approval_during_a_revision_wins_and_late_drafts_are_ready(tmp_path, code, docs, github):  # noqa: F811
    """A code change asked for a plan revision, then the writer approved the plan before the Analyzer ran
    again: the approved plan wins and the set-aside analysis comes back. Drafts proposed after every pull
    request merged are marked ready at once."""
    session = make_config(tmp_path, code, docs, github)
    cfg = make_config(tmp_path, code, docs, github, backend=True)
    config_path, run = planned_feature(tmp_path, session, code)
    process_feature(session, config_path, CODE, "quiet-hours")
    start_or_add(session, config_path, info(code, 12, base=code[2], head=code[3], title="Resume now"))
    process_feature(session, config_path, CODE, "quiet-hours")
    assert process_plan_pr(run, config=session, checkout=docs[0], now=LATER)["result"] == "waiting"
    assert not (run / "analysis" / "HANDOVER.md").exists()  # set aside for the revision
    plan_record = load_plan(run, "plan-pr")
    handle_plan_event(parse_docs_event(*approve(plan_record.commit)), run=run, config=session)
    assert process_plan_pr(run, config=session, checkout=docs[0])["result"] == "approved"
    assert (run / "analysis" / "HANDOVER.md").is_file()
    assert any(h["event"] == "revision_cancelled_by_approval" for h in load_plan(run, "plan-pr").history)

    on_merged(session, config_path, CODE, 11)
    [entry] = on_merged(session, config_path, CODE, 12)
    assert entry["result"].startswith("drafts not proposed yet")
    queue_draft_after_approval(session, config_path, run)
    (run / "analysis" / "claims.json").write_text("{}\n")
    (run / "analysis" / "CROSS-SOURCE.md").write_text("# Cross-source check\n\n" + "Placeholder research output. " * 5)
    result = process_feature(cfg, config_path, CODE, "quiet-hours",
                             backend_client=FakeClient(drafts(), stage_answer("proofreader")))
    assert result["result"] == "drafted" and result["ready"] == "ready" and not github.pulls[2]["draft"]
