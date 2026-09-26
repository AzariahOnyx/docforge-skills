# Quiet Hours — revised-source change impact

## Baseline

- Previous source: `demo/mock-prd.md`, all sections.
- Revised source: `demo/mock-prd-v2.md`, all sections.
- Previous output: `output/quiet-hours/` (preserved).
- New output: `output/quiet-hours-v2/`.
- Comparison limits: neither version has a product build or existing Pulseboard help pages.

## Source changes

| Change ID | Previous evidence | Revised evidence | Type | Affected claims / questions | Reader-facing impact |
| --- | --- | --- | --- | --- | --- |
| D01 | Previous UI and workflow says 1 hour | Revised UI and workflow says 2 hours | CHANGED | C03, Q01 | Feature option, how-to title/actions/outcome, release note; remove stale 1-hour statements. |
| D02 | Previous UI and workflow specifies online pausing but leaves offline Resume now unknown | Revised UI and workflow explicitly says Resume now requires online access | RESOLVED | C10, C12, Q03 | State online requirement near Resume now; narrow Q03 to mid-pause edits. |
| D03 | Previous Known gap leaves Until tomorrow time/zone undefined | Revised Known gap still leaves both undefined | UNCHANGED | C08, Q01 | Continue omitting a specific end time and time zone. |
| D04 | Neither version defines alert backlog, mid-pause changes, date, platforms, or rollout | Revised Known gap and Release preserve those omissions | UNCHANGED | C09-C11, Q02-Q04 | Keep blocked passages and publication limitations; Q03 is only partly resolved. |

## Document actions

| Existing destination | Action | Evidence | Reason and review gate |
| --- | --- | --- | --- |
| `feature/feature-guide.md` | UPDATE | D01-D02, C03/C12 | Replace fixed option and add online Resume now rule; verify against revised source. |
| `how-to/how-to.md` | UPDATE | D01-D02, C03/C12 | Retitle and choose 2 hours; condition early Resume now on connection. |
| `release-note/release-note.md` | UPDATE | D01-D02, C03/C12 | Reflect changed option and connection requirement; no release metadata. |
| `analysis/clarifications-and-assumptions.md` | UPDATE | D02-D04, Q01-Q04 | Resolve only offline Resume now question; preserve others. |
| Existing Pulseboard help, if supplied later | DEFER | Content plan | No existing help pages supplied; no target invented. |

## Reconciliation

- Still supported: C01-C02, C04-C09, C11, with evidence in revised Product context through Release. C10 now means only mid-pause changes.
- Stale: previous 1-hour option and the statement that offline Resume now is unknown. They do not appear in revised reader-facing drafts.
- New fact: C12, online-only Resume now. No new source contradiction found.
- Product decisions: Q01, Q02, remaining Q03, and Q04.
- Verification: source-first review recorded in `../qa/QA-REPORT.md`; structural checker result recorded there.
