"""Documentation runs: start a run, track its stages, and check the result."""

from .stages import DEFAULT_DELIVERABLES, RESEARCH, STAGES, Stage, stage_outputs, stages_for
from .start import BACKEND, RunError, add_sources, start_run
from .status import StageStatus, load_manifest, next_stage, run_checks, run_status

__all__ = [
    "add_sources",
    "BACKEND",
    "DEFAULT_DELIVERABLES",
    "RunError",
    "RESEARCH",
    "STAGES",
    "Stage",
    "StageStatus",
    "load_manifest",
    "next_stage",
    "run_checks",
    "run_status",
    "stage_outputs",
    "stages_for",
    "start_run",
]
