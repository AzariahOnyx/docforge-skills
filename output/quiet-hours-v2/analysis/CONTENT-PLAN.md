# Quiet Hours — content scope and change plan

## Source and existing-content inventory

- Current evidence: `demo/mock-prd-v2.md`, all sections. Previous source and output are used for comparison only; see `CHANGE-IMPACT.md`.
- No existing Pulseboard documentation was supplied; existence, names, and navigation of help pages are UNKNOWN.
- Three requested reader goals: understand the feature, complete one task, scan the change.

## Scope decisions

| Topic / reader goal | Action | Destination or candidate | Evidence | Open questions | Reason |
| --- | --- | --- | --- | --- | --- |
| Understand which alerts are paused and how they resume | UPDATE in new output | `feature/feature-guide.md` | C01-C07, C12, revised PRD Product context through Permissions | Q01-Q03 | Change fixed option and online resume requirement without inventing delivery semantics. |
| Pause in-app alerts for 2 hours | UPDATE in new output | `how-to/how-to.md` | C03-C07, C12, revised PRD UI and workflow, Permissions | Q03 | Replace former 1-hour procedure with supported 2-hour goal. |
| Announce Quiet Hours | UPDATE in new output | `release-note/release-note.md` | C02-C07, C12, revised PRD Feature through Permissions | Q04 | Update summary and keep metadata unknown. |
| Add cross-links to existing notification help | DEFER proposed UPDATE | Existing notification help, if it exists | C03, mock PRD UI and workflow | Existing-doc inventory missing | Verify actual pages before editing or linking. |
| Exact Until tomorrow example or mid-pause edit task | DEFER | Future how-to or reference | C08, C10, revised PRD Known gap | Q01, Q03 | Missing behavior blocks accurate steps. |

## Information architecture

- Proposed parent: notification settings help; actual help navigation is UNKNOWN.
- Link the feature guide to the supported 2-hour how-to; do not invent links to existing pages.
- Diagram decision: none. The simple pause/resume flow is clearer in short prose, while the exact Until tomorrow boundary is unresolved.
- Publication blockers for affected claims: Q01-Q04.

## Delivery boundary

The three revised drafts are suitable for rehearsal review. The exact Until tomorrow end, alert backlog, mid-pause edits, availability, and existing-document integration require clarification or inventory before publication.
