# Tracks — editorial blueprint

Internal V2.2 drafting decision record. Source: input/Technical Writer - Case Study.pdf; evidence and locators are in HANDOVER.md. This blueprint was completed before reader-facing drafting. Q01 and Q09 remain unresolved publication blockers.

## Document contracts

| Deliverable | Primary reader | Reader job | One-sentence promise | Must include | Must exclude / defer | Success test |
| --- | --- | --- | --- | --- | --- | --- |
| Feature guide | First-time Tracks user | Understand one task across project workstreams | Explain independent statuses, where to see them, access and information-loss boundaries. | Model, board/pill distinction, lifecycle, irreversible deletion, moves, offline loss | Exhaustive actions, management tutorial, toggle outcomes, counter guesses | Reader distinguishes track Done from task closure and recognizes what can remove assignments. |
| How-to | Member or guest updating existing work | Finish one track without changing other tracks | Mark an open In Progress task Done and optionally resume it. | Verified starting state/access, pill actions, observable result, offline caveat | Start initial state, closed-task mutation, task creation, bulk actions | Inline status becomes Done; other tracks remain unchanged. |
| Release note | Existing user scanning a change | Notice two distinct Tracks capabilities | Show parallel progress and the complete task-level track view. | Two supported capabilities and guide link | Procedures, offline repetition, launch date, plan or rollout claim | Reader identifies the progress model and the consolidated view in under 30 seconds. |

## Feature-guide blueprint

- Core mental model: A task belongs to one project and can participate in several of that project's tracks. Each participating track holds its own In Progress or Done status. The project board shows open tasks, while the task's Tracks pill shows its status across project tracks. Whole-task closure is independent of track completion.
- Essential IDs: C02, C05, C07–C15, C25–C26, C31–C33, C36, C41, C43–C44, C48, C52, C55–C58.
- Material consequences: C31–C33 and C36 must be read together; C57–C58 limit offline and retention expectations. Q01 prohibits any off/on outcome assertion; Q09 prohibits live release claims.
- Secondary useful IDs: C06, C17, C30, C38–C39. Capability permissions do not authorize documentation of unresolved toggle outcomes.
- Deferred reference details: task anatomy C01/C03/C04, management C18–C20/C34/C40/C45, bulk C23/C42, duplicate start C47, counter C16/C53, Stop C21/C51. Exact admissions below supersede broad candidate lists.
- Planned sequence: purpose; task/track model; status surfaces; access; lifecycle and loss; offline limits; supported next task.
- No state diagram: a compact status definition avoids accidentally asserting an inferred Start transition. No detailed button table: the how-to owns the state-change controls.

## How-to selection

| Candidate task | User value | Consequence | Evidence completeness: start/action/result | Assignment fit | Decision |
| --- | --- | --- | --- | --- | --- |
| Mark existing In Progress task Done | High | Independent state change with supported reversal | Complete: C25–C29, C41, C49–C52 | Strong specific task | SELECT |
| Start a task across tracks | High | New participation | Incomplete initial status C69/Q12 and bulk controls Q07 | Potentially strong | REJECT pending evidence |
| Create/reorder tracks | Medium | Project organization | Creation controls incomplete Q07 | Broader than task goal | REJECT |
| View all statuses | Medium | Read only | Complete C25–C26 | Weaker than supported state change | REJECT as main task; keep as feature concept |
| Delete a track | High risk | Irreversible information loss | Authority/confirmation incomplete Q03/Q06 | Unsafe procedural choice | REJECT; warning retained in feature |

Selected task: mark an already open task that is In Progress on one track Done, with optional Mark Pending.

- Starting state: Tracks enabled; task details already open; task Open and In Progress on selected track; member with task access or guest with the same permissions on accessible project (C07, C25, C28, C41, C44).
- Actions: open Tracks pill, find In Progress track, select Mark Done (C25–C28/C49).
- Observable result: inline Done, other tracks unchanged; independent from whole-task completion (C26/C49/C52/C09).
- Recovery/continuation: Mark Pending returns to In Progress (C29/C50); this is task continuation, not sync recovery.
- Exclusions: invented navigation, initial Start state, closed-task edits, universal sync success.
- Substantiality: the procedure makes a consequential state change for a discipline; extra setup steps would weaken source fidelity rather than improve the assigned specific-task guide.

## Release-note blueprint

- Supported change: Tracks supports parallel workstreams on a single task; the working-draft PRD establishes capabilities, not shipment.
- Practical impact: maintain independent workstream progress and inspect the task's full track picture.
- Priority 1: parallel progress with per-track independence (C08/C52).
- Priority 2: every project track and task status in the Tracks pill (C25/C26).
- No priority 3: offline capability needs loss caveats and would repeat the feature/how-to without improving this short announcement.
- Omit dates, version, rollout, plans, platforms and invented prior behavior (Q09). Undated review draft; publication remains blocked.
- Delegate access, lifecycle, management and offline details to the feature guide.

## Cross-document separation

| Information | Feature guide | How-to | Release note | Reason |
| --- | --- | --- | --- | --- |
| Task/track mental model | PRIMARY | BRIEF | BRIEF | Essential local orientation only |
| Board/pill and count explanation | PRIMARY | BRIEF pill route | BRIEF view capability | No repeated reference table |
| Mark Done/Mark Pending actions | LINK | PRIMARY | OMIT | One procedure owner |
| Permissions | PRIMARY | BRIEF prerequisites | OMIT | Task success needs local access boundary |
| Closure, deletion and project move | PRIMARY | OMIT | OMIT | Procedure does not close/delete/move |
| Offline and deleted-track writes | PRIMARY | BRIEF relevant loss note | OMIT | Mark Done can queue; warning must accompany it |
| Change announcement | OMIT | OMIT | PRIMARY | Distinct scanning job |

## Claim-admission gate

One row per material claim, including deferred and direct-uncertainty claims. Final destinations are recorded in COVERAGE.md and TRACEABILITY.json. QUALIFY means the factual boundary is stated without filling neighboring gaps, not that internal uncertainty appears in customer prose.

| Claim / claim ID | Evidence | Reader value | Uncertainty proximity | Harm if misunderstood | Decision | Treatment |
| --- | --- | --- | --- | --- | --- | --- |
| C01 | FACT | LOW | NONE | LOW | DEFER | General team/project hierarchy is background; project scope is enough here. |
| C02 | FACT | USEFUL | NONE | LOW | INCLUDE | One project per task supplies scope. |
| C03 | FACT | LOW | ADJACENT | LOW | DEFER | Task attachments are unrelated background. |
| C04 | FACT | LOW | ADJACENT | LOW | DEFER | Participant counts are unrelated background. |
| C05 | FACT | USEFUL | ADJACENT | LOW | QUALIFY | Explain Completed and Discarded as closed; omit ambiguous terminal. |
| C06 | FACT | USEFUL | ADJACENT | LOW | QUALIFY | Reopening returns to Open; no irreversible closure implication. |
| C07 | FACT | USEFUL | ADJACENT | LOW | QUALIFY | Already enabled project only; no settings route or toggle result. |
| C08 | FACT | USEFUL | ADJACENT | LOW | QUALIFY | Parallel workstreams; undated PRD-based capability draft, not launch assertion. |
| C09 | FACT | USEFUL | NONE | LOW | INCLUDE | Keep whole-task closure distinct from per-track Done. |
| C10 | FACT | USEFUL | NONE | LOW | INCLUDE | Tracks belong to their project. |
| C11 | FACT | USEFUL | ADJACENT | LOW | QUALIFY | Any number of tracks per task only; no other capacity promise. |
| C12 | FACT | USEFUL | ADJACENT | LOW | QUALIFY | Exactly one of In Progress or Done per participating track; no Start outcome. |
| C13 | FACT | USEFUL | ADJACENT | LOW | QUALIFY | Not started defined without inferred Stop result. |
| C14 | FACT | USEFUL | NONE | LOW | INCLUDE | Board columns and two sections explain the project view. |
| C15 | FACT | USEFUL | NONE | LOW | INCLUDE | Only open tasks in columns; closure removes board visibility. |
| C16 | FACT | LOW | ADJACENT | LOW | DEFER | Board-counter meaning unresolved Q02; omit its display rather than invite interpretation. |
| C17 | FACT | USEFUL | NONE | LOW | INCLUDE | Source example of three tracks and three columns; scoped to open tasks. |
| C18 | FACT | LOW | ADJACENT | LOW | DEFER | Create-track flow lacks complete controls Q07; no management tutorial. |
| C19 | FACT | LOW | ADJACENT | LOW | DEFER | Management control inventory adds reference detail; deletion consequence retained separately. |
| C20 | FACT | LOW | NONE | LOW | DEFER | Column reordering is low-value for these reader jobs. |
| C21 | FACT | LOW | ADJACENT | LOW | DEFER | Board action inventory omitted; task-detail route owns selected procedure. |
| C22 | FACT | LOW | NONE | LOW | DEFER | Alternate board route omitted to keep one procedure. |
| C23 | FACT | LOW | ADJACENT | LOW | DEFER | Bulk start is a separate incomplete procedure Q07. |
| C24 | FACT | LOW | NONE | LOW | DEFER | Alternate route and attached detail inventory unnecessary because task details are the verified starting point. |
| C25 | FACT | USEFUL | ADJACENT | LOW | QUALIFY | Task detail pill, scoped to enabled project; no disputed entry-point label. |
| C26 | FACT | USEFUL | ADJACENT | LOW | QUALIFY | Every project track and inline status; no claim broadening task visibility. |
| C27 | FACT | LOW | ADJACENT | LOW | DEFER | Start route deferred with initial-state inference Q12; no unsupported starting outcome. |
| C28 | FACT | USEFUL | ADJACENT | LOW | QUALIFY | Admit Mark Done for an In Progress task only; omit Stop control and outcome. |
| C29 | FACT | USEFUL | ADJACENT | LOW | QUALIFY | Mark Pending on Done, within selected open-task scope. |
| C30 | FACT | USEFUL | NONE | LOW | INCLUDE | Count semantics explicitly pill-only. |
| C31 | FACT | ESSENTIAL | ADJACENT | HIGH | QUALIFY | Closing itself retains status; reopening uses retained status, with deletion and move limits adjacent. No toggle promise. |
| C32 | FACT | ESSENTIAL | ADJACENT | HIGH | QUALIFY | Closed-task pill visibility within enabled-project scope; no closed-task mutation promise. |
| C33 | FACT | ESSENTIAL | ADJACENT | HIGH | QUALIFY | Prominent irreversible deletion warning, open and closed tasks, no undo/recovery; no authority claim. |
| C34 | FACT | LOW | NONE | LOW | DEFER | Rename invariants are low-value management reference. |
| C35 | CONTRADICTION | ESSENTIAL | DIRECT | HIGH | BLOCK | Unresolved Q01; no reader-facing assertion. Material publication blocker. |
| C36 | FACT | ESSENTIAL | NONE | HIGH | INCLUDE | Cross-project move clears all assignments even same-name destination tracks. |
| C37 | FACT | LOW | NONE | LOW | DEFER | Future-release intent is not a dated roadmap promise; omit. |
| C38 | FACT | ESSENTIAL | ADJACENT | HIGH | QUALIFY | Member enable permission only, no setup route or outcome. |
| C39 | FACT | ESSENTIAL | ADJACENT | HIGH | QUALIFY | Admin-only disable permission, no retention/restoration claim; publication remains blocked Q01. |
| C40 | FACT | LOW | ADJACENT | HIGH | DEFER | Create/rename/reorder permission reference is outside selected tasks; no management procedure suggests broader access. |
| C41 | FACT | ESSENTIAL | ADJACENT | HIGH | QUALIFY | Task access required for status changes; selected how-to omits Start/Stop procedures. |
| C42 | FACT | LOW | ADJACENT | HIGH | DEFER | Bulk permission deferred with bulk procedure; no multi-select instructions. |
| C43 | FACT | ESSENTIAL | ADJACENT | HIGH | QUALIFY | Project access required to view board, not universal task visibility. |
| C44 | FACT | ESSENTIAL | ADJACENT | HIGH | QUALIFY | Guest equivalence only on accessible projects, preserving task-access requirement. |
| C45 | FACT | LOW | ADJACENT | LOW | DEFER | Name uniqueness belongs to deferred create-track reference. |
| C46 | FACT | LOW | ADJACENT | LOW | DEFER | Starting task procedure deferred with Q12 initial-state gap. |
| C47 | FACT | LOW | ADJACENT | LOW | DEFER | Duplicate-start edge case is outside selected goal. |
| C48 | FACT | ESSENTIAL | ADJACENT | HIGH | QUALIFY | Closed tasks must be reopened before a new track can be started; no existing-status edit promise. |
| C49 | FACT | USEFUL | NONE | LOW | INCLUDE | Verified In Progress to Done transition. |
| C50 | FACT | USEFUL | NONE | LOW | INCLUDE | Verified Done to In Progress transition. |
| C51 | FACT | LOW | ADJACENT | LOW | DEFER | Stop not taught or advertised; Done restriction deferred with Stop procedure Q08. |
| C52 | FACT | USEFUL | ADJACENT | LOW | QUALIFY | Changing one track to Done leaves other tracks unchanged. |
| C53 | FACT | LOW | ADJACENT | LOW | DEFER | Counter update edge case deferred with Q02. |
| C54 | FACT | LOW | ADJACENT | HIGH | DEFER | Off-state visibility reference deferred; drafts explicitly scoped to enabled projects and do not guide disabling. |
| C55 | FACT | ESSENTIAL | ADJACENT | HIGH | QUALIFY | Only Start, Mark Done and Mark Pending; queue/reconcile accompanied by silent deletion-drop caveat. |
| C56 | FACT | ESSENTIAL | ADJACENT | HIGH | QUALIFY | Online-only management and capability changes, with no settings path or toggle/deletion outcome. |
| C57 | FACT | ESSENTIAL | ADJACENT | HIGH | QUALIFY | Queued membership writes dropped silently if track deleted; no recreation. |
| C58 | FACT | ESSENTIAL | ADJACENT | HIGH | QUALIFY | Offline closure plus online deletion loses assignment at sync; reopening does not restore deleted track. |
| C59 | UNKNOWN | LOW | DIRECT | LOW | DEFER | Unresolved Q02; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. |
| C60 | UNKNOWN | LOW | DIRECT | HIGH | DEFER | Unresolved Q03; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. |
| C61 | UNKNOWN | LOW | DIRECT | HIGH | DEFER | Unresolved Q04; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. |
| C62 | UNKNOWN | LOW | DIRECT | HIGH | DEFER | Unresolved Q05; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. |
| C63 | UNKNOWN | LOW | DIRECT | LOW | DEFER | Unresolved Q06; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. |
| C64 | UNKNOWN | LOW | DIRECT | LOW | DEFER | Unresolved Q07; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. |
| C65 | UNKNOWN | LOW | DIRECT | LOW | DEFER | Unresolved Q08; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. |
| C66 | UNKNOWN | ESSENTIAL | DIRECT | HIGH | BLOCK | Unresolved Q09; no reader-facing assertion. Material publication blocker. |
| C67 | UNKNOWN | LOW | DIRECT | LOW | DEFER | Unresolved Q10; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. |
| C68 | UNKNOWN | LOW | DIRECT | HIGH | DEFER | Unresolved Q11; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. |
| C69 | INFERENCE | LOW | DIRECT | LOW | DEFER | Unresolved Q12; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. |
| C70 | UNKNOWN | LOW | DIRECT | HIGH | DEFER | Unresolved Q13; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. |
| C71 | UNKNOWN | LOW | DIRECT | LOW | DEFER | Unresolved Q14; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. |

## Pre-draft challenge

- All must-include behavior maps to FACT claims; C35 and C59–C71 are withheld.
- No contradiction is resolved: Q01 remains a publication blocker. No toggle outcome enters the guide or procedure.
- Feature order follows understanding, finding status, access, consequences and next task, rather than PRD order.
- Selected how-to has a complete bounded start/action/result; no inferred Start state.
- Release priorities distinguish independent progress from consolidated visibility; no release metadata is invented.
- Deletion and moves remain prominent; offline claims include silent loss; retention does not promise restoration after unrelated destructive changes.
- Removed management/action inventory, roadmap, duplicates and counter interpretation before drafting. Remaining sections each serve the document contract.

Blueprint status: PASS for bounded drafting. Publication remains BLOCKED by Q01 and Q09; this is not a publication or independent-QA verdict.

## Draft challenge result

PASS — Drafter senior editorial and sentence-level restraint pass completed; independent source-first review also PASS.

- Built the feature around independent progress and board versus task view, with access before lifecycle consequences. Removed management reference tables, duplicate action explanations and general Tasket anatomy.
- Kept the how-to to a verified state change from already open task details. Separated observable Done from optional Mark Pending continuation; did not invent Start's initial state or closed-task editing.
- Limited the release note to two distinguishable capabilities. Removed offline as a third priority to avoid repeating a warning-heavy explanation; no unsupported rollout wording or before-state appears.
- Retained permanent deletion, same-name cross-project clearing, task access, silent offline drop and the offline-close/deleted-track case. Closure retention explicitly concerns retained statuses and sits beside deletion/move limits; it does not guarantee recovery after unrelated changes. No toggle outcome is supplied.
- Example gate: the spec/design example and three-column example are SOURCE; the selected task starting state is a supported PRODUCT-BEHAVIOR scenario, not an invented task narrative. No fabricated example names, UI, permissions or outcomes.
- Markdown normalized, local links target the three canonical draft files, and claim destinations/coverage were reconciled after prose creation. No extra reader-facing article.

Claim-admission self-audit: PASS for bounded draft claims. Blueprint compliance: PASS in Drafter review. Q01 and Q09 stay publication blockers. Independent Proofreader final V2.2 gates: PASS; see qa/QA-REPORT.md for source evidence, separate gate results and REVIEW-READY decision.
