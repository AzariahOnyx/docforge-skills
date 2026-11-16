"""Notification channels for the fictional Pulseboard app."""

EMAIL = "email"
IN_APP = "in_app"


def channels():
    return [EMAIL, IN_APP]


def settings_sections():
    return ["Email alerts", "In-app alerts", "Quiet Hours"]
