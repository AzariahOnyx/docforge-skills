"""Live GitHub (B7a): placement from pack templates, pushing the branch, opening and readying the draft PR.

A fake GitHub API (tests/github_stub.py) and a local bare repository stand in for GitHub. No network.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

import pytest
from conftest import git
from github_stub import FakeGithub
from test_gate import make_run
from test_publish import COLLECTION, PLACE, config, docs  # noqa: F401

from docforge.cli import main
from docforge.config import DocForgeConfig
from docforge.github import GithubClient, GithubError, graphql_url, push_branch, web_git_url
from docforge.publish import (
    PublishError,
    apply_ready,
    load_plan,
    mark_ready,
    open_pr,
    pack_placements,
    prepare_publish,
)

ROOT = Path(__file__).resolve().parents[1]
DEMO_PACK = ROOT / "tests" / "fixtures" / "packs" / "demo"
TOKEN = "fictional-github-token"
FRONT = {
    "feature/feature-guide.md": "---\ntitle: Pause in-app alerts with Quiet Hours\ncategory: Notifications\n---\n\n",
    "how-to/how-to.md": "---\ntitle: Pause your alerts\ncategory: Notifications\nslug: pause-for-1-hour\n---\n\n",
    "release-note/release-note.md": "---\ntitle: 'Quiet Hours: pause in-app alerts'\n---\n\n",
}


@pytest.fixture
def github(monkeypatch):
    server = FakeGithub(TOKEN)
    monkeypatch.setenv("GITHUB_TOKEN", TOKEN)
    yield server
    server.close()


@pytest.fixture
def remote(tmp_path, docs):  # noqa: F811
    bare = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    git(docs, "push", "-q", str(bare), "main:main")
    return bare


def gh_config(tmp_path, github, remote, extra: str = "") -> DocForgeConfig:
    return config(tmp_path, f"    api_url: {github.url}\n    git_url: file://{remote}\n" + extra)


def prepared(tmp_path, docs, cfg, place=PLACE, **run_kwargs):  # noqa: F811
    run = make_run(tmp_path, **run_kwargs)
    return run, prepare_publish(run=run, checkout=docs, config=cfg, collection=COLLECTION, placements=place)


# --- placement ---------------------------------------------------------------------------


def _with_front_matter(run: Path, front=FRONT):
    for rel, header in front.items():
        (run / rel).write_text(header + (run / rel).read_text())


def test_pack_placements_fill_templates_from_front_matter(tmp_path):
    run = make_run(tmp_path, pack=DEMO_PACK, product="alerts")
    _with_front_matter(run)
    when = datetime(2026, 11, 19, tzinfo=timezone.utc)
    assert pack_placements(run, now=when) == [
        ("feature/feature-guide.md", "site/alerts/notifications/pause-in-app-alerts-with-quiet-hours.md"),
        ("how-to/how-to.md", "site/alerts/notifications/pause-for-1-hour.md"),
        ("release-note/release-note.md", "site/release-notes/2026-11/quiet-hours-pause-in-app-alerts.md"),
    ]


def test_missing_front_matter_is_an_error_not_a_guess(tmp_path):
    run = make_run(tmp_path, pack=DEMO_PACK, product="alerts")
    _with_front_matter(run, {**FRONT, "how-to/how-to.md": "---\ntitle: Pause your alerts\n---\n\n"})
    with pytest.raises(PublishError, match=r"how-to/how-to.md: cannot place it .* no category \(from front matter\)"):
        pack_placements(run)


def test_prepare_without_place_uses_the_pack(tmp_path, docs):  # noqa: F811
    run = make_run(tmp_path, pack=DEMO_PACK, product="alerts")
    _with_front_matter(run)
    plan = prepare_publish(run=run, checkout=docs, config=config(tmp_path), collection=COLLECTION, placements=[])
    assert "site/alerts/notifications/pause-for-1-hour.md" in {f["path"] for f in plan.files}


def test_placement_templates_are_checked():
    from docforge.packs.model import Placement

    with pytest.raises(ValueError, match="unknown field"):
        Placement(applies_to=["how-to/"], path="site/{team}/{slug}.md")
    with pytest.raises(ValueError, match="needs \\{slug\\}"):
        Placement(applies_to=["how-to/"], path="site/{product}/index.md")
    with pytest.raises(ValueError, match="relative path"):
        Placement(applies_to=["how-to/"], path="../{slug}.md")


# --- push --------------------------------------------------------------------------------


def test_push_sends_only_the_recorded_docforge_branch(tmp_path, docs, remote):  # noqa: F811
    _, plan = prepared(tmp_path, docs, config(tmp_path))
    push_branch(docs, plan.branch, plan.commit, f"file://{remote}", None)
    assert git(remote, "rev-parse", plan.branch) == plan.commit
    with pytest.raises(PublishError, match="only DocForge branches"):
        push_branch(docs, "main", git(docs, "rev-parse", "main"), f"file://{remote}", None)
    git(docs, "branch", "-f", plan.branch, "main")  # someone moved the local branch
    with pytest.raises(PublishError, match="commits DocForge did not record"):
        push_branch(docs, plan.branch, plan.commit, f"file://{remote}", None)


def test_push_never_forces(tmp_path, docs, remote):  # noqa: F811
    _, plan = prepared(tmp_path, docs, config(tmp_path))
    push_branch(docs, plan.branch, plan.commit, f"file://{remote}", None)
    other = tmp_path / "other"
    subprocess.run(["git", "clone", "-q", "-b", plan.branch, str(remote), str(other)], check=True)
    (other / "extra.md").write_text("someone else\n")
    git(other, "add", ".")
    git(other, "-c", "user.name=O", "-c", "user.email=o@example.com", "commit", "-q", "-m", "other")
    git(other, "push", "-q", "origin", plan.branch)
    rewritten = git(docs, "commit-tree", f"{plan.commit}^{{tree}}", "-p", "main", "-m", "rewrite")
    git(docs, "branch", "-f", plan.branch, rewritten)
    with pytest.raises(PublishError, match="git push of docforge/qh-docs failed"):
        push_branch(docs, plan.branch, rewritten, f"file://{remote}", None)


def test_https_push_needs_a_token_and_never_shows_it(tmp_path, docs):  # noqa: F811
    _, plan = prepared(tmp_path, docs, config(tmp_path))
    with pytest.raises(PublishError, match="no GitHub token"):
        push_branch(docs, plan.branch, plan.commit, "https://127.0.0.1:9/example-org/docs-site.git", None)
    with pytest.raises(PublishError) as failed:
        push_branch(docs, plan.branch, plan.commit, "https://127.0.0.1:9/example-org/docs-site.git", TOKEN)
    assert TOKEN not in str(failed.value)


# --- client ------------------------------------------------------------------------------


def test_urls():
    assert graphql_url("https://api.github.com") == "https://api.github.com/graphql"
    assert graphql_url("https://ghe.example.com/api/v3") == "https://ghe.example.com/api/graphql"
    assert web_git_url("https://api.github.com", "o/r") == "https://github.com/o/r.git"


def test_client_needs_token_and_refuses_redirects(monkeypatch, github):
    cfg = DocForgeConfig.model_validate({"doc_collections": {"o/r": {"api_url": github.url}}})
    monkeypatch.delenv("GITHUB_TOKEN")
    with pytest.raises(GithubError, match="GITHUB_TOKEN is not set"):
        GithubClient(cfg.doc_collections["o/r"])
    monkeypatch.setenv("GITHUB_TOKEN", "wrong-token")
    with pytest.raises(GithubError, match="HTTP 401 \\(check the token\\)") as failed:
        GithubClient(cfg.doc_collections["o/r"]).get_pr("o/r", 1)
    assert "wrong-token" not in str(failed.value)


def test_config_checks_github_settings():
    for bad, message in (({"api_url": "http://example.com"}, "https"), ({"token_env": "ghp_abc"}, "variable"),
                         ({"git_url": "https://user:pw@github.com/o/r.git"}, "credentials"),
                         ({"git_url": "https://github.com/o/r"}, "end in .git")):
        with pytest.raises(ValueError, match=message):
            DocForgeConfig.model_validate({"doc_collections": {"o/r": bad}})


# --- open and ready ------------------------------------------------------------------------


def test_open_pushes_and_opens_a_draft_once(tmp_path, docs, github, remote):  # noqa: F811
    cfg = gh_config(tmp_path, github, remote)
    run, plan = prepared(tmp_path, docs, cfg)
    assert plan.draft  # the source PR is not merged
    opened = open_pr(run=run, checkout=docs, config=cfg)
    assert (opened.pr_number, opened.pr_url) == (1, "https://github.example/example-org/docs-site/pull/1")
    pr = github.pulls[1]
    assert pr["draft"] and pr["head"]["ref"] == "docforge/qh-docs" and pr["base"]["ref"] == "main"
    assert pr["body"] == (run / "publish" / "pr-body.md").read_text()
    assert git(remote, "rev-parse", plan.branch) == plan.commit
    assert all(TOKEN not in json.dumps(h) for h in load_plan(run).history)
    assert TOKEN not in (run / "publish" / "pr.json").read_text()

    again = open_pr(run=run, checkout=docs, config=cfg)  # safe to repeat
    assert again.pr_number == 1 and len(github.pulls) == 1
    assert [e["event"] for e in again.history][-3:] == ["pushed", "pr_opened", "pr_updated"]


def test_open_finds_an_existing_pr_instead_of_creating_another(tmp_path, docs, github, remote):  # noqa: F811
    cfg = gh_config(tmp_path, github, remote)
    run, plan = prepared(tmp_path, docs, cfg)
    github.pulls[7] = {"number": 7, "repo": COLLECTION, "node_id": "PR_node7", "state": "open", "draft": True,
                       "title": "t", "body": "old", "head": {"ref": plan.branch}, "base": {"ref": "main"},
                       "html_url": "https://github.example/pr/7"}
    opened = open_pr(run=run, checkout=docs, config=cfg)
    assert opened.pr_number == 7 and github.pulls[7]["body"] != "old" and len(github.pulls) == 1


def test_open_refuses_a_closed_pr(tmp_path, docs, github, remote):  # noqa: F811
    cfg = gh_config(tmp_path, github, remote)
    run, _ = prepared(tmp_path, docs, cfg)
    open_pr(run=run, checkout=docs, config=cfg)
    github.pulls[1]["state"] = "closed"
    with pytest.raises(PublishError, match="is closed"):
        open_pr(run=run, checkout=docs, config=cfg)


def test_ready_only_after_the_source_merged(tmp_path, docs, github, remote):  # noqa: F811
    cfg = gh_config(tmp_path, github, remote)
    run, _ = prepared(tmp_path, docs, cfg)
    open_pr(run=run, checkout=docs, config=cfg)
    with pytest.raises(PublishError, match="stays a draft"):
        apply_ready(run=run, config=cfg)
    assert github.pulls[1]["draft"]
    mark_ready(run, "merged")
    done = apply_ready(run=run, config=cfg)
    assert done.ready_applied and not github.pulls[1]["draft"]
    assert apply_ready(run=run, config=cfg).ready_applied  # repeat is a no-op
    assert sum(1 for r in github.requests if r[1] == "/graphql") == 1


def test_ready_needs_an_opened_pr(tmp_path, docs, github, remote):  # noqa: F811
    cfg = gh_config(tmp_path, github, remote)
    run, _ = prepared(tmp_path, docs, cfg)
    mark_ready(run, "merged")
    with pytest.raises(PublishError, match="not been opened"):
        apply_ready(run=run, config=cfg)
    assert not github.requests


def test_update_then_open_pushes_the_revision(tmp_path, docs, github, remote):  # noqa: F811
    from docforge.publish import update_publish

    cfg = gh_config(tmp_path, github, remote)
    run, _ = prepared(tmp_path, docs, cfg)
    open_pr(run=run, checkout=docs, config=cfg)
    page = run / "how-to" / "how-to.md"
    page.write_text(page.read_text().replace("Use Quiet Hours when", "Use Quiet Hours whenever"))
    revised = update_publish(run=run, checkout=docs, config=cfg)
    after = open_pr(run=run, checkout=docs, config=cfg)
    assert git(remote, "rev-parse", revised.branch) == revised.commit == after.pushed_commit
    assert len(github.pulls) == 1


def test_cli_open_and_ready(tmp_path, docs, github, remote, capsys):  # noqa: F811
    cfg_path = tmp_path / "docforge.yaml"
    run, _ = prepared(tmp_path, docs, gh_config(tmp_path, github, remote))
    assert main(["publish", "open", str(run), "--docs-checkout", str(docs), "--config", str(cfg_path)]) == 0
    assert "pull request #1 (draft)" in capsys.readouterr().out
    assert main(["publish", "ready", str(run), "--source-state", "merged", "--apply", "--config", str(cfg_path)]) == 0
    assert "Marked pull request #1 ready" in capsys.readouterr().out
    assert not github.pulls[1]["draft"]


def test_source_origin_names_flow_pdfs_and_answers():
    from docforge.publish.pr_body import source_origin

    flow = {"kind": "flow", "origin": {"pdf": "pause.pdf", "steps": "2", "fetched_at": "t"}}
    assert source_origin(flow) == "Flow PDF pause.pdf, 2 steps, fetched t"
    answers = {"kind": "answer", "origin": {"id": "PULSE-77 A1", "version": "40002", "fetched_at": "t"}}
    assert source_origin(answers).startswith("Ticket owner answers PULSE-77 A1")
