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
| P0 | Public repository includes original interview assignment PDF | `input/Technical Writer - Case Study.pdf` | Confirm rights to redistribute; if not authorized, remove assignment PDF and product-specific outputs from public history or migrate to a clean public repo | Public showcase contains only authorized material; historical git exposure addressed |
| P0 | No systematic semantic evaluation benchmark | Checker and demo tests | Create public-safe gold cases for contradictions, missing steps, source revisions, false claims | Report pass/fail per case and false-assertion counts without fabricated performance percentages |
| P1 | Structural validator is profile-specific | `REQUIRED` paths in checker | Add profile-aware manifests and validators | Default and custom profiles each have explicit tested validation |
| P1 | Citations are mostly Markdown line-based and narrowly parsed | `SOURCE_LINE` regex recognizes only `demo/` or `input/` Markdown | Support source IDs + page/section/line locators for PDF, HTML, screenshots, API schemas | Mixed-format citations trace to the inventoried source; unresolvable locators are warnings or failures |
| P1 | Limited automated accessibility/style coverage | `standards/documentation.md` | Add MSTP-aligned style, inclusive language, headings, alt text, tables, code examples, and task-result checks | Lint examples flag representative accessibility and style issues |
| P1 | Proofreader independence can be ambiguous | Reviewer instructions permit second pass | Record reviewer identity/method, evidence, and unresolved failures; don't claim independent validation without separate agent/reviewer | QA report explicitly distinguishes independent review, same-agent second pass, and human approval |
| P1 | No automated source-to-claim entailment checks | Checker verifies only citation existence/nonblank target | Add evidence quotation/locator audit, optional semantic review, and manual verification | Misleading citation to unrelated passage is rejected in an evaluation fixture |
| P1 | No clear general user onboarding | README originally opens with interview submission | Make fictional case study and intake contract the entry point; provide one-command demo and examples | A new user can understand requirements, run example, locate output, and interpret limits |
| P2 | No measured quality or speed baseline | Existing demo has no baseline comparator | Evaluate direct-prompt baseline versus staged workflow on same fixed corpus | Publish reproducible results with denominator, method, and limitations |
| P2 | Missing explicit source change provenance | Update mode is Markdown-only | Track source hashes/versions and review decisions | Each run records exactly which source version generated its outputs |
| P2 | No packaged distribution | Skills live under repo-local `.agents/skills` | Publish portable skill pack and installation instructions for compatible agents | A fresh compatible environment can load the skill without repo-specific assumptions |

## What was changed in the first generalization pass

- Added `docs/INPUT-CONTRACT.md` to specify inputs, authority, deliverables, privacy, and review boundaries.
- Expanded the master `generate-docs` skill to allow non-default documentation profiles while preserving the legacy three-document pipeline.
- Added `CASE-STUDY.md` using the fictional Quiet Hours demo, without inventing impact metrics.
- Added this backlog to make limitations and next steps explicit.

**Not yet implemented:** profile-aware Python validation, arbitrary-format parsing, semantic evaluation, multi-agent isolation enforcement, benchmark results, and historical public-PDF cleanup. Do not claim these are complete.

## External references

- Agent Skills specification: https://agentskills.io/specification
- Microsoft Writing Style Guide: https://learn.microsoft.com/en-us/style-guide/welcome/
- Google developer documentation style guide: https://developers.google.com/style

These references guide structure and style; they do not validate product-specific claims.
