"""Review on the plan pull request (B7c-2): comments revise the plan, approval starts drafting.

`handle_plan_event` records what a delivery means (a change request, answers, an approval with its commit,
the pull request merged or closed). `process_plan_pr` later acts on it:

- change requests: after the quiet period, the Analyzer runs again with the feedback (through the API
  backend, or by waiting for a Claude Code session); the new ia-plan.md must pass `plan check`, and is
  committed to the plan branch, pushed and answered when `auto_create_pr` allows. If a person has pushed
  to the plan branch, DocForge stops rewriting the file and says so: the writer's edits are never overwritten.
- approval (or a merge without an approving review): DocForge reads ia-plan.md as of the approved commit,
  so the writer's edits count, checks it, keeps it as analysis/ia-plan.approved.md, matches its articles to
  the run's deliverables, rewrites the Drafter and Proofreader work orders, and calls `on_approved` (the
  Jira route queues drafting). Articles a run cannot draft are named in the reply as needing their own run.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path

from docforge.config import DocForgeConfig
from docforge.github.docs_pr import (
    DocsPrError,
    _remember,
    _reviewer_problem,
    record_answers,
    reply,
    repo_of,
)
from docforge.github.events import DocsPrEvent, mentions, strip_mention
from docforge.publish import PublishError, load_plan, save_plan
from docforge.run.stages import DEFAULT_DELIVERABLES, IA_PLAN

from .model import IaPlan, read_plan
from .run import check_run_plan, run_plan_types

KIND = "plan-pr"
APPROVED = "analysis/ia-plan.approved.md"
TYPE_TO_DELIVERABLE = {"overview": "feature/feature-guide.md", "procedural": "how-to/how-to.md",
                       "release-notes": "release-note/release-note.md"}
ACTIVE = ("changes_requested", "revising", "approved")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


# --- recording events -------------------------------------------------------------------


def handle_plan_event(event: DocsPrEvent, *, run: Path, config: DocForgeConfig, delivery_id: str | None = None,
                      client=None) -> dict:
    from docforge.jira.answers import split_answers

    record = load_plan(run, KIND)
    result = {"run": str(run), "pull_request": record.pr_number, "event": event.kind, "kind": KIND}
    if delivery_id and delivery_id in record.processed:
        return {**result, "action": "duplicate"}
    collection = config.doc_collections.get(record.repo)
    if collection is None:
        raise DocsPrError(f"doc collection {record.repo!r} is not in the config")
    at = _now().isoformat()

    if event.kind in ("merged", "closed"):
        record.github_state = event.kind
        if event.kind == "merged" and record.status not in ("approved", "drafting") and event.commit:
            record.approved_commit, record.status = event.commit, "approved"  # merged without an approving review
        elif event.kind == "closed":
            record.status = "closed"
        record.history.append({"at": at, "event": f"github_{event.kind}"})
        _remember(record, delivery_id)
        save_plan(run, record)
        return {**result, "action": "approved" if record.status == "approved" else event.kind}
    if record.github_state or record.status == "closed":
        return {**result, "action": "ignore", "reason": f"the plan pull request is {record.github_state or 'closed'}"}
    if event.kind == "ignore":
        return {**result, "action": "ignore", "reason": event.reason}
    problem = _reviewer_problem(event, collection)
    if problem:
        return {**result, "action": "ignore", "reason": problem}
    if record.status in ("approved", "drafting"):
        return {**result, "action": "ignore", "reason": "the plan is already approved; comment on the drafts instead"}

    if event.kind == "review" and event.review_state == "approved":
        record.approved_commit, record.status = event.commit, "approved"
        record.history.append({"at": at, "event": "approved", "by": event.author, "commit": event.commit})
        _remember(record, delivery_id)
        save_plan(run, record)
        return {**result, "action": "approved", "commit": event.commit}

    login = collection.bot_login
    mentioned = mentions(event.body, login)
    text = strip_mention(event.body, login)
    if event.kind == "line_comment":
        record.line_comments.append({"id": event.comment_id, "review_id": event.review_id, "page": event.path,
                                     "line": event.line, "body": text, "author": event.author,
                                     "mention": mentioned, "used": False})
        record.last_request_at = at
        _remember(record, delivery_id)
        save_plan(run, record)
        return {**result, "action": "line_comment_recorded"}
    if event.kind == "review" and event.review_state == "changes_requested":
        if event.review_id is not None:
            record.requested_reviews.append(event.review_id)
    elif not mentioned:
        return {**result, "action": "ignore", "reason": "does not request changes or mention DocForge"}

    plan_answers, cross_answers, feedback = split_answers(text)
    note = ""
    if plan_answers or cross_answers:
        save_plan(run, record)
        source_id, answered, unknown = record_answers(run, record, event, plan_answers, cross_answers)
        record = load_plan(run, KIND)
        if unknown:
            reply(run, record, config, "unknown_questions",
                  f"DocForge did not record these answers: {', '.join(unknown)} "
                  f"{'is' if len(unknown) == 1 else 'are'} not an open question in this plan. "
                  "Nothing from the comment was used.", client)
            _remember(record, delivery_id)
            save_plan(run, record)
            return {**result, "action": "refused", "unknown": unknown}
        note = f"Answers recorded as {source_id}: {', '.join(answered)}. Update the plan where they change it."
        result["answers"] = source_id
    comment = "\n".join(part for part in (feedback, note) if part)
    if comment:
        record.requests.append({"id": event.comment_id or event.review_id, "author": event.author, "body": comment,
                                "at": at, "used": False})
    record.status = "changes_requested" if (comment or event.review_state == "changes_requested") else record.status
    record.last_request_at = at
    _remember(record, delivery_id)
    save_plan(run, record)
    return {**result, "action": "changes_requested" if comment else "review_recorded"}


# --- acting on them ---------------------------------------------------------------------


def _git(config: DocForgeConfig, record):
    from docforge.github import web_git_url

    collection = config.doc_collections[record.repo]
    return collection, collection.git_url or web_git_url(collection.api_url, record.repo), \
        os.environ.get(collection.token_env)


def _promote(record) -> None:
    for item in record.line_comments:
        if item.get("used"):
            continue
        if item.get("mention") or (item.get("review_id") is not None and item["review_id"] in record.requested_reviews):
            where = f" (line {item['line']})" if item.get("line") else ""
            record.requests.append({"id": item.get("id"), "author": item["author"], "at": _now().isoformat(),
                                    "body": f"On the plan file{where}: {item['body']}", "used": False})
            item["used"] = True
            record.status = "changes_requested"


def apply_approved_plan(run: Path, plan: IaPlan, *, commit: str, link: str | None) -> dict:
    """Match the approved plan's articles to the run's deliverables, record them in run.json and rewrite the
    Drafter and Proofreader work orders. Returns {placements, needs_own_run}."""
    from docforge.run.start import rewrite_work_orders

    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    if manifest.get("profile") != "default":
        raise DocsPrError("drafting from an approved plan needs a default-profile run")
    placements: dict[str, str] = {}
    extra: list[str] = []
    for article in plan.articles():
        deliverable = TYPE_TO_DELIVERABLE.get(article["type"] or "")
        if article["change"] != "create":
            extra.append(f"{article['title']} ({article['change']} of an existing article)")
        elif deliverable is None or deliverable in placements:
            extra.append(f"{article['title']} ({article['type']})")
        else:
            placements[deliverable] = article["path"]
    if not placements:
        raise DocsPrError("no article in the approved plan matches a draft this run can write "
                          f"({', '.join(TYPE_TO_DELIVERABLE)})")
    manifest["deliverables"] = [d for d in DEFAULT_DELIVERABLES if d in placements]
    manifest["approved_plan"] = {"commit": commit, "pull_request": link, "file": APPROVED,
                                 "placements": [{"src": d, "dest": placements[d]} for d in manifest["deliverables"]],
                                 "needs_own_run": extra}
    (run / "run.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    rewrite_work_orders(run, repo_of(run))
    return {"placements": manifest["approved_plan"]["placements"], "needs_own_run": extra}


def _read_approval(run: Path, record, config: DocForgeConfig, checkout: Path, client) -> dict:
    from docforge.github.push import fetch_branch, is_ancestor, show_file

    collection, git_url, token = _git(config, record)
    tip = fetch_branch(checkout, record.branch, git_url, token)
    commit = record.approved_commit or tip
    if commit != tip and not is_ancestor(checkout, commit, tip):
        raise PublishError(f"the approved commit {commit[:12]} is not on {record.branch}")
    dest = record.placements[0]["dest"]
    text = show_file(checkout, commit, dest)
    plan, errors = read_plan(text, types=run_plan_types(run), allows=collection.allows)
    if errors or plan is None:
        record.status = "approval_invalid"
        record.history.append({"at": _now().isoformat(), "event": "approval_invalid", "commit": commit})
        reply(run, record, config, "approval_invalid",
              f"The approved plan (commit {commit[:12]}) has problems, so DocForge did not start drafting:\n\n"
              + "\n".join(f"- {e}" for e in errors[:15]) + "\n\nFix the file in this pull request and approve again.",
              client)
        save_plan(run, record)
        return {"result": "failed", "reason": "; ".join(errors[:3])}
    from docforge.flow import stage_done

    if not stage_done(run, 1):
        # Approved while a plan revision was still waiting for the Analyzer: the approved plan wins. The plan
        # set aside for that revision comes back, so the run's analysis matches what was approved.
        from docforge.jira.work import _restore_plan

        folder = run / "analysis" / "revisions"
        latest = max((int(p.name[1:]) for p in folder.glob("r*") if p.name[1:].isdigit()), default=None)
        if latest is None:
            raise DocsPrError("the run has no finished analysis to draft from")
        _restore_plan(run, latest)
        record.history.append({"at": _now().isoformat(), "event": "revision_cancelled_by_approval",
                               "restored": f"r{latest}"})
    (run / APPROVED).write_text(text, encoding="utf-8")
    applied = apply_approved_plan(run, plan, commit=commit, link=record.pr_url)
    record.status, record.approved_commit = "drafting", commit
    record.history.append({"at": _now().isoformat(), "event": "approval_read", "commit": commit})
    lines = [f"Plan approved at {commit[:12]}. DocForge drafts:"]
    lines += [f"- `{p['dest']}` ({p['src'].split('/')[0]})" for p in applied["placements"]]
    if applied["needs_own_run"]:
        lines += ["", "These articles need their own run; this run drafts one article of each type and no updates "
                  "to existing articles yet:"] + [f"- {x}" for x in applied["needs_own_run"]]
    reply(run, record, config, "approved", "\n".join(lines), client)
    save_plan(run, record)
    return {"result": "approved", **applied}


def process_plan_pr(run: Path, *, config: DocForgeConfig, checkout: Path | None, client=None, backend_client=None,
                    now: datetime | None = None, on_approved=None) -> dict:
    """Act on the plan pull request's recorded review as far as it can go. Returns what happened."""
    from docforge.github.push import fetch_branch

    record = load_plan(run, KIND)
    result = {"run": str(run), "pull_request": record.pr_number, "kind": KIND}
    if record.status not in ACTIVE:
        return {**result, "result": "nothing pending", "status": record.status}
    collection = config.doc_collections.get(record.repo)
    if collection is None:
        raise DocsPrError(f"doc collection {record.repo!r} is not in the config")
    if checkout is None:
        raise DocsPrError("no docs checkout: set the doc collection's checkout or pass --docs-checkout")
    now = now or _now()
    _promote(record)
    save_plan(run, record)

    if record.status == "approved":
        try:
            outcome = _read_approval(run, record, config, checkout, client)
        except (PublishError, DocsPrError) as exc:
            return {**result, "result": "failed", "reason": str(exc)}
        if outcome["result"] == "approved" and on_approved is not None:
            on_approved(run)
        return {**result, **outcome}

    if record.status == "changes_requested":
        if record.last_request_at and now < datetime.fromisoformat(record.last_request_at) + timedelta(
                seconds=collection.revision_delay_seconds):
            return {**result, "result": "waiting", "reason": "waiting for the review to finish"}
        if record.automatic_revisions >= collection.max_revisions:
            if not any(r["kind"] == "revision_limit" for r in record.replies):
                reply(run, record, config, "revision_limit", f"DocForge has revised this plan "
                      f"{record.automatic_revisions} times, the most it does on its own. Edit the plan file directly.",
                      client)
                save_plan(run, record)
            return {**result, "result": "limit"}
        tip = record.pushed_commit
        if record.pushed_commit:  # only a pushed branch can have been edited by someone else
            _, git_url, token = _git(config, record)
            try:
                tip = fetch_branch(checkout, record.branch, git_url, token)
            except PublishError as exc:
                return {**result, "result": "failed", "reason": str(exc)}
        if record.pushed_commit and tip != record.pushed_commit:
            record.status = "hand_edited"
            record.history.append({"at": now.isoformat(), "event": "hand_edited", "tip": tip})
            reply(run, record, config, "hand_edited",
                  "Someone pushed changes to this plan, so DocForge will not rewrite the file. The open requests "
                  "are left for the writer; approving the pull request still starts drafting from it.", client)
            save_plan(run, record)
            return {**result, "result": "hand_edited"}
        from docforge.jira.work import _archive_plan

        folder = run / "analysis" / "revisions"
        number = len([p for p in folder.glob("r*") if p.is_dir()]) if folder.is_dir() else 0
        pending = [r for r in record.requests if not r.get("used")]
        feedback = "\n".join(f"{r['author']}: {r['body']}" for r in pending)
        _archive_plan(run, number, feedback, ", ".join(sorted({r["author"] for r in pending})) or None)
        for r in pending:
            r["used"] = True
        record.status = "revising"
        record.history.append({"at": now.isoformat(), "event": "revising", "archive": f"r{number}"})
        save_plan(run, record)

    # status "revising": the Analyzer runs again (backend) or a session does it.
    from docforge.jira.work import _restore_plan, _stage_done

    if not _stage_done(run, 1):
        if config.backend is None:
            return {**result, "result": "waiting", "reason": "a Claude Code session runs the Analyzer again",
                    "work_order": "prompts/1-analyzer.md"}
        from docforge.backend import BackendError, exec_run

        try:
            outcomes = exec_run(run, repo_of(run), config, only=1, repair=1, client=backend_client)
            failed = next((o for o in outcomes if o.status == "failed"), None)
            message = f"{failed.stage}: {failed.message}" if failed else ""
        except BackendError as exc:
            message = str(exc)
        if message:
            return _revision_failed(run, record, config, message, client, _restore_plan)
    plan, errors = check_run_plan(run, config)
    if errors:
        return _revision_failed(run, record, config, "ia-plan.md has problems: " + "; ".join(errors[:5]), client,
                                _restore_plan)
    from docforge.publish import open_pr
    from docforge.publish.branch import update_branch
    from docforge.plan.pr import plan_body

    dest = record.placements[0]["dest"]
    try:
        updated = update_branch(checkout, record.branch, record.commit, [(run / IA_PLAN, dest)],
                                f"{record.title} (revision {record.revision + 1})\n\nRevised by DocForge after review "
                                "comments on the plan pull request.")
    except PublishError as exc:
        return {**result, "result": "failed", "reason": str(exc)}
    record.commit, record.revision = updated.commit, record.revision + 1
    record.automatic_revisions += 1
    record.status = "revised"
    record.history.append({"at": now.isoformat(), "event": "updated", "commit": updated.commit,
                           "revision": record.revision})
    (run / "publish" / f"{KIND}-body.md").write_text(plan_body(plan, run, dest), encoding="utf-8")
    save_plan(run, record)
    summary = (f"Plan revision {record.revision} is on `{record.branch}` (commit {updated.commit[:12]}): "
               f"{len(plan.articles())} article(s), {len(plan.questions)} open question(s).")
    policy = config.resolve_policy(trigger=None, doc_collection=record.repo)["publishing"]
    if policy.get("auto_create_pr") and record.pr_number is not None:
        try:
            record = open_pr(run=run, checkout=checkout, config=config, client=client, kind=KIND)
        except PublishError as exc:
            return {**result, "result": "failed", "reason": str(exc)}
        reply(run, record, config, "revised", summary, client)
        save_plan(run, record)
        return {**result, "result": "revised", "pushed": True, "revision": record.revision}
    reply(run, record, config, "revised", summary + " To push it, a person runs `docforge plan open`.", client)
    save_plan(run, record)
    return {**result, "result": "revised", "pushed": False, "revision": record.revision}


def _revision_failed(run, record, config, message, client, restore) -> dict:
    folder = run / "analysis" / "revisions"
    latest = max((int(p.name[1:]) for p in folder.glob("r*") if p.name[1:].isdigit()), default=None)
    if latest is not None:
        restore(run, latest)
    record = load_plan(run, KIND)
    record.status = "revision_failed"
    record.history.append({"at": _now().isoformat(), "event": "revision_failed", "reason": message})
    reply(run, record, config, "revision_failed", f"DocForge could not revise the plan: {message}. The plan is "
          "unchanged; a new review comment starts another attempt.", client)
    save_plan(run, record)
    return {"run": str(run), "pull_request": record.pr_number, "kind": KIND, "result": "failed", "reason": message}
