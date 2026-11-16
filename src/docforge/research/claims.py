"""analysis/claims.json: each claim's PRD evidence and code evidence.

The research stage writes this file. `check_claims` verifies it: every PRD
quote must appear in its run.json source, and every code citation must match
a local checkout when one is supplied (otherwise it is reported as not
verified). Judging what the code means is the researcher's job; this module
only checks that the cited evidence exists as cited.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from docforge.evidence.code import is_git_checkout, verify_code_evidence
from docforge.evidence.models import CLAIM_ID, CodeEvidence, parse_line_range

from .packet import ResearchError

Relation = Literal["supports", "contradicts", "context"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PrdEvidence(Strict):
    source_id: str
    quote: str = Field(min_length=1)


class CodeCitation(Strict):
    repo: str = Field(pattern=r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
    commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    path: str = Field(min_length=1)
    lines: str
    excerpt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    relation: Relation
    note: str | None = None

    @field_validator("path")
    @classmethod
    def _relative(cls, value: str) -> str:
        if value.startswith("/") or ".." in value.split("/") or "\\" in value:
            raise ValueError("path must be relative and stay inside the repository")
        return value

    @field_validator("lines")
    @classmethod
    def _lines(cls, value: str) -> str:
        if parse_line_range(value) is None:
            raise ValueError("lines must look like L10 or L10-L24")
        return value

    def as_evidence(self, claim_id: str) -> CodeEvidence:
        first, last = parse_line_range(self.lines)
        return CodeEvidence(claim_id, None, [], self.repo, self.commit, self.path, first, last, self.excerpt_sha256)


class Claim(Strict):
    claim_id: str
    statement: str = Field(min_length=1)
    prd: list[PrdEvidence] = Field(default_factory=list)
    code: list[CodeCitation] = Field(default_factory=list)
    # A question the code cannot answer (for example, behaviour owned by another service).
    needs_engineering: str | None = None

    @field_validator("claim_id")
    @classmethod
    def _claim_id(cls, value: str) -> str:
        if not CLAIM_ID.fullmatch(value):
            raise ValueError("claim_id must look like C01 or C12A")
        return value


class ClaimsFile(Strict):
    schema_version: Literal[1]
    claims: list[Claim] = Field(min_length=1)


def load_claims(path: Path) -> ClaimsFile:
    if not path.is_file():
        raise ResearchError(f"missing {path.name}; the research stage writes it")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return ClaimsFile.model_validate(data)
    except ValueError as exc:
        if isinstance(exc, ValidationError):
            lines = [f"{path.name} is invalid:"]
            for err in exc.errors():
                loc = ".".join(str(p) for p in err["loc"]) or "(root)"
                lines.append(f"  - {loc}: {err['msg']}")
            raise ResearchError("\n".join(lines)) from None
        raise ResearchError(f"{path.name} is not valid JSON: {exc}") from None


def _normalize(text: str) -> str:
    return " ".join(text.split()).casefold()


def check_claims(
    claims: ClaimsFile, sources: dict[str, Path], code_roots: dict[str, Path] | None = None
) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for the evidence cited in claims.json."""
    errors: list[str] = []
    warnings: list[str] = []
    roots = {k.casefold(): Path(v) for k, v in (code_roots or {}).items()}
    checked_roots: dict[str, bool] = {}
    texts: dict[str, str] = {}
    seen: set[str] = set()
    for claim in claims.claims:
        cid = claim.claim_id
        if cid in seen:
            errors.append(f"duplicate claim {cid}")
        seen.add(cid)
        for prd in claim.prd:
            if prd.source_id not in sources:
                errors.append(f"{cid}: unknown source {prd.source_id}")
                continue
            if prd.source_id not in texts:
                texts[prd.source_id] = _normalize(sources[prd.source_id].read_text(encoding="utf-8"))
            if _normalize(prd.quote) not in texts[prd.source_id]:
                errors.append(f"{cid}: quotation not found in {prd.source_id}")
        for citation in claim.code:
            key = citation.repo.casefold()
            root = roots.get(key)
            if root is None:
                warnings.append(f"{cid}: code evidence not verified (no local checkout for {citation.repo})")
                continue
            if key not in checked_roots:
                checked_roots[key] = is_git_checkout(root)
                if not checked_roots[key]:
                    errors.append(f"code root for {citation.repo} is not a Git checkout")
            if checked_roots[key]:
                errors.extend(verify_code_evidence(citation.as_evidence(cid), root))
    return errors, warnings
