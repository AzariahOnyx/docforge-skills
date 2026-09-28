# Tracks — source-to-document coverage

## Claim coverage

Each claim in HANDOVER.md is mapped once. INCLUDED compound claims identify intentional background omissions. Product support is the working PRD, not implementation verification.

| Claim ID | Disposition | Destination | Rationale / section | Related question |
| --- | --- | --- | --- | --- |
| C01 | CONTEXT | — | Team collaboration background; guide includes team hierarchy via C02 and permissions via C23–C25, omits organisation model. | — |
| C02 | INCLUDED | feature/feature-guide.md | Understand tasks and tracks — project hierarchy and single-project task ownership. | — |
| C03 | CONTEXT | — | General task properties and creator/assignee limits do not explain Tracks; relevant task-detail view separately covered by C14. | Q09 |
| C04 | INCLUDED | feature/feature-guide.md | Understand tasks and tracks — task status and reopen. | — |
| C05 | INCLUDED | feature/feature-guide.md | Find your work on the board — enabled Tracks tab. Other navigation and grouping omitted as unrelated background and Q09. | — |
| C06 | INCLUDED | feature/feature-guide.md | Introduction; Understand tasks and tracks — parallel work and independent states. Also release-note/release-note.md, introduction and first bullet. | — |
| C07 | INCLUDED | feature/feature-guide.md | Understand tasks and tracks — scope, participation and states. | — |
| C08 | INCLUDED | feature/feature-guide.md | Find your work on the board — columns, sections and open-only filtering. Also how-to/how-to.md, Steps and Expected result. | — |
| C09 | BLOCKED | — | Board counter formula is unknown; display format omitted, counter update alone supported by C30. | Q02 |
| C10 | INCLUDED | feature/feature-guide.md | Manage the project’s tracks — Add track locations and capability; no detailed creation procedure. | — |
| C11 | INCLUDED | feature/feature-guide.md | Manage the project’s tracks — action names and move effect; no Delete permission assertion. | — |
| C12 | INCLUDED | feature/feature-guide.md | Find your work on the board — state-specific actions. Also how-to/how-to.md, Steps and Return the work to In Progress. | — |
| C13 | INCLUDED | feature/feature-guide.md | Find your work on the board — bulk starts; also release-note/release-note.md, second bullet. | — |
| C14 | INCLUDED | feature/feature-guide.md | See a task’s full track status — task details. | — |
| C15 | INCLUDED | feature/feature-guide.md | See a task’s full track status — full project list; also release-note/release-note.md, third bullet. | — |
| C16 | INCLUDED | feature/feature-guide.md | See a task’s full track status — pill actions described for open tasks; action availability on closed tasks left unspecified (Q06). | — |
| C17 | INCLUDED | feature/feature-guide.md | See a task’s full track status — defined pill counter only. | — |
| C18 | INCLUDED | feature/feature-guide.md | Understand what happens when tasks change — retained states and board restoration. | — |
| C19 | INCLUDED | feature/feature-guide.md | Manage the project’s tracks; Understand what happens when tasks change — irreversible deletion, closed tasks and no recovery. | — |
| C20 | INCLUDED | feature/feature-guide.md | Manage the project’s tracks — rename and move effects. | — |
| C21 | BLOCKED | — | Opposing disable outcomes preserved in handover and register only. Guide publication blocked because omitting the data-loss risk is material. | Q01 |
| C22 | INCLUDED | feature/feature-guide.md | Understand what happens when tasks change — cross-project clearing; future user choice omitted as roadmap context, no current preservation option promised. | — |
| C23 | INCLUDED | feature/feature-guide.md | Know who can act — membership and admin roles; disable result blocked separately. | — |
| C24 | INCLUDED | feature/feature-guide.md | Know who can act — task/project access. Also how-to/how-to.md, Before you begin. | — |
| C25 | INCLUDED | feature/feature-guide.md | Know who can act — guest project-access qualification. Also how-to/how-to.md, Before you begin. | — |
| C26 | INCLUDED | feature/feature-guide.md | Manage the project’s tracks — unique names within project. | — |
| C27 | INCLUDED | feature/feature-guide.md | Find your work on the board — open-only new starts and repeat-start highlight. | — |
| C28 | INCLUDED | feature/feature-guide.md | Find your work on the board — existing placement preserved in multi-select start. | — |
| C29 | INCLUDED | feature/feature-guide.md | Understand tasks and tracks — Done/Pending. Also how-to/how-to.md, Steps, Expected result and Return the work to In Progress; release-note/release-note.md, first bullet. | — |
| C30 | INCLUDED | feature/feature-guide.md | Find your work on the board — Done cannot be stopped. Also how-to/how-to.md, Expected result and Return the work to In Progress — final item and counter update. | — |
| C31 | INCLUDED | feature/feature-guide.md | See a task’s full track status — retained closed statuses, pill absent when disabled. | — |
| C32 | INCLUDED | feature/feature-guide.md | Work offline — named available actions, queued writes and reconciliation; no blanket availability claim. | — |
| C33 | INCLUDED | feature/feature-guide.md | Work offline — online-only capability and track management. | — |
| C34 | INCLUDED | feature/feature-guide.md | Work offline — both deleted-track sync cases, no recreation. | — |
| C35 | DEFERRED | — | Inferred Start/Stop outcomes not asserted; explicit Done/Pending transitions support selected procedure. | Q07 |
| C36 | BLOCKED | — | Delete authorization, safeguards and validation unspecified; only established consequences included via C19. | Q03/Q04/Q11 |
| C37 | BLOCKED | — | Closed-task editing and unstated offline/conflict behavior omitted; no inferred permissions or recovery. | Q06/Q08/Q12 |
| C38 | BLOCKED | — | Release facts and baseline absent; release draft states capability without launch or before-state claims. | Q13 |
| C39 | CONTEXT | — | Assignment scope governs these three drafts and analysis; existing reusable workflow executed, no packaging or skill edits requested. | — |
| C40 | CONTEXT | — | Inventory supports CREATE only; existing-document updates deferred and no revised-source comparison applicable. | Q14 |

## Coverage review

- All 40 claims C01–C40 accounted for exactly once; no missing or duplicate IDs.
- Reader-facing claims and every disposition/destination independently verified against all six original PDF pages, including both tables. All C01–C40 and Q01–Q14 audited; no unsupported material claim remains.
- Material publication blocker: Q01 disabling data preservation versus destruction. Q02–Q14 limit additional detail; scope choices are documented in the clarification register.
- Reader-facing text omits the internal disabling dispute; omission does not clear the publication blocker.
- Independent source-fidelity and editorial results are recorded in qa/QA-REPORT.md. Assignment drafts pass review; feature-guide publication remains blocked by Q01.
