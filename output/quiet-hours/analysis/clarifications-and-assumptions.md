# Quiet Hours — clarifications and working assumptions

The mock PRD is the only evidence. Each assumption below is editorial and does not assert product behavior.

## Q01 — Until tomorrow boundary

- **Classification:** UNKNOWN.
- **Evidence:** `demo/mock-prd.md`, UI and workflow names Until tomorrow and says the screen displays an end time; Known gap explicitly leaves time of day and time zone undefined (C03, C04, C08).
- **Question:** Which time zone and exact time define the end of Until tomorrow?
- **Why it matters:** A user could plan around a false deadline.
- **Working assumption:** ASSUMPTION (editorial): use the 1 hour option in the how-to; mention Until tomorrow only by its label, without an exact end time.
- **Documentation impact:** Block an exact Until tomorrow example or instruction until clarified.

## Q02 — Alerts that arise during a pause

- **Classification:** UNKNOWN.
- **Evidence:** `demo/mock-prd.md`, Feature and UI and workflow describe pausing and resuming but not backlog handling (C02, C05, C09).
- **Question:** Are in-app alerts created during the pause discarded, retained, or delivered on resume?
- **Why it matters:** Users may expect to recover missed alerts.
- **Working assumption:** ASSUMPTION (editorial): omit backlog claims.
- **Documentation impact:** No promise about later delivery.

## Q03 — Active pause changes and offline resume

- **Classification:** UNKNOWN.
- **Evidence:** `demo/mock-prd.md`, UI and workflow says pausing requires online access; it does not specify Resume now offline or changes to an active period (C06, C10).
- **Question:** Can Resume now work offline, and can a member replace a current pause?
- **Why it matters:** Both affect task steps and recovery guidance.
- **Working assumption:** ASSUMPTION (editorial): document only supported online pause steps and the named Resume now outcome.
- **Documentation impact:** Defer offline-resume and edit-active-pause procedures.

## Q04 — Release metadata

- **Classification:** UNKNOWN.
- **Evidence:** `demo/mock-prd.md`, Release says no date, platform list, or rollout plan is supplied (C11).
- **Question:** When and where is Quiet Hours available?
- **Why it matters:** Release notes usually need availability.
- **Working assumption:** ASSUMPTION (editorial): omit release metadata.
- **Documentation impact:** Keep the note to source-supported capabilities.
