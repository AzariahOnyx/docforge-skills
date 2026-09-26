# Tracks — documentation handover

> Internal documentation contract. Product behavior below is sourced from a working PRD, not verified in a running product. Keep unresolved items unresolved.

## Assignment scope

The assignment asks for (1) clarifications with a working assumption for each, (2) a first-time user feature document, a task-focused how-to guide, and a brief release note, and (3) a reusable skill for a different PRD. The live round requires a rerun and a skill modification (pp. 1-2).

- Source authority: `input/Technical Writer - Case Study.pdf`, six pages. Pages 1-2 contain assignment instructions; the Tracks PRD begins on page 2 and continues through page 6.
- Coverage: extracted and visually checked all six pages, including the assignment table on page 1 and permissions table on page 5. No unreadable pages or supporting artifacts were provided.
- Audience: first-time user, task-oriented user, and existing user, respectively. No product style guide, screenshots, or actual application access was supplied.

## Claim register

FACT means the working PRD states it; implementation remains unverified. CONTRADICTION entries preserve incompatible claims. UNKNOWN records a gap. The `C20A/C20B` pair must not be resolved by assumption.

| ID | Class | Statement | Evidence |
| --- | --- | --- | --- |
| C01 | FACT | Tasket has teams with members, admins, and guests; projects belong to teams and contain tasks. | input/Technical Writer - Case Study.pdf, p. 2, What Tasket is |
| C02 | FACT | A task belongs to exactly one project. | input/Technical Writer - Case Study.pdf, p. 2, Tasks |
| C03 | FACT | Task statuses are Open, Completed, and Discarded; the latter two are called closed, and reopening returns a task to Open. | input/Technical Writer - Case Study.pdf, p. 2, Task status |
| C04 | FACT | A project's Tracks tab appears when Tracks is enabled; My Work lists assigned tasks and Updates lists activity for participants. | input/Technical Writer - Case Study.pdf, p. 2, Where things appear |
| C05 | FACT | Tracks lets a task take part in multiple workstreams at once, each with its own status. | input/Technical Writer - Case Study.pdf, p. 3, What are tracks |
| C06 | FACT | Tracks are project-scoped; a task can be on any number of tracks and has one status on each started track: In Progress or Done. A non-started track is Not started for that task. | input/Technical Writer - Case Study.pdf, p. 3, Scope |
| C07 | FACT | Completing or discarding the task is independent of which tracks it has started on. | input/Technical Writer - Case Study.pdf, p. 3, What are tracks |
| C08 | FACT | The Tracks board has one column per track, split into In Progress and Done sections, showing only open tasks. | input/Technical Writer - Case Study.pdf, p. 3, The Tracks board > Layout |
| C09 | FACT | A task on three tracks appears in three board columns. A column header has an X out of Y counter. | input/Technical Writer - Case Study.pdf, p. 3, The Tracks board > Layout |
| C10 | FACT | Add track is located at the end of the track panels and between tracks; it lets a user name a track and start tasks on it. | input/Technical Writer - Case Study.pdf, p. 4, Managing tracks from the board |
| C11 | FACT | Track actions include Rename, Move track, and Delete; Move track chooses a board position. | input/Technical Writer - Case Study.pdf, p. 4, Managing tracks from the board |
| C12 | FACT | In Progress task actions on the board are Mark Done, Stop, and Select; Done task actions are Mark Pending and Select. | input/Technical Writer - Case Study.pdf, p. 4, Actions on a task in a column |
| C13 | FACT | Select supports choosing multiple tasks and starting them on other tracks. | input/Technical Writer - Case Study.pdf, p. 4, Actions on a task in a column |
| C14 | FACT | The task detail view shows a Tracks pill regardless of the entry point; opening it lists all project tracks with this task's Not started, In Progress, or Done status. | input/Technical Writer - Case Study.pdf, p. 4, The Tracks pill |
| C15 | FACT | The pill offers Start for Not started, Mark Done and Stop for In Progress, and Mark Pending for Done; it shows Done tracks out of available tracks. | input/Technical Writer - Case Study.pdf, p. 4, The Tracks pill |
| C16 | FACT | The pill is the one view that shows the task's full track picture. | input/Technical Writer - Case Study.pdf, p. 4, The Tracks pill |
| C17 | FACT | Closing an open task retains its track membership and statuses while hiding it from board columns; the pill continues showing statuses; reopening restores the task to its former columns and statuses. | input/Technical Writer - Case Study.pdf, p. 4, Lifecycle rules > Close and reopen |
| C18 | FACT | Deleting a track irreversibly removes its assignments and statuses from open and closed tasks, with no undo or recovery window. | input/Technical Writer - Case Study.pdf, p. 4, Lifecycle rules > Delete a track; p. 5, US-1 |
| C19 | FACT | Renaming changes the column/pill label without changing statuses or assignments; moving changes only column order. | input/Technical Writer - Case Study.pdf, p. 4, Lifecycle rules > Rename/Move; p. 5, US-1 |
| C20A | CONTRADICTION | Switching Tracks off hides it without deleting tracks or assignments; switching it back on restores them exactly. | input/Technical Writer - Case Study.pdf, p. 3, Capabilities > Switch the Tracks capability on and off |
| C20B | CONTRADICTION | Switching Tracks off clears assignments and per-track statuses; switching it back on requires an admin to recreate tracks and associations. | input/Technical Writer - Case Study.pdf, p. 5, Lifecycle rules > Switch the capability off |
| C21 | FACT | Moving a task to another project clears track assignments, even when a target track has the same name; a user choice is deferred to a future release. | input/Technical Writer - Case Study.pdf, p. 5, Lifecycle rules > Cross-project move |
| C22 | FACT | Any team member can enable Tracks, create, rename, or move a track; only an admin can disable Tracks. | input/Technical Writer - Case Study.pdf, p. 2, Capabilities; p. 5, Permissions |
| C23 | FACT | Starting a task, changing its track state, or selecting and starting tasks requires access to the affected task(s); viewing the board requires project access. | input/Technical Writer - Case Study.pdf, p. 5, Permissions |
| C24 | FACT | Guests have the same track permissions as members on projects they can access. | input/Technical Writer - Case Study.pdf, p. 5, Permissions, paragraph after table |
| C25 | FACT | Two tracks in one project cannot share a name. | input/Technical Writer - Case Study.pdf, p. 5, US-1 |
| C26 | FACT | Starting a task already on a track highlights its existing placement; multi-select leaves a task already on the target track in place. | input/Technical Writer - Case Study.pdf, p. 6, US-2 |
| C27 | FACT | A closed task cannot start on a new track until reopened. | input/Technical Writer - Case Study.pdf, p. 6, US-2 |
| C28 | FACT | Mark Done changes In Progress to Done and Mark Pending changes Done to In Progress; marking Done in one track leaves other tracks unchanged. | input/Technical Writer - Case Study.pdf, p. 3, Capabilities; p. 6, US-3 |
| C29 | FACT | A Done task cannot be stopped; marking the last In Progress task Done empties that section and updates the counter. | input/Technical Writer - Case Study.pdf, p. 6, US-3 |
| C30 | FACT | A closed task retains a visible pill with statuses; a task in a project with Tracks switched off shows no pill. | input/Technical Writer - Case Study.pdf, p. 6, US-4 |
| C31 | FACT | Start, Mark Done, and Mark Pending can be used offline; writes queue locally and reconcile on reconnect. | input/Technical Writer - Case Study.pdf, p. 6, Offline behaviour |
| C32 | FACT | Switching Tracks on/off and creating, renaming, moving, or deleting tracks require an online connection. | input/Technical Writer - Case Study.pdf, p. 6, Offline behaviour |
| C33 | FACT | A queued membership write for a track deleted online is silently dropped on sync, without recreating the track. | input/Technical Writer - Case Study.pdf, p. 6, Offline behaviour |
| C34 | FACT | If a task closes offline while its track is deleted online, the deleted track assignment is dropped on sync and does not reappear on reopen. | input/Technical Writer - Case Study.pdf, p. 6, Offline behaviour |
| C35 | UNKNOWN | The X and Y in a board column's counter are not defined. | input/Technical Writer - Case Study.pdf, p. 3, Layout; p. 6, US-3 |
| C36 | UNKNOWN | The permissions table does not list Delete a track, although the capability and US-1 mention deletion. | input/Technical Writer - Case Study.pdf, pp. 3-5, Capabilities, Permissions, US-1 |
| C37 | UNKNOWN | The PRD does not give an exact UI sequence for enabling Tracks, creating a track, or bulk starting tasks. | input/Technical Writer - Case Study.pdf, pp. 2-6, Capabilities, board, US-1/US-2 |
| C38 | UNKNOWN | The PRD does not specify whether Stop or Select works offline, or how queued writes fail/retry beyond the deleted-track case. | input/Technical Writer - Case Study.pdf, p. 6, Offline behaviour |
| C39 | UNKNOWN | The PRD does not state whether a closed task's retained track statuses can be edited through the pill while it remains closed. | input/Technical Writer - Case Study.pdf, p. 4, pill/lifecycle; p. 6, US-2/US-4 |
| C40 | UNKNOWN | Release date, rollout plan, platform availability, and migration guidance are not stated. | input/Technical Writer - Case Study.pdf, pp. 1-6, assignment and PRD |

## Product model

- **Structure and scope:** Teams contain projects; a task belongs to one project, and tracks are project-scoped (C01, C02, C06). A task can participate in multiple tracks at once (C05, C06).
- **Separate state systems:** Task status is Open, Completed, or Discarded (C03). For each project track the task is Not started, In Progress, or Done; the latter two represent started membership (C06). Mark Done and Mark Pending change only that track's state (C28). Closing a task is separate (C07, C17).
- **Board:** One column per track, split into In Progress and Done; only open tasks appear, and a multi-track task appears in multiple columns (C08, C09). The X/Y counter exists but its calculation is unknown (C35, Q02).
- **Pill:** Opening a task's Tracks pill shows the task's status across project tracks and the state-dependent actions (C14-C16). Closed tasks retain the displayed statuses (C17, C30), but editing them while closed is unknown (Q10).
- **Management:** Add track, Rename, Move track, and Delete are specified (C10, C11). Rename preserves membership; move affects only order (C19). Delete permanently removes the track's statuses and assignments for open and closed tasks (C18); deletion permission and confirmation UI need clarification (Q03).
- **Lifecycle:** Closing hides the task from the board and reopening restores its prior placement and track statuses (C17). Moving the task across projects clears track assignments even if names match (C21). Disabling has mutually incompatible data-retention rules (C20A/C20B, Q01).
- **Permissions:** Explicit rows authorize enable/create/rename/move for team members and disable for admins; task actions and board view require the corresponding access (C22-C24). Delete is omitted from the permissions table (Q03). Do not infer that a guest gains admin-only rights.
- **Offline:** Start, Mark Done, and Mark Pending queue while offline; capability switches and track management are online-only (C31, C32). Deleted tracks cause queued membership writes to be dropped silently; a specific offline-close/deleted-track case is given (C33, C34). Stop, Select, conflict feedback, and general offline close behavior are unspecified (Q04, Q11, Q15).
- **Limits and edges:** No duplicate track names (C25); already-started targets are handled without duplicate placement (C26); a closed task cannot start a new track (C27); Done cannot be stopped (C29). A disabled project hides the pill (C30), but its data retention is unresolved (Q01).

## Clarifications and contradictions

The complete question, evidence, why, editorial assumption, and documentation impact for every ID are in `clarifications-and-assumptions.md`.

| ID | Topic | Class | Evidence IDs | Draft impact |
| --- | --- | --- | --- | --- |
| Q01 | Disabling Tracks | CONTRADICTION | C20A (p. 3) and C20B (p. 5) | Blocks disable/re-enable instructions and any data-retention claim; QA publication WARNING. |
| Q02 | Board counter | UNKNOWN | C09, C29, C35 (pp. 3, 6) | Omit counter interpretation and numerical examples. |
| Q03 | Track deletion permission | UNKNOWN | C11, C18, C22, C36 (pp. 3-5) | Describe destructive effect; defer delete procedure and permission claim. |
| Q04 | Stop outcome and offline access | UNKNOWN | C06, C12, C15, C38 (pp. 3-4, 6) | Block Stop procedure and avoid claiming offline support. |
| Q05 | Add track flow | UNKNOWN | C10, C37 (p. 4) | Choose a supported state-change how-to instead. |
| Q06 | Enablement setup | UNKNOWN | C04, C22, C37 (pp. 2, 5-6) | Omit enablement procedure and default-state claim. |
| Q07 | Multi-select flow | UNKNOWN | C13, C23, C26, C37 (pp. 4-6) | Omit detailed bulk-start steps. |
| Q08 | Access and guests | UNKNOWN | C01, C22-C24 (pp. 2, 5) | Keep permission statements scoped to explicit table rows. |
| Q09 | Cross-project move safeguards | UNKNOWN | C21 (p. 5) | Include a brief warning in conceptual documentation; no move procedure. |
| Q10 | Closed task pill actions | UNKNOWN | C15, C17, C27, C30, C39 (pp. 4, 6) | Restrict how-to to an open task. |
| Q11 | Offline conflict feedback | UNKNOWN | C31-C34, C38 (p. 6) | Avoid guarantees of successful sync or feedback. |
| Q12 | Terminology and labels | UNKNOWN | C04, C14, pp. 2, 4; 'tasket' pp. 2-3 | Use stable labels Tracks tab, Tracks pill, Mark Done, Mark Pending. |
| Q13 | Pill progress denominator | UNKNOWN | C15 (p. 4) | Mention statuses without a numeric example. |
| Q14 | Release availability | UNKNOWN | C40 (pp. 1-6) | Keep release note limited to confirmed capabilities. |
| Q15 | Offline close behavior | UNKNOWN | C17, C34 (pp. 4, 6) | Do not advertise a general offline close/reopen workflow. |
| Q16 | Terminal status language | UNKNOWN | C03 (p. 2) | Avoid 'permanently completed' or irreversible task-status language. |
| Q17 | Feature disable and offline writes | UNKNOWN | C20A/C20B (pp. 3, 5), C31-C34 (p. 6) | Exclude from drafts; flag for product confirmation. |

### Critical conflict: switching Tracks off

- **C20A, page 3, Capabilities:** off is a hide; on again restores tracks and assignments exactly.
- **C20B, page 5, Lifecycle rules:** off clears assignments/statuses; on again requires rebuilding tracks and associations.
- **Related C30, page 6, US-4:** the pill is hidden while off. This describes visibility but does not resolve retention.
- **Decision:** No side selected. Q01 blocks any end-user claim about data retention, restoration, or rebuilding when switching the capability off/on. The assignment may include a draft with this material explicitly unresolved; it cannot be published as a complete disable/re-enable guide.

## Documentation plan

See `CONTENT-PLAN.md` for CREATE / UPDATE / DEFER scope, destinations, and information architecture.

| Deliverable | Reader goal | Supported claim IDs | Excluded or blocked |
| --- | --- | --- | --- |
| Feature guide | Understand parallel workstreams, state, board, pill, and lifecycle | C05-C08, C12, C14-C19, C21-C24, C27-C32 | Disable retention Q01; counter meaning Q02; Delete procedure/permission Q03; closed-task edits Q10 |
| How-to: Mark a task Done on a track | Change one open task's per-track status | C04, C08, C12, C23, C28, C31 | Unspecified first-time enablement Q06; unknown counter meaning Q02 |
| Release note | Scan new capability and major user impact | C05, C06, C08, C14, C17, C28, C31 | Release metadata Q14; disable retention Q01 |

## Drafter guidance

- Use **task** for the work item, **track** for a project-scoped workstream, and UI labels **Tracks tab**, **Tracks pill**, **Mark Done**, **Mark Pending**, **In Progress**, **Done**, **Not started**. Avoid relying on the inconsistent “tasket” or “Work tab” wording (Q12).
- Present only FACT claims as unqualified product behavior. Do not turn the editorial working assumptions in the clarification register into product claims. No product behavior has been assumed to settle Q01.
- For the how-to, choose an open task already In Progress on a track and use the board's specified Mark Done action. Do not invent Settings navigation, a Save button, a confirmation dialog, or a counter formula.
- Mention irreversible track deletion and cross-project assignment loss accurately where useful, but do not fabricate warnings or undo controls.
- Publication readiness: the core introductory and state-change drafts can be reviewed. Disable/re-enable behavior requires product clarification before complete public documentation.

## Draft claim map (review-only)

- `feature/feature-guide.md`: overview C05-C07; board C08-C09/C12; pill C14-C16; close/reopen C17/C30; rename/move/delete C18-C19; cross-project C21; permissions C22-C24; offline C31-C34.
- `how-to/how-to.md`: prerequisite C04/C08/C23; board action C12/C28; outcome C08/C28; offline note C31.
- `release-note/release-note.md`: C05-C06, C08, C14-C17, C28, C31.

This map is for the reviewer and should be checked against the actual passages in the drafts.
