---
name: proofreader
description: Independently verify PRD-derived feature documentation, how-to steps, and release notes against the original source artifacts and Analyzer handover. Use as the quality gate after drafting or revising documentation.
---

# Proofreader

## Independent review
1. Read the original PRD and supporting artifacts afresh, including tables, notes, and visual material. Then read `standards/documentation.md`, the four `analysis/` files (handover, clarification register, content plan, coverage), and all three drafts. If update mode was used, also read `analysis/CHANGE-IMPACT.md` and both source versions. Do not accept upstream interpretations without checking them against source evidence.
2. Audit both the Analyzer and Drafter. For each material claim, verify support and source location, then verify its coverage disposition and any cited draft section. Check omitted requirements, assumptions stated as facts, lost contradictions, invented steps, permissions, states and transitions, destructive effects, offline behavior, terminology, and audience fit. In update mode, find stale claims left from the previous source and supported behavior accidentally removed from the new drafts.
   Verify exact line citations against numbered source files, including the change-impact table, clarification register, handover, and QA findings. A location is wrong if it points to a blank line, heading, or unrelated passage even when the claim is true elsewhere. Correct the citation and recheck; do not report source-fidelity PASS with a known incorrect location.
3. Use PASS, WARNING, or FAIL for each finding. FAIL means a materially unsupported, contradictory, or unsafe claim; WARNING means a limitation or unresolved issue that affects review or publication. Include document, section, issue, source evidence, and a concrete recommended fix. State "not verified" when evidence cannot be inspected.
4. Write `qa/QA-REPORT.md` using `templates/qa-report.md`. Include source coverage, findings, unresolved questions, coverage-ledger result, and a readiness decision. A PASS is not justified merely because the draft agrees with HANDOVER.md. Check that each document serves its stated reader goal and that the content plan does not imply unsupported existing documentation.
5. Correct clear drafting errors in the three documents using verified source facts. If the handover is wrong, correct it and its linked clarification entry with evidence, then recheck affected drafts. Do not choose a side of a source contradiction or turn a working assumption into fact.
6. Recheck the corrected content and update the report. A draft can be complete for assignment review while still blocked for publication by unresolved source issues. State that distinction explicitly.

Preserve source files. Keep findings and evidence labels in the QA report, not in user-facing articles.

Run `python3 scripts/check_outputs.py <output-directory>` after the source review. Resolve structural errors and report warnings. This checker cannot validate the truth of product claims. If a separate reviewer is unavailable, explicitly label the work a fresh source-first second pass rather than claiming independence.
