---
name: demo-studio
description: Run the reusable documentation demo for any user-supplied PRD PDF. Invoke as $demo-studio input/<PDF filename>. Select the source, create a fresh output folder, and complete analysis, drafting, independent proofreading, and checks.
---

# One-command documentation demo

Work from the repository root. The words after `$demo-studio` identify the input PDF; accept a path such as `input/Technical Writer - Case Study.pdf`, a filename in `input/`, or a uniquely matching filename stem. Quoted paths and spaces are valid. Do not require the user to specify an output directory or repeat the workflow prompt.

1. Read `AGENTS.md` and `.agents/skills/generate-docs/SKILL.md`. Check Git status without changing branches, stashing, resetting, committing, or pushing. Keep all existing system files, inputs, outputs, and backups unchanged.
2. Resolve the supplied PDF within `input/`. If the path is missing, find a unique matching PDF in `input/`; if ambiguous or absent, ask only for the correct filename. Do not select a PDF in `.demo-backups/`, an old output, or another example as product evidence. Verify readable text, page count, and all pages; render pages where extraction misses visual content. Stop and explain if unreadable.
3. Derive a short descriptive lowercase hyphenated slug from the PDF's product or feature title, removing generic words such as PRD, dummy, case study, and PDF. Create a fresh `output/<slug>/` set. If that directory exists or is already tracked, choose `output/<slug>-2/`, then the next unused number. Never overwrite, move, delete, or use a prior output as evidence. Report the chosen path.
4. Run the entire `generate-docs` workflow on this PDF: source-first Analyzer and structured handover, clarification register and content plan; Drafter using repository standards and templates; claim coverage; independent source-first Proofreader and evidence-backed corrections. Inspect every page before drafting. Apply the editorial gate for descriptive titles, a meaningful supported how-to, and a change-focused release note. Preserve both sides of contradictions in review artifacts and mark unknowns. Propose CREATE, UPDATE, and DEFER scope based on an inventory of any supplied existing docs. Add Mermaid flows only where the source supports them.
5. Run `python3 scripts/check_outputs.py output/<chosen-slug>`. Fix structural errors, rerun, and report the result separately from source-fidelity review. Never claim publication readiness while material contradictions or unknowns remain.
6. Summarize source page count, exact new file paths, scope, proofreading and structural QA, unresolved questions, and readiness. Leave all files uncommitted and unpushed.

Invocation example: `$demo-studio input/Technical Writer - Case Study.pdf`. The same skill must work for the next PDF uploaded into `input/`, without editing this skill or asking for a long prompt.


## V2 quality override

The V2 editorial workflow is mandatory for every invocation. The Drafter must create `analysis/EDITORIAL-BLUEPRINT.md` before reader-facing prose and complete its Draft challenge after drafting. The Proofreader must review the blueprint against the original source and apply the correction loop in `generate-docs`. A run is complete only after the final structural checker and the master skill's solid-doc-set acceptance decision.
