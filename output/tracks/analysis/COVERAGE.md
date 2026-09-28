# Tracks — source-to-document coverage

## Claim coverage

Each material claim in `HANDOVER.md` is accounted for once. Reader-facing inclusion is based on both source support and audience relevance; supported reference and edge-case detail may remain in analysis when it does not serve the selected document goal.

| Claim ID | Disposition | Destination | Rationale | Related question |
| --- | --- | --- | --- | --- |
| C01 | CONTEXT | — | General organisation collaboration model is not required to understand Tracks. | — |
| C02 | INCLUDED | feature/feature-guide.md | Establishes project scope and task ownership. | — |
| C03 | CONTEXT | — | General task properties are unrelated to the reader goals. | Q09 |
| C04 | INCLUDED | feature/feature-guide.md | Separates task lifecycle from track progress. | — |
| C05 | INCLUDED | feature/feature-guide.md | Uses the verified Tracks tab entry point; unrelated navigation is omitted. | Q09 |
| C06 | INCLUDED | feature/feature-guide.md; release-note/release-note.md | Core parallel-work and independent-progress model. | — |
| C07 | INCLUDED | feature/feature-guide.md | Project scope, multiple tracks and per-track states. | — |
| C08 | INCLUDED | feature/feature-guide.md; how-to/how-to.md | Board columns, sections and open-task behavior needed for orientation and procedure. | — |
| C09 | BLOCKED | — | Board counter formula is undefined. | Q02 |
| C10 | DEFERRED | — | Detailed track creation is supported only at a high level and is not needed for the newcomer mental model. | Q10 |
| C11 | INCLUDED | feature/feature-guide.md | Rename/move/delete concepts are included only where their effects matter. | Q03 |
| C12 | INCLUDED | feature/feature-guide.md; how-to/how-to.md | Mark Done/Mark Pending and Select support core behavior and selected task; other action detail is not enumerated. | — |
| C13 | INCLUDED | feature/feature-guide.md; release-note/release-note.md | Multi-select start is a distinguishing supported capability. | Q10 |
| C14 | INCLUDED | feature/feature-guide.md | Task entry point is summarized without unrelated task-detail inventory. | — |
| C15 | INCLUDED | feature/feature-guide.md; release-note/release-note.md | Tracks pill provides the cross-track view. | — |
| C16 | DEFERRED | — | Full state-specific pill action matrix is reference detail; closed-task action availability is unresolved. | Q06 |
| C17 | INCLUDED | feature/feature-guide.md | Defined pill count is included without borrowing the unknown board-counter formula. | — |
| C18 | INCLUDED | feature/feature-guide.md | Closing/reopening behavior materially affects visibility and retained progress. | — |
| C19 | INCLUDED | feature/feature-guide.md | Irreversible deletion consequence is material and prominently warned. | Q03/Q04 |
| C20 | INCLUDED | feature/feature-guide.md | Rename and move effects help distinguish safe management actions. | — |
| C21 | BLOCKED | — | Conflicting disable outcomes remain only in analysis; publication of the guide remains blocked until resolved. | Q01 |
| C22 | INCLUDED | feature/feature-guide.md | Cross-project moves clear assignments; material lifecycle consequence. | — |
| C23 | INCLUDED | feature/feature-guide.md | Enable/admin distinction is concise access context; disable outcome remains blocked separately. | Q05 |
| C24 | INCLUDED | feature/feature-guide.md; how-to/how-to.md | Project/task access supports access summary and prerequisites. | — |
| C25 | INCLUDED | feature/feature-guide.md | Guest parity is summarized with project-access qualification. | Q05 |
| C26 | INCLUDED | feature/feature-guide.md | Unique track names are a useful management constraint. | Q11 |
| C27 | DEFERRED | — | New-track start edge cases are not needed in the primary newcomer flow and Start outcome remains partly unresolved. | Q07 |
| C28 | INCLUDED | feature/feature-guide.md | Existing placement is preserved for multi-select start. | — |
| C29 | INCLUDED | feature/feature-guide.md; how-to/how-to.md; release-note/release-note.md | Verified Done/Pending transition is central to all three reader goals. | — |
| C30 | INCLUDED | how-to/how-to.md | Verified empty-section/counter update is used as observable result; Stop restriction is omitted as unrelated. | — |
| C31 | CONTEXT | — | Closed-task retained status is covered through lifecycle behavior; disabled-pill detail is omitted because disable behavior is disputed elsewhere. | Q01/Q06 |
| C32 | INCLUDED | feature/feature-guide.md | Explicit offline actions and queued reconciliation are important operating limits. | Q08 |
| C33 | INCLUDED | feature/feature-guide.md | Online-only management constraint is important operating context. | — |
| C34 | INCLUDED | feature/feature-guide.md | Deleted-track queued-write loss is included; the more specific close-offline variant remains analysis detail. | Q12 |
| C35 | DEFERRED | — | Start/Stop outcomes are inferred and not asserted. | Q07 |
| C36 | BLOCKED | — | Delete authorization, safeguards and validation are unspecified. | Q03/Q04/Q11 |
| C37 | BLOCKED | — | Closed-task actions and unspecified offline/conflict behavior remain unresolved. | Q06/Q08/Q12 |
| C38 | BLOCKED | — | Release date, rollout, platform, version and previous-state baseline are absent. | Q13 |
| C39 | CONTEXT | — | Assignment requirements govern the deliverable set. | — |
| C40 | CONTEXT | — | No existing documentation was supplied, so confirmed UPDATE targets cannot be named. | Q14 |

## Coverage review

All C01–C40 are accounted for. The revised reader-facing set intentionally prioritizes reader goals over maximum claim inclusion while retaining material destructive, lifecycle, access and offline consequences. Q01 remains a publication blocker because the supplied source gives incompatible outcomes for disabling Tracks. The selected how-to is the strongest fully supported state-changing procedure but is narrower than an ideal substantial assignment task; broader candidates require unsupported controls or outcomes.
