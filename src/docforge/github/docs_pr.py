"""Review on DocForge's own docs pull requests: GitHub feedback becomes revisions.

`handle_docs_event` records what a delivery means for a run (a change request, answers, a line comment
waiting for its review, the pull request merged or closed) in the run's files. It never calls a model or
GitHub. `process_revision` later runs the pending revision (through the API backend, or by waiting for a
Claude Code session), commits it to the same branch, pushes it and replies on the pull request, when the
`auto_create_pr` policy allows; otherwise the reply waits in `publish/pr.json` with the command a person runs.

Only reviewers whose `author_association` the doc collection lists count. Bots and DocForge itself are
ignored, as are edits, deletions and anything on a merged or closed pull request. A revision starts only
after a quiet period, so one review that arrives as several deliveries becomes one revision, and at most
`max_revisions` revisions run automatically.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from docforge.config import DocCollection, DocForgeConfig
from docforge.publish import PrPlan, PublishError, load_plan, save_plan

from .events import DocsPrEvent, mentions, strip_mention

FOOTER = "_Posted by DocForge. A person reviews and approves every change._"
MAX_PROCESSED = 500
SEARCH_DEPTH = 4
BLOCKED = {"conflicting", "unknown", "needs_engineering"}


class DocsPrError(Exception):
    """A docs pull request event or revision cannot be handled."""


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _iso(when: datetime) -> str:
    return when.isoformat()


# --- finding runs ------------------------------------------------------------------------


def find_runs(roots: list[Path], kinds: tuple[str, ...] = ("pr",)) -> list[tuple[Path, PrPlan]]:
    """(run, pull request record) for runs up to four levels under each root. `kinds`: "pr" (the drafts)
    and/or "plan-pr" (the ia-plan.md pull request); each record's `kind` says which it is."""
    found, seen = [], set()
    for root in roots:
        for depth in range(SEARCH_DEPTH + 1):
            for kind in kinds:
                for path in sorted(root.glob("/".join(["*"] * depth + ["publish", f"{kind}.json"]))):
                    run = path.parent.parent.resolve()
                    if (run, kind) in seen:
                        continue
                    seen.add((run, kind))
                    try:
                        found.append((run, load_plan(run, kind)))
                    except (PublishError, ValueError):
                        continue
    return found


def find_run(roots: list[Path], repo: str, number: int, branch: str | None = None,
             kinds: tuple[str, ...] = ("pr", "plan-pr")) -> tuple[Path, PrPlan] | None:
    for run, plan in find_runs(roots, kinds):
        if plan.repo.casefold() != repo.casefold():
            continue
        if plan.pr_number == number or (branch is not None and plan.branch == branch and plan.pr_number is None):
            return run, plan
    return None


def repo_of(run: Path) -> Path:
    """The folder run.json's source paths are relative to: the nearest parent that holds the first source."""
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    first = next((s["path"] for s in manifest.get("sources", []) if s.get("path")), None)
    for parent in [run, *run.parents]:
        if first and (parent / first).is_file():
            return parent
    raise DocsPrError(f"cannot find the repository the sources of {run} are relative to")


# --- replies -----------------------------------------------------------------------------


def _policy(config: DocForgeConfig, plan: PrPlan, run: Path) -> dict:
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    return config.resolve_policy(trigger=manifest.get("trigger"), doc_collection=plan.repo)["publishing"]


def reply(run: Path, plan: PrPlan, config: DocForgeConfig, kind: str, text: str, client=None) -> dict:
    """Post a reply on the pull request when the policy allows; otherwise keep it in pr.json, unsent."""
    body = f"{text}\n\n{FOOTER}"
    entry = {"at": _iso(_now()), "kind": kind, "body": body, "sent": False, "note": ""}
    if not _policy(config, plan, run).get("auto_create_pr"):
        entry["note"] = "not sent: the auto_create_pr policy is off"
    elif plan.pr_number is None:
        entry["note"] = "not sent: the pull request is not open on GitHub"
    else:
        from docforge.github import GithubClient, GithubError

        try:
            client = client or GithubClient(config.doc_collections[plan.repo])
            client.comment(plan.repo, plan.pr_number, body)
            entry["sent"] = True
        except GithubError as exc:
            entry["note"] = f"not sent: {exc}"
    plan.replies.append(entry)
    return entry


# --- recording events --------------------------------------------------------------------


def _remember(plan: PrPlan, delivery_id: str | None) -> None:
    if delivery_id:
        plan.processed = (plan.processed + [delivery_id])[-MAX_PROCESSED:]


def _reviewer_problem(event: DocsPrEvent, collection: DocCollection) -> str | None:
    if event.author_type == "Bot" or event.author.endswith("[bot]"):
        return "comment by a bot"
    if collection.bot_login and event.author.casefold() == collection.bot_login.casefold():
        return "comment by DocForge itself"
    if event.association not in collection.reviewer_associations:
        return f"{event.author or 'someone'} is not a reviewer ({event.association or 'no association'})"
    return None


def _cross_questions(run: Path) -> dict[int, dict]:
    path = run / "analysis" / "cross-source.json"
    if not path.is_file():
        return {}
    found = {}
    for result in json.loads(path.read_text(encoding="utf-8")):
        qid = result.get("question_id") or ""
        if qid.startswith("X") and qid[1:].isdigit() and result.get("status") in BLOCKED:
            found[int(qid[1:])] = result
    return found


def record_answers(run: Path, plan: PrPlan, event: DocsPrEvent, plan_answers: dict[int, str],
                   cross_answers: dict[int, str]) -> tuple[str | None, list[str], list[str]]:
    """(answer source ID, labels answered, unknown labels). Nothing is written when any label is unknown."""
    from docforge.jira.answers import question_ids, write_labelled_answers
    from docforge.jira.runfiles import open_questions
    from docforge.run import RunError, add_sources

    questions = open_questions(run)
    labels = question_ids(questions)
    cross = _cross_questions(run)
    unknown = [f"Q{n}" for n in sorted(plan_answers) if n not in labels]
    unknown += [f"X{n}" for n in sorted(cross_answers) if n not in cross]
    if unknown:
        return None, [], unknown
    texts = {q.split(":", 1)[0].strip(): q.split(":", 1)[1].strip() for q in questions if ":" in q}
    texts.update({f"X{n}": r.get("question", "") for n, r in cross.items()})
    answers = {labels[n]: a for n, a in plan_answers.items()}
    answers.update({f"X{n}": a for n, a in cross_answers.items()})

    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    repo = repo_of(run)
    earlier = next((s["path"] for s in manifest["sources"] if s.get("kind") == "answer"), None)
    folder = (repo / earlier).parent if earlier else run / "answers"
    taken = {s["id"] for s in manifest["sources"]}
    source_id, path = write_labelled_answers(
        folder, key=f"{plan.repo}#{plan.pr_number}", answers=answers, questions=texts, by=event.author,
        comment_id=str(event.comment_id or event.review_id or "unknown"), created=event.created, taken=taken,
        role="a pull request reviewer")
    from docforge.jira.work import ANSWERS_NOTE

    try:
        added = add_sources(run, repo, [path], note=ANSWERS_NOTE)
    except RunError as exc:
        path.unlink(missing_ok=True)
        raise DocsPrError(str(exc)) from None
    if cross_answers:
        file = run / "analysis" / "resolutions.json"
        resolved = json.loads(file.read_text(encoding="utf-8")) if file.is_file() else []
        for n in sorted(cross_answers):
            resolved.append({"claim_id": cross[n]["claim_id"], "question_id": f"X{n}", "source_id": source_id,
                             "sha256": added[0]["sha256"], "by": event.author, "at": _iso(_now())})
        file.write_text(json.dumps(resolved, indent=2) + "\n", encoding="utf-8")
    return source_id, sorted(answers), []


def handle_docs_event(event: DocsPrEvent, *, run: Path, config: DocForgeConfig, delivery_id: str | None = None,
                      client=None) -> dict:
    """Record what one delivery means for the run. Returns what happened."""
    from docforge.jira.answers import split_answers
    from docforge.review import ReviewError, request_changes

    plan = load_plan(run)
    result = {"run": str(run), "pull_request": plan.pr_number, "event": event.kind}
    if delivery_id and delivery_id in plan.processed:
        return {**result, "action": "duplicate"}
    collection = config.doc_collections.get(plan.repo)
    if collection is None:
        raise DocsPrError(f"doc collection {plan.repo!r} is not in the config")

    if event.kind in ("merged", "closed"):
        plan.github_state = event.kind
        if event.kind == "closed":
            plan.status = "closed"
        plan.history.append({"at": _iso(_now()), "event": f"github_{event.kind}"})
        _remember(plan, delivery_id)
        save_plan(run, plan)
        return {**result, "action": event.kind}
    if plan.github_state or plan.status == "closed":
        return {**result, "action": "ignore", "reason": f"the pull request is {plan.github_state or 'closed'}"}
    if event.kind in ("ignore", "pushed"):
        return {**result, "action": "ignore", "reason": event.reason or "new commits on the drafts pull request"}
    problem = _reviewer_problem(event, collection)
    if problem:
        return {**result, "action": "ignore", "reason": problem}

    login = collection.bot_login
    mentioned = mentions(event.body, login)
    text = strip_mention(event.body, login)
    if event.kind == "line_comment":
        dest_to_src = {p["dest"]: p["src"] for p in plan.placements}
        if event.path not in dest_to_src:
            return {**result, "action": "ignore", "reason": f"{event.path} is not one of this pull request's pages"}
        plan.line_comments.append({"id": event.comment_id, "review_id": event.review_id, "page": event.path,
                                   "line": event.line, "body": text, "author": event.author,
                                   "mention": mentioned, "used": False})
        plan.last_request_at = _iso(_now())
        _remember(plan, delivery_id)
        save_plan(run, plan)
        return {**result, "action": "line_comment_recorded"}

    if event.kind == "review" and event.review_state == "changes_requested":
        if event.review_id is not None:
            plan.requested_reviews.append(event.review_id)
    elif not mentioned:
        return {**result, "action": "ignore", "reason": "does not request changes or mention DocForge"}

    plan_answers, cross_answers, feedback = split_answers(text)
    note = ""
    if plan_answers or cross_answers:
        save_plan(run, plan)
        source_id, answered, unknown = record_answers(run, plan, event, plan_answers, cross_answers)
        plan = load_plan(run)
        if unknown:
            reply(run, plan, config, "unknown_questions",
                  f"DocForge did not record these answers: {', '.join(unknown)} "
                  f"{'is' if len(unknown) == 1 else 'are'} not an open question for this pull request. "
                  "Nothing from the comment was used.", client)
            _remember(plan, delivery_id)
            save_plan(run, plan)
            return {**result, "action": "refused", "unknown": unknown}
        note = f"Answers recorded as {source_id}: {', '.join(answered)}."
        result["answers"] = source_id
    comment = "\n".join(part for part in (feedback, note) if part)
    if not comment and event.kind == "review":
        # Changes requested with only line comments: those carry the requests.
        plan.last_request_at = _iso(_now())
        _remember(plan, delivery_id)
        save_plan(run, plan)
        return {**result, "action": "review_recorded"}
    if not comment:
        return {**result, "action": "ignore", "reason": "mention without a request"}
    save_plan(run, plan)
    try:
        feedback_item, _, _ = request_changes(run, comment=comment, reviewer=event.author, origin="github",
                                              github_id=event.comment_id or event.review_id)
    except ReviewError as exc:
        raise DocsPrError(str(exc)) from None
    plan = load_plan(run)
    plan.last_request_at = _iso(_now())
    _remember(plan, delivery_id)
    save_plan(run, plan)
    return {**result, "action": "changes_requested", "feedback_id": feedback_item.feedback_id}


def _promote_line_comments(run: Path) -> int:
    """Line comments become change requests once their review requested changes, or when they mention DocForge."""
    from docforge.review import request_changes

    plan = load_plan(run)
    ready = [c for c in plan.line_comments if not c.get("used")
             and (c.get("mention") or (c.get("review_id") is not None and c["review_id"] in plan.requested_reviews))]
    for item in ready:
        if item.get("body"):
            request_changes(run, comment=item["body"], reviewer=item["author"], page=item["page"],
                            line=item.get("line"), origin="github", github_id=item.get("id"))
        plan = load_plan(run)
        for stored in plan.line_comments:
            if stored.get("id") == item.get("id"):
                stored["used"] = True
        save_plan(run, plan)
    return len(ready)


# --- running revisions ---------------------------------------------------------------------


def process_revision(run: Path, *, config: DocForgeConfig, checkout: Path | None, client=None, backend_client=None,
                     now: datetime | None = None) -> dict:
    """Run the pull request's pending revision as far as it can go. Returns what happened."""
    from docforge.backend import BackendError, exec_revision
    from docforge.publish import open_pr, update_publish

    plan = load_plan(run)
    result = {"run": str(run), "pull_request": plan.pr_number}
    if plan.github_state or plan.status == "closed":
        return {**result, "result": "nothing pending", "reason": f"the pull request is {plan.github_state or 'closed'}"}
    collection = config.doc_collections.get(plan.repo)
    if collection is None:
        raise DocsPrError(f"doc collection {plan.repo!r} is not in the config")
    _promote_line_comments(run)
    plan = load_plan(run)
    now = now or _now()

    if plan.status == "changes_requested":
        if plan.last_request_at and now < datetime.fromisoformat(plan.last_request_at) + timedelta(
                seconds=collection.revision_delay_seconds):
            return {**result, "result": "waiting", "reason": "waiting for the review to finish"}
        if plan.automatic_revisions >= collection.max_revisions:
            if not any(r["kind"] == "revision_limit" for r in plan.replies):
                reply(run, plan, config, "revision_limit",
                      f"DocForge has made {plan.automatic_revisions} revisions to this pull request, the most it makes "
                      "on its own. A person can revise the pages and run `docforge publish update`.", client)
                save_plan(run, plan)
            return {**result, "result": "limit"}
        order = f"prompts/revise-{plan.revision + 1}.md"
        if config.backend is None:
            return {**result, "result": "waiting", "reason": "a Claude Code session carries out the revision order",
                    "work_order": order}
        if checkout is None:
            raise DocsPrError("no docs checkout: set the doc collection's checkout or pass --docs-checkout")
        try:
            outcome = exec_revision(run, repo_of(run), config, order, [p["src"] for p in plan.placements],
                                    client=backend_client)
        except BackendError as exc:
            outcome = None
            message = str(exc)
        else:
            message = outcome.message
        if outcome is None or outcome.status != "done":
            plan = load_plan(run)
            plan.status = "revision_failed"
            plan.history.append({"at": _iso(now), "event": "revision_failed", "reason": message})
            reply(run, plan, config, "revision_failed",
                  f"DocForge could not make revision {plan.revision + 1}: {message}. The pull request is unchanged; "
                  "a new review comment starts another attempt.", client)
            save_plan(run, plan)
            return {**result, "result": "failed", "reason": message}
        try:
            update_publish(run=run, checkout=checkout, config=config)
        except PublishError as exc:
            plan = load_plan(run)
            plan.status = "revision_failed"
            plan.history.append({"at": _iso(now), "event": "revision_failed", "reason": str(exc)})
            save_plan(run, plan)
            return {**result, "result": "failed", "reason": str(exc)}
        plan = load_plan(run)
        plan.automatic_revisions += 1
        save_plan(run, plan)

    plan = load_plan(run)
    if plan.status == "revised" and plan.pushed_commit != plan.commit:
        if checkout is None:
            raise DocsPrError("no docs checkout: set the doc collection's checkout or pass --docs-checkout")
        addressed = [f for f in _feedback(run) if f.revision == plan.revision - 1 and f.action == "request_changes"]
        gate = json.loads((run / "qa" / "gate.json").read_text(encoding="utf-8")) if (run / "qa" / "gate.json").is_file() else {}
        summary = (f"Revision {plan.revision} is on `{plan.branch}` (commit {plan.commit[:12]}). It addresses "
                   + (", ".join(f"{f.feedback_id} from @{f.reviewer}" for f in addressed) or "the review feedback")
                   + f". Claim gate: {'PASS' if gate.get('passed') else 'see the checks'}"
                   + (f" ({gate.get('statements')} statements)." if gate.get("statements") else "."))
        if not _policy(config, plan, run).get("auto_create_pr") or plan.pr_number is None:
            if not any(r["kind"] == "revised" and plan.commit[:12] in r["body"] for r in plan.replies):
                reply(run, plan, config, "revised", summary + " To push it, a person runs `docforge publish open`.",
                      client)
                save_plan(run, plan)
            return {**result, "result": "revised", "pushed": False}
        try:
            open_pr(run=run, checkout=checkout, config=config, client=client)
        except PublishError as exc:
            return {**result, "result": "failed", "reason": str(exc)}
        plan = load_plan(run)
        reply(run, plan, config, "revised", summary, client)
        save_plan(run, plan)
        return {**result, "result": "revised", "pushed": True, "revision": plan.revision}
    return {**result, "result": "nothing pending"}


def _feedback(run: Path):
    from docforge.review import load_feedback

    return load_feedback(run)


def source_merged(roots: list[Path], repo: str, number: int, *, config: DocForgeConfig, client=None) -> list[dict]:
    """A source pull request merged: every docs pull request proposed for it may leave draft."""
    from docforge.publish import apply_ready, mark_ready

    done = []
    for run, plan in find_runs(roots):
        source = plan.source_pr or {}
        if str(source.get("repo", "")).casefold() != repo.casefold() or source.get("number") != number:
            continue
        if plan.status == "closed" or plan.github_state:
            continue
        entry = {"run": str(run), "pull_request": plan.pr_number}
        try:
            if plan.draft:
                plan = mark_ready(run, "merged")
            if _policy(config, plan, run).get("auto_create_pr") and plan.pr_number is not None:
                plan = apply_ready(run=run, config=config, client=client)
                reply(run, plan, config, "ready", f"The source change {repo}#{number} is merged, so DocForge marked "
                      "this pull request ready for review.", client)
                save_plan(run, plan)
                entry["result"] = "ready"
            else:
                entry["result"] = "may leave draft"
        except PublishError as exc:
            entry["result"], entry["reason"] = "failed", str(exc)
        done.append(entry)
    return done
