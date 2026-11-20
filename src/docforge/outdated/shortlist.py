"""The shortlist: which published pages the verdict passes read. Free and deterministic.

- Must review: a page that contains an old UI string word for word, or one of the doc collection's
  must-review keywords. These pages always stay on the list and must get a verdict.
- Ranked: pages that match the change note's terms (feature names, UI labels) in the docs index search,
  best first, up to the cap.

Each page carries its reasons, the matching lines and the images in the matching sections (screenshots
that may need recapturing).
"""

from __future__ import annotations

from pathlib import Path
import re

from docforge.config import DocCollection

from .note import ChangeNote

IMAGE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")


def _word(text: str) -> re.Pattern:
    return re.compile(rf"(?<![\w-]){re.escape(text)}(?![\w-])")


def _section_of(page, line: int):
    return next((s for s in page.sections if s.start_line <= line <= s.end_line), None)


def build_shortlist(docs: Path, note: ChangeNote, *, collection: DocCollection | None = None,
                    must_review: list[str] = (), cap: int = 25) -> dict:
    from docforge.docs_index import build_index, search

    index = build_index(docs, collection=collection)
    pages: dict[str, dict] = {}

    def entry(page) -> dict:
        return pages.setdefault(page.path, {"path": page.path, "title": page.title, "must_review": False,
                                            "reasons": [], "matches": [], "score": 0, "images": []})

    olds = [(s, _word(s)) for s in note.old_strings]
    keywords = [(k, re.compile(re.escape(k), re.I)) for k in must_review]
    for page in index.pages:
        lines = (docs / page.path).read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines, start=1):
            hits = [s for s, pattern in olds if pattern.search(line)]
            hits_kw = [k for k, pattern in keywords if pattern.search(line)]
            if not hits and not hits_kw:
                continue
            item = entry(page)
            item["must_review"] = True
            for text in hits:
                reason = f"old wording \"{text}\""
                if reason not in item["reasons"]:
                    item["reasons"].append(reason)
            for text in hits_kw:
                reason = f"must-review keyword \"{text}\""
                if reason not in item["reasons"]:
                    item["reasons"].append(reason)
            item["matches"].append({"line": number, "text": line.strip()[:300]})
            item["score"] += 10
            section = _section_of(page, number)
            if section is not None:
                for image in IMAGE.findall("\n".join(lines[section.start_line - 1:section.end_line])):
                    if image not in item["images"]:
                        item["images"].append(image)
    by_path = {p.path: p for p in index.pages}
    for term in note.terms:
        for hit in search(docs, term, collection=collection, limit=10, match="all"):
            page = by_path.get(hit.path)
            if page is None:
                continue
            item = entry(page)
            reason = f"term \"{term}\""
            if reason not in item["reasons"]:
                item["reasons"].append(reason)
                item["score"] += max(1, hit.score)
            if len(item["matches"]) < 10 and all(m["line"] != hit.line for m in item["matches"]):
                item["matches"].append({"line": hit.line, "text": hit.snippet[:300]})
    must = sorted((p for p in pages.values() if p["must_review"]), key=lambda p: (-p["score"], p["path"]))
    rest = sorted((p for p in pages.values() if not p["must_review"]), key=lambda p: (-p["score"], p["path"]))
    kept = must + rest[: max(0, cap - len(must))]
    return {"pages": kept, "must_review": [p["path"] for p in must], "cap": cap,
            "dropped": len(pages) - len(kept), "searched_pages": len(index.pages),
            "old_strings": note.old_strings, "terms": note.terms}
