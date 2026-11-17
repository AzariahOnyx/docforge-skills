"""Fetch one Confluence page as a Markdown source file (read-only)."""

from __future__ import annotations

import re

from docforge.config import ConfluenceSource

from . import provenance
from .adf import storage_to_markdown
from .atlassian import AtlassianClient, SourceFetchError, segment

PAGE_ID_RE = re.compile(r"^[1-9][0-9]{0,19}$")


def fetch_page(source: ConfluenceSource, page_id: str, *, client: AtlassianClient | None = None) -> tuple[str, dict]:
    """Return (markdown, provenance) for one page. Refuses pages outside space_keys."""
    if not PAGE_ID_RE.match(page_id):
        raise SourceFetchError(f"not a Confluence page ID: {page_id!r}")
    client = client or AtlassianClient(source)
    data = client.get_json(f"rest/api/content/{segment(page_id)}?expand=body.storage,version,space")
    if data.get("type") not in (None, "page", "blogpost"):
        raise SourceFetchError(f"content {page_id} is a {data.get('type')}, not a page")
    space = ((data.get("space") or {}).get("key")) or ""
    if source.space_keys and space not in source.space_keys:
        # Checked before anything is written; the content is discarded.
        raise SourceFetchError(f"page {page_id} is in space {space or 'unknown'}, which is not in space_keys")
    version = data.get("version") or {}
    storage = (((data.get("body") or {}).get("storage")) or {}).get("value", "")
    webui = ((data.get("_links") or {}).get("webui")) or ""
    meta = {
        "kind": "confluence", "id": page_id, "title": data.get("title") or page_id, "space": space,
        "url": client.url(webui) if webui.startswith("/") else client.url(f"pages/viewpage.action?pageId={page_id}"),
        "version": version.get("number", "unknown"), "updated": version.get("when"), "fetched_at": provenance.now(),
    }
    return provenance.render(meta, data.get("title") or f"Page {page_id}", storage_to_markdown(storage)), meta
