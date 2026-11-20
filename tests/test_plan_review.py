"""Review on the plan pull request (B7c-2): approval drafts from the approved file, comments revise the plan,
hand edits are left alone, and the drafts PR links back to the plan.

Stub Jira, fake model client, fake GitHub API and a local bare repository. No network, no key, no cost.
"""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys

import pytest

pytest.importorskip("pdfplumber")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conftest import git  # noqa: E402
from github_stub import FakeGithub  # noqa: E402,F401
from test_backend import DONE, FakeClient, answer, stage_answer  # noqa: E402
from test_gate import MARKED  # noqa: E402
from test_ia_plan import FIXTURE, _session_plan, docs, github, plan_config, run_ticket  # noqa: E402,F401
from test_jira_work import ANALYSIS, KEY, _queue, jira  # noqa: E402,F401

from docforge.github.events import parse_docs_event  # noqa: E402
from docforge.jira import load_state  # noqa: E402
from docforge.jira.work import queue_draft_after_approval  # noqa: E402
from docforge.plan.review import handle_plan_event, process_plan_pr  # noqa: E402
from docforge.publish import load_plan  # noqa: E402

REPO = "example-org/docs-site"
BOT = "docforge-bot"
LATER = datetime.now(timezone.utc) + timedelta(days=1)
PLAN_FILE = "plans/quiet-hours/ia-plan.md"
BRANCH = "docforge/plan-quiet-hours"


def planned(jira, tmp_path, github, docs, plan_text=None, **extra):
    """A Jira ticket whose plan PR is open on the fake GitHub."""
    from docforge.config import DocForgeConfig

    def build(**more):
        data = plan_config(jira, github, docs, **more).model_dump(by_alias=True, exclude_none=True)
        data["doc_collections"][REPO].update({"bot_login": BOT, "revision_delay_seconds": 0})
        return DocForgeConfig.model_validate(data)

    stub, _ = jira
    stub.json(f"/rest/api/3/issue/{KEY}?fields=attachment",  # the PRD only: the drafts need no flow-backed steps
              {"fields": {"attachment": [{"id": "1", "filename": "Quiet Hours PRD.pdf", "size": 100}]}})
    session = build()  # planned by a session first, so no test reaches a real API client
    _queue(tmp_path / "state", "plan")
    run_ticket(session, tmp_path)
    run = jira[1] / "tickets" / KEY / "run"
    _session_plan(run, plan_text or FIXTURE.read_text())
    assert run_ticket(session, tmp_path)["result"] == "planned"
    return build(**extra), run


def deliver(run, cfg, name, payload):
    return handle_plan_event(parse_docs_event(name, payload), run=run, config=cfg)


def approve(commit, login="writer-1", association="MEMBER"):
    return "pull_request_review", {"action": "submitted", "repository": {"full_name": REPO},
                                   "pull_request": {"number": 1, "head": {"ref": BRANCH}},
                                   "review": {"id": 901, "state": "approved", "body": "", "commit_id": commit,
                                              "user": {"login": login, "type": "User"},
                                              "author_association": association}}


def comment(body):
    return "issue_comment", {"action": "created", "repository": {"full_name": REPO},
                             "issue": {"number": 1, "pull_request": {"url": "x"}},
                             "comment": {"id": 502, "body": body, "user": {"login": "writer-1", "type": "User"},
                                         "author_association": "MEMBER", "created_at": "2026-11-19T10:00:00Z"}}


def writer_push(tmp_path, bare, change) -> str:
    """A writer edits the plan file on the plan branch and pushes."""
    clone = tmp_path / f"writer-{len(list(tmp_path.glob('writer-*')))}"
    subprocess.run(["git", "clone", "-q", "-b", BRANCH, str(bare), str(clone)], check=True)
    path = clone / PLAN_FILE
    path.write_text(change(path.read_text()))
    git(clone, "-c", "user.name=W", "-c", "user.email=w@example.com", "commit", "-q", "-am", "writer edit")
    git(clone, "push", "-q", "origin", BRANCH)
    return git(clone, "rev-parse", "HEAD")


def drafts(**pages):
    files = {p: (MARKED / p).read_text() for p in ("feature/feature-guide.md", "how-to/how-to.md")}
    # The coverage ledger of a run that drafts only the feature guide and the how-to.
    files["analysis/COVERAGE.md"] = (DONE / "analysis" / "COVERAGE.md").read_text().replace(
        "; release-note/release-note.md", "")
    return answer({**files, **pages})


# --- approval ---------------------------------------------------------------------------


def test_approval_drafts_from_the_approved_plan(jira, tmp_path, github, docs):
    cfg, run = planned(jira, tmp_path, github, docs, backend={})
    record = load_plan(run, "plan-pr")
    edited = writer_push(tmp_path, docs[1], lambda t: t.replace(
        "site/alerts/notifications/pause-for-1-hour.md", "site/alerts/notifications/pause-alerts.md"))
    assert deliver(run, cfg, *approve(edited))["action"] == "approved"

    queued = []
    result = process_plan_pr(run, config=cfg, checkout=docs[0], on_approved=queued.append)
    assert result["result"] == "approved" and queued == [run]
    kept = (run / "analysis" / "ia-plan.approved.md").read_text()
    assert kept.replace("\nstatus: approved", "") == git(docs[1], "show", f"{edited}:{PLAN_FILE}") + "\n"
    assert "\nstatus: approved\n---" in kept  # the approved copy records the approval
    manifest = json.loads((run / "run.json").read_text())
    assert manifest["deliverables"] == ["feature/feature-guide.md", "how-to/how-to.md"]
    assert manifest["approved_plan"]["commit"] == edited and manifest["approved_plan"]["needs_own_run"] == []
    assert {p["src"]: p["dest"] for p in manifest["approved_plan"]["placements"]}["how-to/how-to.md"] == \
        "site/alerts/notifications/pause-alerts.md"  # the writer's edit counts
    order = (run / "prompts" / "2-drafter.md").read_text()
    assert "## Approved plan" in order and "`how-to/how-to.md` -> `site/alerts/notifications/pause-alerts.md`" in order
    assert "release-note/release-note.md" not in order.split("## Write")[1]
    assert "Plan approved at" in github.comments[-1]["body"]
    assert load_plan(run, "plan-pr").status == "drafting" and record.commit != edited

    assert queue_draft_after_approval(tmp_path / "state", KEY)
    client = FakeClient(drafts(), stage_answer("proofreader"))
    drafted = run_ticket(cfg, tmp_path, client)
    assert drafted["result"] == "drafted", drafted
    draft_pr = github.pulls[2]
    assert draft_pr["head"]["ref"] == "docforge/pulse-77" and draft_pr["draft"]
    assert "Drafted from the plan approved in" in draft_pr["body"] and edited[:12] in draft_pr["body"]
    assert "site/alerts/notifications/pause-alerts.md" in git(docs[1], "ls-tree", "-r", "--name-only",
                                                              "docforge/pulse-77")
    assert f"The drafts for this plan are in {draft_pr['html_url']}" in github.comments[-1]["body"]
    assert 'path="analysis/ia-plan.approved.md"' in client.requests[0]["messages"][0]["content"]


def test_an_invalid_approved_plan_does_not_draft(jira, tmp_path, github, docs):
    cfg, run = planned(jira, tmp_path, github, docs)
    broken = writer_push(tmp_path, docs[1], lambda t: t.replace("| overview |", "| tutorial |"))
    deliver(run, cfg, *approve(broken))
    queued = []
    result = process_plan_pr(run, config=cfg, checkout=docs[0], on_approved=queued.append)
    assert result["result"] == "failed" and not queued
    assert load_plan(run, "plan-pr").status == "approval_invalid"
    assert "type 'tutorial' is not one of" in github.comments[-1]["body"]
    assert "approved_plan" not in json.loads((run / "run.json").read_text())


def test_merge_without_review_counts_as_approval(jira, tmp_path, github, docs):
    cfg, run = planned(jira, tmp_path, github, docs)
    head = load_plan(run, "plan-pr").commit
    merged = {"action": "closed", "repository": {"full_name": REPO},
              "pull_request": {"number": 1, "merged": True, "head": {"ref": BRANCH, "sha": head}}}
    assert deliver(run, cfg, "pull_request", merged)["action"] == "approved"
    assert process_plan_pr(run, config=cfg, checkout=docs[0])["result"] == "approved"


def test_only_reviewers_approve_and_drafting_needs_approval(jira, tmp_path, github, docs):
    cfg, run = planned(jira, tmp_path, github, docs)
    result = deliver(run, cfg, *approve(load_plan(run, "plan-pr").commit, association="CONTRIBUTOR"))
    assert result["action"] == "ignore" and "not a reviewer" in result["reason"]
    state = load_state(tmp_path / "state", KEY)
    from docforge.jira.state import Pending, save_state

    state.phase, state.pending = "drafting", Pending(action="draft", at="t")
    save_state(tmp_path / "state", state)
    failed = run_ticket(cfg, tmp_path)
    assert failed["result"] == "failed" and "not approved yet" in failed["reason"]
    assert load_state(tmp_path / "state", KEY).phase == "planned"


def test_articles_a_run_cannot_draft_are_named(jira, tmp_path, github, docs):
    extra_rows = ("| Pause from the mobile app | procedural | site/alerts/notifications/pause-mobile.md | Mobile | C03 |\n"
                  "| Quiet Hours FAQ | faq | site/alerts/notifications/faq.md | Questions | C02 |\n")
    plan_text = FIXTURE.read_text().replace(
        "| Pause your in-app alerts for 1 hour |", extra_rows + "| Pause your in-app alerts for 1 hour |", 1)
    plan_text = plan_text.replace("## Existing articles - impact\n\nNone.", (
        "## Existing articles - impact\n\n| Article | Docs path | Change | Why | Claims |\n| --- | --- | --- | --- | --- |\n"
        "| Alerts overview | site/alerts/index.md | update | Mention Quiet Hours | C01 |"))
    cfg, run = planned(jira, tmp_path, github, docs, plan_text=plan_text)
    deliver(run, cfg, *approve(load_plan(run, "plan-pr").commit))
    result = process_plan_pr(run, config=cfg, checkout=docs[0])
    assert [p["dest"] for p in result["placements"]] == ["site/alerts/notifications/quiet-hours.md",
                                                         "site/alerts/notifications/pause-mobile.md"]
    assert result["needs_own_run"] == ["Quiet Hours FAQ (faq)", "Pause your in-app alerts for 1 hour (procedural)",
                                       "Alerts overview (update of an existing article; not found on the docs "
                                       "repository's base branch)"]
    assert "need their own run" in github.comments[-1]["body"]


# --- revisions --------------------------------------------------------------------------


def test_comment_revises_the_plan(jira, tmp_path, github, docs):
    cfg, run = planned(jira, tmp_path, github, docs, backend={})
    assert deliver(run, cfg, *comment(f"@{BOT} Add a FAQ article."))["action"] == "changes_requested"
    revised_plan = FIXTURE.read_text().replace(
        "| Pause your in-app alerts for 1 hour |",
        "| Quiet Hours FAQ | faq | site/alerts/notifications/faq.md | Common questions | C02 |\n"
        "| Pause your in-app alerts for 1 hour |", 1)
    files = {p: (DONE / p).read_text() for p in ANALYSIS}
    client = FakeClient(answer({**files, "analysis/ia-plan.md": revised_plan}))
    result = process_plan_pr(run, config=cfg, checkout=docs[0], backend_client=client, now=LATER)
    assert result == {**result, "result": "revised", "pushed": True, "revision": 1}
    assert "Quiet Hours FAQ" in git(docs[1], "show", f"{BRANCH}:{PLAN_FILE}")
    assert "## Revision 1 feedback" in (run / "prompts" / "1-analyzer.md").read_text()
    assert "writer-1: Add a FAQ article." in (run / "prompts" / "1-analyzer.md").read_text()
    assert (run / "analysis" / "revisions" / "r0" / "ia-plan.md").is_file()
    assert "Plan revision 1" in github.comments[-1]["body"] and "Quiet Hours FAQ" in github.pulls[1]["body"]
    record = load_plan(run, "plan-pr")
    assert record.status == "revised" and all(r["used"] for r in record.requests)
    # Approval after a revision drafts from the revised file.
    deliver(run, cfg, *approve(record.commit))
    assert process_plan_pr(run, config=cfg, checkout=docs[0])["result"] == "approved"


def test_hand_edits_are_never_overwritten(jira, tmp_path, github, docs):
    cfg, run = planned(jira, tmp_path, github, docs, backend={})
    edited = writer_push(tmp_path, docs[1], lambda t: t.replace("owner: unknown", "owner: writer-1"))
    deliver(run, cfg, *comment(f"@{BOT} Add a FAQ article."))
    result = process_plan_pr(run, config=cfg, checkout=docs[0], backend_client=FakeClient(), now=LATER)
    assert result["result"] == "hand_edited"
    assert git(docs[1], "rev-parse", BRANCH) == edited
    assert "will not rewrite the file" in github.comments[-1]["body"]
    deliver(run, cfg, *approve(edited))  # approval still works, from the writer's version
    assert process_plan_pr(run, config=cfg, checkout=docs[0])["result"] == "approved"


def test_session_revision_and_failed_revision(jira, tmp_path, github, docs):
    cfg, run = planned(jira, tmp_path, github, docs)
    deliver(run, cfg, *comment(f"@{BOT} Add a FAQ article."))
    waiting = process_plan_pr(run, config=cfg, checkout=docs[0], now=LATER)
    assert waiting["result"] == "waiting" and waiting["work_order"] == "prompts/1-analyzer.md"
    before = (run / "analysis" / "revisions" / "r0" / "ia-plan.md").read_text()
    _session_plan(run, FIXTURE.read_text().replace("mode: Net-New", "mode: Someday"))  # the session's broken plan
    failed = process_plan_pr(run, config=cfg, checkout=docs[0], now=LATER)
    assert failed["result"] == "failed" and "mode must be" in failed["reason"]
    assert (run / "analysis" / "ia-plan.md").read_text() == before  # the previous plan is back
    assert load_plan(run, "plan-pr").status == "revision_failed"
    deliver(run, cfg, *comment(f"@{BOT} Add a FAQ article, please."))
    process_plan_pr(run, config=cfg, checkout=docs[0], now=LATER)
    _session_plan(run, FIXTURE.read_text().replace("owner: unknown", "owner: docs-team"))
    assert process_plan_pr(run, config=cfg, checkout=docs[0], now=LATER)["result"] == "revised"
    assert "owner: docs-team" in git(docs[1], "show", f"{BRANCH}:{PLAN_FILE}")


def test_answers_on_the_plan_pr_and_jira_queue(jira, tmp_path, github, docs):
    cfg, run = planned(jira, tmp_path, github, docs)
    result = deliver(run, cfg, *comment(f"@{BOT}\nQ01: Midnight in the workspace time zone."))
    assert result["answers"] == "A1" and result["action"] == "changes_requested"
    assert any(s["id"] == "A1" for s in json.loads((run / "run.json").read_text())["sources"])
    assert not queue_draft_after_approval(tmp_path / "state", "PULSE-1")  # unknown ticket
    assert queue_draft_after_approval(tmp_path / "state", KEY)
    assert not queue_draft_after_approval(tmp_path / "state", KEY)  # already drafting


def test_webhook_routes_plan_pr_events(jira, tmp_path, github, docs, monkeypatch):
    from docforge.webhook import DocsPrEndpoint, JiraEndpoint, Receiver, sign

    cfg, run = planned(jira, tmp_path, github, docs)
    monkeypatch.setattr("docforge.jira.work.process", lambda key, **kw: None)
    monkeypatch.setenv("TEST_JIRA_SECRET", "s")
    jira_endpoint = JiraEndpoint(config=cfg, config_path=tmp_path / "docforge.yaml", trigger="docs-tickets",
                                 state_root=tmp_path / "state", run_work=False)
    endpoint = DocsPrEndpoint(config=cfg, config_path=tmp_path / "docforge.yaml", roots=[jira[1]], run_work=False,
                              jira=jira_endpoint)
    secret = b"fictional-webhook-secret"
    receiver = Receiver(config=cfg, secret=secret, log=tmp_path / "decisions.jsonl", docs=endpoint)
    name, payload = approve(load_plan(run, "plan-pr").commit)
    body = json.dumps(payload).encode()
    status, data = receiver.handle({"X-Hub-Signature-256": sign(secret, body), "X-GitHub-Event": name,
                                    "X-GitHub-Delivery": "p1"}, body)
    assert status == 202 and data["action"] == "approved" and data["kind"] == "plan-pr"
    endpoint.approved(run)
    assert jira_endpoint.queue.get_nowait() == KEY
    assert load_state(tmp_path / "state", KEY).phase == "drafting"


def test_checker_requires_only_the_approved_drafts(tmp_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location("check_outputs", Path(__file__).resolve().parents[1] / "scripts"
                                                  / "check_outputs.py")
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    assert checker.required_files(tmp_path) == checker.REQUIRED  # no run.json
    manifest = {"deliverables": ["feature/feature-guide.md", "how-to/how-to.md"]}
    (tmp_path / "run.json").write_text(json.dumps(manifest))
    assert "release-note/release-note.md" in checker.required_files(tmp_path)  # no approved plan: all three
    (tmp_path / "run.json").write_text(json.dumps({**manifest, "approved_plan": {"commit": "x"}}))
    required = checker.required_files(tmp_path)
    assert "release-note/release-note.md" not in required and "how-to/how-to.md" in required
    (tmp_path / "run.json").write_text(json.dumps({"deliverables": ["other.md"], "approved_plan": {}}))
    assert checker.required_files(tmp_path) == checker.REQUIRED


def _synchronize(commit, sender="writer-1"):
    return "pull_request", {"action": "synchronize", "repository": {"full_name": REPO}, "sender": {"login": sender},
                            "pull_request": {"number": 1, "head": {"ref": BRANCH, "sha": commit}}}


def test_status_approved_in_the_file_approves_the_plan(jira, tmp_path, github, docs):
    cfg, run = planned(jira, tmp_path, github, docs)
    own = load_plan(run, "plan-pr").pushed_commit
    assert deliver(run, cfg, *_synchronize(own))["action"] == "ignore"  # DocForge's own push
    approved = writer_push(tmp_path, docs[1], lambda t: t.replace("docforge_run: pulse-77",
                                                                  "docforge_run: pulse-77\nstatus: approved"))
    assert deliver(run, cfg, *_synchronize(approved))["action"] == "pushed"
    queued = []
    result = process_plan_pr(run, config=cfg, checkout=docs[0], on_approved=queued.append)
    assert result["result"] == "approved" and queued == [run]
    assert load_plan(run, "plan-pr").approved_commit == approved
    assert "status: approved" in (run / "analysis" / "ia-plan.approved.md").read_text()


def test_a_push_without_approval_is_a_hand_edit(jira, tmp_path, github, docs):
    cfg, run = planned(jira, tmp_path, github, docs)
    edited = writer_push(tmp_path, docs[1], lambda t: t.replace("owner: unknown", "owner: writer-1"))
    deliver(run, cfg, *_synchronize(edited))
    assert process_plan_pr(run, config=cfg, checkout=docs[0])["result"] == "hand_edited"
    assert load_plan(run, "plan-pr").status == "hand_edited"
    deliver(run, cfg, *approve(edited))  # approving the pull request still works
    assert process_plan_pr(run, config=cfg, checkout=docs[0])["result"] == "approved"
    assert "status: approved" in (run / "analysis" / "ia-plan.approved.md").read_text()
