"""Clean-up steps from the demo pack (fictional): every kind, protected text, report, and the gate safety net."""

import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from docforge.cleanup import CleanupError, apply_cleanup, plan_cleanup
from docforge.cli import main
from docforge.packs.model import PackManifest
from docforge.run import start_run

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "tests" / "fixtures" / "packs" / "demo"
PRD = "demo/mock-prd.md"
DELIVERABLES = ["feature/overview.md", "how-to/steps.md", "release-note/notes.md"]

OVERVIEW = """---
title: Alerts — overview
---

# Alerts overview

Alerts watch a board metric — and notify the owner. Use `a — b` in code [docs](https://example.com/a—b).

> [!NOTE]
> Alerts belong to a board. <!-- evidence: C01 -->

> [!NOTE]
> - Owners get every alert.
> - Viewers get none. <!-- evidence: C02, C01 -->

> [!WARNING]
> Deleting a board deletes its alerts. <!-- evidence: C03 -->

> [!IMPORTANT]
> **Preview**
> Alerts are in preview. <!-- evidence: none (status label) -->

For help, contact [SUPPORT INQUIRY: alert thresholds]. [UPDATE EXISTING]

This sentence stays. The pulse_alert_rollout_v2 flag gates the feature. Another one stays.

| Setting | Name |
| --- | --- |
| Rollout | pulse_alert_rollout_v2 |

<span>raw</span> and <details>ok</details>

```
pulse_alert_rollout_v2 — in code
```
"""

NOTES = """# Release notes

> [!NOTE]
> First. <!-- evidence: C01 -->

> [!IMPORTANT]
> **Preview**
> Alerts are in preview. <!-- evidence: none (status label) -->
"""


@pytest.fixture
def run(tmp_path):
    out = start_run(repo=ROOT, prds=[PRD], out=tmp_path / "run", audience="admins", profile="custom",
                    deliverables=DELIVERABLES, pack=DEMO)
    for rel, text in (("feature/overview.md", OVERVIEW), ("how-to/steps.md", "# Steps\n\n1. Open a board.\n"),
                      ("release-note/notes.md", NOTES)):
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        (out / rel).write_text(text, encoding="utf-8")
    return out


def test_schema_is_strict():
    base = {"schema_version": 1, "name": "x", "version": "1.0.0"}
    bad = [
        ({"id": "a", "description": "d", "kind": "shell", "command": "rm"}, "kind"),
        ({"id": "a", "description": "d", "kind": "replace", "pattern": "(", "replacement": ""}, "invalid regular expression"),
        ({"id": "a", "description": "d", "kind": "marker_link", "pattern": r"\[S\]", "address": "s@x.example",
          "templates": {"I": {"subject": "s", "line": "l"}}, "default_type": "I"}, "named groups"),
        ({"id": "a", "description": "d", "kind": "marker_link", "pattern": r"(?P<type>x)(?P<phrase>y)",
          "address": "not-an-address", "templates": {"I": {"subject": "s", "line": "l"}}, "default_type": "I"}, "address"),
        ({"id": "a", "description": "d", "kind": "merge_alerts", "types": ["INFO"]}, "types"),
        ({"id": "a", "description": "d", "kind": "check", "pattern": "x", "message": "m", "extra": 1}, "Extra inputs"),
    ]
    for step, message in bad:
        with pytest.raises(ValueError, match=message):
            PackManifest.model_validate({**base, "cleanup_steps": [step]})


def test_preview_changes_nothing_and_lists_every_change(run):
    before = (run / "feature" / "overview.md").read_text()
    result = plan_cleanup(run)
    assert (run / "feature" / "overview.md").read_text() == before
    assert not (run / "qa" / "cleanup.json").exists()
    assert result.pack == "demo 0.1.0"
    counts = {s["id"]: (s["changes"], s["findings"]) for s in result.steps}
    assert counts["em-dashes"][0] == 1          # the prose line only
    assert counts["triage-tags"] == (1, 0)
    assert counts["feature-flags"][0] == 1      # one sentence; the cell and the code block stay
    assert counts["support-links"] == (1, 0)
    assert counts["merge-notes"] == (1, 0)      # the release note has one note only
    assert counts["preview-first"] == (1, 0)    # not in release notes
    assert counts["no-raw-html"] == (0, 1)
    assert result.diff.startswith("--- a/feature/overview.md")


def test_apply_writes_pages_and_report(run):
    result = apply_cleanup(run, plan_cleanup(run))
    text = (run / "feature" / "overview.md").read_text()
    lines = text.splitlines()
    # replace: prose only; front matter, inline code and link targets keep the em dash.
    assert "Alerts watch a board metric - and notify the owner." in text
    assert "title: Alerts — overview" in text and "`a — b`" in text and "example.com/a—b" in text
    assert "[UPDATE EXISTING]" not in text
    # drop_sentences: the sentence goes, neighbours stay, the cell and code block stay.
    assert "This sentence stays. Another one stays." in text
    assert "| Rollout | pulse_alert_rollout_v2 |" in text
    assert "pulse_alert_rollout_v2 — in code" in text
    assert any(f.message == "match is a whole table cell; left in place" for f in result.findings)
    # marker_link: a pre-filled mailto link.
    link = next(l for l in lines if "support@pulseboard.example" in l)
    url = link[link.index("(mailto:") + 1: link.index(")", link.index("(mailto:"))]
    query = parse_qs(urlsplit(url).query)
    assert query["subject"] == ["Question about alert thresholds"]
    assert query["body"] == ["Hello Pulseboard Support,\n\nI have a question about alert thresholds.\n\nThanks,\n"]
    # move_to_top: the Preview callout is the first block under the title.
    title = lines.index("# Alerts overview")
    assert lines[title + 2:title + 4] == ["> [!IMPORTANT]", "> **Preview**"]
    # merge_alerts: one note with a list, one combined marker; the warning is untouched.
    assert "> [!NOTE]\n> - Alerts belong to a board.\n> - Owners get every alert.\n> - Viewers get none. " \
           "<!-- evidence: C01, C02 -->" in text
    assert text.count("> [!NOTE]") == 1 and "> [!WARNING]" in text
    # Release notes: notes merge only with notes; the Preview callout is not moved there.
    assert (run / "release-note" / "notes.md").read_text().index("[!NOTE]") < \
        (run / "release-note" / "notes.md").read_text().index("**Preview**")
    record = json.loads((run / "qa" / "cleanup.json").read_text())
    assert record["applied"] is True and len(record["changes"]) == len(result.changes)
    report = (run / "qa" / "CLEANUP-REPORT.md").read_text()
    assert "| feature-flags | `feature/overview.md` |" in report and "removed" in report
    assert "raw HTML is not allowed outside details" in report
    assert "<!--" not in report.split("## Changes")[1].replace("&lt;!--", "")
    # Running again changes nothing.
    assert plan_cleanup(run).changes == []


def test_dropping_a_whole_statement_keeps_its_marker(tmp_path):
    from docforge.cleanup.steps import run_drop_sentences
    from docforge.packs.model import DropSentencesStep

    step = DropSentencesStep(id="f", description="d", kind="drop_sentences", pattern=r"\bsecret_flag_name\b")
    text = "# T\n\nFirst line of a paragraph\nsecret_flag_name is on. <!-- evidence: C01 -->\n\n- secret_flag_name only.\n"
    new, changes, _ = run_drop_sentences(step, "p.md", text)
    assert "First line of a paragraph <!-- evidence: C01 -->" in new
    assert "secret_flag_name" not in new and len(changes) == 2


def test_gated_run_is_restored_when_the_gate_fails(run):
    manifest = json.loads((run / "run.json").read_text())
    manifest["publish"] = {"collection": "example-org/docs"}
    (run / "run.json").write_text(json.dumps(manifest))
    before = {d: (run / d).read_text() for d in DELIVERABLES}
    with pytest.raises(CleanupError, match="claim gate failed after clean-up"):
        apply_cleanup(run, plan_cleanup(run))
    assert {d: (run / d).read_text() for d in DELIVERABLES} == before
    assert not (run / "qa" / "cleanup.json").exists()


def test_run_without_pack_has_no_steps(tmp_path):
    out = start_run(repo=ROOT, prds=[PRD], out=tmp_path / "run", audience="admins")
    assert plan_cleanup(out).steps == []


def test_cli_preview_and_apply(run, capsys):
    assert main(["cleanup", str(run)]) == 0
    out = capsys.readouterr().out
    assert "feature-flags (drop_sentences): 1 change(s)" in out and "Preview only" in out
    assert not (run / "qa" / "CLEANUP-REPORT.md").exists()
    assert main(["cleanup", str(run), "--apply"]) == 0
    assert "Report:" in capsys.readouterr().out and (run / "qa" / "CLEANUP-REPORT.md").is_file()


def test_work_orders_and_pr_body_mention_cleanup(run):
    from docforge.publish.gate import GateResult
    from docforge.publish.pr_body import render_body

    assert "docforge cleanup" in (run / "prompts" / "2-drafter.md").read_text()
    assert "qa/CLEANUP-REPORT.md" in (run / "prompts" / "3-proofreader.md").read_text()
    apply_cleanup(run, plan_cleanup(run))
    body = render_body(run, json.loads((run / "run.json").read_text()), GateResult(passed=True, pages=[]), [],
                       branch="b", draft=True, evidence_manifest="m")
    assert "## Clean-up" in body and "feature-flags removed" in body


def test_backend_applies_cleanup_after_the_drafter(run):
    from docforge.backend.runner import _cleanup

    assert _cleanup(run) == []
    assert (run / "qa" / "cleanup.json").is_file()


def test_check_ignores_link_targets_and_link_text():
    from docforge.cleanup.steps import run_check
    from docforge.packs.model import CheckStep

    step = CheckStep(id="c", description="d", kind="check", pattern=r"help@example\.com", message="hand-written",
                     unless_linked=True)
    text = "# T\n\n[help@example.com](mailto:help@example.com?subject=x)\n\nWrite to help@example.com today.\n"
    _, _, findings = run_check(step, "p.md", text)
    assert [f.line for f in findings] == [5]
