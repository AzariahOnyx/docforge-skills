# Live round: use the workflow

1. Practice with `demo/mock-prd.md`, or put a new PRD and supporting artifacts in `input/` under distinct filenames. Do not overwrite the Tracks source.
2. In the repository root, launch Codex and request: "Use $generate-docs on demo/mock-prd.md and write to output/quiet-hours/. Review the source first and preserve unknowns." For a different PRD, change both paths.
3. Inspect HANDOVER.md and clarifications-and-assumptions.md first. Check that each material claim cites the new source and both sides of any contradiction appear.
4. Inspect the three audience-specific documents and QA-REPORT.md. Explain any publication blockers.
5. For a live edit, ask Codex to change one rule in the relevant SKILL.md, review the Git diff, and rerun the affected stage or the full workflow. Compare outputs and explain the difference.
6. For the practice PRD, verify the workflow flags the undefined meaning of “Until tomorrow” and never guesses a time zone or time. For an interview PRD, commit its source and outputs only when permitted.

If the CLI session does not list a newly added skill, refer to its repository path explicitly in the prompt. If PDF text extraction misses graphics or tables, inspect those pages visually and record the coverage limit.
