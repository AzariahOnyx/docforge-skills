"""Models for the docs index and search results."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

LinkStatus = Literal["ok", "broken_page", "broken_anchor", "external", "unchecked"]


class Section(BaseModel):
    heading: str
    level: int
    anchor: str
    start_line: int
    # Last line of the section, including its subsections.
    end_line: int
    # Words in the section's own text, excluding subsections.
    word_count: int = 0


class Page(BaseModel):
    path: str
    title: str
    front_matter: dict = Field(default_factory=dict)
    sections: list[Section] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class Link(BaseModel):
    source: str
    line: int
    target: str
    status: LinkStatus
    resolved_path: str | None = None
    anchor: str | None = None
    note: str | None = None


class DocsIndex(BaseModel):
    collection: str | None = None
    pages: list[Page]
    links: list[Link]
    backlinks: dict[str, list[str]]
    broken_links: list[Link]


class SearchHit(BaseModel):
    path: str
    title: str
    score: int
    # Best-matching section; None when the match is only in the title or the
    # text before the first heading.
    anchor: str | None = None
    heading: str | None = None
    line: int
    snippet: str
