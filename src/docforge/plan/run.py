"""Check a run's `analysis/ia-plan.md` against the run's pack and doc collection."""

from __future__ import annotations

import json
from pathlib import Path

from docforge.run.stages import IA_PLAN

from .model import IaPlan, read_plan


def run_plan_types(run: Path) -> list[str] | None:
    """The article types the run's pack defines, or None (the default types) without a pack."""
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    record = manifest.get("pack")
    if not record:
        return None
    from docforge.packs import PackError, run_manifest

    try:
        pack = run_manifest(run, record)
    except PackError:
        return None
    return [s.type for s in pack.article_specs] or None


def check_run_plan(run: Path, config=None, *, path: str = IA_PLAN) -> tuple[IaPlan | None, list[str]]:
    """(plan, problems). With a config, docs paths are checked against the run's doc collection filter."""
    file = run / path
    if not file.is_file():
        return None, [f"{path} is missing"]
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    allows = None
    collection = (manifest.get("publish") or {}).get("collection")
    if config is not None and collection in config.doc_collections:
        allows = config.doc_collections[collection].allows
    return read_plan(file.read_text(encoding="utf-8"), types=run_plan_types(run), allows=allows)
