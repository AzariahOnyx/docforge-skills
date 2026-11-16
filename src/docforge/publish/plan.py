"""`docforge publish prepare` and `docforge publish ready`.

prepare: runs the claim gate, places the run's pages (and an evidence
manifest for CI) on a new local suggestion branch, writes the pull request
title and body, and records what the policy allows. It never pushes and never
calls GitHub: it prints the commands a person runs after review.

ready: once the source change is merged, records that the pull request may
leave draft and prints the command for it.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import shlex

from pydantic import BaseModel, Field

from docforge.config import DocForgeConfig

from .branch import BRANCH_PREFIX, PublishError, create_branch
from .gate import EvidenceManifest, GateResult, gate_run, rules_for_run
from .pr_body import default_title, render_body

PUBLISH_DIR = "publish"


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
    out_dir = run / PUBLISH_DIR
    if (out_dir / "pr.json").exists():
        raise PublishError(f"{out_dir / 'pr.json'} already exists; this run was already prepared")
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    target = config.doc_collections.get(collection)
    if target is None:
        raise PublishError(f"doc collection {collection!r} is not in the config")
    if not placements:
        raise PublishError("give at least one --place run-file=docs-path")

    deliverables = set(manifest.get("deliverables", []))
    seen_dest: set[str] = set()
    checked: list[tuple[str, str]] = []
    for src, dest in placements:
        if src not in deliverables:
            raise PublishError(f"{src} is not a deliverable of this run")
        dest = _safe_docs_path(dest)
        if not target.allows(dest):
            raise PublishError(f"{dest} is outside the {collection} filter {target.filter}")
        if dest in seen_dest:
            raise PublishError(f"two pages placed at {dest}")
        seen_dest.add(dest)
        checked.append((src, dest))

    gate: GateResult = gate_run(run)
    if not gate.passed:
        first = gate.errors[0]
        raise PublishError(f"the claim gate failed with {len(gate.errors)} error(s); first: "
                           f"{first.path} line {first.line}: {first.message}")

    # Evidence manifest keyed by published paths, so the docs repo's CI can rerun the gate.
    run_rules = rules_for_run(run)
    by_dest = {dest: run_rules.allowed.get(src, []) for src, dest in checked}
    evidence = EvidenceManifest(run=run.name, rules=run_rules.model_copy(update={"allowed": by_dest}))
    evidence_dest = _manifest_path(target.filter, run.name)
    if not target.allows(evidence_dest):
        raise PublishError(f"evidence manifest path {evidence_dest} is outside the {collection} filter")
    out_dir.mkdir(exist_ok=True)
    evidence_file = out_dir / "evidence-manifest.json"
    evidence_file.write_text(evidence.model_dump_json(indent=2) + "\n", encoding="utf-8")

    source_pr = manifest.get("source_pr")
    draft = not (source_pr and source_pr.get("state") == "merged")
    title = title or default_title(run)
    branch = f"{BRANCH_PREFIX}{run.name}"
    message = f"{title}\n\nPrepared by DocForge from run {run.name}. Proposed for human review; not approved."
    placed = dict(checked)
    pages_dir = out_dir / "pages"
    files: list[tuple[Path, str]] = []
    for src, dest in checked:
        page = pages_dir / dest
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(rewrite_links((run / src).read_text(encoding="utf-8"), src, dest, placed), encoding="utf-8")
        files.append((page, dest))
    result = create_branch(checkout, branch, base, files + [(evidence_file, evidence_dest)], message)
    changes = {c.path: c.change for c in result.changes}
    body = render_body(run, manifest, gate, [(src, dest, changes[dest]) for src, dest in checked],
                       branch=branch, draft=draft, evidence_manifest=evidence_dest)
    body_file = out_dir / "pr-body.md"
    body_file.write_text(body, encoding="utf-8")

    policy = config.resolve_policy(trigger=manifest.get("trigger"), doc_collection=collection)["publishing"]
    action = ("allowed_by_policy_no_github_connection" if policy.get("auto_create_pr")
              else "awaiting_approval")
    create = ["gh", "pr", "create", "--repo", collection, "--base", base, "--head", branch,
              "--title", title, "--body-file", str(body_file)] + (["--draft"] if draft else [])
    plan = PrPlan(
        repo=collection, base=base, branch=branch, commit=result.commit, title=title, draft=draft,
        source_pr=source_pr, policy=policy, action=action,
        files=[c.model_dump() for c in result.changes], gate_passed=gate.passed,
        commands=[shlex.join(["git", "-C", str(checkout), "push", "origin", f"{branch}:{branch}"]), shlex.join(create)],
        history=[{"at": _now(), "event": "prepared", "commit": result.commit, "draft": draft}],
    )
    (out_dir / "pr.json").write_text(plan.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return plan


def mark_ready(run: Path, source_state: str) -> PrPlan:
    path = run / PUBLISH_DIR / "pr.json"
    if not path.is_file():
        raise PublishError(f"{path} not found; run docforge publish prepare first")
    plan = PrPlan.model_validate_json(path.read_text(encoding="utf-8"))
    if source_state != "merged":
        raise PublishError("a docs pull request leaves draft only after its source change is merged")
    if not plan.draft:
        raise PublishError("the pull request is already marked ready")
    plan.draft = False
    if plan.source_pr:
        plan.source_pr = {**plan.source_pr, "state": "merged"}
    plan.commands = [shlex.join(["gh", "pr", "ready", plan.branch, "--repo", plan.repo])]
    plan.history.append({"at": _now(), "event": "source_merged", "draft": False})
    path.write_text(plan.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return plan
