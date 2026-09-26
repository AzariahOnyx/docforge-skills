# [Feature] — source-to-document coverage

> Review artifact. Create after drafting; the Proofreader validates every disposition against the source and drafts.

## Claim coverage

List every material claim ID in HANDOVER.md exactly once. Use INCLUDED when a claim appears in one or more reader-facing drafts, CONTEXT when it informs analysis but is not useful to those readers, DEFERRED when a supported topic is out of the requested scope, or BLOCKED when an unknown or contradiction prevents a safe claim. For each INCLUDED row, name a destination and section; for the other statuses, explain the reason. Do not treat a PRD fact as implementation verification.

| Claim ID | Disposition | Destination | Rationale / section | Related question |
| --- | --- | --- | --- | --- |
| C01 | INCLUDED | feature/feature-guide.md | Overview; source-backed scope | None |

For CONTEXT, DEFERRED, or BLOCKED use an em dash in Destination and put the reason in Rationale / section.

## Coverage review

- Missing or duplicated claim IDs: [none or list]
- Reader-facing passages without a supporting claim ID: [none or list]
- High-risk omissions or blocked topics: [Q IDs, reason, destination if later resolved]
- Reviewer result: [PASS / WARNING / FAIL, source-first rationale]
