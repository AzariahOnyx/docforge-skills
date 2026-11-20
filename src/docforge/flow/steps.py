"""The steps of a documentation run that every route shares.

- `stage_done` / `run_stages`: run the next stages through the API backend, or report that a Claude Code
  session must do them ("waiting").
- `propose_plan_pr`: check ia-plan.md, prepare the plan pull request, and open it when `auto_create_pr`
  allows.
- `publish_drafts`: prepare the drafts pull request (at the approved plan's docs paths when there is one),
  open it when the policy allows, and tell the plan pull request where the drafts are.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from docforge.config import DocForgeConfig


class FlowError(Exception):
    """A shared step cannot go on (a broken plan file, a pull request that cannot be prepared)."""


def stage_done(run: Path, number: int) -> bool:
    from docforge.run import run_status

    return next(s for s in run_status(run) if s.stage.number == number).complete


def run_stages(run: Path, workspace: Path, config: DocForgeConfig, only: int | None, backend_client) -> str:
    """'done', 'waiting' (no backend: a session must do the stage) or an error message."""
    if config.backend is None:
        return "waiting"
    from docforge.backend import BackendError, exec_run

    try:
        outcomes = exec_run(run, workspace, config, only=only, repair=1, client=backend_client)
    except BackendError as exc:
        return str(exc)
    failed = [o for o in outcomes if o.status == "failed"]
    return f"{failed[0].stage}: {failed[0].message}" if failed else "done"


@dataclass
class Proposed:
    record: object  # PrPlan of the plan pull request
    plan: object  # IaPlan
    prepared: bool  # prepared now (not found from an earlier call)
    opened: bool  # opened now


def propose_plan_pr(run: Path, config: DocForgeConfig, *, collection: str, checkout: Path, base: str,
                    trigger: str | None, client=None) -> Proposed:
    from docforge.plan import check_run_plan
    from docforge.plan.pr import prepare_plan_pr
    from docforge.publish import PublishError, load_plan, open_pr

    plan, errors = check_run_plan(run, config)
    if errors:
        raise FlowError("ia-plan.md has problems: " + "; ".join(errors[:5]))
    prepared = opened = False
    try:
        if (run / "publish" / "plan-pr.json").is_file():
            record = load_plan(run, "plan-pr")
        else:
            record = prepare_plan_pr(run=run, checkout=checkout, config=config, collection=collection, base=base)
            prepared = True
        policy = config.resolve_policy(trigger=trigger, doc_collection=collection)["publishing"]
        if policy.get("auto_create_pr") and record.pr_number is None:
            record = open_pr(run=run, checkout=checkout, config=config, client=client, kind="plan-pr")
            opened = True
    except PublishError as exc:
        raise FlowError(f"the plan pull request could not be prepared: {exc}") from None
    return Proposed(record, plan, prepared, opened)


@dataclass
class Published:
    record: object | None  # PrPlan of the drafts pull request
    prepared: bool
    opened: bool
    error: str | None = None


def publish_drafts(run: Path, config: DocForgeConfig, *, collection: str, checkout: Path, base: str, slug: str,
                   trigger: str | None, client=None) -> Published:
    """Never raises for publishing problems: a failure never undoes the drafts, it is reported."""
    from docforge.publish import PublishError, load_plan, open_pr, prepare_publish, save_plan

    prepared = False
    try:
        if (run / "publish" / "pr.json").is_file():
            record = load_plan(run)
        else:
            approved = json.loads((run / "run.json").read_text(encoding="utf-8")).get("approved_plan") or {}
            placements = [(p["src"], p["dest"]) for p in approved.get("placements", [])]
            record = prepare_publish(run=run, checkout=checkout, config=config, collection=collection,
                                     placements=placements, base=base, slug=slug)
            prepared = True
        policy = config.resolve_policy(trigger=trigger, doc_collection=collection)["publishing"]
        if not policy.get("auto_create_pr"):
            return Published(record, prepared, False)
        record = open_pr(run=run, checkout=checkout, config=config, client=client)
    except PublishError as exc:
        return Published(None, prepared, False, str(exc))
    if (run / "publish" / "plan-pr.json").is_file():
        from docforge.github.docs_pr import reply

        plan_record = load_plan(run, "plan-pr")
        reply(run, plan_record, config, "drafts", f"The drafts for this plan are in {record.pr_url}.", client)
        save_plan(run, plan_record)
    return Published(record, prepared, True)


def outdated_step(run: Path, workspace: Path, config: DocForgeConfig, *, collection: str, docs: Path | None,
                  code_checkout: Path | None = None, spec_paths=(), client=None) -> str:
    """The outdated content finder before the plan pull request: 'skip' (not switched on for the doc
    collection, or no docs checkout), 'done', 'waiting' (two session passes) or an error message."""
    target = config.doc_collections.get(collection)
    if target is None or not target.find_outdated or docs is None or not docs.is_dir():
        return "skip"
    from docforge.outdated import find_outdated

    try:
        return find_outdated(run, workspace, config, docs=docs, collection=collection, code_checkout=code_checkout,
                             spec_paths=spec_paths, client=client)
    except (OSError, ValueError) as exc:
        return f"outdated content finder: {exc}"


def apply_edits(run: Path) -> list[str]:
    """Apply and check the paragraph-level fixes to existing articles, if the run has any. Problems, or []."""
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    if not manifest.get("edits"):
        return []
    from docforge.outdated.fix import apply_fixes

    return apply_fixes(run)["problems"]
