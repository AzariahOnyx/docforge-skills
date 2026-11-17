"""Product-change sources: GitHub pull request events and their diffs; Jira issues and
Confluence pages fetched read-only as Markdown source files."""

from .diff import ChangedFile, DiffError, changes_for_event, git_diff, parse_unified_diff, read_diff_file
from .atlassian import SourceFetchError
from .github_event import EventError, PrEvent, parse_event

__all__ = [
    "ChangedFile",
    "DiffError",
    "EventError",
    "PrEvent",
    "SourceFetchError",
    "changes_for_event",
    "git_diff",
    "parse_event",
    "parse_unified_diff",
    "read_diff_file",
]
