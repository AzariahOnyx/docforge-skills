# Tracks — editorial blueprint

> Internal drafting artifact. Built from the analyzed source evidence; not user documentation.

## Document contracts

| Deliverable | Primary reader | Reader job | One-sentence promise | Must include | Must exclude / defer | Success test |
| --- | --- | --- | --- | --- | --- | --- |
| Feature guide | First-time Tracks user | Understand the model and consequential behavior | Explain how task status and per-track progress work together | Project scope, state separation, board/pill model, material lifecycle/permission/offline consequences | Counter formula, unsupported procedures, unresolved disable outcome | Reader can explain where progress lives and what major actions affect |
| How-to | User updating track progress | Mark one track Done and resume it if needed | Complete one verified state change without affecting other tracks | Prerequisites, Mark Done, observable Done result, Mark Pending reversal | Inferred Start/Stop behavior and unsupported bulk sequence | Reader can complete and verify the task from supported controls |
| Release note | Existing user scanning the change | Notice the main new capability | Summarize independent track progress and the highest-value supporting capabilities | Independent progress, selected-task starts, task-wide Tracks pill | Procedure detail, launch metadata, unsupported previous-state comparison | Reader can identify the practical change in under 30 seconds |

## Feature-guide blueprint

- Core mental model: A task belongs to one project, while a project can have multiple Tracks. Task status is separate from per-track progress, so the same task can progress independently across multiple workstreams.
- Essential claim IDs: C02, C04, C06–C08, C12–C18, C22–C25, C29–C34
- Material consequences / risks that must remain visible: C18–C21, C23–C26, C32–C37; Q01
- Useful but secondary claim IDs: C09–C13, C27–C28
- Edge/reference claims to omit or defer: undefined counter formula and unsupported detailed procedures
- Planned section sequence:
  1. Establish task versus track scope and states.
  2. Explain the board and task-level Tracks view.
  3. Explain management, lifecycle, offline, and access consequences.
  4. Link to the supported task.
- Duplication to avoid: Keep step-by-step Mark Done instructions in the how-to and release-note scanning detail in the release note.

## How-to selection

| Candidate task | User value | Consequence | Evidence completeness: start/action/result | Assignment fit | Decision |
| --- | --- | --- | --- | --- | --- |
| Mark Done and resume with Mark Pending | High | State change | Complete: C08, C12, C24, C29–C30, C32 | Acceptable | SELECT — strongest complete supported state-changing task |
| Start or Stop | High | State change | Incomplete: C35/Q07 | Weak | REJECT — outcome gap |
| Bulk start selected tasks | High | State change | Incomplete: C13/C28/Q10 | Strong if clarified | REJECT — sequence gap |
| Delete a track | High | Irreversible | Incomplete: C11/C19/Q03/Q04 | Strong if clarified | REJECT — permission/safeguard gaps |

Selected task: Mark a task Done on one track.

- Verified starting state: open task, In Progress on the target track
- Verified user actions and exact UI labels: Tracks tab, Mark Done, Mark Pending
- Verified observable result: Done on that track; other tracks unchanged
- Supported reversal/recovery, if any: Mark Pending returns the track state to In Progress
- Explicitly excluded steps/outcomes: inferred Start/Stop behavior, unsupported bulk-start sequence
- Substantiality note: Narrower than ideal, but it is the strongest complete state-changing procedure supported by the source.

## Release-note blueprint

- Supported change: Tracks supports parallel workstreams for the same task with independent per-track progress.
- Practical user impact: Users can coordinate progress across workstreams without completing the task itself.
- Priority 1: Independent track progress — C06/C29
- Priority 2: Start selected tasks across tracks — C13
- Priority 3: Review all track statuses through the Tracks pill — C15–C17
- Release metadata intentionally omitted: date, version, rollout, platform, previous-state baseline
- Details delegated to feature guide: model, lifecycle, permissions, offline behavior

## Cross-document separation

| Information | Feature guide | How-to | Release note | Reason |
| --- | --- | --- | --- | --- |
| Task vs track mental model | PRIMARY | BRIEF | BRIEF | Essential newcomer context |
| Mark Done procedure | BRIEF | PRIMARY | BRIEF | Procedure belongs in task article |
| Management/lifecycle/offline consequences | PRIMARY | OMIT | OMIT | Important understanding, not scanning/task detail |
| Three headline capabilities | BRIEF | OMIT | PRIMARY | Existing-user scan goal |

## Pre-draft challenge

- All must-include product behavior traces to FACT evidence.
- Q01 remains unresolved; neither disputed disable outcome is selected.
- The feature sequence follows reader questions rather than PRD order.
- The selected how-to has supported start, action, and result.
- Release-note priorities are distinct and limited.
- Material irreversible and lifecycle consequences remain visible.

Blueprint status: PASS for assignment drafting; Q01 remains a publication blocker.

## Draft challenge result

PASS. Reader-facing drafts were shaped around distinct reader jobs, low-value reference detail was deferred, the narrow how-to was retained instead of padded with unsupported actions, and the release note was reduced to three high-value capabilities. Q01 remains unresolved.
