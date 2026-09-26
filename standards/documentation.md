# Documentation standard

Apply this to any PRD. The source and the Analyzer handover determine product truth; this standard determines presentation.

## Evidence and scope

- In the handover, label each material claim FACT, ASSUMPTION, INFERENCE, UNKNOWN, or CONTRADICTION with a source location. A PRD FACT is a stated requirement, not proof of implemented behavior.
- Write unqualified product behavior in reader-facing docs only when the source supports it. Keep editorial assumptions and unresolved questions in review artifacts. Do not choose between contradictory requirements.
- Record CREATE, UPDATE, or DEFER in the content plan. Inspect actual existing documentation before naming an update target. If none was supplied, label proposed updates as candidates.
- After drafting, give every material handover claim exactly one row in `analysis/COVERAGE.md`: INCLUDED with a reader-facing destination, CONTEXT, DEFERRED, or BLOCKED with a reason. Review both the ledger and draft passages against the original source. A complete ledger alone does not establish source fidelity.
- For a revised PRD, compare the previous and new source versions in `analysis/CHANGE-IMPACT.md` before changing reader-facing text. Record added, changed, removed, resolved, and conflicting requirements, affected sections, CREATE/UPDATE/DEFER/RETIRE-CANDIDATE actions, and evidence. Keep the previous output intact. If the old source is missing, state that the comparison is unavailable.
- If a complete procedure lacks a verified starting point, action, or result, select another supported task or mark it blocked. Never fill in a UI click path.

## Feature guide: understand

- Lead with what the feature does and when it helps, then explain objects, relationships, states, important behavior, access, and limits.
- Group concepts by the reader's mental model. Link to supported tasks; avoid turning the whole article into one long procedure.
- Use a small Mermaid diagram only when source-backed relationships or transitions are clearer visually. Keep disputed edges out. Explain the diagram in nearby text and avoid product UI mockups that imply unverified controls.

## How-to: accomplish one goal

- Use an action title, short purpose, supported prerequisites, `## Steps` with numbered imperative actions, and a distinct `## Expected result`.
- Match every UI label and transition to the source. State a verified warning near the step it affects. Avoid unrelated background and unsupported recovery advice.

## Release note: notice the change

- Start with the capability and practical user effect. Keep the note short and scannable, with only the most important supported behaviors.
- State release date, platform, edition, rollout, migration, or permission details only when supplied by the source. Do not copy the feature guide or procedure.

## Style and review

- Use direct language, consistent source terminology, second person where useful, and bold for verified UI labels. Remove template placeholders and internal claim IDs from reader-facing articles.
- Check links, headings, accessibility of diagrams, grammar, duplication, and that each article serves its audience.
- The structural checker verifies files, headings, local links, ID references, and unique claim dispositions. The source-first Proofreader verifies meaning, coverage decisions, omissions, and publication risks. Record PASS, WARNING, or FAIL and distinguish an assignment-ready draft from publication-ready documentation.
