"""Notifications about suggestions. Nothing is sent without --send and a policy that allows it."""

from .slack import EVENTS, NotifyError, Outcome, build_message, notify

__all__ = ["EVENTS", "NotifyError", "Outcome", "build_message", "notify"]
