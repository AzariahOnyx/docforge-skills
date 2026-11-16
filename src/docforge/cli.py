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
        record = run_checks(args.out, args.repo)
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
    verdict = "PASS" if structural["passed"] else "FAIL"
    print(f"{verdict}: {structural['checker']}; {len(record['lint_findings'])} lint finding(s). "
          f"Saved {args.out / 'qa' / 'checks.json'}.")
    print(record["note"])
    return 0 if structural["passed"] else 1


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
    start.set_defaults(func=_run_start)
    status = run_sub.add_parser("status", help="show which stages have their files and what comes next")
    status.add_argument("out", type=Path)
    status.set_defaults(func=_run_status)
    check = run_sub.add_parser("check", help="run the structural checker and lint; save qa/checks.json")
    check.add_argument("out", type=Path)
    check.add_argument("--repo", type=Path, default=Path("."),
                       help="root that run.json source paths are relative to (default: current folder)")
    check.set_defaults(func=_run_check)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
