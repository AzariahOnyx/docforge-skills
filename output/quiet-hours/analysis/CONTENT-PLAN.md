# Quiet Hours — content scope and change plan

## Source and existing-content inventory

- Sole evidence: `demo/mock-prd.md`, all sections.
- No existing Pulseboard documentation was supplied; existence, names, and navigation of help pages are UNKNOWN.
- Three requested reader goals: understand the feature, complete one task, scan the change.

## Scope decisions

| Topic / reader goal | Action | Destination or candidate | Evidence | Open questions | Reason |
| --- | --- | --- | --- | --- | --- |
| Understand which alerts are paused and how they resume | CREATE | `feature/feature-guide.md` | C01-C07, mock PRD Product context through Permissions | Q01-Q03 | Gives a first-time user the model without inventing delivery semantics. |
| Pause in-app alerts for 1 hour | CREATE | `how-to/how-to.md` | C03-C07, mock PRD UI and workflow, Permissions | Q03 | One fully specified path and expected result. |
| Announce Quiet Hours | CREATE | `release-note/release-note.md` | C02-C07, mock PRD Feature through Permissions | Q04 | Short supported change summary. |
| Add cross-links to existing notification help | DEFER proposed UPDATE | Existing notification help, if it exists | C03, mock PRD UI and workflow | Existing-doc inventory missing | Verify actual pages before editing or linking. |
| Exact Until tomorrow example or offline resume task | DEFER | Future how-to or reference | C08, C10, mock PRD Known gap and UI and workflow | Q01, Q03 | Missing behavior blocks accurate steps. |

## Information architecture

- Proposed parent: notification settings help; actual help navigation is UNKNOWN.
- Link the feature guide to the supported 1 hour how-to; do not invent links to existing pages.
- Diagram decision: none. The simple pause/resume flow is clearer in short prose, while the exact Until tomorrow boundary is unresolved.
- Publication blockers for affected claims: Q01-Q04.

## Delivery boundary

The three drafts are suitable for editorial review. The exact Until tomorrow end, alert backlog, offline resume, availability, and existing-document integration require clarification or inventory before publication.
