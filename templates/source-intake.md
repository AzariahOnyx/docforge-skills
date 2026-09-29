# Source intake manifest

## Intake summary
- Invocation: [exact $demo-studio arguments]
- Source package root: [path or multiple paths]
- Input mode: [SINGLE / PACKAGE / UPDATE]
- Total artifacts: [count]
- Readability status: [PASS / PARTIAL / BLOCKED]

## Artifact inventory

| Source ID | Path | Detected type | Format | Authority role | Coverage | Limitations |
| --- | --- | --- | --- | --- | --- | --- |
| S01 | [path] | [PRD / REQUIREMENTS / ENGINEERING-SPEC / SUPPORT-CASE / RELEASE-BRIEF / SCREENSHOT / EXISTING-DOC / API-NOTES / MEETING-NOTES / OTHER] | [pdf/docx/md/txt/png/etc.] | [PRIMARY / SUPPORTING / PRIOR-DOC / UNKNOWN] | [pages/sections/images reviewed] | [none or issue] |

## Source relationships
Record explicit version relationships, attachments, references, or supersession only when supported. Do not invent precedence between conflicting sources.

## Evidence extraction notes
- Text sources: preserve headings, tables, notes, code, and appendices.
- Visual sources: record visible text, controls, states, relationships, and annotations separately from interpretation.
- Existing docs: treat as evidence of current documentation, not automatically as product truth.
- Meeting/support material: attribute statements to the artifact; do not silently promote them over formal requirements.

## Intake decision
- Documentation workflow can proceed: [YES / BOUNDED / NO]
- Update mode detected: [YES / NO]
- Missing/unreadable evidence: [items]
- Source-precedence question required: [YES / NO; why]
