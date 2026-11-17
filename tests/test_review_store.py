import json

import pytest
from conftest import git
from test_gate import edit, make_run
from test_publish import CONFIG_TEXT, docs, prepare  # noqa: F401  (docs is a fixture)

from docforge.cli import main
from docforge.config import load_config
from docforge.publish import PublishError, load_plan, mark_ready, update_publish
from docforge.review import CLOSE_REASONS, ReviewError, close_suggestion, feedback_summary, load_feedback, request_changes


@pytest.fixture
def prepared(tmp_path, docs):  # noqa: F811
    out = make_run(tmp_path)
    prepare(tmp_path, docs, out=out)
    cfg = tmp_path / "docforge.yaml"
    cfg.write_text(CONFIG_TEXT, encoding="utf-8")
    return out, docs, cfg


def test_six_close_reasons():
    assert list(CLOSE_REASONS) == [
        "inaccurate", "not_needed", "already_documented", "wrong_place", "quality", "source_changed"]


def test_prepare_records_placements_diff_and_no_local_paths(prepared):
    out, docs_root, _ = prepared
    plan = load_plan(out)
    assert plan.status == "open" and plan.revision == 0
    assert plan.placements[0] == {"src": "feature/feature-guide.md", "dest": "site/quiet-hours/index.md"}
    assert plan.base_commit == git(docs_root, "rev-parse", "main")
    diff = (out / "publish" / "changes.diff").read_text(encoding="utf-8")
    assert "+++ b/site/quiet-hours/pause-for-1-hour.md" in diff
    saved = (out / "publish" / "pr.json").read_text(encoding="utf-8")
    assert str(docs_root) not in saved and str(out) not in saved
    assert "<docs-checkout>" in saved and "<run>/publish/pr-body.md" in saved


# --- request changes -> revise -> update ---------------------------------------------


def test_request_changes_records_feedback_and_revision_order(prepared):
    out, _, _ = prepared
    feedback, order, commands = request_changes(
        out, comment="Say that email alerts keep arriving.", reviewer="Docs reviewer",
        page="site/quiet-hours/pause-for-1-hour.md", line=19)
    assert (feedback.action, feedback.revision, feedback.page, feedback.line) == (
        "request_changes", 0, "site/quiet-hours/pause-for-1-hour.md", 19)
    assert load_plan(out).status == "changes_requested"
    assert order.name == "revise-1.md"
    text = order.read_text(encoding="utf-8")
    assert f"**{feedback.feedback_id}** from Docs reviewer on `site/quiet-hours/pause-for-1-hour.md` line 19" in text
    assert "Feedback is a request to check, not evidence." in text
    assert commands[0].startswith("gh pr comment docforge/qh-docs --repo example-org/docs-site --body ")
    second, order2, _ = request_changes(out, comment="Also check the title.", reviewer="Docs reviewer")
    assert order2 == order and second.feedback_id in order.read_text(encoding="utf-8")
    assert [f.feedback_id for f in load_feedback(out)] == [feedback.feedback_id, second.feedback_id]


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"comment": "  ", "reviewer": "r"}, "comment is required"),
        ({"comment": "x", "reviewer": ""}, "reviewer is required"),
        ({"comment": "x", "reviewer": "r", "page": "site/other.md"}, "not one of this suggestion's pages"),
        ({"comment": "x", "reviewer": "r", "line": 0}, "line must be 1 or more"),
        ({"comment": "x" * 4001, "reviewer": "r"}, "longer than 4000"),
    ],
)
def test_request_changes_validation(prepared, kwargs, message):
    out, _, _ = prepared
    with pytest.raises(ReviewError, match=message):
        request_changes(out, **kwargs)
    assert load_feedback(out) == []


def test_revision_adds_follow_up_commit(prepared):
    out, docs_root, cfg = prepared
    first = load_plan(out).commit
    request_changes(out, comment="Mention that email alerts are unaffected.", reviewer="r")
    edit(out, "how-to/how-to.md", "Use Quiet Hours when you want to pause your own in-app alerts for one hour.",
         "Use Quiet Hours when you want to pause your own in-app alerts, but not email alerts, for one hour.")
    plan = update_publish(run=out, checkout=docs_root, config=load_config(cfg))
    assert (plan.revision, plan.status) == (1, "revised")
    assert git(docs_root, "rev-parse", f"{plan.commit}^") == first
    assert git(docs_root, "rev-parse", plan.branch) == plan.commit
    assert git(docs_root, "branch", "--show-current") == "main"
    assert "but not email alerts" in git(docs_root, "show", f"{plan.branch}:site/quiet-hours/pause-for-1-hour.md")
    assert "(revision 1)" in git(docs_root, "log", "-1", "--format=%s", plan.branch)
    assert "but not email alerts" in (out / "publish" / "changes.diff").read_text(encoding="utf-8")
    assert [h["event"] for h in plan.history] == ["prepared", "changes_requested", "updated"]
    assert plan.commands == ["git -C <docs-checkout> push origin docforge/qh-docs:docforge/qh-docs"]


def test_update_refuses_unchanged_failing_moved_or_closed(prepared):
    out, docs_root, cfg = prepared
    config = load_config(cfg)
    with pytest.raises(PublishError, match="nothing changed"):
        update_publish(run=out, checkout=docs_root, config=config)
    edit(out, "how-to/how-to.md", " <!-- evidence: C07 -->", "")
    with pytest.raises(PublishError, match="claim gate failed"):
        update_publish(run=out, checkout=docs_root, config=config)
    edit(out, "how-to/how-to.md", "- Sign in to Pulseboard.", "- Sign in to Pulseboard. <!-- evidence: C07 -->")
    edit(out, "how-to/how-to.md", "for one hour.", "for one hour only.")
    # Someone else moves the branch: DocForge must not overwrite their commit.
    tip = git(docs_root, "rev-parse", "docforge/qh-docs")
    other = git(docs_root, "commit-tree", f"{tip}^{{tree}}", "-p", tip, "-m", "manual edit")
    git(docs_root, "update-ref", "refs/heads/docforge/qh-docs", other)
    with pytest.raises(PublishError, match="moved since DocForge last committed"):
        update_publish(run=out, checkout=docs_root, config=config)
    assert git(docs_root, "rev-parse", "docforge/qh-docs") == other
    close_suggestion(out, reason="not_needed", note="", reviewer="r")
    with pytest.raises(PublishError, match="closed"):
        update_publish(run=out, checkout=docs_root, config=config)


# --- close ----------------------------------------------------------------------------


def test_close_with_reason(prepared, tmp_path):
    out, _, _ = prepared
    feedback, commands = close_suggestion(out, reason="already_documented", note="Covered by the settings page.",
                                          reviewer="Docs reviewer")
    plan = load_plan(out)
    assert (plan.status, plan.history[-1]["event"], plan.history[-1]["reason"]) == ("closed", "closed", "already_documented")
    assert commands == ["gh pr close docforge/qh-docs --repo example-org/docs-site --comment "
                        "'Closed: already_documented (Existing documentation already covers it). "
                        "Covered by the settings page.'"]
    row = json.loads((out / "review" / "feedback.jsonl").read_text(encoding="utf-8"))
    assert {k: row[k] for k in ("action", "reason", "reviewer", "comment", "revision")} == {
        "action": "close", "reason": "already_documented", "reviewer": "Docs reviewer",
        "comment": "Covered by the settings page.", "revision": 0}
    assert feedback_summary(out.parent)["already_documented"] == 1
    with pytest.raises(ReviewError, match="already closed"):
        close_suggestion(out, reason="quality", note="", reviewer="r")
    with pytest.raises(ReviewError, match="already closed"):
        request_changes(out, comment="x", reviewer="r")
    with pytest.raises(PublishError, match="closed"):
        mark_ready(out, "merged")


def test_close_needs_a_known_reason(prepared):
    out, _, _ = prepared
    with pytest.raises(ReviewError, match="reason must be one of"):
        close_suggestion(out, reason="meh", note="", reviewer="r")
    assert load_plan(out).status == "open"


# --- CLI ------------------------------------------------------------------------------


def test_cli_review_and_update(prepared, capsys):
    out, docs_root, cfg = prepared
    assert main(["review", "request-changes", str(out), "--comment", "Tighten the intro.", "--reviewer", "r"]) == 0
    assert "revise-1.md" in capsys.readouterr().out
    edit(out, "how-to/how-to.md", "for one hour.", "for one hour only.")
    assert main(["publish", "update", str(out), "--docs-checkout", str(docs_root), "--config", str(cfg)]) == 0
    text = capsys.readouterr().out
    assert "Added revision 1" in text and f"git -C {docs_root} push origin" in text
    assert main(["review", "close", str(out), "--reason", "quality", "--reviewer", "r"]) == 0
    assert "gh pr close docforge/qh-docs" in capsys.readouterr().out
    assert main(["review", "close", str(out), "--reason", "quality", "--reviewer", "r"]) == 1
