# Tasket Tracks — content scope and change plan

## Source and existing-content inventory

Only product evidence: `input/Technical Writer - Case Study.pdf`, six pages; PRD pp. 2–6. Inspected output directory file inventory: quiet-hours, quiet-hours-v2 and quiet-hours-v2-live outputs are present and unrelated. Git index lists output/tracks reader-facing paths, but those files are absent from the current output directory inventory; their content was not accessed. No `.demo-backups/` or prior-output content read or reused as evidence. An update target's content therefore has not been inspected; no confirmed UPDATE is planned. Fresh slug tracks-2 avoids the reserved tracked Tracks output. Existing files remain unchanged.

## Scope decisions

| Topic / reader goal | Action | Destination or update candidate | Evidence | Open questions | Reason |
| --- | --- | --- | --- | --- | --- |
| Understand parallel task work across tracks | CREATE | `../feature/feature-guide.md` | C1–C24 | Q1–Q9 | Required first-time conceptual guide; preserve contradiction and avoid unsupported specifics. |
| View all statuses for one task | CREATE | `../how-to/how-to.md` | C11, C13, C18, C22 | None for selected task | Supported starting point: task detail, action: open Tracks pill, result: every project track/status. |
| Scan capability and practical benefit | CREATE | `../release-note/release-note.md` | C5–C7, C11, C31 | Q8 | Required brief draft release note, no launch assertion. |
| Explain definite disable/re-enable outcome | DEFER | Future feature-guide correction after clarification | C16 | Q1 | Conflicting preservation versus destruction requirements. |
| Write management/deletion/offline recovery procedures | DEFER | No extra article now | C26–C28 | Q3–Q5 | Missing permission/UI/recovery details; not needed for requested three pieces. |
| Update earlier Tracks documentation | DEFER | Tracked `output/tracks/` is an uninspected candidate only | Git index inventory, not product evidence | None | Fresh run required; preserve existing files and do not reuse prior outputs. |

## Information architecture

Three reader-facing documents only; relative links between new feature and how-to. Analysis/QA are review artifacts. Optional small relationship diagram can illustrate project-scoped tracks and one task participating in multiple tracks (C5–C6), but a table is sufficient and avoids conflating task and track states. No disputed disable edge or inferred Start/Stop transition in any diagram.

## Delivery boundary

All requested draft types can proceed. Q1 prevents publication-ready lifecycle advice; other questions restrict affected claims. Release note is a draft of a working-PRD capability, not verified availability. This is a fresh output from one source version, not a source revision comparison; no CHANGE-IMPACT.md required. Source assignment mentions reusable skill and packaging; current reusable workflow already exists, and this run does not change skills or package/send a submission.
