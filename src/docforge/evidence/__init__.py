"""Evidence core: run.json and evidence.json models, claim classes, validation.

Standard library only, so the scripts in scripts/ run with plain python3.
"""
from .code import excerpt_sha256, verify_code_evidence
from .models import (
    ClaimClass,
    CodeEvidence,
    Evidence,
    EvidenceKind,
    EvidenceStatus,
    FlowEvidence,
    QuoteEvidence,
    Review,
    ReviewMethod,
    ReviewStatus,
    RunManifest,
    Source,
    parse_evidence,
    parse_line_range,
    parse_manifest,
)
from .validate import validate

__all__ = [
    "ClaimClass",
    "CodeEvidence",
    "Evidence",
    "EvidenceKind",
    "EvidenceStatus",
    "FlowEvidence",
    "QuoteEvidence",
    "Review",
    "ReviewMethod",
    "ReviewStatus",
    "RunManifest",
    "Source",
    "excerpt_sha256",
    "parse_evidence",
    "parse_line_range",
    "parse_manifest",
    "validate",
    "verify_code_evidence",
]
