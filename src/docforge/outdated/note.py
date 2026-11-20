"""The change note: what a change altered, as the outdated content finder needs it.

From a code diff, for free: the old and new values of changed locale strings (JSON files), and quoted
strings on removed and added code lines (code-like strings dropped). From a changed spec: its removed and
added lines. Terms (feature names, bold UI labels) widen the search. Everything here is data from the
change, never instructions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import re
import subprocess

QUOTED = re.compile(r"""(?<![\w$])(["'`])((?:(?!\1).){3,120})\1""")
CODE_LIKE = re.compile(r"[{}<>=;()\[\]\\_$]|^https?:|^\s|\s$|\.\w{2,4}$|^[./]")
TITLE_WORD = re.compile(r"^[A-Z][a-z]{2,}$")
BOLD = re.compile(r"\*\*([^*\n]{2,80})\*\*")


@dataclass
class StringChange:
    old: str | None
    new: str | None
    where: str  # file (and key, for locale strings)


@dataclass
class ChangeNote:
    source: str  # what the note was made from
    strings: list[StringChange] = field(default_factory=list)
    spec_changes: list[dict] = field(default_factory=list)  # {path, removed: [...], added: [...]}
    terms: list[str] = field(default_factory=list)
    behaviour: list[dict] = field(default_factory=list)  # {old, new} written by a person, session or model

    @property
    def old_strings(self) -> list[str]:
        return list(dict.fromkeys(s.old for s in self.strings if s.old))

    def to_dict(self) -> dict:
        return {**asdict(self), "old_strings": self.old_strings}

    @classmethod
    def from_dict(cls, data: dict) -> "ChangeNote":
        return cls(data.get("source", ""), [StringChange(**s) for s in data.get("strings", [])],
                   data.get("spec_changes", []), data.get("terms", []), data.get("behaviour", []))


def _git(checkout: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(checkout), *args], capture_output=True, text=True, timeout=60, check=False)
    if result.returncode != 0:
        raise ValueError(f"git {args[0]} failed: {(result.stderr or result.stdout).strip()[:200]}")
    return result.stdout


def _flatten(data, prefix: str = "") -> dict[str, str]:
    out = {}
    if isinstance(data, dict):
        for key, value in data.items():
            out.update(_flatten(value, f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(data, str):
        out[prefix] = data
    return out


def _is_text(value: str) -> bool:
    """A user-facing string, not an identifier, path or code fragment."""
    if len(value) < 3 or CODE_LIKE.search(value) or not any(c.isalpha() for c in value):
        return False
    if " " not in value:
        return bool(TITLE_WORD.match(value))  # "Schedule", not "scheduleBtn", "SCHEDULE" or "schedule"
    return True


def _locale_changes(old_text: str | None, new_text: str | None, path: str) -> list[StringChange]:
    try:
        old = _flatten(json.loads(old_text)) if old_text else {}
        new = _flatten(json.loads(new_text)) if new_text else {}
    except ValueError:
        return []
    changes = []
    for key in sorted(set(old) | set(new)):
        if old.get(key) != new.get(key):
            changes.append(StringChange(old.get(key), new.get(key), f"{path}:{key}"))
    return changes


def _show(checkout: Path, commit: str, path: str) -> str | None:
    try:
        return _git(checkout, "show", f"{commit}:{path}")
    except ValueError:
        return None


def _quoted(lines: list[str]) -> list[str]:
    found = []
    for line in lines:
        for _, text in QUOTED.findall(line):
            if _is_text(text):
                found.append(text.strip())
    return list(dict.fromkeys(found))


def note_from_code(checkout: Path, base: str, head: str, *, spec_paths=(), locale_patterns=(), terms=()) -> ChangeNote:
    """The change note for base..head in a local checkout."""
    from docforge.triage.rules import DEFAULT_PATHS, matches

    locales = (*DEFAULT_PATHS["ui_text"], *locale_patterns)
    note = ChangeNote(f"code {base[:12]}..{head[:12]}", terms=list(dict.fromkeys(terms)))
    names = [p for p in _git(checkout, "diff", "--name-only", base, head).splitlines() if p]
    for path in names:
        if matches(path, locales) and path.endswith(".json"):
            note.strings += _locale_changes(_show(checkout, base, path), _show(checkout, head, path), path)
            continue
        diff = _git(checkout, "diff", "--unified=0", "--no-color", base, head, "--", path)
        removed = [l[1:] for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")]
        added = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
        if spec_paths and matches(path, spec_paths):
            note.spec_changes.append({"path": path, "removed": [l for l in removed if l.strip()][:200],
                                      "added": [l for l in added if l.strip()][:200]})
            note.terms += [t for t in BOLD.findall("\n".join(removed + added)) if t not in note.terms]
            continue
        old_q, new_q = _quoted(removed), _quoted(added)
        for text in old_q:
            if text not in new_q:
                note.strings.append(StringChange(text, None, path))
        for text in new_q:
            if text not in old_q:
                note.strings.append(StringChange(None, text, path))
    return note


def note_from_sources(texts: list[str], *, terms=()) -> ChangeNote:
    """A change note for a run without code (a PRD or ticket): the bold UI labels its sources name."""
    found = [t for text in texts for t in BOLD.findall(text)]
    return ChangeNote("sources", terms=list(dict.fromkeys([*terms, *found]))[:60])
