import json
from pathlib import Path
import shutil
import stat
import sys

import pytest
from test_gate import MARKED, edit, make_run

from docforge.cli import main
from docforge.lint import Alert, LintError, LintResult, apply_fixes, changed_lines, find_vale, lint_run, plan_fixes
from docforge.run import run_checks, start_run

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "vale"
REPO = Path(__file__).resolve().parent.parent
requires_vale = pytest.mark.skipif(find_vale() is None and "DOCFORGE_VALE" not in __import__("os").environ,
                                   reason="Vale is not installed")


def custom_run(tmp_path, publish: bool = False) -> Path:
    """A custom-profile run whose one page is the Vale fixture page."""
    repo = tmp_path / "repo"
    (repo / "demo").mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO / "demo" / "mock-prd.md", repo / "demo" / "mock-prd.md")
    out = start_run(repo=repo, prds=["demo/mock-prd.md"], out=repo / "output" / "style", audience="members",
                    profile="custom", deliverables=["page.md"],
                    **({"publish_to": "example-org/docs-site"} if publish else {}))
    shutil.copy(FIXTURES / "page.md", out / "page.md")
    return out


@pytest.fixture
def fake_vale(tmp_path, monkeypatch):
    """A stand-in `vale` that replays recorded output, so these tests do not need Vale."""
    script = tmp_path / "fake-vale"
    script.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "if '--version' in sys.argv:\n    print('vale version 0.0-fake'); sys.exit(0)\n"
        f"recorded = json.load(open({str(FIXTURES / 'page.vale.json')!r}))\n"
        "files = [a for a in sys.argv[1:] if a.endswith('.md')]\n"
        "print(json.dumps({f: recorded.get(os.path.basename(f), []) for f in files}))\n",
        encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("DOCFORGE_VALE", str(script))
    return script


# --- changed lines --------------------------------------------------------------------


def test_changed_lines():
    assert changed_lines("a\nb\n", None) is None
    assert changed_lines("a\nB\nc\nd\n", "a\nb\nc\n") == {2, 4}
    assert changed_lines("same\n", "same\n") == set()


# --- parsing (recorded Vale output) -------------------------------------------------------


def test_lint_run_parses_alerts(tmp_path, fake_vale):
    out = custom_run(tmp_path)
    result = lint_run(out)
    assert result.vale_version == "0.0-fake"
    assert [(a.line, a.check.split(".")[1], a.replacement) for a in result.alerts] == [
        (7, "Subjective", None), (7, "DeviceNeutral", "select"), (7, "Wordiness", "to"),
        (9, "Inclusive", "allowlist"), (9, "DeviceNeutral", "select"), (9, "GenericLinkText", None),
        (11, "Wordiness", "before"),
    ]
    assert result.counts == {"error": 1, "warning": 4, "suggestion": 2}
    saved = json.loads((out / "qa" / "vale.json").read_text(encoding="utf-8"))
    assert len(saved["alerts"]) == 7 and saved["changed_only"] is True


def test_missing_vale_is_a_clear_error(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCFORGE_VALE", str(tmp_path / "no-such-vale"))
    with pytest.raises(LintError, match="Vale is not installed"):
        lint_run(custom_run(tmp_path))


def test_run_check_reports_missing_vale_without_failing(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCFORGE_VALE", str(tmp_path / "no-such-vale"))
    out = make_run(tmp_path)
    for rel in ["analysis/COVERAGE.md"]:
        assert (out / rel).is_file()
    record = run_checks(out, REPO)
    assert record["vale"]["available"] is False and record["vale"]["passed"] is True
    assert "Vale is not installed" in record["vale"]["note"]


# --- fixes -------------------------------------------------------------------------------


def test_fix_plan_applies_only_safe_replacements(tmp_path, fake_vale):
    out = custom_run(tmp_path)
    plan = plan_fixes(out, lint_run(out))
    assert [(f.line, f.before, f.after) for f in plan.fixes] == [
        (7, "click on", "select"), (7, "in order to", "to"), (9, "whitelist", "allowlist"), (11, "Prior to", "Before")]
    assert plan.skipped == ["page.md:9:38 DocForge.DeviceNeutral: overlaps DocForge.GenericLinkText, which needs a person"]
    assert "+Simply select **Pause alerts** to stop in-app alerts. <!-- evidence: C03 -->" in plan.diff
    assert "+Use `click` in scripts. Before pausing, sign in. <!-- evidence: C07 -->" in plan.diff
    assert (out / "page.md").read_text(encoding="utf-8") == (FIXTURES / "page.md").read_text(encoding="utf-8")


def alert(line, start, end, match, replacement="x", check="DocForge.Test"):
    return Alert(page="page.md", line=line, start=start, end=end, check=check, severity="warning",
                 message="m", match=match, replacement=replacement)


@pytest.mark.parametrize(
    "a, reason",
    [
        (alert(2, 8, 12, "Quiet"), "in front matter"),
        (alert(11, 6, 10, "click"), "inside a marker, code, link target or tag"),
        (alert(7, 81, 83, "C03"), "inside a marker, code, link target or tag"),
        (alert(9, 75, 79, "setup"), "inside a marker, code, link target or tag"),
        (alert(7, 1, 6, "Plainly"), "text no longer matches 'Plainly'"),
    ],
)
def test_fix_protections(tmp_path, a, reason):
    out = custom_run(tmp_path)
    result = LintResult(vale_version="t", config="t", changed_only=True, pages=["page.md"], alerts=[a])
    plan = plan_fixes(out, result)
    assert plan.fixes == []
    assert plan.skipped[0].endswith(reason)


def test_apply_writes_fixes(tmp_path, fake_vale):
    out = custom_run(tmp_path)
    apply_fixes(out, plan_fixes(out, lint_run(out)))
    text = (out / "page.md").read_text(encoding="utf-8")
    assert "Simply select **Pause alerts** to stop in-app alerts." in text
    assert "allowlist, then click here" in text
    assert "<!-- evidence: C03 -->" in text and "<!-- evidence: C07 -->" in text


def test_apply_restores_pages_when_gate_fails(tmp_path, fake_vale):
    out = custom_run(tmp_path, publish=True)  # meant for publishing, so the gate must keep passing
    before = (out / "page.md").read_text(encoding="utf-8")
    plan = plan_fixes(out, lint_run(out))
    with pytest.raises(LintError, match="claim gate failed after fixing.*every page was restored"):
        apply_fixes(out, plan)  # this run has no evidence ledger, so the gate cannot pass
    assert (out / "page.md").read_text(encoding="utf-8") == before


def test_apply_refuses_if_page_changed_after_planning(tmp_path, fake_vale):
    out = custom_run(tmp_path)
    plan = plan_fixes(out, lint_run(out))
    edit(out, "page.md", "click on", "tap on")
    with pytest.raises(LintError, match="changed since the fixes were planned"):
        apply_fixes(out, plan)


# --- CLI ---------------------------------------------------------------------------------


def test_cli_lint_fix_and_apply(tmp_path, fake_vale, capsys):
    out = custom_run(tmp_path)
    assert main(["lint", str(out)]) == 1  # one error-level alert (Inclusive)
    text = capsys.readouterr().out
    assert "page.md:9:22 error DocForge.Inclusive" in text and "-> 'allowlist'" in text
    assert main(["lint", str(out), "--fix"]) == 0
    text = capsys.readouterr().out
    assert "4 fix(es) proposed. Rerun with --apply" in text and "NOT FIXED: page.md:9:38" in text
    assert "allowlist" not in (out / "page.md").read_text(encoding="utf-8")
    assert main(["lint", str(out), "--apply"]) == 0
    assert "Applied 4 fix(es)" in capsys.readouterr().out
    assert "allowlist" in (out / "page.md").read_text(encoding="utf-8")


# --- real Vale ------------------------------------------------------------------------------


@requires_vale
def test_real_vale_matches_recorded_output(tmp_path, monkeypatch):
    monkeypatch.delenv("DOCFORGE_VALE", raising=False)
    out = custom_run(tmp_path)
    result = lint_run(out)
    recorded = json.loads((FIXTURES / "page.vale.json").read_text(encoding="utf-8"))["page.md"]
    assert [(a.line, a.start, a.check) for a in result.alerts] == [
        (r["Line"], r["Span"][0], r["Check"]) for r in recorded]


@requires_vale
def test_real_vale_skips_markers_code_and_clean_demo_pages(tmp_path, monkeypatch):
    monkeypatch.delenv("DOCFORGE_VALE", raising=False)
    out = make_run(tmp_path)  # the marked Quiet Hours pages
    result = lint_run(out)
    assert result.alerts == []  # markers such as <!-- evidence: C03 --> are comments, not prose


@requires_vale
def test_real_vale_changed_prose_only_after_prepare(tmp_path, monkeypatch):
    from test_publish import config, prepare
    from conftest import git

    monkeypatch.delenv("DOCFORGE_VALE", raising=False)
    docs_root = tmp_path / "docs-site"
    (docs_root / "site").mkdir(parents=True)
    git(docs_root, "init", "-q", "-b", "main")
    (docs_root / "README.md").write_text("# Docs\n", encoding="utf-8")
    git(docs_root, "add", ".")
    git(docs_root, "-c", "user.name=T", "-c", "user.email=t@example.com", "commit", "-q", "-m", "init")
    git(docs_root, "config", "user.name", "T")
    git(docs_root, "config", "user.email", "t@example.com")
    out = make_run(tmp_path)
    edit(out, "how-to/how-to.md", "Select **Confirm**.", "Click **Confirm**.")  # existing prose, before prepare
    prepare(tmp_path, docs_root, out=out, cfg=config(tmp_path))
    edit(out, "how-to/how-to.md", "Choose **1 hour**.", "Simply choose **1 hour**.")  # new prose
    changed = lint_run(out)
    assert [(a.page, a.line, a.check) for a in changed.alerts] == [("how-to/how-to.md", 14, "DocForge.Subjective")]
    assert changed.unchanged_alerts == 1
    everything = lint_run(out, changed_only=False)
    assert {a.check for a in everything.alerts} == {"DocForge.Subjective", "DocForge.DeviceNeutral"}


@requires_vale
def test_run_check_fails_on_vale_error(tmp_path, monkeypatch):
    monkeypatch.delenv("DOCFORGE_VALE", raising=False)
    out = make_run(tmp_path)
    record = run_checks(out, REPO)
    assert record["vale"]["available"] and record["vale"]["passed"]
    edit(out, "feature/feature-guide.md", "Pausing alerts requires an online connection.",
         "Pausing alerts requires an online connection (see C06).")
    record = run_checks(out, REPO)
    assert record["vale"]["passed"] is False
    assert any("DocForge.ClaimIDs" in a for a in record["vale"]["alerts"])
    assert main(["run", "check", str(out), "--repo", str(REPO)]) == 1
