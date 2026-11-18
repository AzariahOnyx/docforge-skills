"""Text an automatic edit must never touch, and the claim-gate safety net.

Shared by Vale fixes (`docforge lint --fix`) and clean-up steps (`docforge cleanup`).
Protected: front matter, fenced code, HTML comments (evidence markers), inline
code, link targets and HTML tags.
"""

from __future__ import annotations

import json
from pathlib import Path
import re

from docforge.docs_index.build import split_front_matter

PROTECTED = re.compile(r"<!--.*?-->|`+[^`]*`+|\]\([^)]*\)|<[^>\n]+>")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")


def protected_spans(line: str) -> list[tuple[int, int]]:
    """0-based [start, end) ranges in one line that an edit must not touch."""
    return [(m.start(), m.end()) for m in PROTECTED.finditer(line)]


def mask(line: str) -> str:
    """The line with protected spans blanked out (same length), for matching prose only."""
    chars = list(line)
    for start, end in protected_spans(line):
        chars[start:end] = " " * (end - start)
    return "".join(chars)


def prose_lines(lines: list[str]) -> list[int]:
    """0-based indexes of lines outside front matter and fenced code blocks."""
    _, start = split_front_matter(lines, [])
    keep, fence = [], None
    for index in range(start, len(lines)):
        match = FENCE.match(lines[index])
        if fence is not None:
            if match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence):
                fence = None
            continue
        if match:
            fence = match.group(1)
            continue
        keep.append(index)
    return keep


def sub_prose(line: str, pattern: re.Pattern, repl) -> tuple[str, int]:
    """re.subn on the unprotected parts of a line only."""
    spans = protected_spans(line)
    out, count, cursor = [], 0, 0
    for start, end in spans + [(len(line), len(line))]:
        new, n = pattern.subn(repl, line[cursor:start])
        out.append(new)
        out.append(line[start:end])
        count += n
        cursor = end
    return "".join(out), count


def is_gated(run: Path) -> bool:
    """Pages that must keep passing the claim gate: meant for publishing, already proposed, or a flow run."""
    if (run / "publish" / "pr.json").is_file():
        return True
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    return bool(manifest.get("publish")) or manifest.get("flow_steps") == "required"


def gate_or_restore(run: Path, originals: dict[str, str], error: type[Exception], what: str) -> None:
    """Re-run the claim gate on a gated run; restore every page and raise `error` if it fails."""
    if not is_gated(run):
        return
    from docforge.publish import GateError, gate_run

    def restore(reason: str) -> None:
        for page, text in originals.items():
            (run / page).write_text(text, encoding="utf-8")
        raise error(f"the claim gate failed after {what} ({reason}); every page was restored")

    try:
        result = gate_run(run, write=False)
    except (GateError, OSError, ValueError) as exc:
        restore(str(exc))
    if not result.passed:
        first = result.errors[0]
        restore(f"{first.path}:{first.line} {first.message}")
