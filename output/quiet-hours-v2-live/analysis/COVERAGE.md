# Quiet Hours — source-to-document coverage

## Claim coverage

Each current handover claim appears exactly once. The previous 1-hour direction is tracked as stale in CHANGE-IMPACT.md and does not appear as current product behavior.

| Claim ID | Disposition | Destination | Rationale / section | Related question |
| --- | --- | --- | --- | --- |
| C01 | INCLUDED | feature/feature-guide.md | Opening; revised assigned-item context | None |
| C02 | INCLUDED | feature/feature-guide.md; how-to/how-to.md; release-note/release-note.md | Personal in-app scope and exclusions | Q02 |
| C03 | INCLUDED | feature/feature-guide.md; how-to/how-to.md; release-note/release-note.md | Revised navigation and 2-hour / Until tomorrow choices | Q01 |
| C04 | INCLUDED | feature/feature-guide.md; how-to/how-to.md | Displayed end time and Resume now | None |
| C05 | INCLUDED | feature/feature-guide.md; how-to/how-to.md | Manual immediate resume, online requirement | None |
| C06 | INCLUDED | feature/feature-guide.md; how-to/how-to.md; release-note/release-note.md | Automatic resume at end; no added online condition | None |
| C07 | INCLUDED | feature/feature-guide.md; how-to/how-to.md | Pausing requires online connection | None |
| C08 | INCLUDED | feature/feature-guide.md; how-to/how-to.md | Signed-in self-service and admin restriction | None |
| C09 | BLOCKED | — | Until tomorrow timing and time zone unknown; do not define them. | Q01 |
| C10 | BLOCKED | — | Alert disposition during pause unknown. | Q02 |
| C11 | BLOCKED | — | Editing active period unknown. | Q03 |
| C12 | BLOCKED | — | Release metadata unavailable. | Q04 |

## Coverage review

- Claim register IDs: C01–C12, each accounted for once.
- Reader-facing passages without claim support: none identified; all copy maps to the revised-source claim register.
- High-risk stale content: previous 1-hour title/instructions are replaced with 2 hours in this new set; previous offline manual-resume unknown is updated to the explicit online requirement. Old files remain untouched.
- Blocked: Q01–Q04. No unsupported time, zone, alert-delivery, active-period-editing, or release claim appears.
- Reviewer result: PASS for source coverage with publication WARNING for Q01–Q04; see `qa/QA-REPORT.md`.
