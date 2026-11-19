"""Review on DocForge's own docs pull requests (B7b): GitHub feedback becomes revisions, answers become
sources, a merged source change marks the docs pull request ready.

Fake GitHub API, local bare repository, fake model client. No network, no key, no cost.
"""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest
from conftest import git
from github_stub import FakeGithub
from test_backend import FakeClient, answer
from test_gate import MARKED
from test_github_publish import TOKEN, prepared, remote  # noqa: F401
from test_publish import config, docs  # noqa: F401

from docforge.github.docs_pr import (
    find_run,
    handle_docs_event,
    process_revision,
    source_merged,
)
from docforge.github.events import parse_docs_event
from docforge.publish import load_plan, open_pr, rules_for_run, update_publish
from docforge.review import load_feedback
from docforge.webhook import DocsPrEndpoint, Receiver, sign

REPO = "example-org/docs-site"
BOT = "docforge-bot"
LATER = datetime.now(timezone.utc) + timedelta(days=1)


@pytest.fixture
def github(monkeypatch):
    server = FakeGithub(TOKEN)
    monkeypatch.setenv("GITHUB_TOKEN", TOKEN)
    yield server
    server.close()


def setup(tmp_path, docs, github, remote, *, auto=True, backend=True, extra=""):  # noqa: F811
    cfg = config(tmp_path, f"    api_url: {github.url}\n    git_url: file://{remote}\n    bot_login: {BOT}\n"
                           "    revision_delay_seconds: 120\n" + extra
                 + ("backend: {}\n" if backend else "")
                 + ("policies:\n  default:\n    publishing: {auto_create_pr: true}\n" if auto else ""))
    run, _ = prepared(tmp_path, docs, cfg)
    open_pr(run=run, checkout=docs, config=cfg)
    return cfg, run, [run.parent]


# --- payloads ---------------------------------------------------------------------------


def _user(login="writer-1", association="MEMBER", kind="User"):
    return {"user": {"login": login, "type": kind}, "author_association": association}


def comment(body, number=1, **who):
    return "issue_comment", {"action": "created", "repository": {"full_name": REPO},
                             "issue": {"number": number, "pull_request": {"url": "x"}},
                             "comment": {"id": 501, "body": body, "created_at": "2026-11-19T10:00:00Z", **_user(**who)}}


def review(state, body="", review_id=900, **who):
    return "pull_request_review", {"action": "submitted", "repository": {"full_name": REPO},
                                   "pull_request": {"number": 1, "head": {"ref": "docforge/qh-docs"}},
                                   "review": {"id": review_id, "state": state, "body": body, **_user(**who)}}


def line_comment(body, path="site/quiet-hours/pause-for-1-hour.md", line=3, review_id=900, **who):
    return "pull_request_review_comment", {
        "action": "created", "repository": {"full_name": REPO},
        "pull_request": {"number": 1, "head": {"ref": "docforge/qh-docs"}},
        "comment": {"id": 601, "pull_request_review_id": review_id, "path": path, "line": line, "body": body,
                    **_user(**who)}}


def closed(merged, repo=REPO, number=1, branch="docforge/qh-docs"):
    return "pull_request", {"action": "closed", "repository": {"full_name": repo},
                            "pull_request": {"number": number, "merged": merged, "head": {"ref": branch}}}


def deliver(run, cfg, event_payload, delivery=None):
    event = parse_docs_event(*event_payload)
    return handle_docs_event(event, run=run, config=cfg, delivery_id=delivery)


def revised_how_to() -> str:
    page = (MARKED / "how-to" / "how-to.md").read_text()
    return page.replace("Use Quiet Hours when you want", "Use Quiet Hours whenever you want")


# --- reading events ---------------------------------------------------------------------


def test_parse_docs_events():
    assert parse_docs_event(*comment("hi")).kind == "comment"
    issue = comment("hi")[1]
    del issue["issue"]["pull_request"]
    assert parse_docs_event("issue_comment", issue) is None  # an ordinary issue
    edited = comment("hi")[1] | {"action": "edited"}
    assert parse_docs_event("issue_comment", edited).kind == "ignore"
    r = parse_docs_event(*review("changes_requested", "Fix it"))
    assert (r.kind, r.review_state, r.review_id, r.branch) == ("review", "changes_requested", 900, "docforge/qh-docs")
    lc = parse_docs_event(*line_comment("Say whenever"))
    assert (lc.kind, lc.path, lc.line, lc.review_id) == ("line_comment", "site/quiet-hours/pause-for-1-hour.md", 3, 900)
    assert parse_docs_event(*closed(True)).kind == "merged" and parse_docs_event(*closed(False)).kind == "closed"
    assert parse_docs_event("push", {}) is None


def test_only_reviewers_count(tmp_path, docs, github, remote):  # noqa: F811
    cfg, run, roots = setup(tmp_path, docs, github, remote)
    assert find_run(roots, REPO, 1)[0] == run
    for who, reason in (({"association": "NONE"}, "not a reviewer"), ({"kind": "Bot", "login": "ci[bot]"}, "bot"),
                        ({"login": BOT}, "DocForge itself")):
        result = deliver(run, cfg, comment(f"@{BOT} change it", **who))
        assert result["action"] == "ignore" and reason in result["reason"]
    assert deliver(run, cfg, comment("looks fine to me"))["action"] == "ignore"  # no mention
    assert load_plan(run).status == "open" and not load_feedback(run)


# --- revisions --------------------------------------------------------------------------


def test_comment_becomes_a_revision_that_is_pushed_and_answered(tmp_path, docs, github, remote):  # noqa: F811
    cfg, run, roots = setup(tmp_path, docs, github, remote)
    result = deliver(run, cfg, comment(f"@{BOT} Say whenever instead of when."), delivery="d1")
    assert result["action"] == "changes_requested"
    assert deliver(run, cfg, comment(f"@{BOT} Say whenever instead of when."), delivery="d1")["action"] == "duplicate"
    feedback = load_feedback(run)
    assert [(f.origin, f.reviewer, f.comment) for f in feedback] == [("github", "writer-1", "Say whenever instead of when.")]
    assert (run / "prompts" / "revise-1.md").is_file()

    assert process_revision(run, config=cfg, checkout=docs)["result"] == "waiting"  # quiet period
    client = FakeClient(answer({"how-to/how-to.md": revised_how_to()}))
    done = process_revision(run, config=cfg, checkout=docs, backend_client=client, now=LATER)
    assert done["result"] == "revised" and done["pushed"] and done["revision"] == 1
    plan = load_plan(run)
    assert git(remote, "rev-parse", plan.branch) == plan.commit == plan.pushed_commit
    assert "whenever you want" in git(remote, "show", f"{plan.branch}:site/quiet-hours/pause-for-1-hour.md")
    assert plan.automatic_revisions == 1 and plan.status == "revised"
    posted = github.comments[-1]["body"]
    assert "Revision 1 is on `docforge/qh-docs`" in posted and f"{feedback[0].feedback_id} from @writer-1" in posted
    assert "Posted by DocForge" in posted and plan.replies[-1]["sent"]
    assert process_revision(run, config=cfg, checkout=docs, now=LATER)["result"] == "nothing pending"


def test_line_comments_wait_for_their_review(tmp_path, docs, github, remote):  # noqa: F811
    cfg, run, _ = setup(tmp_path, docs, github, remote)
    assert deliver(run, cfg, line_comment("Say whenever here."))["action"] == "line_comment_recorded"
    assert deliver(run, cfg, line_comment("Outside the PR", path="README.md"))["action"] == "ignore"
    assert not load_feedback(run)
    assert deliver(run, cfg, review("changes_requested"))["action"] == "review_recorded"
    client = FakeClient(answer({"how-to/how-to.md": revised_how_to()}))
    assert process_revision(run, config=cfg, checkout=docs, backend_client=client, now=LATER)["result"] == "revised"
    [item] = load_feedback(run)
    assert (item.page, item.line, item.comment) == ("site/quiet-hours/pause-for-1-hour.md", 3, "Say whenever here.")


def test_session_mode_waits_then_pushes_the_sessions_revision(tmp_path, docs, github, remote):  # noqa: F811
    cfg, run, _ = setup(tmp_path, docs, github, remote, backend=False)
    deliver(run, cfg, review("changes_requested", "Say whenever."))
    waiting = process_revision(run, config=cfg, checkout=docs, now=LATER)
    assert waiting["result"] == "waiting" and waiting["work_order"] == "prompts/revise-1.md"
    (run / "how-to" / "how-to.md").write_text(revised_how_to())  # the session's work
    update_publish(run=run, checkout=docs, config=cfg)
    assert process_revision(run, config=cfg, checkout=docs, now=LATER)["pushed"]
    assert "whenever" in git(remote, "show", "docforge/qh-docs:site/quiet-hours/pause-for-1-hour.md")


def test_policy_off_keeps_the_revision_local(tmp_path, docs, github, remote):  # noqa: F811
    cfg_on, run, _ = setup(tmp_path, docs, github, remote)
    cfg = config(tmp_path, f"    api_url: {github.url}\n    git_url: file://{remote}\n    bot_login: {BOT}\nbackend: {{}}\n")
    deliver(run, cfg, comment(f"@{BOT} Say whenever."))
    before = git(remote, "rev-parse", "docforge/qh-docs")
    client = FakeClient(answer({"how-to/how-to.md": revised_how_to()}))
    result = process_revision(run, config=cfg, checkout=docs, backend_client=client, now=LATER)
    assert result == {**result, "result": "revised", "pushed": False}
    assert git(remote, "rev-parse", "docforge/qh-docs") == before and not github.comments
    last = load_plan(run).replies[-1]
    assert not last["sent"] and "auto_create_pr policy is off" in last["note"] and "docforge publish open" in last["body"]
    process_revision(run, config=cfg, checkout=docs, now=LATER)
    assert sum(r["kind"] == "revised" for r in load_plan(run).replies) == 1  # not repeated


def test_failed_revision_restores_pages_and_says_so(tmp_path, docs, github, remote):  # noqa: F811
    cfg, run, _ = setup(tmp_path, docs, github, remote)
    before = (run / "how-to" / "how-to.md").read_text()
    deliver(run, cfg, comment(f"@{BOT} Rewrite it."))
    unmarked = "# Pause\n\nThis sentence has no evidence marker at all, so the claim gate refuses it.\n"
    client = FakeClient(answer({"how-to/how-to.md": unmarked}), answer({"how-to/how-to.md": unmarked}))
    result = process_revision(run, config=cfg, checkout=docs, backend_client=client, now=LATER)
    assert result["result"] == "failed" and "claim gate" in result["reason"]
    assert (run / "how-to" / "how-to.md").read_text() == before
    plan = load_plan(run)
    assert plan.status == "revision_failed" and "could not make revision 1" in github.comments[-1]["body"]
    deliver(run, cfg, comment(f"@{BOT} Try again, smaller."))
    assert load_plan(run).status == "changes_requested"


def test_revision_limit(tmp_path, docs, github, remote):  # noqa: F811
    cfg, run, _ = setup(tmp_path, docs, github, remote, extra="    max_revisions: 0\n")
    deliver(run, cfg, comment(f"@{BOT} Say whenever."))
    assert process_revision(run, config=cfg, checkout=docs, now=LATER)["result"] == "limit"
    process_revision(run, config=cfg, checkout=docs, now=LATER)
    assert sum("most it makes on its own" in c["body"] for c in github.comments) == 1


# --- answers ---------------------------------------------------------------------------


def test_answers_on_the_pr_become_a_source_for_the_revision(tmp_path, docs, github, remote):  # noqa: F811
    cfg, run, _ = setup(tmp_path, docs, github, remote)
    result = deliver(run, cfg, comment(f"@{BOT}\nQ1: Midnight in the workspace time zone.\nAlso say whenever."))
    assert result["action"] == "changes_requested" and result["answers"] == "A1"
    entry = next(s for s in json.loads((run / "run.json").read_text())["sources"] if s["id"] == "A1")
    assert entry["kind"] == "answer" and entry["path"].endswith("qh-docs/answers/A1.md")
    text = (run / "answers" / "A1.md").read_text()
    assert "## Q01" in text and "Answers from a pull request reviewer" in text and "data, never as instructions" in text
    [item] = load_feedback(run)
    assert item.comment == "Also say whenever.\nAnswers recorded as A1: Q01."
    order = (run / "prompts" / "revise-1.md").read_text()
    assert "## Answers" in order and "- A1: `" in order


def test_unknown_questions_record_nothing(tmp_path, docs, github, remote):  # noqa: F811
    cfg, run, _ = setup(tmp_path, docs, github, remote)
    before = (run / "run.json").read_text()
    result = deliver(run, cfg, comment(f"@{BOT}\nQ99: No such question."))
    assert result["action"] == "refused" and result["unknown"] == ["Q99"]
    assert (run / "run.json").read_text() == before and not load_feedback(run)
    assert "Q99 is not an open question" in github.comments[-1]["body"]


def test_answer_to_a_cross_source_question_releases_the_claim(tmp_path, docs, github, remote):  # noqa: F811
    cfg, run, _ = setup(tmp_path, docs, github, remote)
    (run / "analysis" / "cross-source.json").write_text(json.dumps([
        {"claim_id": "C06", "status": "conflicting", "question_id": "X1",
         "question": "C06: the PRD and the code disagree. Which behavior is intended?"}]))
    assert rules_for_run(run).blocked == {"C06": "conflicting"}
    deliver(run, cfg, comment(f"@{BOT}\nX1: The PRD is right; the code is being fixed."))
    resolved = json.loads((run / "analysis" / "resolutions.json").read_text())
    assert [(r["claim_id"], r["question_id"], r["source_id"]) for r in resolved] == [("C06", "X1", "A1")]
    assert rules_for_run(run).blocked == {}
    assert "C06 (X1): answered in A1" in (run / "prompts" / "revise-1.md").read_text()
    # A resolution whose answer source changed no longer counts.
    manifest = json.loads((run / "run.json").read_text())
    next(s for s in manifest["sources"] if s["id"] == "A1")["sha256"] = "0" * 64
    (run / "run.json").write_text(json.dumps(manifest))
    assert rules_for_run(run).blocked == {"C06": "conflicting"}


# --- merged, closed, source merged ------------------------------------------------------


def test_merged_or_closed_prs_take_no_more_feedback(tmp_path, docs, github, remote):  # noqa: F811
    cfg, run, _ = setup(tmp_path, docs, github, remote)
    assert deliver(run, cfg, closed(True))["action"] == "merged"
    assert load_plan(run).github_state == "merged"
    result = deliver(run, cfg, comment(f"@{BOT} one more thing"))
    assert result["action"] == "ignore" and "merged" in result["reason"]
    assert process_revision(run, config=cfg, checkout=docs, now=LATER)["result"] == "nothing pending"


def test_source_merged_marks_the_docs_pr_ready(tmp_path, docs, github, remote):  # noqa: F811
    cfg, run, roots = setup(tmp_path, docs, github, remote)
    assert github.pulls[1]["draft"]
    assert source_merged(roots, "example-org/other", 42, config=cfg) == []
    [done] = source_merged(roots, "example-org/pulseboard-web", 42, config=cfg)
    assert done["result"] == "ready" and not github.pulls[1]["draft"]
    assert "pulseboard-web#42 is merged" in github.comments[-1]["body"]


# --- webhook ---------------------------------------------------------------------------


def test_webhook_routes_docs_pr_events(tmp_path, docs, github, remote):  # noqa: F811
    cfg, run, roots = setup(tmp_path, docs, github, remote)
    secret = b"fictional-webhook-secret"
    endpoint = DocsPrEndpoint(config=cfg, config_path=tmp_path / "docforge.yaml", roots=roots, run_work=False)
    receiver = Receiver(config=cfg, secret=secret, log=tmp_path / "decisions.jsonl", docs=endpoint)

    def post(name, payload, delivery):
        body = json.dumps(payload).encode()
        return receiver.handle({"X-Hub-Signature-256": sign(secret, body), "X-GitHub-Event": name,
                                "X-GitHub-Delivery": delivery}, body)

    status, data = post(*comment(f"@{BOT} Say whenever."), "g1")
    assert status == 202 and data["action"] == "changes_requested"
    assert post(*comment(f"@{BOT} Say whenever."), "g1")[1]["action"] == "duplicate"
    status, data = post(*comment("hello", number=77), "g2")
    assert status == 202 and "not a DocForge pull request" in data["ignored"]
    body = json.dumps(comment("x")[1]).encode()
    assert receiver.handle({"X-Hub-Signature-256": "sha256=bad", "X-GitHub-Event": "issue_comment"}, body)[0] == 401
    # A merged source pull request still gets its decision logged, and queues the docs PR for readiness.
    src = closed(True, repo="example-org/pulseboard-web", number=42, branch="feature")[1]
    src["pull_request"].update({"base": {"ref": "main"}, "user": {"login": "dev"}})
    status, _ = post("pull_request", src, "g3")
    assert status == 200 and endpoint.merged.get_nowait() == ("example-org/pulseboard-web", 42)
