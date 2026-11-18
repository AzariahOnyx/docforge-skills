"""The clean-up step kinds. Each takes a page's text and returns (new text, changes, findings).

Steps edit prose only: front matter, fenced code, evidence markers and other HTML
comments, inline code, link targets and HTML tags are never changed (see textguard).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import html
import re
from urllib.parse import quote

from docforge.packs.model import (
    CheckStep,
    DropSentencesStep,
    MarkerLinkStep,
    MergeAlertsStep,
    MoveToTopStep,
    ReplaceStep,
)
from docforge.textguard import mask, prose_lines, sub_prose

MARKER = re.compile(r"\s*<!--\s*evidence:\s*(.*?)\s*-->\s*$")
LINE_PARTS = re.compile(r"^(\s*(?:>\s?)*\s*(?:(?:[-*+]|\d+[.)])\s+)?)(.*)$")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
ALERT_START = re.compile(r"^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$")
LINK_TEXT = re.compile(r"\[([^\]]*)\]\([^)]*\)")


@dataclass
class Change:
    step: str
    page: str
    line: int
    action: str  # replaced, removed, linked, merged, moved
    before: str
    after: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Finding:
    step: str
    page: str
    line: int
    message: str
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


def _flags(ignorecase: bool) -> int:
    return re.I if ignorecase else 0


def _short(text: str, limit: int = 160) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


# --- replace -------------------------------------------------------------------------


def run_replace(step: ReplaceStep, page: str, text: str):
    pattern = re.compile(step.pattern, _flags(step.ignorecase))
    lines = text.split("\n")
    changes = []
    for i in prose_lines(lines):
        new, count = sub_prose(lines[i], pattern, step.replacement)
        if count:
            changes.append(Change(step.id, page, i + 1, "replaced", _short(lines[i]), _short(new)))
            lines[i] = new
    return "\n".join(lines), changes, []


# --- drop_sentences ------------------------------------------------------------------


def _drop_in(body: str, pattern: re.Pattern) -> tuple[str, list[str]]:
    """Remove matching sentences from one piece of prose; returns (kept text, removed sentences)."""
    kept, removed = [], []
    for sentence in SENTENCE_SPLIT.split(body):
        if pattern.search(mask(sentence)):
            removed.append(sentence)
        else:
            kept.append(sentence)
    return " ".join(kept), removed


def run_drop_sentences(step: DropSentencesStep, page: str, text: str):
    pattern = re.compile(step.pattern, _flags(step.ignorecase))
    lines = text.split("\n")
    changes, findings, drop = [], [], set()
    for i in prose_lines(lines):
        line = lines[i]
        if not pattern.search(mask(line)):
            if pattern.search(line):
                findings.append(Finding(step.id, page, i + 1, "match left in code or a link target", _short(line)))
            continue
        marker = MARKER.search(line)
        content = line[: marker.start()] if marker else line
        tail = line[marker.start():] if marker else ""
        if content.lstrip().startswith("|"):
            cells = content.split("|")
            for c in range(1, len(cells) - 1):
                cell = cells[c]
                if pattern.fullmatch(mask(cell).strip() or "-"):
                    findings.append(Finding(step.id, page, i + 1, "match is a whole table cell; left in place",
                                            cell.strip()))
                    continue
                kept, removed = _drop_in(cell.strip(), pattern)
                if removed:
                    cells[c] = f" {kept} " if kept else " "
                    changes += [Change(step.id, page, i + 1, "removed", _short(r), "") for r in removed]
            lines[i] = "|".join(cells) + tail
            continue
        prefix, body = LINE_PARTS.match(content).groups()
        kept, removed = _drop_in(body, pattern)
        changes += [Change(step.id, page, i + 1, "removed", _short(r), "") for r in removed]
        if kept.strip():
            lines[i] = prefix + kept + tail
        else:
            drop.add(i)
            if marker and i > 0 and lines[i - 1].strip() and (i - 1) not in drop:
                lines[i - 1] = lines[i - 1].rstrip() + " " + tail.strip()  # the statement keeps its marker
    if drop:
        lines = [l for n, l in enumerate(lines) if n not in drop]
    out = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    return out, changes, findings


# --- marker_link ---------------------------------------------------------------------


def _mailto(step: MarkerLinkStep, kind: str, phrase: str) -> str:
    phrase = " ".join(html.unescape(phrase or "").split()).rstrip(".").strip()
    if not phrase:
        return f"mailto:{step.address}"
    template = step.templates.get(kind.upper()) or step.templates[step.default_type]
    subject = template.subject.replace("{phrase}", phrase)
    body = step.body.replace("{line}", template.line.replace("{phrase}", phrase))
    return f"mailto:{step.address}?subject={quote(subject, safe='')}&body={quote(body, safe='')}"


def run_marker_link(step: MarkerLinkStep, page: str, text: str):
    pattern = re.compile(step.pattern)
    lines = text.split("\n")
    changes = []

    def link(match: re.Match) -> str:
        return f"[{step.link_text or step.address}]({_mailto(step, match.group('type') or '', match.group('phrase') or '')})"

    for i in prose_lines(lines):
        new, count = sub_prose(lines[i], pattern, link)
        if count:
            changes.append(Change(step.id, page, i + 1, "linked", _short(lines[i]), _short(new)))
            lines[i] = new
    return "\n".join(lines), changes, []


# --- alerts --------------------------------------------------------------------------


def _alert_blocks(lines: list[str], allowed: set[int]) -> list[tuple[int, int, str]]:
    """(first line, last line exclusive, type) for each GitHub alert block in prose."""
    blocks, i = [], 0
    while i < len(lines):
        match = ALERT_START.match(lines[i]) if i in allowed else None
        if not match:
            i += 1
            continue
        end = i + 1
        while end < len(lines) and lines[end].startswith(">"):
            end += 1
        blocks.append((i, end, match.group(1)))
        i = end
    return blocks


def _marker_ids(block: list[str]) -> tuple[list[str], str | None]:
    ids, exempt = [], None
    for line in block:
        found = MARKER.search(line)
        if found:
            value = found.group(1)
            if value.lower().startswith("none"):
                exempt = exempt or value
            else:
                ids += [x.strip() for x in value.split(",") if x.strip()]
    return list(dict.fromkeys(ids)), exempt


def _items(block: list[str]) -> list[str]:
    """The alert's content as list items: its own list items, or its paragraph as one item."""
    body = [MARKER.sub("", re.sub(r"^>\s?", "", l)).rstrip() for l in block[1:]]
    body = [l for l in body if l.strip()]
    if body and all(re.match(r"^\s*[-*+]\s+", l) for l in body):
        return [re.sub(r"^\s*[-*+]\s+", "", l) for l in body]
    return [" ".join(l.strip() for l in body)] if body else []


def run_merge_alerts(step: MergeAlertsStep, page: str, text: str):
    lines = text.split("\n")
    changes = []
    types = set(step.types)
    while True:
        blocks = _alert_blocks(lines, set(prose_lines(lines)))
        pair = next(((a, b) for a, b in zip(blocks, blocks[1:])
                     if a[2] == b[2] and (not types or a[2] in types)
                     and all(not l.strip() for l in lines[a[1]:b[0]])), None)
        if pair is None:
            break
        (s1, e1, kind), (s2, e2, _) = pair
        first, second = lines[s1:e1], lines[s2:e2]
        ids, exempt = _marker_ids(first + second)
        items = _items(first) + _items(second)
        marker = f" <!-- evidence: {', '.join(ids)} -->" if ids else (f" <!-- evidence: {exempt} -->" if exempt else "")
        merged = [f"> [!{kind}]"] + [f"> - {item}" for item in items]
        merged[-1] += marker
        changes.append(Change(step.id, page, s1 + 1, "merged", _short(" ".join(first + second)), _short(" ".join(merged))))
        lines[s1:e2] = merged
    return "\n".join(lines), changes, []


def run_move_to_top(step: MoveToTopStep, page: str, text: str):
    pattern = re.compile(step.match, re.M)
    lines = text.split("\n")
    allowed = prose_lines(lines)
    title = next((i for i in allowed if re.match(r"^#\s+\S", lines[i])), None)
    if title is None:
        return text, [], [Finding(step.id, page, 0, "page has no # title; nothing moved", "")]
    blocks = _alert_blocks(lines, set(allowed))
    target = next((b for b in blocks if pattern.search("\n".join(lines[b[0]:b[1]]))), None)
    if target is None:
        return text, [], []
    first_block = next((i for i in allowed if i > title and lines[i].strip()), None)
    if first_block == target[0]:
        return text, [], []
    block = lines[target[0]:target[1]]
    rest = lines[: target[0]] + lines[target[1]:]
    if target[1] < len(lines) and target[0] > 0 and not lines[target[0] - 1].strip() and not lines[target[1]].strip():
        rest = lines[: target[0]] + lines[target[1] + 1:]  # keep a single blank line where it was
    insert = title + 1
    rest[insert:insert] = [""] + block
    out = re.sub(r"\n{3,}", "\n\n", "\n".join(rest))
    return out, [Change(step.id, page, target[0] + 1, "moved", _short(" ".join(block)), "below the page title")], []


# --- check ---------------------------------------------------------------------------


def run_check(step: CheckStep, page: str, text: str):
    pattern = re.compile(step.pattern, _flags(step.ignorecase))
    lines = text.split("\n")
    findings = []
    for i in prose_lines(lines):
        line = re.sub(r"<!--.*?-->", lambda m: " " * len(m.group(0)), lines[i])
        line = re.sub(r"`+[^`]*`+", lambda m: " " * len(m.group(0)), line)
        line = re.sub(r"\]\([^)]*\)", lambda m: "]" + " " * (len(m.group(0)) - 1), line)  # link targets
        for match in pattern.finditer(line):
            if step.unless_linked and any(l.start(1) <= match.start() and match.end() <= l.end(1)
                                          for l in LINK_TEXT.finditer(lines[i])):
                continue
            findings.append(Finding(step.id, page, i + 1, step.message, _short(lines[i])))
            break  # one finding per line
    return text, [], findings


RUNNERS = {
    "replace": run_replace,
    "drop_sentences": run_drop_sentences,
    "marker_link": run_marker_link,
    "merge_alerts": run_merge_alerts,
    "move_to_top": run_move_to_top,
    "check": run_check,
}
