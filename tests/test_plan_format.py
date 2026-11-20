"""One ia-plan.md format for the engine and the docs-writer agent (B12a-0).

The unified format adds an Outdated passage column, source-tag evidence, archive/none actions and the
decision/status front matter; plans in the first engine format are still read and converted.
"""

from pathlib import Path

import pytest

from docforge.plan import read_plan
from docforge.plan.model import parse_plan

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "plan"
UNIFIED = (FIXTURES / "ia-plan-unified.md").read_text()
FIRST = (FIXTURES / "ia-plan.md").read_text()
TYPES = ["overview", "procedural", "faq"]


def test_unified_plan_reads_back():
    plan, errors = read_plan(UNIFIED, types=TYPES, allows=lambda p: p.startswith("site/"))
    assert errors == []
    assert plan.front["decision"] == "act" and not plan.approved
    assert [(a["path"], a["change"]) for a in plan.articles()] == [
        ("site/alerts/notifications/pause-for-1-hour.md", "create"),
        ("site/alerts/notifications/settings.md", "update"),
        ("site/alerts/notifications/snooze.md", "archive"),
    ]  # the "none" row is listed in the plan but needs no work
    assert plan.existing[1]["Outdated passage"] == "Select **Snooze** to pause alerts."
    assert plan.conflicts[0]["Where"].startswith("Spec: Documentation impact")


def test_first_format_plans_are_converted():
    plan, errors = read_plan(FIRST, types=TYPES)
    assert errors == []
    assert set(plan.new[0]) == {"Title", "Type", "Docs path", "Why", "Evidence"}
    first_existing = FIRST.replace("## Existing articles - impact\n\nNone.", (
        "## Existing articles - impact\n\n| Article | Docs path | Change | Why | Claims |\n| --- | --- | --- | --- | --- |\n"
        "| Old | site/old.md | deprecate | Replaced | C01 |"))
    plan, errors = read_plan(first_existing, types=TYPES)
    assert errors == [] and plan.existing[0]["Action"] == "archive" and plan.existing[0]["Evidence"] == "C01"


@pytest.mark.parametrize("old, new, message", [
    ("| archive |", "| retire |", "action 'retire' must be update, archive, none"),
    ("status: proposed", "status: done", "status must be proposed or approved"),
    ("decision: act", "decision: maybe", "decision must be act, confirm, quiet"),
    ("| C02 |", "| the old article |", "neither a claim ID"),
    ("| X01 |", "| Conflict 1 |", "must look like X1"),
])
def test_unified_plan_problems(old, new, message):
    _, errors = read_plan(UNIFIED.replace(old, new), types=TYPES)
    assert any(message in e for e in errors), errors


def test_status_approved_and_mixed_columns():
    plan, _ = parse_plan(UNIFIED.replace("status: proposed", "status: approved"))
    assert plan.approved
    agent_a1 = UNIFIED.replace("| Article | Docs path | Action | Change needed | Outdated passage | Evidence |",
                               "| Article | Action | Change needed | Outdated passage |")
    _, errors = read_plan(agent_a1, types=TYPES)
    assert any("the columns must be Article | Docs path | Action" in e for e in errors)  # every route writes one format


def test_approved_copy_records_status():
    from docforge.plan.review import _with_status_approved

    assert "status: approved" in _with_status_approved(UNIFIED) and "status: proposed" not in _with_status_approved(UNIFIED)
    added = _with_status_approved(FIRST)
    assert parse_plan(added)[0].approved and added.endswith(FIRST.split("\n---", 1)[1][-40:])


def test_plan_body_shows_outdated_passages(tmp_path):
    from docforge.plan.pr import plan_body

    plan, _ = parse_plan(UNIFIED)
    body = plan_body(plan, tmp_path, "plans/quiet-hours/ia-plan.md")
    assert "## Outdated passages" in body and '"Select **Snooze** to pause alerts."' in body
    assert "- X01: Which behaviour is intended?" in body
