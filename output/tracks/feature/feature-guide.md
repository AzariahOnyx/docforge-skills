# Coordinate parallel work with Tracks

With Tracks, you can work on the same task across several workstreams at once and track progress separately in each. For example, a sign-in redesign can be in spec and design at the same time.

## Understand tasks and tracks

Tasket teams contain projects, and each task belongs to one project. Tracks belong to a project too. A task can participate in any number of that project's tracks.

A task has its own status: Open, Completed, or Discarded. Completed and Discarded tasks are closed; reopening returns them to Open. Track progress is separate from task status:

| Status on a track | Meaning |
| --- | --- |
| Not started | The task has not been started on this track. |
| In Progress | The task participates in this track and is not marked Done on it. |
| Done | The task is marked Done on this track. |

Marking a task **Done** on one track does not affect its other tracks or complete the task. Use **Mark Pending** to return it to **In Progress** on that track.

## Find your work on the board

When Tracks is enabled for a project, its **Tracks** tab shows one column per track. Each column has **In Progress** and **Done** sections. Only open tasks appear on the board. A task started on three tracks appears in three columns.

For a task in **In Progress**, the board offers **Mark Done**, **Stop**, and **Select**. For a task in **Done**, it offers **Mark Pending** and **Select**. A task marked Done cannot be stopped.

Use **Select** to select multiple tasks and start them across other tracks in one action. If a task is already on the target track, a multi-select start leaves it where it is. Starting an individual task on a track it already participates in highlights its existing placement.

Only open tasks can be started on new tracks. Reopen a closed task before starting it on a new track.

## See a task's full track status

Open a task from a track to see its assignees, watchers, comments, and attached documents or chats. Wherever you open the task, its detail view includes a **Tracks** pill when Tracks is enabled.

Open the pill to see every track in the project and the task's status beside each one. It shows how many tracks are Done out of all available tracks for the task. This is the single view of the task's full track picture, including retained statuses for closed tasks.

For an open task, the pill offers **Start** for Not started tracks, **Mark Done** and **Stop** for In Progress tracks, and **Mark Pending** for Done tracks. When Tracks is switched off, the pill is absent.

## Manage the project's tracks

**Add track** appears between tracks and at the end of the track panels. You can add and name a track and start tasks with it. Each track must have a unique name within its project.

| Action | Effect |
| --- | --- |
| **Rename** | Changes the name on the column and in the pill. Assignments and statuses stay the same. |
| **Move track** | Changes the column's position on the board without affecting tasks. |
| **Delete** | Removes the track's statuses and assignments everywhere, including on closed tasks. |

**Track deletion is irreversible.** There is no undo or recovery window.

## Know who can act

| Action | Required access or role |
| --- | --- |
| Enable Tracks; create, rename, or move a track | Any team member |
| Disable Tracks | Admin only |
| View the Tracks board | Member with access to the project |
| **Start**, **Mark Done**, **Stop**, or **Mark Pending** | Member with access to the task |
| **Select** and start tasks across tracks | Member with access to the selected tasks |

Guests have the same track permissions as members on projects they can access.

## Understand what happens when tasks change

**Closing and reopening a task:** Completing or discarding a task retains its track memberships and statuses. It disappears from all board columns, but the Tracks pill still shows its statuses. Reopening returns it to its columns with those statuses. Deleting a track removes its assignments even from closed tasks.

**Moving a task to another project:** The move clears all track assignments. The task arrives with no track started, even if the destination has a track with the same name.

## Work offline

**Start**, **Mark Done**, and **Mark Pending** are available offline. Changes queue locally and reconcile when you reconnect. Enabling or disabling Tracks and creating, renaming, moving, or deleting tracks require an online connection.

If a queued membership change syncs after its track was deleted online, the change is silently dropped. It does not recreate the track. If you close a task offline while its track is deleted online, that assignment is dropped on sync and does not return when you reopen the task.

## Related task

[Mark a task Done on one track](../how-to/how-to.md).
