import json
from pathlib import Path

import pytest

from docforge.sources import EventError, parse_event

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "github"


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "name, kind",
    [
        ("pr_opened.json", "opened"),
        ("pr_reopened.json", "opened"),
        ("pr_ready_for_review.json", "opened"),
        ("pr_synchronize.json", "updated"),
        ("pr_merged.json", "merge"),
    ],
)
def test_pull_request_actions(name, kind):
    event = parse_event("pull_request", load(name))
    assert (event.kind, event.ignored_reason) == (kind, None)


@pytest.mark.parametrize(
    "name, reason",
    [
        ("pr_closed_unmerged.json", "closed without merging"),
        ("pr_labeled.json", "pull_request action 'labeled' does not start work"),
    ],
)
def test_ignored_pull_request_actions(name, reason):
    event = parse_event("pull_request", load(name))
    assert (event.kind, event.ignored_reason) == (None, reason)


def test_fields_are_normalised():
    event = parse_event("pull_request", load("pr_opened.json"))
    assert event.repo == "example-org/product-web"
    assert event.owner == "example-org"
    assert event.topics == ["docs-sync", "web"]
    assert (event.number, event.author, event.draft) == (42, "example-dev", False)
    assert (event.base_branch, event.head_branch) == ("main", "feature/quiet-hours")
    assert (event.base_sha, event.head_sha) == ("1" * 40, "2" * 40)


def test_draft_flag():
    assert parse_event("pull_request", load("pr_opened_draft.json")).draft is True


def test_first_approval_needs_known_prior_count():
    payload = load("review_approved.json")
    unknown = parse_event("pull_request_review", payload)
    assert (unknown.kind, unknown.ignored_reason) == (
        None, "cannot confirm this is the first approval without a GitHub lookup")
    first = parse_event("pull_request_review", payload, prior_approvals=0)
    assert first.kind == "first_approval"
    later = parse_event("pull_request_review", payload, prior_approvals=2)
    assert (later.kind, later.ignored_reason) == (None, "not the first approval (2 earlier)")


def test_non_approval_review():
    event = parse_event("pull_request_review", load("review_commented.json"), prior_approvals=0)
    assert (event.kind, event.ignored_reason) == (None, "review 'submitted' with state 'commented' is not an approval")


@pytest.mark.parametrize(
    "github_event, payload, message",
    [
        ("push", {"pull_request": {}}, "unsupported GitHub event"),
        ("pull_request", [], "no pull_request object"),
        ("pull_request", {"action": "opened"}, "no pull_request object"),
        ("pull_request", {"action": "opened", "pull_request": {"number": 1}}, "repository.full_name"),
    ],
)
def test_bad_payloads(github_event, payload, message):
    with pytest.raises(EventError, match=message):
        parse_event(github_event, payload)


def test_negative_prior_approvals():
    with pytest.raises(EventError, match="cannot be negative"):
        parse_event("pull_request_review", load("review_approved.json"), prior_approvals=-1)
