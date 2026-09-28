# [Feature] — editorial blueprint

> Internal drafting artifact. Build this before reader-facing prose. It is a decision record, not product documentation.

## Document contracts

| Deliverable | Primary reader | Reader job | One-sentence promise | Must include | Must exclude / defer | Success test |
| --- | --- | --- | --- | --- | --- | --- |
| Feature guide | [reader] | [understand...] | [what this guide will make clear] | [essential concepts/consequences] | [reference/edge/internal detail] | [what a first-time user should understand after reading] |
| How-to | [reader] | [accomplish...] | [specific supported outcome] | [prerequisites/actions/result] | [background/unverified steps] | [observable completion test] |
| Release note | [reader] | [scan what changed] | [change + practical impact] | [2–3 distinguishing changes] | [procedure/reference detail/unverified release metadata] | [what an existing user should notice in <30 seconds] |

## Feature-guide blueprint

- Core mental model: [2–4 sentences derived only from supported claims]
- Essential claim IDs: [IDs]
- Material consequences / risks that must remain visible: [IDs / Q IDs]
- Useful but secondary claim IDs: [IDs]
- Edge/reference claims to omit or defer: [IDs + reason]
- Planned section sequence:
  1. [reader question answered]
  2. [reader question answered]
  3. [reader question answered]
- Duplication to avoid: [what belongs in how-to/release note instead]

## How-to selection

| Candidate task | User value | Consequence | Evidence completeness: start/action/result | Assignment fit | Decision |
| --- | --- | --- | --- | --- | --- |
| [task] | High/Medium/Low | [state change/view/destructive] | Complete/Incomplete + IDs | Strong/Acceptable/Weak | SELECT / REJECT + reason |

Selected task: [one task]

- Verified starting state: [claim IDs]
- Verified user actions and exact UI labels: [claim IDs]
- Verified observable result: [claim IDs]
- Supported reversal/recovery, if any: [claim IDs or none]
- Explicitly excluded steps/outcomes: [unsupported items]
- Substantiality note: [why this is appropriate; if narrow because evidence is limited, say so]

## Release-note blueprint

- Supported change: [what the source establishes without inventing a before-state]
- Practical user impact: [supported impact]
- Priority 1: [capability/effect + claim IDs]
- Priority 2: [capability/effect + claim IDs]
- Priority 3: [optional capability/effect + claim IDs]
- Release metadata intentionally omitted: [unknown date/version/rollout/platform/etc.]
- Details delegated to feature guide: [topics]

## Cross-document separation

| Information | Feature guide | How-to | Release note | Reason |
| --- | --- | --- | --- | --- |
| [topic] | PRIMARY / BRIEF / OMIT | PRIMARY / BRIEF / OMIT | PRIMARY / BRIEF / OMIT | [reader need] |

## Claim-admission gate

Evaluate every candidate reader-facing claim that is essential, consequential, or near an unresolved gap.

| Claim / claim ID | Evidence | Reader value | Uncertainty proximity | Harm if misunderstood | Decision | Treatment |
| --- | --- | --- | --- | --- | --- | --- |
| [claim] | FACT / other | Essential / Useful / Low | None / Adjacent / Direct | Low / Medium / High | INCLUDE / QUALIFY / DEFER / BLOCK | [where/how or why omitted] |

Decision rules:
- INCLUDE only when evidence is FACT, reader value justifies space, and nearby uncertainty does not make the wording misleading.
- QUALIFY when the supported core is useful but scope, permission, lifecycle, availability, or an adjacent condition remains unresolved. State only the supported boundary; do not expose internal uncertainty language to readers.
- DEFER supported facts that are low-value, reference-heavy, or adjacent to unresolved behavior when omission is safe.
- BLOCK when omission or qualification would hide a material destructive, irreversible, security, privacy, data-loss, or task-success risk.
- A FACT is eligible evidence, not an automatic instruction to publish it.
- Never use reader value to promote ASSUMPTION, INFERENCE, UNKNOWN, or CONTRADICTION to product fact.

## Pre-draft challenge

Before drafting, answer all of these:

- Can every must-include item be traced to FACT evidence?
- Is any contradiction being silently resolved? If yes, stop and fix the blueprint.
- Does the feature guide have a reader-shaped mental model rather than PRD order?
- Does the how-to have a verified start, action, and observable result?
- Are the release-note priorities distinct from a feature-guide summary?
- Are destructive, irreversible, permission, lifecycle, and data-loss consequences prominent when material?
- Can any planned section be removed without harming the reader's job? If yes, remove or defer it.

Blueprint status: [PASS / BLOCKED, with Q IDs]
