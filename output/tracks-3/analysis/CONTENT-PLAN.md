# Tracks — content scope and change plan

## Source and existing-content inventory
Authoritative source: `input/Technical Writer - Case Study.pdf`, assignment pp1–2 and working-draft PRD pp2–6. All pages and both tables reviewed. No existing reader documentation supplied in input; existence elsewhere is UNKNOWN. No UPDATE is authorized or evidenced. Prior run outputs are excluded as drafting input. Assignment p1 requests a first-use feature document, specific-task how-to, and change-focused release note.

## Scope decisions
| Topic / reader goal | Action | Destination | Evidence | Open questions | Relevance and reason |
| --- | --- | --- | --- | --- | --- |
| Understand parallel work on one task | CREATE | feature/feature-guide.md | C01–C02, C08–C15, C17 | Q12 | ESSENTIAL: build model before controls; omit inferred initial state. |
| Find and interpret track status | CREATE | feature/feature-guide.md | C07, C14–C15, C25–C30, C54 | Q01, Q02, Q06, Q10, Q13 | ESSENTIAL: distinguish board from pill; no board-counter meaning or disputed navigation. |
| Understand independent state actions | CREATE | feature/feature-guide.md | C09, C27–C29, C48–C52 | Q08, Q11, Q12 | ESSENTIAL: track Done differs from task Completed; avoid Stop outcomes. |
| Know access and material consequences | CREATE | feature/feature-guide.md | C31–C44, C48, C55–C58 | Q01, Q03–Q06, Q13 | ESSENTIAL: permissions, irreversible deletion, project moves, retention and offline loss survive compression. |
| Update one track without changing others | CREATE | how-to/how-to.md | C24–C29, C41, C49–C52 | Q11 | ESSENTIAL: open, accessible task already In Progress; Mark Done, verify inline Done, optionally Mark Pending. |
| Learn what Tracks enables | CREATE | release-note/release-note.md | C08, C26, C52, C55, C57 | Q09, Q05 | ESSENTIAL: select up to three user impacts; undated draft, no launch or previous-state invention. |
| Track management details | DEFER | Proposed future reference; no file | C18–C20, C23, C34, C40, C45 | Q03, Q07 | REFERENCE CANDIDATE: controls supported but full create/bulk procedures incomplete; no extra article needed. |
| Disable/re-enable, deletion procedure, sync recovery | DEFER | No reader procedure | C35, C60–C65 | Q01, Q03–Q08 | EDGE CASE except material consequences retained above; unsupported or contradictory sequences. |
| Existing documentation updates | DEFER | Proposed inventory before any UPDATE | Existing content UNKNOWN | No supplied document | Cannot claim a confirmed update target. |

## Information architecture
These three new documents form the complete reader set. Feature guide owns conceptual explanation and lifecycle cautions; how-to links to it for context; release note may link to feature guide. Links must resolve to actual newly created files. Parent documentation placement is proposed only. No diagram: the compact relationship explanation is sufficient, and a Start arrow would promote C69 inference. Publication remains blocked by Q01 and release expectations Q09; drafting can proceed within bounded claims.

## Essential newcomer concepts
1. One task, several project-scoped tracks, independent status per track (C02, C08–C13).
2. Track Done and whole-task closure are distinct (C05, C09, C49–C52).
3. Board columns show open tasks; the pill lists project tracks and inline statuses (C14–C15, C25–C30).
4. Access requirements and closed-task restrictions (C41–C44, C48).
5. Closure preserves state; deletion and project moves remove track information (C31–C36), qualified so capability-off ambiguity does not become a restoration assurance.
6. Named offline actions queue work; deleted tracks can silently lose queued writes (C55–C58).

Task participant counts and attached-content types (C03–C04) are REFERENCE CANDIDATE, not essential Tracks teaching. Column repositioning and rename invariants (C20, C34) are USEFUL if space permits. Empty-section counter behavior and duplicate-start edge cases (C47, C53) are EDGE CASE and can remain in analysis.

## How-to candidates ranked
| Rank / candidate | Start → action → observable result | User value / substance / consequence | Evidence completeness | Audience and assignment fit / decision |
| --- | --- | --- | --- | --- |
| 1. Mark one track Done, optionally resume | Open accessible task already In Progress, Tracks enabled → open task and pill, Mark Done → inline Done; Mark Pending → In Progress (C24–C29, C41, C49–C52) | Completes a discipline's work independently; narrow but real state change with reversible continuation | Complete for selected bounded starting state | Fits a specific task in hand. SELECT. Source assignment requires specific task, not a long or substantial workflow. |
| 2. Start an open task across tracks | Open accessible task, track exists → Start → column placement (C27, C46–C47); initial status inferred C69 | More setup value, state-changing | Initial-state gap Q12; bulk target dialogs Q07 | Defer procedure until exact result and bulk route confirmed. |
| 3. Create a track and organize board | Enabled project → Add track/name/Move track → column order (C18–C20, C40, C45) | Team-level organization, more substantive | Creation dialogs/confirmation incomplete Q07 | Defer full tutorial; may describe management conceptually. |
| 4. Inspect task status | Accessible task → open pill → inline statuses (C25–C26) | Informational, no state change | Complete with access boundaries | Good feature-guide concept but lower-value how-to than candidate 1. |
| 5. Delete a track | Existing track → Delete → irreversible removal (C19, C33) | Destructive, irreversible, data loss | Permission/confirmation missing Q03/Q06 | Do not select; retain consequence warning in feature guide. |

## Material consequences and review intensity
C31–C32 retention, C33 irreversible deletion on open and closed tasks, C35 contradictory capability retention, C36 cross-project clearing even for same-name targets, C38–C44 permissions, C48 reopening before new starts, C55–C58 offline and silent loss require source recheck. State actions C49–C50 are state-changing and reversible; pill/board viewing is informational. No source establishes billing, migration or security implementation. Do not invent those topics.

## Release-note priorities
1. **Parallel workstreams with independent progress** (C08, C52): readers can track several disciplines on one task; no claim that prior versions duplicated tasks.
2. **All project-track statuses in task details** (C25–C26): readers can inspect the task's status across tracks in one view; no invented prior UI comparison.
3. **Named offline actions** (C55, C57): Start, Mark Done, Mark Pending queue until reconnection; select only with the deleted-track silent-drop caveat. Distinct useful benefit but secondary to model and visibility.
These are source-supported feature capabilities, not verified release availability. Q09 blocks publication metadata. Omit priority 3 if caveat cannot fit without obscuring the first two.

## Delivery boundary
Feature guide excludes exhaustive background task anatomy, unspecified counter semantics and unsupported setup/deletion/Stop procedures. How-to excludes creation, bulk start, task closure, closed-task edits and unrelated management instructions. Release note excludes full procedures, exhaustive permissions, dates, plan availability and speculative previous behavior. No fourth reader-facing article. All three requested drafts may proceed; unanswered questions remain in the review packet and must not be presented as resolved product behavior.
