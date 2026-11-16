"""Split reader-facing Markdown into statements and read their evidence markers.

A statement is a paragraph, a list item (with its continuation lines), a
block quote, or a table data row. Headings, table header rows, fenced code,
front matter and plain HTML comments are not statements.

Each statement carries one invisible marker, usually at its end:

    <!-- evidence: C03, C07 -->              backed by these claims
    <!-- evidence: none (navigation) -->      states no product fact; reason shown to reviewers

A marker on its own line belongs to the statement just above it.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from docforge.docs_index.build import FENCE_RE, split_front_matter
from docforge.evidence.models import CLAIM_ID

MARKER_RE = re.compile(r"<!--\s*evidence:\s*(.*?)\s*-->", re.I | re.S)
COMMENT_ONLY_RE = re.compile(r"^\s*<!--.*-->\s*$")
HEADING_RE = re.compile(r"^ {0,3}#{1,6}(\s|$)")
LIST_RE = re.compile(r"^ {0,3}(?:[-*+]|\d+[.)])\s+")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
NONE_RE = re.compile(r"none\s*\((.+)\)", re.I | re.S)


@dataclass
class Statement:
    line: int
    kind: str  # paragraph, list, table
    lines: list[str]
    end: int = 0
    claims: list[str] | None = None
    exempt: str | None = None
    error: str | None = None

    @property
    def text(self) -> str:
        text = MARKER_RE.sub("", " ".join(l.strip() for l in self.lines)).strip()
        if self.kind == "list":
            text = LIST_RE.sub("", text, count=1)
        return text

    @property
    def snippet(self) -> str:
        text = " ".join(self.text.split())
        return text if len(text) <= 80 else text[:77].rstrip() + "..."


def read_marker(text: str) -> tuple[list[str] | None, str | None, str | None]:
    """(claim IDs, exemption reason, error) for the markers in one statement."""
    values = MARKER_RE.findall(text)
    if not values:
        return None, None, None
    if len(values) > 1:
        return None, None, "more than one evidence marker"
    value = " ".join(values[0].split())
    if value.lower().startswith("none"):
        match = NONE_RE.fullmatch(value)
        if not match or not match.group(1).strip():
            return None, None, "write an exemption as 'evidence: none (reason)'"
        return None, match.group(1).strip(), None
    ids = [part.strip() for part in value.split(",")]
    bad = [i for i in ids if not CLAIM_ID.fullmatch(i)]
    if bad or not ids:
        return None, None, f"invalid claim ID(s) in marker: {', '.join(bad) or '(empty)'}"
    return list(dict.fromkeys(ids)), None, None


def statements(markdown: str) -> list[Statement]:
    lines = markdown.splitlines()
    _, start = split_front_matter(lines, [])
    found: list[Statement] = []
    current: Statement | None = None
    fence: str | None = None

    def close() -> None:
        nonlocal current
        if current is not None:
            found.append(current)
            current = None

    for index in range(start, len(lines)):
        number, line = index + 1, lines[index]
        fence_match = FENCE_RE.match(line)
        if fence is not None:
            if fence_match and fence_match.group(1)[0] == fence[0] and len(fence_match.group(1)) >= len(fence):
                fence = None
            continue
        if fence_match:
            close()
            fence = fence_match.group(1)
            continue
        stripped = line.strip()
        if not stripped or HEADING_RE.match(line):
            close()
            continue
        if COMMENT_ONLY_RE.match(line):
            if not MARKER_RE.search(line):
                continue  # an ordinary comment
            # A marker on its own line belongs to the statement above it.
            target = current if current is not None else (found[-1] if found and found[-1].end == number - 1 else None)
            if target is None:
                found.append(Statement(number, "marker", [line], number, error="evidence marker is not attached to a statement"))
            else:
                target.lines.append(line)
                target.end = number
            continue
        if stripped.startswith("|"):
            close()
            if TABLE_SEP_RE.match(stripped):
                if found and found[-1].kind == "table" and found[-1].end == number - 1:
                    found.pop()  # the row above a separator is the header row
                continue
            found.append(Statement(number, "table", [line], number))
            continue
        if LIST_RE.match(line):
            close()
            current = Statement(number, "list", [line], number)
            continue
        if current is None:
            current = Statement(number, "paragraph", [line], number)
        else:
            current.lines.append(line)
            current.end = number
    close()

    for statement in found:
        if statement.error is None:
            statement.claims, statement.exempt, statement.error = read_marker("\n".join(statement.lines))
    return found
