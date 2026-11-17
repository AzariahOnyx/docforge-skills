"""Fetch one Jira issue as a Markdown source file (read-only)."""

from __future__ import annotations

import re

from docforge.config import JiraSource

from . import provenance
from .adf import adf_to_markdown, neutralise
from .atlassian import AtlassianClient, SourceFetchError, segment

ISSUE_KEY_RE = re.compile(r"^([A-Z][A-Z0-9_]{0,31})-([1-9][0-9]{0,9})$")
FIELDS = ("summary", "description", "status", "labels", "issuelinks", "issuetype", "updated")


def project_of(key: str) -> str:
    match = ISSUE_KEY_RE.match(key)
    if not match:
        raise SourceFetchError(f"not a Jira issue key: {key!r}")
    return match.group(1)


def _check_project(source: JiraSource, key: str) -> None:
    project = project_of(key)
    if source.project_keys and project not in source.project_keys:
        raise SourceFetchError(f"project {project} is not in this source's project_keys")


def _links(fields: dict) -> list[str]:
    lines = []
    for link in fields.get("issuelinks") or []:
        kind = link.get("type") or {}
        if "outwardIssue" in link:
            other, relation = link["outwardIssue"], kind.get("outward", "relates to")
        elif "inwardIssue" in link:
            other, relation = link["inwardIssue"], kind.get("inward", "relates to")
        else:
            continue
        summary = ((other.get("fields") or {}).get("summary")) or ""
        lines.append(f"- {neutralise(relation)} {neutralise(other.get('key', '?'))}: {neutralise(summary)}".rstrip(": "))
    return lines


def fetch_issue(source: JiraSource, key: str, *, client: AtlassianClient | None = None) -> tuple[str, dict]:
    """Return (markdown, provenance) for one issue. Refuses issues outside project_keys."""
    _check_project(source, key)
    client = client or AtlassianClient(source)
    fields = list(FIELDS) + ([source.acceptance_criteria_field] if source.acceptance_criteria_field else [])
    data = client.get_json(f"rest/api/3/issue/{segment(key)}?fields={','.join(fields)}")
    actual = data.get("key") or key
    if actual != key:
        # A moved issue answers under its new key; check that project too.
        _check_project(source, actual)
    f = data.get("fields") or {}
    parts = []
    meta_lines = [
        f"- Type: {neutralise(((f.get('issuetype') or {}).get('name')) or 'unknown')}",
        f"- Status: {neutralise(((f.get('status') or {}).get('name')) or 'unknown')}",
    ]
    if f.get("labels"):
        meta_lines.append("- Labels: " + ", ".join(neutralise(str(x)) for x in f["labels"]))
    parts.append("\n".join(meta_lines))
    parts.append("## Description\n\n" + (adf_to_markdown(f.get("description")) or "_No description._"))
    if source.acceptance_criteria_field:
        criteria = adf_to_markdown(f.get(source.acceptance_criteria_field))
        parts.append("## Acceptance criteria\n\n" + (criteria or "_None recorded in the issue._"))
    links = _links(f)
    if links:
        parts.append("## Linked issues\n\n" + "\n".join(links) + "\n\nLinked issues were not fetched.")
    meta = {
        "kind": "jira", "id": actual, "title": f.get("summary") or actual,
        "url": client.url(f"browse/{segment(actual)}"),
        "version": f.get("updated") or "unknown", "updated": f.get("updated"), "fetched_at": provenance.now(),
    }
    title = f"{actual}: {f.get('summary') or 'Untitled issue'}"
    return provenance.render(meta, title, "\n\n".join(parts)), meta
