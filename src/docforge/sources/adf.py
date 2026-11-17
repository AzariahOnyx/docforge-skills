"""Convert Atlassian rich text to Markdown.

- `adf_to_markdown`: Atlassian Document Format (Jira Cloud descriptions and
  rich-text fields), a JSON tree.
- `storage_to_markdown`: Confluence storage format, an XHTML dialect.

Content is untrusted data. Raw HTML comment openers are neutralised so fetched
text can never pose as a DocForge marker or provenance header. Images and
attachments are not downloaded; a placeholder says what was left out.
"""

from __future__ import annotations

from html.parser import HTMLParser
import re


def neutralise(text: str) -> str:
    return text.replace("<!--", "&lt;!--").replace("-->", "--&gt;")


# --- ADF ---------------------------------------------------------------------


def _text(node: dict) -> str:
    text = neutralise(node.get("text", ""))
    for mark in node.get("marks", []) or []:
        kind = mark.get("type")
        if kind == "code":
            text = f"`{text}`"
        elif kind == "strong":
            text = f"**{text}**"
        elif kind == "em":
            text = f"*{text}*"
        elif kind == "strike":
            text = f"~~{text}~~"
        elif kind == "link":
            href = (mark.get("attrs") or {}).get("href", "")
            if href.startswith(("https://", "http://", "mailto:")):
                text = f"[{text}]({href})"
    return text


def _inline(nodes: list) -> str:
    out = []
    for node in nodes or []:
        kind = node.get("type")
        attrs = node.get("attrs") or {}
        if kind == "text":
            out.append(_text(node))
        elif kind == "hardBreak":
            out.append("  \n")
        elif kind == "mention":
            out.append(neutralise(attrs.get("text") or "@someone"))
        elif kind == "emoji":
            out.append(attrs.get("text") or attrs.get("shortName") or "")
        elif kind in ("inlineCard", "blockCard"):
            url = attrs.get("url", "")
            out.append(f"<{url}>" if url.startswith(("https://", "http://")) else "[link]")
        elif kind == "status":
            out.append(f"[{neutralise(attrs.get('text', ''))}]")
        elif kind == "date":
            out.append(str(attrs.get("timestamp", "")))
        else:
            out.append(_inline(node.get("content", [])))
    return "".join(out)


def _cell(node: dict) -> str:
    return " ".join(_blocks(node.get("content", []), 0)).replace("\n", " ").replace("|", "\\|").strip()


def _list(node: dict, depth: int, ordered: bool) -> list[str]:
    lines = []
    for i, item in enumerate(node.get("content", []), start=1):
        bullet = f"{i}." if ordered else "-"
        children = _blocks(item.get("content", []), depth + 1)
        first, rest = (children[0], children[1:]) if children else ("", [])
        lines.append("  " * depth + f"{bullet} {first.strip()}")
        lines += [c for c in rest if c.strip()]
    return lines


def _blocks(nodes: list, depth: int) -> list[str]:
    blocks: list[str] = []
    for node in nodes or []:
        kind = node.get("type")
        attrs = node.get("attrs") or {}
        if kind == "paragraph":
            blocks.append(_inline(node.get("content", [])))
        elif kind == "heading":
            level = min(max(int(attrs.get("level", 2)), 1), 6)
            blocks.append("#" * level + " " + _inline(node.get("content", [])))
        elif kind in ("bulletList", "orderedList"):
            blocks.append("\n".join(_list(node, depth, kind == "orderedList")))
        elif kind == "codeBlock":
            code = "".join(n.get("text", "") for n in node.get("content", []))
            blocks.append(f"```{attrs.get('language') or ''}\n{neutralise(code)}\n```")
        elif kind == "blockquote":
            inner = "\n\n".join(_blocks(node.get("content", []), depth))
            blocks.append("\n".join("> " + line for line in inner.splitlines()))
        elif kind == "panel":
            inner = "\n\n".join(_blocks(node.get("content", []), depth))
            label = (attrs.get("panelType") or "info").capitalize()
            blocks.append("\n".join(f"> **{label}:** " * (i == 0) + ("> " if i else "") + line
                                    for i, line in enumerate(inner.splitlines())))
        elif kind == "rule":
            blocks.append("---")
        elif kind == "table":
            rows = node.get("content", [])
            if rows:
                cells = [[_cell(c) for c in row.get("content", [])] for row in rows]
                width = max(len(r) for r in cells)
                cells = [r + [""] * (width - len(r)) for r in cells]
                lines = ["| " + " | ".join(cells[0]) + " |", "|" + " --- |" * width]
                lines += ["| " + " | ".join(r) + " |" for r in cells[1:]]
                blocks.append("\n".join(lines))
        elif kind in ("mediaSingle", "mediaGroup", "media"):
            blocks.append("[Image or attachment not fetched]")
        elif kind in ("expand", "nestedExpand", "layoutSection", "layoutColumn", "doc"):
            if kind in ("expand", "nestedExpand") and attrs.get("title"):
                blocks.append(f"**{neutralise(attrs['title'])}**")
            blocks += _blocks(node.get("content", []), depth)
        elif node.get("content"):
            blocks += _blocks(node["content"], depth)
        elif kind:
            blocks.append(f"[Unsupported content: {kind}]")
    return blocks


def adf_to_markdown(doc) -> str:
    """Markdown for an ADF document. A plain string (Jira Server) is returned as is."""
    if doc is None:
        return ""
    if isinstance(doc, str):
        return neutralise(doc).strip()
    if not isinstance(doc, dict):
        return ""
    blocks = _blocks(doc.get("content", []) if doc.get("type") == "doc" else [doc], 0)
    return "\n\n".join(b.rstrip() for b in blocks if b.strip()).strip()


# --- Confluence storage format ----------------------------------------------

_BLOCK = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "table", "tr", "blockquote", "pre", "hr"}
_SKIP = {"script", "style", "ac:parameter"}


class _Storage(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self.buf: list[str] = []
        self.lists: list[list] = []  # [ordered, counter, item already has text]
        self.skip = 0
        self.pre = 0
        self.links: list[str] = []
        self.table: list[list[str]] | None = None
        self.cell: list[str] | None = None
        self.header_row = False
        self.quote = 0
        self.macro: list[str] = []

    # helpers
    def _flush(self, prefix: str = ""):
        text = re.sub(r"[ \t]+", " ", "".join(self.buf)).strip() if not self.pre else "".join(self.buf)
        self.buf = []
        if text:
            if self.quote:
                text = "\n".join("> " + line for line in text.splitlines())
            self.blocks.append(prefix + text)
            if self.lists and prefix and prefix.lstrip() and prefix.lstrip()[0] in "-0123456789":
                self.lists[-1][2] = True

    def _out(self, text: str):
        (self.cell if self.cell is not None else self.buf).append(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in _SKIP:
            self.skip += 1
            return
        if self.skip:
            return
        if tag == "ac:structured-macro":
            name = attrs.get("ac:name", "")
            self.macro.append(name)
            if name not in ("code", "noformat", "info", "note", "warning", "tip", "panel", "expand"):
                self._flush()
                self.blocks.append(f"[Confluence macro not converted: {neutralise(name) or 'unknown'}]")
                self.skip += 1
            return
        if tag == "ac:plain-text-body" and self.macro and self.macro[-1] in ("code", "noformat"):
            self._flush()
            self.pre += 1
            return
        if tag in ("ac:image", "ac:link", "ri:attachment"):
            if tag == "ac:image":
                self._out("[Image not fetched]")
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "blockquote", "pre", "hr"):
            if self.cell is None:
                self._flush()
            if tag == "blockquote":
                self.quote += 1
            elif tag == "pre":
                self.pre += 1
            elif tag == "hr":
                self.blocks.append("---")
        elif tag in ("ul", "ol"):
            self._flush(self._list_prefix())
            self.lists.append([tag == "ol", 0, False])
        elif tag == "li":
            self._flush(self._list_prefix())
            if self.lists:
                self.lists[-1][1] += 1
                self.lists[-1][2] = False
        elif tag == "br":
            self._out("  \n")
        elif tag in ("strong", "b"):
            self._out("**")
        elif tag in ("em", "i"):
            self._out("*")
        elif tag == "code" and not self.pre:
            self._out("`")
        elif tag == "a":
            href = attrs.get("href") or ""
            self.links.append(href if href.startswith(("https://", "http://", "mailto:")) else "")
            if self.links[-1]:
                self._out("[")
        elif tag == "table":
            self._flush()
            self.table = []
        elif tag == "tr" and self.table is not None:
            self.table.append([])
        elif tag in ("td", "th") and self.table is not None:
            self.cell = []
            if tag == "th" and len(self.table) == 1:
                self.header_row = True

    def _list_prefix(self) -> str:
        if not self.lists:
            return ""
        ordered, count, used = self.lists[-1]
        indent = "  " * (len(self.lists) - 1)
        if used:
            return indent + "  "
        return indent + (f"{count}. " if ordered else "- ")

    def handle_endtag(self, tag):
        if tag in _SKIP:
            self.skip = max(0, self.skip - 1)
            return
        if tag == "ac:structured-macro":
            name = self.macro.pop() if self.macro else ""
            if name not in ("code", "noformat", "info", "note", "warning", "tip", "panel", "expand"):
                self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag == "ac:plain-text-body" and self.pre and self.macro and self.macro[-1] in ("code", "noformat"):
            code = "".join(self.buf).strip("\n")
            self.buf = []
            self.blocks.append(f"```\n{neutralise(code)}\n```")
            self.pre -= 1
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if self.cell is None:
                self._flush("#" * int(tag[1]) + " ")
        elif tag in ("p", "div"):
            if self.cell is None:
                self._flush(self._list_prefix() if self.lists else "")
        elif tag == "blockquote":
            self._flush()
            self.quote = max(0, self.quote - 1)
        elif tag == "pre":
            code = "".join(self.buf).strip("\n")
            self.buf = []
            self.blocks.append(f"```\n{neutralise(code)}\n```")
            self.pre = max(0, self.pre - 1)
        elif tag == "li":
            self._flush(self._list_prefix())
        elif tag in ("ul", "ol"):
            self._flush(self._list_prefix())
            if self.lists:
                self.lists.pop()
        elif tag in ("strong", "b"):
            self._out("**")
        elif tag in ("em", "i"):
            self._out("*")
        elif tag == "code" and not self.pre:
            self._out("`")
        elif tag == "a":
            href = self.links.pop() if self.links else ""
            if href:
                self._out(f"]({href})")
        elif tag in ("td", "th") and self.table is not None and self.cell is not None:
            text = re.sub(r"\s+", " ", "".join(self.cell)).strip().replace("|", "\\|")
            self.table[-1].append(text)
            self.cell = None
        elif tag == "table" and self.table is not None:
            rows = [r for r in self.table if r]
            if rows:
                width = max(len(r) for r in rows)
                rows = [r + [""] * (width - len(r)) for r in rows]
                head = rows[0] if self.header_row else [""] * width
                body = rows[1:] if self.header_row else rows
                lines = ["| " + " | ".join(head) + " |", "|" + " --- |" * width]
                lines += ["| " + " | ".join(r) + " |" for r in body]
                self.blocks.append("\n".join(lines))
            self.table, self.header_row = None, False

    def handle_data(self, data):
        if self.skip:
            return
        self._out(data if self.pre else neutralise(data))

    def unknown_decl(self, data):
        # Confluence wraps code macro bodies in CDATA.
        if data.startswith("CDATA["):
            self.handle_data(data[len("CDATA["):])

    def close(self):
        super().close()
        self._flush()


def storage_to_markdown(html: str) -> str:
    parser = _Storage()
    parser.feed(html or "")
    parser.close()
    return "\n\n".join(b.rstrip() for b in parser.blocks if b.strip()).strip()
