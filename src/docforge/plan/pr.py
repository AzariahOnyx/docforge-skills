"""The plan pull request: `analysis/ia-plan.md` proposed to the docs repository for writer review.

`prepare_plan_pr` checks the plan, commits it to a new local branch `docforge/plan-<slug>` (the checkout's
working tree and current branch are never touched), writes the pull request body and records everything in
`publish/plan-pr.json`. `docforge.publish.open_pr(kind="plan-pr")` pushes it and opens the pull request,
ready for review: approving it approves the plan.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shlex

from docforge.config import DocForgeConfig
from docforge.publish import PrPlan, PublishError, create_branch, save_plan
from docforge.publish.branch import BRANCH_PREFIX
from docforge.publish.plan import PUBLISH_DIR
from docforge.run.stages import IA_PLAN

from .model import IaPlan, plan_slug
from .run import check_run_plan

KIND = "plan-pr"
MAX_BODY = 60000


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def plan_body(plan: IaPlan, run: Path, dest: str) -> str:
    front = plan.front
    lines = [f"> Drafted by DocForge from run `{front.get('docforge_run') or run.name}`. Approving this pull request "
             "approves the plan; DocForge then drafts the articles from the approved version of the file. Edit the "
             f"file in this pull request to add, remove or correct articles. Nothing here is verified against the "
             "live product.", "",
             f"**Plan file:** `{dest}`", "",
             "| Feature | Mode | Product | Category | Owner | Release |", "| --- | --- | --- | --- | --- | --- |",
             "| " + " | ".join(str(front.get(k, "unknown")).replace("|", "\\|") for k in
                              ("feature", "mode", "product", "category", "owner", "release")) + " |", ""]
    if front.get("jira") not in (None, "none"):
        lines += [f"Jira: {front['jira']}", ""]
    lines += ["## Articles", ""]
    for a in plan.articles():
        kind = f"{a['type']}, create" if a["change"] == "create" else a["change"]
        lines.append(f"- **{a['title']}** ({kind}): `{a['path']}`")
    lines += ["", f"## Open questions ({len(plan.questions)})", ""]
    lines += [f"- {q['ID']}: {q['Question']}" for q in plan.questions] or ["None."]
    lines += ["", f"## Spec-versus-code conflicts ({len(plan.conflicts)})", ""]
    lines += [f"- {c['ID']} ({c['Claim']}): {c['Question']}" for c in plan.conflicts] or ["None."]
    lines += ["", "To answer a question, comment with each answer on its own line, for example `Q3: only workspace "
              "admins`, mentioning DocForge. Answers become sources the drafts can cite.", ""]
    body = "\n".join(lines)
    return body if len(body) <= MAX_BODY else body[:MAX_BODY - 40] + "\n\n(Truncated; see the plan file.)\n"


def prepare_plan_pr(*, run: Path, checkout: Path, config: DocForgeConfig, collection: str,
                    base: str = "main") -> PrPlan:
    """Check the run's plan and commit it to a new local branch. Never pushes."""
    run = run.resolve()
    if (run / PUBLISH_DIR / f"{KIND}.json").exists():
        raise PublishError(f"{run / PUBLISH_DIR / (KIND + '.json')} already exists; this plan was already prepared")
    target = config.doc_collections.get(collection)
    if target is None:
        raise PublishError(f"doc collection {collection!r} is not in the config")
    plan, errors = check_run_plan(run, config)
    if errors or plan is None:
        raise PublishError("ia-plan.md has problems: " + "; ".join(errors[:8])
                           + (f" (and {len(errors) - 8} more)" if len(errors) > 8 else ""))
    slug = plan_slug(plan)
    dest = target.plan_path.replace("{slug}", slug)
    branch = f"{BRANCH_PREFIX}plan-{slug}"
    title = f"docs plan: {plan.front['feature']} (DocForge)"
    message = f"{title}\n\nIA plan drafted by DocForge from run {run.name}. Proposed for writer review; not approved."
    result = create_branch(checkout, branch, base, [(run / IA_PLAN, dest)], message)
    (run / PUBLISH_DIR).mkdir(exist_ok=True)
    (run / PUBLISH_DIR / f"{KIND}-body.md").write_text(plan_body(plan, run, dest), encoding="utf-8")
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    policy = config.resolve_policy(trigger=manifest.get("trigger"), doc_collection=collection)["publishing"]
    record = PrPlan(
        repo=collection, base=base, branch=branch, commit=result.commit, title=title, draft=False,
        policy=policy, action="awaiting_approval", files=[c.model_dump() for c in result.changes], gate_passed=True,
        commands=[f"docforge plan open {shlex.quote(str(run.name))} --docs-checkout <docs-checkout>"],
        history=[{"at": _now(), "event": "prepared", "commit": result.commit}], base_commit=result.base_commit,
        placements=[{"src": IA_PLAN, "dest": dest}],
    )
    save_plan(run, record, KIND)
    return record
