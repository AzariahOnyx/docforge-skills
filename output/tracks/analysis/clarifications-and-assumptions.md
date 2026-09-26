# Tracks — clarifications and working assumptions

The source is a working draft. Each item identifies what must be confirmed before the affected behavior can be documented accurately. “ASSUMPTION (editorial)” describes how these **drafts** proceed; it is not a claim about implemented product behavior. There is no product assumption that resolves a source contradiction.

Source: `input/Technical Writer - Case Study.pdf`. Page numbers refer to the six-page case-study PDF.

## Q01 — Disabling Tracks

- **Classification:** CONTRADICTION.
- **Source evidence:** C20A (p. 3) and C20B (p. 5).
- **Clarifying question:** Does switching Tracks off merely hide and preserve all tracks/assignments, or clear them and require recreation? Does switching back on require an admin?
- **Why it matters:** The two data retention stories lead to opposite warnings and recovery instructions.
- **Working assumption:** ASSUMPTION (editorial): do not choose either behavior; omit disable effects from reader-facing drafts until confirmed.
- **Documentation impact:** Blocks disable/re-enable instructions and any data-retention claim; QA publication WARNING.

## Q02 — Board counter

- **Classification:** UNKNOWN.
- **Source evidence:** C09, C29, C35 (pp. 3, 6).
- **Clarifying question:** What do X and Y count, and do closed or Not started tasks affect either number?
- **Why it matters:** A first-time user may otherwise misread progress.
- **Working assumption:** ASSUMPTION (editorial): mention that a counter exists only if needed; do not explain its calculation.
- **Documentation impact:** Omit counter interpretation and numerical examples.

## Q03 — Track deletion permission

- **Classification:** UNKNOWN.
- **Source evidence:** C11, C18, C22, C36 (pp. 3-5).
- **Clarifying question:** Who can delete a track: any team member, admin only, or another role? Is a confirmation step shown?
- **Why it matters:** Deletion irreversibly removes statuses on open and closed tasks.
- **Working assumption:** ASSUMPTION (editorial): do not name a deleting role or invent a confirmation UI.
- **Documentation impact:** Describe destructive effect; defer delete procedure and permission claim.

## Q04 — Stop outcome and offline access

- **Classification:** UNKNOWN.
- **Source evidence:** C06, C12, C15, C38 (pp. 3-4, 6).
- **Clarifying question:** Does Stop remove a task's membership and return it to Not started? Can Stop and Select be used offline?
- **Why it matters:** Determines status description, task actions, and offline guidance.
- **Working assumption:** ASSUMPTION (editorial): show Stop as an available action on In Progress only; omit post-Stop behavior and offline availability.
- **Documentation impact:** Block Stop procedure and avoid claiming offline support.

## Q05 — Add track flow

- **Classification:** UNKNOWN.
- **Source evidence:** C10, C37 (p. 4).
- **Clarifying question:** After Add track, is naming required before saving, are tasks automatically started, and how are they chosen?
- **Why it matters:** The exact create-track procedure and expected result are unclear.
- **Working assumption:** ASSUMPTION (editorial): omit the full creation procedure; mention Add track's location and purpose only.
- **Documentation impact:** Choose a supported state-change how-to instead.

## Q06 — Enablement setup

- **Classification:** UNKNOWN.
- **Source evidence:** C04, C22, C37 (pp. 2, 5-6).
- **Clarifying question:** Where does a team member enable Tracks, and does a newly enabled project begin with zero tracks or defaults?
- **Why it matters:** First-time setup steps and prerequisites need a verifiable path.
- **Working assumption:** ASSUMPTION (editorial): state only that the Tracks tab appears when enabled; do not give settings clicks or default tracks.
- **Documentation impact:** Omit enablement procedure and default-state claim.

## Q07 — Multi-select flow

- **Classification:** UNKNOWN.
- **Source evidence:** C13, C23, C26, C37 (pp. 4-6).
- **Clarifying question:** How does a user choose target tracks and confirm a multi-select start? Does it support multiple targets in one action?
- **Why it matters:** A task guide needs a reproducible sequence.
- **Working assumption:** ASSUMPTION (editorial): describe capability at a high level, not a click path.
- **Documentation impact:** Omit detailed bulk-start steps.

## Q08 — Access and guests

- **Classification:** UNKNOWN.
- **Source evidence:** C01, C22-C24 (pp. 2, 5).
- **Clarifying question:** What qualifies as access to a task/project, and how does the guest-as-member rule interact with admin-only disabling?
- **Why it matters:** Permissions and guest guidance could otherwise overpromise.
- **Working assumption:** ASSUMPTION (editorial): use the table's explicit access requirement; do not infer a guest can disable Tracks.
- **Documentation impact:** Keep permission statements scoped to explicit table rows.

## Q09 — Cross-project move safeguards

- **Classification:** UNKNOWN.
- **Source evidence:** C21 (p. 5).
- **Clarifying question:** Is there a warning or confirmation before a move clears track assignments, and can that loss be recovered?
- **Why it matters:** A destructive move warrants safe task guidance.
- **Working assumption:** ASSUMPTION (editorial): state the documented loss, but do not claim a warning, undo, or recovery.
- **Documentation impact:** Include a brief warning in conceptual documentation; no move procedure.

## Q10 — Closed task pill actions

- **Classification:** UNKNOWN.
- **Source evidence:** C15, C17, C27, C30, C39 (pp. 4, 6).
- **Clarifying question:** Can Mark Done, Mark Pending, or Stop be used through the pill while a task is closed, or is the pill read-only then?
- **Why it matters:** A visible pill does not necessarily mean edits are permitted.
- **Working assumption:** ASSUMPTION (editorial): explain visibility only; do not instruct changes on closed tasks.
- **Documentation impact:** Restrict how-to to an open task.

## Q11 — Offline conflict feedback

- **Classification:** UNKNOWN.
- **Source evidence:** C31-C34, C38 (p. 6).
- **Clarifying question:** How are queued changes ordered and conflicts or rejected writes shown to users after reconnect?
- **Why it matters:** Users need to know whether to retry or verify a change.
- **Working assumption:** ASSUMPTION (editorial): state only queue/reconcile and the documented silent deleted-track case.
- **Documentation impact:** Avoid guarantees of successful sync or feedback.

## Q12 — Terminology and labels

- **Classification:** UNKNOWN.
- **Source evidence:** C04, C14, pp. 2, 4; 'tasket' pp. 2-3.
- **Clarifying question:** Are 'task' and 'tasket' the same object, and is 'My Work' the same navigation label as 'Work tab'? What is the exact case for UI labels?
- **Why it matters:** Inconsistent names can misdirect readers.
- **Working assumption:** ASSUMPTION (editorial): use 'task' as the PRD's dominant term and avoid an unsupported My Work click path.
- **Documentation impact:** Use stable labels Tracks tab, Tracks pill, Mark Done, Mark Pending.

## Q13 — Pill progress denominator

- **Classification:** UNKNOWN.
- **Source evidence:** C15 (p. 4).
- **Clarifying question:** Does 'available tracks' mean every project track, including tracks where this task is Not started, and how are deleted tracks handled?
- **Why it matters:** The progress fraction could be misunderstood.
- **Working assumption:** ASSUMPTION (editorial): do not interpret or calculate the pill fraction.
- **Documentation impact:** Mention statuses without a numeric example.

## Q14 — Release availability

- **Classification:** UNKNOWN.
- **Source evidence:** C40 (pp. 1-6).
- **Clarifying question:** What release date, editions, platforms, rollout conditions, and migration details should the release note state?
- **Why it matters:** Release notes commonly require availability context.
- **Working assumption:** ASSUMPTION (editorial): omit unavailable release metadata rather than guessing.
- **Documentation impact:** Keep release note limited to confirmed capabilities.

## Q15 — Offline close behavior

- **Classification:** UNKNOWN.
- **Source evidence:** C17, C34 (pp. 4, 6).
- **Clarifying question:** Is closing and reopening generally supported offline, and what happens to queued track updates when a task is closed before sync?
- **Why it matters:** The edge case implies an offline close but does not define the whole workflow.
- **Working assumption:** ASSUMPTION (editorial): mention only the stated deleted-track sync case if necessary.
- **Documentation impact:** Do not advertise a general offline close/reopen workflow.

## Q16 — Terminal status language

- **Classification:** UNKNOWN.
- **Source evidence:** C03 (p. 2).
- **Clarifying question:** Should Completed and Discarded be called terminal in customer docs when both can be reopened?
- **Why it matters:** The word terminal may imply irreversibility to readers.
- **Working assumption:** ASSUMPTION (editorial): call both statuses 'closed' as the PRD defines, and explain reopen separately.
- **Documentation impact:** Avoid 'permanently completed' or irreversible task-status language.

## Q17 — Feature disable and offline writes

- **Classification:** UNKNOWN.
- **Source evidence:** C20A/C20B (pp. 3, 5), C31-C34 (p. 6).
- **Clarifying question:** If the capability is disabled while track writes are queued offline, are they applied, discarded, or restored on re-enable?
- **Why it matters:** The unresolved disable model and queued writes affect data integrity.
- **Working assumption:** ASSUMPTION (editorial): make no claim about this interaction.
- **Documentation impact:** Exclude from drafts; flag for product confirmation.


## Drafting decision

The feature guide, how-to, and release note cover only independently supported behavior. The critical disable/re-enable contradiction (Q01) remains open. Product confirmation is required before publishing a complete account of that lifecycle.
