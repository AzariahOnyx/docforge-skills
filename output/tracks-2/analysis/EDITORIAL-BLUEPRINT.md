# Tracks — editorial blueprint

## Document contracts

| Deliverable | Primary reader | Reader job | Promise | Must include | Must exclude / defer | Success test |
| --- | --- | --- | --- | --- | --- | --- |
| Feature guide | First-time Tracks user | Understand parallel progress | Explain how one task has independent progress in several project tracks. | Task/track distinction, board/pill, access, lifecycle, deletion/move and offline consequences | Setup procedure, full control inventory, undefined counters and disputed disable outcome | Reader knows where progress lives and which actions can remove it. |
| How-to | Member finishing one workstream | Mark one track Done | Finish the selected track and recognize the result without changing other tracks. | Existing open task In Progress, access, pill action, Done result, Mark Pending recovery | Inferred Start transition, setup, Stop, bulk UI, closed-task editing | Reader can mark the selected track Done and resume it if needed. |
| Release note | Existing user scanning changes | Notice independent workstream progress | Introduce parallel progress and its task-level view in a short scan. | Independent track statuses and full track picture from task details | Procedure, release metadata, historical baseline, lifecycle reference | Reader identifies the two practical additions in under 30 seconds. |

## Feature-guide blueprint

A task belongs to one project and can participate in several of its tracks. Each track records that task's own progress, separately from the task's overall status. The board organizes open work by track; the Tracks pill gathers one task's statuses in one place.

- Essential claims: C01, C03–C06, C10–C14, C17–C22.
- Material consequences: independent completion C04/C20; close/reopen C13; irreversible deletion C14; project-move clearing C17; access C18; offline deletion loss C22. C16/Q01 stays unresolved and blocks publication of complete lifecycle guidance.
- Useful secondary claims: C08/C15 (unique names, rename and reorder). Include a short distinction between reordering a track and moving a task between projects if it improves clarity.
- Reference/edge omissions: C02 task metadata; C07 board counter; detailed C08 creation controls; C09 exhaustive action inventory; C19 duplicate-start highlighting. Record omissions in coverage.
- Section sequence: purpose and independent progress → board versus task view → access → lifecycle and destructive consequences → offline work → next task.
- Use a state-definition table, not a lifecycle diagram: no inferred Start or Stop arrows. Keep the procedure in the how-to.

## How-to selection

| Candidate | User value | Consequence | Start / action / result evidence | Assignment fit | Decision |
| --- | --- | --- | --- | --- | --- |
| Mark a task Done on one track | High: finish one discipline's work | State-changing, reversible with Mark Pending | Complete: existing In Progress, pill Mark Done, Done on that track only; C04, C11–C12, C18, C20 | Strong specific task with observable outcome | SELECT |
| Start a task across tracks | High: establish parallel work | State-changing | Initial In Progress transition inferred, C23 | Useful but less explicit evidence | REJECT for this procedure |
| Bulk start | High: update several tasks | State-changing | Target/commit controls missing, Q07 | Potentially strong | DEFER |
| Configure or delete tracks | High: organize project | Project-wide / irreversible | Missing UI and permissions, Q01/Q03/Q04 | Unsafe as full procedure | DEFER |
| View track status | Medium: inspect progress | Informational | Complete C11 | Weaker than supported state change | REJECT as sole task |

Verified start: Tracks enabled, existing open task In Progress on target track, member access to task (C06, C12, C18); guests have the stated member permissions. Open is this guide's chosen starting condition, not a claim that closed-task editing is prohibited (Q08).

Verified actions: open task details, open **Tracks** pill, select **Mark Done** on the intended track (C10–C12). Result: Done on that track, other tracks unaffected; overall task completion remains independent (C04/C20). Recovery: **Mark Pending** returns that track to In Progress (C12/C20).

Exclude setup, inferred Start destination, Stop outcome, reopening controls and batch selection. This short procedure is substantive because it changes workstream progress and has a supported reversal; the assignment does not require a long procedure. Offline instructions belong in the feature guide rather than adding unrelated steps here.

## Release-note blueprint

- Supported change: Tracks introduces independent workstream progress for one task (C04–C06), with a complete per-task picture (C11).
- Practical impact: disciplines can update progress separately while users can check all track statuses from task details.
- Priority 1: parallel participation and independent Mark Done, C04/C05/C20.
- Priority 2: project-wide track list and inline task statuses in the pill, C10/C11.
- Omit optional offline priority to keep the note focused; C21/C22 are explained with the necessary loss caveat in the guide.
- Omit date, version, rollout, platform, plan and previous-state comparisons, C24/Q10. This is proposed release copy based on a working PRD, not verification of a launch.
- Delegate permissions, lifecycle and destructive effects to feature guide. Do not advertise disabling or deletion.

## Cross-document separation

| Information | Feature guide | How-to | Release note | Reason |
| --- | --- | --- | --- | --- |
| Independent progress model | PRIMARY | BRIEF | BRIEF | Orient newcomer; establish task boundary; identify change |
| Mark Done steps and recovery | BRIEF | PRIMARY | OMIT | Action belongs in procedure |
| Board and pill | PRIMARY | BRIEF | BRIEF | Explain views; locate action; highlight new visibility |
| Access and consequential lifecycle | PRIMARY | BRIEF | OMIT | Explain risks and necessary task prerequisites |
| Offline actions and deletion exception | PRIMARY | OMIT | OMIT | Keep promise and caveat together |
| Unresolved source disputes | OMIT | OMIT | OMIT | Preserve in analysis/QA and block publication |

## Pre-draft challenge

- Must-include product statements trace to FACT evidence; C23 is excluded from procedural assertions.
- No contradiction is resolved: C16/Q01 retains both competing source claims in the handover and clarification register.
- The feature plan follows reader questions rather than source order.
- How-to has an explicit starting state, action and observable result, with a supported reversal.
- Release note selects two distinguishing capabilities rather than compressing every guide section.
- Deletion, project-move loss, permissions, lifecycle and offline write loss retain prominence in the guide.
- Removed optional offline release bullet and exhaustive action inventory because they add density without serving the scan.

Blueprint status: PASS for bounded drafting. Publication remains blocked by Q01 and release confirmation Q10; other unknowns constrain omitted administration/reference topics.

## Draft challenge result

PASS for the bounded document set. The senior editorial pass kept the guide organized around progress, views and consequences; used a status table instead of a speculative state diagram; kept the how-to to the verified Mark Done action with Mark Pending recovery; and limited the release note to two distinct capabilities. Removed setup navigation, inferred Start outcome, exhaustive action inventory and extra offline release detail. Essential deletion, cross-project and offline-loss consequences remain visible in the guide. The three articles serve different reader jobs. C16/Q01 is still unresolved, and this drafting PASS is not publication approval.

Presentation follows repository standards and the current [Microsoft style and voice guidance](https://learn.microsoft.com/en-us/style-guide/top-10-tips-style-voice), inspected during this run: direct language, sentence-case headings and concise reader-focused sections. It supplies style guidance only, never product evidence.
