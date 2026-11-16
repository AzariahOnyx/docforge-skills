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
        hits = search(args.path, args.query, field=args.in_, limit=args.limit, collection=collection)
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
    search.add_argument("--json", action="store_true", help="print results as JSON")
    _add_collection_args(search)
    search.set_defaults(func=_search)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
