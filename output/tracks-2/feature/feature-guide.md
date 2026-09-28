# Tracks

Tracks lets your team work on one task across several workstreams at the same time. For example, a task can be in spec and design simultaneously, with its own status in each track.

## How it works

Tasket teams contain projects, and each task belongs to exactly one project. Tracks belong to a project too: a track in one project does not exist in another. A task can participate in any number of its project's tracks.

Track status and task status are independent:

| Status type | Values | Meaning |
| --- | --- | --- |
| Task status | Open, Completed, Discarded | Completed and Discarded tasks are closed. Reopening returns a task to Open. |
| Status on a track | In Progress, Done | Each track a task participates in has its own status. |
| No participation on a track | Not started | The task has not been started on that track. |

Marking a task **Done** on one track does not affect its other tracks. Completing or discarding the task is independent of its track participation.

## Board and task views

When Tracks is enabled, the project has a **Tracks** tab. Its board has one column per track, split into **In Progress** and **Done**. Columns show only open tasks. A task started on several tracks appears in each corresponding column.

Open a task from a track to view its assignees, watchers, comments, and attached documents or chats.

The task detail view has a **Tracks** pill wherever you access the task. Open it to see every track in the project and the task's status on each: **Not started**, **In Progress**, or **Done**. The pill counts Done tracks out of all available tracks for the task. It provides the full track picture in one view, including retained statuses for closed tasks. The pill is absent when Tracks is switched off.

## Working with tracks

**Add track** appears at the end of the track panels and between tracks. It lets you add and name a track and start tasks with it. Track names must be unique within the project.

| Track action | Effect |
| --- | --- |
| Rename | Changes the column and pill label, preserving assignments and statuses. |
| Move track | Changes the column's position on the board without affecting tasks. |
| Delete | Irreversibly removes the track's statuses and assignments from both open and closed tasks. There is no undo or recovery window. |

For an open task, actions depend on its status on that track:

| Status | Actions in the Tracks pill | Actions on the board |
| --- | --- | --- |
| Not started | Start | No placement on that track |
| In Progress | Mark Done, Stop | Mark Done, Stop, Select |
| Done | Mark Pending | Mark Pending, Select |

**Mark Pending** returns a task from Done to In Progress. A task marked Done cannot be stopped. Marking the last In Progress task Done leaves that section empty and updates the column counter. Each column header displays a counter in the form X out of Y.

**Select** lets you select multiple tasks and start them across other tracks. Starting a task on a track it already participates in highlights its existing placement; a multi-select start leaves already-placed tasks where they are.

Only open tasks can be started on new tracks. Reopen a closed task before starting it on a new track.

## Access

| Action | Who can perform it |
| --- | --- |
| Enable Tracks; create, rename, or move a track | Any team member |
| Disable Tracks | Admin only |
| View the Tracks board | Members with access to the project |
| Start, Mark Done, Stop, Mark Pending | Members with access to the task |
| Select and start across tracks | Members with access to the selected tasks |

Guests have the same track permissions as members on projects they can access.

## Important behavior

**Closing and reopening:** Completing or discarding a task preserves its track memberships and statuses. The task disappears from board columns, but its Tracks pill still shows its statuses. Reopening restores it to its columns with the same statuses, unless a track has since been deleted.

**Moving a task to another project:** All track assignments are cleared. The task arrives with no track started, even if the destination project has a track with the same name.

**Disabling Tracks — unresolved:** The requirements conflict: one passage says switching off hides Tracks and switching back on restores all tracks and assignments; another says switching off clears assignments and statuses and requires an admin to recreate tracks and associations. The data outcome is unconfirmed, so this draft provides no disable/re-enable procedure.

## Working offline

**Start**, **Mark Done**, and **Mark Pending** work offline. Changes queue locally and reconcile when you reconnect. Enabling or disabling Tracks and creating, renaming, moving, or deleting tracks require an online connection.

If a queued membership change reaches the server after its track was deleted online, the change is silently dropped and does not recreate the track. If you close a task offline while its track is deleted online, that assignment is removed on sync; reopening the task does not restore the deleted track in its pill.

## Related tasks

[View all of a task's track statuses](../how-to/how-to.md).
