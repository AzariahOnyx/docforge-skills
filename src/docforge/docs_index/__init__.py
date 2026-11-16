"""Docs index: pages, sections, links and keyword search for a local docs folder."""

from .build import DocsIndexError, build_index, parse_page, slugify
from .models import DocsIndex, Link, Page, SearchHit, Section
from .search import search

__all__ = [
    "DocsIndex",
    "DocsIndexError",
    "Link",
    "Page",
    "SearchHit",
    "Section",
    "build_index",
    "parse_page",
    "search",
    "slugify",
]
