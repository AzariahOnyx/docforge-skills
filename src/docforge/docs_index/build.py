"""Page/section index and link map for a local docs folder.

`build_index` walks a docs folder, reads every Markdown/MDX page (limited by a
doc collection's `filter` when one is given), and records pages, sections,
links and backlinks. It only reads files and never uses the network.

Known limits: only ATX headings (`# Heading`) are indexed, not setext
(underlined) headings; anchors follow GitHub-style slugs, with Docusaurus-style
`{#custom-id}` overrides; site routes (`/docs/page`) that are not file paths
cannot be checked and are marked `unchecked`.
"""

from __future__ import annotations

from collections import defaultdict
import os
from pathlib import Path, PurePosixPath
import re
from typing import Iterator
from urllib.parse import unquote

import yaml

from docforge.config import DocCollection

from .models import DocsIndex, Link, Page, Section

PAGE_SUFFIXES = (".md", ".mdx")
SKIP_DIRS = {"node_modules"}  # plus every directory whose name starts with "."

HEADING_RE = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
CUSTOM_ID_RE = re.compile(r"\s*\{#([A-Za-z0-9_-]+)\}\s*$")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
INLINE_CODE_RE = re.compile(r"(`+).+?\1")
INLINE_LINK_RE = re.compile(r"(?<!!)\[(?:[^\[\]]|\[[^\]]*\])*\]\(\s*(<[^>]*>|[^\s)]+)(?:\s+[\"'(][^)]*)?\s*\)")
REF_DEF_RE = re.compile(r"^ {0,3}\[[^\]]+\]:\s*(<[^>]*>|\S+)")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
WORD_RE = re.compile(r"\w+")


class DocsIndexError(Exception):
    """Raised when a docs folder cannot be indexed."""


# --- headings and anchors --------------------------------------------------


def slugify(text: str) -> str:
    """GitHub-style heading anchor (lowercase, punctuation dropped, spaces to hyphens)."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # keep link text only
    text = re.sub(r"<[^>]+>", "", text)  # drop inline HTML tags
    text = text.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def _heading_text(raw: str) -> tuple[str, str | None]:
    """Return heading text and its explicit `{#id}`, if any."""
    match = CUSTOM_ID_RE.search(raw)
    if match:
        return raw[: match.start()].strip(), match.group(1)
    return raw.strip(), None


def visible_text(line: str) -> str:
    """Line text with link and image targets removed, keeping their labels."""
    return re.sub(r"\]\([^)]*\)", "]", line)


def _plain(text: str) -> str:
    """Heading text without inline Markdown emphasis or code markers."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.sub(r"[*_`]", "", text).strip()


# --- page parsing ----------------------------------------------------------


def split_front_matter(lines: list[str], warnings: list[str]) -> tuple[dict, int]:
    """Return (front matter, number of lines it occupies)."""
    if not lines or lines[0].strip() != "---":
        return {}, 0
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            try:
                data = yaml.safe_load("\n".join(lines[1:i]))
            except yaml.YAMLError:
                warnings.append("front matter is not valid YAML; ignored")
                return {}, i + 1
            if data is None:
                return {}, i + 1
            if not isinstance(data, dict):
                warnings.append("front matter is not a mapping; ignored")
                return {}, i + 1
            return data, i + 1
    warnings.append("front matter is not closed; treated as page content")
    return {}, 0


def _content_lines(lines: list[str], start: int) -> Iterator[tuple[int, str]]:
    """Yield (line number, text) for lines outside fenced code blocks."""
    fence: str | None = None
    for index in range(start, len(lines)):
        line = lines[index]
        match = FENCE_RE.match(line)
        if fence is None:
            if match:
                fence = match.group(1)
                continue
            yield index + 1, line
        elif match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence):
            fence = None


def own_text_ranges(page: Page, line_count: int, body_start: int) -> list[tuple[Section | None, int, int]]:
    """(section, first line, last line) of each section's own text, 1-based.

    The first entry has section None and covers the text before the first
    heading (after any front matter). Ranges exclude the heading line.
    """
    starts = sorted(page.sections, key=lambda s: s.start_line)
    ranges: list[tuple[Section | None, int, int]] = []
    first_heading = starts[0].start_line if starts else line_count + 1
    ranges.append((None, body_start + 1, first_heading - 1))
    for i, section in enumerate(starts):
        end = starts[i + 1].start_line - 1 if i + 1 < len(starts) else line_count
        ranges.append((section, section.start_line + 1, end))
    return ranges


def parse_page(path: str, text: str) -> tuple[Page, list[tuple[int, str]]]:
    """Parse one page. Returns the page and its raw (line, target) links."""
    lines = text.splitlines()
    warnings: list[str] = []
    front_matter, body_start = split_front_matter(lines, warnings)

    headings: list[tuple[int, int, str, str | None]] = []  # line, level, text, custom id
    raw_links: list[tuple[int, str]] = []
    for number, line in _content_lines(lines, body_start):
        heading = HEADING_RE.match(line)
        if heading:
            text_, custom = _heading_text(heading.group(2))
            if text_:
                headings.append((number, len(heading.group(1)), text_, custom))
        searchable = INLINE_CODE_RE.sub("", line)
        for match in INLINE_LINK_RE.finditer(searchable):
            raw_links.append((number, match.group(1)))
        ref = REF_DEF_RE.match(searchable)
        if ref:
            raw_links.append((number, ref.group(1)))

    sections: list[Section] = []
    used: dict[str, int] = {}
    for i, (number, level, heading_text, custom) in enumerate(headings):
        if custom:
            anchor = custom
        else:
            base = slugify(heading_text)
            count = used.get(base, 0)
            anchor = base if count == 0 else f"{base}-{count}"
            used[base] = count + 1
        end = len(lines)
        for later_number, later_level, _, _ in headings[i + 1 :]:
            if later_level <= level:
                end = later_number - 1
                break
        sections.append(
            Section(heading=_plain(heading_text), level=level, anchor=anchor, start_line=number, end_line=end)
        )
    anchors = [s.anchor for s in sections]
    if len(anchors) != len(set(anchors)):
        warnings.append("two or more sections share an anchor")

    title = front_matter.get("title")
    if not isinstance(title, str) or not title.strip():
        h1 = next((s.heading for s in sections if s.level == 1), None)
        title = h1 or PurePosixPath(path).stem
    page = Page(path=path, title=title.strip(), front_matter=front_matter, sections=sections, warnings=warnings)

    for section, first, last in own_text_ranges(page, len(lines), body_start):
        if section is not None:
            section.word_count = sum(len(WORD_RE.findall(visible_text(lines[n - 1]))) for n in range(first, last + 1))
    return page, raw_links


# --- discovery -------------------------------------------------------------


def discover_pages(root: Path, collection: DocCollection | None = None) -> list[str]:
    """Folder-relative POSIX paths of the pages to index."""
    found: list[str] = []
    resolved_root = root.resolve()
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS)
        for name in sorted(filenames):
            if not name.lower().endswith(PAGE_SUFFIXES):
                continue
            full = Path(directory) / name
            if not full.resolve().is_relative_to(resolved_root):
                continue  # symlink pointing outside the folder
            rel = full.relative_to(root).as_posix()
            if collection is None or collection.allows(rel):
                found.append(rel)
    return found


# --- link resolution -------------------------------------------------------


def _normalize(parts: PurePosixPath) -> str | None:
    """Collapse '.' and '..'; return None if the path leaves the indexed folder."""
    out: list[str] = []
    for part in parts.parts:
        if part in ("", "."):
            continue
        if part == "..":
            if not out:
                return None
            out.pop()
        else:
            out.append(part)
    return "/".join(out)


def _candidates(path: str) -> list[str]:
    if PurePosixPath(path).suffix.lower() in PAGE_SUFFIXES:
        return [path]
    stem = path.rstrip("/")
    options = [path] if path and not path.endswith("/") else []
    options += [f"{stem}.md", f"{stem}.mdx"]
    prefix = f"{stem}/" if stem else ""
    options += [f"{prefix}index.md", f"{prefix}index.mdx", f"{prefix}README.md"]
    return options


def _resolve_link(source: str, line: int, raw: str, pages: dict[str, Page], root: Path) -> Link:
    target = raw[1:-1] if raw.startswith("<") and raw.endswith(">") else raw
    if SCHEME_RE.match(target) or target.startswith("//"):
        return Link(source=source, line=line, target=target, status="external")

    path_part, _, anchor = target.partition("#")
    path_part = unquote(path_part.split("?", 1)[0])
    anchor = unquote(anchor) or None

    if not path_part:
        resolved: str | None = source
    else:
        root_relative = path_part.startswith("/")
        base = PurePosixPath("") if root_relative else PurePosixPath(source).parent
        joined = _normalize(base / path_part.lstrip("/"))
        if joined is None:
            # Leaves the indexed folder; it may still be a real file in the repo.
            outside = (root / PurePosixPath(source).parent / path_part).resolve()
            if outside.exists():
                return Link(source=source, line=line, target=target, status="unchecked", anchor=anchor,
                            note="outside the indexed folder")
            return Link(source=source, line=line, target=target, status="broken_page", anchor=anchor,
                        note="no file at this path")
        resolved = next((c for c in _candidates(joined) if c in pages), None)
        if resolved is None:
            on_disk = next((c for c in _candidates(joined) if c and (root / c).is_file()), None)
            if on_disk:
                return Link(source=source, line=line, target=target, status="unchecked", resolved_path=on_disk,
                            anchor=anchor, note="target exists but is not an indexed page")
            if root_relative:
                return Link(source=source, line=line, target=target, status="unchecked", anchor=anchor,
                            note="site route, not a file path; cannot be checked locally")
            return Link(source=source, line=line, target=target, status="broken_page", anchor=anchor,
                        note="no page at this path")

    if anchor and anchor not in {s.anchor for s in pages[resolved].sections}:
        return Link(source=source, line=line, target=target, status="broken_anchor", resolved_path=resolved,
                    anchor=anchor, note="no section with this anchor")
    return Link(source=source, line=line, target=target, status="ok", resolved_path=resolved, anchor=anchor)


# --- entry point -----------------------------------------------------------


def read_page(root: Path, rel: str) -> str | None:
    """Page text, or None if it is not valid UTF-8."""
    try:
        return (root / rel).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def build_index(
    root: str | Path,
    collection_name: str | None = None,
    collection: DocCollection | None = None,
) -> DocsIndex:
    """Index a docs folder. With `collection`, only pages its filter allows."""
    root = Path(root)
    if not root.is_dir():
        raise DocsIndexError(f"not a directory: {root}")

    pages: dict[str, Page] = {}
    raw_links: list[tuple[str, int, str]] = []
    for rel in discover_pages(root, collection):
        text = read_page(root, rel)
        if text is None:
            pages[rel] = Page(path=rel, title=PurePosixPath(rel).stem, warnings=["not valid UTF-8; skipped"])
            continue
        page, links = parse_page(rel, text)
        pages[rel] = page
        raw_links.extend((rel, line, target) for line, target in links)

    links = [_resolve_link(source, line, target, pages, root) for source, line, target in raw_links]

    backlinks: dict[str, set[str]] = defaultdict(set)
    for link in links:
        if link.status == "ok" and link.resolved_path and link.resolved_path != link.source:
            backlinks[link.resolved_path].add(link.source)

    return DocsIndex(
        collection=collection_name,
        pages=list(pages.values()),
        links=links,
        backlinks={target: sorted(sources) for target, sources in sorted(backlinks.items())},
        broken_links=[l for l in links if l.status in ("broken_page", "broken_anchor")],
    )
