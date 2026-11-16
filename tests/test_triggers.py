import json
from pathlib import Path

import pytest

from docforge.config import GithubPrMatch, GithubPrTrigger, load_config
from docforge.sources import ChangedFile, parse_event, read_diff_file
from docforge.triggers import check_trigger, entry_failures, is_dot_path

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "github"
CONFIG = load_config(FIXTURES / "triggers.yaml")
PRODUCT = CONFIG.triggers["product-prs"]
TOPIC = CONFIG.triggers["topic-prs"]
CHANGES = read_diff_file(FIXTURES / "product_change.diff")
DOTFILES = read_diff_file(FIXTURES / "dotfiles_only.diff")


def event(name, github_event="pull_request", **kwargs):
    return parse_event(github_event, json.loads((FIXTURES / name).read_text(encoding="utf-8")), **kwargs)


def outcome(trigger, ev, changed=CHANGES, name="t"):
    check = check_trigger(name, trigger, ev, changed)
    return check.outcome, check.reasons


# --- recorded sample webhooks against tests/fixtures/github/triggers.yaml -----


@pytest.mark.parametrize(
    "fixture, product, topic",
    [
        ("pr_opened.json", "triggered", "not_matched"),
        ("pr_merged.json", "triggered", "not_matched"),
        ("pr_release_branch.json", "triggered", "not_matched"),
        ("pr_synchronize.json", "not_matched", "not_matched"),
        ("pr_closed_unmerged.json", "not_matched", "not_matched"),
        ("pr_labeled.json", "not_matched", "not_matched"),
        ("pr_other_branch.json", "not_matched", "not_matched"),
        ("pr_opened_draft.json", "skipped", "skipped"),
        ("pr_own_branch.json", "skipped", "skipped"),
        ("pr_own_bot.json", "skipped", "not_matched"),
        ("pr_infra_merged.json", "not_matched", "triggered"),
        ("pr_other_org.json", "not_matched", "not_matched"),
    ],
)
def test_recorded_webhooks(fixture, product, topic):
    ev = event(fixture)
    assert outcome(PRODUCT, ev)[0] == product
    assert outcome(TOPIC, ev)[0] == topic


def test_first_approval_review():
    assert outcome(PRODUCT, event("review_approved.json", "pull_request_review", prior_approvals=0))[0] == "triggered"
    status, reasons = outcome(PRODUCT, event("review_approved.json", "pull_request_review"))
    assert status == "not_matched"
    assert reasons == ["cannot confirm this is the first approval without a GitHub lookup"]


# --- reasons ---------------------------------------------------------------


def test_triggered_names_the_entry():
    check = check_trigger("product-prs", PRODUCT, event("pr_opened.json"), CHANGES)
    assert (check.match_entry, check.reasons) == (1, ["match entry 1 passed every filter"])


def test_skip_reasons():
    assert outcome(PRODUCT, event("pr_opened_draft.json"))[1] == ["draft pull request"]
    assert outcome(PRODUCT, event("pr_own_branch.json"))[1] == [
        "our own pull request (head branch starts with 'docforge/')"]
    assert outcome(PRODUCT, event("pr_own_bot.json"))[1] == ["our own pull request (author 'example-docs[bot]')"]
    assert outcome(PRODUCT, event("pr_opened.json"), DOTFILES)[1] == ["only dot-files changed"]


def test_not_matched_reasons_cover_each_failing_filter():
    status, reasons = outcome(TOPIC, event("pr_opened.json"))
    assert status == "not_matched"
    assert reasons == [
        "entry 1: event 'opened' not in trigger_on ['merge']",
        "entry 1: repo example-org/product-web is excluded",
    ]
    _, reasons = outcome(PRODUCT, event("pr_other_branch.json"))
    assert reasons == ["entry 1: target branch 'develop' matches none of ['main', 'release/*']"]
    _, reasons = outcome(TOPIC, event("pr_other_org.json"))
    assert reasons == ["entry 1: owner another-org not in repo_owners"]


def test_directories_need_a_diff():
    status, reasons = outcome(PRODUCT, event("pr_opened.json"), changed=None)
    assert status == "not_matched"
    assert reasons == ["entry 1: trigger_directories set but the changed files are unknown (no diff supplied)"]


def test_directories_must_contain_a_changed_file():
    docs_only = [ChangedFile(path="docs/readme.md")]
    _, reasons = outcome(PRODUCT, event("pr_opened.json"), changed=docs_only)
    assert reasons == ["entry 1: no changed file under ['src/']"]


def test_renamed_out_of_directory_still_counts():
    moved = [ChangedFile(path="lib/panel.py", old_path="src/settings/panel.py", status="renamed")]
    assert outcome(PRODUCT, event("pr_opened.json"), changed=moved)[0] == "triggered"


# --- combining match entries -------------------------------------------------


def test_any_entry_may_match_and_first_passing_entry_wins():
    trigger = GithubPrTrigger(trigger_type="github_pr", match=[
        GithubPrMatch(repos=["example-org/other"], trigger_on=["opened"]),
        GithubPrMatch(repos=["example-org/product-web"], trigger_on=["opened"]),
        GithubPrMatch(repos="all", trigger_on=["opened"]),
    ])
    check = check_trigger("t", trigger, event("pr_opened.json"), CHANGES)
    assert (check.outcome, check.match_entry) == ("triggered", 2)


def test_all_filters_in_an_entry_must_pass():
    entry = GithubPrMatch(repos="all", trigger_on=["opened"], repo_topics=["docs-sync"], branches=["develop"])
    assert entry_failures(entry, event("pr_opened.json"), CHANGES) == [
        "target branch 'main' matches none of ['develop']"]


def test_repo_names_are_case_insensitive():
    entry = GithubPrMatch(repos=["Example-Org/Product-Web"], trigger_on=["opened"])
    assert entry_failures(entry, event("pr_opened.json"), CHANGES) == []


@pytest.mark.parametrize(
    "path, expected",
    [(".github/workflows/ci.yml", True), (".editorconfig", True), ("src/.env.example", True),
     ("src/app.py", False), ("docs/guide.md", False)],
)
def test_is_dot_path(path, expected):
    assert is_dot_path(path) is expected
