# Revised PRD: expected source impact

Use this as a review oracle, not as product evidence. Compare the two mock PRDs directly before reviewing a generated `output/quiet-hours-v2/` set.

| Change | Previous evidence | Revised evidence | Required document action |
| --- | --- | --- | --- |
| Fixed pause option changed | `mock-prd.md`, UI and workflow: 1 hour | `mock-prd-v2.md`, UI and workflow: 2 hours | UPDATE option in feature guide and release note; update how-to title, purpose, selection, and expected result. No current 1-hour instruction may remain. |
| Resume now requires a connection | `mock-prd.md`, UI and workflow: offline Resume now unspecified | `mock-prd-v2.md`, UI and workflow: explicitly online-only | UPDATE feature guide and any how-to resume note; update clarification register so this specific question is resolved. Do not extend the rule to automatic resume. |
| Until tomorrow still undefined | Both versions, Known gap | `mock-prd-v2.md`, Known gap | Keep UNKNOWN, with no invented end time or time zone. |
| Backlog and mid-pause changes | Neither version defines backlog; revised version still omits mid-pause changes | `mock-prd-v2.md`, Known gap | Keep these questions open. Do not call all of the old offline-action question resolved. |
| Release metadata | Neither version supplies date, platform, or rollout | `mock-prd-v2.md`, Release | Keep omitted; publication warning remains. |

The new `analysis/CHANGE-IMPACT.md` should name both source versions and the previous output, identify affected passages and stale claims, and distinguish supported updates from open questions. The Proofreader checks each revised passage against the **revised** source and verifies that the old output remains intact.
