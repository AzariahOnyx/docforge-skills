"""Slack notifications: dry run by default, policy-gated sending, against a local stub. No network."""

import json

import pytest

from docforge.cli import main
from docforge.config import DocForgeConfig
from docforge.notify import NotifyError, build_message, notify

PRD_TEXT = "SECRET-PRD-SENTENCE about alerts."


@pytest.fixture
def run(tmp_path):
    folder = tmp_path / "quiet-hours-docs"
    (folder / "analysis").mkdir(parents=True)
    (folder / "publish").mkdir()
    (folder / "run.json").write_text(json.dumps({"sources": [], "publish": {"collection": "example-org/docs"}}))
    (folder / "analysis" / "HANDOVER.md").write_text(f"# Quiet Hours\n\n{PRD_TEXT}\n")
    (folder / "analysis" / "clarifications-and-assumptions.md").write_text(
        f"## Q1: Time zone?\n\n{PRD_TEXT}\n\n## Q2: Weekends?\n")
    (folder / "analysis" / "cross-source.json").write_text(json.dumps(
        [{"claim_id": "C01", "status": "needs_engineering", "question_id": "X1", "question": "?"},
         {"claim_id": "C02", "status": "confirmed"}]))
    (folder / "publish" / "pr.json").write_text(json.dumps(
        {"title": "docs: Quiet Hours (DocForge draft)", "repo": "example-org/docs", "branch": "docforge/quiet-hours",
         "status": "open", "revision": 1}))
    return folder


def _config(webhook_env="TEST_SLACK_WEBHOOK", channel="#docs-review", collection_rule=True):
    notification = {"slack_channel": channel, "slack_webhook_env": webhook_env}
    rules = [{"if": {"doc_collection": "example-org/docs"}, "then": {"notification": notification}}]
    return DocForgeConfig.model_validate({"doc_collections": {"example-org/docs": {}},
                                          "policies": {"rules": rules if collection_rule else []}})


def test_message_is_minimal_and_has_no_source_text(run):
    text = build_message(run, "prepared", pr_url="https://github.com/example-org/docs/pull/7")
    assert text.startswith("*Docs suggestion prepared:* docs: Quiet Hours (DocForge draft)")
    assert "`example-org/docs`, branch `docforge/quiet-hours`, status open, revision 1" in text
    assert "Open questions: 3." in text
    assert "<https://github.com/example-org/docs/pull/7|Open the pull request>" in text
    assert PRD_TEXT not in text


def test_bad_pr_url_and_event_are_refused(run):
    with pytest.raises(NotifyError, match="pull request URL"):
        build_message(run, "prepared", pr_url="https://evil.example.com/x")
    with pytest.raises(NotifyError, match="event must be"):
        build_message(run, "merged")


def test_dry_run_is_default_and_posts_nothing(run, stub_server, monkeypatch):
    monkeypatch.setenv("TEST_SLACK_WEBHOOK", stub_server.url + "/hook")
    outcome = notify(run, "prepared", config=_config())
    assert not outcome.sent and outcome.reason.startswith("dry run")
    assert stub_server.requests == []
    log = [json.loads(line) for line in (run / "notify" / "slack.jsonl").read_text().splitlines()]
    assert log[-1]["sent"] is False


def test_send_posts_to_the_webhook_when_policy_allows(run, stub_server, monkeypatch):
    webhook = stub_server.url + "/services/T000/B000/fictional"
    stub_server.routes["/services/T000/B000/fictional"] = (200, b"ok", {"Content-Type": "text/plain"})
    monkeypatch.setenv("TEST_SLACK_WEBHOOK", webhook)
    outcome = notify(run, "revised", config=_config(), send=True)
    assert outcome.sent and outcome.channel == "#docs-review"
    method, path, headers, body = stub_server.requests[-1]
    assert method == "POST" and path == "/services/T000/B000/fictional"
    assert json.loads(body)["text"] == outcome.text
    log = (run / "notify" / "slack.jsonl").read_text()
    assert "fictional" not in log and stub_server.url not in log


def test_send_without_policy_does_not_post(run, stub_server, monkeypatch):
    monkeypatch.setenv("TEST_SLACK_WEBHOOK", stub_server.url + "/hook")
    outcome = notify(run, "prepared", config=_config(collection_rule=False), send=True)
    assert not outcome.sent and "sets no slack_channel" in outcome.reason
    outcome = notify(run, "prepared", config=None, send=True)
    assert not outcome.sent and "no docforge.yaml" in outcome.reason
    assert stub_server.requests == []


def test_missing_or_foreign_webhook_is_refused_without_echoing_it(run, monkeypatch):
    monkeypatch.delenv("TEST_SLACK_WEBHOOK", raising=False)
    with pytest.raises(NotifyError, match="TEST_SLACK_WEBHOOK is not set"):
        notify(run, "prepared", config=_config(), send=True)
    monkeypatch.setenv("TEST_SLACK_WEBHOOK", "https://collector.example.com/secret-path")
    with pytest.raises(NotifyError) as info:
        notify(run, "prepared", config=_config(), send=True)
    assert "secret-path" not in str(info.value)


def test_webhook_errors_do_not_leak_the_url(run, stub_server, monkeypatch):
    monkeypatch.setenv("TEST_SLACK_WEBHOOK", stub_server.url + "/secret-path")
    stub_server.routes["/secret-path"] = (403, b"invalid_token", {})
    with pytest.raises(NotifyError, match="HTTP 403") as info:
        notify(run, "prepared", config=_config(), send=True)
    assert "secret-path" not in str(info.value)
    stub_server.routes["/secret-path"] = (302, b"", {"Location": stub_server.url + "/elsewhere"})
    with pytest.raises(NotifyError, match="redirect"):
        notify(run, "prepared", config=_config(), send=True)
    assert all(r[1] != "/elsewhere" for r in stub_server.requests)


def test_cli_dry_run_and_send(run, stub_server, monkeypatch, tmp_path, capsys):
    import yaml

    config = tmp_path / "docforge.yaml"
    config.write_text(yaml.safe_dump(_config().model_dump(by_alias=True, exclude_none=True)))
    assert main(["notify", "slack", str(run), "--event", "prepared", "--config", str(config)]) == 0
    assert "[dry run" in capsys.readouterr().out
    assert stub_server.requests == []
    stub_server.routes["/hook"] = (200, b"ok", {})
    monkeypatch.setenv("TEST_SLACK_WEBHOOK", stub_server.url + "/hook")
    assert main(["notify", "slack", str(run), "--event", "prepared", "--config", str(config), "--send"]) == 0
    assert "[sent to #docs-review]" in capsys.readouterr().out
    assert len(stub_server.requests) == 1
    # --send without a config is reported as not sent and exits non-zero.
    assert main(["notify", "slack", str(run), "--event", "prepared", "--send"]) == 1
