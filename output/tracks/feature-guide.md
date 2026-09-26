# Use Tracks to manage parallel work on a task

Tracks let a team follow the same task through multiple workstreams in a project. For example, a task can be in a design track and an engineering track at the same time. Each track has its own status for that task, so progress in one workstream does not change the others.

## How tracks and task status work

Tracks belong to a project. A task belongs to one project and can be started on any number of that project's tracks. For each track, the task is **Not started**, **In Progress**, or **Done**. A started task has one status on that track: In Progress or Done.

A task's overall status is separate: **Open**, **Completed**, or **Discarded**. Completed and Discarded tasks are called **closed**. Marking a task Done on one track does not complete the task or change its status on other tracks.

## See work on the Tracks board

When Tracks is enabled for a project, open its **Tracks** tab. Each track has a column with an **In Progress** section and a **Done** section. Only open tasks appear on the board. A task started on several tracks appears in each corresponding column.

For a task in a track's In Progress section, the available actions include **Mark Done**, **Stop**, and **Select**. For a task in the Done section, the actions include **Mark Pending** and **Select**. Mark Pending returns the task to In Progress on that track. Select lets you choose multiple tasks to start on other tracks.

## See all of a task's tracks

Open a task and select its **Tracks pill** to see every track in the project and that task's status on each one. The pill offers **Start** for a Not started track, **Mark Done** and **Stop** for an In Progress track, and **Mark Pending** for a Done track. A closed task still displays its retained track statuses in the pill, although it must be reopened before it can be started on a new track.

## What happens when work changes

Closing a task removes it from the Tracks board without removing its track memberships or statuses. Reopening it restores the same placements and statuses.

Renaming a track changes its label without changing task assignments or statuses. Moving a track changes its column position only. **Deleting a track is irreversible:** it removes that track's assignments and statuses from both open and closed tasks, with no undo or recovery window.

Moving a task to another project clears all its track assignments. Tracks in the destination project are separate, even when a track has the same name.

## Access and offline use

A team member can enable Tracks and create, rename, or move a track. Only an admin can switch the capability off. To view the board, a member needs access to the project; task actions require access to the affected task.

**Start**, **Mark Done**, and **Mark Pending** are available offline. These changes queue locally and reconcile when a connection returns. Switching the capability on or off and creating, renaming, moving, or deleting tracks require an online connection.

To change a task's status on one track, see [Mark a task Done on a track](how-to.md).
