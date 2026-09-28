#!/usr/bin/env python3
"""Check the structure of one generated documentation set.

This gate checks files, headings, links, placeholders, and Markdown source
line locators. A source-first
Proofreader must still check the accuracy and completeness of product claims.
"""

from pathlib import Path
import re
import sys
from urllib.parse import unquote
import json


REQUIRED = {
    "analysis/HANDOVER.md": ("## Claim register", "## Clarifications and contradictions"),
    "analysis/clarifications-and-assumptions.md": (),
    "analysis/CONTENT-PLAN.md": ("## Scope decisions", "## Delivery boundary"),
    "analysis/COVERAGE.md": ("## Claim coverage",),
    "analysis/EDITORIAL-BLUEPRINT.md": ("## Document contracts", "## Feature-guide blueprint", "## How-to selection", "## Release-note blueprint", "## Cross-document separation", "## Claim-admission gate", "## Pre-draft challenge", "## Draft challenge result"),
    "feature/feature-guide.md": (),
    "how-to/how-to.md": ("## Steps", "## Expected result"),
    "release-note/release-note.md": (),
    "qa/QA-REPORT.md": ("## Findings", "## Readiness"),
}
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|Lorem ipsum)\b|\{\{[^}]+\}\}|\[Feature name\]", re.I)
CLAIM = re.compile(r"\bC\d+[A-Z]?\b")
QUESTION = re.compile(r"\bQ\d+\b")
REGISTER_ROW = re.compile(r"^\|\s*(C\d+[A-Z]?)\s*\|", re.M)
ALLOWED_DISPOSITIONS = {"INCLUDED", "CONTEXT", "DEFERRED", "BLOCKED"}
SOURCE_LINE = re.compile(
    r"(?P<path>(?:demo|input)/[^\s`|,;()]+\.md)"
    r"(?:\s*,?\s*(?:at\s+)?lines?\s+|:L?)"
    r"(?P<first>\d+)(?:\s*[-–]\s*L?(?P<last>\d+))?",
    re.I,
)


def check_source_lines(relative: str, body: str, errors: list[str]) -> None:
    repo = Path(__file__).resolve().parents[1]
    for match in SOURCE_LINE.finditer(body):
        source = repo / match["path"]
        first = int(match["first"])
        last = int(match["last"] or first)
        if not source.is_file():
            errors.append(f"{relative}: source line citation file missing: {match['path']}")
            continue
        lines = source.read_text(encoding="utf-8").splitlines()
        if first < 1 or last < first or last > len(lines):
            errors.append(f"{relative}: invalid source lines {match.group(0)}")
        elif not any(lines[index - 1].strip() for index in range(first, last + 1)):
            errors.append(f"{relative}: source citation points only to blank lines: {match.group(0)}")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/check_outputs.py output/<slug>")
        return 2

    root = Path(sys.argv[1]).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    texts: dict[str, str] = {}

    for relative, headings in REQUIRED.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"Missing {relative}")
            continue
        body = path.read_text(encoding="utf-8")
        texts[relative] = body
        if len(body.strip()) < 100:
            errors.append(f"{relative}: appears incomplete (<100 characters)")
        for heading in headings:
            if not re.search(rf"^{re.escape(heading)}\s*$", body, re.M):
                errors.append(f"{relative}: missing {heading}")
        if PLACEHOLDER.search(body):
            warnings.append(f"{relative}: possible placeholder text")
        if body.count("```") % 2:
            errors.append(f"{relative}: unclosed fenced block")
        for target in LINK.findall(body):
            if target.startswith(("http:", "https:", "mailto:", "#")):
                continue
            resolved = path.parent / unquote(target.split("#", 1)[0])
            if not resolved.exists():
                errors.append(f"{relative}: broken link to {target}")

    handover = texts.get("analysis/HANDOVER.md", "")
    clarifications = texts.get("analysis/clarifications-and-assumptions.md", "")
    plan = texts.get("analysis/CONTENT-PLAN.md", "")
    coverage = texts.get("analysis/COVERAGE.md", "")
    if handover:
        known_claims = set(CLAIM.findall(handover))
        known_questions = set(QUESTION.findall(handover))
        register_section = handover.split("## Claim register", 1)[-1].split("\n## ", 1)[0]
        register_ids = REGISTER_ROW.findall(register_section)
        if not register_ids:
            errors.append("analysis/HANDOVER.md: no claim register rows")
        if len(register_ids) != len(set(register_ids)):
            errors.append("analysis/HANDOVER.md: duplicate claim register IDs")
        rows = []
        for line in coverage.splitlines():
            if REGISTER_ROW.match(line):
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                rows.append(cells)
        covered_ids = [row[0] for row in rows]
        for claim in sorted(set(register_ids) - set(covered_ids)):
            errors.append(f"analysis/COVERAGE.md: missing {claim}")
        for claim in sorted(set(covered_ids) - set(register_ids)):
            errors.append(f"analysis/COVERAGE.md: unexpected {claim}")
        if len(covered_ids) != len(set(covered_ids)):
            errors.append("analysis/COVERAGE.md: duplicate claim IDs")
        for row in rows:
            if len(row) < 4:
                errors.append(f"analysis/COVERAGE.md: incomplete row for {row[0]}")
                continue
            claim, disposition, destination, reason = row[:4]
            if disposition not in ALLOWED_DISPOSITIONS:
                errors.append(f"analysis/COVERAGE.md: {claim} invalid disposition {disposition}")
            if not reason:
                errors.append(f"analysis/COVERAGE.md: {claim} missing rationale")
            if disposition == "INCLUDED":
                paths = re.findall(r"(?:feature|how-to|release-note)/[\w.-]+\.md", destination)
                if not paths or any(not (root / path).is_file() for path in paths):
                    errors.append(f"analysis/COVERAGE.md: {claim} needs an existing reader-facing destination")
            elif destination not in {"—", "-", "None"}:
                errors.append(f"analysis/COVERAGE.md: {claim} non-included destination must be empty")
        for relative, body in (
            ("analysis/clarifications-and-assumptions.md", clarifications),
            ("analysis/CONTENT-PLAN.md", plan),
            ("analysis/COVERAGE.md", coverage),
            ("qa/QA-REPORT.md", texts.get("qa/QA-REPORT.md", "")),
        ):
            for claim in sorted(set(CLAIM.findall(body)) - known_claims):
                errors.append(f"{relative}: {claim} missing from handover")
            for question in sorted(set(QUESTION.findall(body)) - known_questions):
                errors.append(f"{relative}: {question} missing from handover")
        for question in sorted(known_questions - set(QUESTION.findall(clarifications))):
            warnings.append(f"Clarification register does not mention {question}")

    # V2.2 artifacts are mandatory for fresh V2.2 runs but optional for legacy
    # benchmark sets. If any one is present, require and validate the complete set.
    advanced = {
        "analysis/TERMINOLOGY.md": ("## Canonical terms", "## Final terminology audit"),
        "analysis/RISK-REVIEW.md": ("## High-impact claims", "## Example safety", "## Cross-document ownership", "## Final risk audit"),
        "analysis/TRACEABILITY.json": (),
    }
    advanced_present = any((root / relative).is_file() for relative in advanced)
    if advanced_present:
        for relative, headings in advanced.items():
            path = root / relative
            if not path.is_file():
                errors.append(f"Missing V2.2 artifact {relative}")
                continue
            body = path.read_text(encoding="utf-8")
            if len(body.strip()) < 100:
                errors.append(f"{relative}: appears incomplete (<100 characters)")
            for heading in headings:
                if not re.search(rf"^{re.escape(heading)}\s*$", body, re.M):
                    errors.append(f"{relative}: missing {heading}")
        manifest_path = root / "analysis/TRACEABILITY.json"
        if manifest_path.is_file():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest_ids = [item.get("id") for item in manifest.get("claims", [])]
                if len(manifest_ids) != len(set(manifest_ids)):
                    errors.append("analysis/TRACEABILITY.json: duplicate claim IDs")
                register_ids_set = set(register_ids) if handover else set()
                if set(manifest_ids) != register_ids_set:
                    errors.append("analysis/TRACEABILITY.json: claim IDs must exactly match HANDOVER claim register")
                readiness = manifest.get("readiness")
                if readiness not in {"DRAFTABLE", "ASSIGNMENT-READY", "REVIEW-READY", "PUBLICATION-READY"}:
                    errors.append("analysis/TRACEABILITY.json: invalid readiness state")
                blockers = manifest.get("publication_blockers", [])
                if readiness == "PUBLICATION-READY" and blockers:
                    errors.append("analysis/TRACEABILITY.json: PUBLICATION-READY cannot have publication blockers")
            except json.JSONDecodeError as exc:
                errors.append(f"analysis/TRACEABILITY.json: invalid JSON ({exc})")

    impact_path = root / "analysis/CHANGE-IMPACT.md"
    if impact_path.is_file():
        impact = impact_path.read_text(encoding="utf-8")
        for heading in ("## Baseline", "## Source changes", "## Document actions"):
            if not re.search(rf"^{re.escape(heading)}\s*$", impact, re.M):
                errors.append(f"analysis/CHANGE-IMPACT.md: missing {heading}")
        if PLACEHOLDER.search(impact):
            warnings.append("analysis/CHANGE-IMPACT.md: possible placeholder text")
        for claim in sorted(set(CLAIM.findall(impact)) - set(CLAIM.findall(handover))):
            # Previous-source IDs may differ from the current register; the
            # proofreader reviews those references rather than rejecting them.
            warnings.append(f"analysis/CHANGE-IMPACT.md: check prior-source reference {claim}")

    for relative, body in texts.items():
        if relative.startswith(("analysis/", "qa/")):
            check_source_lines(relative, body, errors)
    if impact_path.is_file():
        check_source_lines("analysis/CHANGE-IMPACT.md", impact, errors)

    # Editorial prompts are warnings: source fidelity and audience fit require
    # human/source-first review, so a title heuristic must not become a gate.
    feature = texts.get("feature/feature-guide.md", "")
    release = texts.get("release-note/release-note.md", "")
    feature_title = re.search(r"^#\s+(.+)$", feature, re.M)
    release_title = re.search(r"^#\s+(.+)$", release, re.M)
    if feature_title and release_title and feature_title[1].strip().casefold() == release_title[1].strip().casefold():
        warnings.append("Feature guide and release note use the same title; review distinct reader goals")
    for relative in ("feature/feature-guide.md", "how-to/how-to.md", "release-note/release-note.md"):
        body = texts.get(relative, "")
        if re.search(r"\b(?:requirements conflict|unresolved in this proposal|internal note)\b", body, re.I):
            warnings.append(f"{relative}: internal review language in reader-facing draft")

    for issue in errors:
        print(f"FAIL: {issue}")
    for issue in warnings:
        print(f"WARNING: {issue}")
    print(f"{'FAIL' if errors else 'PASS'}: {len(texts)}/{len(REQUIRED)} files checked; "
          f"{len(errors)} error(s), {len(warnings)} warning(s)")
    print("Structural and line-target checks only; source fidelity requires the Proofreader.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
