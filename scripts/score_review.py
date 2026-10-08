#!/usr/bin/env python3
"""Summarize human judgments for fictional benchmark assertions.

This program does not perform evaluation itself. It summarizes supplied
reviewer decisions and refuses missing or duplicate case assertions.
"""
import argparse
import json
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("judgments", type=Path)
    p.add_argument("--cases", type=Path, default=Path(__file__).resolve().parents[1] / "benchmarks/cases.json")
    a = p.parse_args()
    cases = json.loads(a.cases.read_text(encoding="utf-8"))["cases"]
    expected = {(c["id"], i) for c in cases for i in range(len(c["expected"]))}
    rows = json.loads(a.judgments.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        p.error("judgments must be an array")
    seen, counts = set(), {"pass": 0, "fail": 0, "uncertain": 0}
    for row in rows:
        key = (row.get("case_id"), row.get("assertion_index"))
        if key not in expected or key in seen:
            p.error(f"unknown or duplicate judgment: {key}")
        seen.add(key)
        result = row.get("result")
        if result not in counts:
            p.error(f"invalid result: {result}")
        if not isinstance(row.get("reviewer"), str) or not row["reviewer"].strip():
            p.error(f"missing reviewer for {key}")
        if not isinstance(row.get("evidence"), str) or not row["evidence"].strip():
            p.error(f"missing evidence for {key}")
        counts[result] += 1
    missing = expected - seen
    if missing:
        p.error(f"{len(missing)} assertions have no judgment")
    total = sum(counts.values())
    print(json.dumps({"total": total, **counts, "pass_rate": counts["pass"] / total if total else None}, indent=2))
    print("Judgments are supplied by reviewers; this script does not independently verify them.")

if __name__ == "__main__":
    main()
