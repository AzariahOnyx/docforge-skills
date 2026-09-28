# Tracks — documentation handover

## Assignment scope

Create a feature guide for first-time users, a task-focused how-to, a release note for existing users, and a clarification register. Assignment evidence: `input/Technical Writer - Case Study.pdf`, pp. 1–2. Part 3 requests a reusable skill: this invocation reuses the repository’s existing generic demo-studio → generate-docs → Analyzer/Drafter/independent Proofreader skills; no system-file modification is authorized or needed. The assignment permits a zip folder or one document; this run produces the requested documentation files and reuses the existing skills.

## Source inventory

| Source ID | Path and location | Authority / purpose | Extraction limits |
| --- | --- | --- | --- |
| S1 | `input/Technical Writer - Case Study.pdf`, pp. 1–6 | Only supplied input: assignment pp. 1–2 and working-draft Tracks PRD pp. 2–6 | All six pages extracted with PyMuPDF and all six page renders inspected; permissions table and assignment audience table checked visually. No unreadable sections. |

`input/` contains only S1. No existing product documentation supplied; its existence is UNKNOWN. Prior outputs and backups were not read as evidence. FACT means explicitly stated in the working draft, not verified in implementation.

## Claim register

| ID | Classification | Claim or competing statement | Evidence | Reasoning / limits |
| --- | --- | --- | --- | --- |
| C01 | **FACT** | Tasket teams contain members, admins and guests; teams contain projects; each task belongs to exactly one project. | `input/Technical Writer - Case Study.pdf`, p. 2, What Tasket is / Tasks | Foundation; guests are users from another organisation. |
| C02 | **FACT** | Tasks have a title, comment thread, attached Studio documents and Friday chat; one creator, up to ten assignees and any number of watchers. | `input/Technical Writer - Case Study.pdf`, p. 2, Tasks | Reference context, not central to Tracks. |
| C03 | **FACT** | Task status is Open, Completed or Discarded; the latter two are called closed; reopening returns a task to Open. | `input/Technical Writer - Case Study.pdf`, p. 2, Task status | “Terminal” is used despite explicit reopening; use closed, not irreversible. |
| C04 | **FACT** | Tracks lets one task participate in several parallel workstreams with a separate status in each; overall completion/discard is independent. | `input/Technical Writer - Case Study.pdf`, p. 3, What are tracks / Scope | Essential mental model. |
| C05 | **FACT** | Tracks are project-scoped; a task may be on any number, with In Progress or Done per started track; otherwise its status there is Not started. | `input/Technical Writer - Case Study.pdf`, p. 3, Scope | No numeric maximum is specified. |
| C06 | **FACT** | The Tracks tab appears when enabled; its columns each have In Progress and Done sections and show only open tasks. A task appears in every column it is started on. | `input/Technical Writer - Case Study.pdf`, p. 2, Where things appear; p. 3, Layout | Avoid claiming that a missing board task lost its assignments. |
| C07 | **FACT** | Each column has an X out of Y counter; marking the last In Progress item Done empties that section and updates the counter. | `input/Technical Writer - Case Study.pdf`, p. 3, Layout; p. 6, US-3 | The meanings of X and Y are UNKNOWN (Q02). |
| C08 | **FACT** | Add track is available after the track panels and between two tracks; tracks can be named, renamed, moved and deleted; duplicate names within a project are disallowed. | `input/Technical Writer - Case Study.pdf`, p. 4, Managing tracks from the board; p. 5, US-1 | Exact naming validation and creation dialog are unspecified. |
| C09 | **FACT** | An In Progress board task offers Mark Done, Stop and Select; a Done task offers Mark Pending and Select. Select enables multi-select starting across other tracks. | `input/Technical Writer - Case Study.pdf`, p. 4, Actions on a task in a column | Target picker/confirmation steps unspecified. |
| C10 | **FACT** | Task details opened from a track expose assignees, watchers, comments and attached docs/chats. The Tracks pill is available in task details regardless of entry point. | `input/Technical Writer - Case Study.pdf`, p. 4, Actions on a task / The Tracks pill | Pill absent when capability is off (C19). |
| C11 | **FACT** | Opening the Tracks pill lists every project track and the task’s Not started, In Progress or Done status; it counts Done tracks out of all available tracks for the task. | `input/Technical Writer - Case Study.pdf`, p. 4, The Tracks pill | Full per-task picture in one place; do not reinterpret denominator as started tracks. |
| C12 | **FACT** | The pill offers Start for Not started, Mark Done and Stop for In Progress, and Mark Pending for Done. Mark Pending returns Done to In Progress. | `input/Technical Writer - Case Study.pdf`, p. 4, The Tracks pill; p. 3, Capabilities | Start workflow and expected placement supported by p. 6 US-2; Stop’s exact post-state is not explicit (Q05). |
| C13 | **FACT** | Closing retains memberships and per-track statuses, hides task from columns and retains statuses in the pill; reopening restores the task to columns with those statuses. | `input/Technical Writer - Case Study.pdf`, p. 4, Lifecycle rules, Close and reopen | Subject to separately documented deletion/move consequences. |
| C14 | **FACT** | Deleting a track permanently removes its statuses and assignments everywhere, including closed tasks; there is no undo or recovery window. | `input/Technical Writer - Case Study.pdf`, p. 4, Lifecycle rules, Delete a track; p. 5, US-1 | Irreversible and data-loss risk; permission omitted from matrix (Q03). |
| C15 | **FACT** | Rename changes the column and pill label without changing statuses/assignments. Move track changes only column position and does not affect tasks. | `input/Technical Writer - Case Study.pdf`, p. 4, Lifecycle rules; p. 5, US-1 | State-changing organisation controls, not task transfer. |
| C16 | **CONTRADICTION** | Page 3 says disabling hides without deleting and reenabling restores every track and assignment exactly. Page 5 says disabling clears assignments/statuses and reenabling requires admin recreation of tracks and associations. | `input/Technical Writer - Case Study.pdf`, p. 3, Capabilities, Switching off; p. 5, Lifecycle rules, Switch the capability off | Q01: preserve both sides; do not promise retention or deletion. |
| C17 | **FACT** | Moving a task to another project clears all track assignments; none are started in the target, even if track names match. Choosing what to retain is future scope. | `input/Technical Writer - Case Study.pdf`, p. 5, Lifecycle rules, Cross-project move | Data-loss consequence must remain visible; no move procedure provided. |
| C18 | **FACT** | Any team member can enable/create/rename/move tracks; only Admin can disable. Task actions require member access to the task, bulk start requires access to selected tasks, and board viewing requires project access. Guests have member track permissions on accessible projects. | `input/Technical Writer - Case Study.pdf`, p. 5, Permissions table and guest statement; p. 2, Capabilities | Do not assume assignee-only access or specify deletion permission. |
| C19 | **FACT** | Open tasks can be started on one or more tracks; closed tasks must be reopened first. An already-started task is highlighted without another placement; bulk start leaves existing target placements unchanged. The pill is absent while Tracks is off. | `input/Technical Writer - Case Study.pdf`, p. 6, US-2 / US-4 | Start is state-changing; duplication behaviour is secondary. |
| C20 | **FACT** | Mark Done changes only that track; Mark Pending returns it to In Progress; Done tasks cannot be stopped. | `input/Technical Writer - Case Study.pdf`, p. 6, US-3; p. 3, Capabilities | Distinguish track Done from task Completed. |
| C21 | **FACT** | Start, Mark Done and Mark Pending work offline; writes queue locally and reconcile on reconnect. Enable/disable/create/rename/move/delete tracks are online-only. | `input/Technical Writer - Case Study.pdf`, p. 6, Offline behaviour | Stop and bulk-start offline availability unspecified (Q06). |
| C22 | **FACT** | If a queued membership write arrives after online track deletion, it is silently dropped and does not recreate the track; if a task closed offline while its track was deleted online, its assignment is dropped on sync and does not reappear on reopening. | `input/Technical Writer - Case Study.pdf`, p. 6, Offline behaviour | Material silent data-loss exception, not a generic conflict policy. |
| C23 | **INFERENCE** | Starting via the task pill supplies a complete supported task: an accessible open task and enabled project tracks, Start, then In Progress placement; continue independently to Done and optionally back to In Progress. | `input/Technical Writer - Case Study.pdf`, p. 3, Scope; p. 4, pill actions; p. 6, US-2 / US-3 | Start action is explicitly tied to open-task column placement; its initial In Progress state is inferred from the model and actions, not stated explicitly. Do not invent a confirmation dialog. |
| C24 | **UNKNOWN** | Release date, rollout, plans, platforms and a historical baseline are not supplied. | `input/Technical Writer - Case Study.pdf`, pp. 2–6, full PRD | Describe introduced capability without asserting public availability or prior limitations (Q10). |

## Product model

- Purpose, hierarchy and scope: C01, C04–C05. Project tracks classify the same task into parallel workstreams; they are not copies or a required sequential pipeline.
- States: C03, C12–C13, C19–C20. Keep task-level Open/closed separate from per-track In Progress/Done. Not started denotes lack of started membership.
- Permissions: C18 and Q03. Team membership and task/project access matter; guests inherit the stated accessible-project member permissions. Deletion authorization is not established.
- UI: C06–C12. Board gives each track’s open-task workload; pill gives one task’s entire track picture. “Work” and “My Work” naming needs confirmation (Q09).
- Creation/editing/destruction: C08, C14–C17. Track deletion is irreversible; cross-project task moves clear assignments. Neither warrants an unsupported how-to.
- Lifecycle and persistence: C13–C17. Close/reopen is supported; capability-off retention is contradictory (Q01).
- Offline: C21–C22. Queued writes do not protect assignments from track deletion; silent loss must survive editorial compression.
- Limits: C05, C08, C19–C20. No duplicate track names, no starting closed tasks, no stopping Done tasks. Numeric track limits are not established.

## Clarifications and contradictions

See [clarifications and assumptions](clarifications-and-assumptions.md) for Q01, Q02, Q03, Q04, Q05, Q06, Q07, Q08, Q09, Q10, Q11 and Q12, each with evidence, consequence and the safe drafting decision. C16/Q01 is an explicit material contradiction: p. 3 promises restoration after disable; p. 5 requires rebuilding after data clearing. Neither is authoritative over the other. Publication remains blocked for capability-off guidance. Q03 blocks an authoritative deletion procedure. Other workflow omissions limit detailed administration and recovery instructions.

## Documentation plan

| Deliverable | Reader goal | Supported topics / claim IDs | Blocked topics |
| --- | --- | --- | --- |
| Feature guide | Understand parallel progress and where to see it | C01, C03–C06, C10–C14, C17–C22 | Disable retention, deletion permission, undefined board counter |
| How-to guide | Mark an open task Done on one track without closing it, and resume if needed | C04, C11–C12, C18, C20–C22 | Setup navigation, inferred Start transition, bulk picker, Stop outcome |
| Release note | Scan the change and practical effect | C04–C06, C11–C12, C20–C22 | Release metadata, historical comparisons |

See [content plan](CONTENT-PLAN.md) for CREATE / UPDATE / DEFER decisions and editorial ranking.

## Drafter guidance

Use “task” consistently; quote action labels Start, Mark Done and Mark Pending. Explain the pill in familiar language as the Tracks control in task details. Avoid “terminal” suggesting that reopening is impossible. Avoid undocumented click paths, alerts, confirmation dialogs, Stop reset behaviour, bulk confirmations, counter formulas, permissions and release availability. No unverified product assumptions are needed; assumptions in the register are explicitly editorial scope decisions. Retain the destructive-action and offline-loss consequences when compressing content. Keep disputed disable behaviour in internal review artifacts and visibly identify publication blockers there, without inserting competing instructions into customer prose.

Write the editorial blueprint before drafting. Map C01–C24 and Q01–Q12 in coverage after drafting, including intentional omission of secondary material. Analysis is complete for all supplied source pages; implementation verification and unresolved source questions remain outside that conclusion.
