from pathlib import Path

import pytest

from docforge.cli import main
from docforge.config import ConfigError, DocForgeConfig, load_config

ROOT = Path(__file__).resolve().parent.parent


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "docforge.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_example_config_is_valid():
    config = load_config(ROOT / "docforge.example.yaml")
    assert "example-org/docs" in config.doc_collections
    assert "product-prs" in config.triggers


def test_empty_file_gives_empty_config(tmp_path):
    config = load_config(write(tmp_path, ""))
    assert config == DocForgeConfig()


def test_unknown_key_is_rejected(tmp_path):
    with pytest.raises(ConfigError, match="Extra inputs are not permitted"):
        load_config(write(tmp_path, "doc_colections: {}\n"))


def test_collection_key_must_be_owner_repo(tmp_path):
    with pytest.raises(ConfigError, match="owner/repo"):
        load_config(write(tmp_path, "doc_collections:\n  docs: {}\n"))


def test_trigger_key_must_be_slug(tmp_path):
    text = (
        "triggers:\n"
        "  Product_PRs:\n"
        "    trigger_type: github_pr\n"
        "    match: [{repos: all, trigger_on: [merge]}]\n"
    )
    with pytest.raises(ConfigError, match="lowercase slug"):
        load_config(write(tmp_path, text))


def test_updated_requires_explicit_repos(tmp_path):
    text = (
        "triggers:\n"
        "  prs:\n"
        "    trigger_type: github_pr\n"
        "    match: [{repos: all, trigger_on: [updated]}]\n"
    )
    with pytest.raises(ConfigError, match="explicit repos"):
        load_config(write(tmp_path, text))


def test_unknown_trigger_event_is_rejected(tmp_path):
    text = (
        "triggers:\n"
        "  prs:\n"
        "    trigger_type: github_pr\n"
        "    match: [{repos: all, trigger_on: [closed]}]\n"
    )
    with pytest.raises(ConfigError, match="trigger_on"):
        load_config(write(tmp_path, text))


def test_rule_referencing_unknown_trigger_is_rejected(tmp_path):
    text = (
        "policies:\n"
        "  rules:\n"
        "    - if: {trigger: missing}\n"
        "      then: {publishing: {auto_create_pr: true}}\n"
    )
    with pytest.raises(ConfigError, match="unknown trigger 'missing'"):
        load_config(write(tmp_path, text))


def test_rule_may_reference_built_in_trigger(tmp_path):
    text = (
        "policies:\n"
        "  rules:\n"
        "    - if: {trigger: github_mention}\n"
        "      then: {publishing: {suppress_source_pr_comments: true}}\n"
    )
    load_config(write(tmp_path, text))


def test_filter_rejects_paths_outside_repo(tmp_path):
    text = "doc_collections:\n  org/docs:\n    filter: [../secrets/]\n"
    with pytest.raises(ConfigError, match="relative path inside the repo"):
        load_config(write(tmp_path, text))


def test_filter_allows():
    config = load_config(ROOT / "docforge.example.yaml")
    docs = config.doc_collections["example-org/docs"]
    assert docs.allows("docs/guide/setup.md")
    assert not docs.allows("README.md")
    assert not docs.allows("docsx/page.md")


def test_policy_defaults_are_safe():
    policy = DocForgeConfig().resolve_policy(trigger=None, doc_collection=None)
    assert policy["publishing"]["auto_create_pr"] is False
    assert policy["publishing"]["auto_merge"] is False
    assert policy["archiving"] == {"enabled": True, "stale_after_days": 30}


def test_policy_rule_overrides_only_what_it_sets():
    config = load_config(ROOT / "docforge.example.yaml")
    matched = config.resolve_policy(trigger="product-prs", doc_collection="example-org/docs")
    assert matched["publishing"]["auto_create_pr"] is True
    assert matched["publishing"]["auto_merge"] is False
    other = config.resolve_policy(trigger="api", doc_collection="example-org/docs")
    assert other["publishing"]["auto_create_pr"] is False


def test_later_rule_wins(tmp_path):
    text = (
        "doc_collections:\n  org/docs: {}\n"
        "policies:\n"
        "  rules:\n"
        "    - if: {doc_collection: org/docs}\n"
        "      then: {archiving: {stale_after_days: 10}}\n"
        "    - if: {doc_collection: org/docs}\n"
        "      then: {archiving: {stale_after_days: 5}}\n"
    )
    config = load_config(write(tmp_path, text))
    policy = config.resolve_policy(trigger=None, doc_collection="org/docs")
    assert policy["archiving"]["stale_after_days"] == 5


def test_cli_validate(capsys, tmp_path):
    assert main(["config", "validate", str(ROOT / "docforge.example.yaml")]) == 0
    assert "is valid" in capsys.readouterr().out
    bad = write(tmp_path, "triggers: [oops]\n")
    assert main(["config", "validate", str(bad)]) == 1
    assert "is invalid" in capsys.readouterr().err


def test_own_pr_defaults_to_docforge_branch_prefix(tmp_path):
    text = (
        "triggers:\n"
        "  prs:\n"
        "    trigger_type: github_pr\n"
        "    match: [{repos: all, trigger_on: [merge]}]\n"
    )
    trigger = load_config(write(tmp_path, text)).triggers["prs"]
    assert trigger.own_pr.branch_prefix == "docforge/"
    assert trigger.own_pr.bot_logins == []


def test_own_pr_accepts_bot_logins(tmp_path):
    text = (
        "triggers:\n"
        "  prs:\n"
        "    trigger_type: github_pr\n"
        "    own_pr: {branch_prefix: docs-bot/, bot_logins: ['example-docs[bot]', example-user]}\n"
        "    match: [{repos: all, trigger_on: [merge]}]\n"
    )
    own = load_config(write(tmp_path, text)).triggers["prs"].own_pr
    assert (own.branch_prefix, own.bot_logins) == ("docs-bot/", ["example-docs[bot]", "example-user"])


@pytest.mark.parametrize(
    "own_pr, message",
    [
        ("{bot_logins: ['not a login']}", "not a GitHub login"),
        ("{branch_prefix: ''}", "at least 1 character"),
        ("{prefix: docforge/}", "Extra inputs are not permitted"),
    ],
)
def test_own_pr_is_strict(tmp_path, own_pr, message):
    text = (
        "triggers:\n"
        "  prs:\n"
        "    trigger_type: github_pr\n"
        f"    own_pr: {own_pr}\n"
        "    match: [{repos: all, trigger_on: [merge]}]\n"
    )
    with pytest.raises(ConfigError, match=message):
        load_config(write(tmp_path, text))


@pytest.mark.parametrize("source,message", [
    ({"source_type": "jira", "base_url": "http://jira.example.com"}, "must use https"),
    ({"source_type": "jira", "base_url": "https://user:pw@jira.example.com"}, "credentials"),
    ({"source_type": "jira", "base_url": "https://jira.example.com/?x=1"}, "query"),
    ({"source_type": "jira", "base_url": "ftp://jira.example.com"}, "https:// URL"),
    ({"source_type": "jira", "auth_token_env": "abc-123-token-value"}, "environment variable name"),
    ({"source_type": "jira", "user_env": "JIRA_USER"}, "user_env needs auth_token_env"),
    ({"source_type": "jira", "project_keys": ["lower"]}, "Jira project key"),
    ({"source_type": "jira", "acceptance_criteria_field": "description"}, "custom field"),
    ({"source_type": "confluence", "space_keys": ["bad key"]}, "space key"),
    ({"source_type": "confluence", "api_token": "x"}, "Extra inputs"),
])
def test_atlassian_sources_are_strict(source, message):
    with pytest.raises(ValueError, match=message):
        DocForgeConfig.model_validate({"context_sources": {"s": source}})


def test_atlassian_source_accepts_env_names_and_loopback_http():
    config = DocForgeConfig.model_validate({"context_sources": {
        "j": {"source_type": "jira", "base_url": "https://example.atlassian.net/", "user_env": "JIRA_USER_EMAIL",
              "auth_token_env": "JIRA_API_TOKEN", "project_keys": ["EXAMPLE"]},
        "local": {"source_type": "confluence", "base_url": "http://127.0.0.1:8080/wiki"}}})
    assert config.context_sources["j"].base_url == "https://example.atlassian.net"
    assert config.context_sources["local"].base_url == "http://127.0.0.1:8080/wiki"


def test_slack_webhook_is_named_by_env_var_and_resolved_by_policy():
    with pytest.raises(ValueError, match="environment variable name"):
        DocForgeConfig.model_validate({"policies": {"default": {"notification": {
            "slack_webhook_env": "https://hooks.slack.com/services/x"}}}})
    config = DocForgeConfig.model_validate({"policies": {"default": {"notification": {
        "slack_channel": "#docs", "slack_webhook_env": "SLACK_WEBHOOK_URL"}}}})
    assert config.resolve_policy(trigger=None, doc_collection=None)["notification"] == {
        "slack_channel": "#docs", "slack_webhook_env": "SLACK_WEBHOOK_URL"}
    assert DocForgeConfig().resolve_policy(trigger=None, doc_collection=None)["notification"] == {
        "slack_channel": None, "slack_webhook_env": None}
