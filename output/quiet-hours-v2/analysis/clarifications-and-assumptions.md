# Quiet Hours — clarifications and working assumptions

The mock PRD is the only evidence. Each assumption below is editorial and does not assert product behavior.

## Q01 — Until tomorrow boundary

- **Classification:** UNKNOWN.
- **Evidence:** `demo/mock-prd-v2.md`, UI and workflow names Until tomorrow and says the screen displays an end time; Known gap explicitly leaves time of day and time zone undefined (C03, C04, C08).
- **Question:** Which time zone and exact time define the end of Until tomorrow?
- **Why it matters:** A user could plan around a false deadline.
- **Working assumption:** ASSUMPTION (editorial): use the 2 hours option in the how-to; mention Until tomorrow only by its label, without an exact end time.
- **Documentation impact:** Block an exact Until tomorrow example or instruction until clarified.

## Q02 — Alerts that arise during a pause

- **Classification:** UNKNOWN.
- **Evidence:** `demo/mock-prd-v2.md`, Feature and UI and workflow describe pausing and resuming but not backlog handling (C02, C05, C09).
- **Question:** Are in-app alerts created during the pause discarded, retained, or delivered on resume?
- **Why it matters:** Users may expect to recover missed alerts.
- **Working assumption:** ASSUMPTION (editorial): omit backlog claims.
- **Documentation impact:** No promise about later delivery.

## Q03 — Active pause changes

- **Classification:** UNKNOWN.
- **Evidence:** `demo/mock-prd-v2.md`, UI and workflow explicitly requires online access for Resume now (C12); Known gap does not define changes to an active period (C10).
- **Question:** Can a member replace a current pause with a different duration?
- **Why it matters:** This affects editing steps and recovery guidance.
- **Working assumption:** ASSUMPTION (editorial): state the supported online requirement for Resume now, and omit mid-pause editing guidance.
- **Documentation impact:** The prior offline-resume question is resolved by C12. Defer only edit-active-pause procedures.

## Q04 — Release metadata

- **Classification:** UNKNOWN.
- **Evidence:** `demo/mock-prd-v2.md`, Release says no date, platform list, or rollout plan is supplied (C11).
- **Question:** When and where is Quiet Hours available?
- **Why it matters:** Release notes usually need availability.
- **Working assumption:** ASSUMPTION (editorial): omit release metadata.
- **Documentation impact:** Keep the note to source-supported capabilities.
