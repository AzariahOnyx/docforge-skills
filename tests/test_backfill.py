import json
from pathlib import Path
import stat
import subprocess
import sys

import pytest

from docforge.backfill import BackfillError, blind, fetch_prs, load_labels, prepare, replay, score, write_labels_template
from docforge.cli import main
from docforge.config import load_config

FIXTURES = Path(__file__).resolve().parent / "fixtures"
RECORDED = FIXTURES / "backfill"
REPO = Path(__file__).resolve().parent.parent
CASES = REPO / "benchmarks" / "cases.json"
CONFIG = FIXTURES / "github" / "triggers.yaml"


@pytest.fixture
def fake_gh(tmp_path, monkeypatch):
    """A stand-in `gh` that serves recorded API responses and logs every call."""
    log = tmp_path / "gh-calls.log"
    script = tmp_path / "fake-gh"
    script.write_text(
        f"#!{sys.executable}\n"
        "import sys\n"
        f"open({str(log)!r}, 'a').write(' '.join(sys.argv[1:]) + '\\n')\n"
        "args = sys.argv[1:]\n"
        "assert args[0] == 'api', args\n"
        "path = args[1]\n"
        f"base = {str(RECORDED)!r}\n"
        "if path.endswith('/pulls/11') or path.endswith('/pulls/12') or path.endswith('/pulls/13') or path.endswith('/pulls/14'):\n"
        "    print(open(f\"{base}/{path.rsplit('/', 1)[1]}.diff\").read(), end='')\n"
        "elif '/pulls?' in path:\n"
        "    print(open(f'{base}/pulls.json').read())\n"
        "else:\n"
        "    print(open(f'{base}/repo.json').read())\n",
        encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("DOCFORGE_GH", str(script))
    return log


@pytest.fixture
def fetched(tmp_path, fake_gh):
    folder = tmp_path / "eval" / "prs"
    fetch_prs("example-org/product-web", folder)
    return folder


def write_labels(folder, values: dict):
    path = write_labels_template(folder)
    data = json.loads(path.read_text(encoding="utf-8"))
    for row in data["labels"]:
        if row["number"] in values:
            row["docs_needed"], row["labelled_by"] = values[row["number"]], "Docs lead"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# --- fetch -----------------------------------------------------------------------------


def test_fetch_saves_events_and_diffs_read_only(fetched, fake_gh):
    manifest = json.loads((fetched / "fetch.json").read_text(encoding="utf-8"))
    assert [p["number"] for p in manifest["prs"]] == [11, 12, 13, 14]
    event = json.loads((fetched / "events" / "11.json").read_text(encoding="utf-8"))
    assert (event["action"], event["pull_request"]["merged"], event["repository"]["topics"]) == (
        "closed", True, ["docs-sync", "web"])
    assert json.loads((fetched / "events" / "12.json").read_text(encoding="utf-8"))["pull_request"]["merged"] is False
    assert (fetched / "diffs" / "13.diff").read_text(encoding="utf-8").startswith("diff --git a/.github/")
    calls = fake_gh.read_text(encoding="utf-8").splitlines()
    assert all(c.startswith("api ") for c in calls)
    assert not any(flag in c for c in calls for flag in ("-X", "--method", "-f ", "-F "))  # GET only


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"repo": "product-web"}, "owner/repo"),
        ({"state": "merged"}, "open, closed or all"),
        ({"limit": 0}, "between 1 and 100"),
    ],
)
def test_fetch_validation(tmp_path, fake_gh, kwargs, message):
    args = {"repo": "example-org/product-web", "out": tmp_path / "x"}
    args.update(kwargs)
    with pytest.raises(BackfillError, match=message):
        fetch_prs(args.pop("repo"), args.pop("out"), **args)


def test_fetch_never_reuses_a_folder(fetched):
    with pytest.raises(BackfillError, match="already exists"):
        fetch_prs("example-org/product-web", fetched)


def test_fetch_needs_gh(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCFORGE_GH", str(tmp_path / "missing"))
    with pytest.raises(BackfillError, match="GitHub CLI"):
        fetch_prs("example-org/product-web", tmp_path / "x")


# --- labels and replay ----------------------------------------------------------------------


def test_labels_template_and_validation(fetched):
    path = write_labels_template(fetched)
    rows = json.loads(path.read_text(encoding="utf-8"))["labels"]
    assert [(r["number"], r["docs_needed"]) for r in rows] == [(11, None), (12, None), (13, None), (14, None)]
    with pytest.raises(BackfillError, match="may hold someone's labels"):
        write_labels_template(fetched)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["labels"][0]["docs_needed"] = "maybe"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(BackfillError, match="must be"):
        load_labels(path)
    data["labels"][0]["docs_needed"] = "yes"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(BackfillError, match="labelled_by is required"):
        load_labels(path)


def test_replay_scores_against_labels(fetched):
    # The person thinks the CI change (#13) also needed docs; #14 is left unlabelled.
    labels = write_labels(fetched, {11: "yes", 12: "no", 13: "yes"})
    report = replay(fetched, load_config(CONFIG), labels)
    rows = {r["number"]: r for r in report["rows"]}
    assert {n: r["predicted"] for n, r in rows.items()} == {11: "yes", 12: "no", 13: "no", 14: "no"}
    assert rows[13]["outcome"] == "false_negative"
    assert "only dot-files changed" in rows[13]["summary"]
    assert "our own pull request" in rows[14]["summary"]
    assert report["counts"] == {"true_positive": 1, "false_positive": 0, "false_negative": 1, "true_negative": 1}
    assert (report["precision"], report["recall"], report["unscored"]) == ("1/1", "1/2", [14])
    md = (fetched / report["files"][1]).read_text(encoding="utf-8")
    assert "| DocForge said yes | 1 | 0 |" in md and "| 14 | Docs: Quiet Hours |" in md
    assert report["independent_labels"] is True and report["labelled_by"] == ["Docs lead"]


def test_session_made_labels_are_flagged(fetched):
    path = write_labels(fetched, {11: "yes"})
    data = json.loads(path.read_text(encoding="utf-8"))
    data["labels"][0]["labelled_by"] = "Claude (DocForge session)"
    path.write_text(json.dumps(data), encoding="utf-8")
    report = replay(fetched, load_config(CONFIG), path)
    assert report["independent_labels"] is False
    assert "not as measured accuracy" in (fetched / report["files"][1]).read_text(encoding="utf-8")


def test_replay_without_labels_reports_all_unscored(fetched):
    report = replay(fetched, load_config(CONFIG))
    assert report["labelled"] == 0 and report["unscored"] == [11, 12, 13, 14]
    assert report["precision"].startswith("n/a")


# --- benchmark arms, blinding and scoring ---------------------------------------------------------


@pytest.fixture
def prepared(tmp_path):
    out = tmp_path / "eval" / "bench"
    prepare(CASES, out, REPO)
    return out


def finish_outputs(folder: Path):
    for case_dir in sorted(p for p in folder.iterdir() if (p / "case.json").is_file()):
        for arm in ("direct", "staged"):
            (case_dir / arm / "output.md").write_text(f"# {case_dir.name}\n\nDraft text.\n", encoding="utf-8")


def test_prepare_creates_two_arms_per_case(prepared):
    record = json.loads((prepared / "eval.json").read_text(encoding="utf-8"))
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    assert len(record["arms"]) == 2 * len(cases)
    case = cases[0]["id"]
    assert (prepared / case / "direct" / "WORK-ORDER.md").read_text(encoding="utf-8").startswith(f"# Direct arm: {case}")
    staged = json.loads((prepared / case / "staged" / "run.json").read_text(encoding="utf-8"))
    assert (staged["profile"], staged["deliverables"]) == ("custom", ["output.md"])
    assert (prepared / case / "staged" / "prompts" / "1-analyzer.md").is_file()
    with pytest.raises(BackfillError, match="already exists"):
        prepare(CASES, prepared, REPO)


def test_blind_needs_every_output(prepared):
    with pytest.raises(BackfillError, match="outputs missing for"):
        blind(prepared)


def test_blind_hides_the_arm(prepared):
    finish_outputs(prepared)
    result = blind(prepared)
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    assert result == {"outputs": 2 * len(cases), "assertions": 2 * sum(len(c["expected"]) for c in cases)}
    key = json.loads((prepared / "key.json").read_text(encoding="utf-8"))
    for token in key:
        names = [p.name for p in (prepared / "blind" / token).iterdir()]
        assert sorted(names) == ["REVIEW.md", "output.md"]
        review = (prepared / "blind" / token / "REVIEW.md").read_text(encoding="utf-8").lower()
        assert "direct" not in review and "staged" not in review
    template = json.loads((prepared / "judgments.template.json").read_text(encoding="utf-8"))
    assert all(set(row) == {"output", "case_id", "assertion_index", "assertion", "result", "reviewer", "evidence"}
               for row in template)
    with pytest.raises(BackfillError, match="already blinded"):
        blind(prepared)


def judge(prepared, reviewer="Docs lead"):
    key = json.loads((prepared / "key.json").read_text(encoding="utf-8"))
    rows = json.loads((prepared / "judgments.template.json").read_text(encoding="utf-8"))
    for row in rows:
        arm = key[row["output"]]["arm"]
        if arm == "staged":
            row["result"] = "uncertain" if row["assertion_index"] == 2 else "pass"
        else:
            row["result"] = "pass" if row["assertion_index"] == 0 else "fail"
        row["reviewer"], row["evidence"] = reviewer, "Quoted from the output."
    path = prepared / "judgments.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    return path, key, rows


def test_score_counts_uncertain_as_not_passed_and_matches_score_review(prepared, tmp_path):
    finish_outputs(prepared)
    blind(prepared)
    path, key, rows = judge(prepared)
    report = score(prepared, path)
    assert report["human_reviewed"] is True
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    total = sum(len(c["expected"]) for c in cases)
    with_third = sum(len(c["expected"]) >= 3 for c in cases)
    assert report["by_arm"]["staged"] == {"pass": total - with_third, "fail": 0, "uncertain": with_third,
                                          "total": total, "pass_rate": f"{total - with_third}/{total}"}
    assert report["by_arm"]["direct"]["pass"] == len(cases)
    # The existing scorer, given one arm's unblinded judgments, gives the same counts.
    for arm in ("direct", "staged"):
        arm_rows = [{"case_id": r["case_id"], "assertion_index": r["assertion_index"], "result": r["result"],
                     "reviewer": r["reviewer"], "evidence": r["evidence"]}
                    for r in rows if key[r["output"]]["arm"] == arm]
        arm_file = tmp_path / f"{arm}.json"
        arm_file.write_text(json.dumps(arm_rows), encoding="utf-8")
        out = subprocess.run([sys.executable, str(REPO / "scripts" / "score_review.py"), str(arm_file)],
                             capture_output=True, text=True, check=True).stdout
        summary = json.loads(out[: out.rindex("}") + 1])
        mine = report["by_arm"][arm]
        assert (summary["pass"], summary["fail"], summary["uncertain"], summary["total"]) == (
            mine["pass"], mine["fail"], mine["uncertain"], mine["total"])
    md = (prepared / report["files"][1]).read_text(encoding="utf-8")
    assert md.startswith("# Benchmark replay\n\nHuman-reviewed") and "## Not passed" in md


def test_generator_as_reviewer_is_not_human_reviewed(prepared):
    finish_outputs(prepared)
    blind(prepared)
    path, _, _ = judge(prepared, reviewer="claude-code-session")
    report = score(prepared, path)
    assert report["human_reviewed"] is False
    assert "NOT human-reviewed" in (prepared / report["files"][1]).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda rows: rows.pop(), "have no judgment"),
        (lambda rows: rows.append(dict(rows[0])), "duplicate judgment"),
        (lambda rows: rows[0].update(result="maybe"), "result must be"),
        (lambda rows: rows[0].update(evidence=" "), "evidence is required"),
        (lambda rows: rows[0].update(case_id="other"), "names the wrong case"),
        (lambda rows: rows[0].update(assertion_index=99), "unknown judgment"),
    ],
)
def test_score_validates_judgments(prepared, mutate, message):
    finish_outputs(prepared)
    blind(prepared)
    path, _, rows = judge(prepared)
    mutate(rows)
    path.write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(BackfillError, match=message):
        score(prepared, path)


# --- CLI ------------------------------------------------------------------------------------


def test_cli_backfill_triggers(tmp_path, fake_gh, capsys):
    folder = tmp_path / "eval" / "prs"
    assert main(["backfill", "fetch", "example-org/product-web", "--out", str(folder)]) == 0
    assert "Fetched 4 PR(s)" in capsys.readouterr().out
    assert main(["backfill", "label", str(folder)]) == 0
    # labels.json now exists; a person fills in two rows
    data = json.loads((folder / "labels.json").read_text(encoding="utf-8"))
    for row in data["labels"][:2]:
        row["docs_needed"], row["labelled_by"] = ("yes" if row["number"] == 11 else "no"), "Docs lead"
    (folder / "labels.json").write_text(json.dumps(data), encoding="utf-8")
    capsys.readouterr()
    assert main(["backfill", "replay", str(folder), "--config", str(CONFIG)]) == 0
    text = capsys.readouterr().out
    assert "TP 1, FP 0, FN 0, TN 1. Precision 1/1, recall 1/1." in text
    assert "Unscored (no label): #13, #14" in text
