# Tracks — source-to-document coverage

## Claim coverage

Each handover claim has one disposition. For grouped claims, the rationale identifies reader-facing content and any secondary details retained only as analysis. FACT means source-stated, not implementation-tested.

| Claim ID | Disposition | Destination | Rationale / section | Related question |
| --- | --- | --- | --- | --- |
| C01 | INCLUDED | feature/feature-guide.md | One task, separate progress; Who can use Tracks: project membership and role model. Team hierarchy and definition of guest organisation remain background context. | None |
| C02 | CONTEXT | — | Task metadata and participant limits do not help these three reader jobs. | Q09 |
| C03 | INCLUDED | feature/feature-guide.md | One task, separate progress; What happens when work closes or moves: Open/Completed/Discarded, closed and reopen. Avoid ambiguous terminal wording. | Q08 |
| C04 | INCLUDED | feature/feature-guide.md; how-to/how-to.md; release-note/release-note.md | Feature introduction and One task, separate progress; how-to Expected result; release introduction and first bullet: parallel work and independent completion. | None |
| C05 | INCLUDED | feature/feature-guide.md; release-note/release-note.md | One task, separate progress: project scope, any number of tracks and status definitions; release both bullets. | Q12 |
| C06 | INCLUDED | feature/feature-guide.md; how-to/how-to.md | Find progress on the board or in a task; how-to Expected result: enabled Tracks tab, columns, open-task filter and Done section. | None |
| C07 | DEFERRED | — | Counter exists and updates, but its formula is unknown; last-item empty-section detail adds little to the selected task. No counter interpretation asserted. | Q02 |
| C08 | INCLUDED | feature/feature-guide.md | Who can use Tracks: creation, naming uniqueness and organization; deletion consequence under What happens when work closes or moves. Add track placement and dialog details deferred as setup reference. | Q03, Q04 |
| C09 | CONTEXT | — | Board action inventory and bulk-start capability inform candidate ranking. The selected task uses the pill; bulk UI is incomplete. | Q05, Q07 |
| C10 | INCLUDED | feature/feature-guide.md; how-to/how-to.md; release-note/release-note.md | Feature Find progress on the board or in a task; how-to Steps; release second bullet: pill in task details without prescribing an entry tab. Assignees/docs/chat inventory stays background context. | Q09 |
| C11 | INCLUDED | feature/feature-guide.md; how-to/how-to.md; release-note/release-note.md | Feature Find progress on the board or in a task: full statuses and Done/all-available count; how-to Steps; release second bullet. | Q12 |
| C12 | INCLUDED | feature/feature-guide.md; how-to/how-to.md | Feature One task, separate progress and Work offline; how-to Steps and Resume work on the same track: Mark Done/Mark Pending. Start capability retained without inferred initial state; Stop availability not needed by selected task. | Q05 |
| C13 | INCLUDED | feature/feature-guide.md | What happens when work closes or moves: close/reopen retention, board filtering and pill visibility, adjacent deletion/move exceptions. | Q08 |
| C14 | INCLUDED | feature/feature-guide.md | What happens when work closes or moves: prominent irreversible deletion warning for open and closed tasks, no undo or recovery window. | Q03 |
| C15 | INCLUDED | feature/feature-guide.md | Who can use Tracks: rename/reorder affect label/order only, not assignments/statuses. | None |
| C16 | BLOCKED | — | Disable retention directly conflicts: p. 3 hide/restore versus p. 5 clear/recreate. Neither outcome asserted. Complete lifecycle guidance cannot be published safely until resolved. | Q01 |
| C17 | INCLUDED | feature/feature-guide.md | What happens when work closes or moves: all assignments cleared on cross-project move, including same-name tracks. Future choice is not advertised as a release commitment. | Q11 |
| C18 | INCLUDED | feature/feature-guide.md; how-to/how-to.md | Who can use Tracks and Before you begin: project/task access, guests, member enable/create/rename/reorder. Admin-only disable and bulk-access specifics retained as context for deferred administration/bulk topics, not contradicted. | Q03, Q04, Q07, Q12 |
| C19 | INCLUDED | feature/feature-guide.md | Find progress on the board or in a task: open-task Start, reopen prerequisite for new tracks, pill absent when disabled. Duplicate-start highlighting and batch no-op behavior remain edge-case context. | Q07, Q08 |
| C20 | INCLUDED | feature/feature-guide.md; how-to/how-to.md; release-note/release-note.md | Feature One task, separate progress; how-to Expected result and Resume work on the same track; release first bullet: independent Done and Mark Pending. Done cannot be stopped is retained as context because no Stop procedure is provided. | Q05 |
| C21 | INCLUDED | feature/feature-guide.md | Work offline: three named actions, queued reconciliation, management online-only. How-to links here; release intentionally omits offline claim/caveat pair. | Q06 |
| C22 | INCLUDED | feature/feature-guide.md | Work offline: silently dropped queued assignment write, no track recreation, offline-close/online-delete assignment loss with no return on reopen. | Q06 |
| C23 | CONTEXT | — | Inferred Start-to-In Progress transition informs rejected candidate only. Selected procedure begins at explicit In Progress state and asserts no inferred initial Start status. | Q04 |
| C24 | BLOCKED | — | No verified release metadata, eligibility or historical baseline; withheld from announcement copy and publication scheduling. | Q10 |

## Coverage review

- All C01–C24 appear exactly once; no additional product claims are intended.
- Reader-facing examples are limited to the source's spec/design parallel-work example (C04).
- Q01 blocks complete lifecycle publication; Q10 blocks release confirmation. Q02–Q09 and Q11–Q12 remain in the clarification register with explicit omissions or bounded wording.
- No previous source version was supplied; change-impact comparison is inapplicable.
- Drafter self-check: PASS for mapping completeness. Independent source-first meaning and omission review is recorded in the QA report.
