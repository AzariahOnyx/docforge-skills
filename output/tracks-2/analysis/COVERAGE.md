# Tracks — source-to-document coverage

## Claim coverage

Every handover claim C1–C34 has one disposition. INCLUDED rows identify supported material used; any omitted background within a compound claim is stated explicitly. Product facts describe PRD requirements, not verified implementation.

| Claim ID | Disposition | Destination | Rationale / section | Related question |
| --- | --- | --- | --- | --- |
| C1 | INCLUDED | feature/feature-guide.md | How it works; team/project/task hierarchy. Member, admin and guest permissions appear in Access; the definition of guests as users from other organisations is background and omitted. | None |
| C2 | INCLUDED | feature/feature-guide.md | How it works and Board and task views; project ownership and task details. The title, creator and assignment limits, and Studio/Friday product names are background and omitted from this Tracks guide. | None |
| C3 | INCLUDED | feature/feature-guide.md | How it works; task states and reopening. | None |
| C4 | INCLUDED | feature/feature-guide.md | Board and task views; enabled Tracks tab. Other tabs and activity surfaces are background and omitted. | None |
| C5 | INCLUDED | feature/feature-guide.md | Overview and How it works; parallel work and independent states. | None |
| C6 | INCLUDED | feature/feature-guide.md | How it works; project scope, unlimited participation and status model. | None |
| C7 | INCLUDED | feature/feature-guide.md | Board and task views; column structure, open-only filtering and multiple placements. Counter existence appears in Working with tracks; meaning is blocked by Q2. | Q2 |
| C8 | INCLUDED | feature/feature-guide.md | Working with tracks; creation controls and management actions. | None |
| C9 | INCLUDED | feature/feature-guide.md | Working with tracks; board action table and selection. | None |
| C10 | INCLUDED | feature/feature-guide.md | Board and task views; task details. | None |
| C11 | INCLUDED | feature/feature-guide.md | Board and task views; full overview and pill count. Also how-to/how-to.md, Steps and Expected result. | None |
| C12 | INCLUDED | feature/feature-guide.md | Working with tracks; pill actions and Mark Pending result. | None |
| C13 | INCLUDED | feature/feature-guide.md | Important behavior; retention and restoration. Also how-to/how-to.md, Before you begin. | None |
| C14 | INCLUDED | feature/feature-guide.md | Working with tracks; irreversible deletion from open and closed tasks. | None |
| C15 | INCLUDED | feature/feature-guide.md | Working with tracks; rename, order and unique names. | None |
| C16 | BLOCKED | — | Conflicting disable outcomes; neither asserted as fact. Both are flagged in feature guide Important behavior. | Q1 |
| C17 | INCLUDED | feature/feature-guide.md | Important behavior; cross-project clearing. Future choice is deferred release context, not a current option. | None |
| C18 | INCLUDED | feature/feature-guide.md | Access; role and access restrictions. | None |
| C19 | INCLUDED | feature/feature-guide.md | Access; guest equivalence. | None |
| C20 | INCLUDED | feature/feature-guide.md | Working with tracks; open-task restriction and repeated/multiselect start. | None |
| C21 | INCLUDED | feature/feature-guide.md | Working with tracks and How it works; Done restriction, final item and independent status. | None |
| C22 | INCLUDED | feature/feature-guide.md | Board and task views; hidden pill. Also how-to/how-to.md, Before you begin. | None |
| C23 | INCLUDED | feature/feature-guide.md | Working offline; supported offline actions and online-only management. | None |
| C24 | INCLUDED | feature/feature-guide.md | Working offline; deleted-track sync cases. | None |
| C25 | BLOCKED | — | Board counter meaning unconfirmed; do not borrow pill counter semantics. | Q2 |
| C26 | BLOCKED | — | Delete permission not established by permission table. | Q3 |
| C27 | BLOCKED | — | Offline Stop/multiselect and other sync recovery behavior unspecified. | Q4 |
| C28 | BLOCKED | — | Exact switch and multiselect procedure, extra naming constraints and confirmation unspecified. | Q5 |
| C29 | BLOCKED | — | Work/My Work and task/task et naming unresolved; generic task navigation avoids dependency. | Q6 |
| C30 | BLOCKED | — | Closed-task editing beyond new-start restriction unspecified. | Q7 |
| C31 | BLOCKED | — | Release metadata absent; release note is a draft with no availability claim. | Q8 |
| C32 | DEFERRED | — | Inferred Start/Stop outcome is not asserted; selected viewing procedure does not require it. | Q9 |
| C33 | DEFERRED | — | Inferred Start/Stop outcome is not asserted; selected viewing procedure does not require it. | Q9 |
| C34 | CONTEXT | — | Assignment and reusable-workflow requirements govern these artifacts; packaging and submission are outside this run. | None |

## Coverage review

- Missing or duplicated claim IDs: none; 34 rows cover C1–C34.
- Release note uses C5–C7 and C11; how-to uses C11, C13, C18 and C22.
- Reader-facing passages without source support: none remain after independent source-first review. Action-table scope was restricted to open tasks to avoid implying closed-task editing.
- High-risk blocked topic: Q1, contradictory disabling outcomes. Q2–Q8 limit other claims; Q9 transitions are deferred.
- Reviewer result: all 34 claim rows, dispositions and destinations checked against the six-page original PDF and drafts. See ../qa/QA-REPORT.md; source fidelity passes within the documented scope, with publication warnings for unresolved questions.
