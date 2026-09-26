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
| Working assumption | Labeled ASSUMPTION and rationale only if needed; otherwise none. Never select a side of a contradiction. |
| Documentation impact | Affected topics or claims; whether to qualify, omit, or block them pending clarification. |

## Outputs

When invoked for analysis, produce these two files in the assignment's designated output location. Leave source files unchanged.

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

Before handing off, verify source coverage, citations, classification consistency, and matching IDs across outputs. Explicitly report incomplete analysis.
