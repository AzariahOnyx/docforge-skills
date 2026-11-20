"""Schema and loader for docforge.yaml, the single configuration file.

The file has six sections, all optional:

- doc_collections: Git repositories the agent may write documentation to.
- context_sources: read-only sources the agent may consult, with scope limits.
- triggers: named events that start documentation work.
- policies: what happens to a suggestion (publishing, notifications, archiving).
- packs: local folders with house style, references and article specs.
- backend: model settings for running stages through the Anthropic API.

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
    # GitHub connection, used only by `publish open` / `publish ready --apply` (and the Jira route
    # when a policy allows it). The token is read from the named environment variable at use time.
    api_url: str = "https://api.github.com"
    token_env: str = "GITHUB_TOKEN"
    # Where the docs branch is pushed. Default: https://<web host>/<owner>/<repo>.git. A file:// URL
    # (a local bare repository) is allowed for tests and demos.
    git_url: str | None = None
    # A local clone of the docs repository (relative to docforge.yaml), used to commit revisions.
    checkout: str | None = None
    # Where a plan pull request puts ia-plan.md ({slug}: the feature in lowercase with hyphens). The plan is
    # not a docs page, so this path is allowed even outside `filter`.
    plan_path: str = "plans/{slug}/ia-plan.md"
    # Review on DocForge's own pull requests (B7b). bot_login: DocForge's GitHub account, so mentions are
    # recognised and its own comments ignored. Only reviewers whose association is listed can ask for a revision.
    bot_login: str | None = Field(default=None, pattern=r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})(?:\[bot\])?$")
    reviewer_associations: list[Literal["OWNER", "MEMBER", "COLLABORATOR"]] = Field(
        default_factory=lambda: ["OWNER", "MEMBER", "COLLABORATOR"], min_length=1)
    max_revisions: int = Field(default=5, ge=0, le=20)
    revision_delay_seconds: int = Field(default=120, ge=0, le=3600)

    @field_validator("plan_path")
    @classmethod
    def _plan_path(cls, value):
        rest = value.replace("{slug}", "x")
        if "{slug}" not in value or "{" in rest or not value.endswith(".md") or value.startswith("/") \
                or ".." in value.split("/") or "\\" in value:
            raise ValueError(f"plan_path must be a relative .md path containing {{slug}}: {value!r}")
        return value

    @field_validator("api_url")
    @classmethod
    def _api_url(cls, value):
        return check_service_url(value)

    @field_validator("token_env")
    @classmethod
    def _token_env(cls, value):
        return check_env_name(value)

    @field_validator("git_url")
    @classmethod
    def _git_url(cls, value):
        if value is None or value.startswith("file:///"):
            return value
        url = check_service_url(value)
        if not url.endswith(".git"):
            raise ValueError(f"must end in .git: {value!r}")
        return url

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


class JiraStatuses(Strict):
    """Workflow status names. DocForge reacts only to `plan` and `draft`, and only writes the others,
    so its own ticket moves can never trigger it again (except the deliberate pull-back to `plan`)."""

    plan: str = Field(min_length=1)
    draft: str = Field(min_length=1)
    bounce: str = Field(min_length=1)
    planned: str = Field(min_length=1)
    # Statuses that mean the feature has shipped: the docs pull request may then leave draft.
    shipped: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _distinct(self):
        names = [self.plan, self.draft, self.bounce, self.planned]
        if len({n.casefold() for n in names}) != 4:
            raise ValueError("the four Jira status names must be different")
        if {n.casefold() for n in names} & {n.casefold() for n in self.shipped}:
            raise ValueError("a shipped status cannot also be the plan, draft, bounce or planned status")
        return self


class JiraWorkTypes(Strict):
    net_new: list[str] = Field(default_factory=list)
    enhancement: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _some(self):
        if not self.net_new and not self.enhancement:
            raise ValueError("work_types needs at least one Work Type name")
        if {w.casefold() for w in self.net_new} & {w.casefold() for w in self.enhancement}:
            raise ValueError("a Work Type cannot be both net_new and enhancement")
        return self


class JiraAttachments(Strict):
    max_bytes: int = Field(default=10 * 1024 * 1024, gt=0, le=100 * 1024 * 1024)
    max_pages: int = Field(default=300, gt=0)
    types: list[Literal["pdf", "md"]] = Field(default_factory=lambda: ["pdf", "md"], min_length=1)
    # Jira Cloud serves attachment content through a redirect to its media host. Only these hosts
    # (HTTPS) may be followed; credentials are never sent on a redirect.
    redirect_hosts: list[str] = Field(default_factory=lambda: ["api.media.atlassian.com"])

    @field_validator("redirect_hosts")
    @classmethod
    def _hosts(cls, value):
        for host in value:
            if not re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", host):
                raise ValueError(f"not a host name: {host!r}")
        return value


class JiraProduct(Strict):
    """Which pack product a ticket is about: a label (or component) mapped to a product key, else the default."""

    labels: dict[str, str] = Field(default_factory=dict)
    components: dict[str, str] = Field(default_factory=dict)
    default: str | None = None


class JiraPublish(Strict):
    """Where a ticket's drafts go: a doc collection (owner/repo) and a local checkout of it."""

    collection: str = Field(pattern=r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
    checkout: str = Field(min_length=1)  # relative to docforge.yaml
    base: str = Field(default="main", min_length=1)
    # Propose the plan as ia-plan.md in a plan pull request; approving that pull request approves the plan.
    plan_pr: bool = False


class JiraTicketTrigger(Strict):
    """A Jira board as the front door: ticket status moves start planning and drafting."""

    trigger_type: Literal["jira_ticket"]
    source: str  # a jira entry in context_sources (site, credentials, project_keys)
    statuses: JiraStatuses
    work_types: JiraWorkTypes
    bot_account_env: str
    webhook_secret_env: str
    attachments: JiraAttachments = Field(default_factory=JiraAttachments)
    pack: str | None = None
    product: JiraProduct = Field(default_factory=JiraProduct)
    # Folder (relative to docforge.yaml) where each ticket's sources and run are written:
    # <workspace>/tickets/<KEY>/. Keep it in a private repository.
    workspace: str | None = None
    audience: str = "readers of the product documentation"
    # Prepare a docs pull request after drafting. Opening it needs the auto_create_pr policy or a person.
    publish: JiraPublish | None = None

    @field_validator("bot_account_env", "webhook_secret_env")
    @classmethod
    def _env(cls, value):
        return check_env_name(value)


Trigger = Annotated[Union[GithubPrTrigger, JiraTicketTrigger], Field(discriminator="trigger_type")]


# --- policies --------------------------------------------------------------


class Publishing(Strict):
    auto_create_pr: bool | None = None
    auto_merge: bool | None = None
    suppress_source_pr_comments: bool | None = None
    # Jira front door: post comments on tickets, and move tickets between statuses.
    # Off by default: DocForge then records what it would post in the ticket's outbox.
    jira_comments: bool | None = None
    jira_transitions: bool | None = None
    # Code pull requests: post the advisory docs status (always "success", never blocking) and, when docs are
    # needed or a person must confirm, one comment. Off by default: decisions are only logged.
    source_pr_feedback: bool | None = None


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
        "jira_comments": False,
        "source_pr_feedback": False,
        "jira_transitions": False,
    },
    "notification": {"slack_channel": None, "slack_webhook_env": None},
    "archiving": {"enabled": True, "stale_after_days": 30},
}


# --- packs -----------------------------------------------------------------


class PackRef(Strict):
    """A local folder holding a pack.yaml. Relative paths resolve against docforge.yaml's folder."""

    path: str = Field(min_length=1)


# --- backend ---------------------------------------------------------------

Effort = Literal["low", "medium", "high", "xhigh", "max"]
MODEL_RE = re.compile(r"^[a-z0-9][a-z0-9.-]{1,63}$")


class ModelPrice(Strict):
    """US dollars per million tokens."""

    input: float = Field(ge=0)
    output: float = Field(ge=0)
    cache_read: float = Field(ge=0)
    cache_write_5m: float = Field(ge=0)
    cache_write_1h: float = Field(ge=0)


class BackendStage(Strict):
    model: str | None = None
    effort: Effort | None = None
    max_tokens: int | None = Field(default=None, ge=1024, le=128000)

    @field_validator("model")
    @classmethod
    def _model(cls, value):
        if value is not None and not MODEL_RE.match(value):
            raise ValueError(f"not a model ID: {value!r}")
        return value


class Backend(Strict):
    """Runs stages through the Anthropic API. Without this section no paid call is ever made."""

    provider: Literal["anthropic"] = "anthropic"
    model: str = "claude-opus-5-5"
    effort: Effort = "high"
    max_tokens: int = Field(default=64000, ge=1024, le=128000)
    # Name of the environment variable holding the API key. If it is unset, the SDK's own
    # credential chain is used (for example an `ant auth login` profile).
    api_key_env: str = "ANTHROPIC_API_KEY"
    # Server-side refusal fallback: a declined request is re-run on another model.
    fallbacks: bool = True
    max_cost_usd: float = Field(default=5.0, gt=0)
    prices: dict[str, ModelPrice] = Field(default_factory=dict)
    stages: dict[Literal["analyzer", "drafter", "proofreader"], BackendStage] = Field(default_factory=dict)

    @field_validator("model")
    @classmethod
    def _model(cls, value):
        if not MODEL_RE.match(value):
            raise ValueError(f"not a model ID: {value!r}")
        return value

    @field_validator("api_key_env")
    @classmethod
    def _env(cls, value):
        return check_env_name(value)


# --- root ------------------------------------------------------------------


# --- dependency map and triage (B7d) -----------------------------------------


GLOB_RE = re.compile(r"^[A-Za-z0-9_.*?\[\]{}/@+-]+$")


def check_globs(value: list[str]) -> list[str]:
    for pattern in value:
        if not GLOB_RE.match(pattern) or pattern.startswith("/") or ".." in pattern.split("/"):
            raise ValueError(f"not a relative path pattern: {pattern!r}")
    return value


class CodeArea(Strict):
    """Part of a code repository (a path prefix; "" is the whole repository) and what it belongs to."""

    path: str = ""
    products: list[str] = Field(min_length=1)
    feature: str | None = None
    spec: str | None = None  # the feature's spec.md in this repository, read when code here needs docs
    owner: str | None = None  # the owning writer
    documented: bool = True  # false: internal code nobody documents; changes there stay quiet

    @field_validator("path", "spec")
    @classmethod
    def _path(cls, value):
        if value is not None and (value.startswith("/") or ".." in value.split("/")):
            raise ValueError(f"area paths must be relative and stay inside the repository: {value!r}")
        return value


class CodeRepo(Strict):
    """One entry of the dependency map: a code repository, the docs it feeds and who owns what in it."""

    doc_collection: str | None = None
    documented: bool = True
    spec_paths: list[str] = Field(default_factory=lambda: ["spec.md", "**/spec.md"])
    areas: list[CodeArea] = Field(default_factory=list)
    api_url: str = "https://api.github.com"
    token_env: str = "GITHUB_TOKEN"
    # Local clone of this repository (relative to docforge.yaml): spec files and diffs are read from it.
    checkout: str | None = None
    # Folder (relative to docforge.yaml) for features started from this repository's pull requests:
    # <workspace>/features/<feature>/ and their state in <workspace>/state/. Keep it in a private repository.
    workspace: str | None = None
    pack: str | None = None  # house pack for plans and drafts from this repository
    audience: str = "readers of the product documentation"
    base: str = "main"  # the docs repository branch plan and drafts pull requests target

    @field_validator("spec_paths")
    @classmethod
    def _spec_paths(cls, value):
        return check_globs(value)

    @field_validator("api_url")
    @classmethod
    def _api_url(cls, value):
        return check_service_url(value)

    @field_validator("token_env")
    @classmethod
    def _token_env(cls, value):
        return check_env_name(value)


TRIAGE_CATEGORIES = ("tests", "ci_build", "dependencies", "infra", "repo_docs", "ui_text", "feature_flags")


class Triage(Strict):
    """The "docs needed?" decision for code pull requests. Path rules always run; the model runs only for
    changes the rules cannot decide, and only when `model` is set. Without it, those changes get "confirm"."""

    model: str | None = None
    api_key_env: str = "ANTHROPIC_API_KEY"
    effort: Effort = "low"
    max_tokens: int = Field(default=2000, ge=256, le=16000)
    max_diff_chars: int = Field(default=40000, ge=1000, le=400000)
    max_cost_usd_per_pr: float = Field(default=0.10, gt=0)
    max_cost_usd_per_day: float = Field(default=5.0, gt=0)
    prices: dict[str, ModelPrice] = Field(default_factory=dict)
    # Extra path patterns per category, added to DocForge's defaults.
    paths: dict[Literal["tests", "ci_build", "dependencies", "infra", "repo_docs", "ui_text", "feature_flags"],
                list[str]] = Field(default_factory=dict)

    @field_validator("api_key_env")
    @classmethod
    def _env(cls, value):
        return check_env_name(value)

    @field_validator("paths")
    @classmethod
    def _paths(cls, value):
        for patterns in value.values():
            check_globs(patterns)
        return value


class DocForgeConfig(Strict):
    doc_collections: dict[str, DocCollection] = Field(default_factory=dict)
    context_sources: dict[str, ContextSource] = Field(default_factory=dict)
    triggers: dict[str, Trigger] = Field(default_factory=dict)
    policies: Policies = Field(default_factory=Policies)
    packs: dict[str, PackRef] = Field(default_factory=dict)
    backend: Backend | None = None
    code_repos: dict[str, CodeRepo] = Field(default_factory=dict)  # the dependency map
    triage: Triage = Field(default_factory=Triage)

    @field_validator("code_repos")
    @classmethod
    def _code_repo_keys(cls, value):
        for key in value:
            if not REPO_RE.match(key):
                raise ValueError(f"code_repos key must be owner/repo: {key!r}")
        return value

    @model_validator(mode="after")
    def _code_repos_reference_collections(self):
        for name, repo in self.code_repos.items():
            if repo.doc_collection is not None and repo.doc_collection not in self.doc_collections:
                raise ValueError(f"code_repos.{name}: doc_collection {repo.doc_collection!r} is not in doc_collections")
            if repo.pack is not None and repo.pack not in self.packs:
                raise ValueError(f"code_repos.{name}: pack {repo.pack!r} is not in packs")
        return self

    @field_validator("doc_collections")
    @classmethod
    def _collection_keys(cls, value):
        for key in value:
            if not REPO_RE.match(key):
                raise ValueError(f"doc_collections key must be owner/repo: {key!r}")
        return value

    @field_validator("context_sources", "triggers", "packs")
    @classmethod
    def _slug_keys(cls, value):
        for key in value:
            if not SLUG_RE.match(key):
                raise ValueError(
                    f"key must be a lowercase slug (letters, digits, hyphens; max 64): {key!r}"
                )
        return value

    @model_validator(mode="after")
    def _jira_triggers_reference_sources(self):
        for name, trigger in self.triggers.items():
            if isinstance(trigger, JiraTicketTrigger):
                source = self.context_sources.get(trigger.source)
                if not isinstance(source, JiraSource):
                    raise ValueError(f"triggers.{name}: source {trigger.source!r} is not a jira context source")
                if trigger.pack is not None and trigger.pack not in self.packs:
                    raise ValueError(f"triggers.{name}: pack {trigger.pack!r} is not in packs")
                if trigger.publish is not None and trigger.publish.collection not in self.doc_collections:
                    raise ValueError(f"triggers.{name}: publish collection {trigger.publish.collection!r} "
                                     "is not in doc_collections")
        return self

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
