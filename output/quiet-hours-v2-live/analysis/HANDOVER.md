# Quiet Hours — documentation handover

## Assignment scope

Update mode: compare `demo/mock-prd.md` with revised `demo/mock-prd-v2.md`, using the prior documentation set `output/quiet-hours/` as a comparison baseline. Create a complete fresh set in `output/quiet-hours-v2-live/`. The revised PRD is the current product source; the previous PRD and output are historical baseline only. Audiences: signed-in members understanding the feature, members pausing/resuming alerts, and readers scanning the change.

## Source inventory and coverage

| Source | Role and coverage | Limits |
| --- | --- | --- |
| `demo/mock-prd.md` | Previous product source, all sections, lines 1–23 | Historical comparison only. |
| `demo/mock-prd-v2.md` | Current product source, full file, Product context through Release, lines 1–27 | Sole basis for current product assertions. No implementation verification. |
| `output/quiet-hours/` | Existing previous output, all eight documents inspected | Documentation comparison only; not product evidence. Preserved. |

Both PRDs are complete, readable Markdown without diagrams or attachments. No other source is used.

## Claim register

FACT means explicitly stated in the revised PRD, not independently verified product behavior.

| ID | Classification | Current claim | Revised evidence | Change / limit |
| --- | --- | --- | --- | --- |
| C01 | FACT | Pulseboard is a team dashboard; members receive in-app alerts for items assigned to them. | Product context, line 7 | Wording update from prior source. |
| C02 | FACT | Quiet Hours pauses a member's own in-app alerts for a selected period; it does not affect email alerts or other members' settings. | Feature, line 11 | Scope retained. |
| C03 | FACT | From Settings > Notifications > Quiet Hours, select Pause alerts, choose 2 hours or Until tomorrow, then Confirm. | UI and workflow, line 15 | Fixed option changed from 1 to 2 hours. |
| C04 | FACT | Screen displays the selected end time and Resume now. | UI and workflow, line 15 | Display format unspecified. |
| C05 | FACT | Resume now restarts in-app alerts immediately and requires an online connection. | UI and workflow, line 15 | New explicit prerequisite; do not apply to automatic resumption. |
| C06 | FACT | In-app alerts resume automatically when the selected period ends. | UI and workflow, line 15 | No online condition specified for this automatic transition. |
| C07 | FACT | Pausing is available only while online. | UI and workflow, line 15 | Separate from manual resume requirement C05. |
| C08 | FACT | Any signed-in member can change their own setting; admins cannot change another member's setting. | Permissions, line 19 | Retained. |
| C09 | UNKNOWN | Until tomorrow's time of day and time zone are not specified. | Known gap, line 23; option in line 15 | Q01; explicitly do not guess. |
| C10 | UNKNOWN | Whether alerts created during a pause are delivered later is unspecified. | Known gap, line 23 | Q02. |
| C11 | UNKNOWN | Whether the selected period can be changed during an active pause is unspecified. | Known gap, line 23 | Q03; newly explicit unknown. |
| C12 | UNKNOWN | Release date, platform list, and rollout plan are absent. | Release, line 27 | Q04; retained. |

No working assumption is needed. No material INFERENCE is used as product behavior. No CONTRADICTION found between the source versions. Previous output claims of 1 hour are stale relative to the current source and are excluded from this register except as documented in CHANGE-IMPACT.md.

## Product model and documentation implications

- **Users and scope:** members manage their own in-app alerts for assigned items; email alerts and other members' settings are unaffected (C01–C02, C08).
- **Terminology/UI:** use exact revised labels Settings > Notifications > Quiet Hours, Pause alerts, 2 hours, Until tomorrow, Confirm, and Resume now (C03–C05).
- **Permissions:** any signed-in member may change their own setting; no admin change to another's setting (C08).
- **States and lifecycle:** pause for selected period, immediately resume via Resume now, or resume automatically at period end (C02, C05–C06). The source explicitly requires connectivity for pausing and manual resume (C05, C07). It does not establish an online requirement for automatic resumption.
- **Destructive action, creation, retention:** none described; do not invent deletion, alert retention, or backlog behavior (C10).
- **Offline, recovery, and mid-pause editing:** pausing and manual resume require online connection. Active-period modification remains unknown. Do not conflate manual and automatic resumption (C05–C07, C11).
- **Limits:** Until tomorrow time/zone, backlog delivery, mid-pause period changes, and release availability remain unresolved (C09–C12).

## Clarifications and contradictions

See [clarifications-and-assumptions.md](clarifications-and-assumptions.md). Compared with the previous register, the offline Resume now question is resolved by C05; active-pause change behavior remains open separately as Q03. Prior Q IDs are historical and need not map one-to-one after questions are split.

| ID | Topic | Evidence | Question |
| --- | --- | --- | --- |
| Q01 | Until tomorrow boundary | C09; revised Known gap, line 23 | What exact time and time zone define the option? |
| Q02 | Alerts generated during pause | C10; revised Known gap, line 23 | Are they delivered later, discarded, or handled another way? |
| Q03 | Changing an active period | C11; revised Known gap, line 23 | Can a member change the selected period mid-pause; if so, how? |
| Q04 | Release metadata | C12; revised Release, line 27 | What date, platforms, and rollout may be announced? |

No source contradiction identified. Preserve Q01–Q04 as unknowns; do not infer answers.

## Documentation plan

The new content plan proposes three UPDATEs in the fresh folder based on the prior supplied drafts, not in-place edits. `analysis/CHANGE-IMPACT.md` records stale content and review-only retirement candidacy. A one-step task update remains supported. See `CONTENT-PLAN.md` for actions and destination details.

## Drafter guidance

Use the revised PRD as the only authority for current behavior. Retain personal scope, update **1 hour** to **2 hours** everywhere, and explicitly state that both pausing and Resume now require online connectivity. Do not extend that prerequisite to automatic resumption. Keep Until tomorrow unqualified except as an option label; do not add a cutoff or time zone. Do not assert alert backlog or mid-pause editing behavior. Omit release date/platform/rollout. No working assumptions are necessary. Publication warnings remain for Q01–Q04.

## Draft claim map

The Drafter produced all three mapped drafts. The Coverage ledger accounts for C01–C12 exactly once; independent source-first proofreading is recorded in `qa/QA-REPORT.md`.
