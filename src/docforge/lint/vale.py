"""Run Vale on a run's pages and keep the alerts on changed prose.

"Changed prose" means: every line of a page that was never proposed, or, once
a suggestion exists, the lines that differ from the version DocForge last
committed (publish/pages/<docs path>). Vale itself runs read-only.
"""

from __future__ import annotations

import difflib
import json
import os
from pathlib import Path
import shutil
import subprocess

from pydantic import BaseModel, Field

TOOLS_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = TOOLS_ROOT / ".vale.ini"
VALE_TIMEOUT_SECONDS = 120


class LintError(Exception):
    """Raised when Vale cannot run or its output cannot be read."""


class Alert(BaseModel):
    page: str  # run-relative path
    line: int
    start: int  # 1-based column, inclusive
    end: int  # 1-based column, inclusive
    check: str
    severity: str  # error, warning, suggestion
    message: str
    match: str
    replacement: str | None = None  # set when the rule offers exactly one replacement


class LintResult(BaseModel):
    vale_version: str
    config: str
    changed_only: bool
    pages: list[str]
    alerts: list[Alert] = Field(default_factory=list)
    unchanged_alerts: int = 0  # alerts on lines that did not change, not reported

    @property
    def counts(self) -> dict[str, int]:
        counts = {"error": 0, "warning": 0, "suggestion": 0}
        for alert in self.alerts:
            counts[alert.severity] = counts.get(alert.severity, 0) + 1
        return counts


def find_vale() -> str | None:
    override = os.environ.get("DOCFORGE_VALE")
    if override:
        return override if Path(override).is_file() else None
    found = shutil.which("vale")
    if found:
        return found
    local = Path.home() / ".local" / "bin" / "vale"
    return str(local) if local.is_file() else None


def _vale(binary: str, *args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run([binary, *args], capture_output=True, text=True, timeout=VALE_TIMEOUT_SECONDS,
                              check=False, cwd=str(TOOLS_ROOT))
    except (OSError, subprocess.SubprocessError) as exc:
        raise LintError(f"could not run Vale: {exc}") from None


def run_vale(files: dict[str, Path], config: Path, binary: str) -> list[Alert]:
    """Lint {run-relative name: file} and return every alert."""
    if not files:
        return []
    if not config.is_file():
        raise LintError(f"Vale config not found: {config}")
    by_path = {str(path.resolve()): name for name, path in files.items()}
    result = _vale(binary, "--config", str(config), "--output=JSON", "--no-exit", *by_path)
    try:
        data = json.loads(result.stdout or "{}")
    except ValueError:
        raise LintError(f"Vale did not return JSON: {(result.stderr or result.stdout).strip()[:300]}") from None
    if isinstance(data, dict) and "Code" in data and "Text" in data:
        raise LintError(f"Vale failed: {data['Text']}")
    alerts = []
    for path, items in data.items():
        name = by_path.get(str(Path(path).resolve()), path)
        for item in items:
            action = item.get("Action") or {}
            params = action.get("Params") or []
            replacement = params[0] if action.get("Name") == "replace" and len(params) == 1 else None
            span = item.get("Span") or [0, 0]
            alerts.append(Alert(page=name, line=item["Line"], start=span[0], end=span[1], check=item["Check"],
                                severity=item["Severity"], message=item["Message"], match=item.get("Match", ""),
                                replacement=replacement))
    return sorted(alerts, key=lambda a: (a.page, a.line, a.start))


def vale_version(binary: str) -> str:
    out = _vale(binary, "--version").stdout.strip()
    return out.rsplit(" ", 1)[-1] if out else "unknown"


def changed_lines(new_text: str, old_text: str | None) -> set[int] | None:
    """1-based lines of new_text that differ from old_text; None means every line."""
    if old_text is None:
        return None
    lines: set[int] = set()
    matcher = difflib.SequenceMatcher(a=old_text.splitlines(), b=new_text.splitlines(), autojunk=False)
    for tag, _, _, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "insert"):
            lines.update(range(j1 + 1, j2 + 1))
    return lines


def lint_run(run: Path, *, changed_only: bool = True, config: Path | None = None,
             write: bool = True) -> LintResult:
    """Lint the run's deliverables with Vale; writes qa/vale.json unless write is False."""
    binary = find_vale()
    if binary is None:
        raise LintError("Vale is not installed. Install it (https://vale.sh) or set DOCFORGE_VALE to its path.")
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    pages = {d: run / d for d in manifest.get("deliverables", []) if (run / d).is_file()}
    learned_used = False
    extras_label = ""
    if config is None:
        from docforge.rules import RuleError, lint_config, live_rules, rules_dir

        extra_styles = []
        pack = manifest.get("pack")
        if pack:
            from docforge.packs import PackError
            from docforge.packs.load import run_vale_styles

            try:
                extra_styles = run_vale_styles(run, pack)
            except (PackError, ValueError) as exc:
                raise LintError(f"pack styles could not be used: {exc}") from None
            if extra_styles:
                extras_label = f" + pack {pack['name']} styles ({', '.join(n for n, _ in extra_styles)})"
        try:
            learned_used = any(r.kind == "avoid" for r in live_rules(rules_dir()))
            with lint_config(rules_dir(), extra_styles) as built:
                alerts = run_vale(pages, built or DEFAULT_CONFIG, binary)
        except RuleError as exc:
            raise LintError(f"learned rules could not be loaded: {exc}") from None
        config = DEFAULT_CONFIG
    else:
        alerts = run_vale(pages, config, binary)

    # Page -> lines changed since DocForge last committed it (pages never proposed are absent: all lines count).
    changed: dict[str, set[int]] = {}
    pr = run / "publish" / "pr.json"
    if changed_only and pr.is_file():
        from docforge.publish.plan import rewrite_links

        plan = json.loads(pr.read_text(encoding="utf-8"))
        placed = {p["src"]: p["dest"] for p in plan.get("placements", [])}
        for src, dest in placed.items():
            committed = run / "publish" / "pages" / dest
            if committed.is_file() and src in pages:
                # Compare like with like: the committed copy has its links rewritten (line count unchanged).
                current = rewrite_links(pages[src].read_text(encoding="utf-8"), src, dest, placed)
                changed[src] = changed_lines(current, committed.read_text(encoding="utf-8")) or set()

    kept, skipped = [], 0
    for alert in alerts:
        if alert.page in changed and alert.line not in changed[alert.page]:
            skipped += 1
            continue
        kept.append(alert)
    label = os.path.relpath(config, TOOLS_ROOT) if config.resolve().is_relative_to(TOOLS_ROOT) else config.name
    result = LintResult(vale_version=vale_version(binary), config=label + extras_label + (" + live learned rules" if learned_used else ""),
                        changed_only=changed_only, pages=sorted(pages), alerts=kept, unchanged_alerts=skipped)
    if write:
        (run / "qa").mkdir(exist_ok=True)
        (run / "qa" / "vale.json").write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return result
