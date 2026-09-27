# Quiet Hours — source change impact

## Baseline

- Previous source: `demo/mock-prd.md`, complete file, lines 1–23.
- Revised source: `demo/mock-prd-v2.md`, complete file, lines 1–27; current product evidence for this run.
- Previous output: `output/quiet-hours/`, inspected in full. It contains feature guide, how-to, release note, handover, clarification register, content plan, coverage, and QA report.
- New output: `output/quiet-hours-v2-live/`.
- Comparison limits: both sources are plain Markdown and fully readable. The previous output is a documentation baseline, not product evidence. Only the two source PRDs establish product requirements.

## Source changes

| Change ID | Previous evidence | Revised evidence | Type | Affected current claims / questions | Reader-facing impact |
| --- | --- | --- | --- | --- | --- |
| D01 | `demo/mock-prd.md`, Product context, line 6: alerts for assigned items | `demo/mock-prd-v2.md`, Product context, line 6: items assigned to them | CHANGED wording | C01 | Preserve the same meaning; use revised phrasing. |
| D02 | Previous UI and workflow, line 12: **1 hour** or **Until tomorrow** | Revised UI and workflow, line 12: **2 hours** or **Until tomorrow** | CHANGED | C03; stale C03 in prior handover | UPDATE all fixed-duration mentions; remove stale one-hour how-to and title. |
| D03 | Previous UI and workflow, line 14: pausing online-only; offline Resume now unspecified (prior Q03) | Revised UI and workflow, line 14: pausing online-only and Resume now also requires online connection | RESOLVED in part | C05, C07; Q03 resolved part; Q04 remains for mid-pause changes | State online prerequisite for both pausing and manual resume. Do not extend it to automatic resume. |
| D04 | Previous Known gap, lines 19–20: tomorrow time/zone undefined | Revised Known gap, lines 22–23: still undefined | UNCHANGED / unresolved | C09, Q01 | Keep UNKNOWN; no time or zone in docs. |
| D05 | Previous source did not specify alert handling during pause (Feature/UI workflow, lines 9–14) | Revised Known gap, line 23: still says later delivery is unspecified | CONFIRMED UNKNOWN | C10, Q02 | Keep alert backlog behavior out of product claims. |
| D06 | Previous source did not mention changing duration mid-pause | Revised Known gap, line 23: explicitly says this is unspecified | ADDED clarification of UNKNOWN | C11, Q03 | Ask whether active periods can be changed; do not document such a workflow. |
| D07 | Previous Release, line 23: date/platform/rollout absent | Revised Release, line 27: same absence | UNCHANGED / unresolved | C12, Q04 | Continue omitting release metadata. |
| D08 | Previous output's how-to and release note specify 1 hour | Current source now specifies 2 hours | STALE previous-output content | D02; affected prior paths below | Use 2 hours in every new fixed-duration reference. Prior articles are preserved; consider retirement only after review. |
| D09 | Previous handover says offline Resume now unspecified and groups that with mid-pause changes | Revised source resolves manual-resume connection but leaves mid-pause editing unknown | RESOLVED in part / changed | D03–D06; prior Q03 | Split the old compound question: close offline manual resume; keep active-pause changes open. |

## Document actions

| Existing destination | Action | Evidence | Reason and review gate |
| --- | --- | --- | --- |
| `output/quiet-hours/feature-guide.md` | UPDATE in new set: `feature/feature-guide.md` | D02–D06; C03, C05, C07, C09–C11 | Retain supported scope; replace option with 2 hours, state manual resume online requirement, preserve gaps. Prior file remains untouched. |
| `output/quiet-hours/how-to.md` | UPDATE in new set: `how-to/how-to.md` | D02–D03; C03, C05, C07 | Change title, purpose, choice, and expected result to 2 hours; require connection for Resume now. Old one-hour article is stale against revised source. |
| `output/quiet-hours/release-note.md` | UPDATE in new set: `release-note/release-note.md` | D02, D07; C03, C12 | Update option to 2 hours; omit unsupplied availability metadata. |
| Prior handover and clarification register | UPDATE in new set: `analysis/HANDOVER.md`, `analysis/clarifications-and-assumptions.md` | D03–D07 | Reassess resolved offline-resume question and split remaining gap; do not reuse old handover as current truth. |
| Prior outputs as files | RETIRE-CANDIDATE for review only | D08–D09 | Prior output remains intact and may be stale; no deletion or retirement is performed. |

## Reconciliation

- Claims still supported: personal in-app-only scope, assigned-item context, UI flow, automatic expiry resume, online-only pausing, self-service permissions, and no release metadata (revised source, lines 6–27).
- Stale: fixed **1 hour** selection across previous drafts; previous offline manual-resume uncertainty is superseded by the explicit online requirement.
- Newly explicit: Resume now also requires online connectivity; mid-pause period changes are unspecified.
- Unresolved: Until tomorrow boundary, alert delivery during pause, active-pause modification, release details. No contradictions found.
- Required product decisions: Q01–Q04 in the current handover and clarification register.
- Verification: source-first proofreading completed with no source-fidelity failures; publication warnings remain for Q01–Q04. `python3 scripts/check_outputs.py output/quiet-hours-v2-live` passed with 8/8 files, 0 errors, 0 warnings.
