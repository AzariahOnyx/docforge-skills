---
name: drafter
description: Draft audience-specific feature documentation, a task-focused how-to guide, and a concise release note from an Analyzer HANDOVER.md. Use after source analysis in a PRD documentation workflow, preserving evidence classifications and unresolved issues.
---

# Drafter

## Inputs
- Read `analysis/HANDOVER.md`, `analysis/clarifications-and-assumptions.md`, and `analysis/CONTENT-PLAN.md`.
- Read `docs/INPUT-CONTRACT.md`, `standards/documentation.md`, and the templates relevant to the requested deliverables. Consult the original sources only to confirm citations or a specifically identified gap; do not reinterpret unresolved product behavior independently.
- If the handover is absent or its source coverage is incomplete, stop and request Analyzer work.

## Draft
1. Map each candidate product claim to a claim ID in the handover. Use FACT claims for unqualified product behavior. Express a necessary working ASSUMPTION explicitly in review-facing material; do not present it as confirmed behavior. Do not assert INFERENCE, UNKNOWN, or either side of a CONTRADICTION as product fact.
2. If uncertainty blocks a safe procedure, omit the unsupported step or mark the draft as blocked for clarification. Never fabricate UI labels, sequences, permissions, defaults, availability, or outcomes.
3. Use the source's terminology consistently. Write directly for the audience and deliverable type recorded in `analysis/CONTENT-PLAN.md`. For the default three-document profile:
   - Feature guide: a first-time user's conceptual understanding, important behavior, limits, and links to tasks.
   - How-to: one supported user goal, prerequisites, numbered actions, expected result, and only necessary notes. Every how-to guide must include a separate `## Expected result` section.
   - Release note: a short change summary and supported user impact, optimized for scanning.
   For other requested types (for example, API reference or troubleshooting), define type-specific sections, evidence needs, and success criteria in the content plan. Do not invent endpoints, response schemas, error codes, fixes, or procedures.
4. For the default profile, follow templates/feature-doc.md, templates/how-to.md, and templates/release-note.md as adaptable structures. For custom profiles, use a source-supported structure documented in the content plan. Delete placeholder sections with no supported content. Do not copy template instructions into final documents.
5. For the default profile, write `feature/feature-guide.md`, `how-to/how-to.md`, and `release-note/release-note.md`. For a custom profile, write only the requested, supported documents at descriptive paths recorded in the content plan. Do not silently create unrelated articles.
6. Read `templates/coverage.md` and create `analysis/COVERAGE.md`: account for each HANDOVER claim exactly once as INCLUDED, CONTEXT, DEFERRED, or BLOCKED. An INCLUDED claim needs a draft path and section; the other dispositions need a reason. Record unsupported passages for review. Keep the claim map out of user-facing prose.
7. Report which passages or deliverables remain blocked by questions. Do not claim publication readiness before source-first proofreading and authorized human approval.

Do not modify the source artifacts or silently answer clarification questions.

## Custom profile evidence ledger

For a custom run, read `docs/RUN-FORMAT.md` and create `analysis/evidence.json`. Map included claims to existing deliverable paths and quote exact source evidence. The quote is for traceability, not proof of entailment. Cite source IDs and locators in drafts. Avoid generic API endpoints, fixes, or code examples when the source does not establish them. Use `docs/REVIEW-CHECKLIST.md` for accessibility and writing quality.
