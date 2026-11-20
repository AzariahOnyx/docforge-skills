---
feature: [Feature name as readers see it]
mode: Net-New            # Net-New or Enhancement
product: [product key]
category: [category the new articles belong to]
owner: unknown           # the owning writer, or unknown
source_prs: []           # owner/repo#123 entries, or []
engineering_spec: none   # path or link to spec.md, or none
release: unknown         # release name or YYYY-MM, or unknown
jira: none               # optional: ticket key, or none
docforge_run: [run name] # optional
decision: act            # optional: act or confirm, and decision_reason: one sentence
status: proposed         # optional: proposed; only a writer (or approving the pull request) makes it approved
---

# IA plan: [Feature name]

> Drafted by DocForge for writer review. A writer may add, remove or correct rows before approving the pull request; DocForge drafts from the approved version. Keep the table columns as they are: DocForge reads this file back.

## Existing articles - impact

| Article | Docs path | Action | Change needed | Outdated passage | Evidence |
| --- | --- | --- | --- | --- | --- |
| [Existing article title] | [docs path of the existing article] | update | [what changes for readers] | [the exact sentence that is now wrong] | C04, C07 |

## New articles

| Title | Type | Docs path | Why | Evidence |
| --- | --- | --- | --- | --- |
| [Article title] | [article type, for example procedural] | [docs path] | [reader goal it serves] | C06, C08 |

## Out of scope

| Topic | Reason |
| --- | --- |
| [Topic not documented now] | [why: unsupported, internal, deferred] |

## Open questions

| ID | Question | Why it matters |
| --- | --- | --- |
| Q01 | [question for the PM or engineer] | [what the answer changes in the docs] |

## Spec-versus-code conflicts

| ID | Spec says | Code says | Where | Question |
| --- | --- | --- | --- | --- |
| X01 | [what the spec states] | [what the code does] | [spec section; code file and line] | [which behavior is intended?] |

<!--
One plan format for every route: DocForge's engine and the docs-writer agent write the same file.
Rules:
- A section with nothing in it holds the single line "None." instead of a table.
- Action (existing articles): update, archive or none. "Outdated passage" quotes the published sentence
  that is now wrong, word for word (empty when the article only needs an addition).
- Type (new articles): one of the article types the run's pack defines (without a pack: overview, procedural,
  release-notes).
- Docs path: a relative .md path in the docs repository, unique in the plan, inside the doc collection's filter.
- Evidence: claim IDs from the handover (C03), or source tags (SPEC:<section>, CODE:<path>:<line>), or none.
- Open questions use the IDs of the clarification register; conflicts use X IDs. Without a code comparison,
  the conflicts section says "None. No code was compared."
- The first DocForge format (Change / Why / Claims columns) is still read.
-->
