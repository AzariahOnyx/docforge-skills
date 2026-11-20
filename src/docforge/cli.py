"""Command-line entry point: `docforge`."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys

from docforge.config import ConfigError, load_config


def _validate(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.path)
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(
        f"{args.path} is valid: "
        f"{len(config.doc_collections)} doc collection(s), "
        f"{len(config.context_sources)} context source(s), "
        f"{len(config.triggers)} trigger(s), "
        f"{len(config.policies.rules)} policy rule(s)."
    )
    return 0


def _collection(args: argparse.Namespace):
    """Return (name, DocCollection) from --collection/--config, or (None, None)."""
    if args.collection is None:
        return None, None
    config = load_config(args.config)
    collection = config.doc_collections.get(args.collection)
    if collection is None:
        known = ", ".join(sorted(config.doc_collections)) or "none"
        raise ConfigError(f"doc collection {args.collection!r} is not in {args.config} (defined: {known})")
    return args.collection, collection


def _index(args: argparse.Namespace) -> int:
    from docforge.docs_index import DocsIndexError, build_index

    if args.out is not None and args.out.exists():
        print(f"refusing to overwrite existing file: {args.out}", file=sys.stderr)
        return 1
    try:
        name, collection = _collection(args)
        index = build_index(args.path, name, collection)
    except (ConfigError, DocsIndexError) as exc:
        print(exc, file=sys.stderr)
        return 1
    data = index.model_dump_json(indent=2)
    if args.out is None:
        print(data)
    else:
        with args.out.open("x", encoding="utf-8") as f:
            f.write(data + "\n")
        print(f"wrote {args.out}", file=sys.stderr)
    print(
        f"Indexed {len(index.pages)} page(s), "
        f"{sum(len(p.sections) for p in index.pages)} section(s), "
        f"{len(index.links)} link(s); {len(index.broken_links)} broken.",
        file=sys.stderr,
    )
    return 0


def _search(args: argparse.Namespace) -> int:
    from docforge.docs_index import DocsIndexError, search

    try:
        _, collection = _collection(args)
        hits = search(args.path, args.query, field=args.in_, limit=args.limit, collection=collection,
                      match=args.match)
    except (ConfigError, DocsIndexError) as exc:
        print(exc, file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps([h.model_dump() for h in hits], indent=2))
    elif not hits:
        print("No matches.")
    else:
        for hit in hits:
            where = f"{hit.path}#{hit.anchor}" if hit.anchor else hit.path
            print(f"{hit.score:>3}  {where}:{hit.line}  {hit.title}")
            print(f"     {hit.snippet}")
    return 0


def _run_start(args: argparse.Namespace) -> int:
    from docforge.packs import PackError, resolve_pack
    from docforge.run import RunError, start_run

    try:
        pack = resolve_pack(load_config(args.config), Path(args.config), args.pack) if args.pack else None
    except (ConfigError, PackError) as exc:
        print(exc, file=sys.stderr)
        return 1
    try:
        out = start_run(
            repo=args.repo, prds=args.prd, out=args.out, audience=args.audience, docs=args.docs,
            profile=args.profile, deliverables=args.deliverable, docs_include=args.docs_include,
            code_repo=args.code, base=args.base, head=args.head,
            publish_to=args.publish_to, source_pr=args.source_pr, source_state=args.source_state,
            context=args.context, pack=pack, product=args.product, flows=args.flow, flow_steps=args.flow_steps,
        )
    except (RunError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Started run {out}" + (f" with pack {args.pack}" if args.pack else ""))
    print(f"Next: stage 1 work order at {out / 'prompts' / '1-analyzer.md'}")
    return 0


def _run_status(args: argparse.Namespace) -> int:
    from docforge.run import RunError, next_stage, run_status

    try:
        statuses = run_status(args.out)
    except RunError as exc:
        print(exc, file=sys.stderr)
        return 1
    for status in statuses:
        mark = "done" if status.complete else f"{len(status.done)}/{len(status.done) + len(status.missing)} files"
        print(f"Stage {status.stage.number} {status.stage.name}: {mark}")
        for rel in status.missing:
            print(f"    missing {rel}")
    upcoming = next_stage(statuses)
    if upcoming is None:
        print(f"All stages have their files. Next: uv run docforge run check {args.out}")
    else:
        print(f"Next: stage {upcoming.stage.number} work order at {args.out / upcoming.stage.work_order}")
    try:
        backend = json.loads((args.out / "run.json").read_text(encoding="utf-8")).get("backend")
    except (OSError, ValueError):
        backend = None
    if backend:
        print(f"API backend: {backend['calls']} call(s), estimated ${backend['cost_usd']:.2f} "
              f"(models: {', '.join(backend.get('models') or ['none'])}; prices as of {backend.get('prices_as_of')})")
    return 0


def _run_check(args: argparse.Namespace) -> int:
    from docforge.run import RunError, run_checks

    try:
        record = run_checks(args.out, args.repo, dict(args.code_root))
    except RunError as exc:
        print(exc, file=sys.stderr)
        return 1
    structural = record["structural"]
    for error in structural["errors"]:
        print("FAIL:", error)
    for warning in structural["warnings"]:
        print("WARNING:", warning)
    for finding in record["lint_findings"]:
        print("LINT:", finding)
    research = record.get("research")
    if research is not None:
        for error in research["errors"]:
            print("FAIL (research):", error)
        for warning in research["warnings"]:
            print("WARNING (research):", warning)
        if research["statuses"]:
            counts = {}
            for status in research["statuses"].values():
                counts[status] = counts.get(status, 0) + 1
            print("Cross-source:", ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    vale = record.get("vale") or {}
    if vale.get("available"):
        for alert in vale["alerts"]:
            print("VALE:", alert)
        counts = vale["counts"]
        print(f"Vale: {counts.get('error', 0)} error(s), {counts.get('warning', 0)} warning(s), "
              f"{counts.get('suggestion', 0)} suggestion(s) on changed prose.")
    elif vale:
        print("Vale: not run.", vale.get("note", ""))
    passed = structural["passed"] and (research is None or research["passed"]) and vale.get("passed", True)
    verdict = "PASS" if passed else "FAIL"
    print(f"{verdict}: {structural['checker']}; {len(record['lint_findings'])} lint finding(s). "
          f"Saved {args.out / 'qa' / 'checks.json'}.")
    print(record["note"])
    return 0 if passed else 1


def _checkout_arg(value: str) -> tuple[str, Path]:
    name, sep, path = value.partition("=")
    if not sep or "/" not in name or not path:
        raise argparse.ArgumentTypeError("use owner/repo=PATH")
    return name.casefold(), Path(path)


def _trigger_check(args: argparse.Namespace) -> int:
    from docforge.agent import append_decision, decide
    from docforge.sources import DiffError, EventError, changes_for_event, parse_event

    try:
        config = load_config(args.config)
        payload = json.loads(args.payload.read_text(encoding="utf-8"))
        event = parse_event(args.event, payload, prior_approvals=args.prior_approvals)
        changed, source = changes_for_event(event.base_sha, event.head_sha, diff_file=args.diff,
                                            checkout=args.checkout)
        diff_text = ""
        if args.diff is not None:
            diff_text = args.diff.read_text(encoding="utf-8", errors="replace")[: config.triage.max_diff_chars + 1]
        elif args.checkout is not None and event.base_sha and event.head_sha:
            from docforge.webhook import _diff_text

            diff_text = _diff_text(args.checkout, event.base_sha, event.head_sha, config.triage.max_diff_chars)
    except (ConfigError, EventError, DiffError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    decision = decide(config, event, changed, diff_source=source, diff_text=diff_text,
                      ledger=args.log.with_name("triage-costs.jsonl"), config_path=Path(args.config))
    if not args.no_log:
        append_decision(args.log, decision)
        print(f"Logged decision {decision.decision_id} to {args.log}", file=sys.stderr)
    if getattr(args, "readable", False):
        t = decision.triage or {}
        print(f"{(decision.outcome or 'quiet').upper()}"
              + (f" ({decision.category}, decided by {t.get('layer')})" if decision.category else ""))
        for reason in decision.reasons or [decision.summary]:
            print(f"  - {reason}")
        if t.get("products"):
            print(f"  Product: {', '.join(t['products'])}"
                  + (f"; feature: {', '.join(t['features'])}" if t.get("features") else "")
                  + (f"; writer: {', '.join(t['owners'])}" if t.get("owners") else ""))
        if t.get("cost_usd"):
            print(f"  Model cost: ${t['cost_usd']:.4f}")
        return 0
    print(decision.model_dump_json(indent=2))
    return 0


def _serve(args: argparse.Namespace) -> int:
    import os

    from docforge.webhook import SECRET_ENV, Receiver, serve

    from docforge.webhook import JiraEndpoint

    secret = os.environ.get(SECRET_ENV, "")
    if not secret and not args.jira_trigger:
        print(f"set {SECRET_ENV} to the GitHub webhook secret, or give --jira-trigger; unsigned deliveries are "
              "never accepted", file=sys.stderr)
        return 1
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        return 1
    docs = None
    if args.docs_runs:
        if not secret:
            print(f"--docs-runs needs {SECRET_ENV}: GitHub deliveries must be signed", file=sys.stderr)
            return 1
        from docforge.webhook import DocsPrEndpoint

        docs = DocsPrEndpoint(config=config, config_path=Path(args.config), roots=list(args.docs_runs),
                              checkout=args.docs_checkout)
    features = None
    if secret and any(r.workspace for r in config.code_repos.values()):
        from docforge.webhook import FeatureEndpoint

        features = FeatureEndpoint(config=config, config_path=Path(args.config))
        if docs is not None:
            docs.features = features
    receiver = (Receiver(config=config, secret=secret.encode("utf-8"), log=args.log, checkouts=dict(args.checkout),
                         docs=docs, config_path=Path(args.config), features=features) if secret else None)
    jira = None
    if args.jira_trigger:
        if args.jira_trigger not in config.triggers:
            print(f"no trigger {args.jira_trigger!r} in {args.config}", file=sys.stderr)
            return 1
        jira = JiraEndpoint(config=config, config_path=Path(args.config), trigger=args.jira_trigger,
                            state_root=args.jira_state, client_factory=_jira_client_factory(config, args.jira_trigger))
    if docs is not None:
        docs.jira = jira
    serve(receiver, host=args.host, port=args.port, jira=jira)
    return 0


def _pr_handle(args: argparse.Namespace) -> int:
    from docforge.github.docs_pr import DocsPrError, find_run, handle_docs_event, source_merged
    from docforge.github.events import parse_docs_event

    try:
        config = load_config(args.config)
        payload = json.loads(args.payload.read_text(encoding="utf-8"))
        event = parse_docs_event(args.event, payload)
        if event is None:
            raise DocsPrError(f"{args.payload} is not a pull request event")
        found = find_run(args.runs, event.repo, event.number, event.branch)
        if found is None:
            if event.kind == "merged":
                print(json.dumps(source_merged(args.runs, event.repo, event.number, config=config), indent=2))
                return 0
            raise DocsPrError(f"no DocForge pull request {event.repo}#{event.number} under the given runs")
        if found[1].kind == "plan-pr":
            from docforge.plan.review import handle_plan_event

            result = handle_plan_event(event, run=found[0], config=config, delivery_id=args.delivery_id)
        else:
            result = handle_docs_event(event, run=found[0], config=config, delivery_id=args.delivery_id)
    except (ConfigError, DocsPrError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


def _pr_run(args: argparse.Namespace) -> int:
    from datetime import datetime, timezone

    from docforge.github.docs_pr import DocsPrError, find_runs, process_revision
    from docforge.publish import PublishError, load_plan

    if bool(args.run) == bool(args.all):
        print("give one run folder, or --all with --runs", file=sys.stderr)
        return 2
    try:
        config = load_config(args.config)
        from docforge.plan.review import ACTIVE, process_plan_pr

        if args.all:
            records = [(r, p) for r, p in find_runs(args.runs, ("pr", "plan-pr"))
                       if p.status in (ACTIVE if p.kind == "plan-pr" else ("changes_requested", "revised"))]
        else:
            records = [(args.run, load_plan(args.run, kind)) for kind in ("plan-pr", "pr")
                       if (args.run / "publish" / f"{kind}.json").is_file()]
            if not records:
                raise PublishError(f"{args.run} has no pull request record")

        def approved(run: Path) -> None:
            from docforge.features import process_feature, queue_draft_after_approval

            queued = queue_draft_after_approval(config, Path(args.config), run)
            if queued:
                results.append(process_feature(config, Path(args.config), *queued))
                return
            if not (args.jira_trigger and args.jira_state):
                return
            from docforge.jira.work import process as jira_process, queue_draft_after_approval

            key = (json.loads((run / "run.json").read_text(encoding="utf-8")).get("ia_plan") or {}).get("jira")
            if key and key != "none" and queue_draft_after_approval(args.jira_state, key):
                results.append(jira_process(key, config=config, config_path=Path(args.config),
                                            trigger_name=args.jira_trigger, state_root=args.jira_state,
                                            client_factory=_jira_client_factory(config, args.jira_trigger)))

        results = []
        now = datetime.max.replace(tzinfo=timezone.utc) if args.no_wait else None
        for run, plan in records:
            collection = config.doc_collections.get(plan.repo)
            checkout = args.docs_checkout or (
                (Path(args.config).parent / collection.checkout).resolve() if collection and collection.checkout else None)
            if plan.kind == "plan-pr":
                if plan.status in ACTIVE or not args.all:
                    results.append(process_plan_pr(run, config=config, checkout=checkout, now=now,
                                                   on_approved=approved))
            else:
                results.append(process_revision(run, config=config, checkout=checkout, now=now))
    except (ConfigError, DocsPrError, PublishError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(json.dumps(results, indent=2))
    return 0 if all(r.get("result") != "failed" for r in results) else 1


def _feature_handle(args: argparse.Namespace) -> int:
    from docforge.agent import append_decision, decide
    from docforge.features import FeatureError, on_comment, on_decision, on_merged
    from docforge.github.events import parse_docs_event
    from docforge.sources import DiffError, EventError, changes_for_event, parse_event
    from docforge.triage.feedback import post_feedback

    try:
        config = load_config(args.config)
        payload = json.loads(args.payload.read_text(encoding="utf-8"))
        if args.event == "issue_comment":
            event = parse_docs_event("issue_comment", payload)
            result = on_comment(config, Path(args.config), event) if event else None
            print(json.dumps(result or {"result": "ignore", "reason": "not a comment on a pull request"}, indent=2))
            return 0
        event = parse_event("pull_request", payload)
        if event.kind == "merge":
            print(json.dumps(on_merged(config, Path(args.config), event.repo, event.number), indent=2))
            return 0
        changed, source = changes_for_event(event.base_sha, event.head_sha, diff_file=args.diff,
                                            checkout=args.code_checkout)
        diff_text = args.diff.read_text(encoding="utf-8", errors="replace") if args.diff else ""
        decision = decide(config, event, changed, diff_source=source, diff_text=diff_text,
                          ledger=args.log.with_name("triage-costs.jsonl"), config_path=Path(args.config))
        if decision.triage is not None:
            t = decision.triage
            decision.feedback = post_feedback(config, repo=event.repo, number=event.number, sha=event.head_sha,
                                              outcome=decision.outcome, category=decision.category,
                                              reasons=decision.reasons, products=t["products"], owners=t["owners"])
        append_decision(args.log, decision)
        routed = (on_decision(config, Path(args.config), event, decision)
                  if decision.triage is not None and decision.outcome in ("act", "confirm") else {"result": "quiet"})
    except (ConfigError, EventError, DiffError, FeatureError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(json.dumps({"outcome": decision.outcome, "reasons": decision.reasons, **routed}, indent=2))
    return 0


def _feature_run(args: argparse.Namespace) -> int:
    from docforge.features import FeatureError, list_features, process_feature

    if bool(args.key) == bool(args.all):
        print("give one feature key, or --all", file=sys.stderr)
        return 2
    try:
        config = load_config(args.config)
        features = list_features(config, Path(args.config))
        chosen = [(r, s) for r, s in features if args.all or s.key == args.key]
        if not chosen:
            raise FeatureError(f"no feature {args.key!r}")
        results = [process_feature(config, Path(args.config), repo, state.key, code_checkout=args.code_checkout)
                   for repo, state in chosen
                   if not args.all or state.phase in ("planning", "drafting") or any(p.source_id is None for p in state.prs)]
    except (ConfigError, FeatureError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(json.dumps(results, indent=2))
    return 0 if all(r.get("result") != "failed" for r in results) else 1


def _feature_list(args: argparse.Namespace) -> int:
    from docforge.features import list_features

    try:
        config = load_config(args.config)
        features = list_features(config, Path(args.config))
    except (ConfigError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    for repo, state in features:
        prs = ", ".join(f"#{p.number} ({p.state})" for p in state.prs)
        print(f"{state.key}: {state.label}, {state.phase}, {repo} {prs}"
              + (f"; plan {state.plan_pr}" if state.plan_pr else "")
              + (f"; drafts {state.pull_request}" if state.pull_request else ""))
    if not features:
        print("no features yet")
    return 0


def _research_packet(args: argparse.Namespace) -> int:
    from docforge.research import ResearchError, build_packet
    from docforge.run import RunError, load_manifest

    try:
        code = load_manifest(args.run).get("code")
        if not code:
            raise RunError(f"{args.run} has no product code; start the run with --code, --base and --head")
        packet = build_packet(args.checkout, code["repo"], code["base"], code["head"])
    except (RunError, ResearchError) as exc:
        print(exc, file=sys.stderr)
        return 1
    target = args.run / "research" / "changes.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(packet.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {target}: {len(packet.files)} changed file(s), {len(packet.hunks)} cited hunk(s).")
    for note in packet.notes:
        print("NOTE:", note)
    return 0


def _research_check(args: argparse.Namespace) -> int:
    from docforge.research import ResearchError, research_check

    try:
        record = research_check(args.run, args.repo, dict(args.code_root))
    except ResearchError as exc:
        print(exc, file=sys.stderr)
        return 1
    for error in record["errors"]:
        print("FAIL:", error)
    for warning in record["warnings"]:
        print("WARNING:", warning)
    if record["errors"]:
        print(f"FAIL: {len(record['errors'])} evidence error(s); nothing was written.")
        return 1
    for result in record["results"]:
        question = f"  {result['question_id']}" if result["question_id"] else ""
        print(f"{result['claim_id']:>5}  {result['status']:<17}{question}")
    print("Wrote " + ", ".join(record["written"]) + ".")
    return 0


def _evidence_code_ref(args: argparse.Namespace) -> int:
    from docforge.research import ResearchError, code_ref

    try:
        ref = code_ref(args.checkout, args.repo, args.commit, args.path, args.lines)
    except ResearchError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(ref.model_dump_json(indent=2))
    return 0


def _place_arg(value: str) -> tuple[str, str]:
    src, sep, dest = value.partition("=")
    if not sep or not src or not dest:
        raise argparse.ArgumentTypeError("use run-file=docs-path")
    return src, dest


def _print_gate(result) -> None:
    for issue in result.errors:
        print(f"FAIL: {issue.path}:{issue.line}: {issue.message}")
    for exemption in result.exemptions:
        print(f"EXEMPT: {exemption.path}:{exemption.line} ({exemption.reason}): {exemption.text}")
    verdict = "PASS" if result.passed else "FAIL"
    print(f"{verdict}: {result.statements} statement(s) in {len(result.pages)} page(s); {result.cited} backed by "
          f"claims, {len(result.exemptions)} exempt, {len(result.errors)} error(s).")


def _gate(args: argparse.Namespace) -> int:
    from docforge.publish import GateError, gate_manifest, gate_run

    try:
        if args.manifest:
            result = gate_manifest(args.manifest, args.docs_root)
        elif args.run:
            result = gate_run(args.run)
        else:
            print("give a run folder, or --manifest with --docs-root", file=sys.stderr)
            return 2
    except (GateError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    _print_gate(result)
    return 0 if result.passed else 1


def _publish_prepare(args: argparse.Namespace) -> int:
    from docforge.publish import PublishError, prepare_publish, resolve_commands

    try:
        config = load_config(args.config)
        manifest = json.loads((args.run / "run.json").read_text(encoding="utf-8"))
        collection = args.collection or (manifest.get("publish") or {}).get("collection")
        if not collection:
            raise PublishError("no docs repo: start the run with --publish-to or pass --collection")
        plan = prepare_publish(run=args.run, checkout=args.docs_checkout, config=config, collection=collection,
                               placements=args.place, base=args.base, title=args.title)
    except (ConfigError, PublishError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Created local branch {plan.branch} at {plan.commit[:12]} (not pushed).")
    for f in plan.files:
        print(f"  {f['change']:<9}{f['path']}")
    print(f"Pull request: {'draft' if plan.draft else 'ready for review'}; policy action: {plan.action}.")
    print(f"Wrote {args.run / 'publish' / 'pr.json'} and {args.run / 'publish' / 'pr-body.md'}.")
    print("After review, a person runs:")
    for command in resolve_commands(plan.commands, run=args.run, checkout=args.docs_checkout):
        print("  " + command)
    return 0


def _publish_ready(args: argparse.Namespace) -> int:
    from docforge.publish import PublishError, apply_ready, load_plan, mark_ready

    try:
        if not (args.apply and args.source_state == "merged" and not load_plan(args.run).draft):
            plan = mark_ready(args.run, args.source_state)
            print(f"Recorded that the source change is merged; {plan.branch} may leave draft.")
        if args.apply:
            plan = apply_ready(run=args.run, config=load_config(args.config))
            print(f"Marked pull request #{plan.pr_number} ready for review: {plan.pr_url or ''}".rstrip(": "))
            return 0
    except (ConfigError, PublishError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print("A person runs:")
    for command in plan.commands:
        print("  " + command)
    return 0


def _publish_open(args: argparse.Namespace) -> int:
    from docforge.publish import PublishError, open_pr

    try:
        plan = open_pr(run=args.run, checkout=args.docs_checkout, config=load_config(args.config))
    except (ConfigError, PublishError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    state = "draft" if plan.draft else "ready for review"
    print(f"Pushed {plan.branch} at {plan.commit[:12]}; pull request #{plan.pr_number} ({state}): {plan.pr_url}")
    return 0


def _publish_update(args: argparse.Namespace) -> int:
    from docforge.publish import PublishError, resolve_commands, update_publish

    try:
        plan = update_publish(run=args.run, checkout=args.docs_checkout, config=load_config(args.config))
    except (ConfigError, PublishError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Added revision {plan.revision} to local branch {plan.branch} at {plan.commit[:12]} (not pushed).")
    print("After review, a person runs:")
    for command in resolve_commands(plan.commands, run=args.run, checkout=args.docs_checkout):
        print("  " + command)
    return 0


def _review_request_changes(args: argparse.Namespace) -> int:
    from docforge.review import ReviewError, request_changes

    try:
        feedback, order, commands = request_changes(args.run, comment=args.comment, reviewer=args.reviewer,
                                                    page=args.page, line=args.line)
    except ReviewError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Recorded change request {feedback.feedback_id}. Revision work order: {order}")
    print("To mirror it on GitHub, run:")
    for command in commands:
        print("  " + command)
    return 0


def _review_close(args: argparse.Namespace) -> int:
    from docforge.review import ReviewError, close_suggestion

    try:
        feedback, commands = close_suggestion(args.run, reason=args.reason, note=args.note, reviewer=args.reviewer)
    except ReviewError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Closed {args.run} with reason {feedback.reason} ({feedback.feedback_id}).")
    print("To mirror it on GitHub, run:")
    for command in commands:
        print("  " + command)
    return 0


def _review_serve(args: argparse.Namespace) -> int:
    from docforge.review.web import ReviewApp, serve

    if not args.runs.is_dir():
        print(f"not a directory: {args.runs}", file=sys.stderr)
        return 1
    serve(ReviewApp(root=args.runs, reviewer=args.reviewer or ""), host=args.host, port=args.port)
    return 0


def _lint(args: argparse.Namespace) -> int:
    from docforge.lint import LintError, apply_fixes, lint_run, plan_fixes

    try:
        result = lint_run(args.run, changed_only=not args.all, config=args.vale_config)
        for alert in result.alerts:
            fix = f" -> '{alert.replacement}'" if alert.replacement else ""
            print(f"{alert.page}:{alert.line}:{alert.start} {alert.severity} {alert.check}: {alert.message}{fix}")
        counts = result.counts
        scope = "changed prose" if result.changed_only else "all prose"
        print(f"Vale {result.vale_version}: {counts['error']} error(s), {counts['warning']} warning(s), "
              f"{counts['suggestion']} suggestion(s) on {scope} in {len(result.pages)} page(s)"
              + (f"; {result.unchanged_alerts} on unchanged lines not shown." if result.unchanged_alerts else "."))
        if not (args.fix or args.apply):
            return 1 if counts["error"] else 0
        plan = plan_fixes(args.run, result)
        for skipped in plan.skipped:
            print("NOT FIXED:", skipped)
        if not plan.fixes:
            print("No automatic fixes available.")
            return 1 if counts["error"] else 0
        print(plan.diff, end="")
        if not args.apply:
            print(f"{len(plan.fixes)} fix(es) proposed. Rerun with --apply to write them.")
            return 0
        apply_fixes(args.run, plan)
        print(f"Applied {len(plan.fixes)} fix(es); the claim gate still passes where it applies.")
        return 0
    except (LintError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1


def _rules_folder(args: argparse.Namespace) -> Path:
    from docforge.rules import rules_dir

    return rules_dir(args.rules_dir)


def _origin_arg(value: str) -> tuple[str, str]:
    run, sep, feedback = value.partition(":")
    if not sep or not run or not re.fullmatch(r"[0-9a-f]{12}", feedback):
        raise argparse.ArgumentTypeError("use run-name:feedback-id (12 hex characters)")
    return run, feedback


def _rules(args: argparse.Namespace) -> int:
    from docforge.rules import RuleError, approve, close, feedback_digest, load_rules, propose, try_rule

    folder = _rules_folder(args)
    try:
        if args.rules_command == "list":
            rules = load_rules(folder)
            if not rules:
                print(f"No rules in {folder}.")
            for rule in rules:
                print(f"{rule.id}  {rule.effective_status():<30} {rule.kind:<9} {rule.title}")
        elif args.rules_command == "suggest":
            print(json.dumps(feedback_digest(args.runs, folder), indent=2))
        elif args.rules_command == "propose":
            rule = propose(folder, kind=args.kind, title=args.title, message=args.message, pattern=args.pattern,
                           replace=args.replace, level=args.level, guidance=args.guidance,
                           applies_to=args.applies_to, origins=args.origin, proposed_by=args.by,
                           ignorecase=not args.case_sensitive)
            print(f"Proposed {rule.id} ({rule.kind}): {rule.title}. Next: docforge rules test {rule.id} --runs ...")
        elif args.rules_command == "test":
            report = try_rule(folder, args.id, args.runs)
            print(f"Tried {args.id} on {len(report.runs)} run(s), {report.pages_checked} page(s).")
            for hit in report.hits:
                print(f"  HIT {hit.run}/{hit.page}:{hit.line} '{hit.match}': {hit.text}")
            for quote in report.feedback:
                print(f"  FROM {quote}")
            print(report.note)
        elif args.rules_command == "approve":
            rule = approve(folder, args.id, by=args.by)
            print(f"{rule.id} is live (approved by {rule.approval.by}).")
        else:
            status = "rejected" if args.rules_command == "reject" else "retired"
            rule = close(folder, args.id, status=status, by=args.by, reason=args.reason)
            print(f"{rule.id} is {rule.status}.")
    except RuleError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


def _backfill(args: argparse.Namespace) -> int:
    from docforge import backfill

    try:
        command = args.backfill_command
        if command == "fetch":
            manifest = backfill.fetch_prs(args.repo, args.out, state=args.state, limit=args.limit)
            print(f"Fetched {len(manifest['prs'])} PR(s) of {args.repo} into {args.out} (read-only).")
            print(f"Next: docforge backfill label {args.out}, then a person fills in labels.json.")
        elif command == "label":
            path = backfill.write_labels_template(args.folder)
            print(f"Wrote {path}. A person sets docs_needed (yes/no) and labelled_by for each PR.")
        elif command == "replay":
            labels = args.labels or (args.folder / "labels.json" if (args.folder / "labels.json").is_file() else None)
            report = backfill.replay(args.folder, load_config(args.config), labels, use_model=args.use_model)
            c = report["counts"]
            print(f"Replayed {report['prs']} PR(s); {report['labelled']} labelled. "
                  f"TP {c['true_positive']}, FP {c['false_positive']}, FN {c['false_negative']}, TN {c['true_negative']}. "
                  f"Precision {report['precision']}, recall {report['recall']}.")
            if report["unscored"]:
                print("Unscored (no label): " + ", ".join(f"#{n}" for n in report["unscored"]))
            print("Wrote " + ", ".join(report["files"]) + ".")
        elif command == "prepare":
            record = backfill.prepare(args.cases, args.out, args.repo)
            print(f"Prepared {len(record['arms'])} arm(s) in {args.out}. Each arm's work order is in its folder; "
                  "outputs go to output.md.")
        elif command == "blind":
            result = backfill.blind(args.folder)
            print(f"Blinded {result['outputs']} output(s); {result['assertions']} assertion(s) in "
                  "judgments.template.json. Reviewers must not open key.json.")
        else:
            report = backfill.score(args.folder, args.judgments)
            for arm, s in report["by_arm"].items():
                print(f"{arm}: {s['pass']} pass, {s['fail']} fail, {s['uncertain']} uncertain; pass rate {s['pass_rate']}")
            print("Human-reviewed." if report["human_reviewed"] else "NOT human-reviewed: a reviewer is the generator.")
            print("Wrote " + ", ".join(report["files"]) + ".")
    except (backfill.BackfillError, ConfigError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


def _add_collection_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--collection", help="limit to a doc_collections entry's filter (owner/repo)")
    parser.add_argument("--config", default="docforge.yaml", help="config used with --collection")


def _pick_source(config, kind: str, name: str | None):
    matches = {k: v for k, v in config.context_sources.items() if v.source_type == kind}
    if name is not None:
        if name not in matches:
            raise ConfigError(f"no {kind} source named {name!r} in context_sources")
        return matches[name]
    if len(matches) != 1:
        raise ConfigError(f"{len(matches)} {kind} sources are configured; choose one with --source")
    return next(iter(matches.values()))


def _sources_fetch(args: argparse.Namespace) -> int:
    from docforge.sources import SourceFetchError, provenance
    from docforge.sources.confluence import fetch_page
    from docforge.sources.jira import fetch_issue

    try:
        source = _pick_source(load_config(args.config), args.kind, args.source)
        if args.out.exists():
            raise SourceFetchError(f"{args.out} already exists; choose a new file (sources are never overwritten)")
        fetch = fetch_issue if args.kind == "jira" else fetch_page
        text, meta = fetch(source, args.id)
        provenance.write_new(args.out, text)
    except (ConfigError, SourceFetchError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Fetched {args.kind} {meta['id']} (version {meta['version']}) to {args.out}")
    print(f"Use it with: docforge run start --prd {args.out} ...  (or --context for supporting material)")
    return 0


def _notify_slack(args: argparse.Namespace) -> int:
    from docforge.notify import NotifyError, notify

    try:
        config = load_config(args.config) if args.config else None
        outcome = notify(args.run, args.event, config=config, trigger=args.trigger, pr_url=args.pr_url, send=args.send)
    except (ConfigError, NotifyError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(outcome.text)
    print(f"\n[{outcome.reason}]")
    return 0 if outcome.sent or not args.send else 1


def _plan_check(args: argparse.Namespace) -> int:
    from docforge.plan import check_run_plan, read_plan

    try:
        config = load_config(args.config) if Path(args.config).is_file() else None
        if args.target.is_dir():
            plan, errors = check_run_plan(args.target, config)
        else:
            plan, errors = read_plan(args.target.read_text(encoding="utf-8"))
    except (ConfigError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        return 1
    articles = plan.articles()
    print(f"PASS: {plan.front['feature']}: {sum(a['change'] == 'create' for a in articles)} new and "
          f"{sum(a['change'] != 'create' for a in articles)} existing article(s), {len(plan.questions)} open "
          f"question(s), {len(plan.conflicts)} conflict(s).")
    return 0


def _plan_prepare(args: argparse.Namespace) -> int:
    from docforge.plan.pr import prepare_plan_pr
    from docforge.publish import PublishError

    try:
        config = load_config(args.config)
        manifest = json.loads((args.run / "run.json").read_text(encoding="utf-8"))
        collection = args.collection or (manifest.get("publish") or {}).get("collection")
        if not collection:
            raise PublishError("no docs repo: start the run with --publish-to or pass --collection")
        record = prepare_plan_pr(run=args.run, checkout=args.docs_checkout, config=config, collection=collection,
                                 base=args.base)
    except (ConfigError, PublishError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Created local branch {record.branch} at {record.commit[:12]} with {record.placements[0]['dest']} "
          "(not pushed). After review, a person runs: docforge plan open")
    return 0


def _plan_open(args: argparse.Namespace) -> int:
    from docforge.publish import PublishError, open_pr

    try:
        record = open_pr(run=args.run, checkout=args.docs_checkout, config=load_config(args.config), kind="plan-pr")
    except (ConfigError, PublishError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Pushed {record.branch}; plan pull request #{record.pr_number}: {record.pr_url}")
    return 0


def _collection_of(config, name):
    if name is None:
        return None
    if name not in config.doc_collections:
        raise ValueError(f"doc collection {name!r} is not in the config")
    return config.doc_collections[name]


def _outdated_note(args: argparse.Namespace) -> int:
    from docforge.outdated import note_from_code

    try:
        note = note_from_code(args.code_checkout, args.base, args.head, spec_paths=args.spec_path, terms=args.term)
    except (OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    text = json.dumps(note.to_dict(), indent=2) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"Wrote {args.out}: {len(note.strings)} string change(s), {len(note.spec_changes)} spec change(s), "
              f"{len(note.terms)} term(s).")
    else:
        print(text, end="")
    return 0


def _outdated_shortlist(args: argparse.Namespace) -> int:
    from docforge.outdated import ChangeNote, build_shortlist

    try:
        config = load_config(args.config) if Path(args.config).is_file() else None
        collection = _collection_of(config, args.collection) if config else None
        note = ChangeNote.from_dict(json.loads(args.note.read_text(encoding="utf-8")))
        shortlist = build_shortlist(args.docs, note, collection=collection,
                                    must_review=(collection.must_review if collection else []) + args.must_review,
                                    cap=args.cap or (collection.outdated_cap if collection else 25))
    except (ConfigError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    for page in shortlist["pages"]:
        print(f"{'MUST ' if page['must_review'] else '     '}{page['path']}: {'; '.join(page['reasons'])}")
    print(f"{len(shortlist['pages'])} of {shortlist['searched_pages']} page(s) shortlisted, "
          f"{len(shortlist['must_review'])} must review, {shortlist['dropped']} beyond the cap.")
    return 0


def _outdated_run(args: argparse.Namespace) -> int:
    from docforge.outdated import find_outdated

    try:
        config = load_config(args.config)
        manifest = json.loads((args.run / "run.json").read_text(encoding="utf-8"))
        collection = args.collection or (manifest.get("publish") or {}).get("collection")
        if not collection:
            raise ValueError("no doc collection: start the run with --publish-to or pass --collection")
        outcome = find_outdated(args.run, args.repo.resolve(), config, docs=args.docs, collection=collection,
                                code_checkout=args.code_checkout, spec_paths=args.spec_path)
    except (ConfigError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    if outcome == "waiting":
        print("Wrote prompts/outdated-pass-1.md and prompts/outdated-pass-2.md: run each in its own Claude Code "
              "session, then run this command again.")
        return 0
    if outcome != "done":
        print(outcome, file=sys.stderr)
        return 1
    print((args.run / "analysis" / "OUTDATED.md").read_text(encoding="utf-8"), end="")
    return 0


def _outdated_fix(args: argparse.Namespace) -> int:
    from docforge.outdated.fix import apply_fixes

    try:
        result = apply_fixes(args.run)
    except (OSError, ValueError, KeyError) as exc:
        print(exc, file=sys.stderr)
        return 1
    for dest, item in result["edits"].items():
        verdict = "PASS" if not item["problems"] else "FAIL"
        print(f"{verdict}: {dest} ({item['action']}, {item.get('fixes', 0)} fix(es), changed lines {item['ranges']})")
        for problem in item["problems"]:
            print(f"  - {problem}")
    for problem in result["problems"]:
        if not any(problem.startswith(dest + ":") for dest in result["edits"]):
            print(f"FAIL: {problem}")
    return 1 if result["problems"] else 0


def _outdated_eval(args: argparse.Namespace) -> int:
    from docforge.outdated.evaluate import EvalError, evaluate, render_eval

    try:
        config = load_config(args.config) if Path(args.config).is_file() else None
        collection = _collection_of(config, args.collection) if config else None
        report = evaluate(args.cases, args.docs, collection=collection,
                          must_review=collection.must_review if collection else [],
                          cap=collection.outdated_cap if collection else 25)
    except (ConfigError, EvalError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(render_eval(report), end="")
    return 0


def _outdated_cases(args: argparse.Namespace) -> int:
    from docforge.outdated.evaluate import EvalError, propose_cases

    try:
        config = load_config(args.config) if Path(args.config).is_file() else None
        collection = _collection_of(config, args.collection) if config else None
        data = propose_cases(args.docs_checkout, args.out, collection=collection, limit=args.limit)
    except (ConfigError, EvalError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Wrote {args.out}: {len(data['cases'])} proposed case(s). A person fills in each change note and checks "
          "the expected pages before `docforge outdated eval`.")
    return 0


def _pack_check(args: argparse.Namespace) -> int:
    from docforge.packs import PackError, load_pack, resolve_pack

    try:
        folder = (resolve_pack(load_config(args.config), Path(args.config), str(args.path))
                  if args.config else args.path)
        pack = load_pack(folder)
    except (ConfigError, PackError) as exc:
        print(exc, file=sys.stderr)
        return 1
    m = pack.manifest
    print(f"Pack {m.name} {m.version} is valid. sha256 {pack.sha256}")
    roles: dict[str, int] = {}
    for f in pack.files:
        roles[f.role] = roles.get(f.role, 0) + 1
    print("Files: " + ", ".join(f"{n} {role}" for role, n in sorted(roles.items())))
    if m.article_specs:
        print("Article specs: " + ", ".join(s.type for s in m.article_specs))
    return 0


def _run_exec(args: argparse.Namespace) -> int:
    from docforge.backend import BackendError, exec_run

    try:
        config = load_config(args.config) if Path(args.config).is_file() else None
        if config is None and not args.dry_run:
            raise BackendError(f"{args.config} not found; the backend needs its backend section")
        outcomes = exec_run(args.out, args.repo, config, only=args.stage, dry_run=args.dry_run, repair=args.repair)
    except (ConfigError, BackendError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    failed = False
    for o in outcomes:
        line = f"{o.stage}: {o.status.replace('_', ' ')}"
        if o.calls:
            line += f", {o.calls} call(s), ${o.cost_usd:.4f}"
        if o.estimate_usd is not None and o.status == "dry_run":
            line += f", worst case ${o.estimate_usd:.2f}"
        print(line + (f" ({o.message})" if o.message else ""))
        for f in o.files:
            print(f"    {f}")
        if o.notes:
            print(f"    notes: {o.notes}")
        failed = failed or o.status == "failed"
    if args.dry_run:
        print("Dry run: no API call was made. Estimates are upper bounds from a local token estimate.")
    return 1 if failed else 0


def _sources_flow(args: argparse.Namespace) -> int:
    from docforge.sources.flow import FlowError, FlowProfile, extract_flow, write_flow

    try:
        profile = None
        if args.pack:
            from docforge.packs import PackError, load_pack, resolve_pack

            try:
                pack = load_pack(resolve_pack(load_config(args.config), Path(args.config), args.pack))
            except PackError as exc:
                raise FlowError(str(exc)) from None
            spec = pack.manifest.flow_profile
            if spec is None:
                raise FlowError(f"pack {args.pack} has no flow_profile")
            profile = FlowProfile(header=spec.header, noise=tuple(spec.noise), name=f"{pack.manifest.name} pack")
        flow = extract_flow(args.pdf, args.id, profile, title=args.title)
        json_path, md_path = write_flow(flow, args.out)
    except (ConfigError, FlowError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Extracted {len(flow['steps'])} step(s) from {args.pdf.name} ({flow['pages']} pages, {flow['profile']} profile)")
    for warning in flow["warnings"]:
        print(f"    warning: {warning}")
    print(f"Wrote {md_path} and {json_path}. Use it with: docforge run start ... --flow {md_path}")
    return 0


def _cleanup(args: argparse.Namespace) -> int:
    from docforge.cleanup import CleanupError, apply_cleanup, plan_cleanup

    try:
        result = plan_cleanup(args.run)
        if args.apply:
            apply_cleanup(args.run, result)
    except (CleanupError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    if not result.steps:
        print("The run's pack has no clean-up steps (or the run has no pack).")
        return 0
    for step in result.steps:
        print(f"{step['id']} ({step['kind']}): {step['changes']} change(s), {step['findings']} finding(s)")
    for f in result.findings:
        print(f"    finding {f.page}:{f.line} [{f.step}] {f.message}")
    if args.apply:
        print(f"Applied {len(result.changes)} change(s) to {len(result.pages)} page(s). "
              f"Report: {args.run / 'qa' / 'CLEANUP-REPORT.md'}")
    else:
        print(result.diff or "No changes.")
        if result.changes:
            print("Preview only. Run again with --apply to write the changes and the report.")
    return 0


def _jira(args: argparse.Namespace) -> int:
    from docforge.jira import HandleError, StateError, handle, load_state

    try:
        if args.jira_command == "handle":
            config = load_config(args.config)
            if not args.unsigned and not args.signature:
                raise HandleError("give --signature (the X-Hub-Signature header) or --unsigned for a local recording")
            result = handle(args.payload.read_bytes(), config=config, trigger_name=args.trigger, state_root=args.state,
                            signature=args.signature, verify=not args.unsigned, delivery_id=args.delivery_id,
                            client_factory=_jira_client_factory(config, args.trigger))
            print(json.dumps(result, indent=2))
            return 0
        if args.jira_command == "run":
            from docforge.jira.work import WorkError, process, process_all

            if bool(args.key) == bool(args.all):
                raise HandleError("give one ticket key or --all")

            config = load_config(args.config)
            kw = dict(config=config, config_path=Path(args.config), trigger_name=args.trigger,
                      client_factory=_jira_client_factory(config, args.trigger))
            try:
                results = (process_all(args.state, **kw) if args.all else
                           [process(args.key, state_root=args.state, **kw)])
            except WorkError as exc:
                raise HandleError(str(exc)) from None
            print(json.dumps(results, indent=2))
            return 0
        state = load_state(args.state, args.key)
        if state is None:
            print(f"no state for {args.key} in {args.state}", file=sys.stderr)
            return 1
        print(f"{state.key}: phase {state.phase}, mode {state.mode}, revision {state.revision}, run {state.run or '-'}"
              + (f", pending {state.pending.action}" if state.pending else ""))
        if state.answered:
            print("  answered: " + ", ".join(f"{q} ({a})" for q, a in sorted(state.answered.items())))
        for entry in state.outbox:
            print(f"  {entry.at} {entry.kind} {entry.message}: {'sent' if entry.sent else entry.note}")
        return 0
    except (ConfigError, HandleError, StateError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1


def _jira_client_factory(config, trigger_name: str):
    def factory():
        from docforge.sources.atlassian import AtlassianClient

        return AtlassianClient(config.context_sources[config.triggers[trigger_name].source])

    return factory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="docforge")
    sub = parser.add_subparsers(dest="command", required=True)

    config_cmd = sub.add_parser("config", help="work with docforge.yaml")
    config_sub = config_cmd.add_subparsers(dest="config_command", required=True)
    validate = config_sub.add_parser("validate", help="check docforge.yaml for errors")
    validate.add_argument("path", nargs="?", default="docforge.yaml")
    validate.set_defaults(func=_validate)

    index = sub.add_parser("index", help="print a page/section/link index of a docs folder as JSON (read-only)")
    index.add_argument("path", help="local docs folder")
    index.add_argument("--out", type=Path, help="write the JSON to this new file instead of stdout")
    _add_collection_args(index)
    index.set_defaults(func=_index)

    search = sub.add_parser("search", help="keyword search over a docs folder")
    search.add_argument("path", help="local docs folder")
    search.add_argument("query")
    search.add_argument("--in", dest="in_", choices=("all", "title", "heading"), default="all")
    search.add_argument("--limit", type=int, default=10, help="maximum results (0 for all)")
    search.add_argument("--match", choices=("all", "any"), default="all",
                        help="all: every word must match (default); any: at least one")
    search.add_argument("--json", action="store_true", help="print results as JSON")
    _add_collection_args(search)
    search.set_defaults(func=_search)

    from docforge.agent import DEFAULT_LOG

    trigger = sub.add_parser("trigger", help="check pull request events against triggers")
    trigger_sub = trigger.add_subparsers(dest="trigger_command", required=True)
    tcheck = trigger_sub.add_parser("check", help="decide whether a saved webhook payload needs docs work")
    tcheck.add_argument("payload", type=Path, help="webhook payload JSON file")
    tcheck.add_argument("--event", required=True, choices=("pull_request", "pull_request_review"),
                        help="the X-GitHub-Event of the payload")
    source = tcheck.add_mutually_exclusive_group()
    source.add_argument("--diff", type=Path, help="unified diff of the pull request")
    source.add_argument("--checkout", type=Path, help="local checkout to diff base...head in (read-only)")
    tcheck.add_argument("--prior-approvals", type=int, help="approvals before this review (for first_approval)")
    tcheck.add_argument("--config", default="docforge.yaml")
    tcheck.add_argument("--log", type=Path, default=DEFAULT_LOG, help="decision log (JSON lines, appended)")
    tcheck.add_argument("--no-log", action="store_true", help="print the decision without logging it")
    tcheck.set_defaults(func=_trigger_check)

    tri = sub.add_parser("triage", help="decide whether a saved code pull request needs docs: quiet, act or confirm")
    tri.add_argument("payload", type=Path, help="pull_request webhook payload JSON file")
    tri_source = tri.add_mutually_exclusive_group()
    tri_source.add_argument("--diff", type=Path, help="unified diff of the pull request")
    tri_source.add_argument("--checkout", type=Path, help="local checkout to diff base..head")
    tri.add_argument("--config", default="docforge.yaml")
    tri.add_argument("--log", type=Path, default=DEFAULT_LOG, help="decision log (JSON lines, appended)")
    tri.add_argument("--no-log", action="store_true")
    tri.set_defaults(func=_trigger_check, event="pull_request", prior_approvals=None, readable=True)

    serve_cmd = sub.add_parser("serve", help="receive GitHub (and Jira) webhooks; --docs-runs handles review on DocForge PRs")
    serve_cmd.add_argument("--host", default="127.0.0.1")
    serve_cmd.add_argument("--port", type=int, default=8787)
    serve_cmd.add_argument("--config", default="docforge.yaml")
    serve_cmd.add_argument("--log", type=Path, default=DEFAULT_LOG)
    serve_cmd.add_argument("--jira-trigger", help="also receive Jira webhooks at /jira/webhook for this jira_ticket trigger")
    serve_cmd.add_argument("--jira-state", type=Path, default=Path(".docforge/jira"))
    serve_cmd.add_argument("--checkout", type=_checkout_arg, action="append", default=[],
                           metavar="OWNER/REPO=PATH", help="local checkout used to diff that repo's PRs")
    serve_cmd.add_argument("--docs-runs", type=Path, action="append", default=[], metavar="FOLDER",
                           help="handle review on DocForge's own docs pull requests whose runs are under FOLDER")
    serve_cmd.add_argument("--docs-checkout", type=Path, help="docs clone for revisions (default: the collection's)")
    serve_cmd.set_defaults(func=_serve)

    feat = sub.add_parser("feature", help="the code route: code pull requests that need docs become features")
    feat_sub = feat.add_subparsers(dest="feature_command", required=True)
    fhandle = feat_sub.add_parser("handle", help="decide and route one saved code pull request event or comment")
    fhandle.add_argument("payload", type=Path)
    fhandle.add_argument("--event", required=True, choices=("pull_request", "issue_comment"))
    fsrc = fhandle.add_mutually_exclusive_group()
    fsrc.add_argument("--diff", type=Path, help="unified diff of the pull request")
    fsrc.add_argument("--code-checkout", type=Path, help="local checkout to diff base..head")
    fhandle.add_argument("--config", default="docforge.yaml")
    fhandle.add_argument("--log", type=Path, default=DEFAULT_LOG)
    fhandle.set_defaults(func=_feature_handle)
    frun = feat_sub.add_parser("run", help="do a feature's pending work: plan, sources, drafts")
    frun.add_argument("key", nargs="?")
    frun.add_argument("--all", action="store_true")
    frun.add_argument("--code-checkout", type=Path, help="default: the code repo's checkout setting")
    frun.add_argument("--config", default="docforge.yaml")
    frun.set_defaults(func=_feature_run)
    flist = feat_sub.add_parser("list", help="list features and their pull requests")
    flist.add_argument("--config", default="docforge.yaml")
    flist.set_defaults(func=_feature_list)

    prc = sub.add_parser("pr", help="review on DocForge's own docs pull requests: comments become revisions")
    prc_sub = prc.add_subparsers(dest="pr_command", required=True)
    phandle = prc_sub.add_parser("handle", help="record one saved GitHub delivery about a DocForge pull request")
    phandle.add_argument("payload", type=Path)
    phandle.add_argument("--event", required=True, help="the X-GitHub-Event name, for example issue_comment")
    phandle.add_argument("--runs", type=Path, action="append", required=True, metavar="FOLDER")
    phandle.add_argument("--delivery-id")
    phandle.add_argument("--config", default="docforge.yaml")
    phandle.set_defaults(func=_pr_handle)
    prun = prc_sub.add_parser("run", help="run pending revisions: backend or session, then push and reply")
    prun.add_argument("run", type=Path, nargs="?")
    prun.add_argument("--all", action="store_true", help="every DocForge pull request under --runs")
    prun.add_argument("--runs", type=Path, action="append", default=[], metavar="FOLDER")
    prun.add_argument("--docs-checkout", type=Path, help="docs clone (default: the doc collection's checkout)")
    prun.add_argument("--no-wait", action="store_true", help="do not wait for the review's quiet period")
    prun.add_argument("--jira-trigger", help="with --jira-state: an approved plan pull request drafts its ticket")
    prun.add_argument("--jira-state", type=Path)
    prun.add_argument("--config", default="docforge.yaml")
    prun.set_defaults(func=_pr_run)

    research = sub.add_parser("research", help="compare a run's PRD claims with product code")
    research_sub = research.add_subparsers(dest="research_command", required=True)
    packet = research_sub.add_parser("packet", help="write research/changes.json from a local checkout (read-only)")
    packet.add_argument("run", type=Path)
    packet.add_argument("--checkout", type=Path, required=True, help="local checkout of the run's code repo")
    packet.set_defaults(func=_research_packet)
    rcheck = research_sub.add_parser("check", help="verify claims.json and write the cross-source report")
    rcheck.add_argument("run", type=Path)
    rcheck.add_argument("--repo", type=Path, default=Path("."),
                        help="root that run.json source paths are relative to (default: current folder)")
    rcheck.add_argument("--code-root", type=_checkout_arg, action="append", default=[], metavar="OWNER/REPO=PATH",
                        help="local checkout used to verify code evidence (repeatable)")
    rcheck.set_defaults(func=_research_check)

    evidence = sub.add_parser("evidence", help="evidence helpers")
    evidence_sub = evidence.add_subparsers(dest="evidence_command", required=True)
    ref = evidence_sub.add_parser("code-ref", help="print a verified code citation for some lines (read-only)")
    ref.add_argument("--checkout", type=Path, required=True)
    ref.add_argument("--repo", required=True, metavar="OWNER/REPO")
    ref.add_argument("--commit", required=True, help="commit SHA (7-40 hex)")
    ref.add_argument("--path", required=True, help="file path inside the repo")
    ref.add_argument("--lines", required=True, help="L10 or L10-L24")
    ref.set_defaults(func=_evidence_code_ref)

    gate = sub.add_parser("gate", help="fail if any published statement lacks usable evidence")
    gate.add_argument("run", type=Path, nargs="?", help="run folder (writes qa/gate.json)")
    gate.add_argument("--manifest", type=Path, help="evidence manifest from a docs pull request")
    gate.add_argument("--docs-root", type=Path, default=Path("."), help="docs repo root for --manifest")
    gate.set_defaults(func=_gate)

    publish = sub.add_parser("publish", help="prepare a docs pull request; `open` pushes it after approval")
    publish_sub = publish.add_subparsers(dest="publish_command", required=True)
    prepare = publish_sub.add_parser("prepare", help="gate the run, commit pages to a local branch, write the PR")
    prepare.add_argument("run", type=Path)
    prepare.add_argument("--docs-checkout", type=Path, required=True, help="local clone of the docs repo")
    prepare.add_argument("--place", type=_place_arg, action="append", default=[],
                         metavar="RUN-FILE=DOCS-PATH",
                         help="where a run page goes in the docs repo (repeatable; default: the pack's placement)")
    prepare.add_argument("--collection", metavar="OWNER/REPO", help="docs repo (default: the run's --publish-to)")
    prepare.add_argument("--base", default="main", help="branch the pull request targets (default main)")
    prepare.add_argument("--title")
    prepare.add_argument("--config", default="docforge.yaml")
    prepare.set_defaults(func=_publish_prepare)
    update = publish_sub.add_parser("update", help="gate a revised run and add a follow-up commit (local only)")
    update.add_argument("run", type=Path)
    update.add_argument("--docs-checkout", type=Path, required=True, help="the clone used by publish prepare")
    update.add_argument("--config", default="docforge.yaml")
    update.set_defaults(func=_publish_update)
    ready = publish_sub.add_parser("ready", help="record that the source change merged; --apply marks it on GitHub")
    ready.add_argument("run", type=Path)
    ready.add_argument("--source-state", required=True, choices=("open", "merged"))
    ready.add_argument("--apply", action="store_true", help="also mark the pull request ready on GitHub")
    ready.add_argument("--config", default="docforge.yaml")
    ready.set_defaults(func=_publish_ready)
    popen = publish_sub.add_parser("open", help="push the branch and open (or update) the draft pull request")
    popen.add_argument("run", type=Path)
    popen.add_argument("--docs-checkout", type=Path, required=True, help="the clone used by publish prepare")
    popen.add_argument("--config", default="docforge.yaml")
    popen.set_defaults(func=_publish_open)

    from docforge.review import CLOSE_REASONS

    review = sub.add_parser("review", help="review suggestions: request changes, close with a reason, web UI")
    review_sub = review.add_subparsers(dest="review_command", required=True)
    rserve = review_sub.add_parser("serve", help="local web UI for suggestions (records feedback only)")
    rserve.add_argument("--runs", type=Path, default=Path("output"), help="folder of run folders (or one run)")
    rserve.add_argument("--host", default="127.0.0.1")
    rserve.add_argument("--port", type=int, default=8790)
    rserve.add_argument("--reviewer", help="name prefilled in the forms")
    rserve.set_defaults(func=_review_serve)
    rchanges = review_sub.add_parser("request-changes", help="record a change request and write a revision order")
    rchanges.add_argument("run", type=Path)
    rchanges.add_argument("--comment", required=True)
    rchanges.add_argument("--reviewer", required=True)
    rchanges.add_argument("--page", help="docs path the comment is about")
    rchanges.add_argument("--line", type=int)
    rchanges.set_defaults(func=_review_request_changes)
    rclose = review_sub.add_parser("close", help="close a suggestion with one of six reasons")
    rclose.add_argument("run", type=Path)
    rclose.add_argument("--reason", required=True, choices=sorted(CLOSE_REASONS))
    rclose.add_argument("--note", default="")
    rclose.add_argument("--reviewer", required=True)
    rclose.set_defaults(func=_review_close)

    lint = sub.add_parser("lint", help="Vale style check on a run's changed prose, with safe fixes")
    lint.add_argument("run", type=Path)
    lint.add_argument("--all", action="store_true", help="report alerts on every line, not only changed prose")
    lint.add_argument("--fix", action="store_true", help="show the fixes Vale can make safely")
    lint.add_argument("--apply", action="store_true", help="write the safe fixes (re-runs the claim gate)")
    lint.add_argument("--vale-config", type=Path, help="Vale config (default: DocForge's .vale.ini)")
    lint.set_defaults(func=_lint)

    rules = sub.add_parser("rules", help="learned rules: propose, try against past runs, approve")
    rules.add_argument("--rules-dir", type=Path, help="rules folder (default $DOCFORGE_RULES_DIR or knowledge/rules)")
    rules_sub = rules.add_subparsers(dest="rules_command", required=True)
    rules_sub.add_parser("list", help="list rules and their status").set_defaults(func=_rules)
    rsuggest = rules_sub.add_parser("suggest", help="gather review feedback across runs as JSON")
    rsuggest.add_argument("--runs", type=Path, nargs="+", default=[Path("output")])
    rsuggest.set_defaults(func=_rules)
    rpropose = rules_sub.add_parser("propose", help="propose a rule from feedback")
    rpropose.add_argument("--kind", required=True, choices=("avoid", "guidance"))
    rpropose.add_argument("--title", required=True)
    rpropose.add_argument("--message", required=True, help="what a writer is told")
    rpropose.add_argument("--pattern", help="avoid: word or regular expression (Vale/RE2 syntax)")
    rpropose.add_argument("--replace", help="avoid: replacement, which makes the rule auto-fixable")
    rpropose.add_argument("--level", choices=("suggestion", "warning", "error"), default="warning")
    rpropose.add_argument("--case-sensitive", action="store_true")
    rpropose.add_argument("--guidance", help="guidance: the instruction for writers")
    rpropose.add_argument("--applies-to", action="append", default=[], help="only pages whose path contains this")
    rpropose.add_argument("--origin", type=_origin_arg, action="append", default=[], metavar="RUN:FEEDBACK-ID")
    rpropose.add_argument("--by", required=True, help="who proposes it")
    rpropose.set_defaults(func=_rules)
    rtest = rules_sub.add_parser("test", help="try a rule against past runs and save the report")
    rtest.add_argument("id")
    rtest.add_argument("--runs", type=Path, nargs="+", default=[Path("output")])
    rtest.set_defaults(func=_rules)
    rapprove = rules_sub.add_parser("approve", help="make a tested rule live")
    rapprove.add_argument("id")
    rapprove.add_argument("--by", required=True)
    rapprove.set_defaults(func=_rules)
    for name, help_text in (("reject", "reject a rule that is not live"), ("retire", "take a live rule out of use")):
        closer = rules_sub.add_parser(name, help=help_text)
        closer.add_argument("id")
        closer.add_argument("--by", required=True)
        closer.add_argument("--reason", required=True)
        closer.set_defaults(func=_rules)

    bf = sub.add_parser("backfill", help="replay past PRs and benchmark cases as an evaluation set")
    bf_sub = bf.add_subparsers(dest="backfill_command", required=True)
    bfetch = bf_sub.add_parser("fetch", help="save past PRs and diffs with gh (read-only)")
    bfetch.add_argument("repo", metavar="OWNER/REPO")
    bfetch.add_argument("--out", type=Path, required=True, help="new evaluation folder")
    bfetch.add_argument("--state", choices=("closed", "open", "all"), default="closed")
    bfetch.add_argument("--limit", type=int, default=30)
    bfetch.set_defaults(func=_backfill)
    blabel = bf_sub.add_parser("label", help="write a labels template for a person to fill in")
    blabel.add_argument("folder", type=Path)
    blabel.set_defaults(func=_backfill)
    breplay = bf_sub.add_parser("replay", help="decide every fetched PR again and compare with labels")
    breplay.add_argument("folder", type=Path)
    breplay.add_argument("--config", default="docforge.yaml")
    breplay.add_argument("--labels", type=Path, help="default: the folder's labels.json, if present")
    breplay.add_argument("--use-model", action="store_true",
                         help="let the triage model judge undecided PRs (paid calls; off by default)")
    breplay.set_defaults(func=_backfill)
    bprep = bf_sub.add_parser("prepare", help="create direct and staged arms for each benchmark case")
    bprep.add_argument("--cases", type=Path, default=Path("benchmarks/cases.json"))
    bprep.add_argument("--out", type=Path, required=True, help="new evaluation folder")
    bprep.add_argument("--repo", type=Path, default=Path("."))
    bprep.set_defaults(func=_backfill)
    bblind = bf_sub.add_parser("blind", help="copy finished outputs under random names for reviewers")
    bblind.add_argument("folder", type=Path)
    bblind.set_defaults(func=_backfill)
    bscore = bf_sub.add_parser("score", help="unblind and score reviewer judgments")
    bscore.add_argument("folder", type=Path)
    bscore.add_argument("--judgments", type=Path, required=True)
    bscore.set_defaults(func=_backfill)

    srcs = sub.add_parser("sources", help="fetch Jira issues and Confluence pages as source files (read-only)")
    srcs_sub = srcs.add_subparsers(dest="sources_command", required=True)
    sfetch = srcs_sub.add_parser("fetch", help="save one issue or page as Markdown with a provenance header")
    sfetch.add_argument("kind", choices=("jira", "confluence"))
    sfetch.add_argument("id", help="Jira issue key (PROJ-123) or Confluence page ID")
    sfetch.add_argument("--out", type=Path, required=True, help="new Markdown file; never overwritten")
    sfetch.add_argument("--config", default="docforge.yaml")
    sfetch.add_argument("--source", help="context_sources name, when more than one of this kind is configured")
    sfetch.set_defaults(func=_sources_fetch)
    sflow = srcs_sub.add_parser("flow", help="extract a step-by-step flow PDF into a citable flow source")
    sflow.add_argument("pdf", type=Path)
    sflow.add_argument("--id", required=True, help="flow ID used in citations, for example F1")
    sflow.add_argument("--out", type=Path, required=True, help="folder for <ID>.md and <ID>.json (never overwritten)")
    sflow.add_argument("--title", help="flow title (default: from the file name)")
    sflow.add_argument("--pack", help="use this pack's flow_profile (with --config)")
    sflow.add_argument("--config", default="docforge.yaml")
    sflow.set_defaults(func=_sources_flow)

    ntf = sub.add_parser("notify", help="notifications about suggestions (dry run unless --send)")
    ntf_sub = ntf.add_subparsers(dest="notify_command", required=True)
    nslack = ntf_sub.add_parser("slack", help="print, or with --send post, a short Slack message about a run")
    nslack.add_argument("run", type=Path)
    nslack.add_argument("--event", required=True, choices=("prepared", "revised", "closed", "ready"))
    nslack.add_argument("--config", help="docforge.yaml; sending needs a policy with slack_channel and slack_webhook_env")
    nslack.add_argument("--trigger", help="trigger name, for policy rules that match on it")
    nslack.add_argument("--pr-url", help="GitHub pull request URL to link")
    nslack.add_argument("--send", action="store_true", help="post the message (otherwise only print it)")
    nslack.set_defaults(func=_notify_slack)

    out_cmd = sub.add_parser("outdated", help="find existing articles a change has made outdated")
    out_sub = out_cmd.add_subparsers(dest="outdated_command", required=True)
    onote = out_sub.add_parser("note", help="the change note from a code diff: old and new UI wording")
    onote.add_argument("--code-checkout", type=Path, required=True)
    onote.add_argument("--base", required=True)
    onote.add_argument("--head", required=True)
    onote.add_argument("--spec-path", action="append", default=[], help="spec file pattern (repeatable)")
    onote.add_argument("--term", action="append", default=[], help="extra search term (repeatable)")
    onote.add_argument("--out", type=Path)
    onote.set_defaults(func=_outdated_note)
    oshort = out_sub.add_parser("shortlist", help="the pages the verdict passes would read (free)")
    oshort.add_argument("--note", type=Path, required=True, help="a change-note.json")
    oshort.add_argument("--docs", type=Path, required=True, help="docs checkout")
    oshort.add_argument("--collection", help="doc collection (filter, must-review keywords, cap)")
    oshort.add_argument("--must-review", action="append", default=[])
    oshort.add_argument("--cap", type=int)
    oshort.add_argument("--config", default="docforge.yaml")
    oshort.set_defaults(func=_outdated_shortlist)
    orun = out_sub.add_parser("run", help="note, shortlist, two verdict passes and the merge for a run")
    orun.add_argument("run", type=Path)
    orun.add_argument("--docs", type=Path, required=True, help="docs checkout")
    orun.add_argument("--repo", type=Path, default=Path("."), help="the folder run.json source paths are relative to")
    orun.add_argument("--collection")
    orun.add_argument("--code-checkout", type=Path)
    orun.add_argument("--spec-path", action="append", default=[])
    orun.add_argument("--config", default="docforge.yaml")
    orun.set_defaults(func=_outdated_run)
    ofix = out_sub.add_parser("fix", help="apply and check the paragraph-level fixes to existing articles")
    ofix.add_argument("run", type=Path)
    ofix.set_defaults(func=_outdated_fix)
    oeval = out_sub.add_parser("eval", help="recall on past changes (shortlist recall is free)")
    oeval.add_argument("cases", type=Path)
    oeval.add_argument("--docs", type=Path, required=True)
    oeval.add_argument("--collection")
    oeval.add_argument("--config", default="docforge.yaml")
    oeval.set_defaults(func=_outdated_eval)
    ocases = out_sub.add_parser("cases", help="propose past-change cases from the docs repository's history")
    ocases.add_argument("--docs-checkout", type=Path, required=True)
    ocases.add_argument("--out", type=Path, required=True)
    ocases.add_argument("--collection")
    ocases.add_argument("--limit", type=int, default=300)
    ocases.add_argument("--config", default="docforge.yaml")
    ocases.set_defaults(func=_outdated_cases)

    plan_cmd = sub.add_parser("plan", help="the documentation plan as ia-plan.md and its pull request")
    plan_sub = plan_cmd.add_subparsers(dest="plan_command", required=True)
    pcheck_plan = plan_sub.add_parser("check", help="check a run's analysis/ia-plan.md (or an ia-plan.md file)")
    pcheck_plan.add_argument("target", type=Path, help="a run folder or an ia-plan.md file")
    pcheck_plan.add_argument("--config", default="docforge.yaml", help="checks docs paths against the collection")
    pcheck_plan.set_defaults(func=_plan_check)
    pprep = plan_sub.add_parser("prepare", help="commit the run's ia-plan.md to a local plan branch (never pushes)")
    pprep.add_argument("run", type=Path)
    pprep.add_argument("--docs-checkout", type=Path, required=True)
    pprep.add_argument("--collection", metavar="OWNER/REPO")
    pprep.add_argument("--base", default="main")
    pprep.add_argument("--config", default="docforge.yaml")
    pprep.set_defaults(func=_plan_prepare)
    popen_plan = plan_sub.add_parser("open", help="push the plan branch and open the plan pull request")
    popen_plan.add_argument("run", type=Path)
    popen_plan.add_argument("--docs-checkout", type=Path, required=True)
    popen_plan.add_argument("--config", default="docforge.yaml")
    popen_plan.set_defaults(func=_plan_open)

    pk = sub.add_parser("pack", help="house packs: conventions, references and article specs")
    pk_sub = pk.add_subparsers(dest="pack_command", required=True)
    pcheck = pk_sub.add_parser("check", help="validate a pack folder (or a pack name with --config) and print its hash")
    pcheck.add_argument("path", type=Path, help="pack folder; with --config, a pack name")
    pcheck.add_argument("--config", help="docforge.yaml, to look up a pack by name")
    pcheck.set_defaults(func=_pack_check)

    clean = sub.add_parser("cleanup", help="run the pack's clean-up steps on a run's pages (preview unless --apply)")
    clean.add_argument("run", type=Path)
    clean.add_argument("--apply", action="store_true", help="write the changes and qa/CLEANUP-REPORT.md")
    clean.set_defaults(func=_cleanup)

    jira = sub.add_parser("jira", help="the Jira front door: handle ticket webhooks, show ticket state")
    jira_sub = jira.add_subparsers(dest="jira_command", required=True)
    jhandle = jira_sub.add_parser("handle", help="handle one webhook delivery (a saved payload)")
    jhandle.add_argument("payload", type=Path)
    jhandle.add_argument("--trigger", required=True, help="jira_ticket trigger name in docforge.yaml")
    jhandle.add_argument("--config", default="docforge.yaml")
    jhandle.add_argument("--state", type=Path, default=Path(".docforge/jira"), help="ticket state folder")
    jhandle.add_argument("--signature", help="the delivery's X-Hub-Signature header")
    jhandle.add_argument("--unsigned", action="store_true", help="skip the signature check (local recordings only)")
    jhandle.add_argument("--delivery-id", help="the delivery's X-Atlassian-Webhook-Identifier header")
    jhandle.set_defaults(func=_jira)
    jrun = jira_sub.add_parser("run", help="run a ticket's pending work (plan, revise, draft) as far as it can go")
    jrun.add_argument("key", nargs="?")
    jrun.add_argument("--all", action="store_true", help="every ticket with pending work")
    jrun.add_argument("--trigger", required=True)
    jrun.add_argument("--config", default="docforge.yaml")
    jrun.add_argument("--state", type=Path, default=Path(".docforge/jira"))
    jrun.set_defaults(func=_jira)
    jstate = jira_sub.add_parser("state", help="show a ticket's phase, pending work and outbox")
    jstate.add_argument("key")
    jstate.add_argument("--state", type=Path, default=Path(".docforge/jira"))
    jstate.set_defaults(func=_jira)

    run = sub.add_parser("run", help="start, track and check a documentation run")
    run_sub = run.add_subparsers(dest="run_command", required=True)
    start = run_sub.add_parser("start", help="create a new run folder with a manifest and stage work orders")
    start.add_argument("--prd", action="append", required=True, help="source file inside the repo (repeatable)")
    start.add_argument("--out", type=Path, required=True, help="new run folder, for example output/<slug>")
    start.add_argument("--pack", help="house pack name from docforge.yaml's packs section")
    start.add_argument("--config", default="docforge.yaml", help="docforge.yaml, for --pack")
    start.add_argument("--product", help="product key from the pack, to include that product's references")
    start.add_argument("--flow", action="append", help="flow source from `docforge sources flow` (repeatable)")
    start.add_argument("--flow-steps", choices=("required", "optional"), default="required",
                       help="whether every numbered step must cite a flow-backed claim (default required)")
    start.add_argument("--context", action="append",
                       help="supporting source inside the repo, recorded with authority 'context' (repeatable)")
    start.add_argument("--audience", required=True)
    start.add_argument("--docs", type=Path, help="existing docs folder to index and match against")
    start.add_argument("--docs-include", action="append",
                       help="only index pages under this docs-relative path (repeatable; dirs end in /)")
    start.add_argument("--profile", choices=("default", "custom"), default="default")
    start.add_argument("--deliverable", action="append", help="custom profile: run-relative Markdown path")
    start.add_argument("--repo", type=Path, default=Path("."), help="repository root (default: current folder)")
    start.add_argument("--code", metavar="OWNER/REPO", help="product code repo; adds a Research stage")
    start.add_argument("--base", help="base commit SHA of the product change (with --code)")
    start.add_argument("--head", help="head commit SHA of the product change (with --code)")
    start.add_argument("--publish-to", metavar="OWNER/REPO", help="docs repo the pages will be proposed to")
    start.add_argument("--source-pr", metavar="OWNER/REPO#N", help="the product pull request this run documents")
    start.add_argument("--source-state", choices=("open", "merged"), help="state of --source-pr (default open)")
    start.set_defaults(func=_run_start)
    rexec = run_sub.add_parser("exec", help="run the stages through the Anthropic API (needs a backend section)")
    rexec.add_argument("out", type=Path)
    rexec.add_argument("--repo", type=Path, default=Path("."), help="root that run.json source paths are relative to")
    rexec.add_argument("--config", default="docforge.yaml")
    rexec.add_argument("--stage", type=int, help="run only this stage number")
    rexec.add_argument("--dry-run", action="store_true", help="write the requests and estimates; call nothing")
    rexec.add_argument("--repair", type=int, default=0, help="repair turns after failed checks (0-2, default 0)")
    rexec.set_defaults(func=_run_exec)
    status = run_sub.add_parser("status", help="show which stages have their files and what comes next")
    status.add_argument("out", type=Path)
    status.set_defaults(func=_run_status)
    check = run_sub.add_parser("check", help="run the structural checker and lint; save qa/checks.json")
    check.add_argument("out", type=Path)
    check.add_argument("--repo", type=Path, default=Path("."),
                       help="root that run.json source paths are relative to (default: current folder)")
    check.add_argument("--code-root", type=_checkout_arg, action="append", default=[], metavar="OWNER/REPO=PATH",
                       help="local checkout used to verify code evidence (repeatable)")
    check.set_defaults(func=_run_check)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
