# Tracks — content scope and change plan

> Review artifact. The source is a working PRD; the proposed placement is an editorial plan, not an assertion about Tasket's existing help center.

## Source and existing-content inventory

- Source: `input/Technical Writer - Case Study.pdf`, pp. 1-6; Tracks requirements on pp. 2-6.
- Existing Tasket documentation, navigation, style guide, and product build: not supplied. Existing article names and paths are UNKNOWN.
- Assignment: one feature document for a first-time user, one single-goal how-to, one release note for an existing user (p. 1).

## Scope decisions

| Topic / reader goal | Action | Destination or candidate | Evidence | Open questions | Reason |
| --- | --- | --- | --- | --- | --- |
| Understand Tracks, separate task and track states, board, pill, and lifecycle | CREATE | `feature/feature-guide.md` | C03-C09, C12, C14-C19, C21-C24, C27-C32; PDF pp. 2-6 | Q01-Q04, Q08-Q13 | Required first-time-user article; omit disputed disable outcome and unsupported counter meaning. |
| Mark one open task Done on a track | CREATE | `how-to/how-to.md` | C04, C08, C12, C23, C28, C31; PDF pp. 2-4, 6 | Q06, Q11 | The PRD supports a starting state, named action, and result. |
| Scan the new capability | CREATE | `release-note/release-note.md` | C05-C06, C08, C14-C17, C28, C31; PDF pp. 3-6 | Q01, Q14 | Required concise announcement; omit invented release metadata. |
| Integrate Tracks into existing task/project help and navigation | DEFER proposed UPDATE | Existing help pages, if any; confirm inventory before selecting targets | C04, C14, C21; PDF pp. 2, 4-5 | Q06, Q09, Q12 | No existing documentation was supplied. Candidate cross-links and update scope need an audit. |
| Document disabling and re-enabling Tracks | DEFER | Future capability-management task/reference topic | C20A and C20B; PDF pp. 3, 5 | Q01, Q17 | Contradictory data-retention outcomes make instructions unsafe. |
| Document deletion, bulk start, and exact counters | DEFER | Future task/reference topics | C11, C13, C18, C35-C38; PDF pp. 3-6 | Q02-Q03, Q05, Q07 | Permissions, click paths, or formulas are missing. |

## Information architecture

- Proposed parent: project work management help. The actual help-center tree is UNKNOWN.
- Link the feature guide to the supported Mark Done how-to. Link to any existing pages only after verifying them.
- Diagram: a small per-track state flow in the feature guide clarifies C06/C15/C28. Its Stop edge is omitted because Q04 is open. The separate task close/reopen lifecycle stays in prose to avoid implying a track-state transition.
- Publication blockers: Q01 prevents a complete disable/re-enable account. Q02-Q17 affect the specific topics noted above.

## Delivery boundary

The three required drafts can proceed as review artifacts. A full published documentation set needs product confirmation on Q01, triage of the remaining material questions, and an inventory of existing docs. This PRD does not verify the running product.
