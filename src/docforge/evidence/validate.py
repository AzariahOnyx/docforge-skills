"""Validate a configurable documentation run (run.json + evidence.json + deliverables).

This is structural, provenance and exact-quotation validation, not semantic
entailment, factual correctness, product testing or publication approval.
Moved from scripts/validate_run.py; error messages are kept word for word.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Mapping, Optional

from .code import is_git_checkout, verify_code_evidence
from .flows import check_citation, flow_steps
from .models import (
    FlowEvidence,
    CodeEvidence,
    EvidenceStatus,
    QuoteEvidence,
    ReviewMethod,
    ReviewStatus,
    parse_evidence,
    parse_manifest,
)

SOURCE_REF = re.compile(r"\[([A-Za-z][\w-]*)#(L\d+(?:-L?\d+)?|p\d+(?:-\d+)?|step\d+(?:-\d+)?|section:[^\]]+)\]")
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|Lorem ipsum)\b|\{\{[^}]+\}\}", re.I)
BAD_LINK = re.compile(r"\b(?:click here|read more)\b", re.I)


def safe_path(base: Path, relative) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError(f"Invalid relative path: {relative!r}")
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError(f"Path escapes allowed root: {relative}")
    return path


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _normalize(text: str) -> str:
    return " ".join(text.split()).casefold()


def validate(run: Path, repo: Path, code_roots: Optional[Mapping[str, Path]] = None):
    """Return (errors, warnings) for the run folder `run`.

    `repo` is the root that run.json source paths are relative to.
    `code_roots` maps "owner/repo" to a local Git checkout used to verify code
    evidence; code evidence for any other repo is reported as not verified.
    """
    errors: list[str] = []
    warnings: list[str] = []
    code_roots = dict(code_roots or {})

    manifest_path = run / "run.json"
    if not manifest_path.is_file():
        return ["Missing run.json"], warnings
    try:
        raw = load_json(manifest_path)
    except (ValueError, OSError) as exc:
        return [f"Invalid run.json: {exc}"], warnings
    manifest, manifest_errors = parse_manifest(raw)
    errors.extend(manifest_errors)

    # Sources: files must exist inside `repo` and match their recorded hash.
    source_map: dict[str, Path] = {}
    for source in manifest.sources:
        sid = source.id
        try:
            path = safe_path(repo, source.path)
            if not path.is_file():
                errors.append(f"{sid}: source file missing")
                continue
            if source.sha256 is not None and hashlib.sha256(path.read_bytes()).hexdigest() != source.sha256:
                errors.append(f"{sid}: source hash mismatch")
            source_map[sid] = path
        except (ValueError, OSError) as exc:
            errors.append(f"{sid}: {exc}")

    # Deliverables: Markdown structure, local links and source locators.
    docs: dict[str, str] = {}
    for name in manifest.deliverables:
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
                if locator.startswith("step"):
                    steps = flow_steps(source_map[sid].read_text(encoding="utf-8"))
                    if not steps:
                        errors.append(f"{name}: [{sid}#{locator}] cites steps, but {sid} is not a flow source")
                    else:
                        problem = check_citation(steps, locator)
                        if problem:
                            errors.append(f"{name}: [{sid}#{locator}]: {problem}")
                elif locator.startswith("L"):
                    match = re.fullmatch(r"L(\d+)(?:-L?(\d+))?", locator)
                    first = int(match.group(1))
                    last = int(match.group(2) or first)
                    lines = source_map[sid].read_text(encoding="utf-8").splitlines()
                    if first < 1 or last < first or last > len(lines) or not any(x.strip() for x in lines[first - 1 : last]):
                        errors.append(f"{name}: invalid or blank source locator [{sid}#{locator}]")
                else:
                    warnings.append(f"{name}: page/section locator [{sid}#{locator}] requires manual verification")
        except (ValueError, OSError) as exc:
            errors.append(f"{name}: {exc}")

    # Evidence: every row must be backed by a quotation or by code at a commit.
    evidence_path = run / "analysis" / "evidence.json"
    if not evidence_path.is_file():
        errors.append("missing analysis/evidence.json")
    else:
        try:
            rows, evidence_errors = parse_evidence(load_json(evidence_path))
            errors.extend(evidence_errors)
            checked_roots: dict[str, bool] = {}
            for row in rows:
                cid = row.claim_id
                if isinstance(row, QuoteEvidence):
                    if row.source_id not in source_map:
                        errors.append(f"{cid}: unknown source {row.source_id}")
                    elif not isinstance(row.quote, str) or not row.quote.strip():
                        errors.append(f"{cid}: missing source quotation")
                    elif _normalize(row.quote) not in _normalize(source_map[row.source_id].read_text(encoding="utf-8")):
                        errors.append(f"{cid}: quotation not found in source")
                elif isinstance(row, FlowEvidence):
                    if row.source_id not in source_map:
                        errors.append(f"{cid}: unknown flow source {row.source_id}")
                    else:
                        steps = flow_steps(source_map[row.source_id].read_text(encoding="utf-8"))
                        if not steps:
                            errors.append(f"{cid}: {row.source_id} is not a flow source")
                        elif row.step not in steps:
                            errors.append(f"{cid}: {row.source_id} has no step {row.step}")
                        elif _normalize(row.quote) not in _normalize(steps[row.step]):
                            errors.append(f"{cid}: quotation not found in {row.source_id} step {row.step}")
                elif isinstance(row, CodeEvidence):
                    root = code_roots.get(row.repo)
                    if root is None:
                        warnings.append(f"{cid}: code evidence not verified (no local checkout for {row.repo})")
                    else:
                        if row.repo not in checked_roots:
                            checked_roots[row.repo] = is_git_checkout(Path(root))
                            if not checked_roots[row.repo]:
                                errors.append(f"code root for {row.repo} is not a Git checkout")
                        if checked_roots[row.repo]:
                            errors.extend(verify_code_evidence(row, Path(root)))
                if isinstance(row.destinations, list):
                    if row.status is EvidenceStatus.INCLUDED:
                        if not row.destinations or any(d not in docs for d in row.destinations):
                            errors.append(f"{cid}: included claim lacks an existing deliverable")
                    elif row.destinations:
                        errors.append(f"{cid}: non-included claim must not have destinations")
        except (ValueError, OSError, AttributeError, TypeError) as exc:
            errors.append(f"invalid evidence.json: {exc}")

    review = manifest.review
    if review.method is ReviewMethod.SAME_AGENT_SECOND_PASS:
        warnings.append("same-agent review is not independent")
    if review.human_approval is not ReviewStatus.PASSED:
        warnings.append("not approved for publication")
    return errors, warnings
