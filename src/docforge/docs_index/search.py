"""Keyword search over a docs folder.

Every query word must match (case-insensitive, whole words). Scoring per word:
title 3, heading 2, section text 1, plus 2 when the whole query appears as a
phrase in the title, heading or text. A page's score is its title score plus
its best section's score. Reads the folder fresh; never uses the network.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Literal

from docforge.config import DocCollection

from .build import (
    WORD_RE,
    DocsIndexError,
    discover_pages,
    own_text_ranges,
    parse_page,
    read_page,
    split_front_matter,
    visible_text,
)
from .models import SearchHit

SearchField = Literal["all", "title", "heading"]
SNIPPET_CHARS = 160
TITLE, HEADING, BODY, PHRASE = 3, 2, 1, 2


def tokens(text: str) -> list[str]:
    return [t.casefold() for t in WORD_RE.findall(text)]


def _phrase(terms: list[str], words: list[str]) -> bool:
    n = len(terms)
    return n > 1 and any(words[i : i + n] == terms for i in range(len(words) - n + 1))


def _snippet(lines: list[str], first: int, last: int, terms: set[str], fallback: str) -> tuple[int, str]:
    for number in range(first, last + 1):
        line = lines[number - 1]
        if terms & set(tokens(visible_text(line))):
            text = re.sub(r"^\s*(?:[-*+]|\d+\.|>|\|)\s*", "", line).strip()
            text = " ".join(text.split())
            if len(text) > SNIPPET_CHARS:
                text = text[: SNIPPET_CHARS - 3].rstrip() + "..."
            return number, text
    return first, fallback


def search(
    root: str | Path,
    query: str,
    *,
    field: SearchField = "all",
    limit: int = 10,
    collection: DocCollection | None = None,
) -> list[SearchHit]:
    root = Path(root)
    if not root.is_dir():
        raise DocsIndexError(f"not a directory: {root}")
    terms = list(dict.fromkeys(tokens(query)))
    if not terms:
        return []
    term_set = set(terms)

    hits: list[SearchHit] = []
    for rel in discover_pages(root, collection):
        text = read_page(root, rel)
        if text is None:
            continue
        page, _ = parse_page(rel, text)
        lines = text.splitlines()
        _, body_start = split_front_matter(lines, [])
        title_words = tokens(page.title)
        title_set = set(title_words)

        if field == "title":
            if not term_set <= title_set:
                continue
            score = TITLE * len(terms) + (PHRASE if _phrase(terms, title_words) else 0)
            hits.append(SearchHit(path=rel, title=page.title, score=score, line=1, snippet=page.title))
            continue

        page_words: set[str] = set(title_set)
        best: tuple[int, SearchHit] | None = None
        for section, first, last in own_text_ranges(page, len(lines), body_start):
            heading_words = tokens(section.heading) if section else []
            body_words = [w for n in range(first, last + 1) for w in tokens(visible_text(lines[n - 1]))]
            heading_set, body_set = set(heading_words), set(body_words)
            page_words |= heading_set | body_set
            if field == "heading" and not term_set <= heading_set:
                continue
            score = HEADING * len(term_set & heading_set) + BODY * len(term_set & body_set)
            if _phrase(terms, heading_words) or _phrase(terms, body_words):
                score += PHRASE
            if score == 0:
                continue
            if field == "heading":
                line, snippet = (section.start_line, section.heading)
            else:
                line, snippet = _snippet(lines, first, last, term_set, section.heading if section else page.title)
                if section and term_set & heading_set and not term_set & body_set:
                    line, snippet = section.start_line, section.heading
            hit = SearchHit(
                path=rel, title=page.title, score=score, line=line, snippet=snippet,
                anchor=section.anchor if section else None, heading=section.heading if section else None,
            )
            if best is None or score > best[0]:
                best = (score, hit)

        if field == "all" and not term_set <= page_words:
            continue
        title_score = TITLE * len(term_set & title_set) + (PHRASE if _phrase(terms, title_words) else 0)
        if best is None:
            if title_score == 0:
                continue
            hits.append(SearchHit(path=rel, title=page.title, score=title_score, line=1, snippet=page.title))
            continue
        hit = best[1]
        hit.score += title_score if field == "all" else 0
        hits.append(hit)

    hits.sort(key=lambda h: (-h.score, h.path))
    return hits[:limit] if limit > 0 else hits
