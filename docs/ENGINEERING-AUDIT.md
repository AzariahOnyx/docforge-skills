# Engineering audit and improvement backlog

Assessment date: 2026-10-09. Scope: repository skills, standards, Python checker and tests, fictional demos, CI, and current outputs. Ratings are editorial judgments, **not empirical benchmark scores**.

## Strengths worth preserving

- Clear Analyzer → HANDOVER → Drafter → Proofreader separation.
- Source classifications: FACT, ASSUMPTION, INFERENCE, UNKNOWN, CONTRADICTION.
- Traceable claim IDs and one-disposition-per-claim coverage ledger.
- Unresolved contradiction handling, source-first review, and human publication gate.
- Revised-source change-impact workflow with previous output preserved.
- Structural checker, negative tests, CI, and fictional reproducible examples.

## Prioritized gaps

| Priority | Finding | Evidence | Proposed improvement | Acceptance criterion |
| --- | --- | --- | --- | --- |
| P0 | Default pipeline is tied to three deliverables | `drafter/SKILL.md`, `proofreader/SKILL.md`, `check_outputs.py` | Introduce selectable profiles with a common evidence contract | An API-reference-only or troubleshooting-only run does not produce unrelated articles |
| P0 | Generic intake lacks explicit source hierarchy and privacy | Previous master skill | Introduce `docs/INPUT-CONTRACT.md` and intake checks | Multiple sources are inventoried; conflicts and access gaps surfaced; private material not copied to public outputs |
| P0 | No systematic semantic evaluation benchmark | Checker and demo tests | Create public-safe gold cases for contradictions, missing steps, source revisions, false claims | Report pass/fail per case and false-assertion counts without fabricated performance percentages |
| P1 | Structural validator is profile-specific | `REQUIRED` paths in checker | Add profile-aware manifests and validators | Default and custom profiles each have explicit tested validation |
| P1 | Citations are mostly Markdown line-based and narrowly parsed | `SOURCE_LINE` regex recognizes only `demo/` or `input/` Markdown | Support source IDs + page/section/line locators for PDF, HTML, screenshots, API schemas | Mixed-format citations trace to the inventoried source; unresolvable locators are warnings or failures |
| P1 | Limited automated accessibility/style coverage | `standards/documentation.md` | Add MSTP-aligned style, inclusive language, headings, alt text, tables, code examples, and task-result checks | Lint examples flag representative accessibility and style issues |
| P1 | Proofreader independence can be ambiguous | Reviewer instructions permit second pass | Record reviewer identity/method, evidence, and unresolved failures; don't claim independent validation without separate agent/reviewer | QA report explicitly distinguishes independent review, same-agent second pass, and human approval |
| P1 | No automated source-to-claim entailment checks | Checker verifies only citation existence/nonblank target | Add evidence quotation/locator audit, optional semantic review, and manual verification | Misleading citation to unrelated passage is rejected in an evaluation fixture |
| P2 | No measured quality or speed baseline | Existing demo has no baseline comparator | Evaluate direct-prompt baseline versus staged workflow on same fixed corpus | Publish reproducible results with denominator, method, and limitations |
| P2 | Missing explicit source change provenance | Update mode is Markdown-only | Track source hashes/versions and review decisions | Each run records exactly which source version generated its outputs |
| P2 | No packaged distribution | Skills live under repo-local `.agents/skills` | Publish portable skill pack and installation instructions for compatible agents | A fresh compatible environment can load the skill without repo-specific assumptions |

## What was changed in the first generalization pass

- Added `docs/INPUT-CONTRACT.md` to specify inputs, authority, deliverables, privacy, and review boundaries.
- Expanded the master `generate-docs` skill to allow non-default documentation profiles while preserving the legacy three-document pipeline.
- Added `CASE-STUDY.md` using the fictional Quiet Hours demo, without inventing impact metrics.
- Added this backlog to make limitations and next steps explicit.

**Not yet implemented:** profile-aware Python validation, arbitrary-format parsing, semantic evaluation, multi-agent isolation enforcement, benchmark results, . Do not claim these are complete.

## External references

- Agent Skills specification: https://agentskills.io/specification
- Microsoft Writing Style Guide: https://learn.microsoft.com/en-us/style-guide/welcome/
- Google developer documentation style guide: https://developers.google.com/style

These references guide structure and style; they do not validate product-specific claims.

## Second implementation pass

Implemented in this pass:

- Custom profile manifest with SHA-256 source provenance and a safe-path validator. See `scripts/create_manifest.py`, `scripts/validate_run.py`, and `docs/RUN-FORMAT.md`.
- Exact-quotation checks for claim evidence, source ID and line-locator checks, Markdown structure and link checks, and review status gates. An exact match does not prove that the source supports the interpretation.
- Regression tests for tampered source hashes, fabricated quotations, missing deliverables, duplicate claims, unknown source IDs, invalid locators, unresolved placeholders, and premature approval.
- A fictional benchmark corpus with explicit expected outcomes for contradictions, missing details, revisions, unsupported API claims, and malicious instructions embedded in source text. These are test specifications, not AI performance measurements.
- A review checklist, portable installation guide, detailed README workflow, and a reviewer-judgment scoring utility.
- Removal of legacy names and assignment-specific references from the active public examples.

Still requiring future work or human action:

- Validate extraction and semantic support for PDFs, screenshots, and arbitrary source formats. Page and section locators currently require manual review.
- Execute a blinded comparison of direct prompting and the staged workflow, with actual independent reviewer judgments. The scoring script does not create judgments.
- Verify custom document generation end to end in a compatible agent. The current tests exercise the validator, not an LLM producing correct documentation.
- Ensure private or sensitive material is not accessible through previous Git history. Deleting files from the current branch does not rewrite history. A clean-history migration or authorized history rewrite is a separate operation.
- Improve package portability by eliminating remaining repository-relative assumptions.
