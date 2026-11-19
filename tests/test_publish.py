import json
from pathlib import Path
import shutil

import pytest
from conftest import git
from test_gate import MARKED, edit, make_run

from docforge.cli import main
from docforge.config import DocForgeConfig, load_config
from docforge.publish import PublishError, create_branch, gate_manifest, mark_ready, prepare_publish
from docforge.run import RunError, start_run

CONFIG_TEXT = (MARKED / "docforge.yaml.txt").read_text(encoding="utf-8")
COLLECTION = "example-org/docs-site"
PLACE = [
    ("feature/feature-guide.md", "site/quiet-hours/index.md"),
    ("how-to/how-to.md", "site/quiet-hours/pause-for-1-hour.md"),
    ("release-note/release-note.md", "site/release-notes/quiet-hours.md"),
]


def config(tmp_path, extra: str = "") -> DocForgeConfig:
    path = tmp_path / "docforge.yaml"
    path.write_text(CONFIG_TEXT + extra, encoding="utf-8")
    return load_config(path)


@pytest.fixture
def docs(tmp_path):
    """A local docs checkout with one existing page on main."""
    root = tmp_path / "docs-site"
    (root / "site" / "release-notes").mkdir(parents=True)
    git(root, "init", "-q", "-b", "main")
    (root / "site" / "release-notes" / "quiet-hours.md").write_text("# Old note\n\nOld text.\n", encoding="utf-8")
    (root / "README.md").write_text("# Docs\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "init")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.com")
    (root / "notes.txt").write_text("uncommitted local work\n", encoding="utf-8")
    return root


def prepare(tmp_path, docs, out=None, cfg=None, place=PLACE, **kwargs):
    return prepare_publish(run=out or make_run(tmp_path), checkout=docs, config=cfg or config(tmp_path),
                           collection=COLLECTION, placements=place, **kwargs)


# --- prepare -------------------------------------------------------------------------


def test_prepare_creates_local_branch_without_touching_checkout(tmp_path, docs):
    head_before = git(docs, "rev-parse", "HEAD")
    status_before = git(docs, "status", "--porcelain")
    plan = prepare(tmp_path, docs)
    assert plan.branch == "docforge/qh-docs"
    assert git(docs, "rev-parse", "HEAD") == head_before
    assert git(docs, "branch", "--show-current") == "main"
    assert git(docs, "status", "--porcelain") == status_before  # notes.txt still untracked, nothing staged
    assert git(docs, "rev-parse", plan.branch) == plan.commit
    assert git(docs, "rev-parse", f"{plan.branch}^") == head_before
    assert {(f["path"], f["change"]) for f in plan.files} == {
        ("site/quiet-hours/index.md", "added"),
        ("site/quiet-hours/pause-for-1-hour.md", "added"),
        ("site/release-notes/quiet-hours.md", "modified"),
        ("site/_docforge/qh-docs.evidence.json", "added"),
    }
    assert "Prepared by DocForge from run qh-docs" in git(docs, "log", "-1", "--format=%B", plan.branch)


def test_links_between_placed_pages_are_rewritten(tmp_path, docs):
    plan = prepare(tmp_path, docs)
    page = git(docs, "show", f"{plan.branch}:site/quiet-hours/index.md")
    assert "[Pause in-app alerts for 1 hour](pause-for-1-hour.md)" in page
    assert "../how-to/how-to.md" not in page


def test_pr_plan_and_body(tmp_path, docs):
    out = make_run(tmp_path)
    plan = prepare(tmp_path, docs, out=out)
    assert (plan.draft, plan.action, plan.gate_passed) == (True, "awaiting_approval", True)
    assert plan.policy["auto_create_pr"] is False
    assert plan.source_pr == {"repo": "example-org/pulseboard-web", "number": 42, "state": "open"}
    push, create = plan.commands
    assert push.endswith("push origin docforge/qh-docs:docforge/qh-docs")
    assert "gh pr create --repo example-org/docs-site --base main --head docforge/qh-docs" in create
    assert create.endswith("--draft")
    body = (out / "publish" / "pr-body.md").read_text(encoding="utf-8")
    for expected in [
        "A person must review and approve this pull request",
        "stays a **draft** while its source change is not merged",
        "- Source PR: `example-org/pulseboard-web#42` (open)",
        "| S1 | `demo/mock-prd.md` |",
        "| `release-note/release-note.md` | `site/release-notes/quiet-hours.md` | modified |",
        "**PASS**: 17 statement(s), 16 backed by claims, 1 exempt, 0 error(s).",
        "(navigation link)",
        "| BLOCKED | C08, C09, C10, C11 |",
        "**Publication: conditional.**",
        "- **Q01** Until tomorrow boundary",
        "Structural check: not run",
    ]:
        assert expected in body, expected
    saved = json.loads((out / "publish" / "pr.json").read_text(encoding="utf-8"))
    assert saved["commit"] == plan.commit and saved["history"][0]["event"] == "prepared"


def test_evidence_manifest_lets_docs_ci_rerun_the_gate(tmp_path, docs):
    plan = prepare(tmp_path, docs)
    site = tmp_path / "published"
    for path in [f["path"] for f in plan.files]:
        (site / path).parent.mkdir(parents=True, exist_ok=True)
        (site / path).write_text(git(docs, "show", f"{plan.branch}:{path}") + "\n", encoding="utf-8")
    manifest = site / "site/_docforge/qh-docs.evidence.json"
    assert gate_manifest(manifest, site).passed
    page = site / "site/quiet-hours/pause-for-1-hour.md"
    page.write_text(page.read_text(encoding="utf-8").replace(" <!-- evidence: C07 -->", ""), encoding="utf-8")
    result = gate_manifest(manifest, site)
    assert not result.passed
    assert result.errors[0].path == "site/quiet-hours/pause-for-1-hour.md"


def test_merged_source_is_not_draft(tmp_path, docs):
    out = make_run(tmp_path, source_state="merged")
    plan = prepare(tmp_path, docs, out=out)
    assert plan.draft is False
    assert not plan.commands[1].endswith("--draft")


def test_policy_rule_can_allow_automatic_creation(tmp_path, docs):
    cfg = config(tmp_path, "policies:\n  rules:\n    - if: {doc_collection: example-org/docs-site}\n"
                           "      then: {publishing: {auto_create_pr: true}}\n")
    plan = prepare(tmp_path, docs, cfg=cfg)
    assert plan.action == "allowed_by_policy_no_github_connection"


# --- refusals --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "place, message",
    [
        ([("feature/feature-guide.md", "docs/elsewhere.md")], "outside the example-org/docs-site filter"),
        ([("analysis/HANDOVER.md", "site/handover.md")], "is not a deliverable"),
        ([("feature/feature-guide.md", "site/../secret.md")], "stay inside the repository"),
        ([("feature/feature-guide.md", "site/a.md"), ("how-to/how-to.md", "site/a.md")], "two pages placed"),
        ([], "use --place"),
    ],
)
def test_bad_placements(tmp_path, docs, place, message):
    with pytest.raises(PublishError, match=message):
        prepare(tmp_path, docs, place=place)
    assert "docforge/qh-docs" not in git(docs, "branch", "--list")


def test_gate_failure_blocks_branch(tmp_path, docs):
    out = make_run(tmp_path)
    edit(out, "how-to/how-to.md", " <!-- evidence: C07 -->", "")
    with pytest.raises(PublishError, match="the claim gate failed with 1 error"):
        prepare(tmp_path, docs, out=out)
    assert git(docs, "branch", "--list", "docforge/*") == ""
    assert not (out / "publish" / "pr.json").exists()


def test_never_prepares_twice_or_reuses_branch(tmp_path, docs):
    out = make_run(tmp_path)
    prepare(tmp_path, docs, out=out)
    with pytest.raises(PublishError, match="already prepared"):
        prepare(tmp_path, docs, out=out)
    with pytest.raises(PublishError, match="already exists"):
        create_branch(docs, "docforge/qh-docs", "main", [(out / "how-to" / "how-to.md", "site/x.md")], "m")


def test_branch_rules(tmp_path, docs):
    page = tmp_path / "p.md"
    page.write_text("# P\n", encoding="utf-8")
    with pytest.raises(PublishError, match="must start with 'docforge/'"):
        create_branch(docs, "feature/x", "main", [(page, "site/p.md")], "m")
    with pytest.raises(PublishError, match="base branch 'release' not found"):
        create_branch(docs, "docforge/x", "release", [(page, "site/p.md")], "m")
    same = tmp_path / "README.md"
    same.write_text("# Docs\n", encoding="utf-8")
    with pytest.raises(PublishError, match="identical to main"):
        create_branch(docs, "docforge/y", "main", [(same, "README.md")], "m")
    with pytest.raises(PublishError, match="not a Git checkout"):
        create_branch(tmp_path, "docforge/z", "main", [(page, "site/p.md")], "m")


def test_unknown_collection(tmp_path, docs):
    with pytest.raises(PublishError, match="not in the config"):
        prepare_publish(run=make_run(tmp_path), checkout=docs, config=config(tmp_path), collection="other/repo",
                        placements=PLACE)


# --- ready ---------------------------------------------------------------------------


def test_ready_after_source_merges(tmp_path, docs):
    out = make_run(tmp_path)
    prepare(tmp_path, docs, out=out)
    with pytest.raises(PublishError, match="only after its source change is merged"):
        mark_ready(out, "open")
    plan = mark_ready(out, "merged")
    assert plan.draft is False
    assert plan.commands == ["gh pr ready docforge/qh-docs --repo example-org/docs-site"]
    assert plan.source_pr["state"] == "merged"
    assert [h["event"] for h in plan.history] == ["prepared", "source_merged"]
    with pytest.raises(PublishError, match="already marked ready"):
        mark_ready(out, "merged")


# --- run start options ------------------------------------------------------------------


def test_drafter_work_order_asks_for_markers(tmp_path):
    out = make_run(tmp_path)
    manifest = json.loads((out / "run.json").read_text(encoding="utf-8"))
    assert manifest["publish"] == {"collection": COLLECTION}
    drafter = (out / "prompts" / "2-drafter.md").read_text(encoding="utf-8")
    assert "<!-- evidence: C03, C07 -->" in drafter and "docforge gate output/qh-docs" in drafter


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"source_pr": "pulseboard#42"}, "owner/repo#123"),
        ({"source_pr": "example-org/web#0"}, "owner/repo#123"),
        ({"source_pr": "example-org/web#4", "source_state": "closed"}, "open or merged"),
        ({"source_state": "merged"}, "needs --source-pr"),
        ({"publish_to": "docs"}, "--publish-to must be owner/repo"),
    ],
)
def test_run_start_publish_validation(tmp_path, kwargs, message):
    repo = tmp_path / "repo"
    (repo / "demo").mkdir(parents=True)
    shutil.copy(Path(__file__).resolve().parent.parent / "demo" / "mock-prd.md", repo / "demo" / "mock-prd.md")
    with pytest.raises(RunError, match=message):
        start_run(repo=repo, prds=["demo/mock-prd.md"], out=repo / "output" / "x", audience="a", **kwargs)


# --- CLI ------------------------------------------------------------------------------


def test_cli_publish_prepare_and_ready(tmp_path, docs, capsys):
    out = make_run(tmp_path)
    cfg = tmp_path / "docforge.yaml"
    cfg.write_text(CONFIG_TEXT, encoding="utf-8")
    args = ["publish", "prepare", str(out), "--docs-checkout", str(docs), "--config", str(cfg)]
    for src, dest in PLACE:
        args += ["--place", f"{src}={dest}"]
    assert main(args) == 0
    text = capsys.readouterr().out
    assert "Created local branch docforge/qh-docs" in text and "(not pushed)" in text
    assert "policy action: awaiting_approval" in text
    assert "gh pr create --repo example-org/docs-site" in text
    assert main(args) == 1
    assert "already prepared" in capsys.readouterr().err
    assert main(["publish", "ready", str(out), "--source-state", "merged"]) == 0
    assert "gh pr ready docforge/qh-docs" in capsys.readouterr().out
