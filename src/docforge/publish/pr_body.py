"""The title and body of a DocForge docs pull request.

The body gives a reviewer everything needed to judge the change: sources and
hashes, pages, the claim gate, coverage, cross-source statuses, QA results and
every open question. It never claims the change is approved.
"""

from __future__ import annotations

import json
from pathlib import Path
import re

from .gate import COVERAGE_ROW, GateResult

MAX_BODY = 60000  # GitHub allows 65536 characters
QUESTION_HEADING = re.compile(r"^#{2,3}\s+(Q\d+)\b\s*[—:\-]*\s*(.*)$", re.M)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _readiness(qa: str) -> list[str]:
    section = qa.split("## Readiness", 1)[1] if "## Readiness" in qa else ""
    section = section.split("\n## ", 1)[0]
    return [line.strip() for line in section.splitlines() if line.strip()][:3]


def source_origin(source: dict) -> str:
    """One line on where a source came from, for reviewers."""
    origin = source.get("origin")
    if not origin:
        return "file"
    label = {"jira": "Jira", "confluence": "Confluence page"}.get(source.get("kind"), source.get("kind", "?"))
    text = f"{label} {origin.get('id', '?')}"
    if origin.get("space"):
        text += f" in {origin['space']}"
    text += f", version {origin.get('version', 'unknown')}, fetched {origin.get('fetched_at', 'unknown')}"
    return text.replace("|", "\\|")


def default_title(run: Path) -> str:
    handover = _read(run / "analysis" / "HANDOVER.md")
    match = re.search(r"^#\s+(.+)$", handover, re.M)
    topic = match.group(1).strip() if match else run.name
    topic = re.sub(r"\s*[—-]\s*documentation handover\s*$", "", topic, flags=re.I)
    return f"docs: {topic} (DocForge draft)"


def render_body(
    run: Path,
    manifest: dict,
    gate: GateResult,
    placements: list[tuple[str, str, str]],
    *,
    branch: str,
    draft: bool,
    evidence_manifest: str,
) -> str:
    """`placements` holds (run path, docs path, added|modified)."""
    source_pr = manifest.get("source_pr")
    lines = [
        "> Prepared by DocForge from run `" + run.name + "`. A person must review and approve this pull request; "
        "nothing here is approved or verified against the live product.",
        "",
    ]
    if draft:
        lines += ["This pull request stays a **draft** while its source change is not merged.", ""]

    lines += ["## Source change", ""]
    if source_pr:
        lines.append(f"- Source PR: `{source_pr['repo']}#{source_pr['number']}` ({source_pr.get('state', 'unknown')})")
    code = manifest.get("code")
    if code:
        lines.append(f"- Code: `{code['repo']}` `{code['base'][:12]}...{code['head'][:12]}`")
    if not source_pr and not code:
        lines.append("- None recorded (PRD-only run).")

    lines += ["", "## Sources", "", "| ID | Path | SHA-256 | Authority | Origin |", "| --- | --- | --- | --- | --- |"]
    for s in manifest.get("sources", []):
        lines.append(f"| {s['id']} | `{s['path']}` | `{s['sha256'][:12]}...` | {s.get('authority', 'unconfirmed')} | "
                     f"{source_origin(s)} |")

    backend = manifest.get("backend")
    if backend:
        lines += ["", f"Drafted through the Anthropic API: {backend['calls']} call(s), models "
                      f"{', '.join(backend.get('models') or ['unknown'])}, estimated cost ${backend['cost_usd']:.2f}."]
    pack = manifest.get("pack")
    if pack:
        lines += ["", f"House pack: `{pack['name']}` {pack['version']} (sha256 `{pack['sha256'][:12]}...`). "
                      "It shapes format and style only; it is not a source."]

    lines += ["", "## Pages", "", "| Run file | Docs path | Change |", "| --- | --- | --- |"]
    lines += [f"| `{src}` | `{dest}` | {change} |" for src, dest, change in placements]
    lines += ["", f"Evidence manifest for CI: `{evidence_manifest}`"]

    lines += ["", "## Claim gate", "",
              f"**{'PASS' if gate.passed else 'FAIL'}**: {gate.statements} statement(s), {gate.cited} backed by claims, "
              f"{len(gate.exemptions)} exempt, {len(gate.errors)} error(s)."]
    if gate.flow_steps is not None:
        lines += ["", f"Numbered steps backed by flow steps: {gate.flow_backed_steps}/{gate.flow_steps}."]
    if gate.exemptions:
        lines += ["", "Exempt statements (no product fact claimed; please confirm):", ""]
        lines += [f"- `{e.path}` line {e.line} ({e.reason}): {e.text}" for e in gate.exemptions]

    coverage = _read(run / "analysis" / "COVERAGE.md")
    if coverage:
        counts: dict[str, list[str]] = {}
        for cid, disposition, _ in COVERAGE_ROW.findall(coverage):
            counts.setdefault(disposition, []).append(cid)
        lines += ["", "## Coverage", "", "| Disposition | Claims |", "| --- | --- |"]
        lines += [f"| {d} | {', '.join(ids)} |" for d, ids in sorted(counts.items())]

    cross = run / "analysis" / "cross-source.json"
    results = json.loads(cross.read_text(encoding="utf-8")) if cross.is_file() else []
    if results:
        lines += ["", "## PRD vs code", "", "| Claim | Status |", "| --- | --- |"]
        lines += [f"| {r['claim_id']} | {r['status']} |" for r in results]

    lines += ["", "## QA", ""]
    readiness = _readiness(_read(run / "qa" / "QA-REPORT.md"))
    lines += "\n\n".join(readiness).splitlines() if readiness else ["No QA report found."]
    checks_path = run / "qa" / "checks.json"
    if checks_path.is_file():
        checks = json.loads(checks_path.read_text(encoding="utf-8"))
        structural = checks.get("structural", {})
        lines += ["", f"Structural check (`{structural.get('checker')}`): "
                      f"{'PASS' if structural.get('passed') else 'FAIL'}, {len(checks.get('lint_findings', []))} lint finding(s), "
                      f"checked {checks.get('checked_at')}."]
    else:
        lines += ["", "Structural check: not run (`docforge run check`)."]

    vale_path = run / "qa" / "vale.json"
    if vale_path.is_file():
        vale = json.loads(vale_path.read_text(encoding="utf-8"))
        alerts = vale.get("alerts", [])
        counts = {s: sum(a["severity"] == s for a in alerts) for s in ("error", "warning", "suggestion")}
        lines += ["", "## Style (Vale)", "",
                  f"Vale {vale.get('vale_version')} on {'changed' if vale.get('changed_only') else 'all'} prose: "
                  f"{counts['error']} error(s), {counts['warning']} warning(s), {counts['suggestion']} suggestion(s)."]
        lines += [f"- `{a['page']}` line {a['line']}: {a['severity']} {a['check']}: {a['message']}" for a in alerts[:20]]
        if len(alerts) > 20:
            lines.append(f"- ...and {len(alerts) - 20} more in `qa/vale.json`.")
    lines += ["", "## Open questions", ""]
    questions = [f"- **{qid}** {title.strip()}" for qid, title in QUESTION_HEADING.findall(
        _read(run / "analysis" / "clarifications-and-assumptions.md"))]
    questions += [f"- **{r['question_id']}** ({r['status']}) {r['question']}" for r in results if r.get("question_id")]
    lines += questions or ["None recorded."]

    lines += [
        "", "## Before approving", "",
        "- [ ] Each page states only what its cited claims support.",
        "- [ ] Open questions that affect these pages are answered or the pages say what is unknown.",
        "- [ ] The product behavior was checked where the source is only a specification.",
        "", f"Branch: `{branch}`. Generated by DocForge; edit freely before approving.",
    ]
    body = "\n".join(lines) + "\n"
    if len(body) > MAX_BODY:
        body = body[: MAX_BODY - 200] + "\n\n_Body truncated; see the run folder for the full record._\n"
    return body
