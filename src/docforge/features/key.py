"""Which feature a code pull request belongs to.

1. A Jira key in the head branch or the title (for example `proj-123-schedule` or `PROJ-123: Schedule`). When
   Jira sources are configured, only their project keys count, so `utf-8` or `ISO-8601` never match.
2. Otherwise the dependency-map area's feature, when the changed files point to exactly one.
3. Otherwise the pull request is a feature of its own.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

KEY_RE = re.compile(r"(?<![A-Za-z0-9])([A-Za-z][A-Za-z0-9_]{0,31})-([1-9][0-9]{0,8})(?![A-Za-z0-9])")


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")[:60]


@dataclass
class FeatureKey:
    key: str  # file-safe: proj-123, scheduled-publishing, web-app-pr-105
    label: str  # for people: PROJ-123, Scheduled Publishing, example-org/web-app#105
    jira: str | None = None
    how: str = ""  # jira, area, pull_request


def jira_key(texts: list[str], project_keys: set[str]) -> str | None:
    for text in texts:
        for match in KEY_RE.finditer(text or ""):
            project, number = match.group(1).upper(), match.group(2)
            if project_keys and project not in project_keys:
                continue
            if not project_keys and match.start() != 0:
                continue  # without configured Jira projects, a key counts only at the start (proj-123-..., PROJ-123: ...)
            return f"{project}-{number}"
    return None


def feature_key(*, repo: str, number: int, branch: str, title: str, features: list[str],
                project_keys: set[str]) -> FeatureKey:
    key = jira_key([branch, title], project_keys)
    if key:
        return FeatureKey(slug(key), key, key, "jira")
    if len(features) == 1:
        return FeatureKey(slug(features[0]), features[0], None, "area")
    return FeatureKey(f"{slug(repo.split('/', 1)[1])}-pr-{number}", f"{repo}#{number}", None, "pull_request")
