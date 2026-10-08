# Documentation standard

Apply this to any PRD. The source and the Analyzer handover determine product truth; this standard determines presentation.

## Evidence and scope

- In the handover, label each material claim FACT, ASSUMPTION, INFERENCE, UNKNOWN, or CONTRADICTION with a source location. A PRD FACT is a stated requirement, not proof of implemented behavior.
- Write unqualified product behavior in reader-facing docs only when the source supports it. Keep editorial assumptions and unresolved questions in review artifacts. Do not choose between contradictory requirements.
- Prefer source pages or section names that remain stable across edits. If using Markdown line numbers, check the numbered source at the time of drafting and proofreading; the line must contain the supporting passage. Recheck after source changes. A valid nonblank line alone does not prove the claim.
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
- The structural checker verifies files, headings, local links, ID references, unique claim dispositions, and recognizable Markdown line citations that point to existing nonblank lines. The source-first Proofreader verifies the cited text's meaning, coverage decisions, omissions, and publication risks. Record PASS, WARNING, or FAIL and distinguish an review-ready draft from publication-ready documentation.

## Generalized documentation types

The three document types above are the default profile, not a mandatory package. For an API reference, use a verified contract or implementation evidence to document paths, methods, authentication, parameters, request and response bodies, errors, and examples; omit unsupported fields. For troubleshooting, require a reproducible symptom, supported diagnostic steps, a confirmed or clearly qualified resolution, and a safe recovery boundary. For migration or upgrade instructions, require verified version prerequisites, compatibility, data-impact and rollback information before publishing actionable steps. For conceptual or architecture documentation, distinguish documented components and relationships from illustrative proposals. Each custom type must have a source-backed structure and acceptance criteria in the content plan.

## Style, accessibility, and technical checks

Apply the supplied house style first. In its absence, use the principles of the [Microsoft Writing Style Guide](https://learn.microsoft.com/en-us/style-guide/welcome/) and the [Google developer documentation style guide](https://developers.google.com/style), without claiming certification or exhaustive compliance.

- Prefer short, direct sentences, parallel lists, descriptive headings, and task-oriented titles. Use consistent terminology and UI capitalization; do not invent a UI control to improve prose.
- Use imperative verbs for procedure steps. Keep each step focused on one meaningful action, and state prerequisites, warnings, and expected results when source-supported. Do not assume a mouse, keyboard, touch screen, or visual-only interaction where a neutral verb such as **select** works.
- Use meaningful link text rather than “click here.” Give informative images and diagrams text alternatives or adjacent explanations; label tables clearly and avoid using layout tables as substitutes for headings.
- For code, commands, API payloads, and configuration, verify syntax and examples against authoritative source material or actual test results. Label pseudocode, illustrative values, and unexecuted examples explicitly.
- Check localization readiness: avoid ambiguous dates, units, time zones, idioms, and culturally dependent examples. Never guess a missing time zone or unit.
- Check for unsafe or irreversible actions, credential exposure, privacy risks, and unverified rollback steps. Do not imply an action is reversible unless supported.
- Distinguish editorial quality, source fidelity, technical verification, accessibility review, and publication approval in the QA report; a pass in one category does not imply a pass in the others.
