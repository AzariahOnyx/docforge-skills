"""The front door's decision table: what one webhook delivery means for one ticket.

Status moves: DocForge reacts only to the `plan` and `draft` statuses (and, once
drafted, to a `shipped` status, which lets the docs pull request leave draft), and only
writes `bounce`, `planned` and (as a deliberate one-hop pull-back) `plan`.
Comments: only an owner's @-mention of the bot can revise a plan or answer its
open questions (lines such as `Q3: ...`).

`decide` is pure: it reads the event, the ticket's state and the trigger, and
returns a Decision. `handle` applies a decision: state, outbox, ticket moves.
Stages themselves (planning, drafting) run later from `pending`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from docforge.config import JiraTicketTrigger

from . import comments
from .answers import split_comment
from .events import TicketEvent
from .state import TicketState


@dataclass
class Decision:
    action: str  # ignore, bounce, plan, draft, revise, pull_back, reply, ship
    reason: str
    reply: str | None = None  # comment kind to post
    reply_body: dict | None = None
    move_to: str | None = None
    silent: bool = False  # ignored without recording anything
    feedback: str = ""
    answers: dict[int, str] = field(default_factory=dict)
    detail: dict = field(default_factory=dict)


def mode_of(trigger: JiraTicketTrigger, work_type: str) -> str | None:
    folded = work_type.casefold()
    if folded in {w.casefold() for w in trigger.work_types.net_new}:
        return "net_new"
    if folded in {w.casefold() for w in trigger.work_types.enhancement}:
        return "enhancement"
    return None


def product_of(trigger: JiraTicketTrigger, event: TicketEvent) -> str | None:
    for label in event.labels:
        if label in trigger.product.labels:
            return trigger.product.labels[label]
    for component in event.components:
        if component in trigger.product.components:
            return trigger.product.components[component]
    return trigger.product.default


def _usable(trigger: JiraTicketTrigger, event: TicketEvent) -> tuple[list[str], list[str]]:
    """(usable attachment names, oversized names)."""
    usable, big = [], []
    for a in event.attachments:
        ext = a.filename.rsplit(".", 1)[-1].lower() if "." in a.filename else ""
        if ext not in trigger.attachments.types:
            continue
        (big if a.size > trigger.attachments.max_bytes else usable).append(a.filename)
    return usable, big


def _same(a: str | None, b: str) -> bool:
    return bool(a) and a.casefold() == b.casefold()


def decide(event: TicketEvent, state: TicketState | None, trigger: JiraTicketTrigger, project_keys: list[str],
           bot_account: str) -> Decision:
    s = trigger.statuses
    if project_keys and event.project not in project_keys:
        return Decision("ignore", f"project {event.project} is not watched", silent=True)
    if mode_of(trigger, event.work_type) is None:
        return Decision("ignore", f"Work Type {event.work_type!r} is not a DocForge Work Type", silent=True)
    phase = state.phase if state else "new"

    if event.kind == "status":
        if _same(event.status_to, s.plan):
            if phase in ("new", "failed"):
                usable, big = _usable(trigger, event)
                if big:
                    return Decision("bounce", "oversized attachment", "bounce_oversized",
                                    comments.oversized(big, trigger.attachments.max_bytes / 1024 / 1024, s.bounce, s.plan),
                                    move_to=s.bounce, detail={"files": big})
                if not usable:
                    return Decision("bounce", "no usable attachment", "bounce_no_attachments",
                                    comments.no_attachments(trigger.attachments.types, s.bounce, s.plan), move_to=s.bounce)
                return Decision("plan", "moved to the plan status", detail={"attachments": usable})
            if phase == "planning":
                return Decision("ignore", "already planning")
            if phase == "planned":
                return Decision("reply", "already planned", "already_planned", comments.already_planned(s.plan, s.draft))
            if phase == "drafting":
                return Decision("ignore", "drafting in progress")
            return Decision("reply", "already drafted", "drafts_exist", comments.drafts_exist(state.run if state else None))
        if _same(event.status_to, s.draft):
            if phase in ("new", "failed", "planning"):
                return Decision("pull_back", "no plan yet", "pulled_back",
                                comments.pulled_back(s.plan, s.draft, planning=phase == "planning"), move_to=s.plan)
            if phase == "planned":
                return Decision("draft", "moved to the draft status")
            if phase == "drafting":
                return Decision("ignore", "drafting in progress")
            return Decision("reply", "already drafted", "drafts_ready", comments.drafts_ready(state.run if state else None, []))
        if any(_same(event.status_to, shipped) for shipped in s.shipped):
            if phase == "drafted":
                return Decision("ship", "the feature shipped")
            return Decision("ignore", f"shipped before the documentation was drafted (phase {phase})")
        return Decision("ignore", f"status {event.status_to!r} is not watched")

    if event.kind == "comment":
        if not bot_account or bot_account not in event.comment_mentions:
            return Decision("ignore", "comment does not mention DocForge")
        if event.comment_author == bot_account:
            return Decision("ignore", "comment by DocForge itself")
        if not event.comment_author or event.comment_author not in event.owners:
            return Decision("ignore", "mention by someone who is not the ticket's reporter, creator or assignee")
        if phase in ("new", "failed"):
            return Decision("reply", "no plan to revise", "no_plan_yet", comments.no_plan_yet(s.plan))
        if phase == "planning":
            return Decision("reply", "plan in progress", "plan_in_progress", comments.plan_in_progress())
        if phase in ("drafting", "drafted"):
            return Decision("reply", "revision refused after drafting started", "revision_refused",
                            comments.revision_refused())
        answers, feedback = split_comment(event.comment_text)
        if not answers and not feedback:
            return Decision("reply", "mention without feedback", "ask_specifics", comments.ask_specifics())
        reason = ("owner answered open questions" if answers and not feedback else
                  "owner answered open questions and asked for a revision" if answers else
                  "owner asked for a revision")
        return Decision("revise", reason, feedback=feedback, answers=answers)

    return Decision("ignore", "not a status move or a comment")
