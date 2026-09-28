# Documentation standard

Apply this to any PRD. The source and the Analyzer handover determine product truth; this standard determines presentation.

Use the [Microsoft Writing Style Guide](https://learn.microsoft.com/en-us/style-guide/welcome/) (the current online successor to MSTP) for general English, capitalization, procedures, and UI references. The source's verified product terminology and the repository's explicit rules take precedence when they differ. Do not treat a Microsoft style example as evidence of this product's behavior.

## Evidence and scope

- In the handover, label each material claim FACT, ASSUMPTION, INFERENCE, UNKNOWN, or CONTRADICTION with a source location. A PRD FACT is a stated requirement, not proof of implemented behavior.
- Write unqualified product behavior in reader-facing docs only when the source supports it. Keep editorial assumptions and unresolved questions in review artifacts. Do not choose between contradictory requirements.
- Prefer source pages or section names that remain stable across edits. If using Markdown line numbers, check the numbered source at the time of drafting and proofreading; the line must contain the supporting passage. Recheck after source changes. A valid nonblank line alone does not prove the claim.
- Record CREATE, UPDATE, or DEFER in the content plan. Inspect actual existing documentation before naming an update target. If none was supplied, label proposed updates as candidates.
- After drafting, give every material handover claim exactly one row in `analysis/COVERAGE.md`: INCLUDED with a reader-facing destination, CONTEXT, DEFERRED, or BLOCKED with a reason. Review both the ledger and draft passages against the original source. A complete ledger alone does not establish source fidelity.
- For a revised PRD, compare the previous and new source versions in `analysis/CHANGE-IMPACT.md` before changing reader-facing text. Record added, changed, removed, resolved, and conflicting requirements, affected sections, CREATE/UPDATE/DEFER/RETIRE-CANDIDATE actions, and evidence. Keep the previous output intact. If the old source is missing, state that the comparison is unavailable.
- If a complete procedure lacks a verified starting point, action, or result, select another supported task or mark it blocked. Never fill in a UI click path.
- For each clarification, state the safe editorial assumption or documentation decision used to finish the draft and its impact. Distinguish that choice from an unverified product assumption. Never use an assumption to decide a contradiction. If no assumption is needed, explain the deliberate omission or qualification instead of writing only "None."
- Keep unresolved source disputes, claim IDs, and editorial notes in analysis and QA. Omit the disputed outcome from reader-facing content; if omission would hide a material safety or data-loss risk, block that article for publication until resolved.

## Reader-first editorial rules

- Give each document a distinct reader goal. Use an informative, sentence-case title that says what the reader will learn, do, or gain; avoid a bare feature name unless a site-level title convention requires it. Do not add a version, date, or "now available" without release evidence.
- Lead with the answer or user benefit. Use short, active sentences and familiar words. Prefer "You can ..." or a direct action to "the feature enables/allows/lets users to ..." when natural. Cut repetition and promotional claims.
- Match verified UI labels exactly, including capitalization, and bold actionable labels. Do not invent control names, screen paths, defaults, availability, or error messages. Use one term per concept; flag inconsistent source terms for clarification.
- Use descriptive link text, consistent parallel list items, and accessible table headings. Give a diagram nearby explanation and text alternatives; add it only when a source-backed relationship or branch is easier to understand visually. Never imply an unverified transition with an arrow.

## Feature guide: understand

- Lead with what the feature does and when it helps, then explain objects, relationships, states, important behavior, access, and limits. A descriptive title should identify the capability and user purpose.
- Group concepts by the reader's mental model. Link to supported tasks; avoid turning the whole article into one long procedure.
- Cover high-impact behavior and limits that a first-time user needs; do not turn an internal contradiction into a customer-facing paragraph. Keep disputed details out and record a publication blocker in QA if the omission makes the article unsafe.
- Use a small Mermaid diagram only when source-backed relationships or transitions are clearer visually. Keep disputed edges out. Explain the diagram in nearby text and avoid product UI mockups that imply unverified controls.

## How-to: accomplish one goal

- Use an action title, short purpose, supported prerequisites, `## Steps` with numbered imperative actions, and a distinct `## Expected result`.
- Choose a consequential, representative task with a supported starting point, user action, and observable result. Prefer a state-changing task over merely opening a view when both are equally well supported. A viewing task is valid when the source does not support a complete substantive procedure or viewing is the assigned goal; explain the selection in the content plan.
- Match every UI label and transition to the source. State a verified warning near the step it affects. Avoid unrelated background and unsupported recovery advice.
- Keep one action per step where practicable. Do not turn a concept or feature list into steps; do not infer what a Start or Stop action does beyond the source's stated outcome.

## Release note: notice the change

- Write for an existing user scanning what changed. Use a change-focused title with a concrete action or user outcome, a short benefit statement, and two or three distinct, high-value new capabilities or effects. Contrast with previous behavior only if the baseline is documented.
- Choose the capabilities that distinguish the change, rather than restating the feature guide's introduction. Link to the guide for details. Do not turn the note into a procedure or include unverified launch claims.
- State release date, platform, edition, rollout, migration, or permission details only when supplied by the source. Do not copy the feature guide or procedure.

## Style and review

- Use direct language, consistent source terminology, second person where useful, and bold for verified UI labels. Remove template placeholders and internal claim IDs from reader-facing articles.
- Check links, headings, accessibility of diagrams, grammar, duplication, and that each article serves its audience.
- Before QA passes, compare every sentence and meaningful omission in each reader-facing draft with the original source. Audit titles, benefits, prerequisites, actions, outcomes, permissions, destructive effects, offline behavior, and the difference between PRD intent and shipped behavior. Record exact source locations for any correction.
- Run a separate editorial gate: Does the feature guide orient a newcomer? Does the how-to accomplish a substantial supported goal? Does the release note announce what changed for an existing user? If a document is accurate but weak for its audience, revise it and recheck evidence; structural success alone does not pass this gate.
- The structural checker verifies files, headings, local links, ID references, unique claim dispositions, and recognizable Markdown line citations that point to existing nonblank lines. The source-first Proofreader verifies the cited text's meaning, coverage decisions, omissions, and publication risks. Record PASS, WARNING, or FAIL and distinguish an assignment-ready draft from publication-ready documentation.
