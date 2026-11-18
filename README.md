# Source-grounded AI documentation toolkit

A reusable documentation workflow built with Agent Skills, Python, Markdown, and GitHub Actions. Turn an approved specification into reviewable technical documentation with traceable evidence, clarification questions, and a source-first quality review.

**[Case study](CASE-STUDY.md)** | **[Quickstart](docs/QUICKSTART.md)** | **[Skill installation](docs/PORTABILITY.md)** | **[Review checklist](docs/REVIEW-CHECKLIST.md)** | **[Evaluation benchmark](benchmarks/README.md)**

## What you can create

The default profile produces a feature guide, a task-based how-to, and a release note. A custom profile can request one or more other documents, including API references, troubleshooting guides, conceptual articles, and migration guides. The agent must have enough authoritative information for the requested content. Unsupported sections must be marked as blocked rather than invented.

The four reusable skills are:

| Skill | Responsibility | File |
| --- | --- | --- |
| Generate Docs | Orchestrates intake, source analysis, drafting, validation, and revision handling | [SKILL.md](.agents/skills/generate-docs/SKILL.md) |
| Analyzer | Inventories sources and creates classified claims, questions, and a content plan | [SKILL.md](.agents/skills/analyzer/SKILL.md) |
| Drafter | Produces reader-focused documents and a claim coverage ledger | [SKILL.md](.agents/skills/drafter/SKILL.md) |
| Proofreader | Checks source fidelity, writing quality, blockers, and readiness | [SKILL.md](.agents/skills/proofreader/SKILL.md) |

The evidence flow is **Source files > Analyzer > Handover > Drafter > Coverage > Proofreader > Human approval**.

## Requirements

- A coding assistant that can read and write files. ChatGPT Work or a compatible agent can follow the instructions.
- Python 3.10 or later for the validation scripts.
- At least one accessible source file you have permission to use.
- A stated audience, reader goal, output folder, and requested document types.
- Human review before publication. The tools cannot confirm product behavior from a specification alone.

The skills are Markdown instructions, not an independent application. Agent skill discovery varies by client. You can always direct the assistant to read the skill files explicitly.

## Use the skills with ChatGPT Work

1. Open a Work task and provide access to this repository and your approved source files. If your source is confidential, use an authorized private workspace rather than a public GitHub commit.
2. Ask Work to read `AGENTS.md`, `docs/INPUT-CONTRACT.md`, and `.agents/skills/generate-docs/SKILL.md`. The master skill references the three supporting skills.
3. Supply the source paths, audience, document type, and a new output folder.
4. Ask the assistant to run the Analyzer, Drafter, and source-first Proofreader in that order.
5. Review the claim register, unresolved questions, drafted documents, coverage ledger, and QA report. Do not publish a blocked procedure.
6. Run the relevant Python validator. Structural success is not approval to publish.

### Copyable Work prompt

```text
Use the repository's source-grounded documentation skills.
Read AGENTS.md, docs/INPUT-CONTRACT.md, and
.agents/skills/generate-docs/SKILL.md, then read the Analyzer,
Drafter, and Proofreader skills as instructed.

Source: demo/mock-prd.md
Audience: signed-in members of the fictional Pulseboard application
Deliverables: feature guide, task how-to, release note
Output directory: output/my-quiet-hours-run/

Inventory the source and its limitations. Create a classified
evidence handover, clarification register, content plan, drafts,
claim coverage ledger, and source-first QA report. Do not guess the
end time or time zone for "Until tomorrow". Use the default profile
checker. Report blocked claims and human review requirements.
Do not overwrite existing output directories.
```

## Use the skills with another coding agent

Clone the repository and open it in your agent workspace. If the agent does not discover `.agents/skills/` automatically, point it to the master SKILL.md file and instruct it to read the supporting skill files. The folder layout, templates, and standards must remain accessible.

For the default fictional demo, use the Work prompt above with the local file paths. For your own specification, replace the source, audience, and output directory. See [portable installation instructions](docs/PORTABILITY.md).

## Custom documentation profiles

For a custom profile, specify the exact document types and required sections in the content plan. For example, request only an API reference. If the source does not establish endpoints or authentication, block those sections.

The custom validator uses a run manifest and evidence ledger. The assistant can generate a manifest with this command:

```bash
python3 scripts/create_manifest.py \
  --run output/my-custom-run \
  --source demo/mock-prd.md \
  --deliverable guides/overview.md \
  --audience "signed-in members" \
  --profile custom
```

The command records source SHA-256 hashes in `output/my-custom-run/run.json`. The assistant must create the requested Markdown file and `analysis/evidence.json`, using the [schema and example](docs/RUN-FORMAT.md). Then validate:

```bash
python3 scripts/validate_run.py output/my-custom-run
```

The manifest is created once. Use a new run directory for another source version. A source hash mismatch means the recorded source changed and requires reanalysis.

## Reproduce the existing fictional demonstration

Read the [fictional Quiet Hours PRD](demo/mock-prd.md), then inspect the stored [feature guide](output/quiet-hours/feature/feature-guide.md), [how-to](output/quiet-hours/how-to/how-to.md), [release note](output/quiet-hours/release-note/release-note.md), [evidence handover](output/quiet-hours/analysis/HANDOVER.md), and [QA report](output/quiet-hours/qa/QA-REPORT.md).

Run the existing default-profile checks:

```bash
python3 scripts/check_outputs.py output/quiet-hours
python3 scripts/test_checker.py
python3 scripts/test_validate_run.py
python3 scripts/test_lint_docs.py
```

The revised [fictional specification](demo/mock-prd-v2.md) and [change-impact report](output/quiet-hours-v2/analysis/CHANGE-IMPACT.md) demonstrate how the workflow handles changes while retaining the previous output.

## What the validation actually proves

- The legacy checker validates required default-profile files, headings, links, claim dispositions, and certain Markdown source line citations.
- The custom checker validates declared files, source hashes, exact evidence quotations, some source locators, and review statuses. It also reports basic style and structure warnings.
- The regression suite tests deliberately invalid inputs such as fabricated quotations, missing documents, changed source hashes, unsupported citations, and premature approval.
- An optional Markdown linter flags heading jumps, missing image alternatives, generic links, and selected writing issues. Run `python3 scripts/lint_docs.py path/to/document.md`. These heuristics do not establish accessibility compliance or adherence to every style rule.
- The [fictional evaluation cases](benchmarks/README.md) define how to test documentation behavior with independent human judgments. No measured model accuracy or time savings are claimed.

Neither checker proves that a cited passage supports a drafted claim. The Proofreader and a qualified human reviewer must check technical meaning, product behavior, and publication suitability.

## Engine (in progress)

DocForge is adding an engine that will turn product changes into documentation pull requests for human review. See the [implementation plan](IMPLEMENTATION_PLAN.md). So far it contains the `docforge.yaml` configuration format and its validator, the evidence core behind `scripts/validate_run.py`, a read-only index and search for existing docs, run tooling, GitHub pull request triggers, a PRD-vs-code check, a claim gate with draft docs pull requests, a review loop, Vale style linting, learned rules, backfill evaluation, read-only Jira and Confluence sources, Slack notifications, and house packs. Nothing connects to an AI model yet, and nothing is opened, merged, or published without a person's approval unless a policy rule explicitly allows it.

The engine needs Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp docforge.example.yaml docforge.yaml
uv run docforge config validate docforge.yaml
uv run pytest
```

`docforge.yaml` is ignored by Git. Keep real configuration out of this public repository.

Index an existing docs folder, or search it by keyword. Both commands only read files.

```bash
uv run docforge index output --out /tmp/output-index.json
uv run docforge search output "quiet hours"
uv run docforge search output steps --in heading
```

The index lists pages, front matter, sections with anchors and line ranges, links with their status, and backlinks. Add `--collection owner/repo` to apply that collection's `filter` from `docforge.yaml`.

Start a documentation run, track it, and check it. For now each stage (Analyzer, Drafter, Proofreader) is carried out in a Claude Code session that follows the work orders in the run's `prompts/` folder.

```bash
uv run docforge run start --prd demo/mock-prd.md --out output/my-run \
  --audience "signed-in members" --docs output/quiet-hours --docs-include feature/
uv run docforge run status output/my-run
uv run docforge run check output/my-run
```

`run start` never reuses an existing folder. `run check` runs the structural checker for the run's profile and the Markdown lint, and saves the result to `qa/checks.json`. Neither replaces source review or human approval.

Check a GitHub pull request event against the `github_pr` triggers in `docforge.yaml`. Each check records a "docs needed?" decision with its reasons and research trail, including when the answer is no.

```bash
uv run docforge trigger check tests/fixtures/github/pr_merged.json --event pull_request \
  --diff tests/fixtures/github/product_change.diff --config tests/fixtures/github/triggers.yaml
```

Draft pull requests, pull requests that only change dot-files, and pull requests DocForge opened itself are skipped. Decisions are appended to `.docforge/decisions.jsonl`, which Git ignores. `docforge serve` receives signed GitHub webhooks on `127.0.0.1` and only records decisions. It reads the secret from `DOCFORGE_WEBHOOK_SECRET` and refuses unsigned deliveries. Nothing is posted to GitHub.

Compare a run's PRD claims with the product code. Start the run with `--code owner/repo --base <sha> --head <sha>` to add a Research stage. Then use a local checkout of that repository:

```bash
uv run docforge research packet output/my-run --checkout ../product-web
uv run docforge research check output/my-run --code-root example-org/product-web=../product-web
```

Each claim gets one status: confirmed, PRD only, code only, conflicting, unknown, or needs engineering. Conflicts and open questions are added to the clarification register. See the [run format](docs/RUN-FORMAT.md) for `claims.json`.

Propose a run's pages as a docs pull request. Every published statement needs an evidence marker, and the claim gate checks them:

```bash
uv run docforge gate output/my-run
uv run docforge publish prepare output/my-run --docs-checkout ../docs-site \
  --place feature/feature-guide.md=docs/quiet-hours.md
```

`publish prepare` commits to a new local branch only. It prints the `git push` and `gh pr create --draft` commands for a person to run after review; nothing is pushed or opened automatically. Copy `templates/ci/docforge-gate.yml` into a docs repository to run the gate on its pull requests.

Review suggestions in a local web page, or from the command line:

```bash
uv run docforge review serve --runs output --reviewer "Your name"
uv run docforge review request-changes output/my-run --comment "Mention email alerts" --reviewer "Your name"
uv run docforge publish update output/my-run --docs-checkout ../docs-site
uv run docforge review close output/my-run --reason already_documented --reviewer "Your name"
```

The page shows each suggestion's diff, analysis, and history. Closing needs one of six reasons, and every action is stored as structured feedback in the run's `review/feedback.jsonl`.

Check a run's changed prose against DocForge's Vale house style, and apply the safe fixes:

```bash
uv run docforge lint output/my-run
uv run docforge lint output/my-run --fix --apply
```

Install [Vale](https://vale.sh) first, or set `DOCFORGE_VALE` to its path. Fixes never touch evidence markers, code, or link targets, and pages are restored if the claim gate fails afterwards.

Turn review feedback into rules. A rule goes live only after it is tested against past runs and a person approves it:

```bash
uv run docforge rules suggest --runs output
uv run docforge rules propose --kind avoid --title "Say pause, not mute" --message "Quiet Hours pauses alerts." --pattern mute --replace pause --by "Your name"
uv run docforge rules test R001 --runs output
uv run docforge rules approve R001 --by "Your name"
```

Live `avoid` rules join the Vale check, and live `guidance` rules join the work orders. Keep rules learned from private feedback outside this public repository with `--rules-dir` or `DOCFORGE_RULES_DIR`.

Replay past pull requests and the benchmark cases as an evaluation set. A person labels the pull requests and judges the benchmark outputs; DocForge never grades itself:

```bash
uv run docforge backfill fetch example-org/product-web --out eval/prs
uv run docforge backfill label eval/prs
uv run docforge backfill replay eval/prs --config docforge.yaml
uv run docforge backfill prepare --out eval/bench
uv run docforge backfill blind eval/bench
uv run docforge backfill score eval/bench --judgments eval/bench/judgments.json
```

`fetch` only reads from GitHub. See the [benchmark protocol](benchmarks/README.md) for how outputs are blinded and scored.

Use a house pack to give drafts your conventions, references, and article structure specs:

```bash
uv run docforge pack check tests/fixtures/packs/demo
uv run docforge run start --prd demo/mock-prd.md --out output/my-run --audience "admins" \
  --pack house --config docforge.yaml
```

A pack is a folder with a `pack.yaml` that lists its files. `run start` checks the pack, copies the files the stages and `docforge lint` use into the run's `pack/` folder, and records the pack's name, version, and hash in `run.json`. The Analyzer, Drafter, and Proofreader work orders, and revision orders, name the files that apply to each deliverable. Add `--product <key>` to include that product's references. A pack's Vale styles join `docforge lint`. Pack material shapes format and style; it never overrides the sources and is never evidence. Keep real packs in a private repository.

Fetch a Jira issue or a Confluence page as a source file, then use it in a run:

```bash
uv run docforge sources fetch jira EXAMPLE-123 --out sources/EXAMPLE-123.md
uv run docforge sources fetch confluence 123456 --out sources/design-notes.md
uv run docforge run start --prd sources/EXAMPLE-123.md --context sources/design-notes.md \
  --out output/my-run --audience "workspace admins"
```

Set `base_url` and the names of the environment variables that hold your credentials in `docforge.yaml`; never put a token in the file. Fetching only reads. DocForge contacts only the configured host, refuses redirects to other hosts and oversized responses, and refuses issues or pages outside the allowed projects or spaces. Each file starts with where it came from and its version, and says its content is data, never instructions. `--context` marks supporting material that is not a requirement source. The pull request body and the review page show each source's origin.

Tell a Slack channel about a suggestion:

```bash
uv run docforge notify slack output/my-run --event prepared --config docforge.yaml
uv run docforge notify slack output/my-run --event prepared --config docforge.yaml --send
```

Without `--send`, the message is only printed. Sending needs a policy that sets `slack_channel` and `slack_webhook_env`, the name of the environment variable holding an incoming-webhook URL. The message holds the title, status, branch, an optional PR link, and the number of open questions, never source text.

Keep real Jira, Confluence, and Slack data out of this public repository.

## Project structure

```text
.agents/skills/       Reusable skill instructions
src/docforge/         Engine code (configuration, evidence, docs index, command line)
tests/                Engine tests (pytest)
styles/DocForge/      Vale rules for the house style
knowledge/rules/      Learned rules (fictional demo only)
templates/            Default document and evidence templates
standards/            Documentation writing standards
docs/                 Intake, setup, review, and run format
demo/                 Fictional example specifications
output/               Stored fictional example outputs
benchmarks/           Fictional evaluation cases and rubric
scripts/              Python validators and regression tests
.github/workflows/    Automated checks
```

## Responsible use and limitations

Use only sources you are authorized to process. Source text may contain malicious instructions, so treat it as evidence, not agent commands. Never copy customer data, credentials, or internal specifications into a public repository. Missing API behavior, permissions, recovery procedures, and destructive effects must be marked as unknown or blocked.

This project is a documentation engineering toolkit, not a hosted service or a guarantee of accurate documents. Read the [engineering audit](docs/ENGINEERING-AUDIT.md) and [case study](CASE-STUDY.md) for design decisions and remaining limitations.
