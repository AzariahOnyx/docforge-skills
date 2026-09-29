# Tracks — source-to-document coverage

Review artifact. Each of the 71 material handover claims has exactly one disposition. INCLUDED can admit only the useful portion of a compound claim; its rationale states the boundary. FACT means a PRD requirement, not verified implementation.

## Claim coverage

| Claim ID | Disposition | Destination | Rationale / section | Related question |
| --- | --- | --- | --- | --- |
| C01 | CONTEXT | — | General team/project hierarchy is background; project scope is enough here. | None |
| C02 | INCLUDED | feature/feature-guide.md#how-tracks-relate-to-tasks | One project per task supplies scope. | None |
| C03 | CONTEXT | — | Task attachments are unrelated background. | Q10 |
| C04 | CONTEXT | — | Participant counts are unrelated background. | Q10 |
| C05 | INCLUDED | feature/feature-guide.md#when-a-task-closes-or-moves | Explain Completed and Discarded as closed; omit ambiguous terminal. | Q14 |
| C06 | INCLUDED | feature/feature-guide.md#when-a-task-closes-or-moves | Reopening returns to Open; no irreversible closure implication. | Q14 |
| C07 | INCLUDED | feature/feature-guide.md#find-your-track-status; how-to/how-to.md#before-you-begin | Already enabled project only; no settings route or toggle result. | Q01, Q06 |
| C08 | INCLUDED | feature/feature-guide.md#follow-parallel-work-with-tracks; release-note/release-note.md#track-parallel-progress-on-a-single-task | Parallel workstreams; undated PRD-based capability draft, not launch assertion. | Q09 |
| C09 | INCLUDED | feature/feature-guide.md#how-tracks-relate-to-tasks; how-to/how-to.md#expected-result | Keep whole-task closure distinct from per-track Done. | None |
| C10 | INCLUDED | feature/feature-guide.md#how-tracks-relate-to-tasks | Tracks belong to their project. | None |
| C11 | INCLUDED | feature/feature-guide.md#how-tracks-relate-to-tasks | Any number of tracks per task only; no other capacity promise. | Q13 |
| C12 | INCLUDED | feature/feature-guide.md#how-tracks-relate-to-tasks | Exactly one of In Progress or Done per participating track; no Start outcome. | Q12 |
| C13 | INCLUDED | feature/feature-guide.md#how-tracks-relate-to-tasks | Not started defined without inferred Stop result. | Q08 |
| C14 | INCLUDED | feature/feature-guide.md#find-your-track-status | Board columns and two sections explain the project view. | None |
| C15 | INCLUDED | feature/feature-guide.md#find-your-track-status; feature/feature-guide.md#when-a-task-closes-or-moves | Only open tasks in columns; closure removes board visibility. | None |
| C16 | DEFERRED | — | Board-counter meaning unresolved Q02; omit its display rather than invite interpretation. | Q02 |
| C17 | INCLUDED | feature/feature-guide.md#find-your-track-status | Source example of three tracks and three columns; scoped to open tasks. | None |
| C18 | DEFERRED | — | Create-track flow lacks complete controls Q07; no management tutorial. | Q07 |
| C19 | DEFERRED | — | Management control inventory adds reference detail; deletion consequence retained separately. | Q03 |
| C20 | DEFERRED | — | Column reordering is low-value for these reader jobs. | None |
| C21 | DEFERRED | — | Board action inventory omitted; task-detail route owns selected procedure. | Q08 |
| C22 | DEFERRED | — | Alternate board route omitted to keep one procedure. | None |
| C23 | DEFERRED | — | Bulk start is a separate incomplete procedure Q07. | Q04, Q07 |
| C24 | DEFERRED | — | Alternate route and attached detail inventory unnecessary because task details are the verified starting point. | None |
| C25 | INCLUDED | feature/feature-guide.md#find-your-track-status; how-to/how-to.md#steps | Task detail pill, scoped to enabled project; no disputed entry-point label. | Q01, Q10 |
| C26 | INCLUDED | feature/feature-guide.md#find-your-track-status; how-to/how-to.md#steps; release-note/release-note.md#track-parallel-progress-on-a-single-task | Every project track and inline status; no claim broadening task visibility. | Q09, Q13 |
| C27 | DEFERRED | — | Start route deferred with initial-state inference Q12; no unsupported starting outcome. | Q11, Q12 |
| C28 | INCLUDED | how-to/how-to.md#steps | Admit Mark Done for an In Progress task only; omit Stop control and outcome. | Q04, Q08, Q11 |
| C29 | INCLUDED | how-to/how-to.md#resume-work-on-the-track | Mark Pending on Done, within selected open-task scope. | Q11 |
| C30 | INCLUDED | feature/feature-guide.md#find-your-track-status | Count semantics explicitly pill-only. | None |
| C31 | INCLUDED | feature/feature-guide.md#when-a-task-closes-or-moves | Closing itself retains status; reopening uses retained status, with deletion and move limits adjacent. No toggle promise. | Q01, Q11, Q14 |
| C32 | INCLUDED | feature/feature-guide.md#when-a-task-closes-or-moves | Closed-task pill visibility within enabled-project scope; no closed-task mutation promise. | Q01, Q11 |
| C33 | INCLUDED | feature/feature-guide.md#when-a-task-closes-or-moves | Prominent irreversible deletion warning, open and closed tasks, no undo/recovery; no authority claim. | Q03 |
| C34 | DEFERRED | — | Rename invariants are low-value management reference. | None |
| C35 | BLOCKED | — | Unresolved Q01; no reader-facing assertion. Material publication blocker. | Q01 |
| C36 | INCLUDED | feature/feature-guide.md#when-a-task-closes-or-moves | Cross-project move clears all assignments even same-name destination tracks. | None |
| C37 | CONTEXT | — | Future-release intent is not a dated roadmap promise; omit. | None |
| C38 | INCLUDED | feature/feature-guide.md#access-to-tracks | Member enable permission only, no setup route or outcome. | Q01, Q06 |
| C39 | INCLUDED | feature/feature-guide.md#access-to-tracks | Admin-only disable permission, no retention/restoration claim; publication remains blocked Q01. | Q01, Q06 |
| C40 | DEFERRED | — | Create/rename/reorder permission reference is outside selected tasks; no management procedure suggests broader access. | Q03, Q13 |
| C41 | INCLUDED | feature/feature-guide.md#access-to-tracks; how-to/how-to.md#before-you-begin | Task access required for status changes; selected how-to omits Start/Stop procedures. | Q13 |
| C42 | DEFERRED | — | Bulk permission deferred with bulk procedure; no multi-select instructions. | Q07, Q13 |
| C43 | INCLUDED | feature/feature-guide.md#access-to-tracks | Project access required to view board, not universal task visibility. | Q13 |
| C44 | INCLUDED | feature/feature-guide.md#access-to-tracks; how-to/how-to.md#before-you-begin | Guest equivalence only on accessible projects, preserving task-access requirement. | Q03, Q13 |
| C45 | DEFERRED | — | Name uniqueness belongs to deferred create-track reference. | Q13 |
| C46 | DEFERRED | — | Starting task procedure deferred with Q12 initial-state gap. | Q12 |
| C47 | DEFERRED | — | Duplicate-start edge case is outside selected goal. | Q07 |
| C48 | INCLUDED | feature/feature-guide.md#when-a-task-closes-or-moves | Closed tasks must be reopened before a new track can be started; no existing-status edit promise. | Q11 |
| C49 | INCLUDED | how-to/how-to.md#steps; how-to/how-to.md#expected-result | Verified In Progress to Done transition. | None |
| C50 | INCLUDED | how-to/how-to.md#resume-work-on-the-track | Verified Done to In Progress transition. | None |
| C51 | DEFERRED | — | Stop not taught or advertised; Done restriction deferred with Stop procedure Q08. | Q08 |
| C52 | INCLUDED | feature/feature-guide.md#how-tracks-relate-to-tasks; how-to/how-to.md#expected-result; release-note/release-note.md#track-parallel-progress-on-a-single-task | Changing one track to Done leaves other tracks unchanged. | Q09 |
| C53 | DEFERRED | — | Counter update edge case deferred with Q02. | Q02 |
| C54 | DEFERRED | — | Off-state visibility reference deferred; drafts explicitly scoped to enabled projects and do not guide disabling. | Q01, Q06 |
| C55 | INCLUDED | feature/feature-guide.md#working-offline; how-to/how-to.md#working-offline | Only Start, Mark Done and Mark Pending; queue/reconcile accompanied by silent deletion-drop caveat. | Q04, Q05, Q09 |
| C56 | INCLUDED | feature/feature-guide.md#working-offline | Online-only management and capability changes, with no settings path or toggle/deletion outcome. | Q01, Q03, Q06 |
| C57 | INCLUDED | feature/feature-guide.md#working-offline; how-to/how-to.md#working-offline | Queued membership writes dropped silently if track deleted; no recreation. | Q05 |
| C58 | INCLUDED | feature/feature-guide.md#working-offline | Offline closure plus online deletion loses assignment at sync; reopening does not restore deleted track. | Q05 |
| C59 | BLOCKED | — | Unresolved Q02; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. | Q02 |
| C60 | BLOCKED | — | Unresolved Q03; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. | Q03 |
| C61 | BLOCKED | — | Unresolved Q04; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. | Q04 |
| C62 | BLOCKED | — | Unresolved Q05; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. | Q05 |
| C63 | BLOCKED | — | Unresolved Q06; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. | Q06 |
| C64 | BLOCKED | — | Unresolved Q07; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. | Q07 |
| C65 | BLOCKED | — | Unresolved Q08; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. | Q08 |
| C66 | BLOCKED | — | Unresolved Q09; no reader-facing assertion. Material publication blocker. | Q09 |
| C67 | BLOCKED | — | Unresolved Q10; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. | Q10 |
| C68 | BLOCKED | — | Unresolved Q11; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. | Q11 |
| C69 | BLOCKED | — | Unresolved Q12; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. | Q12 |
| C70 | BLOCKED | — | Unresolved Q13; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. | Q13 |
| C71 | BLOCKED | — | Unresolved Q14; no reader-facing assertion. Affected behavior withheld; independent bounded claims may proceed. | Q14 |

## Coverage review

- Missing or duplicated claim IDs: none; independently reconciled all 71 unique rows with HANDOVER and TRACEABILITY.json.
- Reader-facing passages without a supporting claim: none found in independent sentence-level source review.
- Compound-claim boundaries: C28 admits Mark Done only, not Stop; C41 admits member/task access for described status changes, not a full action reference; C55 includes all three named actions in feature and only the relevant two in how-to. Remaining clauses are safely deferred, not implied.
- High-risk omissions/blockers: Q01/C35 prevents a publication-ready feature guide because capability-off retention remains contradictory; no off/on outcome is asserted. Q09/C66 prevents a publication-ready release announcement. C60–C65/C67–C71 block only their affected unsupported details; no neighboring fact supplies an answer.
- Supported HIGH permission details C40/C42 are deferred with the management/bulk procedures, not silently broadened. C54 off-state pill visibility is omitted; all draft use is scoped to Tracks-enabled projects. No material warning for an admitted procedure has been removed.
- Reviewer result: PASS — independent source and destination review complete. Compound-claim admissions above preserve their explicit partial boundaries. REVIEW-READY; Q01 and Q09 remain publication blockers.
