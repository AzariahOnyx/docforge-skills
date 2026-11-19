"""Jira comment bodies, in Atlassian Document Format (ADF, Jira Cloud REST v3).

Every comment says it was posted by DocForge. Text from runs (article titles,
questions) is inserted as plain text nodes, never as markup.
"""

from __future__ import annotations

FOOTER = "Posted by DocForge. A person reviews and approves every change."


def text(value: str, *, bold: bool = False) -> dict:
    node = {"type": "text", "text": value}
    if bold:
        node["marks"] = [{"type": "strong"}]
    return node


def para(*parts) -> dict:
    content = [text(p) if isinstance(p, str) else p for p in parts if p]
    return {"type": "paragraph", "content": content}


def bullets(items: list) -> dict:
    return {"type": "bulletList", "content": [
        {"type": "listItem", "content": [item if isinstance(item, dict) else para(item)]} for item in items]}


def heading(value: str, level: int = 3) -> dict:
    return {"type": "heading", "attrs": {"level": level}, "content": [text(value)]}


def doc(*blocks) -> dict:
    return {"type": "doc", "version": 1, "content": [b for b in blocks if b] + [para(text(FOOTER))]}


def statuses_hint(plan: str, draft: str) -> str:
    return f"Move the ticket to {plan} to plan the documentation, or to {draft} to draft it once a plan exists."


# --- bounces and replies to moves -----------------------------------------------------


def no_attachments(types: list[str], bounce: str, plan: str) -> dict:
    kinds = " or ".join(t.upper() for t in types)
    return doc(para(f"DocForge cannot plan this ticket: it has no {kinds} attachment."),
               para(f"Attach the PRD (and any Flow PDFs), then move the ticket from {bounce} to {plan} again."))


def oversized(files: list[str], limit_mb: float, bounce: str, plan: str) -> dict:
    return doc(para(f"DocForge cannot plan this ticket: these attachments are larger than {limit_mb:g} MB:"),
               bullets(files),
               para(f"Replace them with smaller files, then move the ticket from {bounce} to {plan} again. "
                    "Nothing was downloaded."))


def pulled_back(plan: str, draft: str, planning: bool) -> dict:
    why = ("The plan is still being prepared." if planning else "This ticket has no documentation plan yet.")
    return doc(para(f"{why} DocForge moved the ticket back to {plan}; drafting starts when the ticket is moved to "
                    f"{draft} after the plan is posted."))


def already_planned(plan: str, draft: str) -> dict:
    return doc(para(f"This ticket already has a documentation plan, so moving it to {plan} again does not re-plan."),
               bullets([f"To change the plan, mention DocForge in a comment and say what to change.",
                        f"To draft the documentation, move the ticket to {draft}."]))


def drafts_exist(run: str | None) -> dict:
    where = f" (run {run})" if run else ""
    return doc(para(f"This ticket's documentation has already been drafted{where}, so its plan can no longer change. "
                    "Create a new ticket for a new plan."))


def drafts_ready(run: str | None, summary: list[str]) -> dict:
    where = f" Run: {run}." if run else ""
    return doc(para(f"The drafts for this ticket are ready for review.{where}"), bullets(summary) if summary else None)


# --- replies to mentions ------------------------------------------------------------


def ask_specifics() -> dict:
    return doc(para("Say what to change in the plan in the same comment as the mention, for example: "
                    "\"add a troubleshooting article for failed schedules\"."))


def no_plan_yet(plan: str) -> dict:
    return doc(para(f"There is no plan to revise yet. Move the ticket to {plan} to create one."))


def revision_refused() -> dict:
    return doc(para("Drafting has started, so the plan can no longer change: a revised plan could rename articles "
                    "that are already drafted. Create a new ticket for a new plan."))


def plan_in_progress() -> dict:
    return doc(para("The plan is still being prepared. Mention DocForge again after it is posted."))


# --- plan pull requests --------------------------------------------------------------


def plan_pr(articles: list[dict], questions: list[str], *, link: str | None, command: str | None,
            notes: list[str]) -> dict:
    """The plan is in a pull request: a short summary and the link (or the command that opens it)."""
    blocks = [heading("Documentation plan")]
    if link:
        blocks.append(para("DocForge proposed the documentation plan as a pull request: ", text(link, bold=True)))
        blocks.append(para("Review it there: approving the pull request approves the plan, and DocForge then drafts "
                           "the articles. Edit the plan file, or comment on the pull request, to change it."))
    else:
        blocks.append(para("DocForge prepared the documentation plan as a branch. The pull request is not opened "
                           f"automatically; to open it, a person runs: {command}"))
    if articles:
        blocks.append(bullets([para(text(a["title"], bold=True), text(f" ({a['type']}, {a['action']})"))
                               for a in articles]))
    blocks.append(para(f"Open questions: {len(questions)}. Answer them on the pull request."))
    if notes:
        blocks += [heading("Notes"), bullets(notes)]
    return doc(*blocks)


def approve_plan_pr(link: str | None) -> dict:
    where = f" ({link})" if link else ""
    return doc(para(f"This ticket's plan is a pull request{where}. Drafting starts when a writer approves that pull "
                    "request, not when the ticket moves."))


def review_on_plan_pr(link: str | None) -> dict:
    where = f": {link}" if link else ""
    return doc(para(f"This ticket's plan is reviewed in its pull request{where}. Comment there, mentioning "
                    "DocForge, to change the plan or answer its questions."))


# --- plans --------------------------------------------------------------------------


def unknown_questions(unknown: list[str], open_ids: list[str]) -> dict:
    listed = ", ".join(open_ids) if open_ids else "none"
    return doc(para(f"DocForge did not record these answers: {', '.join(unknown)} "
                    f"{'is' if len(unknown) == 1 else 'are'} not an open question in the current plan. "
                    "Nothing from the comment was used."),
               para(f"Open questions: {listed}. Mention DocForge again with each answer on its own line, "
                    "for example \"Q3: only workspace admins\"."))


def plan(articles: list[dict], questions: list[str], *, revision: int, draft: str, run: str | None = None,
         answered: dict[str, str] | None = None) -> dict:
    """articles: {"title", "type", "action"} (action: create or update). questions: open questions as text.
    answered: question label -> answer source ID, for questions the ticket's owner has answered."""
    label = "Documentation plan" + (f" (revision {revision})" if revision else "")
    blocks = [heading(label)]
    if articles:
        blocks.append(para("DocForge plans these articles:"))
        blocks.append(bullets([para(text(a.get("title", "Untitled"), bold=True),
                                    text(f" ({a.get('type', 'article')}, {a.get('action', 'create')})"))
                               for a in articles]))
    else:
        blocks.append(para("DocForge found no article to write. Mention DocForge with what the plan should cover."))
    blocks.append(heading("Open questions"))
    blocks.append(bullets(questions) if questions else para("None recorded."))
    if answered:
        blocks.append(para("Answered: " + ", ".join(f"{q} ({a})" for q, a in sorted(answered.items())) + "."))
    if questions:
        blocks.append(para("To answer a question, mention DocForge in a comment with each answer on its own line, "
                           "for example \"Q3: only workspace admins\". Answers become sources the drafts can cite."))
    blocks.append(para(f"To change the plan, mention DocForge in a comment and say what to change. "
                       f"To draft the documentation, move the ticket to {draft}."
                       + (f" Run: {run}." if run else "")))
    return doc(*blocks)
