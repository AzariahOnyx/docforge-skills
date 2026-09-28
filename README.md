# Technical writing case study

This repository contains the three Tasket Tracks case-study deliverables and a reusable Codex workflow for producing first drafts from a different PRD. The source is a working specification, so the outputs distinguish documented facts from assumptions, unknowns, and contradictions.

## Start here

| Assignment part | Review |
| --- | --- |
| 1. Clarifications and assumptions | [Register](output/tracks/analysis/clarifications-and-assumptions.md), [evidence handover](output/tracks/analysis/HANDOVER.md), [content scope](output/tracks/analysis/CONTENT-PLAN.md), [claim coverage](output/tracks/analysis/COVERAGE.md) |
| 2. Three documents | [Feature guide](output/tracks/feature/feature-guide.md), [how-to](output/tracks/how-to/how-to.md), [release note](output/tracks/release-note/release-note.md) |
| 3. Reusable skill | [Generate docs](.agents/skills/generate-docs/SKILL.md), [live-round guide](demo/README.md) |
| Review status | [QA report](output/tracks/qa/QA-REPORT.md) |

The Tracks PDF is [the authoritative source](input/Technical%20Writer%20-%20Case%20Study.pdf). In particular, page 3 says disabling Tracks hides data and restores it later, while page 5 says disabling clears assignments and statuses. [Q01](output/tracks/analysis/clarifications-and-assumptions.md) keeps both statements unresolved. The reader-facing drafts do not choose either disputed outcome. The feature guide flags the conflict at the point where disabling is mentioned and directs the reader to confirm the behavior before disabling Tracks.

## How the workflow works

```mermaid
flowchart TD
    A["PRD and artifacts"] --> B["Analyzer"]
    B --> C["Handover, questions, content plan"]
    C --> D["Drafter"]
    D --> E["Three drafts and coverage ledger"]
    E --> F["Source-first Proofreader"]
    A --> F
    F --> G["QA report and corrections"]
```

The Analyzer establishes a documentation contract and prioritizes supported material by reader relevance. Before prose is written, the Drafter records an editorial blueprint that defines reader jobs, inclusion boundaries, section logic, task selection, release-note priorities, and cross-document separation. The Drafter uses that contract to serve three different reader goals and performs a senior editorial pass before handoff. The Proofreader independently checks source fidelity and editorial quality against the original source. `AGENTS.md` holds repository-wide evidence rules; the stage-specific skills under `.agents/skills/` hold workflow instructions.

## Output structure

Each run creates a separate `output/<feature-slug>/` tree:

| Folder | Files and purpose |
| --- | --- |
| `analysis/` | `HANDOVER.md` (classified claims), `clarifications-and-assumptions.md` (open questions), `CONTENT-PLAN.md` (CREATE / UPDATE / DEFER scope), `COVERAGE.md` (every claim's destination or reason for omission); optional `CHANGE-IMPACT.md` for a revised PRD |
| `feature/` | `feature-guide.md` for a first-time user |
| `how-to/` | `how-to.md` for one supported user goal |
| `release-note/` | `release-note.md` for an existing user scanning the change |
| `qa/` | `QA-REPORT.md` with source-first findings and readiness |

Reusable structures live in `templates/`. [The documentation standard](standards/documentation.md) defines each article's purpose, structure, evidence rules, style, and review gates. The default run creates one file of each type; additional requested articles may use descriptive filenames in the same folders. A revised-source run compares old and new source evidence before drafting, writes `CHANGE-IMPACT.md`, and leaves the previous output intact.

## Run it in Codex CLI

From the repository root in Codespaces, open Codex and enter:

```text
Read .agents/skills/generate-docs/SKILL.md and run it on input/Technical Writer - Case Study.pdf. Write to output/tracks/. Read all pages, including tables. Keep contradictory disable behavior unresolved. Report the content scope and QA result.
```

For a new PRD, place it under `input/` with a distinct name and replace the two paths in that prompt. Use a new output slug so the Tracks files are preserved. Codex discovers repo-local skills in `.agents/skills/`; `$generate-docs` can also invoke the master skill. See [the rehearsal guide](demo/README.md) for a different PRD and a live skill edit.

## Checks and limits

```text
python3 scripts/check_outputs.py output/tracks
```

The checker catches missing files/headings, broken local links, placeholders, unmatched claim/question IDs, and missing, duplicated, or invalid coverage dispositions. GitHub Actions runs it on each generated set for pushes and pull requests. It does not establish whether a product claim is true or whether a cited section truly supports it. The Proofreader compares the source, handover, scope, coverage, and drafts, records PASS/WARNING/FAIL findings, and separates technical fidelity, editorial quality, assignment review, and publication readiness. The latest Tracks drafts were regenerated during submission review after the previous checker run; `output/tracks/qa/QA-REPORT.md` records that the structural checker still needs to be rerun for this revision. The [revised Quiet Hours example](output/quiet-hours-v2/analysis/CHANGE-IMPACT.md) shows a changed duration and a newly confirmed online rule, with the earlier output preserved. No product build or existing Tasket documentation was supplied; proposed updates to existing help content remain candidates until that content is inventoried.

Download this branch as a ZIP from GitHub if a single folder is needed for submission. The [live-round guide](demo/README.md) gives a prompt and verification sequence for a different PRD.
