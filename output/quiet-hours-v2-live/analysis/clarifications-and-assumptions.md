# Quiet Hours — clarifications and assumptions

Current product evidence is exclusively `demo/mock-prd-v2.md` (complete file, lines 1–27). `demo/mock-prd.md` is used only to identify changes. No working assumptions are required and no contradictions were found.

| ID | Classification | Evidence | Question | Why it matters | Working assumption | Documentation impact |
| --- | --- | --- | --- | --- | --- | --- |
| Q01 | UNKNOWN | Revised Known gap, line 23 says time and zone are unspecified; UI and workflow, line 15 offers Until tomorrow (C03, C09). | What time of day and time zone define Until tomorrow? | Users need to predict when alerts resume. | None; do not guess. | Name the option without defining its cutoff; do not give clock-time examples. |
| Q02 | UNKNOWN | Revised Known gap, line 23; feature and workflow describe pause/resume but do not specify later delivery (C02, C05–C06, C10). | Are alerts created during the pause delivered later, discarded, or otherwise handled? | Readers may expect missed alerts. | None. | Omit queueing, discard, and catch-up claims. |
| Q03 | UNKNOWN | Revised Known gap, line 23 explicitly says mid-pause period changes are unspecified (C11). | Can a member change the selected period during an active pause? | A procedure could otherwise imply unsupported controls or transitions. | None. | Do not document editing an active pause. |
| Q04 | UNKNOWN | Revised Release, line 27 says date, platform list, rollout absent (C12). | What release date, platforms, and rollout may documentation announce? | Availability claims need approval/evidence. | None. | Omit release metadata and confirm before publication. |

**Resolved from the prior source:** whether Resume now requires a connection. Previous `demo/mock-prd.md`, UI and workflow line 14, only required online pausing and left offline manual resume unspecified. Revised `demo/mock-prd-v2.md`, UI and workflow line 15 explicitly states Resume now also requires online connection (C05). This resolution applies only to manual Resume now; it does not establish online requirements for automatic resumption. The prior combined question is split: this part is resolved, while mid-pause changes remain Q03.
