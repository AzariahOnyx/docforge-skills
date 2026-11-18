"""Read the steps of a flow source (the Markdown written by `docforge sources flow`).

Standard library only, so the scripts in scripts/ can check flow citations.
A flow source has one `## Step N of M` section per step; a citation such as
[F1#step3] or [F1#step3-5] names steps that must exist.
"""

from __future__ import annotations

import re
from typing import Optional

FLOW_MARKER = "kind: flow"
STEP_HEADING = re.compile(r"^## Step (\d+) of (\d+)\s*$", re.M)
STEP_LOCATOR = re.compile(r"step(\d+)(?:-(\d+))?")
FLOW_CITATION = re.compile(r"\[(F\d+)#(step\d+(?:-\d+)?)\]")


def is_flow(text: str) -> bool:
    head = text[:2000]
    return head.startswith("<!-- docforge-source") and FLOW_MARKER in head.split("-->", 1)[0]


def flow_steps(text: str) -> dict[int, str]:
    """{step number: step text} for a flow source; empty if `text` is not one."""
    if not is_flow(text):
        return {}
    matches = list(STEP_HEADING.finditer(text))
    steps: dict[int, str] = {}
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        steps[int(match.group(1))] = text[match.end():end].strip()
    return steps


def step_range(locator: str) -> Optional[tuple[int, int]]:
    match = STEP_LOCATOR.fullmatch(locator)
    if not match:
        return None
    first = int(match.group(1))
    last = int(match.group(2) or first)
    return (first, last) if 1 <= first <= last else None


def check_citation(steps: dict[int, str], locator: str) -> Optional[str]:
    """An error message, or None if every step the locator names exists."""
    bounds = step_range(locator)
    if bounds is None:
        return f"invalid step locator {locator}"
    missing = [n for n in range(bounds[0], bounds[1] + 1) if n not in steps]
    if missing:
        return f"flow has no step {missing[0]}"
    return None


def run_flows(run_dir, sources: list) -> tuple[dict, list[str]]:
    """({flow ID: steps}, errors) from the flow copies a run keeps (`copy` in run.json), hash-checked."""
    import hashlib
    from pathlib import Path

    flows: dict = {}
    errors: list[str] = []
    for source in sources:
        if not isinstance(source, dict) or source.get("kind") != "flow":
            continue
        copy = source.get("copy")
        path = Path(run_dir) / copy if isinstance(copy, str) else None
        if path is None or not path.is_file():
            errors.append(f"flow source {source.get('id')}: the run's copy {copy} is missing")
            continue
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != source.get("sha256"):
            errors.append(f"flow source {source.get('id')}: the run's copy {copy} does not match its sha256")
            continue
        flows[source["id"]] = flow_steps(data.decode("utf-8"))
    return flows, errors
