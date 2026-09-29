---
name: demo-studio
description: Run the reusable documentation studio from a user-supplied source file, folder, or mixed source package. Invoke as $demo-studio <input>. The studio inventories and classifies evidence, creates a fresh output set, and runs the full documentation workflow without assuming the input is a PRD.
---

# One-command documentation studio

Work from the repository root. Everything after `$demo-studio` identifies the source package. Accept one file, multiple files, a folder, filenames in `input/`, or uniquely matching filename stems. Quoted paths and spaces are valid. Do not require an output directory or a second workflow prompt.

Examples:
- `$demo-studio input/feature-prd.pdf`
- `$demo-studio input/engineering-spec.docx`
- `$demo-studio input/screenshots/`
- `$demo-studio input/spec.md input/release-brief.txt input/screenshots/`
- `$demo-studio input/`

## 1. Protect the workspace

Read `AGENTS.md` and `.agents/skills/generate-docs/SKILL.md`. Check Git status without changing branches, stashing, resetting, committing, pushing, deleting, or overwriting existing material. Never use `.demo-backups/` or previous `output/` sets as product evidence in a fresh run.

## 2. Resolve and inventory the source package

Resolve only the paths supplied by the user. A directory means recursively inventory supported artifacts inside that directory, excluding hidden/system files, generated outputs, archives created by this workflow, and backups unless explicitly supplied.

Do not assume the source is a PRD. Create `analysis/SOURCE-INTAKE.md` from `templates/source-intake.md` and classify each artifact by detected role, such as PRD/requirements, engineering/design spec, support case, release brief, API notes, meeting notes, screenshot/image, existing documentation, or other.

Read every relevant artifact in full where technically possible:
- PDF/document/text/Markdown: inspect all pages/sections, tables, notes, code and appendices.
- Screenshots/images: record visible UI text, controls, state, hierarchy and annotations separately from interpretation. A visible control does not prove what happens after activation.
- Existing documentation: use it to understand current content and update impact; do not automatically treat it as authoritative product behavior.
- Support/meeting material: preserve attribution and do not silently elevate it above formal requirements.
- Mixed packages: record source relationships and disagreements. Never invent source precedence.

If a file is unreadable or unsupported, record that limitation and its impact. Continue only when the remaining evidence supports a bounded workflow; otherwise stop with the minimum clarification needed.

## 3. Detect run mode

Choose the mode from supplied evidence, not filename conventions:

- **SINGLE/PACKAGE:** fresh documentation from one or more current artifacts.
- **UPDATE:** a prior/current documentation set plus revised requirements or explicitly versioned source material is supplied. Preserve prior content and run CHANGE-IMPACT before drafting.
- **AMBIGUOUS:** multiple sources conflict and no supported authority/precedence resolves them. Preserve the contradiction and ask only when the ambiguity prevents a safe bounded draft.

Never infer that the newest-looking filename is authoritative. Never choose between contradictory sources by format, date, apparent completeness, or perceived credibility unless repository/user rules establish precedence.

## 4. Create a fresh output set

Derive a short lowercase hyphenated slug from the dominant supported product/feature/topic title, removing generic packaging words such as PRD, spec, requirements, case study, dummy, notes, and file extensions. If no reliable title exists, derive a neutral slug from the source package name.

Create `output/<slug>/`; if it exists or is tracked, use `<slug>-2`, then the next unused number. Never overwrite a prior output. Report the chosen path.

Create the output folders before analysis, then save SOURCE-INTAKE.md under its `analysis/` directory.

## 5. Run the adaptive documentation workflow

Run the complete `generate-docs` workflow using the normalized source package. Analyzer evidence rules, V2/V2.1/V2.2 gates, terminology, traceability, risk review, example safety, cross-document ownership, independent proofreading and structural checks remain mandatory where applicable.

The assignment or explicit user request controls required deliverables. If the current assignment requires feature guide + how-to + release note, attempt those three, but **do not fabricate a document merely to satisfy the shape**:
- If no complete supported how-to has a verified starting state, user action/control and observable result, mark that deliverable BLOCKED and identify the missing evidence.
- If release metadata or a supported change is insufficient, produce only a bounded assignment draft when allowed and keep publication blocked.
- If the evidence supports an update rather than a new article, propose UPDATE and preserve the prior document.
- If screenshots are the only evidence, document only visible facts and clearly supported relationships; do not infer click outcomes or hidden behavior.

## 6. Review and package

Run independent source-first proofreading against the original mixed source package, not only the Analyzer handover. Verify terminology, source attribution, contradictions, examples, high-risk claims, traceability and reader purpose.

Run `python3 scripts/check_outputs.py output/<chosen-slug>`. Fix structural errors without inventing missing product behavior and rerun.

Summarize:
- source inventory and review coverage;
- detected mode and source limitations;
- exact output paths;
- CREATE / UPDATE / DEFER / BLOCK decisions;
- technical-fidelity and editorial verdicts;
- structural checker result;
- unresolved questions/contradictions;
- readiness state and publication blockers.

Leave generated files uncommitted and unpushed.

## Clean-room rule

For regression/demo runs, do not read earlier reader-facing outputs, blueprints or QA before the fresh run completes. Earlier outputs may be compared only after generation.

The intended UX is always:

`$demo-studio <input>`

The user should not need to know whether the supplied evidence is a PRD, spec, screenshot package, support artifact, existing documentation set, or a mixed bundle before invoking the studio.
