# Coordinate parallel work with Tracks

Tracks lets you organize work on the same task across multiple workstreams and track progress in each one independently. For example, a task can move through specification and design work at the same time without one track's progress changing the other.

## Understand tasks and tracks

Each task belongs to one project, and tracks are scoped to that project. A task can be part of multiple tracks in its project.

Task status and track progress are separate:

| Type | Statuses |
| --- | --- |
| Task | Open, Completed, Discarded |
| Track progress | Not started, In Progress, Done |

Completed and Discarded tasks are closed. Reopening a closed task returns it to Open.

When you mark a task **Done** on one track, its progress on other tracks does not change, and the task itself is not completed. To resume work on that track, use **Mark Pending** to return it to **In Progress**.

## Work with tracks

When Tracks is enabled, the project's **Tracks** tab shows one column for each track. Each column separates **In Progress** and **Done** work. Only open tasks appear on the board. If a task belongs to several tracks, it appears in each corresponding column.

From the board, you can update a task's progress or use **Select** to start selected tasks across other tracks. If a selected task is already on a target track, its existing placement is preserved.

Open a task to view its **Tracks** pill. The pill shows every track in the project and the task's status on each one, giving you one place to review its progress across workstreams. It also shows how many of the available tracks are Done for that task.

## Manage tracks

Team members can enable Tracks and create, rename, or move tracks. Only admins can disable Tracks.

Track names must be unique within a project. Renaming a track changes its name without changing task assignments or statuses. Moving a track changes only its position on the board.

Deleting a track permanently removes its assignments and statuses from tasks, including closed tasks.

> **Warning:** Track deletion is irreversible. There is no undo or recovery window.

The source requirements contain conflicting behavior for what happens to track data when Tracks is disabled. That behavior must be clarified before this guide is published.

## Understand task lifecycle effects

Closing a task keeps its track memberships and statuses but removes the task from the Tracks board. Reopening it restores the task to its track columns with the retained statuses.

Moving a task to another project clears all of its track assignments. The task arrives in the destination project with no track started, even when a track there has the same name.

## Work offline

You can use **Start**, **Mark Done**, and **Mark Pending** while offline. Tasket queues these changes locally and reconciles them when you reconnect.

Managing Tracks requires an online connection. This includes enabling or disabling Tracks and creating, renaming, moving, or deleting tracks.

If an offline queued change refers to a track that was deleted online, Tasket drops that change during synchronization and does not recreate the track.

## Access

You need access to a project to view its Tracks board and access to a task to update its track progress. Guests have the same track permissions as members on projects they can access.

## Related task

[Mark a task Done on one track](../how-to/how-to.md).
