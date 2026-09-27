---
name: generate-docs
description: Run the reusable PRD-to-documentation workflow to produce a clarification register, feature guide, task how-to, release note, and QA report. Use for a new PRD, supporting artifacts, or a live-round rerun after source or skill changes.
---

# Generate docs

Accept source path(s) and an output directory. Default to input/ and output/<feature-slug>/ only when unambiguous; otherwise ask for the missing path. Never use an old handover for a different source. Create `analysis/`, `feature/`, `how-to/`, `release-note/`, and `qa/` below the output directory. Keep source files unchanged.

1. Read `AGENTS.md` and the source artifacts. Read `.agents/skills/analyzer/SKILL.md`, `templates/handover.md`, and `templates/content-plan.md`. Run the Analyzer first and save `analysis/HANDOVER.md`, `analysis/clarifications-and-assumptions.md`, and `analysis/CONTENT-PLAN.md`. Check source coverage and make contradictions traceable to both passages. Inventory supplied existing docs before proposing updates.
2. Read `.agents/skills/drafter/SKILL.md`, `standards/documentation.md`, the three drafting templates, and `templates/coverage.md`. Draft from that handover into `feature/feature-guide.md`, `how-to/how-to.md`, and `release-note/release-note.md`. Create `analysis/COVERAGE.md` mapping every material handover claim to an included draft section, context, deferral, or blocker. For a newly supplied PRD, choose a fresh slug and never overwrite another feature's outputs.
3. Read `.agents/skills/proofreader/SKILL.md` and `templates/qa-report.md`. Use a separate reviewer when available, giving it the original source and all outputs for a fresh check. Otherwise perform a clearly labeled source-first second pass. Save `qa/QA-REPORT.md`, make evidence-backed corrections, and recheck them.
4. Run `python3 scripts/check_outputs.py <output-directory>` to catch missing sections, broken local links, placeholders, and Markdown source citations to missing or blank lines. Treat this as a structural and line-target gate only; the Proofreader must verify that cited passages actually support their claims.
5. Report created paths, CREATE/UPDATE/DEFER scope, coverage gaps, material open questions, checker status, and readiness. Never report a publication PASS for a materially unresolved contradiction.

Keep the stages visible in the file outputs and in a brief completion summary. For a live change to a skill, change only the requested rule, show its diff, then rerun this sequence with the new source or the affected stage as appropriate. Do not bake any example product details into these skills. Add a Mermaid diagram only when it improves a supported flow or relationship; do not let illustrative artwork stand in for source evidence.

## Update mode

When the user supplies a revised PRD plus a prior source and output, keep the prior output intact and choose a fresh output slug or branch. Read `templates/change-impact.md`. Compare the two sources first and write `analysis/CHANGE-IMPACT.md` with added, changed, removed, resolved, and newly conflicting claims and their affected sections. Then run the full Analyzer → Drafter → Proofreader sequence on the revised source, using the old output only as a comparison baseline, never as current product evidence. Explicitly remove stale claims from the new drafts, keep still-supported content, and mark proposed retirement of an existing article for review rather than deleting it. If the prior source is unavailable, report that the change comparison is blocked; a fresh-source run may still proceed if requested. Do not infer a source change merely because two generated drafts differ.
