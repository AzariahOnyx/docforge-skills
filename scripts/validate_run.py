#!/usr/bin/env python3
"""Validate a configurable documentation run using only the Python standard library.

This is structural, provenance and exact-quotation validation, not semantic
entailment, factual correctness, product testing or publication approval.

Thin wrapper over src/docforge/evidence, which holds the validation logic.
Runs with plain python3; nothing needs to be installed.
"""
import argparse
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from docforge.evidence import validate  # noqa: E402  (re-exported for scripts/test_validate_run.py)
from docforge.evidence.models import REPO_NAME  # noqa: E402


def code_root(value: str):
    name, sep, path = value.partition("=")
    if not sep or not REPO_NAME.fullmatch(name) or not path:
        raise argparse.ArgumentTypeError("use owner/repo=PATH")
    return name, Path(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument(
        "--code-root",
        type=code_root,
        action="append",
        default=[],
        metavar="OWNER/REPO=PATH",
        help="local Git checkout used to verify code evidence for that repo (repeatable)",
    )
    args = parser.parse_args()
    roots = {name: path.resolve() for name, path in args.code_root}
    errors, warnings = validate(args.run.resolve(), args.repo.resolve(), roots)
    for error in errors:
        print("FAIL:", error)
    for warning in warnings:
        print("WARNING:", warning)
    print(f"{'FAIL' if errors else 'PASS'}: {len(errors)} errors, {len(warnings)} warnings")
    print("Structure, hashes and exact quotations only. Human source fidelity review is required.")
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
