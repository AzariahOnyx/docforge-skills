# Live-round rehearsal

This is a 45-minute demonstration path. The fictional [Quiet Hours PRD](mock-prd.md) is unrelated to Tasket.

1. In the repository root, open Codex CLI. For the rehearsal, enter:

   ```text
   Read .agents/skills/generate-docs/SKILL.md and run its Analyzer → Drafter → Proofreader workflow on demo/mock-prd.md. Write to output/quiet-hours/. Use only that mock PRD as product evidence. Do not change Tracks files. Report the undefined “Until tomorrow” time and the structural checker result.
   ```

2. Open `output/quiet-hours/analysis/`. Check source citations, classifications, the question register, and `CONTENT-PLAN.md`. The PRD leaves “Until tomorrow” without a time zone or time of day; the workflow must not guess either.
3. Open the three type folders and `qa/QA-REPORT.md`. Check one conceptual guide, one supported how-to, one short release note, and a source-first readiness decision.
4. When asked to change a rule live, edit the relevant `.agents/skills/<stage>/SKILL.md`, show `git diff`, and rerun the affected stage. Example: require a separate `## Expected result` heading in every how-to, then compare the resulting how-to. This rule now exists in the Drafter skill as the recorded practice change.
5. For the interview's new PRD, use a new `input/` filename and `output/<new-slug>/`. Re-run the master skill, review the new source and outputs, and run `python3 scripts/check_outputs.py output/<new-slug>`. Commit only when the interview permits it.

If the current Codex session does not show a new skill under `/skills`, reference the SKILL.md path explicitly or restart Codex. For a PDF with tables or graphics, inspect those pages visually. A structural PASS does not replace source review.
