---
name: generate-docs
description: Run the reusable PRD-to-documentation workflow to produce a clarification register, feature guide, task how-to, release note, and QA report. Use for a new PRD, supporting artifacts, or a live-round rerun after source or skill changes.
---

# Generate docs

Accept source path(s) and an output directory. Default to input/ and output/<feature-slug>/ only when unambiguous; otherwise ask for the missing path. Never use an old handover for a different source. Create `analysis/`, `feature/`, `how-to/`, `release-note/`, and `qa/` below the output directory. Keep source files unchanged.

1. Read `AGENTS.md` and the source artifacts. Read `.agents/skills/analyzer/SKILL.md`, `templates/handover.md`, and `templates/content-plan.md`. Run the Analyzer first and save `analysis/HANDOVER.md`, `analysis/clarifications-and-assumptions.md`, and `analysis/CONTENT-PLAN.md`. Check source coverage and make contradictions traceable to both passages. Inventory supplied existing docs before proposing updates.
2. Read `.agents/skills/drafter/SKILL.md`, `standards/documentation.md`, the three drafting templates, and `templates/coverage.md`. Draft from that handover into `feature/feature-guide.md`, `how-to/how-to.md`, and `release-note/release-note.md`. Create `analysis/COVERAGE.md` mapping every material handover claim to an included draft section, context, deferral, or blocker. For a newly supplied PRD, choose a fresh slug and never overwrite another feature's outputs.
3. Read `.agents/skills/proofreader/SKILL.md` and `templates/qa-report.md`. Use a separate reviewer when available, giving it the original source and all outputs for a fresh check. Otherwise perform a clearly labeled source-first second pass. Save `qa/QA-REPORT.md`, make evidence-backed corrections, and recheck them.
   Require an editorial gate in addition to source fidelity: informative feature title and first-time-user orientation; substantive task selection and complete how-to outcome; change-focused release note for an existing user. Fix audience mismatch even when every sentence is factually supported. Keep unresolved internal disputes in review files and block publication when necessary.
4. Run `python3 scripts/check_outputs.py <output-directory>` to catch missing sections, broken local links, placeholders, and Markdown source citations to missing or blank lines. Treat this as a structural and line-target gate only; the Proofreader must verify that cited passages actually support their claims.
5. Report created paths, CREATE/UPDATE/DEFER scope, coverage gaps, material open questions, checker status, and readiness. Never report a publication PASS for a materially unresolved contradiction.

Keep the stages visible in the file outputs and in a brief completion summary. For a live change to a skill, change only the requested rule, show its diff, then rerun this sequence with the new source or the affected stage as appropriate. Do not bake any example product details into these skills. Add a Mermaid diagram only when it improves a supported flow or relationship; do not let illustrative artwork stand in for source evidence.

## Update mode

When the user supplies a revised PRD plus a prior source and output, keep the prior output intact and choose a fresh output slug or branch. Read `templates/change-impact.md`. Compare the two sources first and write `analysis/CHANGE-IMPACT.md` with added, changed, removed, resolved, and newly conflicting claims and their affected sections. Then run the full Analyzer → Drafter → Proofreader sequence on the revised source, using the old output only as a comparison baseline, never as current product evidence. Explicitly remove stale claims from the new drafts, keep still-supported content, and mark proposed retirement of an existing article for review rather than deleting it. If the prior source is unavailable, report that the change comparison is blocked; a fresh-source run may still proceed if requested. Do not infer a source change merely because two generated drafts differ.
## Submission-quality editorial loop

For assignment or review-ready output, do not stop after a source-fidelity PASS.

1. After drafting, run the Drafter's senior editorial pass before proofreading.
2. During proofreading, record separate **Technical fidelity** and **Editorial quality / assignment fit** verdicts. Both must pass for an unqualified assignment-ready result.
3. If editorial review finds PRD-shaped prose, excessive reference detail, a trivial how-to, a feature-summary-style release note, duplication, or unnatural wording, revise the reader-facing draft without weakening evidence controls, then re-run both gates.
4. Prefer a concise, reader-shaped document over maximum inclusion. Supported facts may remain in analysis/coverage rather than reader-facing prose when they are not needed by that audience, except material risks and consequential behavior.
5. Before final status, reread the three rendered drafts as a set and verify that each has a distinct purpose and does not merely repeat the others.


## V2 acceptance loop

For every fresh run:

1. Analyzer produces evidence and a decision-ready content plan.
2. Drafter creates `analysis/EDITORIAL-BLUEPRINT.md` before reader-facing prose, drafts from it, and completes the Draft challenge.
3. Proofreader checks source fidelity and blueprint compliance against the original source.
4. If review finds a supported, fixable editorial issue, revise from existing evidence and review again. Stop after two correction cycles and record unresolved material issues.
5. Run the structural checker after the final review cycle.

A run receives **solid-doc-set PASS** only when source fidelity, editorial/assignment fit, blueprint challenge, and structural checker all pass; reader-facing claims remain source-supported; contradictions remain unresolved; and publication blockers are separated from assignment readiness.

For regression testing, generate without using previously approved reader-facing articles as input. Compare the completed set with a benchmark only after generation, using reader goal, essential concept coverage, task completeness, release-note focus, unsupported claims, and material-risk handling. Exact wording is not required.


## V2.1 quality gates

A solid-doc-set PASS additionally requires:
- claim-admission audit PASS;
- no DIRECT uncertainty is presented as settled product behavior;
- ADJACENT uncertainty has an explicit INCLUDE/QUALIFY/DEFER/BLOCK decision;
- editorial restraint did not remove a material risk or prerequisite;
- no promotional wording introduces an unsupported benefit or guarantee.

When comparing regression runs, prefer evidence-safe improvement over similarity to the benchmark. A new run may legitimately choose a different title, structure, task route, or release-note priority when its source evidence and reader-job rationale are stronger.


## V2.2 advanced run contract

For every new full run, require these additional analysis artifacts:
- `analysis/TERMINOLOGY.md`
- `analysis/TRACEABILITY.json`
- `analysis/RISK-REVIEW.md`

The Analyzer creates their evidence/risk baseline. The Drafter updates admission destinations, examples, and topic ownership. The Proofreader independently audits all three against the original source.

A solid-doc-set PASS now requires:
- terminology/UI-label audit PASS;
- risk-weighted audit PASS for all material high-impact claims;
- example-safety audit PASS;
- cross-document ownership audit PASS;
- traceability manifest consistency PASS;
- an explicit readiness state, with PUBLICATION-READY forbidden while any material blocker remains.

### Regression rule

For a clean-room regression run, never read prior reader-facing outputs, prior blueprints, or prior QA before the new run is complete. Use a new output slug. After completion, comparison with earlier runs is allowed for evaluation only. Exact prose similarity is not a success criterion.


## Input-agnostic source package contract

The workflow accepts a single artifact or a mixed source package; PRD is only one possible source type. Require `analysis/SOURCE-INTAKE.md` for fresh runs.

Before claim analysis:
1. inventory every supplied artifact and its detected type/role;
2. record readability and review coverage;
3. distinguish current product evidence, prior documentation, contextual/support evidence, and unknown authority;
4. preserve per-claim provenance when combining sources;
5. detect UPDATE mode only from explicit version/current-prior relationships or the user's instruction, never from filename guessing.

The requested deliverable set is a target, not permission to invent. A required deliverable may be marked BLOCKED when the source package cannot establish the minimum evidence needed for an evidence-safe draft. The completion summary must distinguish a blocked deliverable from a workflow failure.

For visual-only evidence, visible state may support descriptive documentation, but interaction outcomes require additional evidence. For mixed-source contradictions, preserve both sides unless an explicit authority rule resolves precedence.
