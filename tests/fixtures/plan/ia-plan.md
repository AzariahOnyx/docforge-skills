---
feature: Quiet Hours
mode: Net-New
product: alerts
category: notifications
owner: unknown
source_prs: []
engineering_spec: none
release: unknown
jira: PULSE-77
docforge_run: pulse-77
---

# IA plan: Quiet Hours

> Drafted by DocForge for writer review (fictional test fixture).

## Existing articles - impact

None.

## New articles

| Title | Type | Docs path | Why | Claims |
| --- | --- | --- | --- | --- |
| Pause in-app alerts with Quiet Hours | overview | site/alerts/notifications/quiet-hours.md | Understand what pausing does and its limits | C01, C02, C04 |
| Pause your in-app alerts for 1 hour | procedural | site/alerts/notifications/pause-for-1-hour.md | Pause alerts for one hour | C03, C06 |

## Out of scope

| Topic | Reason |
| --- | --- |
| Until tomorrow end time | Q01 is open: the time zone is not defined |

## Open questions

| ID | Question | Why it matters |
| --- | --- | --- |
| Q01 | Which time zone and exact time define the end of Until tomorrow? | Readers could plan around a wrong time |
| Q02 | Are in-app alerts created during a pause discarded or delivered on resume? | Readers may expect to recover them |

## Spec-versus-code conflicts

None. No code was compared.
