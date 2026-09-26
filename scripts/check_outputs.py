#!/usr/bin/env python3
"""Check the structure of one generated documentation set.

This gate checks files, headings, links, and placeholders. A source-first
Proofreader must still check the accuracy and completeness of product claims.
"""

from pathlib import Path
import re
import sys
from urllib.parse import unquote


REQUIRED = {
    "analysis/HANDOVER.md": ("## Claim register", "## Clarifications and contradictions"),
    "analysis/clarifications-and-assumptions.md": (),
    "analysis/CONTENT-PLAN.md": ("## Scope decisions", "## Delivery boundary"),
    "feature/feature-guide.md": (),
    "how-to/how-to.md": ("## Steps", "## Expected result"),
    "release-note/release-note.md": (),
    "qa/QA-REPORT.md": ("## Findings", "## Readiness"),
}
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|Lorem ipsum)\b|\{\{[^}]+\}\}|\[Feature name\]", re.I)
CLAIM = re.compile(r"\bC\d+[A-Z]?\b")
QUESTION = re.compile(r"\bQ\d+\b")


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
    if handover:
        known_claims = set(CLAIM.findall(handover))
        known_questions = set(QUESTION.findall(handover))
        for relative, body in (
            ("analysis/clarifications-and-assumptions.md", clarifications),
            ("analysis/CONTENT-PLAN.md", plan),
            ("qa/QA-REPORT.md", texts.get("qa/QA-REPORT.md", "")),
        ):
            for claim in sorted(set(CLAIM.findall(body)) - known_claims):
                errors.append(f"{relative}: {claim} missing from handover")
            for question in sorted(set(QUESTION.findall(body)) - known_questions):
                errors.append(f"{relative}: {question} missing from handover")
        for question in sorted(known_questions - set(QUESTION.findall(clarifications))):
            warnings.append(f"Clarification register does not mention {question}")

    for issue in errors:
        print(f"FAIL: {issue}")
    for issue in warnings:
        print(f"WARNING: {issue}")
    print(f"{'FAIL' if errors else 'PASS'}: {len(texts)}/{len(REQUIRED)} files checked; "
          f"{len(errors)} error(s), {len(warnings)} warning(s)")
    print("Structural checks only; source fidelity requires the Proofreader.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
