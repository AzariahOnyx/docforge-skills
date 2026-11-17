"""Gather review feedback across runs, for a person or this session to draft rules from.

Turning a comment into a rule is a judgement call, so this only collects:
close-reason counts and every change request with where it came from, plus
which feedback is already the origin of a rule.
"""

from __future__ import annotations

import json
from pathlib import Path

from .model import load_rules
from .trial import find_runs


def feedback_digest(paths: list[Path], folder: Path) -> dict:
    used = {(o.run, o.feedback_id) for rule in load_rules(folder) for o in rule.origins}
    reasons: dict[str, int] = {}
    requests = []
    runs = find_runs(paths)
    for run in runs:
        path = run / "review" / "feedback.jsonl"
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if item.get("action") == "close" and item.get("reason"):
                reasons[item["reason"]] = reasons.get(item["reason"], 0) + 1
            if item.get("action") in ("request_changes", "close") and (item.get("comment") or "").strip():
                requests.append({
                    "run": item["run"], "feedback_id": item["feedback_id"], "action": item["action"],
                    "reason": item.get("reason"), "page": item.get("page"), "comment": item["comment"],
                    "already_a_rule": (item["run"], item["feedback_id"]) in used,
                })
    return {"runs": [r.name for r in runs], "close_reasons": dict(sorted(reasons.items())), "feedback": requests}
