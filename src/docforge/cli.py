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
    except (ConfigError, EventError, DiffError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    decision = decide(config, event, changed, diff_source=source)
    if not args.no_log:
        append_decision(args.log, decision)
        print(f"Logged decision {decision.decision_id} to {args.log}", file=sys.stderr)
    print(decision.model_dump_json(indent=2))
    return 0


def _serve(args: argparse.Namespace) -> int:
    import os

    from docforge.webhook import SECRET_ENV, Receiver, serve

    secret = os.environ.get(SECRET_ENV, "")
    if not secret:
        print(f"set {SECRET_ENV} to the webhook secret; unsigned deliveries are never accepted", file=sys.stderr)
        return 1
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        return 1
    receiver = Receiver(config=config, secret=secret.encode("utf-8"), log=args.log, checkouts=dict(args.checkout))
    serve(receiver, host=args.host, port=args.port)
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
    from docforge.publish import PublishError, mark_ready

    try:
        plan = mark_ready(args.run, args.source_state)
    except PublishError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Recorded that the source change is merged; {plan.branch} may leave draft. A person runs:")
    for command in plan.commands:
        print("  " + command)
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
            report = backfill.replay(args.folder, load_config(args.config), labels)
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
        state = load_state(args.state, args.key)
        if state is None:
            print(f"no state for {args.key} in {args.state}", file=sys.stderr)
            return 1
        print(f"{state.key}: phase {state.phase}, mode {state.mode}, revision {state.revision}, run {state.run or '-'}"
              + (f", pending {state.pending.action}" if state.pending else ""))
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

    serve_cmd = sub.add_parser("serve", help="receive GitHub webhooks and log decisions (records only)")
    serve_cmd.add_argument("--host", default="127.0.0.1")
    serve_cmd.add_argument("--port", type=int, default=8787)
    serve_cmd.add_argument("--config", default="docforge.yaml")
    serve_cmd.add_argument("--log", type=Path, default=DEFAULT_LOG)
    serve_cmd.add_argument("--checkout", type=_checkout_arg, action="append", default=[],
                           metavar="OWNER/REPO=PATH", help="local checkout used to diff that repo's PRs")
    serve_cmd.set_defaults(func=_serve)

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

    publish = sub.add_parser("publish", help="prepare a docs pull request (local only; never pushes)")
    publish_sub = publish.add_subparsers(dest="publish_command", required=True)
    prepare = publish_sub.add_parser("prepare", help="gate the run, commit pages to a local branch, write the PR")
    prepare.add_argument("run", type=Path)
    prepare.add_argument("--docs-checkout", type=Path, required=True, help="local clone of the docs repo")
    prepare.add_argument("--place", type=_place_arg, action="append", default=[], required=True,
                         metavar="RUN-FILE=DOCS-PATH", help="where a run page goes in the docs repo (repeatable)")
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
    ready = publish_sub.add_parser("ready", help="record that the source change merged; print the ready command")
    ready.add_argument("run", type=Path)
    ready.add_argument("--source-state", required=True, choices=("open", "merged"))
    ready.set_defaults(func=_publish_ready)

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
