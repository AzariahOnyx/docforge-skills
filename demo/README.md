# Live round: use the workflow

1. Put the new PRD and supporting artifacts in input/ (use a distinct filename). Do not overwrite the Tracks source.
2. In the repository root, launch Codex and request: "Use $generate-docs on input/<new-prd> and write to output/<new-feature>. Review the source first and preserve unknowns."
3. Inspect HANDOVER.md and clarifications-and-assumptions.md first. Check that each material claim cites the new source and both sides of any contradiction appear.
4. Inspect the three audience-specific documents and QA-REPORT.md. Explain any publication blockers.
5. For a live edit, ask Codex to change one rule in the relevant SKILL.md, review the Git diff, and rerun the affected stage or the full workflow. Compare outputs and explain the difference.
6. Commit the PRD and outputs only when the interviewer permits keeping the live-round source.

If the CLI session does not list a newly added skill, refer to its repository path explicitly in the prompt. If PDF text extraction misses graphics or tables, inspect those pages visually and record the coverage limit.
