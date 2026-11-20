"""The advisory docs check on a code pull request: a commit status that is always "success", so it can
never block a merge, and, when docs are needed or a person must confirm, one comment that later pushes
edit rather than repeat. Nothing is posted unless the `source_pr_feedback` policy is on; the
`suppress_source_pr_comments` policy still stops the comment."""

from __future__ import annotations

from docforge.config import DocForgeConfig

CONTEXT = "docforge/docs"
MARKER = "<!-- docforge-docs-check -->"
FOOTER = "_Posted by DocForge. Advisory only: it never blocks a merge. A person reviews and approves every docs change._"
HEADLINE = {
    "quiet": "No docs needed",
    "act": "Docs needed",
    "confirm": "Docs may be needed: please confirm",
}


def describe(outcome: str, reasons: list[str]) -> str:
    """The status description (GitHub allows 140 characters)."""
    text = f"{HEADLINE[outcome]}: {reasons[0]}" if reasons else HEADLINE[outcome]
    return text if len(text) <= 140 else text[:137] + "..."


def comment_body(outcome: str, category: str | None, reasons: list[str], *, products: list[str], owners: list[str]) -> str:
    lines = [MARKER, f"**DocForge: {HEADLINE[outcome]}**", ""]
    lines += [f"- {r}" for r in reasons]
    if category:
        lines += ["", f"Category: `{category}`."]
    if products:
        lines.append(f"Product: {', '.join(products)}." + (f" Writer: {', '.join(owners)}." if owners else ""))
    if outcome == "confirm":
        lines += ["", "A person decides whether this change needs docs. DocForge plans nothing until then."]
    elif outcome == "act":
        lines += ["", "DocForge proposes the docs plan in the docs repository for a writer to review."]
    else:
        lines += ["", "An earlier push needed docs; this one does not."]
    return "\n".join(lines + ["", FOOTER])


def post_feedback(config: DocForgeConfig, *, repo: str, number: int, sha: str, outcome: str, category: str | None,
                  reasons: list[str], products: list[str], owners: list[str], trigger: str | None = None,
                  client=None) -> dict:
    """Post (or explain why not) the advisory status and comment. Never raises for GitHub problems."""
    from docforge.github import GithubClient, GithubError

    code_repo = next((r for name, r in config.code_repos.items() if name.casefold() == repo.casefold()), None)
    policy = config.resolve_policy(trigger=trigger, doc_collection=code_repo.doc_collection if code_repo else None)[
        "publishing"]
    result = {"status": "not posted", "comment": "not posted"}
    if not policy.get("source_pr_feedback"):
        result["note"] = "the source_pr_feedback policy is off"
        return result
    if code_repo is None:
        result["note"] = f"{repo} is not in the dependency map, so DocForge has no connection for it"
        return result
    if not sha:
        result["note"] = "the pull request's head commit is unknown"
        return result
    try:
        client = client or GithubClient(code_repo)
        client.set_status(repo, sha, state="success", context=CONTEXT, description=describe(outcome, reasons))
        result["status"] = "posted"
        if policy.get("suppress_source_pr_comments"):
            result["comment"] = "suppressed by policy"
            return result
        existing = client.find_comment(repo, number, MARKER)
        if outcome == "quiet" and existing is None:
            result["comment"] = "none needed"
            return result
        body = comment_body(outcome, category, reasons, products=products, owners=owners)
        if existing is not None:
            client.update_comment(repo, existing["id"], body)
            result["comment"] = "updated"
        else:
            client.comment(repo, number, body)
            result["comment"] = "posted"
    except GithubError as exc:
        result["note"] = str(exc)
    return result
