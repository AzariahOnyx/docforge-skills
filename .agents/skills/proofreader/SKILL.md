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
   Run a separate audience and style review under `standards/documentation.md`: verify that the feature guide orients a first-time user, the how-to performs a meaningful supported task when one exists, and the release note announces distinct changes for an existing user. Flag a one-word generic title, a view-only how-to chosen despite a fully supported substantive task, or a release note that merely repeats the overview. Verify the clarity and grammar of every heading, table, step, and link. An accurate but audience-mismatched draft needs revision, not an unqualified editorial PASS.
4. Write `qa/QA-REPORT.md` using `templates/qa-report.md`. Include source coverage, findings, unresolved questions, coverage-ledger result, and a readiness decision. A PASS is not justified merely because the draft agrees with HANDOVER.md. Check that each document serves its stated reader goal and that the content plan does not imply unsupported existing documentation.
5. Correct clear drafting errors in the three documents using verified source facts. If the handover is wrong, correct it and its linked clarification entry with evidence, then recheck affected drafts. Do not choose a side of a source contradiction or turn a working assumption into fact.
   Ensure each material gap has an explicit safe editorial decision and documentation impact in the clarification register, without inventing a product outcome. Keep disputed source passages in analysis and QA; do not expose internal requirement conflicts as customer-facing text. If withholding a destructive or data-loss outcome makes a guide unsafe, mark publication blocked.
6. Recheck the corrected content and update the report. A draft can be complete for assignment review while still blocked for publication by unresolved source issues. State that distinction explicitly.

Preserve source files. Keep findings and evidence labels in the QA report, not in user-facing articles.

Run `python3 scripts/check_outputs.py <output-directory>` after the source review. Resolve structural errors and report warnings. This checker cannot validate the truth of product claims. If a separate reviewer is unavailable, explicitly label the work a fresh source-first second pass rather than claiming independence.
## Adversarial editorial gate

Run this separately from source-fidelity review. Do not give an editorial PASS merely because every statement is supported.

Review every reader-facing sentence and section as a senior software technical writer:

- **Need:** Does the target reader need this information in this document?
- **Placement:** Is it in the right document and section, or is supported reference/edge-case detail crowding the primary goal?
- **Naturalness:** Does it read as polished documentation rather than paraphrased PRD, handover, or product-team language?
- **Information design:** Would a table, procedure, note/warning, or state representation communicate the relationship better than prose?
- **Task quality:** If the assignment asks for a substantial how-to, does the selected procedure actually meet that bar? A technically valid but trivial procedure is a WARNING or FAIL for assignment fit unless no substantial supported task exists and that limitation is explicit.
- **Release-note quality:** Does the note communicate a supported change and practical impact for an existing user rather than merely summarize the feature guide?
- **Feature-guide quality:** Does it establish a newcomer mental model and prioritize core behavior before reference details and edge cases?
- **Duplication and density:** Remove repeated explanation and low-value detail that does not serve the document's reader goal.
- **Polish:** Check every sentence for concise, active, natural English and every file for clean Markdown, including leading/trailing blank lines.

Use severity deliberately: source errors and unsafe claims are FAIL; audience/assignment failures can also be FAIL even when technically accurate; lesser editorial weaknesses are WARNING. Record the editorial verdict separately from the technical-fidelity verdict, and require both to pass for an unqualified assignment-ready result.


## Editorial blueprint review

Require `analysis/EDITORIAL-BLUEPRINT.md` and check its decisions against the original source.

Review the declared reader job and success test for each document. Confirm that the feature guide has a coherent newcomer mental model, the selected how-to has supported start/action/result evidence, and the release note is a focused scan of distinct changes rather than a shortened feature guide. Check the PRIMARY/BRIEF/OMIT separation across documents and confirm that editorial compression has not hidden a material consequence.

The blueprint must contain a completed Draft challenge result. If a supported editorial issue can be corrected from existing evidence, revise and run source-fidelity and editorial review again. Use no more than two correction cycles; record any remaining material issue in QA.
