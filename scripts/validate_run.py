#!/usr/bin/env python3
"""Validate a configurable documentation run using only the Python standard library.

This is structural, provenance and exact-quotation validation, not semantic
entailment, factual correctness, product testing or publication approval.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

CLAIM = re.compile(r"\bC\d+[A-Z]?\b")
SOURCE_REF = re.compile(r"\[([A-Za-z][\w-]*)#(L\d+(?:-L?\d+)?|p\d+(?:-\d+)?|section:[^\]]+)\]")
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|Lorem ipsum)\b|\{\{[^}]+\}\}", re.I)
BAD_LINK = re.compile(r"\b(?:click here|read more)\b", re.I)
ALLOWED_STATUS = {"pending", "passed", "failed", "blocked", "not_applicable"}
ALLOWED_METHOD = {"independent_reviewer", "same_agent_second_pass", "human_reviewer", "not_reviewed"}

def safe_path(base: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError(f"Invalid relative path: {relative!r}")
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError(f"Path escapes allowed root: {relative}")
    return path

def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)

def validate(run: Path, repo: Path):
    errors, warnings = [], []
    manifest_path = run / "run.json"
    if not manifest_path.is_file():
        return ["Missing run.json"], warnings
    try:
        m = load_json(manifest_path)
    except (ValueError, OSError) as exc:
        return [f"Invalid run.json: {exc}"], warnings
    if m.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if m.get("profile") not in {"default", "custom"}:
        errors.append("profile must be default or custom")
    if not isinstance(m.get("audience"), str) or not m["audience"].strip():
        errors.append("audience is required")
    sources = m.get("sources", [])
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a nonempty list")
        sources = []
    source_map = {}
    for source in sources:
        if not isinstance(source, dict):
            errors.append("source entry must be an object")
            continue
        sid = source.get("id")
        if not isinstance(sid, str) or not re.fullmatch(r"[A-Za-z][\w-]*", sid):
            errors.append("invalid source ID")
            continue
        if sid in source_map:
            errors.append(f"duplicate source ID {sid}")
            continue
        try:
            path = safe_path(repo, source.get("path"))
            if not path.is_file():
                errors.append(f"{sid}: source file missing")
                continue
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            expected = source.get("sha256")
            if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
                errors.append(f"{sid}: sha256 is required")
            elif actual != expected:
                errors.append(f"{sid}: source hash mismatch")
            source_map[sid] = path
        except (ValueError, OSError) as exc:
            errors.append(f"{sid}: {exc}")
    deliverables = m.get("deliverables", [])
    if not isinstance(deliverables, list) or not deliverables:
        errors.append("deliverables must be a nonempty list")
        deliverables = []
    if len(deliverables) != len(set(str(x) for x in deliverables)):
        errors.append("duplicate deliverables")
    docs = {}
    for name in deliverables:
        try:
            path = safe_path(run, name)
            if not path.is_file() or path.suffix.lower() != ".md":
                errors.append(f"missing Markdown deliverable: {name}")
                continue
            body = path.read_text(encoding="utf-8")
            docs[name] = body
            if len(body.strip()) < 80:
                errors.append(f"{name}: document is too short")
            if not re.search(r"^#\s+\S+", body, re.M):
                errors.append(f"{name}: missing H1")
            if body.count("```") % 2:
                errors.append(f"{name}: unclosed code fence")
            if PLACEHOLDER.search(body):
                errors.append(f"{name}: unresolved placeholder")
            if BAD_LINK.search(body):
                warnings.append(f"{name}: use descriptive link text")
            for target in LINK.findall(body):
                if target.startswith(("http:", "https:", "mailto:", "#")):
                    continue
                if not (path.parent / target.split("#", 1)[0]).resolve().is_file():
                    errors.append(f"{name}: broken local link {target}")
            for ref in SOURCE_REF.finditer(body):
                sid, locator = ref.groups()
                if sid not in source_map:
                    errors.append(f"{name}: unknown source ID {sid}")
                    continue
                if locator.startswith("L"):
                    match = re.fullmatch(r"L(\d+)(?:-L?(\d+))?", locator)
                    first = int(match.group(1))
                    last = int(match.group(2) or first)
                    lines = source_map[sid].read_text(encoding="utf-8").splitlines()
                    if first < 1 or last < first or last > len(lines) or not any(x.strip() for x in lines[first-1:last]):
                        errors.append(f"{name}: invalid or blank source locator [{sid}#{locator}]")
                else:
                    warnings.append(f"{name}: page/section locator [{sid}#{locator}] requires manual verification")
        except (ValueError, OSError) as exc:
            errors.append(f"{name}: {exc}")
    evidence_path = run / "analysis" / "evidence.json"
    if not evidence_path.is_file():
        errors.append("missing analysis/evidence.json")
    else:
        try:
            evidence = load_json(evidence_path)
            if not isinstance(evidence, list) or not evidence:
                errors.append("evidence must be a nonempty array")
                evidence = []
            ids = set()
            for row in evidence:
                cid = row.get("claim_id")
                sid = row.get("source_id")
                quote = row.get("quote")
                destinations = row.get("destinations")
                status = row.get("status")
                if not isinstance(cid, str) or not CLAIM.fullmatch(cid) or cid in ids:
                    errors.append(f"invalid or duplicate evidence claim {cid}")
                ids.add(cid)
                if status not in {"included", "blocked", "deferred", "context"}:
                    errors.append(f"{cid}: invalid evidence status")
                if sid not in source_map:
                    errors.append(f"{cid}: unknown source {sid}")
                elif not isinstance(quote, str) or not quote.strip():
                    errors.append(f"{cid}: missing source quotation")
                else:
                    normalize = lambda s: " ".join(s.split()).casefold()
                    if normalize(quote) not in normalize(source_map[sid].read_text(encoding="utf-8")):
                        errors.append(f"{cid}: quotation not found in source")
                if not isinstance(destinations, list):
                    errors.append(f"{cid}: destinations must be a list")
                elif status == "included":
                    if not destinations or any(d not in docs for d in destinations):
                        errors.append(f"{cid}: included claim lacks an existing deliverable")
                elif destinations:
                    errors.append(f"{cid}: non-included claim must not have destinations")
        except (ValueError, OSError, AttributeError) as exc:
            errors.append(f"invalid evidence.json: {exc}")
    review = m.get("review", {})
    if not isinstance(review, dict):
        review = {}
    if review.get("method") not in ALLOWED_METHOD:
        errors.append("review.method must identify reviewer method")
    for field in ("source_fidelity", "product_verification", "human_approval"):
        if review.get(field) not in ALLOWED_STATUS:
            errors.append(f"review.{field} has invalid status")
    if review.get("human_approval") == "passed" and review.get("source_fidelity") != "passed":
        errors.append("human approval cannot pass with source fidelity pending or failed")
    if review.get("method") == "same_agent_second_pass":
        warnings.append("same-agent review is not independent")
    if review.get("human_approval") != "passed":
        warnings.append("not approved for publication")
    return errors, warnings

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors, warnings = validate(args.run.resolve(), args.repo.resolve())
    for error in errors:
        print("FAIL:", error)
    for warning in warnings:
        print("WARNING:", warning)
    print(f"{'FAIL' if errors else 'PASS'}: {len(errors)} errors, {len(warnings)} warnings")
    print("Structure, hashes and exact quotations only. Human source fidelity review is required.")
    return bool(errors)

if __name__ == "__main__":
    sys.exit(main())
