"""`docforge run status` and `docforge run check`."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

from docforge.evidence import validate

from .stages import Stage, stage_outputs, stages_for
from .start import RunError

MIN_CHARS = 100  # same threshold check_outputs.py uses for "appears incomplete"


def load_manifest(out: Path) -> dict:
    path = out / "run.json"
    if not path.is_file():
        raise RunError(f"not a run folder (no run.json): {out}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise RunError(f"invalid run.json: {exc}") from None
    if manifest.get("profile") not in {"default", "custom"} or not isinstance(manifest.get("deliverables"), list):
        raise RunError("run.json needs a default or custom profile and a deliverables list")
    return manifest


@dataclass
class StageStatus:
    stage: Stage
    done: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not self.missing


def run_status(out: Path) -> list[StageStatus]:
    manifest = load_manifest(out)
    statuses = []
    for stage in stages_for(manifest):
        status = StageStatus(stage)
        for rel in stage_outputs(stage, manifest["profile"], manifest["deliverables"]):
            path = out / rel
            ok = path.is_file() and len(path.read_text(encoding="utf-8").strip()) >= (
                1 if rel.endswith(".json") else MIN_CHARS
            )
            (status.done if ok else status.missing).append(rel)
        statuses.append(status)
    return statuses


def next_stage(statuses: list[StageStatus]) -> StageStatus | None:
    return next((s for s in statuses if not s.complete), None)


# The checker scripts ship with DocForge itself (src/docforge/run/status.py -> repo root),
# independent of the repository that holds a run's sources.
TOOLS_ROOT = Path(__file__).resolve().parents[3]


def _script(name: str, *args: str) -> subprocess.CompletedProcess:
    script = TOOLS_ROOT / "scripts" / name
    if not script.is_file():
        raise RunError(f"missing {script}; DocForge's scripts/ folder is not available")
    return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, check=False)


def run_checks(out: Path, repo: Path, code_roots: dict[str, Path] | None = None) -> dict:
    """Run the structural checker for the run's profile plus the Markdown lint.

    Writes qa/checks.json (replacing any earlier check record) and returns it.
    Structural checks only: they are not source review or publication approval.
    """
    manifest = load_manifest(out)
    if manifest["profile"] == "default":
        result = _script("check_outputs.py", str(out))
        lines = result.stdout.splitlines()
        structural = {
            "checker": "scripts/check_outputs.py",
            "passed": result.returncode == 0,
            "errors": [l[len("FAIL: "):] for l in lines if l.startswith("FAIL: ")],
            "warnings": [l[len("WARNING: "):] for l in lines if l.startswith("WARNING: ")],
        }
    else:
        errors, warnings = validate(out.resolve(), repo.resolve())
        structural = {"checker": "docforge.evidence.validate", "passed": not errors,
                      "errors": errors, "warnings": warnings}

    docs = [str(out / d) for d in manifest["deliverables"] if (out / d).is_file()]
    findings: list[str] = []
    if docs:
        lint = _script("lint_docs.py", *docs)
        prefix = str(out.resolve()) + "/"
        findings = [l.replace(str(out) + "/", "").replace(prefix, "") for l in lint.stdout.splitlines()
                    if ": " in l and not l.endswith("Human review is still required.")]
    research = None
    if manifest.get("code"):
        from docforge.research import ResearchError, research_check

        try:
            result = research_check(out, repo, code_roots)
            research = {"passed": not result["errors"], "errors": result["errors"], "warnings": result["warnings"],
                        "statuses": {r["claim_id"]: r["status"] for r in result["results"]}}
        except ResearchError as exc:
            research = {"passed": False, "errors": [str(exc)], "warnings": [], "statuses": {}}
    vale = vale_summary(out)
    record = {
        "checked_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "profile": manifest["profile"],
        "structural": structural,
        "lint_findings": findings,
        "research": research,
        "vale": vale,
        "note": "Structural and editorial checks only. Source fidelity review and human approval are separate.",
    }
    (out / "qa").mkdir(exist_ok=True)
    (out / "qa" / "checks.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def vale_summary(out: Path) -> dict:
    """Vale on changed prose. Error-level alerts fail the check; Vale missing is reported, not fatal."""
    from docforge.lint import LintError, lint_run

    try:
        result = lint_run(out)
    except LintError as exc:
        return {"available": False, "passed": True, "note": str(exc), "counts": {}, "alerts": []}
    counts = result.counts
    return {"available": True, "passed": counts.get("error", 0) == 0, "counts": counts,
            "unchanged_alerts": result.unchanged_alerts,
            "alerts": [f"{a.page}:{a.line}:{a.start} {a.severity} {a.check}: {a.message}" for a in result.alerts]}
