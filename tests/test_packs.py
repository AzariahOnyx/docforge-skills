"""House packs: schema, loader safety, hashing, run integration. Fictional demo pack only."""

import json
from pathlib import Path
import shutil

import pytest
import yaml

from docforge.cli import main
from docforge.config import DocForgeConfig
from docforge.packs import PackError, load_pack, resolve_pack, run_manifest
from docforge.packs.model import applies
from docforge.run import RunError, start_run

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "tests" / "fixtures" / "packs" / "demo"
PRD = "demo/mock-prd.md"


@pytest.fixture
def pack(tmp_path):
    """A writable copy of the demo pack."""
    folder = tmp_path / "pack"
    shutil.copytree(DEMO, folder)
    return folder


def _edit(folder: Path, change) -> None:
    data = yaml.safe_load((folder / "pack.yaml").read_text())
    change(data)
    (folder / "pack.yaml").write_text(yaml.safe_dump(data))


def _start(tmp_path, pack_folder, name="run", **kw):
    return start_run(repo=ROOT, prds=[PRD], out=tmp_path / name, audience="workspace admins", pack=pack_folder, **kw)


# --- loading -------------------------------------------------------------------


def test_demo_pack_loads_with_roles_and_hash():
    loaded = load_pack(DEMO)
    assert loaded.manifest.name == "demo" and loaded.manifest.version == "0.1.0"
    roles = {f.path: f.role for f in loaded.files}
    assert roles["pack.yaml"] == "manifest" and roles["conventions.md"] == "conventions"
    assert roles["specs/how-to.md"] == "article_spec" and roles["styles/DemoPack/Terms.yml"] == "vale_style"
    assert roles["capture/profiles.yml"] == "capture_profile" and roles["cleanup/README.md"] == "cleanup_step"
    assert len(loaded.sha256) == 64
    assert load_pack(DEMO).sha256 == loaded.sha256


def test_any_file_change_changes_the_hash(pack):
    before = load_pack(pack).sha256
    (pack / "styles" / "DemoPack" / "Terms.yml").write_text("extends: existence\n")
    assert load_pack(pack).sha256 != before


@pytest.mark.parametrize("change,message", [
    (lambda d: d.update(extra=1), "Extra inputs"),
    (lambda d: d.update(schema_version=2), "schema_version"),
    (lambda d: d.update(name="Demo Pack"), "lowercase slug"),
    (lambda d: d.update(version="1"), "version must look like"),
    (lambda d: d.update(conventions="../outside.md"), "relative path inside the pack"),
    (lambda d: d.update(conventions="/etc/hosts"), "relative path inside the pack"),
    (lambda d: d["references"].append({"path": "references/voice.md", "title": "Again"}), "duplicate references path"),
    (lambda d: d["references"][0].update(stages=["publisher"]), "stages"),
    (lambda d: d["references"][0].update(applies_to=["/abs"]), "applies_to"),
    (lambda d: d["article_specs"].append({"type": "faq", "path": "specs/faq.md"}), "duplicate article_specs type"),
    (lambda d: d["vale"].update(based_on=["Bad Name"]), "Vale style name"),
    (lambda d: d["vale"].update(based_on=["DocForge"]), "reserved by DocForge"),
    (lambda d: d["references"][0].update(products=["nope"]), "unknown product"),
    (lambda d: d["products"].append({"key": "alerts", "title": "Again"}), "duplicate products key"),
    (lambda d: d["cleanup_steps"][0].pop("description"), "description"),
])
def test_manifest_is_strict(pack, change, message):
    _edit(pack, change)
    with pytest.raises(PackError, match=message):
        load_pack(pack)


def test_missing_files_and_styles_are_errors(pack):
    (pack / "specs" / "faq.md").unlink()
    with pytest.raises(PackError, match="specs/faq.md: file not found"):
        load_pack(pack)
    shutil.copy(DEMO / "specs" / "faq.md", pack / "specs" / "faq.md")
    _edit(pack, lambda d: d["vale"].update(based_on=["Missing"]))
    with pytest.raises(PackError, match="styles/Missing not found"):
        load_pack(pack)


def test_symlink_out_of_the_pack_is_refused(pack, tmp_path):
    secret = tmp_path / "secret.md"
    secret.write_text("not pack material")
    (pack / "references" / "voice.md").unlink()
    (pack / "references" / "voice.md").symlink_to(secret)
    with pytest.raises(PackError, match="references/voice.md: resolves outside the pack"):
        load_pack(pack)


def test_symlink_in_styles_folder_out_of_the_pack_is_refused(pack, tmp_path):
    (tmp_path / "Leak.yml").write_text("extends: existence\n")
    (pack / "styles" / "DemoPack" / "Leak.yml").symlink_to(tmp_path / "Leak.yml")
    with pytest.raises(PackError, match="Leak.yml: resolves outside the pack"):
        load_pack(pack)


def test_oversized_file_is_refused(pack, monkeypatch):
    monkeypatch.setattr("docforge.packs.load.MAX_FILE_BYTES", 50)
    with pytest.raises(PackError, match="larger than 50 bytes"):
        load_pack(pack)


def test_no_manifest_and_bad_yaml(tmp_path, pack):
    with pytest.raises(PackError, match="no pack.yaml"):
        load_pack(tmp_path / "empty")
    (pack / "pack.yaml").write_text("name: [unclosed\n")
    with pytest.raises(PackError, match="not valid YAML"):
        load_pack(pack)


def test_applies_matches_folders_and_exact_paths():
    assert applies([], "how-to/how-to.md")
    assert applies(["how-to/"], "how-to/how-to.md")
    assert not applies(["how-to/"], "feature/how-to/x.md")
    assert applies(["release-note/release-note.md"], "release-note/release-note.md")
    assert not applies(["release-note/release"], "release-note/release-note.md")


# --- config ----------------------------------------------------------------------


def test_packs_config_resolves_relative_to_the_config_file(tmp_path):
    config = DocForgeConfig.model_validate({"packs": {"house": {"path": "../packs/house"}}})
    assert resolve_pack(config, tmp_path / "cfg" / "docforge.yaml", "house") == tmp_path / "cfg" / ".." / "packs" / "house"
    with pytest.raises(PackError, match="pack 'other' is not in"):
        resolve_pack(config, tmp_path / "docforge.yaml", "other")


@pytest.mark.parametrize("packs,message", [
    ({"House": {"path": "x"}}, "lowercase slug"),
    ({"house": {}}, "path"),
    ({"house": {"path": "x", "token": "y"}}, "Extra inputs"),
])
def test_packs_config_is_strict(packs, message):
    with pytest.raises(ValueError, match=message):
        DocForgeConfig.model_validate({"packs": packs})


# --- runs and work orders ------------------------------------------------------


def test_run_records_pack_and_copies_only_drafting_files(tmp_path):
    out = _start(tmp_path, DEMO)
    record = json.loads((out / "run.json").read_text())["pack"]
    assert record["name"] == "demo" and record["sha256"] == load_pack(DEMO).sha256
    assert record["copied_to"] == "pack"
    assert str(tmp_path) not in json.dumps(record) and str(ROOT) not in json.dumps(record)
    copied = sorted(p.relative_to(out / "pack").as_posix() for p in (out / "pack").rglob("*") if p.is_file())
    assert copied == ["conventions.md", "pack.yaml", "references/how-to-extras.md", "references/product-terms.md",
                      "references/products/alerts.md", "references/products/boards.md",
                      "references/voice.md", "specs/faq.md", "specs/feature-guide.md", "specs/how-to.md",
                      "styles/DemoPack/Terms.yml"]
    for f in record["files"]:
        if (out / "pack" / f["path"]).is_file():
            import hashlib
            assert hashlib.sha256((out / "pack" / f["path"]).read_bytes()).hexdigest() == f["sha256"]


def test_work_orders_get_the_right_pack_files(tmp_path):
    out = _start(tmp_path, DEMO)
    analyzer = (out / "prompts" / "1-analyzer.md").read_text()
    drafter = (out / "prompts" / "2-drafter.md").read_text()
    proofreader = (out / "prompts" / "3-proofreader.md").read_text()
    for order in (analyzer, drafter, proofreader):
        assert "## House pack: demo 0.1.0" in order
        assert "never overrides the run's sources" in order and "never evidence for product behavior" in order
        assert "pack/conventions.md" in order and "pack/references/product-terms.md" in order
    # Voice is for the drafter and proofreader only; the analyzer sees every spec to choose from.
    assert "references/voice.md" not in analyzer and "references/voice.md" in drafter
    assert "`faq`" in analyzer and "(for how-to/)" in analyzer
    assert "`how-to/how-to.md` follows the `procedural` spec" in drafter
    assert "`feature/feature-guide.md` follows the `overview` spec" in drafter
    assert "release-note" not in drafter.split("## House pack")[1].split("## Write")[0]
    assert "sources win" in drafter and "Report every deviation" in proofreader


def test_reference_scoped_to_a_folder_skips_other_deliverables(tmp_path):
    out = start_run(repo=ROOT, prds=[PRD], out=tmp_path / "run", audience="admins", profile="custom",
                    deliverables=["feature/overview.md"], pack=DEMO)
    drafter = (out / "prompts" / "2-drafter.md").read_text()
    assert "how-to-extras.md" not in drafter and "voice.md" in drafter
    assert "follows the `overview` spec" in drafter


def test_run_without_pack_is_unchanged(tmp_path):
    out = _start(tmp_path, None)
    assert "pack" not in json.loads((out / "run.json").read_text())
    assert not (out / "pack").exists()
    assert "House pack" not in (out / "prompts" / "2-drafter.md").read_text()


def test_broken_pack_stops_run_start_before_creating_the_folder(tmp_path, pack):
    (pack / "conventions.md").unlink()
    with pytest.raises(RunError, match="pack: conventions.md: file not found"):
        _start(tmp_path, pack)
    assert not (tmp_path / "run").exists()


def test_run_manifest_detects_a_changed_copy(tmp_path):
    out = _start(tmp_path, DEMO)
    record = json.loads((out / "run.json").read_text())["pack"]
    assert run_manifest(out, record).name == "demo"
    with (out / "pack" / "pack.yaml").open("a") as handle:
        handle.write("\n# edited\n")
    with pytest.raises(PackError, match="does not match"):
        run_manifest(out, record)


def test_revision_order_includes_the_pack(tmp_path):
    from docforge.publish import PrPlan
    from docforge.review.revise import write_revision_order

    out = _start(tmp_path, DEMO)
    plan = PrPlan(repo="example-org/docs", base="main", branch="docforge/x", commit="a" * 40, title="t", draft=True,
                  policy={}, action="awaiting_approval", files=[], gate_passed=True, commands=[],
                  placements=[{"src": "how-to/how-to.md", "dest": "docs/how-to.md"}])
    order = write_revision_order(out, plan, []).read_text()
    assert "## House pack: demo 0.1.0" in order
    assert "follows the `procedural` spec" in order and "how-to-extras.md" in order
    assert order.index("## House pack") < order.index("## Pages")
    (out / "pack" / "pack.yaml").write_text("tampered: true\n")
    order = write_revision_order(out, plan, []).read_text()
    assert "pack copy cannot be used" in order


def test_pr_body_names_the_pack(tmp_path):
    from docforge.publish.gate import GateResult
    from docforge.publish.pr_body import render_body

    out = _start(tmp_path, DEMO)
    manifest = json.loads((out / "run.json").read_text())
    gate = GateResult(passed=True, pages=[], statements=0, cited=0, exemptions=[], errors=[])
    body = render_body(out, manifest, gate, [], branch="docforge/x", draft=True, evidence_manifest="m.json")
    assert f"House pack: `demo` 0.1.0 (sha256 `{manifest['pack']['sha256'][:12]}...`)" in body
    assert "not a source" in body


# --- CLI -----------------------------------------------------------------------


def test_cli_pack_check(capsys, tmp_path):
    assert main(["pack", "check", str(DEMO)]) == 0
    out = capsys.readouterr().out
    assert "Pack demo 0.1.0 is valid" in out and "3 article_spec" in out and "5 reference" in out
    config = tmp_path / "docforge.yaml"
    config.write_text(yaml.safe_dump({"packs": {"demo": {"path": str(DEMO)}}}))
    assert main(["pack", "check", "demo", "--config", str(config)]) == 0
    assert main(["pack", "check", str(tmp_path / "nowhere")]) == 1
    assert "no pack.yaml" in capsys.readouterr().err


def test_cli_run_start_with_pack(tmp_path, capsys):
    config = tmp_path / "docforge.yaml"
    config.write_text(yaml.safe_dump({"packs": {"demo": {"path": str(DEMO)}}}))
    out = tmp_path / "run"
    assert main(["run", "start", "--repo", str(ROOT), "--prd", PRD, "--out", str(out), "--audience", "admins",
                 "--pack", "demo", "--config", str(config)]) == 0
    assert "with pack demo" in capsys.readouterr().out
    assert json.loads((out / "run.json").read_text())["pack"]["name"] == "demo"
    assert main(["run", "start", "--repo", str(ROOT), "--prd", PRD, "--out", str(tmp_path / "r2"),
                 "--audience", "admins", "--pack", "missing", "--config", str(config)]) == 1
    assert "pack 'missing' is not in" in capsys.readouterr().err


# --- products ------------------------------------------------------------------


def test_product_selects_its_references(tmp_path):
    out = _start(tmp_path, DEMO, product="alerts")
    assert json.loads((out / "run.json").read_text())["pack"]["product"] == "alerts"
    for name in ("1-analyzer", "2-drafter", "3-proofreader"):
        order = (out / "prompts" / f"{name}.md").read_text()
        assert "- Product: Pulseboard Alerts (`alerts`)" in order
        assert "references/products/alerts.md" in order and "references/products/boards.md" not in order


def test_without_product_product_references_are_left_out(tmp_path):
    out = _start(tmp_path, DEMO)
    order = (out / "prompts" / "2-drafter.md").read_text()
    assert "Product: not chosen" in order and "`alerts`, `boards`" in order
    assert "references/products/" not in order
    assert "product" not in json.loads((out / "run.json").read_text())["pack"]


def test_unknown_product_or_product_without_pack_is_refused(tmp_path):
    with pytest.raises(RunError, match="product 'billing' is not in pack demo"):
        _start(tmp_path, DEMO, product="billing")
    with pytest.raises(RunError, match="--product needs --pack"):
        _start(tmp_path, None, name="r2", product="alerts")
    assert not (tmp_path / "run").exists()


# --- pack Vale styles ----------------------------------------------------------


def test_pack_vale_styles_are_listed_after_hash_check(tmp_path):
    from docforge.packs.load import run_vale_styles

    out = _start(tmp_path, DEMO)
    record = json.loads((out / "run.json").read_text())["pack"]
    styles = run_vale_styles(out, record)
    assert styles == [("DemoPack", out / "pack" / "styles" / "DemoPack")]
    (out / "pack" / "styles" / "DemoPack" / "Terms.yml").write_text("extends: existence\n")
    with pytest.raises(PackError, match="does not match"):
        run_vale_styles(out, record)


vale = pytest.mark.skipif(__import__("docforge.lint.vale", fromlist=["find_vale"]).find_vale() is None,
                          reason="Vale is not installed")


@vale
def test_lint_applies_pack_styles(tmp_path):
    from docforge.lint import lint_run

    out = start_run(repo=ROOT, prds=[PRD], out=tmp_path / "run", audience="admins", profile="custom",
                    deliverables=["feature/overview.md"], pack=DEMO)
    (out / "feature").mkdir()
    (out / "feature" / "overview.md").write_text("# Overview\n\nOpen the dashboard to see alerts.\n")
    result = lint_run(out)
    assert "pack demo styles (DemoPack)" in result.config
    assert any(a.check == "DemoPack.Terms" for a in result.alerts)


@vale
def test_lint_refuses_a_tampered_pack_style(tmp_path):
    from docforge.lint import LintError, lint_run

    out = start_run(repo=ROOT, prds=[PRD], out=tmp_path / "run", audience="admins", profile="custom",
                    deliverables=["feature/overview.md"], pack=DEMO)
    (out / "feature").mkdir()
    (out / "feature" / "overview.md").write_text("# Overview\n")
    (out / "pack" / "styles" / "DemoPack" / "Terms.yml").write_text("extends: existence\n")
    with pytest.raises(LintError, match="pack styles could not be used"):
        lint_run(out)
