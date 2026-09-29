# Terminology and UI-label ledger

Evidence source throughout: `input/Technical Writer - Case Study.pdf`. FACT labels mean source wording, not implementation verification.

## Canonical terms
| Concept | Canonical term / exact UI label | Type | Source | Aliases or conflicts | Draft rule |
| --- | --- | --- | --- | --- | --- |
| Platform | Tasket | FACT product name | p2, What Tasket is | Lowercase tasket also appears | Use Tasket for platform; do not introduce tasket as a distinct entity. |
| Work item | task | FACT domain term | p2, Tasks; pp3–6 | Each tasket on p2 (Q10) | Use repeated task wording without claiming ambiguous text defines a second object. |
| Feature | Tracks | FACT feature/tab/pill label | p2, Where things appear; p4, The Tracks pill | track = individual project-scoped workstream | Capitalize feature and exact UI label; lowercase an individual track. |
| Container | team; project | FACT domain terms | p2, What Tasket is; p3, Scope | None | Tracks belong to a project; task belongs to exactly one project. |
| Task lifecycle | Open; Completed; Discarded | FACT status labels | p2, Task status | Completed and Discarded called closed and terminal | Use closed collectively; omit ambiguous terminal (Q14). |
| Per-track status | Not started; In Progress; Done | FACT exact status labels | p3, Scope; p4, The Tracks pill | Done differs from Completed | Preserve case; do not conflate Done with whole-task completion. |
| Start participation | Start | FACT action label | p4, The Tracks pill; p6, US-2 | Initial In Progress outcome is C69 INFERENCE | Name control without asserting inferred initial status. |
| Complete track work | Mark Done | FACT action label | p4, The Tracks pill; p6, US-3 | None | Exact case; changes In Progress to Done on that track. |
| Resume track work | Mark Pending | FACT action label | p3, Capabilities; p4, The Tracks pill; p6, US-3 | Pending is not a separately listed status | Control is Mark Pending; result is In Progress. |
| Stop participation | Stop | FACT action label | p4, Actions on a task / The Tracks pill; p6, US-3 | Result/history unspecified Q08 | Do not invent outcome; Done tasks cannot be stopped. |
| Multi-select | Select | FACT action label | p4, Actions on a task in a column | Full target flow unspecified Q07 | Do not invent selection menus/dialogs. |
| Add a track | Add track | FACT action label | p4, Managing tracks from the board | CTA is specification language | Use Add track; no invented dialog fields. |
| Manage tracks | Rename; Move track; Delete | FACT action labels | p4, Managing tracks from the board | Moving track differs from moving task across projects | Preserve distinct actions; deletion authority unresolved Q03. |
| Task status access | Tracks pill; Tracks board | FACT source terms | pp3–4, The Tracks board / The Tracks pill | Pill is UI shape description | First explain task detail Tracks control; avoid unsupported icon or menu description. |
| Role/access | member; admin; guest | FACT roles | p2, What Tasket is; p5, Permissions | Admin capitalization varies | Lowercase role prose; preserve task/project access boundaries. |
| Entry point | My Work / Work | UNKNOWN exact label | p2, Where things appear; p4, The Tracks pill | Conflicting names Q10 | Neither route is needed; use open task details. Do not silently choose one label. |
| Task activity | Updates | FACT label | p2, Where things appear; p4, The Tracks pill | taskets in p2 description | Omit navigation route when unnecessary. |
| Attached collaboration content | Studio documents; Friday chat | FACT names | p2, Tasks | docs/chats generic p4 | Background only, not essential Tracks content. |

## Conflicts and unresolved labels
Q10 retains My Work versus Work and task versus tasket wording; intended UI naming is UNKNOWN, not proof of two distinct interfaces. Q14 retains terminal versus explicit reopening ambiguity. Both source locations remain visible above. Q02 leaves the board X out of Y counter undefined; the pill's Done-out-of-available definition (p4) cannot be transferred to it. Q12 keeps the Start initial-state derivation outside factual UI promises.

## Final terminology audit
Analyzer baseline PASS: exact labels checked against source pages; unresolved labels recorded and excluded from routes. Independent reader-draft terminology/UI audit: PASS. Tracks, Start, Mark Done and Mark Pending match the original PDF labels; state labels retain their case. Done is distinct from Completed, and Mark Pending returns to In Progress rather than an invented Pending state. Neither disputed navigation label is used. No invented UI label or control path appears.
