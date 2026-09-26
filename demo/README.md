# Live-round rehearsal

This is a 45-minute demonstration path. The fictional [Quiet Hours PRD](mock-prd.md) is unrelated to Tasket.

1. In the repository root, open Codex CLI. For the rehearsal, enter:

   ```text
   Read .agents/skills/generate-docs/SKILL.md and run its Analyzer → Drafter → Proofreader workflow on demo/mock-prd.md. Write to output/quiet-hours/. Use only that mock PRD as product evidence. Do not change Tracks files. Report the undefined “Until tomorrow” time and the structural checker result.
   ```

2. Open `output/quiet-hours/analysis/`. Check source citations, classifications, the question register, `CONTENT-PLAN.md`, and `COVERAGE.md`. Every claim must have a destination or an explicit reason for omission. The PRD leaves “Until tomorrow” without a time zone or time of day; the workflow must not guess either.
3. Open the three type folders and `qa/QA-REPORT.md`. Check one conceptual guide, one supported how-to, one short release note, and a source-first readiness decision.
4. When asked to change a rule live, edit the relevant `.agents/skills/<stage>/SKILL.md`, show `git diff`, and rerun the affected stage. Example: require a separate `## Expected result` heading in every how-to, then compare the resulting how-to. This rule now exists in the Drafter skill as the recorded practice change.
5. For the interview's new PRD, use a new `input/` filename and `output/<new-slug>/`. Re-run the master skill, review the new source and outputs, and run `python3 scripts/check_outputs.py output/<new-slug>`. Commit only when the interview permits it.

If the current Codex session does not show a new skill under `/skills`, reference the SKILL.md path explicitly or restart Codex. For a PDF with tables or graphics, inspect those pages visually. A structural PASS does not replace source review.

## Revised-source rehearsal

The fictional [revision](mock-prd-v2.md) changes the fixed option from **1 hour** to **2 hours** and makes **Resume now** online-only; it still leaves the “Until tomorrow” boundary undefined. A [reviewed revised output](../output/quiet-hours-v2/analysis/CHANGE-IMPACT.md) demonstrates the source comparison and updated docs. To rerun it yourself without replacing that example, use this prompt in Codex:

```text
Read .agents/skills/generate-docs/SKILL.md. Use update mode with previous source demo/mock-prd.md, revised source demo/mock-prd-v2.md, and previous output output/quiet-hours/. Write a fresh set to output/quiet-hours-v2-live/. Compare the sources first in analysis/CHANGE-IMPACT.md, then run Analyzer → Drafter → Proofreader. Keep output/quiet-hours/ and output/quiet-hours-v2/ intact. Check that the new how-to says 2 hours, Resume now is online-only, and the undefined Until tomorrow boundary remains UNKNOWN. Run the structural checker and report the QA result.
```

Compare the source-change table to the two PRDs and [revision acceptance notes](revision-acceptance.md), inspect the updated passages and removed 1-hour claims, then run `python3 scripts/check_outputs.py output/quiet-hours-v2-live`. The checker verifies structure and coverage; the Proofreader validates semantic impact.
