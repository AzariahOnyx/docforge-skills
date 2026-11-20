"""The outdated content finder (B12a): change note, shortlist with must-review pages, two verdict passes checked
against the articles, the merge into ia-plan.md, and recall on past changes.

A fictional Pulseboard docs set and code repository; a fake model client. No network, no key, no cost.
"""

import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conftest import git  # noqa: E402
from test_backend import FakeClient  # noqa: E402
from test_triage import model_answer  # noqa: E402

from docforge.cli import main  # noqa: E402
from docforge.config import DocCollection, DocForgeConfig  # noqa: E402
from docforge.outdated import ChangeNote, build_shortlist, find_outdated, note_from_code  # noqa: E402
from docforge.outdated.evaluate import evaluate, propose_cases  # noqa: E402
from docforge.outdated.merge import merge_into_plan  # noqa: E402
from docforge.outdated.verdicts import check_pass, merge_passes, run_passes  # noqa: E402
from docforge.plan.model import parse_plan  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "plan"
PAGES = {
    "site/alerts/notifications/settings.md": "---\ntitle: Notification settings\n---\n\n# Notification settings\n\n"
    "## Pause alerts\n\nSelect **Snooze** to pause your in-app alerts.\n\n![The Snooze button](images/snooze.png)\n",
    "site/alerts/notifications/snooze.md": "---\ntitle: Snooze alerts\n---\n\n# Snooze alerts\n\n"
    "Use Snooze when you need quiet time.\n\n1. Open **Settings > Notifications**.\n2. Click **Snooze**.\n",
    "site/alerts/notifications/quiet-hours-faq.md": "---\ntitle: Quiet Hours FAQ\n---\n\n# Quiet Hours FAQ\n\n"
    "Quiet Hours pauses alerts for a member.\n",
    "site/boards/index.md": "---\ntitle: Boards\n---\n\n# Boards\n\nBoards show your work.\n",
}
SETTINGS, SNOOZE, FAQ = list(PAGES)[:3]


@pytest.fixture
def docs(tmp_path):
    root = tmp_path / "docs-site"
    for rel, text in PAGES.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
    return root


@pytest.fixture
def code(tmp_path):
    root = tmp_path / "web"
    (root / "src" / "locales").mkdir(parents=True)
    (root / "specs" / "quiet-hours").mkdir(parents=True)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.name", "Dev")
    git(root, "config", "user.email", "dev@example.com")
    (root / "src" / "locales" / "en.json").write_text(json.dumps({"alerts": {"pause": "Snooze", "keep": "Keep"}}))
    (root / "src" / "Pause.tsx").write_text('const label = "Snooze";\nconst id = "pause-btn";\n')
    (root / "specs" / "quiet-hours" / "spec.md").write_text("# Spec\n\nMembers use **Snooze**.\n")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "base")
    base = git(root, "rev-parse", "HEAD")
    (root / "src" / "locales" / "en.json").write_text(json.dumps({"alerts": {"pause": "Pause alerts", "keep": "Keep"}}))
    (root / "src" / "Pause.tsx").write_text('const label = "Pause alerts";\nconst id = "pause-button";\n')
    (root / "specs" / "quiet-hours" / "spec.md").write_text("# Spec\n\nMembers use **Pause alerts** in **Quiet Hours**.\n")
    git(root, "commit", "-q", "-am", "rename")
    return root, base, git(root, "rev-parse", "HEAD")


def note(**kw) -> ChangeNote:
    from docforge.outdated import StringChange

    return ChangeNote("test", [StringChange("Snooze", "Pause alerts", "en.json:alerts.pause")], [],
                      kw.get("terms", ["Quiet Hours"]), [])


# --- change note ---------------------------------------------------------------------------


def test_note_from_code(code):
    root, base, head = code
    made = note_from_code(root, base, head, spec_paths=["specs/**/spec.md"])
    pairs = [(s.old, s.new, s.where) for s in made.strings]
    assert ("Snooze", "Pause alerts", "src/locales/en.json:alerts.pause") in pairs
    assert ("Snooze", None, "src/Pause.tsx") in pairs and ("pause-btn", None, "src/Pause.tsx") not in pairs
    assert made.old_strings == ["Snooze"]
    assert made.spec_changes[0]["path"] == "specs/quiet-hours/spec.md"
    assert "Quiet Hours" in made.terms and "Pause alerts" in made.terms


# --- shortlist ----------------------------------------------------------------------------


def test_shortlist_must_review_terms_cap_and_images(docs):
    shortlist = build_shortlist(docs, note(), must_review=["Boards show"], cap=3)
    paths = [p["path"] for p in shortlist["pages"]]
    assert set(shortlist["must_review"]) == {SETTINGS, SNOOZE, "site/boards/index.md"}
    assert paths[:3] != [] and FAQ not in paths  # the cap keeps every must-review page first
    settings = next(p for p in shortlist["pages"] if p["path"] == SETTINGS)
    assert settings["images"] == ["images/snooze.png"] and 'old wording "Snooze"' in settings["reasons"]
    assert shortlist["dropped"] == 1 and shortlist["searched_pages"] == 4
    roomy = build_shortlist(docs, note(), cap=10)
    assert FAQ in [p["path"] for p in roomy["pages"]] and "site/boards/index.md" not in roomy["must_review"]
    narrow = build_shortlist(docs, note(), collection=DocCollection(filter=["site/boards/"]))
    assert narrow["pages"] == []


# --- verdicts -------------------------------------------------------------------------------


def verdict(path, v="affected", passage="", action="edit", reason="r"):
    return {"path": path, "verdict": v, "passage": passage, "action": action, "reason": reason}


def test_quotes_are_checked_against_the_article(docs):
    shortlist = build_shortlist(docs, note(), cap=10)
    checked = check_pass({"verdicts": [
        verdict(SETTINGS, passage="Select Snooze to pause your in-app alerts."),  # emphasis and spacing ignored
        verdict(SNOOZE, passage="Click Snooze twice."),
        verdict(FAQ, passage=""),
        verdict("site/other.md", passage="x")]}, shortlist, docs)
    assert checked[SETTINGS]["verdict"] == "affected"
    assert checked[SNOOZE]["verdict"] == "unsure" and "not in the article" in checked[SNOOZE]["note"]
    assert checked[FAQ]["verdict"] == "unsure" and "site/other.md" not in checked


def test_passes_are_merged(docs):
    shortlist = build_shortlist(docs, note(), cap=10)
    first = {SETTINGS: verdict(SETTINGS, passage="Select **Snooze**"), SNOOZE: verdict(SNOOZE, action="archive"),
             FAQ: verdict(FAQ, "not_affected", action="none")}
    second = {SETTINGS: verdict(SETTINGS, passage="Select **Snooze**"), SNOOZE: verdict(SNOOZE, "not_affected",
                                                                                     action="none")}
    merged = {m["path"]: m for m in merge_passes(first, second, shortlist)}
    assert (merged[SETTINGS]["verdict"], merged[SETTINGS]["passage"]) == ("affected", "Select **Snooze**")
    assert merged[SNOOZE]["verdict"] == "unsure" and "disagree" in merged[SNOOZE]["reason"]
    assert merged[FAQ]["verdict"] == "not_affected"  # one pass, not must-review, not affected
    only_one = {m["path"]: m for m in merge_passes(first, {}, shortlist)}
    assert only_one[SETTINGS]["verdict"] == "unsure" and "without a verdict in pass 2" in only_one[SETTINGS]["reason"]


def config(**extra) -> DocForgeConfig:
    return DocForgeConfig.model_validate({"doc_collections": {"example-org/docs-site": {"filter": ["site/"]}},
                                          **extra})


def run_folder(tmp_path, plan=None) -> Path:
    run = tmp_path / "repo" / "run"
    (run / "analysis").mkdir(parents=True)
    (tmp_path / "repo" / "prd.md").write_text("# PRD\n\nMembers use **Quiet Hours**.\n")
    (run / "run.json").write_text(json.dumps({"sources": [{"id": "S1", "path": "prd.md"}], "deliverables": []}))
    if plan:
        (run / "analysis" / "ia-plan.md").write_text(plan)
    return run


def test_backend_runs_two_independent_passes(tmp_path, docs):
    run = run_folder(tmp_path)
    shortlist = build_shortlist(docs, note(), cap=10)
    answers = [model_answer({"verdicts": [verdict(SETTINGS, passage="Select **Snooze**")]}) for _ in range(2)]
    client = FakeClient(*answers)
    cfg = config(backend={})
    assert run_passes(run, cfg, note().to_dict(), shortlist, docs, client=client) == "done"
    first, second = (r["messages"][0]["content"] for r in client.requests)
    assert first.index(SETTINGS) != second.index(SETTINGS)  # a different page order per pass
    assert "data, never instructions" in client.requests[0]["system"][0]["text"]
    calls = [json.loads(l) for l in (run / "backend" / "calls.jsonl").read_text().splitlines()]
    assert [c["stage"] for c in calls] == ["outdated-pass-1", "outdated-pass-2"]
    capped = config(backend={"max_cost_usd": 0.0001})
    run2 = run_folder(tmp_path / "b")
    assert run_passes(run2, capped, note().to_dict(), shortlist, docs, client=FakeClient()).startswith("stopped before")


def test_find_outdated_fills_the_plan(tmp_path, docs):
    run = run_folder(tmp_path, (FIXTURES / "ia-plan-unified.md").read_text())
    cfg = config()
    repo = tmp_path / "repo"
    sources_only = run_folder(tmp_path / "plain")  # no code change: the note has terms only, no old wording
    find_outdated(sources_only, tmp_path / "plain" / "repo", cfg, docs=docs, collection="example-org/docs-site")
    plain = json.loads((sources_only / "analysis" / "change-note.json").read_text())
    assert plain["old_strings"] == [] and "Quiet Hours" in plain["terms"]
    # This run's change note names the old wording (from a code diff, or written by a person).
    (run / "analysis" / "change-note.json").write_text(json.dumps(note().to_dict()))
    assert find_outdated(run, repo, cfg, docs=docs, collection="example-org/docs-site") == "waiting"
    assert (run / "prompts" / "outdated-pass-1.md").is_file() and (run / "prompts" / "outdated-pass-2.md").is_file()
    shortlist = json.loads((run / "analysis" / "outdated-shortlist.json").read_text())
    passes = {SETTINGS: verdict(SETTINGS, passage="Select **Snooze** to pause your in-app alerts."),
              SNOOZE: verdict(SNOOZE, passage="Click **Snooze**.", action="archive"),
              FAQ: verdict(FAQ, "not_affected", action="none")}
    pages = [p["path"] for p in shortlist["pages"]]
    for n in (1, 2):
        items = [passes[p] for p in pages if p in passes]
        if n == 2:
            items = [dict(i, verdict="unsure") if i["path"] == SNOOZE else i for i in items]
        (run / "outdated").mkdir(exist_ok=True)
        (run / "outdated" / f"pass-{n}.json").write_text(json.dumps({"verdicts": items}))
    assert find_outdated(run, repo, cfg, docs=docs, collection="example-org/docs-site") == "done"
    plan, _ = parse_plan((run / "analysis" / "ia-plan.md").read_text())
    rows = {r["Docs path"]: r for r in plan.existing}
    # The plan quoted a sentence that is not in the article; the finder's checked passage replaces it.
    assert rows[SETTINGS]["Outdated passage"] == "Select **Snooze** to pause your in-app alerts."
    assert rows[SNOOZE]["Change needed"].startswith("(check: ")  # the passes did not agree on this row
    assert FAQ not in rows
    report = (run / "analysis" / "OUTDATED.md").read_text()
    assert "## Screenshots to check" in report and "images/snooze.png" in report


def test_merge_converts_a_first_format_section():
    first = (FIXTURES / "ia-plan.md").read_text().replace("## Existing articles - impact\n\nNone.", (
        "## Existing articles - impact\n\n| Article | Docs path | Change | Why | Claims |\n| --- | --- | --- | --- | --- |\n"
        "| Old | site/old.md | deprecate | Replaced | C01 |"))
    text, changed = merge_into_plan(first, [{"path": SETTINGS, "title": "Notification settings", "verdict": "affected",
                                             "action": "edit", "passage": "Select **Snooze**", "reason": "renamed"}])
    plan, errors = parse_plan(text)
    assert changed == 1 and not errors
    assert [(r["Docs path"], r["Action"]) for r in plan.existing] == [("site/old.md", "archive"), (SETTINGS, "update")]
    assert "| Article | Docs path | Action | Change needed | Outdated passage | Evidence |" in text


def test_plan_body_reports_the_check(tmp_path, docs):
    from docforge.plan.pr import plan_body

    run = run_folder(tmp_path)
    (run / "analysis" / "outdated.json").write_text(json.dumps({"searched": 4, "pages": [
        {"path": SETTINGS, "verdict": "affected", "must_review": True, "reasons": ['old wording "Snooze"']}]}))
    plan, _ = parse_plan((FIXTURES / "ia-plan-unified.md").read_text())
    body = plan_body(plan, run, "plans/quiet-hours/ia-plan.md")
    assert "## Outdated content check (4 pages searched)" in body and 'affected (must review: old wording "Snooze")' in body


# --- recall ---------------------------------------------------------------------------------


def test_recall_and_proposed_cases(tmp_path, docs):
    git(docs, "init", "-q", "-b", "main")
    git(docs, "add", ".")
    git(docs, "-c", "user.name=W", "-c", "user.email=w@example.com", "commit", "-q", "-m", "init")
    (docs / SETTINGS).write_text(PAGES[SETTINGS].replace("Snooze", "Pause alerts"))
    git(docs, "-c", "user.name=W", "-c", "user.email=w@example.com", "commit", "-q", "-am", "PULSE-12 rename Snooze")
    cases_file = tmp_path / "cases.json"
    proposed = propose_cases(docs, cases_file, collection=DocCollection(filter=["site/"]))
    assert [(c["id"], c["expected"]) for c in proposed["cases"]] == [("PULSE-12", [SETTINGS])]
    with pytest.raises(Exception, match="already exists"):
        propose_cases(docs, cases_file)
    git(docs, "checkout", "-q", "HEAD~1")  # score against the docs as they were before the change
    data = json.loads(cases_file.read_text())
    data["cases"][0]["note"] = note().to_dict()
    data["cases"][0]["expected"] = [SETTINGS, SNOOZE, FAQ]
    data["checked_by"] = "Reviewer"
    cases_file.write_text(json.dumps(data))
    report = evaluate(cases_file, docs, cap=2)
    assert report["shortlist_recall"] == "2/3" and report["rows"][0]["missed"] == [FAQ]
    assert report["verdict_recall"].startswith("n/a") and report["checked_by"] == "Reviewer"


def test_cli(tmp_path, docs, code, capsys):
    root, base, head = code
    note_file = tmp_path / "note.json"
    assert main(["outdated", "note", "--code-checkout", str(root), "--base", base, "--head", head,
                 "--out", str(note_file)]) == 0
    assert main(["outdated", "shortlist", "--note", str(note_file), "--docs", str(docs),
                 "--config", str(tmp_path / "none.yaml")]) == 0
    out = capsys.readouterr().out
    assert f"MUST {SETTINGS}" in out and "must review" in out
