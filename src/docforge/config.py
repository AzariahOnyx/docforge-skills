"""Schema and loader for docforge.yaml, the single configuration file.

The file has four sections, all optional:

- doc_collections: Git repositories the agent may write documentation to.
- context_sources: read-only sources the agent may consult, with scope limits.
- triggers: named events that start documentation work.
- policies: what happens to a suggestion (publishing, notifications, archiving).

Validation is strict: unknown keys, bad values, and references to undefined
triggers or collections are errors.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated, Literal, Union
from urllib.parse import urlsplit

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

# Trigger keys that exist without being defined in the file. Policy rules may
# reference them.
BUILT_IN_TRIGGERS = frozenset({"github_mention", "web", "api"})


class Strict(BaseModel):
    """Base model that rejects unknown keys."""

    model_config = ConfigDict(extra="forbid")


# --- doc_collections -------------------------------------------------------


class DocCollection(Strict):
    platform: Literal["github"] = "github"
    default_branch: str | None = None
    docs_framework: str | None = None
    docs_root_url: str | None = None
    config_file_path: str | None = None
    vale_config_path: str | None = None
    # Paths the agent may modify. Empty means any file. Entries ending in "/"
    # match a directory tree; other entries match a single file.
    filter: list[str] = Field(default_factory=list)

    @field_validator("filter")
    @classmethod
    def _no_absolute_paths(cls, value: list[str]) -> list[str]:
        for entry in value:
            if entry.startswith("/") or ".." in entry.split("/"):
                raise ValueError(f"filter entry must be a relative path inside the repo: {entry!r}")
        return value

    def allows(self, path: str) -> bool:
        """Return True if the agent may modify this repo-relative path."""
        if not self.filter:
            return True
        for entry in self.filter:
            if entry.endswith("/") and path.startswith(entry):
                return True
            if path == entry:
                return True
        return False


# --- context_sources -------------------------------------------------------


ENV_NAME_RE = re.compile(r"^[A-Z_][A-Z0-9_]{0,127}$")
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
JIRA_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,31}$")
SPACE_KEY_RE = re.compile(r"^~?[A-Za-z0-9_]{1,255}$")
FIELD_ID_RE = re.compile(r"^customfield_[0-9]{1,10}$")


def check_service_url(value: str) -> str:
    """HTTPS with a host and no credentials, query or fragment. Plain HTTP is
    accepted only for loopback hosts, so local test servers work."""
    parts = urlsplit(value)
    if parts.scheme not in ("https", "http") or not parts.hostname:
        raise ValueError(f"must be an https:// URL with a host: {value!r}")
    if parts.scheme == "http" and parts.hostname not in LOOPBACK_HOSTS:
        raise ValueError(f"must use https (plain http is allowed only for localhost): {value!r}")
    if parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError(f"must not contain credentials, a query or a fragment: {value!r}")
    return value.rstrip("/")


def check_env_name(value: str | None) -> str | None:
    if value is not None and not ENV_NAME_RE.match(value):
        raise ValueError(f"must be an environment variable name like JIRA_API_TOKEN, not a value: {value!r}")
    return value


class AtlassianSource(Strict):
    """Read-only connection settings. Credentials are named by environment
    variable; their values never appear in the config file."""

    base_url: str | None = None
    # With user_env set, requests use basic auth (Atlassian Cloud: account
    # email plus API token); without it, a bearer token (Data Center PAT).
    user_env: str | None = None
    auth_token_env: str | None = None

    @field_validator("base_url")
    @classmethod
    def _url(cls, value):
        return None if value is None else check_service_url(value)

    @field_validator("user_env", "auth_token_env")
    @classmethod
    def _env(cls, value):
        return check_env_name(value)

    @model_validator(mode="after")
    def _user_needs_token(self):
        if self.user_env and not self.auth_token_env:
            raise ValueError("user_env needs auth_token_env")
        return self


class JiraSource(AtlassianSource):
    source_type: Literal["jira"]
    project_keys: list[str] = Field(default_factory=list)
    acceptance_criteria_field: str | None = None

    @field_validator("project_keys")
    @classmethod
    def _keys(cls, value):
        for key in value:
            if not JIRA_KEY_RE.match(key):
                raise ValueError(f"not a Jira project key: {key!r}")
        return value

    @field_validator("acceptance_criteria_field")
    @classmethod
    def _field(cls, value):
        if value is not None and not FIELD_ID_RE.match(value):
            raise ValueError(f"must be a custom field ID like customfield_10050: {value!r}")
        return value


class ConfluenceSource(AtlassianSource):
    source_type: Literal["confluence"]
    space_keys: list[str] = Field(default_factory=list)

    @field_validator("space_keys")
    @classmethod
    def _keys(cls, value):
        for key in value:
            if not SPACE_KEY_RE.match(key):
                raise ValueError(f"not a Confluence space key: {key!r}")
        return value


ContextSource = Annotated[
    Union[JiraSource, ConfluenceSource], Field(discriminator="source_type")
]


# --- triggers --------------------------------------------------------------

PrEvent = Literal["opened", "first_approval", "merge", "updated"]


class GithubPrMatch(Strict):
    repos: Union[Literal["all"], list[str]]
    trigger_on: list[PrEvent] = Field(min_length=1)
    excluded_repos: list[str] = Field(default_factory=list)
    trigger_directories: list[str] = Field(default_factory=list)
    branches: list[str] = Field(default_factory=list)
    repo_topics: list[str] = Field(default_factory=list)
    repo_owners: list[str] = Field(default_factory=list)

    @field_validator("repos")
    @classmethod
    def _check_repos(cls, value):
        if value == "all":
            return value
        if not value:
            raise ValueError("repos must be 'all' or a non-empty list of owner/repo")
        for repo in value:
            if not REPO_RE.match(repo):
                raise ValueError(f"not an owner/repo name: {repo!r}")
        return value

    @model_validator(mode="after")
    def _updated_needs_explicit_repos(self):
        # 'updated' runs on every push, so it must be scoped to named repos.
        if "updated" in self.trigger_on and self.repos == "all":
            raise ValueError("trigger_on 'updated' requires an explicit repos list, not 'all'")
        return self


GITHUB_LOGIN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})(?:\[bot\])?$")


class OwnPr(Strict):
    """How to recognise pull requests DocForge opened itself, so they never trigger work."""

    branch_prefix: str = Field(default="docforge/", min_length=1)
    bot_logins: list[str] = Field(default_factory=list)

    @field_validator("bot_logins")
    @classmethod
    def _logins(cls, value: list[str]) -> list[str]:
        for login in value:
            if not GITHUB_LOGIN_RE.match(login):
                raise ValueError(f"not a GitHub login: {login!r}")
        return value


class GithubPrTrigger(Strict):
    trigger_type: Literal["github_pr"]
    own_pr: OwnPr = Field(default_factory=OwnPr)
    match: list[GithubPrMatch] = Field(min_length=1)


Trigger = Annotated[Union[GithubPrTrigger], Field(discriminator="trigger_type")]


# --- policies --------------------------------------------------------------


class Publishing(Strict):
    auto_create_pr: bool | None = None
    auto_merge: bool | None = None
    suppress_source_pr_comments: bool | None = None


class Notification(Strict):
    slack_channel: str | None = None
    # Name of the environment variable holding the Slack incoming-webhook URL.
    slack_webhook_env: str | None = None

    @field_validator("slack_webhook_env")
    @classmethod
    def _env(cls, value):
        return check_env_name(value)


class Archiving(Strict):
    enabled: bool | None = None
    stale_after_days: int | None = Field(default=None, gt=0)


class PolicyBlock(Strict):
    publishing: Publishing = Field(default_factory=Publishing)
    notification: Notification = Field(default_factory=Notification)
    archiving: Archiving = Field(default_factory=Archiving)


class RuleCondition(Strict):
    trigger: str | None = None
    doc_collection: str | None = None

    @model_validator(mode="after")
    def _needs_one(self):
        if self.trigger is None and self.doc_collection is None:
            raise ValueError("a rule's 'if' needs a trigger, a doc_collection, or both")
        return self


class PolicyRule(Strict):
    if_: RuleCondition = Field(alias="if")
    then: PolicyBlock

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Policies(Strict):
    default: PolicyBlock = Field(default_factory=PolicyBlock)
    rules: list[PolicyRule] = Field(default_factory=list)


# Safe defaults: nothing is opened or merged without a person choosing to.
DEFAULT_POLICY = {
    "publishing": {
        "auto_create_pr": False,
        "auto_merge": False,
        "suppress_source_pr_comments": False,
    },
    "notification": {"slack_channel": None, "slack_webhook_env": None},
    "archiving": {"enabled": True, "stale_after_days": 30},
}


# --- root ------------------------------------------------------------------


class DocForgeConfig(Strict):
    doc_collections: dict[str, DocCollection] = Field(default_factory=dict)
    context_sources: dict[str, ContextSource] = Field(default_factory=dict)
    triggers: dict[str, Trigger] = Field(default_factory=dict)
    policies: Policies = Field(default_factory=Policies)

    @field_validator("doc_collections")
    @classmethod
    def _collection_keys(cls, value):
        for key in value:
            if not REPO_RE.match(key):
                raise ValueError(f"doc_collections key must be owner/repo: {key!r}")
        return value

    @field_validator("context_sources", "triggers")
    @classmethod
    def _slug_keys(cls, value):
        for key in value:
            if not SLUG_RE.match(key):
                raise ValueError(
                    f"key must be a lowercase slug (letters, digits, hyphens; max 64): {key!r}"
                )
        return value

    @model_validator(mode="after")
    def _rules_reference_known_names(self):
        known_triggers = set(self.triggers) | BUILT_IN_TRIGGERS
        for i, rule in enumerate(self.policies.rules):
            cond = rule.if_
            if cond.trigger is not None and cond.trigger not in known_triggers:
                raise ValueError(f"policies.rules[{i}] references unknown trigger {cond.trigger!r}")
            if cond.doc_collection is not None and cond.doc_collection not in self.doc_collections:
                raise ValueError(
                    f"policies.rules[{i}] references unknown doc_collection {cond.doc_collection!r}"
                )
        return self

    def resolve_policy(self, *, trigger: str | None, doc_collection: str | None) -> dict:
        """Return the effective policy for a suggestion.

        Starts from safe defaults, applies policies.default, then each matching
        rule in order. Later rules override fields set by earlier ones.
        """
        effective = {section: dict(values) for section, values in DEFAULT_POLICY.items()}

        def apply(block: PolicyBlock) -> None:
            for section in ("publishing", "notification", "archiving"):
                for field, value in getattr(block, section).model_dump(exclude_unset=True).items():
                    effective[section][field] = value

        apply(self.policies.default)
        for rule in self.policies.rules:
            cond = rule.if_
            if cond.trigger is not None and cond.trigger != trigger:
                continue
            if cond.doc_collection is not None and cond.doc_collection != doc_collection:
                continue
            apply(rule.then)
        return effective


class ConfigError(Exception):
    """Raised when docforge.yaml cannot be read or is invalid."""


def load_config(path: str | Path) -> DocForgeConfig:
    path = Path(path)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"config file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path} is not valid YAML: {exc}") from exc
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ConfigError(f"{path} must contain a mapping at the top level")
    try:
        return DocForgeConfig.model_validate(raw)
    except ValidationError as exc:
        lines = [f"{path} is invalid:"]
        for err in exc.errors():
            loc = ".".join(str(part) for part in err["loc"]) or "(root)"
            lines.append(f"  - {loc}: {err['msg']}")
        raise ConfigError("\n".join(lines)) from exc
