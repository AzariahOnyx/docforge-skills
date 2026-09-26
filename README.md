# Technical writing case study

This repository contains a reusable PRD-to-documentation workflow and the Tasket Tracks case-study outputs. It is a Markdown-first technical writing project.

## Architecture

PRD and supporting artifacts → Analyzer → structured HANDOVER.md → Drafter → feature guide, how-to guide, release note → Proofreader → QA report and corrected drafts.

The Analyzer establishes the documentation contract; the Drafter writes for three distinct reader goals; the Proofreader checks the handover and drafts against the original source. The workflow is reusable for a different PRD.

## Repository map

- input/: PRDs and supporting artifacts. The source PDF is the authority for Tracks.
- AGENTS.md: project-wide evidence rules.
- .agents/skills/analyzer/SKILL.md: source analysis and clarification register.
- .agents/skills/drafter/SKILL.md: audience-specific drafting.
- .agents/skills/proofreader/SKILL.md: independent source check.
- .agents/skills/generate-docs/SKILL.md: one entry point that runs all three stages.
- templates/: reusable handover, document, and QA structures.
- output/<feature>/: one set of generated case-study files per source.
- demo/README.md: live-round procedure.

## Run in Codex CLI

From the repository root, ask:

`Use $generate-docs on input/Technical Writer - Case Study.pdf and write to output/tracks/. Review all pages and supporting artifacts. Produce the handover and clarification register before drafting, then independently proofread against the original source.`

If skill discovery in an already-open session is stale, refer explicitly to .agents/skills/generate-docs/SKILL.md. Use the same command pattern with a different PRD and output directory during the live round.

## Evidence and review

The handover classifies claims as FACT, ASSUMPTION, INFERENCE, UNKNOWN, or CONTRADICTION and records source locations. Product claims in reader-facing documentation require confirmed support. Working assumptions and open questions belong in the clarification register; a blocked step is not filled in by guesswork. QA-REPORT.md distinguishes assignment completion from publication readiness.

For the Tracks assignment, inspect the source's statements about disabling the feature independently. If two passages disagree about retention of assignments, record both with page references and leave the behavior unresolved. Do not encode the answer in a reusable skill.

## Review and commits

Read output/tracks/clarifications-and-assumptions.md, feature-guide.md, how-to.md, release-note.md, and QA-REPORT.md. Commit source and workflow separately from reviewed outputs so the stages remain easy to explain. See demo/README.md for a rerun with another PRD.
