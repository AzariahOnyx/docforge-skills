import json
from pathlib import Path

import pytest
import yaml
from test_gate import make_run
from test_vale import requires_vale

from docforge.cli import main
from docforge.lint import LintError, lint_run
from docforge.rules import (
    RuleError,
    approve,
    close,
    feedback_digest,
    guidance_lines,
    live_rules,
    load_rule,
    propose,
    try_rule,
)
from docforge.run import start_run

REPO = Path(__file__).resolve().parent.parent


def avoid(folder, **kwargs):
    args = dict(kind="avoid", title="Say connected", message="Prefer 'connected'.", pattern="online",
                replace="connected", proposed_by="Test")
    args.update(kwargs)
    return propose(folder, **args)


def add_feedback(run: Path, feedback_id: str, comment: str, action="request_changes", reason=None):
    (run / "review").mkdir(exist_ok=True)
    with (run / "review" / "feedback.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"feedback_id": feedback_id, "at": "2026-11-17T00:00:00+00:00", "run": run.name,
                            "action": action, "reviewer": "Reviewer", "comment": comment, "reason": reason,
                            "page": None, "line": None, "commit": "a" * 40, "revision": 0}) + "\n")


# --- proposing -------------------------------------------------------------------------


def test_propose_assigns_ids_and_saves_yaml(isolated_rules):
    first = avoid(isolated_rules)
    second = propose(isolated_rules, kind="guidance", title="Name unaffected alerts", message="m",
                     guidance="How-to intros say which alerts are not paused.", proposed_by="Test",
                     origins=[("qh", "80d3877af9ea")])
    assert (first.id, second.id, first.status) == ("R001", "R002", "proposed")
    saved = yaml.safe_load((isolated_rules / "R002.yml").read_text(encoding="utf-8"))
    assert saved["origins"] == [{"run": "qh", "feedback_id": "80d3877af9ea"}]


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"pattern": None}, "needs a pattern"),
        ({"pattern": "(?<=x)y"}, "lookaround or a backreference"),
        ({"pattern": r"(a)\1"}, "lookaround or a backreference"),
        ({"pattern": "a*"}, "matches empty text"),
        ({"pattern": "(unclosed"}, "not a valid regular expression"),
        ({"pattern": "x" * 201}, "longer than 200"),
        ({"replace": "  "}, "replace cannot be empty"),
        ({"guidance": "also guidance"}, "has no guidance text"),
        ({"proposed_by": " "}, "proposed_by is required"),
    ],
)
def test_avoid_rule_validation(isolated_rules, kwargs, message):
    with pytest.raises(RuleError, match=message):
        avoid(isolated_rules, **kwargs)
    assert not list(isolated_rules.glob("R*.yml")) if isolated_rules.exists() else True


def test_guidance_rule_validation(isolated_rules):
    with pytest.raises(RuleError, match="needs guidance text"):
        propose(isolated_rules, kind="guidance", title="t", message="m", proposed_by="T")
    with pytest.raises(RuleError, match="has no pattern"):
        propose(isolated_rules, kind="guidance", title="t", message="m", guidance="g", pattern="x", proposed_by="T")


# --- lifecycle ---------------------------------------------------------------------------


def test_approve_needs_a_current_test(isolated_rules, tmp_path):
    rule = propose(isolated_rules, kind="guidance", title="t", message="m", guidance="Say which alerts continue.",
                   proposed_by="T")
    with pytest.raises(RuleError, match="has not been tested"):
        approve(isolated_rules, rule.id, by="Lead")
    run = make_run(tmp_path)
    try_rule(isolated_rules, rule.id, [run])
    assert load_rule(isolated_rules, rule.id).status == "tested"
    # Edit the wording after testing: approval must be refused until it is tested again.
    path = isolated_rules / f"{rule.id}.yml"
    path.write_text(path.read_text(encoding="utf-8").replace("Say which alerts continue.",
                                                             "Say which alerts keep arriving."), encoding="utf-8")
    assert load_rule(isolated_rules, rule.id).effective_status() == "proposed (changed since test)"
    with pytest.raises(RuleError, match="changed after its last test"):
        approve(isolated_rules, rule.id, by="Lead")
    try_rule(isolated_rules, rule.id, [run])
    live = approve(isolated_rules, rule.id, by="Lead")
    assert (live.status, live.approval.by) == ("live", "Lead")
    with pytest.raises(RuleError, match="already live"):
        approve(isolated_rules, rule.id, by="Lead")


def test_editing_a_live_rule_takes_it_out_of_use(isolated_rules, tmp_path):
    rule = propose(isolated_rules, kind="guidance", title="t", message="m", guidance="Original.", proposed_by="T")
    try_rule(isolated_rules, rule.id, [make_run(tmp_path)])
    approve(isolated_rules, rule.id, by="Lead")
    assert [r.id for r in live_rules(isolated_rules)] == ["R001"]
    path = isolated_rules / "R001.yml"
    path.write_text(path.read_text(encoding="utf-8").replace("Original.", "Changed."), encoding="utf-8")
    assert live_rules(isolated_rules) == []
    assert guidance_lines(isolated_rules) == []


def test_reject_and_retire(isolated_rules, tmp_path):
    rule = propose(isolated_rules, kind="guidance", title="t", message="m", guidance="g", proposed_by="T")
    with pytest.raises(RuleError, match="only live rules are retired"):
        close(isolated_rules, rule.id, status="retired", by="Lead", reason="r")
    rejected = close(isolated_rules, rule.id, status="rejected", by="Lead", reason="Too specific.")
    assert (rejected.status, rejected.closed.reason) == ("rejected", "Too specific.")
    with pytest.raises(RuleError, match="is rejected"):
        try_rule(isolated_rules, rule.id, [make_run(tmp_path)])
    other = propose(isolated_rules, kind="guidance", title="t", message="m", guidance="g2", proposed_by="T")
    try_rule(isolated_rules, other.id, [make_run(tmp_path / "x")])
    approve(isolated_rules, other.id, by="Lead")
    with pytest.raises(RuleError, match="retire it instead"):
        close(isolated_rules, other.id, status="rejected", by="Lead", reason="r")
    assert close(isolated_rules, other.id, status="retired", by="Lead", reason="Superseded.").status == "retired"


# --- guidance ------------------------------------------------------------------------------


def test_guidance_trial_quotes_origin_feedback_and_counts_pages(isolated_rules, tmp_path):
    run = make_run(tmp_path)
    add_feedback(run, "80d3877af9ea", "The intro should say that email alerts are not paused.")
    rule = propose(isolated_rules, kind="guidance", title="Name unaffected alerts", message="m",
                   guidance="How-to intros say which alerts are not paused.", applies_to=["how-to/"],
                   origins=[(run.name, "80d3877af9ea")], proposed_by="T")
    report = try_rule(isolated_rules, rule.id, [run.parent])
    assert (report.runs, report.pages_checked, report.hits) == ([run.name], 1, [])
    assert report.feedback == [f"{run.name} 80d3877af9ea (request_changes, Reviewer): "
                               "The intro should say that email alerts are not paused."]
    assert "cannot be checked automatically" in report.note


def test_live_guidance_reaches_work_orders(isolated_rules, tmp_path):
    run = make_run(tmp_path)
    rule = propose(isolated_rules, kind="guidance", title="t", message="m",
                   guidance="How-to intros say which alerts are not paused.", applies_to=["how-to/"],
                   proposed_by="T")
    try_rule(isolated_rules, rule.id, [run])
    approve(isolated_rules, rule.id, by="Lead")
    repo = run.parent.parent
    new = start_run(repo=repo, prds=["demo/mock-prd.md"], out=repo / "output" / "next", audience="members")
    drafter = (new / "prompts" / "2-drafter.md").read_text(encoding="utf-8")
    assert "- **R001** How-to intros say which alerts are not paused. (applies to pages containing: how-to/)" in drafter
    assert "never overrides the sources" in drafter
    custom = start_run(repo=repo, prds=["demo/mock-prd.md"], out=repo / "output" / "api", audience="developers",
                       profile="custom", deliverables=["api/reference.md"])
    assert "R001" not in (custom / "prompts" / "2-drafter.md").read_text(encoding="utf-8")  # no how-to page


def test_live_guidance_reaches_revision_orders(isolated_rules, tmp_path, docs):  # noqa: F811
    from test_publish import prepare

    from docforge.review import request_changes

    rule = propose(isolated_rules, kind="guidance", title="t", message="m", guidance="Keep intros short.",
                   proposed_by="T")
    out = make_run(tmp_path)
    try_rule(isolated_rules, rule.id, [out])
    approve(isolated_rules, rule.id, by="Lead")
    prepare(tmp_path, docs, out=out)
    _, order, _ = request_changes(out, comment="Shorter intro, please.", reviewer="r")
    text = order.read_text(encoding="utf-8")
    assert "## Learned guidance" in text and "- **R001** Keep intros short." in text


from test_publish import docs  # noqa: E402,F401  (fixture used above)


# --- avoid rules with real Vale --------------------------------------------------------------


@requires_vale
def test_avoid_rule_trial_live_and_retire(isolated_rules, tmp_path, monkeypatch):
    monkeypatch.delenv("DOCFORGE_VALE", raising=False)
    run = make_run(tmp_path)
    rule = avoid(isolated_rules)
    report = try_rule(isolated_rules, rule.id, [run])
    assert report.pages_checked == 3
    assert sorted((h.page, h.match) for h in report.hits) == [
        ("feature/feature-guide.md", "online"), ("how-to/how-to.md", "online"),
        ("release-note/release-note.md", "online")]
    assert lint_run(run).alerts == []  # not live yet
    approve(isolated_rules, rule.id, by="Lead")
    generated = isolated_rules / "vale" / "DocForgeLearned" / "R001.yml"
    assert generated.is_file()
    assert not (REPO / "styles" / "DocForgeLearned").exists()  # never written into the public repo
    result = lint_run(run)
    assert len(result.alerts) == 3 and all("learned rule R001" in a.message for a in result.alerts)
    assert all(a.replacement == "connected" for a in result.alerts)
    assert result.config.endswith("+ live learned rules")
    close(isolated_rules, rule.id, status="retired", by="Lead", reason="Not needed.")
    assert not generated.exists()
    assert lint_run(run).alerts == []


@requires_vale
def test_avoid_rule_applies_to_filter(isolated_rules, tmp_path, monkeypatch):
    monkeypatch.delenv("DOCFORGE_VALE", raising=False)
    run = make_run(tmp_path)
    rule = avoid(isolated_rules, applies_to=["how-to/"])
    report = try_rule(isolated_rules, rule.id, [run])
    assert (report.pages_checked, [h.page for h in report.hits]) == (1, ["how-to/how-to.md"])


def test_avoid_rule_trial_needs_vale(isolated_rules, tmp_path, monkeypatch):
    monkeypatch.setenv("DOCFORGE_VALE", str(tmp_path / "missing"))
    rule = avoid(isolated_rules)
    with pytest.raises(RuleError, match="Vale is needed"):
        try_rule(isolated_rules, rule.id, [make_run(tmp_path)])


@requires_vale
def test_invalid_rule_file_stops_lint(isolated_rules, tmp_path, monkeypatch):
    monkeypatch.delenv("DOCFORGE_VALE", raising=False)
    isolated_rules.mkdir(parents=True, exist_ok=True)
    (isolated_rules / "R001.yml").write_text("id: R001\nkind: nonsense\n", encoding="utf-8")
    (isolated_rules / "vale" / "DocForgeLearned").mkdir(parents=True)
    (isolated_rules / "vale" / "DocForgeLearned" / "R001.yml").write_text("extends: existence\n", encoding="utf-8")
    with pytest.raises(LintError, match="learned rules could not be loaded"):
        lint_run(make_run(tmp_path))


@requires_vale
def test_edited_live_avoid_rule_is_not_applied(isolated_rules, tmp_path, monkeypatch):
    monkeypatch.delenv("DOCFORGE_VALE", raising=False)
    run = make_run(tmp_path)
    rule = avoid(isolated_rules)
    try_rule(isolated_rules, rule.id, [run])
    approve(isolated_rules, rule.id, by="Lead")
    assert len(lint_run(run).alerts) == 3
    path = isolated_rules / "R001.yml"
    path.write_text(path.read_text(encoding="utf-8").replace("replace: connected", "replace: linked"), encoding="utf-8")
    assert lint_run(run).alerts == []  # changed since approval: out of use until tested and approved again


# --- suggest and CLI -------------------------------------------------------------------------


def test_feedback_digest(isolated_rules, tmp_path):
    run = make_run(tmp_path)
    add_feedback(run, "aaaaaaaaaaaa", "Say which alerts continue.")
    add_feedback(run, "bbbbbbbbbbbb", "Covered elsewhere.", action="close", reason="already_documented")
    propose(isolated_rules, kind="guidance", title="t", message="m", guidance="g", proposed_by="T",
            origins=[(run.name, "aaaaaaaaaaaa")])
    digest = feedback_digest([run.parent], isolated_rules)
    assert digest["close_reasons"] == {"already_documented": 1}
    assert [(f["feedback_id"], f["already_a_rule"]) for f in digest["feedback"]] == [
        ("aaaaaaaaaaaa", True), ("bbbbbbbbbbbb", False)]


def test_cli_rules(isolated_rules, tmp_path, capsys):
    run = make_run(tmp_path)
    assert main(["rules", "propose", "--kind", "guidance", "--title", "Intro scope", "--message", "m",
                 "--guidance", "Say which alerts continue.", "--origin", f"{run.name}:abcdefabcdef",
                 "--by", "Session"]) == 0
    assert "Proposed R001" in capsys.readouterr().out
    with pytest.raises(SystemExit) as exc:
        main(["rules", "propose", "--kind", "guidance", "--title", "t", "--message", "m", "--guidance", "g",
              "--origin", "bad", "--by", "S"])
    assert exc.value.code == 2
    capsys.readouterr()
    assert main(["rules", "approve", "R001", "--by", "Lead"]) == 1
    assert "has not been tested" in capsys.readouterr().err
    assert main(["rules", "test", "R001", "--runs", str(run)]) == 0
    assert "Tried R001 on 1 run(s), 3 page(s)." in capsys.readouterr().out
    assert main(["rules", "approve", "R001", "--by", "Lead"]) == 0
    assert main(["rules", "list"]) == 0
    assert "R001  live" in capsys.readouterr().out
    assert main(["rules", "suggest", "--runs", str(run.parent)]) == 0
    assert json.loads(capsys.readouterr().out)["runs"] == [run.name]
