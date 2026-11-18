"""Typed models for run.json and analysis/evidence.json.

Standard library only, so `python3 scripts/validate_run.py` keeps working
without installing anything. Parsers collect every problem they find instead
of stopping at the first one; filesystem checks (paths, hashes, quotations,
Git lookups) live in `validate.py` and `code.py`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import PurePosixPath
import re
from typing import Any, Optional, Union

CLAIM_ID = re.compile(r"\bC\d+[A-Z]?\b")
SOURCE_ID = re.compile(r"[A-Za-z][\w-]*")
SHA256 = re.compile(r"[0-9a-f]{64}")
COMMIT_SHA = re.compile(r"[0-9a-f]{40}")
REPO_NAME = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
LINE_RANGE = re.compile(r"L(\d+)(?:-L?(\d+))?")


class ClaimClass(str, Enum):
    """The five claim classes used in analysis (see AGENTS.md)."""

    FACT = "FACT"
    ASSUMPTION = "ASSUMPTION"
    INFERENCE = "INFERENCE"
    UNKNOWN = "UNKNOWN"
    CONTRADICTION = "CONTRADICTION"


# Claims of these classes must never appear in reader-facing text as settled.
NOT_INCLUDABLE = frozenset({ClaimClass.UNKNOWN, ClaimClass.CONTRADICTION})


class EvidenceStatus(str, Enum):
    INCLUDED = "included"
    BLOCKED = "blocked"
    DEFERRED = "deferred"
    CONTEXT = "context"


class EvidenceKind(str, Enum):
    QUOTE = "quote"
    CODE = "code"
    FLOW = "flow"


class ReviewMethod(str, Enum):
    INDEPENDENT_REVIEWER = "independent_reviewer"
    SAME_AGENT_SECOND_PASS = "same_agent_second_pass"
    HUMAN_REVIEWER = "human_reviewer"
    NOT_REVIEWED = "not_reviewed"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    NOT_APPLICABLE = "not_applicable"


def _enum(kind, value):
    try:
        return kind(value)
    except ValueError:
        return None


# --- run.json --------------------------------------------------------------


@dataclass(frozen=True)
class Source:
    id: str
    path: Any  # repository-relative path as written; validated against the filesystem later
    sha256: Optional[str]  # None when missing or malformed
    authority: Optional[str] = None


@dataclass(frozen=True)
class Review:
    method: Optional[ReviewMethod]
    source_fidelity: Optional[ReviewStatus]
    product_verification: Optional[ReviewStatus]
    human_approval: Optional[ReviewStatus]


@dataclass(frozen=True)
class RunManifest:
    schema_version: Any
    profile: Any
    audience: Any
    sources: list[Source]
    deliverables: list[Any]
    review: Review


def parse_manifest(data: Any) -> tuple[RunManifest, list[str]]:
    """Check run.json's shape and return the typed manifest plus errors."""
    errors: list[str] = []
    m = data if isinstance(data, dict) else {}
    if not isinstance(data, dict):
        errors.append("run.json must contain an object")
    if m.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if m.get("profile") not in {"default", "custom"}:
        errors.append("profile must be default or custom")
    if not isinstance(m.get("audience"), str) or not m["audience"].strip():
        errors.append("audience is required")

    raw_sources = m.get("sources", [])
    if not isinstance(raw_sources, list) or not raw_sources:
        errors.append("sources must be a nonempty list")
        raw_sources = []
    sources: list[Source] = []
    seen: set[str] = set()
    for entry in raw_sources:
        if not isinstance(entry, dict):
            errors.append("source entry must be an object")
            continue
        sid = entry.get("id")
        if not isinstance(sid, str) or not SOURCE_ID.fullmatch(sid):
            errors.append("invalid source ID")
            continue
        if sid in seen:
            errors.append(f"duplicate source ID {sid}")
            continue
        seen.add(sid)
        sha = entry.get("sha256")
        if not isinstance(sha, str) or not SHA256.fullmatch(sha):
            errors.append(f"{sid}: sha256 is required")
            sha = None
        authority = entry.get("authority")
        sources.append(Source(sid, entry.get("path"), sha, authority if isinstance(authority, str) else None))

    deliverables = m.get("deliverables", [])
    if not isinstance(deliverables, list) or not deliverables:
        errors.append("deliverables must be a nonempty list")
        deliverables = []
    if len(deliverables) != len(set(str(x) for x in deliverables)):
        errors.append("duplicate deliverables")

    raw_review = m.get("review", {})
    if not isinstance(raw_review, dict):
        raw_review = {}
    review = Review(
        method=_enum(ReviewMethod, raw_review.get("method")),
        source_fidelity=_enum(ReviewStatus, raw_review.get("source_fidelity")),
        product_verification=_enum(ReviewStatus, raw_review.get("product_verification")),
        human_approval=_enum(ReviewStatus, raw_review.get("human_approval")),
    )
    if review.method is None:
        errors.append("review.method must identify reviewer method")
    for name in ("source_fidelity", "product_verification", "human_approval"):
        if getattr(review, name) is None:
            errors.append(f"review.{name} has invalid status")
    if review.human_approval is ReviewStatus.PASSED and review.source_fidelity is not ReviewStatus.PASSED:
        errors.append("human approval cannot pass with source fidelity pending or failed")

    manifest = RunManifest(m.get("schema_version"), m.get("profile"), m.get("audience"), sources, deliverables, review)
    return manifest, errors


# --- evidence.json ---------------------------------------------------------


@dataclass(frozen=True)
class QuoteEvidence:
    """An exact quotation from a source listed in run.json."""

    claim_id: str
    status: Optional[EvidenceStatus]
    destinations: Any
    source_id: Any
    quote: Any
    claim_class: Optional[ClaimClass] = None
    kind: EvidenceKind = field(default=EvidenceKind.QUOTE, init=False)


@dataclass(frozen=True)
class CodeEvidence:
    """Lines of a file at a specific commit of a code repository."""

    claim_id: str
    status: Optional[EvidenceStatus]
    destinations: Any
    repo: str
    commit: str
    path: str
    start_line: int
    end_line: int
    excerpt_sha256: str
    claim_class: Optional[ClaimClass] = None
    kind: EvidenceKind = field(default=EvidenceKind.CODE, init=False)

    @property
    def lines(self) -> str:
        if self.start_line == self.end_line:
            return f"L{self.start_line}"
        return f"L{self.start_line}-L{self.end_line}"


@dataclass(frozen=True)
class FlowEvidence:
    """A step of a flow source listed in run.json, with text quoted from that step."""

    claim_id: str
    status: Optional[EvidenceStatus]
    destinations: Any
    source_id: str
    step: int
    quote: str
    claim_class: Optional[ClaimClass] = None
    kind: EvidenceKind = field(default=EvidenceKind.FLOW, init=False)


Evidence = Union[QuoteEvidence, CodeEvidence, FlowEvidence]


def parse_line_range(value: Any) -> Optional[tuple[int, int]]:
    """Parse "L10" or "L10-L24" (also "L10-24"). Returns None if invalid."""
    if not isinstance(value, str):
        return None
    match = LINE_RANGE.fullmatch(value)
    if not match:
        return None
    first = int(match.group(1))
    last = int(match.group(2) or first)
    if first < 1 or last < first:
        return None
    return first, last


def _safe_repo_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value:
        return False
    parts = PurePosixPath(value).parts
    return bool(parts) and ".." not in parts and ":" not in parts[0]


def parse_evidence(data: Any) -> tuple[list[Evidence], list[str]]:
    """Check evidence.json's shape and return typed rows plus errors.

    Rows without "kind" are quote evidence, so existing files stay valid.
    Rows with errors in their kind-specific fields are not returned.
    """
    errors: list[str] = []
    if not isinstance(data, list) or not data:
        return [], ["evidence must be a nonempty array"]
    rows: list[Evidence] = []
    ids: set[Any] = set()
    for index, row in enumerate(data):
        if not isinstance(row, dict):
            errors.append(f"invalid evidence.json: row {index + 1} is not an object")
            continue
        cid = row.get("claim_id")
        if not isinstance(cid, str) or not CLAIM_ID.fullmatch(cid) or cid in ids:
            errors.append(f"invalid or duplicate evidence claim {cid}")
        ids.add(cid)
        status = _enum(EvidenceStatus, row.get("status"))
        if status is None:
            errors.append(f"{cid}: invalid evidence status")
        destinations = row.get("destinations")
        if not isinstance(destinations, list):
            errors.append(f"{cid}: destinations must be a list")

        claim_class = None
        if "claim_class" in row:
            claim_class = _enum(ClaimClass, row.get("claim_class"))
            if claim_class is None:
                errors.append(f"{cid}: invalid claim_class {row.get('claim_class')!r}")
            elif claim_class in NOT_INCLUDABLE and status is EvidenceStatus.INCLUDED:
                errors.append(f"{cid}: {claim_class.value} claim cannot be included")

        kind = row.get("kind", EvidenceKind.QUOTE.value)
        if kind == EvidenceKind.QUOTE.value:
            rows.append(QuoteEvidence(cid, status, destinations, row.get("source_id"), row.get("quote"), claim_class))
        elif kind == EvidenceKind.CODE.value:
            evidence = _parse_code(row, cid, status, destinations, claim_class, errors)
            if evidence is not None:
                rows.append(evidence)
        elif kind == EvidenceKind.FLOW.value:
            source_id, step, quote = row.get("source_id"), row.get("step"), row.get("quote")
            bad = []
            if not isinstance(source_id, str) or not re.fullmatch(r"F[1-9][0-9]{0,2}", source_id):
                bad.append(f"{cid}: flow evidence source_id must be a flow ID such as F1")
            if not isinstance(step, int) or isinstance(step, bool) or step < 1:
                bad.append(f"{cid}: flow evidence step must be a positive whole number")
            if not isinstance(quote, str) or not quote.strip():
                bad.append(f"{cid}: flow evidence needs a quote from the step")
            errors.extend(bad)
            if not bad:
                rows.append(FlowEvidence(cid, status, destinations, source_id, step, quote, claim_class))
        else:
            errors.append(f"{cid}: unknown evidence kind {kind!r}")
    return rows, errors


def _parse_code(row, cid, status, destinations, claim_class, errors) -> Optional[CodeEvidence]:
    before = len(errors)
    repo, commit, path = row.get("repo"), row.get("commit"), row.get("path")
    if not isinstance(repo, str) or not REPO_NAME.fullmatch(repo):
        errors.append(f"{cid}: code evidence repo must be owner/repo")
    if not isinstance(commit, str) or not COMMIT_SHA.fullmatch(commit):
        errors.append(f"{cid}: code evidence commit must be a full 40-character lowercase SHA")
    if not _safe_repo_path(path):
        errors.append(f"{cid}: code evidence path must be relative and stay inside the repository")
    line_range = parse_line_range(row.get("lines"))
    if line_range is None:
        errors.append(f"{cid}: code evidence lines must look like L10 or L10-L24")
    excerpt = row.get("excerpt_sha256")
    if not isinstance(excerpt, str) or not SHA256.fullmatch(excerpt):
        errors.append(f"{cid}: excerpt_sha256 is required")
    if len(errors) != before:
        return None
    return CodeEvidence(cid, status, destinations, repo, commit, path, line_range[0], line_range[1], excerpt, claim_class)
