"""Handle one Jira webhook delivery: verify, decide, record, and post or queue the reply.

Planning and drafting are not run here: a `plan`, `draft` or `revise` decision is
recorded as the ticket's pending work.
"""

from __future__ import annotations

import os
from pathlib import Path

from docforge.config import DocForgeConfig, JiraTicketTrigger

from .events import EventError, parse, verify_signature
from .flow import decide, mode_of, product_of
from .state import Pending, TicketState, load_state, now, save_state
from .writer import JiraWriter


class HandleError(Exception):
    """A delivery that must be refused (bad signature, unknown trigger, unreadable body)."""


def _trigger(config: DocForgeConfig, name: str) -> JiraTicketTrigger:
    trigger = config.triggers.get(name)
    if not isinstance(trigger, JiraTicketTrigger):
        raise HandleError(f"{name!r} is not a jira_ticket trigger")
    return trigger


def handle(body: bytes, *, config: DocForgeConfig, trigger_name: str, state_root: Path,
           signature: str | None = None, verify: bool = True, delivery_id: str | None = None,
           client_factory=None) -> dict:
    trigger = _trigger(config, trigger_name)
    if verify:
        secret = os.environ.get(trigger.webhook_secret_env, "")
        if not secret:
            raise HandleError(f"environment variable {trigger.webhook_secret_env} is not set; deliveries are refused")
        if not verify_signature(secret, body, signature):
            raise HandleError("signature does not match; delivery refused")
    try:
        event = parse(body, delivery_id)
    except EventError as exc:
        raise HandleError(str(exc)) from None
    source = config.context_sources[trigger.source]
    bot = os.environ.get(trigger.bot_account_env, "")
    state = load_state(state_root, event.issue_key)
    decision = decide(event, state, trigger, list(source.project_keys), bot)
    result = {"issue": event.issue_key, "action": decision.action, "reason": decision.reason}
    if decision.silent:
        return result
    if state is not None and event.delivery_id in state.processed:
        return {**result, "action": "duplicate", "reason": "this delivery was already handled"}
    if state is None and decision.action == "ignore":
        return result  # nothing to remember about a ticket DocForge never worked on
    if state is None:
        state = TicketState(key=event.issue_key, trigger=trigger_name, mode=mode_of(trigger, event.work_type),
                            product=product_of(trigger, event))
    state.processed.append(event.delivery_id)
    state.note(f"{event.kind}: {decision.action}", reason=decision.reason, status_to=event.status_to,
               by=event.comment_author)

    publishing = config.resolve_policy(trigger=trigger_name, doc_collection=None)["publishing"]
    writer = JiraWriter(publishing, client_factory)
    if decision.reply_body is not None:
        result["comment"] = writer.comment(state, decision.reply, decision.reply_body).model_dump()
    if decision.move_to:
        result["move"] = writer.transition(state, decision.move_to).model_dump()
    if decision.action == "plan":
        state.phase = "planning"
        state.product = product_of(trigger, event)
        state.pending = Pending(action="plan", at=now())
    elif decision.action == "draft":
        state.phase = "drafting"
        state.pending = Pending(action="draft", at=now())
    elif decision.action == "ship":
        state.pending = Pending(action="ship", at=now())
    elif decision.action == "revise":
        state.pending = Pending(action="revise", at=now(), feedback=decision.feedback, by=event.comment_author,
                                answers=decision.answers, comment_id=event.comment_id,
                                comment_created=event.comment_created)
    save_state(state_root, state)
    result["phase"] = state.phase
    return result
