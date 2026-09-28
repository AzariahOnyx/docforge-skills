---
name: analyzer
description: Analyze any PRD and supporting artifacts before documentation drafting, producing an evidence-based handover and a clarifications and assumptions register.
---

# Analyzer

Perform the analysis stage of Analyzer → structured handover → Drafter → independent Proofreader. Do not draft product documentation or run downstream stages.

## Source review

1. Accept the supplied PRD, supporting artifacts, and assignment requirements. Follow repository source-authority rules; here, `input/` contains the authoritative PRD and supporting artifacts.
2. Inventory and read all sources in full, including tables, diagrams, notes, and appendices. Inspect visual content when extraction omits meaning. Record unreadable or inaccessible portions and their effect on coverage; never claim full review when incomplete.
3. Cite relevant claims using source paths and page and/or section locators, adding table, figure, or line references where useful. For missing information, cite relevant sections reviewed and explain what they do not establish.
4. Prefer stable section or page locators. If exact Markdown line numbers are useful, inspect the numbered source (for example, `nl -ba <source>`) immediately before writing the citation. Verify that the cited line contains the supporting text; do not cite a heading or blank line as if it proves a behavior. Use `path.md, line N` or `path.md, lines N-M` consistently and recheck after source edits.

## Claim classification

- **FACT:** Explicitly stated in a source; not independent verification of implemented behavior.
- **ASSUMPTION:** An unconfirmed working premise introduced to proceed; explain why it is needed.
- **INFERENCE:** A conclusion derived from cited facts; record reasoning and uncertainty.
- **UNKNOWN:** Information the supplied sources do not establish.
- **CONTRADICTION:** Incompatible source claims; preserve and cite each side separately.

Classify every relevant claim. Never invent product behavior or promote assumptions or inferences to facts. Never decide between contradictory claims or silently reconcile them. Do not use a working assumption to choose a side; leave affected behavior unresolved.

## Analysis coverage

Analyze these areas where applicable and connect findings to documentation needs:

- Product model: entities, relationships, hierarchy, scope, and invariants.
- Users: audiences, roles, goals, and responsibilities.
- Terminology: definitions, UI labels, aliases, and inconsistencies.
- Permissions: who can view or act on which objects and under what conditions.
- States and lifecycle: creation, transitions, completion, retention, and end states.
- Workflows: prerequisites, entry points, steps, outcomes, exceptions, and recovery.
- Destructive actions: scope, consequences, dependencies, confirmation, and reversibility.
- Offline behavior: availability, synchronization, conflicts, and recovery.
- Limitations: constraints, exclusions, dependencies, and unsupported cases.
- Documentation implications: topics, warnings, prerequisites, examples, and claims blocked by missing evidence.

Distinguish inapplicable topics from unknown behavior. This checklist is not evidence that a feature exists.

## Material-gap register

For every material gap, record:

| Field | Content |
| --- | --- |
| ID | Stable identifier shared across outputs. |
| Classification | Applicable claim classification. |
| Evidence | Source locations and relevant claims; both sides of contradictions. |
| Question | Specific clarification needed. |
| Why it matters | Consequence for users, product understanding, or the assignment. |
| Working assumption | State the editorial assumption or safe documentation decision taken to complete the drafts, its rationale and limits. Label an unverified product premise ASSUMPTION only if necessary. Never select a side of a contradiction; explain what was omitted, qualified, or blocked rather than writing only "None." |
| Documentation impact | Affected topics or claims; whether to qualify, omit, or block them pending clarification. |

## Outputs

When invoked for analysis, produce these three files in the assignment's `analysis/` output directory. Leave source files unchanged. Read `templates/handover.md` and `templates/content-plan.md` as adaptable structures.

### HANDOVER.md

Structure the handover for the Drafter as follows:

1. Assignment scope, audience, requested deliverables, and constraints.
2. Source inventory, authority, review coverage, and extraction limitations.
3. Claim register: claim IDs, classifications, statements, evidence, and reasoning for inferences.
4. Product analysis by applicable coverage area, referencing claim IDs.
5. Gaps and contradictions linked by ID to the clarification register, preserving both conflicting claims.
6. Documentation plan: proposed topics, supporting evidence, and unresolved dependencies; distinguish supported content from content needing clarification.
7. Drafter guidance: terminology, working assumptions, unsupported claims to avoid, and readiness or blockers. Preserve unresolved items for independent proofreading.

### clarifications-and-assumptions.md

Provide the assignment's clarification register using every material-gap field above. Include all working assumptions, their rationale, evidence limits, and documentation impact. Reuse IDs from the handover. Keep unanswered questions and contradictions unresolved; never supply invented answers.

Before handing off, verify source coverage, every cited location against the actual source, classification consistency, and matching IDs across outputs. Explicitly report incomplete analysis.

### CONTENT-PLAN.md

Inventory supplied existing documentation, if any. For each topic, record its reader goal, proposed action (CREATE, UPDATE, or DEFER), destination, supporting claim IDs, open question IDs, and reason. If existing documentation was not supplied, mark its existence UNKNOWN and label update candidates as proposed, not confirmed edits. Link each of the three required drafts to a supported reader goal. Recommend a diagram only when relationships, flow, or state changes are clearer visually; use source-backed nodes and transitions, and flag unverified edges. Distinguish a content plan from an instruction to invent new product behavior.
For the how-to, compare supported task candidates and select a consequential action with a verifiable outcome when possible; record why a view-only task was selected if one is used. For the release note, identify the two or three most consequential supported changes for an existing user, without inventing a previous-state comparison or release metadata.
## Editorial planning gate

Before handing off to the Drafter, evaluate supported material for reader value, not only evidence coverage.

- For each proposed reader-facing topic, classify its relevance as **ESSENTIAL**, **USEFUL**, **EDGE CASE**, or **REFERENCE CANDIDATE** for that document's audience. Evidence support determines what may be said; audience relevance determines what should be said.
- Do not force every supported fact into a reader-facing draft. Keep low-value edge cases in analysis unless they materially affect success, safety, data loss, permissions, or irreversible behavior.
- Reconstruct the reader's mental model from verified facts instead of preserving the PRD's order or wording.
- For each how-to candidate, assess **user value, task substance, consequence, evidence completeness, audience fit, and assignment fit**. A short procedure is acceptable only when the requested task is genuinely narrow. If the assignment requires a substantial task and no substantial task is fully supported, record that limitation instead of presenting a trivial task as fully satisfying the requirement.
- For release notes, identify the supported change and user impact separately from feature-description facts. Do not invent a previous-state baseline.
- Classify destructive or consequential behavior as informational, state-changing, destructive, irreversible, or data-loss risk so the Drafter can give it appropriate prominence.


## Decision-ready editorial handoff

Before handoff, make the content plan executable by the Drafter:

- Rank how-to candidates. A complete candidate needs a supported starting state, user action or control, and observable result.
- Identify 3–7 essential newcomer concepts for the feature guide separately from secondary or reference material. Do not preserve PRD order by default.
- Identify material permission, lifecycle, offline, cross-scope, irreversible, and data-retention consequences that must survive editorial compression.
- Rank release-note candidates by practical user impact and distinctiveness. Select no more than three unless the assignment requires more.
- State what each deliverable should deliberately exclude so the three outputs retain distinct reader purposes.


## Uncertainty-neighborhood map

Do not treat gaps as isolated rows. Before handoff, map each CONTRADICTION, UNKNOWN, and material INFERENCE to the supported FACT claims in the same behavioral neighborhood: the same action, object, state, permission, lifecycle, destructive outcome, offline flow, or release assertion.

For each neighboring FACT, mark whether the gap is:
- **DIRECT:** the FACT itself cannot be stated safely without resolving the gap.
- **ADJACENT:** the FACT is independently supported, but wording could imply the unresolved surrounding behavior is settled.
- **NONE:** the gap does not materially change how the FACT should be documented.

Feed DIRECT and ADJACENT relationships into the editorial blueprint's claim-admission gate. This map is for editorial risk control; it must not turn proximity into a contradiction or suppress unrelated facts.


## V2.2 evidence engineering artifacts

For new runs, also create these analysis artifacts before drafting:

1. **TERMINOLOGY.md** from `templates/terminology-ledger.md`. Extract canonical product terms and exact UI labels, their source locations, aliases, and conflicts. A label conflict remains unresolved; do not normalize it by preference.
2. **TRACEABILITY.json** from `templates/traceability-manifest.json`. Represent the same HANDOVER claim register in machine-readable form: claim ID, classification, source locator, risk, uncertainty proximity, admission decision, destinations, blocker IDs, source set, and readiness. HANDOVER remains the human-readable authority; the JSON is an audit projection and must not introduce claims.
3. **RISK-REVIEW.md** from `templates/risk-review.md`. Seed high-impact claims and risk types for independent review.

Assign review intensity by consequence, not by model confidence. Mark destructive, irreversible, data-loss/retention, access/permission, security/privacy, migration, billing, offline/conflict, and release-expectation claims for mandatory source recheck. Do not convert risk severity into truth confidence.
