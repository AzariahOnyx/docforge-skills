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

## Project structure

```text
.agents/skills/       Reusable skill instructions
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
