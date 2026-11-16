"""Command-line entry point: `docforge`."""

from __future__ import annotations

import argparse
import json
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
    from docforge.run import RunError, start_run

    try:
        out = start_run(
            repo=args.repo, prds=args.prd, out=args.out, audience=args.audience, docs=args.docs,
            profile=args.profile, deliverables=args.deliverable, docs_include=args.docs_include,
            code_repo=args.code, base=args.base, head=args.head,
        )
    except (RunError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Started run {out}")
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
    passed = structural["passed"] and (research is None or research["passed"])
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


def _add_collection_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--collection", help="limit to a doc_collections entry's filter (owner/repo)")
    parser.add_argument("--config", default="docforge.yaml", help="config used with --collection")


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

    run = sub.add_parser("run", help="start, track and check a documentation run")
    run_sub = run.add_subparsers(dest="run_command", required=True)
    start = run_sub.add_parser("start", help="create a new run folder with a manifest and stage work orders")
    start.add_argument("--prd", action="append", required=True, help="source file inside the repo (repeatable)")
    start.add_argument("--out", type=Path, required=True, help="new run folder, for example output/<slug>")
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
    start.set_defaults(func=_run_start)
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
