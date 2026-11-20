"""The claim gate: every published statement must be backed by usable evidence.

A statement fails the gate when it has no evidence marker, when a marker is
malformed, when it cites a claim the run does not know, when the claim is not
INCLUDED for that page in the coverage ledger (default profile) or the
evidence ledger (custom profile), or when the claim's cross-source status is
conflicting, unknown or needs_engineering (unless an answer on the pull request resolved it:
analysis/resolutions.json). Exemptions (`evidence: none
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
ORDERED_STEP = re.compile(r"^ {0,3}\d+[.)]\s")


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
    # Numbered steps checked for flow backing, and how many were backed (None when the rule is off).
    flow_steps: int | None = None
    flow_backed_steps: int | None = None


class EvidenceRules(BaseModel):
    """What a gate needs to know about a run's claims."""

    known: list[str]
    # page path -> claims INCLUDED for that page
    allowed: dict[str, list[str]]
    # claim -> cross-source status, for claims that cannot back a statement
    blocked: dict[str, str] = Field(default_factory=dict)
    # Claims backed by a flow step. None: numbered steps need no flow backing.
    flow_backed: list[str] | None = None
    # Edited existing articles (B12b): page path -> changed line ranges [[first, last], ...]. Only statements
    # that start inside a range are gated; the rest of the page was published before.
    scopes: dict[str, list[list[int]]] = Field(default_factory=dict)


class GateError(Exception):
    """Raised when the gate cannot read its inputs."""


def rules_for_run(run: Path) -> EvidenceRules:
    try:
        manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GateError(f"cannot read run.json: {exc}") from None
    deliverables = [d for d in manifest.get("deliverables", []) if isinstance(d, str)]
    edited = [e["src"] for e in manifest.get("edits", []) if e.get("action") == "update"]
    archived = [e["src"] for e in manifest.get("edits", []) if e.get("action") == "archive"]
    known: set[str] = set()
    allowed: dict[str, set[str]] = {d: set() for d in deliverables + edited + archived}

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
                for dest in deliverables + edited:
                    if dest in destination or (dest in edited and dest.split("/", 2)[-1] in destination):
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
    resolutions = run / "analysis" / "resolutions.json"
    if blocked and resolutions.is_file():
        # A cross-source question answered on the pull request: the claim may be used again, backed by the
        # answer source, which must be in run.json with the hash recorded when the answer was saved.
        sources = {s.get("id"): s for s in manifest.get("sources", []) if isinstance(s, dict)}
        try:
            for item in json.loads(resolutions.read_text(encoding="utf-8")):
                source = sources.get(item["source_id"])
                if source and source.get("sha256") == item["sha256"] and item["claim_id"] in blocked:
                    del blocked[item["claim_id"]]
        except (ValueError, KeyError, TypeError) as exc:
            raise GateError(f"cannot read analysis/resolutions.json: {exc}") from None

    flow_backed = _flow_backed(run, manifest) if manifest.get("flow_steps") == "required" else None
    scopes = {src: [] for src in archived}  # an archived article changes no statement: nothing to gate
    edits_file = run / "analysis" / "edits.json"
    if edited and edits_file.is_file():
        report = json.loads(edits_file.read_text(encoding="utf-8")).get("edits", {})
        scopes.update({e["src"]: report.get(e["dest"], {}).get("ranges", [])
                       for e in manifest.get("edits", []) if e.get("action") == "update"})
    return EvidenceRules(known=sorted(known), allowed={k: sorted(v) for k, v in allowed.items()}, blocked=blocked,
                         flow_backed=flow_backed, scopes=scopes)


def _flow_backed(run: Path, manifest: dict) -> list[str]:
    """Claims backed by a flow step that exists: a flow citation in the claim's HANDOVER row (default
    profile) or a flow evidence row (custom profile)."""
    from docforge.evidence.flows import FLOW_CITATION, check_citation, run_flows

    flows, problems = run_flows(run, manifest.get("sources", []))
    if problems:
        raise GateError("; ".join(problems))
    backed: set[str] = set()
    if manifest.get("profile") == "custom":
        rows = json.loads((run / "analysis" / "evidence.json").read_text(encoding="utf-8"))
        for row in rows if isinstance(rows, list) else []:
            if isinstance(row, dict) and row.get("kind") == "flow" and row.get("step") in flows.get(row.get("source_id"), {}):
                backed.add(row["claim_id"])
    else:
        handover = run / "analysis" / "HANDOVER.md"
        for line in handover.read_text(encoding="utf-8").splitlines() if handover.is_file() else []:
            citations = FLOW_CITATION.findall(line)
            if any(fid in flows and check_citation(flows[fid], loc) is None for fid, loc in citations):
                backed |= set(CLAIM_IN_TEXT.findall(line))
    return sorted(backed)


def check_pages(pages: dict[str, str], rules: EvidenceRules, ledger: str = "the coverage ledger") -> GateResult:
    """Gate pages given as {path: markdown}."""
    known, blocked = set(rules.known), rules.blocked
    flow_backed = None if rules.flow_backed is None else set(rules.flow_backed)
    result = GateResult(passed=True, pages=sorted(pages))
    if flow_backed is not None:
        result.flow_steps = result.flow_backed_steps = 0
    for path, text in sorted(pages.items()):
        allowed = set(rules.allowed.get(path, []))
        cited: set[str] = set()
        scope = rules.scopes.get(path)
        for s in statements(text):
            if scope is not None and not any(first <= s.line <= last or s.line <= first <= s.end
                                             for first, last in scope):
                continue  # an edited existing article: only the changed statements are gated
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
                if flow_backed is not None and s.kind == "list" and ORDERED_STEP.match(s.lines[0]):
                    result.flow_steps += 1
                    if flow_backed & set(s.claims):
                        result.flow_backed_steps += 1
                    else:
                        result.errors.append(GateIssue(path=path, line=s.line, message=(
                            f"numbered step is not backed by a flow step (cites {', '.join(s.claims)}): \"{s.snippet}\"")))
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
    edited = [e["src"] for e in manifest.get("edits", []) if e.get("action") == "update"]
    for rel in manifest.get("deliverables", []) + edited:
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
