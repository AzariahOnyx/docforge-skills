# Fictional PRD: Quiet Hours

This is a fictional specification used to test source-grounded documentation workflows.

## Product context
Pulseboard is a team dashboard. Members receive in-app alerts for assigned items.

## Feature
Quiet Hours lets a member pause their own in-app alerts for a selected period. It does not pause email alerts or change another member's settings.

## UI and workflow
From **Settings > Notifications > Quiet Hours**, select **Pause alerts**. Choose **1 hour** or **Until tomorrow**, then select **Confirm**. The screen displays the selected end time and a **Resume now** action.

Selecting **Resume now** restarts in-app alerts immediately. When the selected period ends, in-app alerts resume automatically. Pausing is available only while online.

## Permissions
Any signed-in member can change their own Quiet Hours setting. An admin cannot change another member's setting.

## Known gap
"Until tomorrow" is not defined: the PRD does not state which time zone or time of day is used. Do not guess it in user documentation.

## Release
No release date, platform list, or rollout plan is supplied.
