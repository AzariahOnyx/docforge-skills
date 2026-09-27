# Quiet Hours — content scope and change plan

## Source and existing-content inventory

- Previous source: `demo/mock-prd.md`; revised current source: `demo/mock-prd-v2.md`.
- Previous output supplied: `output/quiet-hours/` and inspected. It includes three reader-facing drafts and review artifacts. Existing outputs are comparison targets; none is edited in place.
- Product assertions for this set use the revised PRD only.
- Audience and goals: understand the feature, pause/resume alerts in one supported procedure, scan the change.

## Scope decisions

All UPDATE actions below mean create revised counterparts in `output/quiet-hours-v2-live/`; preserve the previous files.

| Topic / goal | Action | Destination | Evidence | Open questions | Reason |
| --- | --- | --- | --- | --- | --- |
| Understand personal Quiet Hours behavior | UPDATE | `feature/feature-guide.md` (counterpart to prior guide) | C01–C09; revised Product context through Known gap | Q01–Q02 | Retain supported model, update option to 2 hours, distinguish manual and automatic resumption, preserve unknowns. |
| Pause alerts for a fixed period | UPDATE | `how-to/how-to.md` (counterpart to prior how-to) | C02–C08; revised UI/workflow and Permissions | None for 2-hour task | Update title, purpose, choice, expected result, and online prerequisite for Resume now. |
| Scan capability | UPDATE | `release-note/release-note.md` (counterpart to prior note) | C02–C08; revised Feature through Permissions | Q04 for release metadata | Change option to 2 hours; omit unsupplied release details. |
| Until tomorrow exact cutoff | DEFER | Feature guide expansion | C09; revised Known gap, line 22 | Q01 | Time and zone remain undefined. |
| Alert disposition and active-period changes | DEFER | Future user guidance if resolved | C10–C11; revised Known gap, line 23 | Q02–Q03 | Explicit unresolved behavior. |
| Prior fixed-duration article claims | RETIRE-CANDIDATE for review; no deletion | Prior how-to and prior feature/release docs in `output/quiet-hours/` | D02, D08 | None | Prior 1-hour directions are stale against revised 2-hour source; retire only after review. |
| Add release availability details | DEFER | Release note | C12; revised Release, line 27 | Q04 | Date/platform/rollout absent. |

## Information architecture

- Keep the same conceptual guide, one-task how-to, and concise release-note roles as the baseline. Link feature guide to `../how-to/how-to.md` within this new output set.
- No production parent or existing help destination is established by the sources. No additional article or diagram is needed for the supported linear task.
- Q01–Q04 limit precise timing, alert backlog, period-editing, and availability guidance.

## Delivery boundary

Produce all three drafts in the fresh output tree. Update mode records changes to prior documents but makes no edits or deletions to them. Drafts can be reviewed as a practice set; publication requires resolution or explicit acceptance of Q01–Q04 and the stale prior set's retirement decision.
