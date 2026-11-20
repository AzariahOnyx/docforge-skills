"""Paragraph-level fixes to existing articles (B12b): the checks, the gate on changed lines only, archive
marking, and a Jira ticket's approved plan editing and archiving published articles in the drafts PR.

Stub Jira, fake model client, fake GitHub API and a local bare docs repository. No network, no cost.
"""

import json
from pathlib import Path
import subprocess
import sys

import pytest

pytest.importorskip("pdfplumber")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conftest import git  # noqa: E402
from test_backend import DONE, FakeClient, answer, stage_answer  # noqa: E402
from test_gate import MARKED  # noqa: E402
from test_ia_plan import FIXTURE, docs, github  # noqa: E402,F401
from test_jira_work import KEY, jira  # noqa: E402,F401
from test_plan_review import approve, deliver, planned, run_ticket  # noqa: E402

from docforge.jira import load_state  # noqa: E402
from docforge.jira.state import Pending, save_state  # noqa: E402
from docforge.outdated.fix import check_edit, mark_archived  # noqa: E402
from docforge.plan.review import process_plan_pr  # noqa: E402
from docforge.publish.gate import EvidenceRules, check_pages  # noqa: E402

SETTINGS = "site/alerts/notifications/settings.md"
SNOOZE = "site/alerts/notifications/snooze.md"
ARTICLE = ("---\ntitle: Notification settings\n---\n\n# Notification settings\n\n## Pause alerts\n\n"
           "Notification settings let each member control alerts.\n\n"
           "Select **Snooze** to pause your in-app alerts.\n\n![The pause control](images/snooze.png)\n\n"
           "- Email alerts\n- In-app alerts\n")
OLD_ARTICLE = "---\ntitle: Snooze alerts\n---\n\n# Snooze alerts\n\nUse Snooze when you need quiet time.\n"
PASSAGE = "Select **Snooze** to pause your in-app alerts."
FIXED = "Select **Pause alerts** to pause your in-app alerts for one hour. <!-- evidence: C03 -->"


# --- the checks ---------------------------------------------------------------------------


def check(after, **kw):
    return check_edit(ARTICLE, after, passage=kw.get("passage", PASSAGE), old_strings=kw.get("old", ["Snooze"]),
                      new_strings=kw.get("new", ["Pause alerts"]))


def test_a_good_fix_passes():
    assert check(ARTICLE.replace(PASSAGE, FIXED)) == []
    kept = ARTICLE.replace(PASSAGE, "Select **Snooze to Pause** now.")
    assert check(ARTICLE.replace(PASSAGE, FIXED).replace("pause control", "Snooze control"))  # alt text counts too
    assert check(kept, old=["Snooze"], new=["Snooze to Pause"]) == []  # old wording inside its own new wording


@pytest.mark.parametrize("change, message", [
    (lambda t: t.replace("title: Notification settings", "title: Settings"), "front matter changed"),
    (lambda t: t.replace("## Pause alerts", "## Pausing"), "headings changed"),
    (lambda t: t.replace("- Email alerts\n", ""), "list items were removed"),
    (lambda t: t.replace("![The pause control](images/snooze.png)", ""), "images were lost"),
    (lambda t: t.replace("Notification settings let each member control alerts.", "Hi."), "shrank"),
    (lambda t: t, "outdated passage is still in the article"),
    (lambda t: t.replace(PASSAGE, "Click **Snooze** now to pause alerts quickly."), "old wording is still"),
])
def test_each_check_catches_its_problem(change, message):
    found = check(change(ARTICLE))
    assert any(message in p for p in found), found


def test_archive_only_adds_the_status():
    archived = mark_archived(OLD_ARTICLE)
    assert "status: archived" in archived and archived.endswith("Use Snooze when you need quiet time.\n")
    assert check_edit(OLD_ARTICLE, archived, passage="", old_strings=[], new_strings=[], archive=True) == []
    assert check_edit(OLD_ARTICLE, archived + "More.\n", passage="", old_strings=[], new_strings=[], archive=True)
    assert mark_archived("# No front matter\n").startswith("---\nstatus: archived\n---")
    assert "status: archived" in mark_archived("---\nstatus: draft\n---\n# A\n")


def test_gate_checks_only_changed_lines():
    page = ARTICLE.replace(PASSAGE, FIXED)
    rules = EvidenceRules(known=["C03"], allowed={"p.md": ["C03"]})
    assert not check_pages({"p.md": page}, rules).passed  # the published, unmarked lines would all fail
    line = page.splitlines().index(FIXED) + 1
    scoped = rules.model_copy(update={"scopes": {"p.md": [[line, line]]}})
    assert check_pages({"p.md": page}, scoped).passed
    unmarked = page.replace(" <!-- evidence: C03 -->", "")
    assert not check_pages({"p.md": unmarked}, scoped).passed  # the changed paragraph still needs evidence


# --- end to end: a Jira ticket's approved plan edits and archives published articles ----------


PLAN = FIXTURE.read_text().replace("## Existing articles - impact\n\nNone.", (
    "## Existing articles - impact\n\n"
    "| Article | Docs path | Action | Change needed | Outdated passage | Evidence |\n"
    "| --- | --- | --- | --- | --- | --- |\n"
    f"| Notification settings | {SETTINGS} | update | Name the new button | {PASSAGE} | C03 |\n"
    f"| Snooze alerts | {SNOOZE} | archive | Quiet Hours replaces Snooze | Use Snooze when you need quiet time. | C02 |\n"
    "| Boards | site/index.md | none | Not affected | | none |"))


def publish_articles(docs):  # noqa: F811
    root, bare = docs
    for rel, text in ((SETTINGS, ARTICLE), (SNOOZE, OLD_ARTICLE)):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "published articles")
    git(root, "push", "-q", str(bare), "main:main")


def drafter_answer(fix_text=FIXED):
    files = {p: (MARKED / p).read_text() for p in ("feature/feature-guide.md", "how-to/how-to.md")}
    coverage = (DONE / "analysis" / "COVERAGE.md").read_text().replace("; release-note/release-note.md", "")
    coverage = coverage.replace("| C03 | INCLUDED | feature/feature-guide.md; how-to/how-to.md |",
                                f"| C03 | INCLUDED | feature/feature-guide.md; how-to/how-to.md; existing/edited/{SETTINGS} |")
    fixes = {"fixes": [{"path": SETTINGS, "find": PASSAGE, "replace": fix_text, "reason": "renamed"}]}
    return answer({**files, "analysis/COVERAGE.md": coverage, "analysis/fixes.json": json.dumps(fixes)})


def test_approved_plan_edits_and_archives_published_articles(jira, tmp_path, github, docs):  # noqa: F811
    publish_articles(docs)
    cfg, run = planned(jira, tmp_path, github, docs, plan_text=PLAN, backend={})
    commit = __import__("docforge.publish", fromlist=["load_plan"]).load_plan(run, "plan-pr").commit
    deliver(run, cfg, *approve(commit))
    result = process_plan_pr(run, config=cfg, checkout=docs[0])
    assert result["edits"] == [{"dest": SETTINGS, "action": "update"}, {"dest": SNOOZE, "action": "archive"}]
    assert result["needs_own_run"] == []
    manifest = json.loads((run / "run.json").read_text())
    assert [e["src"] for e in manifest["edits"]] == [f"existing/edited/{SETTINGS}", f"existing/edited/{SNOOZE}"]
    assert (run / "existing" / "original" / SETTINGS).read_text() == ARTICLE
    assert "status: archived" in (run / "existing" / "edited" / SNOOZE).read_text()
    order = (run / "prompts" / "2-drafter.md").read_text()
    assert "## Edits to existing articles" in order and "analysis/fixes.json" in order and PASSAGE in order
    assert "analysis/fixes.json" in order.split("## Write")[1]

    state = load_state(tmp_path / "state", KEY)
    state.phase, state.pending = "drafting", Pending(action="draft", at="t")
    save_state(tmp_path / "state", state)
    bad = drafter_answer(fix_text=PASSAGE + " For one hour. <!-- evidence: C03 -->")  # the outdated passage left in
    client = FakeClient(bad, drafter_answer(), stage_answer("proofreader"))
    drafted = run_ticket(cfg, tmp_path, client)
    assert drafted["result"] == "drafted", drafted
    repair = client.requests[1]["messages"][-1]["content"]
    assert "edit check:" in repair and "the outdated passage is still in the article" in repair
    assert f'path="existing/original/{SETTINGS}"' in client.requests[0]["messages"][0]["content"]
    assert f'path="existing/edited/{SETTINGS}"' in client.requests[2]["messages"][0]["content"]  # the Proofreader

    pr = github.pulls[2]
    tree = git(docs[1], "ls-tree", "-r", "--name-only", "docforge/pulse-77").splitlines()
    assert SETTINGS in tree and SNOOZE in tree
    edited = git(docs[1], "show", f"docforge/pulse-77:{SETTINGS}")
    assert FIXED in edited and "Notification settings let each member control alerts." in edited
    assert "status: archived" in git(docs[1], "show", f"docforge/pulse-77:{SNOOZE}")
    body = pr["body"]
    assert "## Edits to existing articles" in body and f"`{SETTINGS}`: 1 paragraph-level fix(es) (checks passed)" in body
    assert f"  - Before: {PASSAGE}" in body and "<!--" not in body.split("## Edits to existing articles")[1].split("##")[0]
    assert f"`{SNOOZE}`: marked `status: archived`" in body
    evidence = json.loads(git(docs[1], "show", "docforge/pulse-77:site/_docforge/pulse-77.evidence.json"))
    line = edited.splitlines().index(FIXED) + 1
    assert evidence["rules"]["scopes"] == {SETTINGS: [[line, line]], SNOOZE: []}  # an archive gates nothing
    assert evidence["rules"]["allowed"][SETTINGS] == ["C03"]


def test_docs_repo_ci_gate_checks_only_the_changed_lines(jira, tmp_path, github, docs):  # noqa: F811
    from docforge.publish import gate_manifest

    publish_articles(docs)
    cfg, run = planned(jira, tmp_path, github, docs, plan_text=PLAN, backend={})
    from docforge.publish import load_plan

    deliver(run, cfg, *approve(load_plan(run, "plan-pr").commit))
    process_plan_pr(run, config=cfg, checkout=docs[0])
    state = load_state(tmp_path / "state", KEY)
    state.phase, state.pending = "drafting", Pending(action="draft", at="t")
    save_state(tmp_path / "state", state)
    run_ticket(cfg, tmp_path, FakeClient(drafter_answer(), stage_answer("proofreader")))
    checkout = tmp_path / "ci"
    subprocess.run(["git", "clone", "-q", "-b", "docforge/pulse-77", str(docs[1]), str(checkout)], check=True)
    result = gate_manifest(checkout / "site" / "_docforge" / "pulse-77.evidence.json", checkout)
    assert result.passed, result.errors


def test_cli_fix(tmp_path, capsys):
    from docforge.cli import main

    run = tmp_path / "run"
    (run / "existing" / "original" / "site").mkdir(parents=True)
    (run / "analysis").mkdir()
    (run / "existing" / "original" / "site" / "a.md").write_text(ARTICLE)
    (run / "run.json").write_text(json.dumps({"edits": [{"src": "existing/edited/site/a.md", "dest": "site/a.md",
                                                          "action": "update", "passage": PASSAGE}]}))
    (run / "analysis" / "fixes.json").write_text(json.dumps({"fixes": [
        {"path": "site/a.md", "find": "control alerts", "replace": "manage alerts"},
        {"path": "site/other.md", "find": "x", "replace": "y"}]}))
    assert main(["outdated", "fix", str(run)]) == 1
    out = capsys.readouterr().out
    assert "FAIL: site/a.md" in out
    assert "outdated passage is still in the article" in out and "which the approved plan does not edit" in out
