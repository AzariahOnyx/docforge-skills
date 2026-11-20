"""Run the outdated content finder on a documentation run (between the Analyzer and the plan pull request).

Files in the run: analysis/change-note.json, analysis/outdated-shortlist.json, outdated/pass-1.json and
pass-2.json (the verdict passes), analysis/outdated.json and analysis/OUTDATED.md (the merged result), and
the updated "Existing articles - impact" table of analysis/ia-plan.md.
"""

from __future__ import annotations

import json
from pathlib import Path

from docforge.config import DocForgeConfig

from .merge import merge_into_plan
from .note import ChangeNote, note_from_code, note_from_sources
from .shortlist import build_shortlist
from .verdicts import check_pass, merge_passes, render_report, run_passes

NOTE = "analysis/change-note.json"
SHORTLIST = "analysis/outdated-shortlist.json"
RESULT = "analysis/outdated.json"
REPORT = "analysis/OUTDATED.md"


def _write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def make_note(run: Path, repo: Path, *, code_checkout: Path | None = None, spec_paths=(), terms=()) -> ChangeNote:
    """The run's change note: from its code change when it has one and a checkout is given, else from the bold
    UI labels in its sources. The plan's feature name is added as a term."""
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    plan_terms = []
    plan_file = run / "analysis" / "ia-plan.md"
    if plan_file.is_file():
        from docforge.plan.model import parse_plan

        plan, _ = parse_plan(plan_file.read_text(encoding="utf-8"))
        if plan and isinstance(plan.front.get("feature"), str) and plan.front["feature"] != "unknown":
            plan_terms.append(plan.front["feature"])
    code = manifest.get("code")
    if code and code_checkout is not None:
        return note_from_code(code_checkout, code["base"], code["head"], spec_paths=spec_paths,
                              terms=[*plan_terms, *terms])
    texts = [(repo / s["path"]).read_text(encoding="utf-8") for s in manifest.get("sources", [])
             if (repo / s["path"]).is_file()]
    return note_from_sources(texts, terms=[*plan_terms, *terms])


def find_outdated(run: Path, repo: Path, config: DocForgeConfig, *, docs: Path, collection: str,
                  code_checkout: Path | None = None, spec_paths=(), client=None) -> str:
    """'done', 'waiting' (the two passes are work orders for sessions) or an error message."""
    target = config.doc_collections.get(collection)
    if (run / RESULT).is_file():
        return "done"
    if not (run / NOTE).is_file():
        _write(run / NOTE, make_note(run, repo, code_checkout=code_checkout, spec_paths=spec_paths).to_dict())
    note = json.loads((run / NOTE).read_text(encoding="utf-8"))
    if not (run / SHORTLIST).is_file():
        shortlist = build_shortlist(docs, ChangeNote.from_dict(note), collection=target,
                                    must_review=target.must_review if target else [],
                                    cap=target.outdated_cap if target else 25)
        _write(run / SHORTLIST, shortlist)
    shortlist = json.loads((run / SHORTLIST).read_text(encoding="utf-8"))
    if shortlist["pages"]:
        passes = [run / "outdated" / f"pass-{n}.json" for n in (1, 2)]
        if not all(p.is_file() for p in passes):
            outcome = run_passes(run, config, note, shortlist, docs, client=client)
            if outcome != "done":
                return outcome
        first, second = (check_pass(json.loads(p.read_text(encoding="utf-8")), shortlist, docs) for p in passes)
        merged = merge_passes(first, second, shortlist)
    else:
        merged = []
    _write(run / RESULT, {"pages": merged, "must_review": shortlist["must_review"], "searched": shortlist["searched_pages"]})
    (run / REPORT).write_text(render_report(merged, shortlist), encoding="utf-8")
    plan_file = run / "analysis" / "ia-plan.md"
    if plan_file.is_file():
        text, changed = merge_into_plan(plan_file.read_text(encoding="utf-8"), merged, docs)
        if changed:
            plan_file.write_text(text, encoding="utf-8")
    return "done"
