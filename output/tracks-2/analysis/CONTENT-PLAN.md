# Tracks — content scope and change plan

## Source and existing-content inventory

- Only authoritative input: `input/Technical Writer - Case Study.pdf`, six pages; assignment pp. 1–2 and working-draft PRD pp. 2–6, fully reviewed including rendered tables.
- Existing product documentation: none supplied in `input/`; existence UNKNOWN. Existing generated output is not evidence and was not inspected.
- Audiences: first-time feature user, someone completing a specific task, existing user scanning a change (p. 1).
- Reuse existing generic skills for assignment Part 3; do not modify them or create an extra reader-facing article.

## Scope decisions

| Topic / reader goal | Relevance | Action | Destination or update candidate | Evidence | Open questions | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| Understand independent workstream progress | ESSENTIAL | CREATE | `../feature/feature-guide.md` | C01, C03–C06, C10–C14, C17–C22 | Q01–Q03, Q06, Q08–Q12 | Newcomer mental model, views, access and material consequences |
| Mark one workstream Done without closing the task | ESSENTIAL | CREATE | `../how-to/how-to.md` | C04, C11–C12, C18, C20–C22 | Q06, Q08 | Complete explicit start/action/result plus supported recovery; distinct from overview |
| Scan parallel progress, task-level visibility and offline actions | ESSENTIAL | CREATE | `../release-note/release-note.md` | C04–C06, C11–C12, C20–C22 | Q10 | At most three practical changes, concise impact |
| Existing project capability/settings help | REFERENCE CANDIDATE | UPDATE (proposed only) | No verified existing target | C08, C16, C18 | Q01, Q03, Q04 | Requires existing-doc inventory and resolution before an update is possible |
| Capability disable/re-enable, deletion, bulk start, Stop and move procedures | REFERENCE CANDIDATE | DEFER | No article created | C09, C14, C16–C17 | Q01, Q03–Q08, Q11 | Missing controls or unsafe retention ambiguity |
| Board-counter formula, fine permissions, naming rules and conflict recovery | REFERENCE CANDIDATE | DEFER | Analysis only | C07–C08, C18, C21–C22 | Q02, Q04, Q06, Q12 | Unestablished details cannot be filled in |

## Information architecture

Proposed placement is a Tracks feature overview linked to its one specific-task how-to; no existing parent article is asserted. Cross-link only the new feature guide and how-to where useful. No diagram is necessary: a small comparison of task status and track status plus clear prose explains independence. An unsupported Stop transition or disable lifecycle must not appear in a diagram.

## Editorial inputs

### Essential newcomer concepts

1. **ESSENTIAL:** One task can participate in parallel project workstreams; it is not a required sequence (C01, C04–C05).
2. **ESSENTIAL:** Track In Progress/Done differs from overall task Open/closed; finishing one track affects no other (C03–C04, C20).
3. **ESSENTIAL:** Board columns show open-task work by track; the task pill shows every project track and the task’s status (C06, C10–C11).
4. **ESSENTIAL:** Access determines actions, guests have the stated member permissions, and existing tracks enable ordinary task work (C18–C19).
5. **ESSENTIAL:** Close/reopen retains statuses; track deletion and project moves remove associations with serious consequences (C13–C14, C17).
6. **ESSENTIAL:** Only specified actions work offline, and deleted tracks can silently invalidate queued writes (C21–C22).

**USEFUL:** Rename/reorder do not alter task status; unique track names (C08, C15). Keep brief or in coverage context.

**EDGE CASE:** Already-started task highlighting and last-item-empty-section behaviour (C07, C19); omit unless needed for troubleshooting.

**REFERENCE CANDIDATE:** Task participant limits, attached document/chat details and full administration control inventory (C02, C08–C09); not needed by these reader goals.

### How-to candidates ranked

| Rank / candidate | User value and consequence | Evidence completeness / substance | Audience and assignment fit | Decision |
| --- | --- | --- | --- | --- |
| 1. Mark an open task Done on one track and resume it if needed | Complete one discipline’s work without changing other tracks or closing the task; state-changing | Explicit start: open task In Progress on a track; control: pill Mark Done; result: Done on that track only; recovery: Mark Pending returns In Progress (pp. 3–4, 6) | Specific task in hand; short but consequential, as assignment permits | SELECT. Include access prerequisite, enabled Tracks, visible Done result, task/track distinction, optional recovery and relevant offline caveat. |
| 2. Start an open task across several tracks via pill | Establish parallel work, strong value; state-changing | Starting condition/action/column placement supported (pp. 3–4, 6); precise initial In Progress transition is inferred C23 | Good broader task, but requires declaring model inference | Keep Start capability in feature guide; do not use inference to overclaim procedural verification. |
| 3. Bulk start from Select | High impact across several tasks | Target choice/commit/error handling absent Q07 | Good potential task but incomplete instructions | DEFER. |
| 4. Create/configure/delete tracks | Project-wide effect; deletion irreversible | Setup path, confirmation, deletion permission missing Q03–Q04; disable contradictory Q01 | Substantial but unsafe as an executable guide | DEFER. |
| 5. View full track picture | Informational, useful but little consequence | Complete pill flow C11 | Weaker specific-task value than supported state change | Do not select as sole how-to. |

The selected short procedure has a real state change, observable completion and supported reversal; it is not padded into a longer setup workflow. The assignment does not demand a long procedure.

### Material consequences

Preserve independent task/track completion (C04/C20), closed-task board filtering and retained statuses (C13), irreversible track deletion across open and closed tasks (C14), project-move clearing even for same-name tracks (C17), access and guest rules (C18), closed-task Start prohibition and Done Stop restriction where relevant (C19–C20), and offline queued-write deletion loss (C21–C22). Disable contradiction C16/Q01 remains prominently recorded internally and blocks publication of administration guidance; no competing promises go in customer prose.

### Release-note priorities

1. Parallel workstream progress on one task; each discipline can update its own progress independently (C04–C06, C20). Main user impact, not a fabricated comparison to an earlier version.
2. Full task-level track picture in task details (C11–C12). Avoid repeating the entire overview or procedural steps.
3. Start, Mark Done and Mark Pending offline with reconnect sync (C21); if included, retain the deleted-track write-loss qualification (C22). May omit this third candidate to keep note concise.

### Deliberate exclusions

- Feature: no click-by-click setup, exhaustive permission table, counter formula or conflicting disable outcome. Keep essential risks, not PRD ordering.
- How-to: no creating tracks, capability settings, Stop workaround, cross-project transfer or unsupported batch UI. Explain only what enables successful completion of the selected action.
- Release note: no release date/tier/platform, prior-state claims, setup steps, complete lifecycle reference or repeated feature-guide sections. If mentioning a capability with a material caveat, retain that caveat.

## Delivery boundary

All three bounded drafts can proceed from the source. Material questions remain for product owners, so assignment review readiness is distinct from publication readiness. Packaging may include the existing reusable skills unchanged to satisfy Part 3; these files are workflow evidence, never product evidence. There is no revised source version, so a change-impact comparison is inapplicable.
