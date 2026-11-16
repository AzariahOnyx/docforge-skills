"""Quiet Hours: pause a member's own in-app alerts (fictional example code)."""

from datetime import datetime, time, timedelta

PAUSE_OPTIONS = {
    "2_hours": timedelta(hours=2),
    "until_tomorrow": None,
}
UNTIL_TOMORROW_AT = time(hour=8)  # 08:00 in the member's own time zone

PAUSED_CHANNELS = ("in_app",)  # email alerts are never paused


def pause_until(option, now):
    if option == "until_tomorrow":
        tomorrow = (now + timedelta(days=1)).date()
        return datetime.combine(tomorrow, UNTIL_TOMORROW_AT, tzinfo=now.tzinfo)
    return now + PAUSE_OPTIONS[option]


def can_change(actor, member):
    # Only the member may change their own setting; admins cannot.
    return actor.id == member.id


def schedule_resume(member, end_time, scheduler):
    # The notification service runs the resume job; it is not in this repository.
    scheduler.enqueue("resume_alerts", member_id=member.id, at=end_time)
