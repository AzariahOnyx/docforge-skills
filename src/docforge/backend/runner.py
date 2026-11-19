"""`docforge run exec`: run a documentation run's stages through the Anthropic API.

Safety:
- no paid call without a `backend:` section in docforge.yaml;
- `--dry-run` writes each stage's assembled request and a cost estimate, and calls nothing;
- before each call, the run's recorded spend plus the call's worst case must stay
  within backend.max_cost_usd, or the run stops;
- a stage whose outputs already exist is not re-run;
- the model writes only the stage's output paths, inside the run folder.

Every call is recorded in <run>/backend/calls.jsonl (no prompt text, no credentials),
and run.json gets running totals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path

from docforge.config import Backend, DocForgeConfig
from docforge.run.stages import Stage, stages_for
from docforge.run.status import run_checks

from .client import BackendError, CallResult, call, make_client, request_params
from .context import ContextError, StageRequest, build_request
from .costs import PRICES_AS_OF, estimate_upper_bound, usage_cost

BACKEND_DIR = "backend"
CALLS = "calls.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class StageOutcome:
    stage: str
    status: str  # done, dry_run, failed, skipped
    files: list[str] = field(default_factory=list)
    calls: int = 0
    cost_usd: float = 0.0
    estimate_usd: float | None = None
    message: str = ""
    notes: str = ""


def _settings(backend: Backend, stage: Stage) -> tuple[str, str, int]:
    override = backend.stages.get(stage.key)
    return ((override.model if override and override.model else backend.model),
            (override.effort if override and override.effort else backend.effort),
            (override.max_tokens if override and override.max_tokens else backend.max_tokens))


def recorded_calls(run: Path) -> list[dict]:
    path = run / BACKEND_DIR / CALLS
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def spent(run: Path) -> float:
    return round(sum(c.get("cost_usd") or 0.0 for c in recorded_calls(run)), 6)


def _cost(result: CallResult, backend: Backend) -> float | None:
    """Per attempt when the API reports iterations (fallback attempts bill at their own model's rates)."""
    if result.iterations:
        total = 0.0
        for item in result.iterations:
            cost = usage_cost(item, item.get("model") or result.model_served, backend.prices)
            if cost is None:
                return None
            total += cost
        return total
    return usage_cost(result.usage, result.model_served, backend.prices)


def _record(run: Path, entry: dict) -> None:
    folder = run / BACKEND_DIR
    folder.mkdir(exist_ok=True)
    with (folder / CALLS).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")
    manifest_path = run / "run.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    calls = recorded_calls(run)
    manifest["backend"] = {
        "provider": "anthropic-api",
        "calls": len(calls),
        "cost_usd": round(sum(c.get("cost_usd") or 0.0 for c in calls), 4),
        "models": sorted({c["model_served"] for c in calls if c.get("model_served")}),
        "prices_as_of": PRICES_AS_OF,
        "note": "Costs are estimates from token usage; the provider's bill is authoritative.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _write_files(run: Path, request: StageRequest, data: dict, *, require_all: bool = True) -> list[str]:
    seen: dict[str, str] = {}
    for item in data.get("files", []):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("content"), str):
            raise BackendError("a files entry is not a path and content")
        if item["path"] not in request.outputs:
            raise BackendError(f"the answer names a file this stage may not write: {item['path']}")
        if item["path"] in seen:
            raise BackendError(f"the answer names {item['path']} twice")
        if not item["content"].strip():
            raise BackendError(f"the answer left {item['path']} empty")
        seen[item["path"]] = item["content"]
    missing = [p for p in request.outputs if p not in seen] if require_all else ([] if seen else ["any file"])
    if missing:
        raise BackendError(f"the answer is missing: {', '.join(missing)}")
    root = run.resolve()
    for rel, content in seen.items():
        target = (run / rel).resolve()
        if not target.is_relative_to(root):
            raise BackendError(f"refused to write outside the run: {rel}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")
    return sorted(seen)


def _checks(run: Path, repo: Path, stage: Stage, manifest: dict) -> list[str]:
    """Problems the engine finds after a stage; empty means the stage passed its checks."""
    problems: list[str] = []
    if (stage.key == "drafter" and manifest.get("publish")) or stage.key == "revise":
        from docforge.publish.gate import gate_run

        result = gate_run(run)
        problems += [f"claim gate: {e.path}:{e.line} {e.message}" for e in result.errors]
    if stage.key == "analyzer" and manifest.get("ia_plan"):
        from docforge.plan import check_run_plan

        problems += [f"ia-plan.md: {e}" for e in check_run_plan(run)[1]]
    if stage.key == "proofreader":
        record = run_checks(run, repo)
        problems += [f"structural check: {e}" for e in record["structural"]["errors"]]
    return problems


def _cleanup(run: Path) -> list[str]:
    """Apply the pack's clean-up steps after drafting; a gate failure comes back as a problem to repair."""
    from docforge.cleanup import CleanupError, apply_cleanup, plan_cleanup

    try:
        result = plan_cleanup(run)
        if result.steps:
            apply_cleanup(run, result)
    except CleanupError as exc:
        return [f"clean-up: {exc}"]
    return []


def _mark_independent_review(run: Path) -> None:
    path = run / "run.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    review = manifest.setdefault("review", {})
    # A separate API call with a fresh context: it sees the drafts, not the drafter's reasoning.
    review["method"] = "independent_reviewer"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _dry_run(run: Path, request: StageRequest, params: dict, estimate: float | None) -> list[str]:
    folder = run / BACKEND_DIR / "dry-run"
    folder.mkdir(parents=True, exist_ok=True)
    stem = f"{request.stage.number}-{request.stage.key}"
    prompt = folder / f"{stem}.md"
    prompt.write_text("\n\n".join(f"<!-- system block {i} -->\n{b['text']}" for i, b in enumerate(request.system, 1))
                      + f"\n\n<!-- user message -->\n{request.user}\n", encoding="utf-8")
    shown = {k: v for k, v in params.items() if k not in ("system", "messages")}
    shown["prompt_sha256"] = request.sha256
    shown["estimated_input_tokens"] = request.estimated_input_tokens
    shown["worst_case_cost_usd"] = None if estimate is None else round(estimate, 4)
    (folder / f"{stem}.json").write_text(json.dumps(shown, indent=2) + "\n", encoding="utf-8")
    return [prompt.relative_to(run).as_posix(), (folder / f"{stem}.json").relative_to(run).as_posix()]


def _attempts(run: Path, repo: Path, manifest: dict, request: StageRequest, backend: Backend, outcome: StageOutcome,
              *, repair: int, client, model: str, effort: str, max_tokens: int, messages: list[dict], params: dict,
              require_all: bool = True) -> None:
    """Call, write, check and repair one request; fills `outcome`."""
    stage = request.stage
    attempts = 1 + repair
    for attempt in range(1, attempts + 1):
        worst = estimate_upper_bound(request.estimated_input_tokens + sum(len(str(m["content"])) // 4
                                                                          for m in messages[1:]),
                                     max_tokens, model, backend.prices) or 0.0
        if spent(run) + worst > backend.max_cost_usd:
            outcome.status = "failed"
            outcome.message = (f"stopped before the call: recorded spend ${spent(run):.2f} plus this call's "
                               f"worst case ${worst:.2f} exceeds max_cost_usd ${backend.max_cost_usd:.2f}")
            break
        entry = {"at": _now(), "stage": stage.key, "attempt": attempt, "model_requested": model,
                 "effort": effort, "max_tokens": max_tokens, "fallbacks": "fallbacks" in params,
                 "prompt_sha256": request.sha256}
        try:
            result = call(client, backend, params)
        except BackendError as exc:
            _record(run, {**entry, "error": str(exc), "cost_usd": None})
            outcome.status, outcome.message = "failed", str(exc)
            break
        cost = _cost(result, backend)
        _record(run, {**entry, "model_served": result.model_served, "request_id": result.request_id,
                      "stop_reason": result.stop_reason, "duration_s": result.duration_s,
                      "usage": {k: v for k, v in result.usage.items() if k != "iterations"},
                      "iterations": result.iterations, "cost_usd": None if cost is None else round(cost, 6)})
        outcome.calls += 1
        outcome.cost_usd += cost or 0.0
        outcome.notes = str(result.data.get("notes", ""))
        try:
            outcome.files = _write_files(run, request, result.data, require_all=require_all)
        except BackendError as exc:
            problems = [str(exc)]
        else:
            problems = _checks(run, repo, stage, manifest)
        if not problems and stage.key in ("drafter", "revise"):
            problems = _cleanup(run)
        if not problems:
            outcome.status, outcome.message = "done", ""
            if stage.key == "proofreader":
                _mark_independent_review(run)
            break
        outcome.status = "failed"
        outcome.message = "; ".join(problems[:10]) + (f" (and {len(problems) - 10} more)" if len(problems) > 10 else "")
        if attempt == attempts:
            break
        # Repair turn: replay the answer unchanged, then the problems found.
        messages += [{"role": "assistant", "content": result.content},
                     {"role": "user", "content": "The engine's checks found these problems:\n"
                      + "\n".join(f"- {p}" for p in problems)
                      + "\n\nReturn every file again, corrected, in the same JSON format."}]
        params = {**params, "messages": messages}


def exec_run(run: Path, repo: Path, config: DocForgeConfig | None, *, only: int | None = None,
             dry_run: bool = False, repair: int = 0, client=None) -> list[StageOutcome]:
    """Run the run's unfinished stages (or stage `only`) in order. Stops at the first failure."""
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    backend = config.backend if config and config.backend else None
    if backend is None:
        if not dry_run:
            raise BackendError("docforge.yaml has no backend section, so no API call is made "
                               "(use --dry-run to see the requests and estimates for free)")
        backend = Backend()
    if not 0 <= repair <= 2:
        raise BackendError("--repair must be 0, 1 or 2")
    stages = stages_for(manifest)
    if only is not None and only not in [s.number for s in stages]:
        raise BackendError(f"no stage {only}; this run has stages 1 to {len(stages)}")

    from docforge.run.stages import stage_outputs

    outcomes: list[StageOutcome] = []
    for stage in stages:
        if only is not None and stage.number != only:
            continue
        outputs = stage_outputs(stage, manifest["profile"], manifest["deliverables"],
                                ia_plan=bool(manifest.get("ia_plan")))
        if all((run / o).is_file() for o in outputs):
            outcomes.append(StageOutcome(stage.name, "skipped", message="outputs already exist"))
            continue
        if any((run / o).is_file() for o in outputs):
            existing = [o for o in outputs if (run / o).is_file()]
            outcomes.append(StageOutcome(stage.name, "failed", message="some outputs already exist "
                                         f"({', '.join(existing)}); remove them to re-run the stage"))
            break
        try:
            request = build_request(run, repo, stage)
        except ContextError as exc:
            if dry_run and "not finished" in str(exc):
                outcomes.append(StageOutcome(stage.name, "skipped", message=f"dry run stops here: {exc}"))
                break
            outcomes.append(StageOutcome(stage.name, "failed", message=str(exc)))
            break
        model, effort, max_tokens = _settings(backend, stage)
        messages: list[dict] = [{"role": "user", "content": request.user}]
        params = request_params(backend, model=model, effort=effort, max_tokens=max_tokens,
                                system=request.system, messages=messages, schema=request.schema)
        estimate = estimate_upper_bound(request.estimated_input_tokens, max_tokens, model, backend.prices)
        outcome = StageOutcome(stage.name, "done", estimate_usd=None if estimate is None else round(estimate, 4))
        if dry_run:
            outcome.status, outcome.files = "dry_run", _dry_run(run, request, params, estimate)
            outcomes.append(outcome)
            continue
        if estimate is None:
            outcomes.append(StageOutcome(stage.name, "failed", message=f"no price for {model}; add it to "
                                         "backend.prices so the cost cap can be checked"))
            break

        client = client or make_client(backend)
        _attempts(run, repo, manifest, request, backend, outcome, repair=repair, client=client,
                  model=model, effort=effort, max_tokens=max_tokens, messages=messages, params=params)
        outcome.cost_usd = round(outcome.cost_usd, 6)
        outcomes.append(outcome)
        if outcome.status != "done":
            break
    return outcomes


def exec_revision(run: Path, repo: Path, config: DocForgeConfig, order: str, pages: list[str], *,
                  repair: int = 1, client=None) -> StageOutcome:
    """Run one revision order through the API. The answer may change only the pull request's pages, the
    coverage ledger and the QA report; the claim gate and the pack's clean-up must pass. On failure every
    file is put back as it was."""
    from .context import build_revision_request

    backend = config.backend if config and config.backend else None
    if backend is None:
        raise BackendError("docforge.yaml has no backend section, so no API call is made")
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    try:
        request = build_revision_request(run, repo, order, pages)
    except ContextError as exc:
        return StageOutcome("Reviser", "failed", message=str(exc))
    before = {rel: (run / rel).read_text(encoding="utf-8") if (run / rel).is_file() else None
              for rel in request.outputs}
    model, effort, max_tokens = _settings(backend, request.stage)
    messages: list[dict] = [{"role": "user", "content": request.user}]
    params = request_params(backend, model=model, effort=effort, max_tokens=max_tokens,
                            system=request.system, messages=messages, schema=request.schema)
    estimate = estimate_upper_bound(request.estimated_input_tokens, max_tokens, model, backend.prices)
    if estimate is None:
        return StageOutcome("Reviser", "failed", message=f"no price for {model}; add it to backend.prices")
    outcome = StageOutcome("Reviser", "done", estimate_usd=round(estimate, 4))
    _attempts(run, repo, manifest, request, backend, outcome, repair=repair, client=client or make_client(backend),
              model=model, effort=effort, max_tokens=max_tokens, messages=messages, params=params,
              require_all=False)
    if outcome.status != "done":
        for rel, text in before.items():
            if text is None:
                (run / rel).unlink(missing_ok=True)
            else:
                (run / rel).write_text(text, encoding="utf-8")
    outcome.cost_usd = round(outcome.cost_usd, 6)
    return outcome
