# Tracks — content plan

> Review artifact. Source citations below refer to `input/Technical Writer - Case Study.pdf` (S1). Claim IDs refer to `HANDOVER.md`.

## Source and existing-content inventory

S1 is the only file in `input/`. All six pages, including both tables, were reviewed afresh. No existing product documentation was supplied; its existence is **UNKNOWN** (C40/Q14). No prior output was consulted. The three requested deliverables and their audiences come from S1 p. 1, Part 2 (C39). This is the same-source fresh run, so a revised-source CHANGE-IMPACT comparison is inapplicable.

## Scope decisions

| Topic / reader goal | Action | Destination or candidate | Evidence | Open questions | Reason |
| --- | --- | --- | --- | --- | --- |
| Understand work across parallel tracks | CREATE | `feature/feature-guide.md` | C02, C04, C06–C08, C12–C20, C22–C34; S1 pp. 2–6 | Q01–Q12 | Newcomer overview covering model, states, board/pill, permissions, management consequences and offline limits; no extra articles |
| Mark work Done on one track and return it to In Progress when needed | CREATE | `how-to/how-to.md` | C08, C12, C24, C29–C30, C32; S1 p. 3 Capabilities/Layout, p. 4 column actions, p. 5 permissions, p. 6 US-3 | Q06/Q07 avoided by scope | Consequential state change with explicit starting state, control and result, plus supported correction |
| Notice parallel progress, bulk starts and task-wide visibility | CREATE | `release-note/release-note.md` | C06, C13, C15–C17, C29; S1 pp. 3–4, p. 6 US-3 | Q13 | Three distinct high-value capabilities; no unsupported previous-state baseline or launch metadata |
| Explain disabling/re-enabling data retention | DEFER | Proposed section within feature guide; no standalone article | C21; S1 p. 3 Capabilities versus p. 5 lifecycle continuation | Q01 | Direct conflict with material data-loss implications; both outcomes omitted from reader-facing text, overview publication blocked |
| Explain board counter formula | DEFER | Proposed feature guide detail | C09; S1 p. 3 Layout and p. 6 US-3 | Q02 | X and Y undefined; pill formula cannot be substituted |
| Detailed create/delete/bulk-start or Start/Stop procedures | DEFER | Future task candidates only | C10–C13, C19, C27–C28, C35–C36; S1 pp. 3–6 | Q03/Q04/Q07/Q10 | Missing verified controls, permissions or outcomes; no additional reader-facing article justified now |
| Troubleshoot sync and validation | DEFER | Future candidate after evidence supplied | C26, C32–C37; S1 pp. 5–6 | Q08/Q11/Q12 | Keep known limits in overview; do not invent recovery procedures |
| Update existing project/task/permissions/offline docs | DEFER | Proposed UPDATE candidates only; paths unknown | C02, C18–C25, C32–C34, C40 | Q14 | Actual existing docs must be supplied and inspected before any confirmed UPDATE |

## How-to candidate comparison

| Candidate | Supported starting point / action / outcome | Decision |
| --- | --- | --- |
| Mark a track task Done, with Mark Pending to resume | Tracks tab, an open task in the track’s In Progress section; Mark Done; Done on that track. Done section offers Mark Pending, explicitly returning it to In Progress. Other tracks unaffected. C08/C12/C29, S1 pp. 3–4 and p. 6 US-3. | **Selected.** Material state-changing work, clear verification and explicit reversal. Prerequisites: enabled Tracks, project/task access, existing open task In Progress. |
| Start or Stop a task | Pill and actions verified, but initial Start state and exact Stop result are inferred, C35/Q07. | Defer outcome-based procedure pending clarification. |
| Start selected tasks across tracks | Select and bulk capability verified, C13/C28, but target-selection controls and sequence absent, Q10. | Defer complete procedure. |
| Delete a track | Delete and irreversible result verified, C11/C19, but authorization and safeguards unspecified, Q03/Q04. | Explain consequences in overview; do not select destructive procedure with these gaps. |
| Inspect the Tracks pill | Task details → Tracks pill → every project track and status are explicit, C14–C17. | Valid view-only alternative, but weaker than the equally supported consequential Done/Pending task. Cover in overview. |

## Release-note priorities

1. Track progress independently across parallel workstreams, including Mark Done without affecting other tracks (C06/C29).
2. Start selected tasks across other tracks in one action (C13).
3. Inspect every project track’s status for a task through the Tracks pill (C15–C17).

Describe these capabilities as the feature change requested by the assignment. Do not claim they replace particular previous behavior. Release date, version, availability and rollout remain unknown (Q13).

## Information architecture and diagram decision

Proposed placement only: a project/task documentation area; no verified existing parent page. Cross-link only the three newly created drafts using their actual relative paths. Do not link to hypothetical existing documentation.

A small optional state diagram is supported: `In Progress -- Mark Done --> Done -- Mark Pending --> In Progress` for one track (C29). Explain nearby that other tracks are unaffected and task status is separate. This clarifies the central state distinction; omit inferred Start/Stop arrows and all disputed disable/re-enable transitions. Text alone is acceptable if it communicates the same distinction clearly.

## Delivery boundary

All three assignment drafts can proceed with editorial omissions documented in Q01–Q14. The feature guide is blocked for publication by Q01: silently excluding the unresolved disable behavior would conceal a material data-loss risk. The how-to avoids that operation and the unknown closed-task actions. The release note requires confirmed release metadata if publication needs it; it must not imply rollout has occurred. This is evidence-based drafting from a working PRD, not implementation or release verification. Independent Proofreader review and a C01–C40 coverage ledger are required after drafting.
