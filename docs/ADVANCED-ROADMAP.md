# Advanced roadmap

This roadmap extends the reusable documentation system only where the change improves evidence safety, editorial judgment, maintainability, or regression confidence. Do not add features merely to make the workflow look more complex.

## Near-term

### 1. Claim-admission and uncertainty-neighborhood gate — implemented in V2.1
Separate “supported” from “worth publishing.” FACT claims near unresolved behavior receive INCLUDE, QUALIFY, DEFER, or BLOCK treatment based on reader value and consequence.

### 2. Cross-PRD regression corpus
Add small synthetic PRDs that deliberately exercise:
- contradictory lifecycle rules;
- missing permission for a destructive action;
- incomplete procedure outcome;
- offline/concurrency conflict;
- ambiguous terminology;
- release note with missing launch metadata;
- revised PRD that removes or changes an earlier behavior.

Each fixture should define expected evidence classifications and safety invariants, not expected prose. This tests reasoning without overfitting wording.

### 3. Documentation diff / change-impact engine
For revised requirements, make CHANGE-IMPACT a first-class gate. Compare claim IDs semantically: added, changed, removed, resolved, newly contradictory. Then identify affected reader-facing sections and stale claims before rewriting. Never silently carry old behavior forward.

### 4. Traceability manifest
Generate a machine-readable manifest alongside COVERAGE, for example JSON, containing claim ID, classification, source locator, document disposition, destination and blocker IDs. Use it for tooling and audits while Markdown remains the human review surface. The manifest must be generated from the same claim register, not become a competing source of truth.

## Medium-term

### 5. Risk-weighted review
Assign review intensity by consequence. Destructive, irreversible, access/security/privacy, migration, billing, data-retention and offline-conflict claims receive mandatory source recheck and nearby warning review. Low-risk descriptive claims receive normal review. Risk changes review depth, not truth classification.

### 6. Terminology and UI-label ledger
Extract canonical product terms and exact UI strings from sources, record aliases/conflicts, and lint reader-facing docs for inconsistent terminology. Never “correct” a source label without evidence.

### 7. Information-architecture / duplication matrix
Measure topic ownership across the doc set. Flag when the same substantial explanation appears in several deliverables or when no document owns an essential concept. Use semantic review rather than naive text matching.

### 8. Example safety gate
Classify examples as SOURCE, BEHAVIOR-NEUTRAL, or PRODUCT-BEHAVIOR. PRODUCT-BEHAVIOR examples require the same evidence as ordinary claims. This prevents plausible examples from becoming accidental specifications.

### 9. Release-readiness contract
Separate four states: DRAFTABLE, ASSIGNMENT-READY, REVIEW-READY, PUBLICATION-READY. Define required evidence for each. A polished release note without confirmed rollout metadata can pass assignment review while remaining blocked for publication.

## Later / optional

### 10. Multi-reviewer adversarial mode
When runtime supports independent agents, use distinct roles: Evidence Reviewer, Task/Procedure Reviewer, Senior Editorial Reviewer, and Final Integrator. Reviewers should receive source + draft independently where practical, then reconcile findings. Do not simulate independence by copying the Drafter's reasoning as reviewer evidence.

### 11. Confidence calibration dashboard
Report counts of FACT/INFERENCE/UNKNOWN/CONTRADICTION, admitted/deferred/blocked claims, open material questions and high-risk claims. These are diagnostics, not a numeric “documentation quality score.”

### 12. Source-change watch mode
When a new PRD revision is supplied, run impact analysis against the prior source and outputs, preserving the old set. Produce proposed updates and blockers before editing. This is a documentation maintenance workflow, not only a take-home generator.

### 13. Pluggable house-style profiles
Keep evidence and editorial logic universal, but allow presentation profiles (Microsoft-style default, organization-specific terminology/metadata/templates) to be selected without changing product truth rules.

### 14. Packaging and audit manifest
At completion, record source filenames/hashes, skill/standard commit SHA, generated paths, checker result, unresolved blockers and readiness state. Avoid volatile fields when deterministic regression comparison matters.

## Design guardrails

- Do not add an automatic numeric quality score that can hide a material failure.
- Do not use LLM self-confidence as evidence confidence.
- Do not let a linter decide product truth.
- Do not optimize regression tests for exact prose.
- Do not make every run longer: use risk to decide review depth.
- Preserve source-first human inspectability even when machine-readable artifacts are added.
