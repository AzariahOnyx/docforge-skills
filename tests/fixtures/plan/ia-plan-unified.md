---
feature: Quiet Hours
mode: Enhancement
product: alerts
category: notifications
owner: writer-1
source_prs: [example-org/pulseboard-web#11]
engineering_spec: example-org/pulseboard-web:specs/quiet-hours/spec.md
release: unknown
decision: act
decision_reason: The spec adds a new setting members use.
status: proposed
---

# IA plan: Quiet Hours

> Fictional test fixture in the unified plan format (engine and docs-writer agent).

## Existing articles - impact

| Article | Docs path | Action | Change needed | Outdated passage | Evidence |
| --- | --- | --- | --- | --- | --- |
| Notification settings | site/alerts/notifications/settings.md | update | Add Quiet Hours to the settings list | Notification settings has two options. | SPEC:Documentation impact |
| Snooze alerts (legacy) | site/alerts/notifications/snooze.md | archive | Snooze is replaced by Quiet Hours | Select **Snooze** to pause alerts. | C02 |
| Alerts overview | site/alerts/index.md | none | Mentions alerts generally; no change | | none |

## New articles

| Title | Type | Docs path | Why | Evidence |
| --- | --- | --- | --- | --- |
| Pause your in-app alerts for 1 hour | procedural | site/alerts/notifications/pause-for-1-hour.md | Pause alerts for one hour | C03, CODE:src/alerts/pause.ts:1 |

## Out of scope

None.

## Open questions

| ID | Question | Why it matters |
| --- | --- | --- |
| Q01 | Which time zone defines the end of Until tomorrow? | Readers could plan around a wrong time |

## Spec-versus-code conflicts

| ID | Spec says | Code says | Where | Question |
| --- | --- | --- | --- | --- |
| X01 | Pause for 1 hour | Pause for any number of hours | Spec: Documentation impact; CODE:src/alerts/pause.ts:1 | Which behaviour is intended? |
