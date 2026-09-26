---
name: generate-docs
description: Run the reusable PRD-to-documentation workflow to produce a clarification register, feature guide, task how-to, release note, and QA report. Use for a new PRD, supporting artifacts, or a live-round rerun after source or skill changes.
---

# Generate docs

Accept source path(s) and an output directory. Default to input/ and output/<feature-slug>/ only when unambiguous; otherwise ask for the missing path. Never use an old handover for a different source.

1. Read AGENTS.md and the source artifacts. Read .agents/skills/analyzer/SKILL.md and templates/handover.md. Run the Analyzer first and save HANDOVER.md and clarifications-and-assumptions.md. Check full source coverage and make contradictions traceable to both passages.
2. Read .agents/skills/drafter/SKILL.md and the three drafting templates. Run the Drafter from that handover, producing feature-guide.md, how-to.md, and release-note.md.
3. Read .agents/skills/proofreader/SKILL.md and templates/qa-report.md. Run a separate review pass over original sources, handover, and drafts. Save QA-REPORT.md, make evidence-backed corrections, and recheck them.
4. Report created paths, material open questions, and readiness. Never report a publication PASS for a materially unresolved contradiction. Do not rewrite source files.

Keep the stages visible in the file outputs and in a brief completion summary. For a live change to a skill, change only the requested rule, show its diff, then rerun this sequence with the new source or the affected stage as appropriate. Do not bake any example product details into these skills.
