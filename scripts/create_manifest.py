#!/usr/bin/env python3
"""Create a run manifest with reproducible source hashes."""
import argparse
import hashlib
import json
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True)
    p.add_argument("--source", required=True, action="append", help="Repository-relative path, repeatable")
    p.add_argument("--deliverable", required=True, action="append", help="Run-relative Markdown path, repeatable")
    p.add_argument("--audience", required=True)
    p.add_argument("--profile", choices=("default", "custom"), default="custom")
    p.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    args = p.parse_args()
    repo = Path(args.repo).resolve()
    run = Path(args.run).resolve()
    sources = []
    for i, name in enumerate(args.source, 1):
        path = (repo / name).resolve()
        if not path.is_relative_to(repo) or not path.is_file():
            p.error(f"invalid source: {name}")
        sources.append({"id": f"S{i}", "path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "authority": "unconfirmed"})
    run.mkdir(parents=True, exist_ok=True)
    output = run / "run.json"
    if output.exists():
        p.error(f"run manifest already exists: {output}")
    output.write_text(json.dumps({
        "schema_version": 1, "profile": args.profile, "audience": args.audience,
        "sources": sources, "deliverables": args.deliverable,
        "review": {"method": "not_reviewed", "source_fidelity": "pending",
                   "product_verification": "pending", "human_approval": "pending"}
    }, indent=2) + "\n", encoding="utf-8")
    print(output)

if __name__ == "__main__":
    main()
