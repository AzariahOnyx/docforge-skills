# Follow parallel work with Tracks

Tracks keeps the progress of several workstreams on one task. A task can be on spec and design tracks at the same time, with a separate status for each.

## How tracks relate to tasks

Each task belongs to one project, and tracks belong to that project. A task can be on any number of its project's tracks.

| Status on a track | Meaning |
| --- | --- |
| Not started | The task has not been started on this track. |
| In Progress | Work on the task is in progress on this track. |
| Done | The task has been marked Done on this track. |

A task on a track has exactly one status there: In Progress or Done. Marking it Done on one track leaves its other tracks unchanged. Completing or discarding the whole task is independent of its track progress.

## Find your track status

In a project with Tracks enabled, open the **Tracks** tab to see the board. Each track has a column split into In Progress and Done sections. Columns show only open tasks. An open task on three tracks appears in three columns.

For one task's complete track picture, open the **Tracks** pill in its details. It lists every track in the project and the task's status on each. The pill's count shows Done tracks out of all available tracks for that task.

## Access to Tracks

Team members with access to the project can view its Tracks board. Changing a task's track status requires access to that task. Guests have the same track permissions as members on projects they can access.

Any team member can enable Tracks for a project. Only an admin can disable it.

## When a task closes or moves

Completed and Discarded tasks are closed. Closing a task retains its track memberships and statuses, but removes it from the board's columns. In a project with Tracks enabled, you can still see the closed task's statuses in its **Tracks** pill.

Reopening returns the task to Open and puts it back in its columns with its retained statuses. Closure does not protect assignments from track deletion or a move to another project:

> **Warning:** Deleting a track permanently removes its assignments and statuses from both open and closed tasks. There is no undo or recovery window.

Moving a task to another project clears all its track assignments—even if the destination has a track with the same name. The task arrives with no track started.

To start a closed task on a new track, reopen the task first.

## Working offline

**Start**, **Mark Done**, and **Mark Pending** work offline. Changes queue locally and reconcile when you reconnect.

> **Important:** If a queued membership change reaches sync after its track was deleted online, the change is dropped silently. It does not recreate the track.

If a task closes offline while its track is deleted online, sync drops that assignment too. Reopening the task does not restore the deleted track.

Creating, renaming, moving, or deleting tracks requires an online connection, as does enabling or disabling Tracks.

## Related task

[Mark a task Done on one track](../how-to/how-to.md) when that workstream is finished. The guide also shows how to resume work on the track.
