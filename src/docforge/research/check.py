"""`docforge research check`: verify claims.json, work out statuses, write the report."""

from __future__ import annotations

import json
from pathlib import Path

from docforge.evidence.validate import safe_path

from .claims import check_claims, load_claims
from .cross_source import ClaimResult, evaluate, render_report, update_register
from .packet import ResearchError

CLAIMS = Path("analysis/claims.json")
REPORT = Path("analysis/CROSS-SOURCE.md")
RESULTS = Path("analysis/cross-source.json")
REGISTER = Path("analysis/clarifications-and-assumptions.md")


def _sources(run: Path, repo: Path) -> dict[str, Path]:
    try:
        manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ResearchError(f"cannot read run.json: {exc}") from None
    sources = {}
    for source in manifest.get("sources", []):
        try:
            sources[source["id"]] = safe_path(repo, source["path"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ResearchError(f"run.json has an invalid source: {exc}") from None
    return sources


def research_check(run: Path, repo: Path, code_roots: dict[str, Path] | None = None) -> dict:
    """Check evidence, then write CROSS-SOURCE.md, cross-source.json and the register block.

    Nothing is written when the evidence check finds errors.
    """
    claims = load_claims(run / CLAIMS)
    errors, warnings = check_claims(claims, _sources(run, repo.resolve()), code_roots)
    record: dict = {"errors": errors, "warnings": warnings, "results": [], "written": []}
    if errors:
        return record
    results: list[ClaimResult] = evaluate(claims)
    verified = bool(code_roots) and not any("not verified" in w for w in warnings)
    (run / REPORT).write_text(render_report(results, verified=verified), encoding="utf-8")
    (run / RESULTS).write_text(json.dumps([r.model_dump() for r in results], indent=2) + "\n", encoding="utf-8")
    update_register(run / REGISTER, results)
    record["results"] = [r.model_dump() for r in results]
    record["written"] = [str(REPORT), str(RESULTS), str(REGISTER)]
    return record
