#!/usr/bin/env python3
"""Conservative Markdown writing and accessibility checks.

Findings are editorial review prompts, not proof of MSTP compliance or
accessibility conformance. Use the human review checklist as well.
"""
import argparse
from pathlib import Path
import re

IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
LINK = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
HEADING = re.compile(r"^(#{1,6})\s+(.+)$")
GENERIC_LINK = {"click here", "here", "read more", "learn more", "link"}

def lint(text):
    issues = []
    level = 0
    in_code = False
    for n, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        match = HEADING.match(line)
        if match:
            current = len(match.group(1))
            if current > level + 1:
                issues.append((n, "heading-level-skip", "Heading level skips a level"))
            level = current
            if not match.group(2).strip():
                issues.append((n, "empty-heading", "Heading has no text"))
        for img in IMAGE.finditer(line):
            if not img.group(1).strip():
                issues.append((n, "image-alt", "Image has empty alternative text; verify if decorative"))
        for link in LINK.finditer(line):
            if link.group(1).strip().lower() in GENERIC_LINK:
                issues.append((n, "generic-link", "Link text does not describe the destination"))
        if re.search(r"\b(?:simply|obviously|just click)\b", line, re.I):
            issues.append((n, "wording", "Review subjective or dismissive wording"))
        if re.search(r"\b(?:he/she|whitelist|blacklist)\b", line, re.I):
            issues.append((n, "terminology", "Review potentially exclusionary terminology in context"))
    return issues

def main():
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="+", type=Path)
    p.add_argument("--strict", action="store_true", help="Return nonzero when any finding exists")
    args = p.parse_args()
    count = 0
    for path in args.files:
        if not path.is_file():
            p.error(f"missing file: {path}")
        for line, code, description in lint(path.read_text(encoding="utf-8")):
            count += 1
            print(f"{path}:{line}: {code}: {description}")
    print(f"{count} editorial finding(s). Human review is still required.")
    return int(args.strict and count > 0)

if __name__ == "__main__":
    raise SystemExit(main())
