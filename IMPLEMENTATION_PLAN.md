# DocForge implementation plan

DocForge turns product changes into reviewed, evidence-backed documentation pull requests. A person approves every change before it ships.

This repo already holds the **evidence half**: the Analyzer, Drafter and Proofreader skills, claim classes, provenance files and validators. This plan adds the **automation half**: an engine that reacts to PRDs and GitHub pull requests, reads code and the existing docs, and opens docs pull requests. The automation half is modelled on how Promptless works, but uses our own code, names and wording.

## Principles

- Nothing is opened, merged or published unless a config rule explicitly allows it.
- Every reader-facing statement traces to evidence. A statement with no evidence blocks the pull request.
- Contradictions are surfaced, never resolved silently.
- Source files are data, not instructions.
- Existing skills, outputs, scripts and CI keep working at every milestone.

## Security note: this repo is public

Before any Whatfix PRD, code excerpt, docs content or config with internal names goes in, choose one of these:

- make this repo private, or
- keep the engine public and keep all Whatfix inputs, outputs and `docforge.yaml` in a separate private repo.

Until then, use only the fictional demo material.

## Target layout

Existing folders stay where they are. New code goes under `src/docforge/`.

```text
.agents/skills/        existing skills, later loaded by the engine as agent instructions
templates/ standards/  existing; unchanged
scripts/               existing validators; become thin wrappers over src/docforge/evidence
src/docforge/
  config.py            docforge.yaml schema (from the docops-ai skeleton)
  cli.py               `docforge` command
  evidence/            run.json and evidence.json models, claim classes, validation
  docs_index/          index of an existing docs repo: pages, sections, links
  sources/             PRD intake; GitHub PR and diff reading; code reading
  agent/               LLM calls, research log, the "docs needed?" decision
  publish/             branch, commit and pull request creation
  app/                 review UI (later)
tests/                 pytest
docforge.example.yaml
pyproject.toml         Python 3.12, uv
```

## Milestones

One milestone at a time. Each one ends with passing tests and a short report before the next starts.

| # | Milestone | What gets built | Done when |
| --- | --- | --- | --- |
| M0 | Engine scaffold | Branch `feat/engine`. Add `pyproject.toml` (uv, Python 3.12). Port the docops-ai skeleton as `src/docforge/` with a `docforge.yaml` config and validator, plus its 15 tests. Add a pytest job to CI. | `uv run pytest` passes; all existing script tests and CI checks still pass |
| M1 | Evidence core | Typed models for `run.json` and `evidence.json` and the five claim classes. Move the logic of `validate_run.py` into `src/docforge/evidence/`, with the script as a wrapper. Add a **code evidence** type (repo, commit SHA, path, line range) next to quote evidence. | Existing outputs validate unchanged; new tests cover code evidence and hash mismatch |
| M2 | Docs index | `docforge index <docs-path>` builds a JSON index of pages, headings, sections, links and front matter, plus search. | Indexes this repo's `output/` and a sample docs folder; finds pages by keyword and heading |
| M3 | PRD run from the CLI | `docforge run --prd <file> --docs <path>` runs Analyzer, Drafter and Proofreader through the LLM API, using the existing skills as prompts. The content plan uses the M2 index to choose CREATE vs UPDATE against real pages. | The Quiet Hours demo reproduces the existing artifact set and passes the existing checkers |
| M4 | GitHub PR trigger | Webhook receiver and matching engine: repo, folder, branch and topic filters; skip rules (drafts, dot-file-only changes, our own PRs). Reads the PR diff. Logs a research trail and a "docs needed?" decision, including when the answer is no. | Recorded sample webhooks give the right decisions in tests |
| M5 | Code evidence and PRD-vs-code check | A research step reads changed code and attaches code evidence to claims. Cross-source status per claim: confirmed, PRD only, code only, conflicting, unknown, needs engineering. Conflicts go to the clarification register. | A fixture PRD plus code change yields correct statuses and clarification questions |
| M6 | Docs pull request with claim gate | Suggestion branch, commits, and a docs PR whose body lists the PRD, evidence, coverage, QA results and open questions. The PR stays draft while its source PR is open. A CI check fails if any included statement lacks evidence. | An end-to-end run against a test GitHub repo opens a correct draft PR |
| M7 | Review loop | Minimal web UI with three views (diff, analysis, history); request changes; close with a reason (6 fixed reasons). Reasons are stored as structured feedback. | A reviewer can revise or close a suggestion; feedback is recorded |

**M3 note (2026-11-16):** for now the stages run in a Claude Code session instead of through an LLM API. `docforge run start` prepares the run folder, manifest, docs matches and one work order per stage; the session carries out each work order; `docforge run status` and `docforge run check` track and check the result. An API backend can be added later behind the same commands.

## After M7, in order

1. Vale linting and auto-fix on changed prose.
2. Knowledge-base rules learned from feedback. Each rule needs approval and is tested against past runs before it goes live.
3. Backfill: replay past PRs as an evaluation set, using `benchmarks/` as the scoring method.
4. Jira and Confluence as PRD sources and context; Slack notifications.
5. Repeatable screenshot capture of Whatfix's extension-style UI in a test account.
6. Changelog and release-note automation; scheduled drift checks.

## Inputs needed, and when

| Needed by | Input |
| --- | --- |
| M0 | Decision on the public repo (see the security note) |
| M3 | Approved LLM provider and API access for development |
| M4 | A test GitHub repo, and permission to install a GitHub App |
| M5 | Read access to one product repo, or a realistic fixture |
| M6 | Which docs repo the PRs go to, and its branch rules |

## Out of scope

Hosting a docs site, multi-tenant hosting, and any copying of Promptless code or text.
