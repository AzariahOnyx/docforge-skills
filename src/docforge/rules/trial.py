"""Try a rule against past runs before it can go live.

avoid: Vale runs the rule on its own over every past run's pages and the
pages DocForge committed (publish/pages/), and every hit is recorded.

guidance: cannot be checked mechanically. The report lists the pages it would
apply to and quotes the feedback it came from, for a person to judge.
"""

from __future__ import annotations

import json
from pathlib import Path

from docforge.lint.vale import LintError, find_vale, run_vale

from .live import single_rule_config
from .model import Hit, RuleError, TrialReport, load_rule, now, save_rule


def find_runs(paths: list[Path]) -> list[Path]:
    runs: list[Path] = []
    for path in paths:
        if (path / "run.json").is_file():
            runs.append(path)
        elif path.is_dir():
            runs += sorted(p for p in path.iterdir() if (p / "run.json").is_file())
    return list(dict.fromkeys(r.resolve() for r in runs))


def run_pages(run: Path) -> dict[str, Path]:
    """Run-relative page paths: deliverables and committed copies under publish/pages/."""
    pages: dict[str, Path] = {}
    try:
        manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return pages
    for rel in manifest.get("deliverables", []):
        if isinstance(rel, str) and (run / rel).is_file():
            pages[rel] = run / rel
    committed = run / "publish" / "pages"
    if committed.is_dir():
        for path in sorted(committed.rglob("*.md")):
            pages[str(path.relative_to(run))] = path
    return pages


def _feedback_quotes(rule, runs: list[Path]) -> list[str]:
    wanted = {(o.run, o.feedback_id) for o in rule.origins}
    quotes = []
    for run in runs:
        path = run / "review" / "feedback.jsonl"
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            if (item.get("run"), item.get("feedback_id")) in wanted:
                quotes.append(f"{item['run']} {item['feedback_id']} ({item['action']}, {item['reviewer']}): "
                              f"{item.get('comment') or item.get('reason')}")
    return quotes


def try_rule(folder: Path, rule_id: str, paths: list[Path]) -> TrialReport:
    rule = load_rule(folder, rule_id)
    if rule.status in ("rejected", "retired"):
        raise RuleError(f"{rule_id} is {rule.status}")
    runs = find_runs(paths)
    if not runs:
        raise RuleError("no past runs found (folders with run.json)")
    labels = {}
    files: dict[str, Path] = {}
    for run in runs:
        for page, path in run_pages(run).items():
            if rule.applies_to and not any(a in page for a in rule.applies_to):
                continue
            key = f"{run.name}/{page}"
            files[key] = path
            labels[key] = (run.name, page)

    hits: list[Hit] = []
    if rule.kind == "avoid":
        binary = find_vale()
        if binary is None:
            raise RuleError("Vale is needed to test an avoid rule; install it or set DOCFORGE_VALE")
        try:
            with single_rule_config(rule) as config:
                alerts = run_vale(files, config, binary)
        except LintError as exc:
            raise RuleError(f"Vale could not run the rule: {exc}") from None
        for alert in alerts:
            run_name, page = labels[alert.page]
            text = files[alert.page].read_text(encoding="utf-8").splitlines()[alert.line - 1].strip()
            hits.append(Hit(run=run_name, page=page, line=alert.line, match=alert.match, text=text[:200]))
        note = (f"{len(hits)} hit(s) in {len(files)} page(s). Check each hit: a rule that flags correct text "
                "should be narrowed or rejected.")
    else:
        note = ("Guidance cannot be checked automatically. It would apply to the pages listed by count; "
                "a person judges whether it is right and general enough.")
    report = TrialReport(at=now(), content_hash=rule.content_hash(), runs=[r.name for r in runs],
                        pages_checked=len(files), hits=hits, feedback=_feedback_quotes(rule, runs), note=note)
    rule.test = report
    if rule.status == "proposed" or rule.effective_status().startswith("proposed"):
        rule.status = "tested"
        rule.approval = None
    save_rule(folder, rule)
    return report
