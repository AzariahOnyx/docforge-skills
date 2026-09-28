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
