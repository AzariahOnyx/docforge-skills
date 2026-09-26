# Quiet Hours — documentation handover

> Rehearsal artifact. `demo/mock-prd-v2.md` is fictional and is the sole product evidence for this set.

## Assignment scope

- Source: `demo/mock-prd-v2.md`, all sections inspected. No supporting images, existing help pages, style guide, or product build.
- Requested outputs: first-time-user feature guide, one-goal how-to, and scanning release note.
- Evidence status: FACT means stated in this PRD, not verified in a running product. No contradictory statements were found.

## Source inventory

| Source | Coverage | Authority / limit |
| --- | --- | --- |
| S1 `demo/mock-prd-v2.md` | Product context, Feature, UI and workflow, Permissions, Known gap, Release | Sole fictional practice source; no implementation verification. |

## Claim register

| ID | Class | Statement | Evidence / limit |
| --- | --- | --- | --- |
| C01 | FACT | Pulseboard is a team dashboard; members receive in-app alerts for assigned items. | S1, Product context |
| C02 | FACT | Quiet Hours pauses a member's own in-app alerts for a selected period; email alerts and other members' settings are unchanged. | S1, Feature |
| C03 | FACT | The path is Settings > Notifications > Quiet Hours; select Pause alerts, choose 2 hours or Until tomorrow, then Confirm. | S1, UI and workflow |
| C04 | FACT | The screen displays the selected end time and a Resume now action. | S1, UI and workflow |
| C05 | FACT | Resume now restarts in-app alerts immediately; they also resume automatically when the selected period ends. | S1, UI and workflow |
| C06 | FACT | Pausing is available only while online. | S1, UI and workflow |
| C07 | FACT | Any signed-in member can change their own setting; an admin cannot change another member's setting. | S1, Permissions |
| C08 | UNKNOWN | Until tomorrow has no defined time of day or time zone. | S1, Known gap |
| C09 | UNKNOWN | The PRD does not define whether alerts that arise during a pause are discarded or delivered later. | S1, Feature and UI and workflow do not specify this. |
| C10 | UNKNOWN | Changing the selected period during an active pause is not specified. | S1, Known gap |
| C11 | UNKNOWN | Release date, platform list, and rollout plan are absent. | S1, Release |
| C12 | FACT | Resume now requires an online connection. | S1, UI and workflow |

## Product model

- **Reader goal and scope:** A signed-in member pauses only their own in-app alerts; email and other members' settings are unaffected (C01-C02, C07).
- **Procedure:** The named settings path, Pause alerts, 2 hours/Until tomorrow, and Confirm are supported (C03). The screen shows the end time and Resume now (C04).
- **Lifecycle:** Resume now or the selected period's end restarts in-app alerts (C05). Pausing and Resume now require a connection (C06, C12); mid-pause period changes remain unknown (C10). Do not infer connectivity requirements for automatic expiry.
- **Limits:** Until tomorrow's boundary is unknown (C08). Backlog delivery and release metadata are unknown (C09, C11).

## Clarifications and contradictions

| ID | Topic | Evidence IDs | Draft impact |
| --- | --- | --- | --- |
| Q01 | Until tomorrow boundary | C03, C04, C08 | Name the option but do not assert a clock time or time zone; choose 2 hours for the how-to. |
| Q02 | Alerts during pause | C02, C05, C09 | Do not state whether missed alerts appear later. |
| Q03 | Active pause changes | C10, C12 | Resume now's online requirement is resolved; replacement behavior remains unspecified. |
| Q04 | Release metadata | C11 | Omit date, platforms, and rollout assertions. |

No source contradiction was found. See `clarifications-and-assumptions.md` for questions and editorial working assumptions; see `CONTENT-PLAN.md` for destinations and deferred scope.

## Documentation plan

| Deliverable | Goal | Supported IDs | Blocked claims |
| --- | --- | --- | --- |
| Feature guide | Understand what Quiet Hours affects and how it ends | C01-C07, C12 | Q01-Q03 |
| How-to | Pause own in-app alerts for 2 hours | C03-C07, C12 | Do not use Until tomorrow due to Q01 |
| Release note | Scan the new capability | C02-C07, C12 | Q01, Q04 |

## Drafter guidance

- Use only S1 as product evidence. Do not cross-contaminate with the Tracks PRD.
- Keep the how-to to a single 2-hour goal and give a separate Expected result heading.
- State that Resume now requires online access; do not infer exact Until tomorrow timing, alert backlog, mid-pause changes, or release metadata.
- Publication readiness requires answers to Q01-Q04 for affected topics; the selected 2-hour procedure is source-supported.

## Draft claim map (review-only)

- `feature/feature-guide.md`: C01-C07, C12; boundaries C08-C10.
- `how-to/how-to.md`: C03-C07, C12.
- `release-note/release-note.md`: C02-C07, C12; excludes C11.
