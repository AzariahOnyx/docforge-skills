# Tracks — documentation handover

> Review artifact. PRD facts are stated requirements, not verification of implementation.

## Assignment scope

Analyze the supplied working draft for the three audience-specific documents requested on PDF p. 1: a newcomer feature guide, a substantial task how-to, and an existing-user release note. Supply clarification decisions for Part 1. This stage does not draft documentation or modify the reusable skills. Follow `standards/documentation.md`. This is a fresh run of the same source, not a revised-source update.

## Source inventory and coverage

| Source | Authority and coverage | Extraction limits |
| --- | --- | --- |
| `input/Technical Writer - Case Study.pdf` | Sole supplied authoritative artifact. All six pages reviewed afresh using layout-preserving pypdf extraction, including the p. 1 audience table and complete p. 5 permissions table. | Text and table relationships were readable; zero embedded images on all six pages. No unreadable portion identified. No rendered-page visual inspection performed. |

Page coverage: p. 1 assignment and audience table; p. 2 submission/live-round requirements, product hierarchy, task properties/status, navigation and capability permission; p. 3 offline overview, model, capabilities, scope and layout; p. 4 management, column actions, pill and lifecycle; p. 5 lifecycle continuation, permissions table, guest rule and US-1; p. 6 US-2/3/4 and offline conflict rules. No previous outputs or backups used as evidence. Existing product documentation was not supplied; `output/` did not exist at inventory time.

In the registers below, every page/section citation refers to `input/Technical Writer - Case Study.pdf` (S1).

## Claim register

| ID | Classification | Claim | Evidence (S1) | Reasoning / limits |
| --- | --- | --- | --- | --- |
| C01 | FACT | Tasket supports team collaboration inside and outside an organisation; teams have members, admins and guests from another organisation. | p. 2, What Tasket is | Background. |
| C02 | FACT | Projects belong to teams and contain tasks; each task belongs to exactly one project. | p. 2, What Tasket is; Tasks | Hierarchy. |
| C03 | FACT | A task has a title, comment thread, attached Studio documents and Friday chat, one creator, up to ten assignees, and any number of watchers. | p. 2, Tasks | Source also uses “tasket”; see Q09. |
| C04 | FACT | Task statuses are Open, Completed and Discarded; the latter two are called closed. Reopening a closed task returns it to Open. | p. 2, Task status | “Terminal” does not prevent the explicitly supported reopen action. |
| C05 | FACT | Projects have Open, Closed and Settings tabs and a Tracks tab when Tracks is enabled; My Work lists assigned items and Updates shows participant activity. | p. 2, Where things appear | Exact section grouping and Work/My Work naming need Q09. |
| C06 | FACT | Tracks places one task in multiple parallel workstreams, with an independent status in each. Completing or discarding the task is independent of its started tracks. | p. 3, What are tracks | Do not equate track Done with task Completed. |
| C07 | FACT | Tracks are project-scoped. A task can be on any number of tracks, with exactly one status per joined track: In Progress or Done. A track not started for that task is Not started. | p. 3, Scope | Not started is a displayed status for non-membership, not a third joined-track state. |
| C08 | FACT | Tracks board has one column per track, split into In Progress and Done. Only open tasks appear; a task on three tracks appears in three columns. | p. 3, The Tracks board — Layout | Closed tasks are filtered out. |
| C09 | UNKNOWN | The header counter is X out of Y, but the meaning of X and Y is unspecified. | p. 3, Layout; p. 6, US-3 | US-3 says it updates when the last In Progress task is marked Done; no formula. Q02. |
| C10 | FACT | Add track appears at the end of the track panels and between tracks, and supports adding/naming tracks and starting tasks with the track. | p. 4, Managing tracks from the board | Dialog fields and exact sequence absent. Q10. |
| C11 | FACT | A track has Rename, Move track and Delete actions; Move track selects a board position. | p. 4, Managing tracks from the board | Delete authorization unspecified. Q03. |
| C12 | FACT | In Progress column tasks offer Mark Done, Stop and Select; Done tasks offer Mark Pending and Select. | p. 4, Actions on a task in a column | Verified action entry points. |
| C13 | FACT | Select supports multi-selection and starting selected tasks across other tracks in one action. | p. 3, Capabilities; p. 4, Actions on a task in a column | Target-picker mechanics absent. Q10. |
| C14 | FACT | Opening a task from a track shows task details, including assignees, watchers, comments and attached docs or chats. | p. 4, Actions on a task in a column | No invented UI navigation needed. |
| C15 | FACT | Task detail shows a Tracks pill wherever the task is accessed. Opening it lists every project track with Not started, In Progress or Done. It is the only single view of the full track picture. | p. 4, The Tracks pill | Disabled-capability exception in C31. |
| C16 | FACT | The pill offers Start for Not started; Mark Done and Stop for In Progress; Mark Pending for Done. | p. 4, The Tracks pill | Closed-task action availability is not fully specified. Q06. |
| C17 | FACT | The pill counts Done tracks out of all available tracks for the task. | p. 4, The Tracks pill | Do not transfer this denominator to the board counter. |
| C18 | FACT | Closing a task retains track memberships and statuses, hides it from board columns, and preserves pill statuses. Reopening returns it to columns with the same statuses. | p. 4, Lifecycle rules — Close and reopen | Track deletion and cross-project moves have separately stated effects. |
| C19 | FACT | Deleting a track irreversibly removes its statuses and assignments everywhere, including open and closed tasks; there is no undo or recovery window. | p. 4, Lifecycle rules — Delete a track; p. 5, US-1 | Deletion procedure must not invent confirmation or permission. Q03/Q04. |
| C20 | FACT | Renaming changes the column and pill label without changing statuses or assignments. Moving changes only column order. | p. 4, Lifecycle rules — Rename a track; Move a track; p. 5, US-1 | Useful management behavior. |
| C21 | CONTRADICTION | Disabling is a hide, not a delete, and re-enabling restores every track and assignment exactly (p. 3); disabling clears assignments/statuses and requires the admin to recreate tracks and associations (p. 5). | p. 3, Capabilities, first bullet; p. 5, Lifecycle rules — Switch the capability off | Both claims retained; neither selected. Q01. |
| C22 | FACT | Cross-project moves clear all track assignments. No target track is started, even with the same name. User choice is for a future release. | p. 5, Lifecycle rules — Cross-project move | Warn about assignment loss; do not imply name matching or migration choice. |
| C23 | FACT | Any team member can enable Tracks, create, rename and move a track; only admins can disable Tracks. | p. 2, Capabilities; p. 5, Permissions table | Guest wording needs Q05; do not broaden admin-only access. |
| C24 | FACT | Members with task access can Start, Mark Done, Stop and Mark Pending; multi-select start requires access to selected tasks. Board viewing requires project access. | p. 5, Permissions table | No restriction to assignees or creators is stated. |
| C25 | FACT | Guests have the same track permissions as members on projects they can access. | p. 5, paragraph after Permissions table | Retain project qualification; relationship to admin role unresolved Q05. |
| C26 | FACT | Two tracks within the same project cannot have the same name. | p. 5, US-1 | No case, whitespace or name-length rules. Q11. |
| C27 | FACT | Start applies to an open task; a closed task must be reopened before starting on a new track. Starting on an existing track only highlights its existing placement. | p. 6, US-2 | Start initial status not explicitly stated. Q07. |
| C28 | FACT | A multi-select start leaves a task already on the target track where it is. | p. 6, US-2 | Do not promise reset to In Progress. |
| C29 | FACT | Mark Done acts on a task In Progress on one track; Mark Pending moves it back to In Progress. Mark Done on one track does not affect another track. | p. 3, Capabilities; p. 6, US-3 | Supported reversible per-track procedure. |
| C30 | FACT | A Done task cannot be stopped. Marking the last In Progress item Done empties that section and updates the counter. | p. 6, US-3 | No counter arithmetic established; Stop result unspecified. |
| C31 | FACT | Closed tasks still show retained statuses in the Tracks pill; a task in a project with Tracks disabled shows no pill. | p. 6, US-4 | Pill visibility does not resolve C21. |
| C32 | FACT | Tasket works offline but not every action is available. Start, Mark Done and Mark Pending work offline, with local writes queued and reconciled on reconnect. | p. 3, Offline; p. 6, Offline behaviour | No general offline support claim for Stop or Select. Q08. |
| C33 | FACT | Enabling/disabling Tracks and creating, renaming, moving or deleting tracks are online-only. | p. 6, Offline behaviour | Clear management constraint. |
| C34 | FACT | A queued membership write for a track deleted online is silently dropped on sync; it does not recreate the track. If a task closes offline while its track is deleted online, the assignment is dropped on sync and does not reappear on reopen. | p. 6, Offline behaviour | Material exception to retained statuses; no invented notification. |
| C35 | INFERENCE | Starting a previously Not started track likely places the task In Progress, and Stop likely removes its membership. | p. 3, Scope and Capabilities; p. 4, action lists; p. 6, US-2 | Implied by model and labels, but outcomes not explicit. Do not write either outcome as verified. Q07. |
| C36 | UNKNOWN | Delete permission, confirmation controls, validation and error handling are not specified. | p. 4, Managing tracks; Lifecycle rules; p. 5, Permissions table and US-1 | Delete omitted from permission table. Q03/Q04/Q11. |
| C37 | UNKNOWN | Closed-task Mark Done, Mark Pending and Stop permissions, general sync conflict policy, and offline Stop/multi-select are not established. | p. 4, pill and lifecycle; p. 5, Permissions; p. 6, Offline behaviour | Q06/Q08/Q12. |
| C38 | UNKNOWN | No release date, version, rollout, edition, platform availability or prior behavior is supplied. | pp. 2–6, Source material — Tracks | Q13; describe supported capabilities without launch metadata or invented baseline. |
| C39 | FACT | The assignment requests clarifications with assumptions, a first-time-user feature document, a task-focused how-to, an existing-user release note, and a reusable skill for another PRD. | p. 1, Parts 1–3; p. 2, submission/live round | Current delegation is Analyzer only; skill already exists and is outside edit scope. |
| C40 | UNKNOWN | No existing product documentation or second PRD version is supplied. | Source inventory: input/ contains only Technical Writer - Case Study.pdf; pp. 1–6 reviewed | No confirmed UPDATE or revised-source comparison. Q14. |

## Product analysis

- **Audience and purpose:** C01, C06, C39 establish collaboration and parallel workstreams; distinguish each requested reader goal.
- **Model and terminology:** C02–C07 establish team → project → task, project-owned tracks and independent per-track state. C03/C05 need naming clarification Q09.
- **Permissions:** C23–C25 establish task/project access qualifications and admin-only disabling. C36 leaves deletion unknown; guest admin status is not established.
- **States and lifecycle:** C04, C18, C22, C27–C31 separate task Open/closed from track In Progress/Done. Mark Done does not complete the overall task. Start/Stop outcomes remain inference C35. C21 is unresolved.
- **UI and workflows:** C08–C17 establish board and pill entry points. Use the board’s In Progress and Done sections for the C29 state-change task. Creating tracks and bulk starts lack detailed controls (Q10).
- **Management and destructive behavior:** C19–C20/C26 establish rename, order, unique names and irreversible deletion. C22 makes cross-project moves destructive to associations. Do not supply unverified safeguards.
- **Offline and persistence:** C32–C34 define explicit offline actions, online-only management, queued-write loss after deletion and no resurrection. Other offline/conflict behavior is unknown, not inapplicable.
- **Limits and exceptions:** C07 allows any number of memberships; C26 forbids duplicate names in a project; C27/C28 prevent duplicate placement/reset; C30 prohibits stopping Done. No other limits established.

## Clarifications and contradictions

See `clarifications-and-assumptions.md` for Q01–Q14, full evidence, questions, safe editorial decisions and impacts. C21/Q01 preserves both conflicting disable claims above. All questions remain unanswered. No product assumption is required to proceed: omissions and scope decisions are editorial choices, not claims about behavior.

## Documentation plan

| Deliverable | Reader goal | Evidence | Blocked or deferred |
| --- | --- | --- | --- |
| Feature guide | Understand parallel tracks, independent task/track states, visibility, access and consequences | C02, C04, C06–C08, C12–C20, C22–C34 | Q01 blocks publication; Q02–Q12 constrain detail |
| How-to | Mark work Done on one track and return it to In Progress when needed | C08, C12, C24, C29, C30, C32 | Use open task already In Progress; avoid Q06/Q07 |
| Release note | Notice independent workstream progress, multi-track starts, and task-level visibility | C06, C13, C15–C17, C29 | Omit Q01 disputed effects; Q13 metadata pending |

See `CONTENT-PLAN.md` for destinations, candidate comparison and CREATE/DEFER decisions.

## Drafter guidance

Use exact actionable labels: **Tracks**, **Mark Done**, **Mark Pending**, **Start**, **Stop**, **Select**, **Rename**, **Move track**, **Delete**, **Add track**. Use task status Open/Completed/Discarded separately from track status Not started/In Progress/Done. Never describe Done as closing the task or marking all tracks done.

Use an open task already In Progress on a track, with task and project access, for the how-to. Select that task’s **Mark Done** action in its In Progress section; the task is Done on that track and other tracks are unaffected. For correction or resumed work, use **Mark Pending** in Done to return it to In Progress. Make the optional reversal support the same task goal, not a second tutorial. No invented menu expansion, selectors, confirmation or save controls.

Keep C21’s competing outcomes, claim IDs and editorial notes out of reader-facing documents. The overview may be assignment-ready with the safe omissions recorded, but is not publication-ready until Q01 is resolved because capability disabling has a material data-loss dispute. Retain verified deletion, cross-project move and offline deletion-loss consequences. Do not turn missing facts into negative behavior claims. Independent proofreading must compare original source and drafts and map every C01–C40 exactly once in `analysis/COVERAGE.md` after drafting; this stage leaves that ledger to the downstream workflow.
