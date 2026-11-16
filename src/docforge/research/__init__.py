"""Research: changed-code packets, claims.json checks and PRD-vs-code statuses."""

from .check import research_check
from .claims import Claim, ClaimsFile, CodeCitation, PrdEvidence, check_claims, load_claims
from .cross_source import BLOCK_END, BLOCK_START, ClaimResult, classify, evaluate, render_report, update_register
from .packet import CodeRef, Packet, ResearchError, build_packet, code_ref

__all__ = [
    "BLOCK_END",
    "BLOCK_START",
    "Claim",
    "ClaimResult",
    "ClaimsFile",
    "CodeCitation",
    "CodeRef",
    "Packet",
    "PrdEvidence",
    "ResearchError",
    "build_packet",
    "check_claims",
    "classify",
    "code_ref",
    "evaluate",
    "load_claims",
    "render_report",
    "research_check",
    "update_register",
]
