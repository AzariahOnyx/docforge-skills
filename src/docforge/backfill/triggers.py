"""Replay fetched PRs through the trigger engine and score the "docs needed?" decision.

The answer key is labels.json, filled in by a person: for each PR, whether it
needed documentation. DocForge never labels its own test set. PRs without a
label are reported as unscored.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from docforge.agent import decide
from docforge.config import DocForgeConfig
from docforge.sources import DiffError, EventError, parse_event, read_diff_file

from .fetch import BackfillError

LABELS = "labels.json"


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_labels_template(folder: Path) -> Path:
    path = folder / LABELS
    if path.exists():
        raise BackfillError(f"{path} already exists; it may hold someone's labels")
    try:
        prs = json.loads((folder / "fetch.json").read_text(encoding="utf-8"))["prs"]
    except (OSError, ValueError, KeyError) as exc:
        raise BackfillError(f"not a fetched evaluation folder: {exc}") from None
    rows = [{"number": pr["number"], "title": pr["title"], "docs_needed": None, "labelled_by": None, "note": ""}
            for pr in prs]
    path.write_text(json.dumps({"instructions": "Set docs_needed to \"yes\" or \"no\" for each PR and labelled_by "
                                                "to your name. Leave null to skip a PR.", "labels": rows}, indent=2)
                    + "\n", encoding="utf-8")
    return path


def load_labels(path: Path) -> dict[int, str]:
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))["labels"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise BackfillError(f"cannot read labels {path}: {exc}") from None
    labels: dict[int, str] = {}
    for row in rows:
        value = row.get("docs_needed")
        if value is None:
            continue
        if value not in ("yes", "no"):
            raise BackfillError(f"PR {row.get('number')}: docs_needed must be \"yes\", \"no\" or null")
        if not (row.get("labelled_by") or "").strip():
            raise BackfillError(f"PR {row.get('number')}: labelled_by is required for a label")
        if row["number"] in labels:
            raise BackfillError(f"PR {row['number']} is labelled twice")
        labels[row["number"]] = value
    return labels


GENERATOR_MARKERS = ("claude", "docforge session", "claude-code-session")


def labellers(path: Path) -> list[str]:
    rows = json.loads(path.read_text(encoding="utf-8"))["labels"]
    return sorted({r["labelled_by"].strip() for r in rows if r.get("docs_needed") is not None})


def replay(folder: Path, config: DocForgeConfig, labels_path: Path | None = None) -> dict:
    """Decide every fetched PR again and compare with the labels. Writes replay-<time>.json and .md."""
    events = sorted((folder / "events").glob("*.json"), key=lambda p: int(p.stem)) if (folder / "events").is_dir() else []
    if not events:
        raise BackfillError(f"no fetched events in {folder}")
    labels = load_labels(labels_path) if labels_path else {}
    by = labellers(labels_path) if labels_path else []
    independent = bool(by) and not any(m in name.casefold() for name in by for m in GENERATOR_MARKERS)
    rows = []
    counts = {"true_positive": 0, "false_positive": 0, "false_negative": 0, "true_negative": 0}
    for path in events:
        number = int(path.stem)
        try:
            event = parse_event("pull_request", json.loads(path.read_text(encoding="utf-8")))
            diff = folder / "diffs" / f"{number}.diff"
            changed = read_diff_file(diff) if diff.is_file() else None
        except (EventError, DiffError, ValueError) as exc:
            rows.append({"number": number, "error": str(exc)})
            continue
        decision = decide(config, event, changed, diff_source=f"diff {number}")
        predicted = "yes" if decision.docs_needed == "needs_research" else "no"
        label = labels.get(number)
        outcome = None
        if label is not None:
            outcome = {("yes", "yes"): "true_positive", ("yes", "no"): "false_positive",
                       ("no", "yes"): "false_negative", ("no", "no"): "true_negative"}[(predicted, label)]
            counts[outcome] += 1
        rows.append({"number": number, "title": event.title, "kind": event.kind, "predicted": predicted,
                     "label": label, "outcome": outcome, "summary": decision.summary})
    tp, fp, fn = counts["true_positive"], counts["false_positive"], counts["false_negative"]
    report = {
        "replayed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "prs": len(rows), "labelled": sum(counts.values()),
        "unscored": [r["number"] for r in rows if r.get("label") is None],
        "counts": counts,
        "precision": f"{tp}/{tp + fp}" if tp + fp else "n/a (no predicted yes among labelled PRs)",
        "recall": f"{tp}/{tp + fn}" if tp + fn else "n/a (no labelled yes)",
        "rows": rows,
        "labelled_by": by,
        "independent_labels": independent,
        "note": ("Labels are a person's judgement; this compares DocForge's rule-based triage with them."
                 if independent else
                 "Labels were not made independently of DocForge (labelled by the generating session, or none). "
                 "Treat agreement as a consistency check, not as measured accuracy."),
    }
    stamp = _stamp()
    (folder / f"replay-{stamp}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (folder / f"replay-{stamp}.md").write_text(render_replay(report), encoding="utf-8")
    report["files"] = [f"replay-{stamp}.json", f"replay-{stamp}.md"]
    return report


def render_replay(report: dict) -> str:
    c = report["counts"]
    lines = [
        "# Trigger replay", "",
        f"{report['prs']} PR(s) replayed, {report['labelled']} labelled"
        + (f" by {', '.join(report['labelled_by'])}." if report["labelled_by"] else ".") + f" {report['note']}", "",
        "| | Labelled yes | Labelled no |", "| --- | --- | --- |",
        f"| DocForge said yes | {c['true_positive']} | {c['false_positive']} |",
        f"| DocForge said no | {c['false_negative']} | {c['true_negative']} |", "",
        f"Precision: {report['precision']}. Recall: {report['recall']}.", "",
        "| PR | Title | Event | DocForge | Label | Result | Reason |", "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in report["rows"]:
        if "error" in r:
            lines.append(f"| {r['number']} | | | | | error | {r['error']} |")
            continue
        title = r["title"].replace("|", "\\|")
        summary = r["summary"].replace("|", "\\|")
        lines.append(f"| {r['number']} | {title} | {r['kind'] or 'ignored'} | {r['predicted']} | "
                     f"{r['label'] or 'unlabelled'} | {(r['outcome'] or 'unscored').replace('_', ' ')} | {summary} |")
    return "\n".join(lines) + "\n"
