"""`docforge publish prepare | update | ready`.

prepare: runs the claim gate, places the run's pages (and an evidence
manifest for CI) on a new local suggestion branch, writes the pull request
title and body, and records what the policy allows.

update: after a revision, re-runs the gate and adds a follow-up commit to the
same suggestion branch, only if no one else moved it.

ready: once the source change is merged, records that the pull request may
leave draft.

None of these push or call GitHub. Stored commands use the placeholders
<docs-checkout> and <run>, so run files never hold local paths;
`resolve_commands` fills them in for printing.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import shlex

from pydantic import BaseModel, Field

from docforge.config import DocCollection, DocForgeConfig

from .branch import BRANCH_PREFIX, PublishError, create_branch, diff_commits, update_branch
from .gate import EvidenceManifest, GateResult, gate_run, rules_for_run
from .pr_body import default_title, render_body

PUBLISH_DIR = "publish"
CHECKOUT = "<docs-checkout>"
RUN = "<run>"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class PrPlan(BaseModel):
    repo: str
    base: str
    branch: str
    commit: str
    title: str
    draft: bool
    source_pr: dict | None = None
    policy: dict
    action: str
    files: list[dict]
    gate_passed: bool
    commands: list[str]
    history: list[dict] = Field(default_factory=list)
    base_commit: str = ""
    placements: list[dict] = Field(default_factory=list)
    # open, changes_requested, revised, closed
    status: str = "open"
    revision: int = 0


def load_plan(run: Path) -> PrPlan:
    path = run / PUBLISH_DIR / "pr.json"
    if not path.is_file():
        raise PublishError(f"{path} not found; run docforge publish prepare first")
    return PrPlan.model_validate_json(path.read_text(encoding="utf-8"))


def save_plan(run: Path, plan: PrPlan) -> None:
    (run / PUBLISH_DIR / "pr.json").write_text(plan.model_dump_json(indent=2) + "\n", encoding="utf-8")


def resolve_commands(commands: list[str], *, run: Path, checkout: Path | None = None) -> list[str]:
    resolved = []
    for command in commands:
        command = command.replace(RUN, shlex.quote(str(run)))
        if checkout is not None:
            command = command.replace(CHECKOUT, shlex.quote(str(checkout)))
        resolved.append(command)
    return resolved


def _push_command(branch: str) -> str:
    return f"git -C {CHECKOUT} push origin {shlex.quote(f'{branch}:{branch}')}"


def _safe_docs_path(path: str) -> str:
    parts = PurePosixPath(path).parts
    if not path or path.startswith("/") or ".." in parts or "\\" in path:
        raise PublishError(f"docs path must be relative and stay inside the repository: {path!r}")
    return PurePosixPath(path).as_posix()


LINK_RE = re.compile(r"(?<!!)(\[[^\]]*\]\()([^)\s]+)(\))")


def _normalize(path: str) -> str | None:
    out: list[str] = []
    for part in PurePosixPath(path).parts:
        if part in ("", "."):
            continue
        if part == "..":
            if not out:
                return None
            out.pop()
        else:
            out.append(part)
    return "/".join(out)


def rewrite_links(text: str, src: str, dest: str, placed: dict[str, str]) -> str:
    """Point links between placed pages at their new docs paths."""
    def fix(match: re.Match) -> str:
        target = match.group(2)
        if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:|^#|^/", target):
            return match.group(0)
        path, _, anchor = target.partition("#")
        resolved = _normalize(str(PurePosixPath(src).parent / path))
        if resolved not in placed:
            return match.group(0)
        new = posixpath.relpath(placed[resolved], posixpath.dirname(dest) or ".")
        return match.group(1) + new + (f"#{anchor}" if anchor else "") + match.group(3)
    return LINK_RE.sub(fix, text)


def _manifest_path(filters: list[str], slug: str) -> str:
    folder = next((f for f in filters if f.endswith("/")), "")
    return f"{folder}_docforge/{slug}.evidence.json"


def _check_placements(manifest: dict, target: DocCollection, collection: str,
                      placements: list[tuple[str, str]]) -> list[tuple[str, str]]:
    if not placements:
        raise PublishError("give at least one --place run-file=docs-path")
    deliverables = set(manifest.get("deliverables", []))
    seen: set[str] = set()
    checked = []
    for src, dest in placements:
        if src not in deliverables:
            raise PublishError(f"{src} is not a deliverable of this run")
        dest = _safe_docs_path(dest)
        if not target.allows(dest):
            raise PublishError(f"{dest} is outside the {collection} filter {target.filter}")
        if dest in seen:
            raise PublishError(f"two pages placed at {dest}")
        seen.add(dest)
        checked.append((src, dest))
    return checked


def _gate_or_fail(run: Path) -> GateResult:
    gate = gate_run(run)
    if not gate.passed:
        first = gate.errors[0]
        raise PublishError(f"the claim gate failed with {len(gate.errors)} error(s); first: "
                           f"{first.path} line {first.line}: {first.message}")
    return gate


def _stage_files(run: Path, checked: list[tuple[str, str]], target: DocCollection,
                 collection: str) -> tuple[list[tuple[Path, str]], str]:
    """Write placed pages and the evidence manifest under publish/; return (files, manifest path)."""
    out_dir = run / PUBLISH_DIR
    run_rules = rules_for_run(run)
    by_dest = {dest: run_rules.allowed.get(src, []) for src, dest in checked}
    evidence = EvidenceManifest(run=run.name, rules=run_rules.model_copy(update={"allowed": by_dest}))
    evidence_dest = _manifest_path(target.filter, run.name)
    if not target.allows(evidence_dest):
        raise PublishError(f"evidence manifest path {evidence_dest} is outside the {collection} filter")
    out_dir.mkdir(exist_ok=True)
    evidence_file = out_dir / "evidence-manifest.json"
    evidence_file.write_text(evidence.model_dump_json(indent=2) + "\n", encoding="utf-8")
    placed = dict(checked)
    files: list[tuple[Path, str]] = []
    for src, dest in checked:
        page = out_dir / "pages" / dest
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(rewrite_links((run / src).read_text(encoding="utf-8"), src, dest, placed), encoding="utf-8")
        files.append((page, dest))
    return files + [(evidence_file, evidence_dest)], evidence_dest


def _write_body(run: Path, manifest: dict, gate: GateResult, checked, changes: dict[str, str], *,
                branch: str, draft: bool, evidence_dest: str) -> None:
    body = render_body(run, manifest, gate, [(src, dest, changes.get(dest, "modified")) for src, dest in checked],
                       branch=branch, draft=draft, evidence_manifest=evidence_dest)
    (run / PUBLISH_DIR / "pr-body.md").write_text(body, encoding="utf-8")


def prepare_publish(
    *,
    run: Path,
    checkout: Path,
    config: DocForgeConfig,
    collection: str,
    placements: list[tuple[str, str]],
    base: str = "main",
    title: str | None = None,
) -> PrPlan:
    run = run.resolve()
    if (run / PUBLISH_DIR / "pr.json").exists():
        raise PublishError(f"{run / PUBLISH_DIR / 'pr.json'} already exists; this run was already prepared")
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    target = config.doc_collections.get(collection)
    if target is None:
        raise PublishError(f"doc collection {collection!r} is not in the config")
    checked = _check_placements(manifest, target, collection, placements)
    gate = _gate_or_fail(run)
    files, evidence_dest = _stage_files(run, checked, target, collection)

    source_pr = manifest.get("source_pr")
    draft = not (source_pr and source_pr.get("state") == "merged")
    title = title or default_title(run)
    branch = f"{BRANCH_PREFIX}{run.name}"
    message = f"{title}\n\nPrepared by DocForge from run {run.name}. Proposed for human review; not approved."
    result = create_branch(checkout, branch, base, files, message)
    _write_body(run, manifest, gate, checked, {c.path: c.change for c in result.changes},
                branch=branch, draft=draft, evidence_dest=evidence_dest)
    (run / PUBLISH_DIR / "changes.diff").write_text(diff_commits(checkout, result.base_commit, result.commit),
                                                    encoding="utf-8")

    policy = config.resolve_policy(trigger=manifest.get("trigger"), doc_collection=collection)["publishing"]
    action = ("allowed_by_policy_no_github_connection" if policy.get("auto_create_pr")
              else "awaiting_approval")
    create = shlex.join(["gh", "pr", "create", "--repo", collection, "--base", base, "--head", branch,
                         "--title", title]) + f" --body-file {RUN}/publish/pr-body.md" + (" --draft" if draft else "")
    plan = PrPlan(
        repo=collection, base=base, branch=branch, commit=result.commit, title=title, draft=draft,
        source_pr=source_pr, policy=policy, action=action,
        files=[c.model_dump() for c in result.changes], gate_passed=gate.passed,
        commands=[_push_command(branch), create],
        history=[{"at": _now(), "event": "prepared", "commit": result.commit, "draft": draft}],
        base_commit=result.base_commit, placements=[{"src": s, "dest": d} for s, d in checked],
    )
    save_plan(run, plan)
    return plan


def update_publish(*, run: Path, checkout: Path, config: DocForgeConfig) -> PrPlan:
    """Commit a revised run to its existing suggestion branch."""
    run = run.resolve()
    plan = load_plan(run)
    if plan.status == "closed":
        raise PublishError("this suggestion is closed; start a new run instead")
    if not plan.placements:
        raise PublishError("pr.json has no recorded placements; prepare it again with this DocForge version")
    target = config.doc_collections.get(plan.repo)
    if target is None:
        raise PublishError(f"doc collection {plan.repo!r} is not in the config")
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    checked = _check_placements(manifest, target, plan.repo, [(p["src"], p["dest"]) for p in plan.placements])
    gate = _gate_or_fail(run)
    files, evidence_dest = _stage_files(run, checked, target, plan.repo)
    revision = plan.revision + 1
    message = f"{plan.title} (revision {revision})\n\nRevised by DocForge after review feedback on run {run.name}."
    result = update_branch(checkout, plan.branch, plan.commit, files, message)

    plan.commit, plan.revision = result.commit, revision
    plan.gate_passed = gate.passed
    plan.status = "revised"
    plan.commands = [_push_command(plan.branch)]
    plan.history.append({"at": _now(), "event": "updated", "commit": result.commit, "revision": revision,
                         "files": [c.path for c in result.changes]})
    _write_body(run, manifest, gate, checked, {p["path"]: p["change"] for p in plan.files},
                branch=plan.branch, draft=plan.draft, evidence_dest=evidence_dest)
    if plan.base_commit:
        (run / PUBLISH_DIR / "changes.diff").write_text(diff_commits(checkout, plan.base_commit, result.commit),
                                                        encoding="utf-8")
    save_plan(run, plan)
    return plan


def mark_ready(run: Path, source_state: str) -> PrPlan:
    plan = load_plan(run)
    if source_state != "merged":
        raise PublishError("a docs pull request leaves draft only after its source change is merged")
    if plan.status == "closed":
        raise PublishError("this suggestion is closed")
    if not plan.draft:
        raise PublishError("the pull request is already marked ready")
    plan.draft = False
    if plan.source_pr:
        plan.source_pr = {**plan.source_pr, "state": "merged"}
    plan.commands = [shlex.join(["gh", "pr", "ready", plan.branch, "--repo", plan.repo])]
    plan.history.append({"at": _now(), "event": "source_merged", "draft": False})
    save_plan(run, plan)
    return plan
