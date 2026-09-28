---
name: drafter
description: Draft audience-specific feature documentation, a task-focused how-to guide, and a concise release note from an Analyzer HANDOVER.md. Use after source analysis in a PRD documentation workflow, preserving evidence classifications and unresolved issues.
---

# Drafter

## Inputs
- Read `analysis/HANDOVER.md`, `analysis/clarifications-and-assumptions.md`, and `analysis/CONTENT-PLAN.md`.
- Read `standards/documentation.md` and the three templates in `templates/`. Consult the original sources only to confirm citations or a specifically identified gap; do not reinterpret unresolved product behavior independently.
- If the handover is absent or its source coverage is incomplete, stop and request Analyzer work.

## Draft
1. Map each candidate product claim to a claim ID in the handover. Use FACT claims for unqualified product behavior. Express a necessary working ASSUMPTION explicitly in review-facing material; do not present it as confirmed behavior. Do not assert INFERENCE, UNKNOWN, or either side of a CONTRADICTION as product fact.
2. If uncertainty blocks a safe procedure, omit the unsupported step or mark the draft as blocked for clarification. Never fabricate UI labels, sequences, permissions, defaults, availability, or outcomes.
3. Use the source's terminology consistently. Write directly for each distinct audience:
   - Feature guide: a first-time user's conceptual understanding, important behavior, limits, and links to tasks.
   - How-to: one consequential supported user goal, prerequisites, numbered actions, expected result, and only necessary notes. Prefer a state-changing task when the source gives a complete procedure. Use a view-only task only if it is the assigned goal or no substantive procedure is fully supported; record why in the content plan. Every how-to guide must include a separate `## Expected result` section.
   - Release note: a change-focused title, concise practical benefit, two or three distinct supported changes, and a guide link where available. Write for existing users who scan. Do not invent a before-state, launch date, or rollout.
4. Follow templates/feature-doc.md, templates/how-to.md, and templates/release-note.md as adaptable structures. Delete placeholder sections with no supported content. Do not copy template instructions into final documents.
   Apply the current Microsoft Writing Style Guide as referenced in `standards/documentation.md` for clear English, sentence-case headings, and exact UI labels. Give the feature guide an informative title; avoid copying the same generic feature-name title across all three documents. Keep internal contradictions and editorial decisions in analysis/QA, not reader-facing prose; block publication where an omission conceals a material risk.
5. Write the three required deliverables as `feature/feature-guide.md`, `how-to/how-to.md`, and `release-note/release-note.md` in the specified output directory. Additional requested articles may use descriptive filenames in the appropriate folder.
6. Read `templates/coverage.md` and create `analysis/COVERAGE.md`: account for each HANDOVER claim exactly once as INCLUDED, CONTEXT, DEFERRED, or BLOCKED. An INCLUDED claim needs a draft path and section; the other dispositions need a reason. Record unsupported passages for review. Keep the claim map out of user-facing prose.
7. Report which passages or deliverables remain blocked by questions. Do not claim publication readiness before independent proofreading.

Do not modify the source artifacts or silently answer clarification questions.
## Senior editorial pass

After producing a source-faithful draft, revise it once as a senior software technical writer before handing it to the Proofreader.

- Do not paraphrase the PRD or handover sentence by sentence. Reconstruct the explanation from verified facts around the reader's goal and mental model. Remove wording that sounds like requirements language, internal product-team language, or a claim register.
- Apply this test to every paragraph: **Why does this reader need this here?** Keep essential and useful information; move or omit edge cases and reference detail unless they materially affect task success, safety, data loss, permissions, or irreversible behavior.
- Prefer natural, direct software-documentation English. Use the Microsoft Writing Style Guide for presentation, but preserve verified product terminology and exact UI labels.
- Choose structure by information type: comparison or condition/outcome → table; sequence → numbered steps; state model → concise table or source-backed diagram; destructive/irreversible consequence → prominent note or warning when the output format supports it; definition or concept → concise prose.
- Avoid invented behavioral examples. A neutral illustrative scenario is allowed only when it adds no new product behavior, UI, role, permission, limit, state, or outcome; otherwise omit it.
- Feature guide rhetorical flow: **user purpose → mental model → core behavior → important consequences/limits → supported next task**. Do not turn the guide into a requirements inventory or permissions/reference dump.
- How-to rhetorical flow: **goal → prerequisites → actions → observable result → supported recovery/next step**. Reassess whether the selected task is substantial enough for the assignment. If it is not, return to the content plan and choose a better fully supported candidate; if none exists, state the limitation in review artifacts.
- Release-note rhetorical flow: **change → practical user impact → two or three distinguishing capabilities/effects → learn more**. It must not read like a shortened feature guide.
- Remove duplication across the three deliverables unless repetition is necessary for the reader to complete the document's goal.
- Normalize final Markdown: no unexplained leading blank lines, placeholders, empty sections, or formatting artifacts.


## Editorial blueprint gate

Before reader-facing drafting, read `templates/editorial-blueprint.md` and create `analysis/EDITORIAL-BLUEPRINT.md`. Complete its document contracts, feature-guide plan, how-to candidate comparison, release-note priorities, cross-document separation, and pre-draft challenge from the Analyzer evidence.

Draft only after the blueprint records PASS. Build the feature guide around the reader's mental model rather than PRD order. Select the how-to with the strongest complete evidence for starting state, action, and observable result. Select no more than three distinct release-note priorities unless the assignment asks for more.

After drafting, compare every section with its document contract. Rewrite requirements-shaped prose into natural user documentation without changing product meaning. Remove low-value repetition and reference detail that does not serve the reader job, while retaining material permissions, lifecycle effects, irreversible consequences, and data-retention risks.

Append `## Draft challenge result` to the blueprint with PASS or BLOCKED and a concise record of revisions. Keep this review material out of reader-facing files.
