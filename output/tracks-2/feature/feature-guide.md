# Track one task across parallel workstreams

Use Tracks in Tasket when several disciplines work on the same task. A task can be in spec and design at the same time, with separate progress in each workstream.

## One task, separate progress

Each task belongs to one project. Tracks belong to that project, and a task can participate in any number of them.

| Track status | Meaning for the task |
| --- | --- |
| Not started | The task has not been started on this track. |
| In Progress | The task is in progress on this track. |
| Done | The task has been marked done on this track. |

**Mark Done** changes progress on one track without affecting any other track. **Mark Pending** returns that track to In Progress. Track progress is separate from the task's overall status: Open, Completed or Discarded. Finishing a track and completing the task are independent actions.

## Find progress on the board or in a task

When Tracks is enabled, the project's **Tracks** tab shows a column for each track, split into In Progress and Done. Columns show only open tasks. A task started on several tracks appears in each of those columns.

For one task's full picture, open the **Tracks** pill in its details. It lists every track in the project with that task's status. The pill counts Done tracks out of all available tracks for the task, including tracks it has not started. The pill is absent when Tracks is disabled.

You can start an open task on one or more tracks. A closed task must be reopened before it can be started on a new track.

## Who can use Tracks

Members with project access can view the board. Members with access to a task can start it on tracks and update its track progress. Guests have the same track permissions as members on projects they can access.

Team members can enable Tracks and create, rename and reorder tracks. Track names must be unique within a project. Renaming changes the label; reordering changes the column position. Neither changes task assignments or statuses.

## What happens when work closes or moves

Completed and Discarded tasks are closed. Closing a task retains its track assignments and statuses: it leaves the board, but its statuses remain visible in the pill. Reopening returns it to the board with its retained statuses.

Keep these consequences in mind:

- **Deleting a track is irreversible.** It removes that track's assignments and statuses from both open and closed tasks. There is no undo or recovery window.
- Moving a task to another project clears all its track assignments. It has no tracks started in the destination, even when a track there has the same name.

Reopening a task does not restore an assignment removed by track deletion.

## Work offline

**Start**, **Mark Done** and **Mark Pending** work offline. Changes are queued locally and reconciled when you reconnect. Switching Tracks on or off and creating, renaming, reordering or deleting tracks require an internet connection.

**Offline changes can be lost when a track is deleted.** If a queued track-assignment change syncs after the track was deleted online, that change is silently dropped and the track is not recreated. If you close a task offline while its track is deleted online, its assignment to that track is removed on sync and does not return when you reopen the task.

## Next step

[Mark a task done on one track](../how-to/how-to.md).
