# Tracks — documentation handover

## Assignment scope
Create a newcomer feature guide, a task guide for a specific task, and a release note for existing users (source p1, Part 2 table). Part 1 requires clarification decisions. The repository supplies the reusable workflow for Part 3; this run does not alter skills. Clean-room source analysis: no earlier outputs inspected. No implemented behavior independently verified.

## Source inventory
| Source ID | Path and location | Authority / purpose | Extraction limits |
| --- | --- | --- | --- |
| S1 | input/Technical Writer - Case Study.pdf, pp1–6 | Assignment pp1–2; authoritative working-draft PRD pp2–6 | All six pages extracted and visually inspected; assignment table p1 and permission table p5 checked in rendered pages. No unreadable content. |

Only one file exists in input; no supporting artifacts or existing reader documents supplied. Existing documentation existence is UNKNOWN. Temporary page renders are outside the output set. Citation abbreviations pN below refer to S1 page N.

## Claim register
FACT means stated by this working draft, not product verification. Compound outcomes remain together only where they describe a single transition; distinct permissions and states have separate IDs.

| ID | Classification | Claim or competing statement | Evidence | Reasoning / limits |
| --- | --- | --- | --- | --- |
| C01 | FACT | Tasket organizes projects within teams. | input/Technical Writer - Case Study.pdf, p2, What Tasket is | Source assertion only. |
| C02 | FACT | Each task belongs to exactly one project. | input/Technical Writer - Case Study.pdf, p2, Tasks | Source assertion only. |
| C03 | FACT | A task has a title, comments, Studio documents and Friday chat. | input/Technical Writer - Case Study.pdf, p2, Tasks | Source assertion only. |
| C04 | FACT | A task has one creator, up to ten assignees and any number of watchers. | input/Technical Writer - Case Study.pdf, p2, Tasks | Source assertion only. |
| C05 | FACT | Task statuses are Open, Completed and Discarded; the latter two are called closed. | input/Technical Writer - Case Study.pdf, p2, Task status | Source assertion only. |
| C06 | FACT | Reopening a closed task returns it to Open. | input/Technical Writer - Case Study.pdf, p2, Task status | Source assertion only. |
| C07 | FACT | An enabled project has a Tracks tab. | input/Technical Writer - Case Study.pdf, p2, Where things appear | Source assertion only. |
| C08 | FACT | One task can occupy several tracks simultaneously, each with its own status. | input/Technical Writer - Case Study.pdf, p3, What are tracks | Source assertion only. |
| C09 | FACT | Completing or discarding a task is independent of its tracks. | input/Technical Writer - Case Study.pdf, p3, What are tracks | Source assertion only. |
| C10 | FACT | Tracks are project-scoped. | input/Technical Writer - Case Study.pdf, p3, Scope | Source assertion only. |
| C11 | FACT | A task can be on any number of tracks. | input/Technical Writer - Case Study.pdf, p3, Scope | Source assertion only. |
| C12 | FACT | A task on a track has exactly one status there: In Progress or Done. | input/Technical Writer - Case Study.pdf, p3, Scope | Source assertion only. |
| C13 | FACT | A task not started on a track is Not started there. | input/Technical Writer - Case Study.pdf, p3, Scope | Source assertion only. |
| C14 | FACT | The board has one column per track, split into In Progress and Done. | input/Technical Writer - Case Study.pdf, p3, The Tracks board / Layout | Source assertion only. |
| C15 | FACT | Columns show only open tasks. | input/Technical Writer - Case Study.pdf, p3, The Tracks board / Layout | Source assertion only. |
| C16 | FACT | Each column header displays X out of Y. | input/Technical Writer - Case Study.pdf, p3, The Tracks board / Layout | Source assertion only. |
| C17 | FACT | A task on three tracks appears in three columns. | input/Technical Writer - Case Study.pdf, p3, The Tracks board / Layout | Source assertion only. |
| C18 | FACT | Add track appears at the end of the track panels and between tracks; it allows adding and naming tracks and starting tasks. | input/Technical Writer - Case Study.pdf, p4, Managing tracks from the board | Source assertion only. |
| C19 | FACT | Track actions are Rename, Move track and Delete. | input/Technical Writer - Case Study.pdf, p4, Managing tracks from the board | Source assertion only. |
| C20 | FACT | Move track selects a column position and changes only board order. | input/Technical Writer - Case Study.pdf, p4, Managing tracks from the board; Lifecycle rules | Source assertion only. |
| C21 | FACT | In Progress column tasks offer Mark Done, Stop and Select. | input/Technical Writer - Case Study.pdf, p4, Actions on a task in a column | Source assertion only. |
| C22 | FACT | Done column tasks offer Mark Pending and Select. | input/Technical Writer - Case Study.pdf, p4, Actions on a task in a column | Source assertion only. |
| C23 | FACT | Select supports multi-select start across other tracks. | input/Technical Writer - Case Study.pdf, p4, Actions on a task in a column | Source assertion only. |
| C24 | FACT | Opening a task from a track opens its details including participants, comments, docs and chats. | input/Technical Writer - Case Study.pdf, p4, Actions on a task in a column | Source assertion only. |
| C25 | FACT | Task detail exposes a Tracks pill regardless of entry point. | input/Technical Writer - Case Study.pdf, p4, The Tracks pill | Source assertion only. |
| C26 | FACT | Opening the pill lists every project track and the task status on each. | input/Technical Writer - Case Study.pdf, p4, The Tracks pill | Source assertion only. |
| C27 | FACT | The pill offers Start for Not started tracks. | input/Technical Writer - Case Study.pdf, p4, The Tracks pill | Source assertion only. |
| C28 | FACT | The pill offers Mark Done and Stop for In Progress tracks. | input/Technical Writer - Case Study.pdf, p4, The Tracks pill | Source assertion only. |
| C29 | FACT | The pill offers Mark Pending for Done tracks. | input/Technical Writer - Case Study.pdf, p4, The Tracks pill | Source assertion only. |
| C30 | FACT | The pill counts Done tracks out of all available tracks for a task. | input/Technical Writer - Case Study.pdf, p4, The Tracks pill | Source assertion only. |
| C31 | FACT | Closing retains memberships and statuses; reopening restores column placements and statuses. | input/Technical Writer - Case Study.pdf, p4, Lifecycle rules / Close and reopen | Source assertion only. |
| C32 | FACT | Closed tasks retain a visible pill with their statuses. | input/Technical Writer - Case Study.pdf, p4, Lifecycle rules; p6, US-4 | Source assertion only. |
| C33 | FACT | Deleting a track irreversibly removes its assignments and statuses on open and closed tasks, with no undo or recovery window. | input/Technical Writer - Case Study.pdf, p4, Lifecycle rules / Delete a track; p5, US-1 | Source assertion only. |
| C34 | FACT | Renaming changes the column and pill label without changing assignments or statuses. | input/Technical Writer - Case Study.pdf, p4, Lifecycle rules / Rename a track | Source assertion only. |
| C35 | CONTRADICTION | Capability off hides and restores every track and assignment (p3), versus clearing assignments/statuses and requiring tracks and associations to be rebuilt (p5). | input/Technical Writer - Case Study.pdf, p3, Capabilities / Switching off; p5, Lifecycle rules / Switch the capability off | Both claims preserved; Q01. |
| C36 | FACT | Moving a task to another project clears all track assignments, even if a target track has the same name. | input/Technical Writer - Case Study.pdf, p5, Lifecycle rules / Cross-project move | Source assertion only. |
| C37 | FACT | Choosing assignments during cross-project move is designated a future release. | input/Technical Writer - Case Study.pdf, p5, Lifecycle rules / Cross-project move | Source assertion only. |
| C38 | FACT | Any team member can enable Tracks. | input/Technical Writer - Case Study.pdf, p2, Capabilities; p5, Permissions table | Source assertion only. |
| C39 | FACT | Only an admin can disable Tracks. | input/Technical Writer - Case Study.pdf, p2, Capabilities; p5, Permissions table | Source assertion only. |
| C40 | FACT | Any team member can create, rename and move tracks. | input/Technical Writer - Case Study.pdf, p5, Permissions table | Source assertion only. |
| C41 | FACT | Starting, Mark Done, Stop and Mark Pending require membership and task access. | input/Technical Writer - Case Study.pdf, p5, Permissions table | Source assertion only. |
| C42 | FACT | Multi-select start requires access to the selected tasks. | input/Technical Writer - Case Study.pdf, p5, Permissions table | Source assertion only. |
| C43 | FACT | Viewing the board requires membership and project access. | input/Technical Writer - Case Study.pdf, p5, Permissions table | Source assertion only. |
| C44 | FACT | Guests have member-equivalent track permissions on accessible projects. | input/Technical Writer - Case Study.pdf, p5, Permissions | Source assertion only. |
| C45 | FACT | Track names must be unique within a project. | input/Technical Writer - Case Study.pdf, p5, US-1 | Source assertion only. |
| C46 | FACT | An open task can be started on one or more tracks. | input/Technical Writer - Case Study.pdf, p6, US-2 | Source assertion only. |
| C47 | FACT | Starting an already-started task highlights its existing placement; multi-select start leaves it where it is. | input/Technical Writer - Case Study.pdf, p6, US-2 | Source assertion only. |
| C48 | FACT | A closed task must be reopened before starting it on a new track. | input/Technical Writer - Case Study.pdf, p6, US-2 | Source assertion only. |
| C49 | FACT | Mark Done changes an In Progress task to Done on that track. | input/Technical Writer - Case Study.pdf, p6, US-3 | Source assertion only. |
| C50 | FACT | Mark Pending returns a Done task to In Progress. | input/Technical Writer - Case Study.pdf, p3, Capabilities; p6, US-3 | Source assertion only. |
| C51 | FACT | A Done task cannot be stopped. | input/Technical Writer - Case Study.pdf, p6, US-3 | Source assertion only. |
| C52 | FACT | Marking a task Done on one track does not affect other tracks. | input/Technical Writer - Case Study.pdf, p6, US-3 | Source assertion only. |
| C53 | FACT | Marking the last In Progress item Done empties that section and updates the counter. | input/Technical Writer - Case Study.pdf, p6, US-3 | Source assertion only. |
| C54 | FACT | A task in a project with Tracks off has no Tracks pill. | input/Technical Writer - Case Study.pdf, p6, US-4 | Source assertion only. |
| C55 | FACT | Start, Mark Done and Mark Pending work offline; writes queue locally and reconcile on reconnect. | input/Technical Writer - Case Study.pdf, p6, Offline behaviour | Source assertion only. |
| C56 | FACT | Capability changes and creating, renaming, moving and deleting tracks require online access. | input/Technical Writer - Case Study.pdf, p6, Offline behaviour | Source assertion only. |
| C57 | FACT | A queued membership write to a track deleted online is silently dropped and does not recreate the track. | input/Technical Writer - Case Study.pdf, p6, Offline behaviour | Source assertion only. |
| C58 | FACT | If a task closes offline while its track is deleted online, sync drops that assignment; reopening cannot resurrect the track. | input/Technical Writer - Case Study.pdf, p6, Offline behaviour | Source assertion only. |
| C59 | UNKNOWN | The column counter's X and Y definitions are unspecified. | input/Technical Writer - Case Study.pdf, p3, Layout; p6, US-3 | See gap register. |
| C60 | UNKNOWN | Deletion authorization is not explicit in the permissions table; US-1 is insufficiently precise to settle it. | input/Technical Writer - Case Study.pdf, p5, Permissions table and US-1 | See gap register. |
| C61 | UNKNOWN | Offline Stop and offline bulk start support are unspecified. | input/Technical Writer - Case Study.pdf, p6, Offline behaviour; p4, Actions on a task in a column | See gap register. |
| C62 | UNKNOWN | Other concurrent-write resolution, sync failure feedback and recovery are unspecified. | input/Technical Writer - Case Study.pdf, p6, Offline behaviour | See gap register. |
| C63 | UNKNOWN | Capability settings location, confirmations and post-toggle UX are unspecified. | input/Technical Writer - Case Study.pdf, p2, Capabilities; p3, Capabilities; p5, Lifecycle rules | See gap register. |
| C64 | UNKNOWN | Exact creation and bulk-start dialogs, target selection and confirmation steps are unspecified. | input/Technical Writer - Case Study.pdf, p4, Managing tracks; Actions on a task in a column | See gap register. |
| C65 | UNKNOWN | Effects of Stop on retained history and its exact resulting UI are not explicitly defined. | input/Technical Writer - Case Study.pdf, p3, Capabilities; p4, The Tracks pill; p6, US-3 | See gap register. |
| C66 | UNKNOWN | Release date, rollout, plans and availability are not supplied. | input/Technical Writer - Case Study.pdf, p2, PRD heading; p3, Capabilities; p6, Offline behaviour | See gap register. |
| C67 | UNKNOWN | Navigation label conflicts: My Work versus Work; task versus tasket wording is inconsistent. | input/Technical Writer - Case Study.pdf, p2, Tasks and Where things appear; p4, The Tracks pill | See gap register. |
| C68 | UNKNOWN | Mutation permissions for closed-task existing memberships are not explicitly delimited. | input/Technical Writer - Case Study.pdf, p4, The Tracks pill and Lifecycle rules; p6, US-2 | See gap register. |
| C69 | INFERENCE | Starting a Not started open task places it In Progress, derived from the two-state model and explicit Done transition. | input/Technical Writer - Case Study.pdf, p3, Scope; p4, The Tracks pill; p6, US-2 and US-3 | Derived, not explicit initial-state promise; Q12. |
| C70 | UNKNOWN | Limits beyond task track-count, name validation/case sensitivity, and restricted-task visibility within accessible projects are unspecified. | input/Technical Writer - Case Study.pdf, p3, Scope; p5, Permissions and US-1 | See gap register. |
| C71 | UNKNOWN | Source calls closed statuses terminal while explicitly allowing reopen; the intended meaning of terminal is unclear. | input/Technical Writer - Case Study.pdf, p2, Task status | See gap register. |

## Product model
- Purpose and hierarchy: teams → projects → tasks (C01–C02); parallel project tracks add independent per-task statuses (C08–C13).
- Audience: team members; guests share track permissions on accessible projects (C38–C44). Do not broaden task access from project access; delete authority remains Q03.
- Work surfaces: board for open tasks (C14–C17), task pill for all project tracks (C25–C30), conditionally hidden when disabled (C54).
- State actions: Mark Done and Mark Pending (C49–C52) are a complete supported task; Start initial status is inference C69. Stop consequence remains Q08.
- Lifecycle: closure retains state, deletion destroys it, project moves clear assignments (C31–C36). Capability-off is contradictory C35, not an exception we may resolve.
- Offline: only named actions C55, online-only operations C56, deleted-track loss C57–C58. No guaranteed universal sync or recovery.
- Limits: track names unique, closed tasks cannot newly start, Done cannot stop (C45, C48, C51). Billing, migration and security implementation are outside supplied scope; access visibility is an actual gap Q13.

## Clarifications and contradictions
See clarifications-and-assumptions.md for Q01–Q14 with all material-gap fields. No unverified product ASSUMPTION is needed: editorial restrictions permit drafting. Unknowns are not contradictions; only C35 has incompatible behavior claims. C71 is ambiguous terminology because explicit reopen behavior remains usable.

## Uncertainty-neighborhood map
DIRECT also marks the gap claim itself for manifest consistency. FACT neighbors receive only the supported proximity shown; NONE explicitly protects unrelated assertions from suppression. ADJACENT does not automatically block a fact: restrict scope and review wording against the gap.

| Gap | DIRECT | ADJACENT FACT claims | NONE / independent facts | Admission instruction |
| --- | --- | --- | --- | --- |
| Q01 | C35 | C07, C25, C31, C32, C38, C39, C54, C56 | C49, C50, C52 | Block off/on restoration instructions and both incompatible promises; do not choose a side. |
| Q02 | C59 | C16, C53 | C30 | Omit numeric board interpretation; do not transfer pill semantics to columns. |
| Q03 | C60 | C19, C33, C40, C44, C56 | C41 | Document the deletion consequence without claiming which role can execute it. |
| Q04 | C61 | C23, C28, C55 | C56 | Limit offline claims to the three named actions. |
| Q05 | C62 | C55, C57, C58 | C49 | Retain explicit deletion-drop cases; promise no universal eventual success. |
| Q06 | C63 | C07, C38, C39, C54, C56 | C14 | Use Tracks already enabled as the task starting state; no fabricated settings route. |
| Q07 | C64 | C18, C23, C42, C47 | C49 | Choose task-detail state actions whose controls are specified. |
| Q08 | C65 | C13, C21, C28, C51 | C50 | Do not supply an inferred Stop outcome or history promise; omit Stop procedure. |
| Q09 | C66 | C08, C26, C52, C55 | C02 | Draft an undated capability announcement for review; no live availability or prior-state claim. |
| Q10 | C67 | C03, C04, C25 | C26 | Use task, supported repeatedly; avoid disputed navigation route. |
| Q11 | C68 | C27, C28, C29, C31, C32, C48 | C15 | Scope procedural actions to open tasks; state only closed-task retained visibility. |
| Q12 | C69 | C12, C27, C46 | C49, C50 | Keep derivation visible; use already In Progress task for selected how-to, avoiding inferred starting outcome. |
| Q13 | C70 | C11, C26, C40, C41, C42, C43, C44, C45 | C50 | State only unlimited tracks per task, name uniqueness and explicit access requirements; no broader limits or visibility guarantee. |
| Q14 | C71 | C05, C06, C31 | C33 | Use closed and explicit reopen behavior; omit terminal. |

## Documentation plan
Feature guide: newcomer mental model, surfaces, essential transitions and material lifecycle/offline consequences. How-to: mark an already In Progress open task Done on one track and optionally return it with Mark Pending, verifying the inline state. Release note: parallel workstreams and per-track progress, complete task-level view, selected offline actions only if the deletion caveat fits. Detailed ranking, relevance and exclusions are in CONTENT-PLAN.md.

## Drafter guidance
Use exact labels from TERMINOLOGY.md. Build EDITORIAL-BLUEPRINT before prose. Match every admission to this neighborhood map; update JSON destinations only after drafting. Avoid capability reset/restore assurances, counter interpretation, universal offline success, fabricated menus, release dates, deletion authority and Stop outcomes. Keep the irreversible deletion, cross-project clearing, closure-retention caveat and silent offline loss visible wherever relevant. Q01 and Q09 prevent PUBLICATION-READY; DRAFTABLE with bounded claims. Independent proofreader must recheck HIGH claims directly against original pages. No diagram needed: the three-state mental model is brief and a Start transition would introduce C69.
