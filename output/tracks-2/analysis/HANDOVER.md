# Tasket Tracks — documentation handover

## Assignment scope

Fresh documentation demo at output/tracks-2. Produce the three requested article types plus clarification register, content plan, coverage and QA. Do not modify existing outputs, sources or skills. Existing reusable skills satisfy workflow execution; packaging/submission and skill modification are source case-study context, not authorization to send anything or alter skills in this run. No commits/pushes.

## Source inventory

| Source ID | Path and location | Authority / purpose | Extraction limits |
| --- | --- | --- | --- |
| S1 | `input/Technical Writer - Case Study.pdf`, pages 1–6 | Sole product evidence; working-draft Tracks PRD begins p. 2, case-study framing pp. 1–2 | All six pages independently extracted/read in full, including deliverable and permission tables; no embedded images and no unreadable content identified. |

S1 citations resolve to this full PDF path. Prior output and `.demo-backups/` were not read or used as product evidence. Coverage: p. 1 assignment; p. 2 submission plus Tasket model/status/capability; p. 3 offline overview, Tracks scope and layout; p. 4 board actions, pill, lifecycle; p. 5 lifecycle, permission table and US-1; p. 6 US-2–4 and complete offline behavior. FACT means PRD claim, not implementation verification.

## Claim register

| ID | Classification | Claim or competing statement | Evidence |
| --- | --- | --- | --- |
| C1 | FACT | Tasket is work management: teams include members, admins and guests from other organisations; projects belong within teams and contain tasks. | S1, p. 2, What Tasket is |
| C2 | FACT | Each task belongs to exactly one project; has title, comment thread, attached Studio documents and Friday chat; one creator, up to ten assignees and any number of watchers. | S1, p. 2, Tasks; source also uses tasket |
| C3 | FACT | Task states Open, Completed and Discarded; last two are called closed/terminal, but a closed task can be reopened to Open. | S1, p. 2, Task status |
| C4 | FACT | Project has Open/Closed tabs grouped by sections and Settings; Tracks tab appears with capability enabled. My Work lists assignments; Updates lists participant activity. | S1, p. 2, Where things appear |
| C5 | FACT | Tracks lets one task participate in several workstreams simultaneously, with an independent status in each; task completion/discard is independent of track participation. | S1, p. 3, What are tracks |
| C6 | FACT | Tracks are project-scoped; any number of tracks per task. Each started track has exactly one status: In Progress or Done; absent participation is Not started. | S1, p. 3, Scope |
| C7 | FACT | Board has one column per track, each split into In Progress and Done. Columns show open tasks only; same task appears in multiple columns if started on multiple tracks. Headers show X out of Y. | S1, p. 3, The Tracks board / Layout |
| C8 | FACT | Add track appears at end of panels and between tracks; permits adding/naming track and starting tasks with it. Track actions are Rename, Move track and Delete; Move track selects board position. | S1, p. 4, Managing tracks from the board |
| C9 | FACT | In Progress column tasks have Mark Done, Stop, Select; Done tasks have Mark Pending, Select. Select is multi-select for starting tasks across other tracks. | S1, p. 4, Actions on a task in a column |
| C10 | FACT | Opening task from a track shows details including assignees, watchers, comments and attached documents/chats. | S1, p. 4, Actions on a task in a column |
| C11 | FACT | Task detail shows Tracks pill wherever task is accessed; opening it lists every project track with Not started, In Progress or Done. Pill shows Done out of all available tracks and is the only full-track overview in one view. | S1, p. 4, The Tracks pill |
| C12 | FACT | Pill has Start for Not started, Mark Done and Stop for In Progress, and Mark Pending for Done. Mark Pending returns Done to In Progress. | S1, p. 4, The Tracks pill; p. 3, Capabilities |
| C13 | FACT | Closing preserves memberships and per-track statuses; task vanishes from all board columns but pill retains statuses. Reopening restores its columns and statuses exactly. | S1, p. 4, Lifecycle rules / Close and reopen; p. 6, US-4 |
| C14 | FACT | Deleting a track irreversibly removes statuses/assignments everywhere, including closed tasks; no undo/recovery window. | S1, p. 4, Lifecycle rules / Delete a track; p. 5, US-1 |
| C15 | FACT | Rename changes column/pill label only, preserving assignments/statuses. Move changes column position only, affecting no tasks. Names must be unique within project. | S1, p. 4, Lifecycle rules / Rename and Move; p. 5, US-1 |
| C16 | CONTRADICTION | Disable is hide-not-delete and re-enable restores every track/assignment exactly, versus disable clears assignments/statuses and admin must recreate tracks/associations. Neither outcome can be selected (Q1). | S1, p. 3, Capabilities: hide/restoration; p. 5, Lifecycle rules / Switch the capability off: clear/rebuild |
| C17 | FACT | Cross-project task move clears all track assignments even if target track shares a name; arrives with no track started. Choosing preservation is future release. | S1, p. 5, Lifecycle rules / Cross-project move |
| C18 | FACT | Members enable Tracks; only admin disables. Any team member creates, renames and moves tracks; members with project access view board; members with task access Start, Mark Done, Stop, Mark Pending; selection/start requires access to selected tasks. | S1, p. 2, Capabilities; p. 5, Permissions action table |
| C19 | FACT | Guests have same track permissions as members on projects they can access. | S1, p. 5, Permissions opening sentence |
| C20 | FACT | Start operates on open tasks; closed tasks must reopen first. Starting on a track already joined highlights existing placement; multiselect leaves already-placed tasks where they are. | S1, p. 6, US-2 |
| C21 | FACT | Done tasks cannot be stopped. Marking last In Progress item Done empties section and updates counter. Mark Done on one track affects no other track. | S1, p. 6, US-3 |
| C22 | FACT | When Tracks switched off, task does not render Tracks pill. | S1, p. 6, US-4 |
| C23 | FACT | Start, Mark Done and Mark Pending work offline, queue locally and reconcile on reconnect. Capability toggles and track create/rename/move/delete are online-only. | S1, p. 6, Offline behaviour; p. 3, Offline |
| C24 | FACT | Queued membership write for track deleted online is silently dropped, never recreating track. If task closed offline while track deleted online, assignment drops on sync and pill does not restore deleted track on reopening. | S1, p. 6, Offline behaviour |
| C25 | UNKNOWN | Exact board counter numerator/denominator undefined; pill counter is explicitly Done out of all available tracks and cannot define board count (Q2). | S1, p. 3, Layout; p. 4, The Tracks pill; p. 6, US-3 |
| C26 | UNKNOWN | Deletion permission unclear: US-1 generically describes team-member management including deletion, but permission table omits Delete (Q3). | S1, p. 5, US-1 and Permissions table |
| C27 | UNKNOWN | Stop offline and multiselect-start offline availability unspecified; no general concurrent-edit resolution, queue visibility or failure recovery defined (Q4). | S1, p. 6, Offline behaviour |
| C28 | UNKNOWN | Exact capability switch UI, track naming constraints beyond uniqueness, deletion confirmation, and multiselect target/confirmation controls unspecified (Q5). | S1, p. 3, Capabilities; p. 4, Managing tracks and Actions on a task; p. 5, US-1 |
| C29 | UNKNOWN | Work tab versus My Work naming differs; task versus tasket wording also differs (Q6). | S1, p. 2, Tasks and Where things appear; p. 4, The Tracks pill |
| C30 | UNKNOWN | Editing retained track state on a closed task is not defined beyond prohibition on starting new tracks (Q7). | S1, p. 4, The Tracks pill and Lifecycle; p. 6, US-2 and US-4 |
| C31 | UNKNOWN | Release date, rollout, platform support and plan/pricing entitlement are absent (Q8). | S1, pp. 2–6, complete PRD extract |
| C32 | INFERENCE | For an open accessible task in enabled project, Start from pill yields In Progress on selected track and board placement. | S1, p. 3, Scope; p. 4, The Tracks pill; p. 6, US-2–3: Start, then Mark Done for In Progress; transition not stated in one explicit sentence (Q9) |
| C33 | INFERENCE | Stop likely removes current track participation and yields Not started; source provides Stop for In Progress and defines Not started as not started, but never explicitly states post-Stop state (Q9). | S1, p. 3, Capabilities and Scope; p. 4, The Tracks pill |
| C34 | FACT | Assignment asks clarification register with any assumptions, first-time feature guide, task-focused how-to, release note and reusable skill; submission format zip or document and live-round reuse are exercise context. | S1, pp. 1–2, Parts 1–3 and Submission and what happens next |

## Product model

- Hierarchy and users: team → project → task; tracks project-scoped, tasks may participate in many, one status per participation (C1–C6). Task creator/assignees/watchers are distinct from team permissions.
- Status model: task Open/Completed/Discarded independent of track In Progress/Done; Not started describes absence. Closed is reversible via reopen despite source word terminal (C3, C5–C6, C13).
- Surfaces and scope: board shows open tasks; pill gives full track status including closed tasks when enabled (C7–C12, C22). Board counts unresolved (C25).
- Permissions: C18–C19, C26; guests match member permissions with project access, not admin powers. Do not claim who can Delete until Q3 answered.
- Workflow: complete supported how-to is inspecting track statuses in an accessible task via Tracks pill (C11), avoiding unverified result or UI. Start flow available but post-Start In Progress is inference C32; Stop post-state inference C33. Decision actions/state reversals C12 and C21 supported.
- Lifecycle/destructive actions: C13–C17. Explicit deletion warning, cross-project clearing, retention on close, and scope of rename/reorder required. Disable conflict C16 must remain unresolved. No invented deletion confirmation/recovery.
- Offline: C23–C24; state specific supported actions and silent dropped writes after deletion. Stop/multiselect/concurrent writes remain unknown C27.
- Limits: C4, C6, C15, C20–C21; no duplicate project track names, no start on closed task, no Stop on Done; release metadata unknown C31.

## Clarifications and contradictions

See [clarifications-and-assumptions.md](clarifications-and-assumptions.md), Q1–Q9. Preserve both Q1 citations. No working assumption selects a side. Inferences C32–C33 must not become unqualified reader-facing behavior; the selected inspection how-to does not depend on them.

## Documentation plan

| Deliverable | Reader goal | Supported topics / claim IDs | Blocked topics |
| --- | --- | --- | --- |
| Feature guide | Understand parallel track work, board/pill, lifecycle and constraints | C1–C24 | Definite disable outcome Q1, board counter Q2, Delete actor Q3, unsupported gaps Q4–Q9 |
| How-to guide | View all of a task's track statuses in one place | C11, C13, C18, C22 | None for scope; avoid unverified navigation to task |
| Release note | Scan Tracks capability and user benefit | C5–C7, C11 | Availability metadata Q8 |

See [CONTENT-PLAN.md](CONTENT-PLAN.md).

## Drafter guidance

Use task in prose; exact labels Tracks, In Progress, Done, Not started, Mark Done, Mark Pending, Stop, Select. Distinguish task completion from track Done. Do not invent counter meaning, disable consequences, deletion permissions, offline Stop/multiselect, confirmations, release date or launch availability. Draft can proceed while publication readiness remains blocked by Q1 and unresolved material detail. Keep all questions in register and surface disable conflict in feature guide. Map C1–C34 once each in COVERAGE.md, explicitly deferring inferences if unused.
