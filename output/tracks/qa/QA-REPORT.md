# Tracks — documentation QA report

## Scope and source coverage

- Original source inspected: `input/Technical Writer - Case Study.pdf`, all six pages, with extracted text and rendered-page review. Assignment instructions are on pp. 1-2; the Tracks working PRD is on pp. 2-6. The permissions table on p. 5 and assignment table on p. 1 were visually checked.
- Review artifacts: `analysis/HANDOVER.md`, `analysis/clarifications-and-assumptions.md`, `analysis/CONTENT-PLAN.md`, and `analysis/COVERAGE.md`.
- Drafts checked: `feature/feature-guide.md`, `how-to/how-to.md`, and `release-note/release-note.md`.
- No supporting screenshots, product build, style guide, or other artifacts were provided. This is a source-fidelity review, not implementation verification.

## Findings

| Status | Document / section | Issue or check | Source evidence | Resolution |
| --- | --- | --- | --- | --- |
| WARNING | Source and handover / Q01 | Disabling Tracks has incompatible retention rules. The drafts must not say whether data survives or must be rebuilt. | PDF p. 3, Capabilities says hide and restore; p. 5, Lifecycle says clear and rebuild; p. 6, US-4 only confirms pill hidden. | Both claims preserved as C20A/C20B; disable effects omitted from all three reader-facing drafts. Product clarification remains required. |
| PASS | Feature guide / states and board | Task status and per-track status remain distinct; open-only board and multi-column behavior match the PRD. | PDF pp. 2-4, Task status, Scope, Layout, Lifecycle. | Verified against C03, C06-C09, C17. |
| PASS | Feature guide / close and reopen | Closed task leaves the board but retains pill statuses; reopening restores placements. | PDF p. 4, Lifecycle rules; p. 6, US-4. | Verified against C17/C30. |
| PASS | Feature guide / destructive actions | Track deletion and cross-project move consequences are stated without an invented undo or confirmation UI. | PDF pp. 4-5, Lifecycle rules. | Verified against C18/C21. |
| WARNING | Feature guide / permissions | The permission table omits Delete a track. Guest access and task/project access criteria also need detail. | PDF p. 5, Permissions; pp. 3-4, Capabilities and track actions. | No delete-role claim or invented access rule; Q03/Q08 open. |
| WARNING | Feature guide / counters and Stop | X/Y and pill count formulas and the result of Stop are insufficiently specified. | PDF pp. 3-4, Layout and pill; p. 6, US-3. | Counter calculation and Stop result omitted; Q02/Q04/Q13 open. |
| PASS | How-to / Mark Done | Starting point, action, result, and unchanged other tracks follow the board, transition, and user story. | PDF p. 4, Actions on a task; p. 6, US-3; p. 5, Permissions. | Verified against C08/C12/C23/C28. |
| PASS | How-to / offline note | Mark Done may be used offline and queues locally for reconciliation. It does not promise a particular sync success message. | PDF p. 6, Offline behaviour. | Verified against C31; Q11 remains open. |
| PASS | Feature guide / state diagram | Start, Mark Done, and Mark Pending transitions are source-supported. Stop outcome is deliberately excluded. | PDF pp. 3-4, Scope and Tracks pill; p. 6, US-3. | Verified against C06/C15/C28 and Q04. |
| PASS | Release note / audience fit | Short change summary highlights distinct capabilities without step-by-step detail or unsupported release date. | PDF p. 1, Part 2; pp. 3-6, capabilities and lifecycle. | Verified; Q14 covers missing release metadata. |
| WARNING | All drafts / source status | The working PRD has not been checked against a running Tasket build. | PDF p. 1 calls the specification a working draft. | Treat as review drafts pending product confirmation, especially Q01. |

## Checks

- **Source fidelity and traceability: PASS for included claims.** The handover's claim IDs map to the three drafts. The original source, rather than the handover alone, was checked for each material passage.
- **Claim coverage: PASS with publication warning.** All 41 register claims have one disposition in `analysis/COVERAGE.md`; partial uses and unsupported topics are called out, especially C20A/C20B (Q01). This ledger supports review but does not resolve the source conflict.
- **Assumptions, unknowns, and contradictions: WARNING.** All 17 clarification entries carry an explicit editorial assumption. Q01 remains unresolved and no side is asserted.
- **Procedure, permissions, and states: PASS for the selected how-to; WARNING for broader coverage.** The Mark Done procedure uses a named board action on an open In Progress task. Enablement, deletion, bulk start, and closed-task editing lack sufficient detail for procedures.
- **Terminology, audience fit, clarity, and duplication: PASS.** The docs use task and track consistently; the conceptual guide, single-goal how-to, and scannable release note have distinct purposes.
- **Invented UI and availability: PASS.** No Save button, settings path, modal, confirmation, release date, or counter formula was added.
- **Content scope: PASS with warning.** The content plan identifies three new draft types and proposed update candidates; no existing Tasket documentation was supplied, so update targets remain unverified.
- **Structural checker: PASS.** `python3 scripts/check_outputs.py output/tracks` found eight required files, required headings, claim/question ID linkage, complete unique coverage rows, and valid local links, with zero errors or warnings. It cannot verify product truth.

## Corrections made and recheck

The drafting pass deliberately omitted the disable/re-enable retention claim and unsupported click paths before QA. The separate source-first QA pass found no remaining unsupported product claim requiring a post-draft correction. The three drafts were rechecked against the listed page locations. The unresolved source issues remain documented rather than silently fixed.

## Readiness

**Assignment review: PASS with warnings.** The clarification register and three distinct draft types are present, and the reusable skill is separate.

**Publication: BLOCKED for a complete Tracks lifecycle account.** Q01 must be answered before writing data-retention, disable, or re-enable instructions. Q02-Q17 should be triaged with the product team before publishing affected details. The selected Mark Done procedure is source-supported but has not been validated in a product build.
