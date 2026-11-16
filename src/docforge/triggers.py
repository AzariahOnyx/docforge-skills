"""Decide whether a pull request event matches a `github_pr` trigger.

Skip rules run first (draft PRs, PRs that only change dot-files, our own
PRs). Then each `match` entry is checked: within an entry every filter must
pass; across entries, the first entry that passes wins. Every outcome comes
with the reasons, so a "no" can be explained as well as a "yes".
"""

from __future__ import annotations

from fnmatch import fnmatchcase
from typing import Literal

from pydantic import BaseModel, Field

from docforge.config import GithubPrMatch, GithubPrTrigger
from docforge.sources import ChangedFile, PrEvent

Outcome = Literal["triggered", "skipped", "not_matched"]


class TriggerCheck(BaseModel):
    trigger: str
    outcome: Outcome
    reasons: list[str] = Field(default_factory=list)
    # 1-based number of the match entry that passed, when triggered.
    match_entry: int | None = None


def is_dot_path(path: str) -> bool:
    """True for dot-files and anything inside a dot-folder (e.g. .github/)."""
    return any(part.startswith(".") for part in path.split("/") if part)


def _under(path: str, directory: str) -> bool:
    directory = directory.strip("/")
    return not directory or path == directory or path.startswith(directory + "/")


def skip_reasons(trigger: GithubPrTrigger, event: PrEvent, changed: list[ChangedFile] | None) -> list[str]:
    reasons = []
    if event.draft:
        reasons.append("draft pull request")
    own = trigger.own_pr
    if event.head_branch.startswith(own.branch_prefix):
        reasons.append(f"our own pull request (head branch starts with {own.branch_prefix!r})")
    elif event.author and event.author.casefold() in {login.casefold() for login in own.bot_logins}:
        reasons.append(f"our own pull request (author {event.author!r})")
    if changed and all(is_dot_path(f.path) and (f.old_path is None or is_dot_path(f.old_path)) for f in changed):
        reasons.append("only dot-files changed")
    return reasons


def entry_failures(entry: GithubPrMatch, event: PrEvent, changed: list[ChangedFile] | None) -> list[str]:
    """Reasons this match entry does not apply; empty when it does."""
    failures = []
    repo = event.repo.casefold()
    if event.kind not in entry.trigger_on:
        failures.append(f"event {event.kind!r} not in trigger_on {entry.trigger_on}")
    if entry.repos != "all" and repo not in {r.casefold() for r in entry.repos}:
        failures.append(f"repo {event.repo} not in repos")
    if repo in {r.casefold() for r in entry.excluded_repos}:
        failures.append(f"repo {event.repo} is excluded")
    if entry.repo_owners and event.owner.casefold() not in {o.casefold() for o in entry.repo_owners}:
        failures.append(f"owner {event.owner} not in repo_owners")
    if entry.repo_topics and not set(entry.repo_topics) & set(event.topics):
        failures.append(f"repo topics {event.topics} share none of {entry.repo_topics}")
    if entry.branches and not any(fnmatchcase(event.base_branch, b) for b in entry.branches):
        failures.append(f"target branch {event.base_branch!r} matches none of {entry.branches}")
    if entry.trigger_directories:
        if changed is None:
            failures.append("trigger_directories set but the changed files are unknown (no diff supplied)")
        else:
            paths = [p for f in changed for p in (f.path, f.old_path) if p]
            if not any(_under(p, d) for p in paths for d in entry.trigger_directories):
                failures.append(f"no changed file under {entry.trigger_directories}")
    return failures


def check_trigger(name: str, trigger: GithubPrTrigger, event: PrEvent,
                  changed: list[ChangedFile] | None) -> TriggerCheck:
    if event.kind is None:
        return TriggerCheck(trigger=name, outcome="not_matched", reasons=[event.ignored_reason or "event ignored"])
    skips = skip_reasons(trigger, event, changed)
    if skips:
        return TriggerCheck(trigger=name, outcome="skipped", reasons=skips)
    reasons = []
    for number, entry in enumerate(trigger.match, start=1):
        failures = entry_failures(entry, event, changed)
        if not failures:
            return TriggerCheck(trigger=name, outcome="triggered", match_entry=number,
                                reasons=[f"match entry {number} passed every filter"])
        reasons += [f"entry {number}: {failure}" for failure in failures]
    return TriggerCheck(trigger=name, outcome="not_matched", reasons=reasons)
