"""The claim gate: every published statement must be backed by usable evidence.

A statement fails the gate when it has no evidence marker, when a marker is
malformed, when it cites a claim the run does not know, when the claim is not
INCLUDED for that page in the coverage ledger (default profile) or the
evidence ledger (custom profile), or when the claim's cross-source status is
conflicting, unknown or needs_engineering. Exemptions (`evidence: none
(reason)`) pass but are listed for reviewers.

The gate runs on a run folder (`gate_run`) or on published pages with the
evidence manifest a docs pull request carries (`gate_manifest`).
"""

from __future__ import annotations

import json
from pathlib import Path
import re

from pydantic import BaseModel, Field

from docforge.evidence.models import CLAIM_ID

from .markers import statements

BLOCKED_STATUSES = {"conflicting", "unknown", "needs_engineering"}
COVERAGE_ROW = re.compile(r"^\|\s*(C\d+[A-Z]?)\s*\|\s*([A-Z]+)\s*\|\s*([^|]*)\|", re.M)
CLAIM_IN_TEXT = re.compile(r"\bC\d+[A-Z]?\b")


class GateIssue(BaseModel):
    path: str
    line: int
    message: str


class Exemption(BaseModel):
    path: str
    line: int
    reason: str
    text: str


class GateResult(BaseModel):
    passed: bool
    pages: list[str]
    statements: int = 0
    cited: int = 0
    exemptions: list[Exemption] = Field(default_factory=list)
    errors: list[GateIssue] = Field(default_factory=list)
    claims_cited: dict[str, list[str]] = Field(default_factory=dict)


class EvidenceRules(BaseModel):
    """What a gate needs to know about a run's claims."""

    known: list[str]
    # page path -> claims INCLUDED for that page
    allowed: dict[str, list[str]]
    # claim -> cross-source status, for claims that cannot back a statement
    blocked: dict[str, str] = Field(default_factory=dict)


class GateError(Exception):
    """Raised when the gate cannot read its inputs."""


def rules_for_run(run: Path) -> EvidenceRules:
    try:
        manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GateError(f"cannot read run.json: {exc}") from None
    deliverables = [d for d in manifest.get("deliverables", []) if isinstance(d, str)]
    known: set[str] = set()
    allowed: dict[str, set[str]] = {d: set() for d in deliverables}

    handover = run / "analysis" / "HANDOVER.md"
    if handover.is_file():
        known |= set(CLAIM_IN_TEXT.findall(handover.read_text(encoding="utf-8")))

    if manifest.get("profile") == "custom":
        path = run / "analysis" / "evidence.json"
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise GateError(f"cannot read analysis/evidence.json: {exc}") from None
        for row in rows if isinstance(rows, list) else []:
            cid = row.get("claim_id") if isinstance(row, dict) else None
            if isinstance(cid, str) and CLAIM_ID.fullmatch(cid):
                known.add(cid)
                if row.get("status") == "included":
                    for dest in row.get("destinations") or []:
                        allowed.setdefault(dest, set()).add(cid)
    else:
        path = run / "analysis" / "COVERAGE.md"
        if not path.is_file():
            raise GateError("missing analysis/COVERAGE.md; the Drafter stage writes it")
        for cid, disposition, destination in COVERAGE_ROW.findall(path.read_text(encoding="utf-8")):
            known.add(cid)
            if disposition == "INCLUDED":
                for dest in deliverables:
                    if dest in destination:
                        allowed[dest].add(cid)

    blocked: dict[str, str] = {}
    cross = run / "analysis" / "cross-source.json"
    if cross.is_file():
        try:
            for result in json.loads(cross.read_text(encoding="utf-8")):
                known.add(result["claim_id"])
                if result["status"] in BLOCKED_STATUSES:
                    blocked[result["claim_id"]] = result["status"]
        except (ValueError, KeyError, TypeError) as exc:
            raise GateError(f"cannot read analysis/cross-source.json: {exc}") from None

    return EvidenceRules(known=sorted(known), allowed={k: sorted(v) for k, v in allowed.items()}, blocked=blocked)


def check_pages(pages: dict[str, str], rules: EvidenceRules, ledger: str = "the coverage ledger") -> GateResult:
    """Gate pages given as {path: markdown}."""
    known, blocked = set(rules.known), rules.blocked
    result = GateResult(passed=True, pages=sorted(pages))
    for path, text in sorted(pages.items()):
        allowed = set(rules.allowed.get(path, []))
        cited: set[str] = set()
        for s in statements(text):
            if s.kind == "marker":
                result.errors.append(GateIssue(path=path, line=s.line, message=s.error))
                continue
            result.statements += 1
            if s.error:
                result.errors.append(GateIssue(path=path, line=s.line, message=f"{s.error}: \"{s.snippet}\""))
            elif s.exempt is not None:
                result.exemptions.append(Exemption(path=path, line=s.line, reason=s.exempt, text=s.snippet))
            elif s.claims is None:
                result.errors.append(GateIssue(path=path, line=s.line,
                                               message=f"statement has no evidence marker: \"{s.snippet}\""))
            else:
                result.cited += 1
                for cid in s.claims:
                    cited.add(cid)
                    if cid not in known:
                        message = f"{cid} is not a known claim"
                    elif cid in blocked:
                        message = f"{cid} is {blocked[cid]} and cannot back a published statement"
                    elif cid not in allowed:
                        message = f"{cid} is not INCLUDED for {path} in {ledger}"
                    else:
                        continue
                    result.errors.append(GateIssue(path=path, line=s.line, message=f"{message}: \"{s.snippet}\""))
        result.claims_cited[path] = sorted(cited)
    result.passed = not result.errors
    return result


def gate_run(run: Path, *, write: bool = True) -> GateResult:
    """Gate a run's deliverables; writes qa/gate.json unless write is False."""
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    rules = rules_for_run(run)
    pages: dict[str, str] = {}
    missing = []
    for rel in manifest.get("deliverables", []):
        path = run / rel
        if path.is_file():
            pages[rel] = path.read_text(encoding="utf-8")
        else:
            missing.append(rel)
    ledger = "the evidence ledger" if manifest.get("profile") == "custom" else "the coverage ledger"
    result = check_pages(pages, rules, ledger)
    for rel in missing:
        result.errors.append(GateIssue(path=rel, line=0, message="deliverable is missing"))
    result.passed = not result.errors
    if write:
        (run / "qa").mkdir(exist_ok=True)
        (run / "qa" / "gate.json").write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return result


class EvidenceManifest(BaseModel):
    """Carried in a docs pull request so the gate can run in the docs repo's CI."""

    schema_version: int = 1
    run: str
    rules: EvidenceRules  # keyed by published docs paths


def gate_manifest(manifest_path: Path, docs_root: Path) -> GateResult:
    try:
        manifest = EvidenceManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GateError(f"cannot read evidence manifest {manifest_path}: {exc}") from None
    pages: dict[str, str] = {}
    missing = []
    for rel in manifest.rules.allowed:
        path = docs_root / rel
        if path.is_file():
            pages[rel] = path.read_text(encoding="utf-8")
        else:
            missing.append(rel)
    result = check_pages(pages, manifest.rules, "the run's coverage")
    for rel in missing:
        result.errors.append(GateIssue(path=rel, line=0, message="page listed in the evidence manifest is missing"))
    result.passed = not result.errors
    return result
