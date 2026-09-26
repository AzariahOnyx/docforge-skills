# Quiet Hours — revised fictional PRD

Revision of `demo/mock-prd.md`. Use both files in update mode; this file alone is the current product source.

## Product context

Pulseboard is a team dashboard. Members receive in-app alerts for items assigned to them.

## Feature

Quiet Hours lets a member pause their own in-app alerts for a selected period. It does not affect email alerts or other members' settings.

## UI and workflow

Open Settings > Notifications > Quiet Hours. Select Pause alerts, choose 2 hours or Until tomorrow, and select Confirm. The screen displays the selected end time and Resume now. Resume now restarts in-app alerts immediately; alerts also resume automatically when the selected period ends. Pausing is available only while online. Resume now also requires an online connection.

## Permissions

Any signed-in member can change their own Quiet Hours setting. An admin cannot change another member's setting.

## Known gap

Until tomorrow does not specify a time of day or time zone. The PRD does not say whether alerts created during a pause are delivered later, or whether the selected period can be changed mid-pause.

## Release

No release date, platform list, or rollout plan has been supplied.
