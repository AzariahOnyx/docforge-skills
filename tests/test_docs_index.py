import json
from pathlib import Path

import pytest

from docforge.cli import main
from docforge.config import DocCollection
from docforge.docs_index import DocsIndexError, build_index, parse_page, slugify

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "docs-repo"
REPO = Path(__file__).resolve().parent.parent
COLLECTION = "example-org/docs"


@pytest.fixture(scope="module")
def index():
    return build_index(FIXTURE, COLLECTION, DocCollection(filter=["docs/"]))


def page(index, path):
    return next(p for p in index.pages if p.path == path)


def link(index, source, target):
    return next(l for l in index.links if l.source == source and l.target == target)


# --- pages -----------------------------------------------------------------


def test_indexes_only_filtered_visible_pages(index):
    assert sorted(p.path for p in index.pages) == [
        "docs/guides/bad-front-matter.md",
        "docs/guides/index.mdx",
        "docs/guides/setup.md",
        "docs/index.md",
    ]


def test_no_collection_indexes_whole_folder_except_hidden_dirs():
    full = build_index(FIXTURE)
    paths = {p.path for p in full.pages}
    assert full.collection is None
    assert {"README.md", "drafts/notes.md"} <= paths
    assert not any("/." in p for p in paths)


def test_title_comes_from_front_matter_then_h1_then_filename(index):
    assert page(index, "docs/index.md").title == "Welcome"
    assert page(index, "docs/guides/setup.md").title == "Set up the product"
    assert page(index, "docs/guides/bad-front-matter.md").title == "bad-front-matter"


def test_front_matter_is_parsed(index):
    assert page(index, "docs/index.md").front_matter == {"title": "Welcome", "sidebar_position": 1}


def test_invalid_front_matter_is_a_warning_not_a_failure(index):
    bad = page(index, "docs/guides/bad-front-matter.md")
    assert bad.front_matter == {}
    assert bad.warnings == ["front matter is not valid YAML; ignored"]


def test_sections_have_anchors_and_line_ranges(index):
    sections = page(index, "docs/guides/setup.md").sections
    assert [(s.heading, s.level, s.anchor, s.start_line, s.end_line) for s in sections] == [
        ("Set up the product", 1, "set-up-the-product", 1, 21),
        ("Install", 2, "install", 3, 14),
        ("Install", 3, "install-1", 11, 14),
        ("Configure", 2, "config", 15, 18),
        ("Use docforge safely", 2, "use-docforge-safely", 19, 21),
    ]


def test_section_word_counts_exclude_subsections(index):
    counts = {s.anchor: s.word_count for s in page(index, "docs/guides/setup.md").sections}
    # "Install" owns "First install." and the fenced block, not its "Install" subsection.
    assert counts == {"set-up-the-product": 0, "install": 6, "install-1": 6, "config": 6, "use-docforge-safely": 1}


def test_headings_inside_code_fences_are_ignored(index):
    headings = [s.heading for s in page(index, "docs/guides/setup.md").sections]
    assert "not a heading" not in headings


def test_slugify_matches_github_style():
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("Use `docforge` *safely*") == "use-docforge-safely"
    assert slugify("See [the API](api.md)") == "see-the-api"
    assert slugify("snake_case stays") == "snake_case-stays"


def test_unclosed_front_matter_is_treated_as_content():
    result, _ = parse_page("p.md", "---\ntitle: x\n# Heading\n")
    assert result.front_matter == {}
    assert result.title == "Heading"
    assert "front matter is not closed; treated as page content" in result.warnings


# --- links -----------------------------------------------------------------


def test_link_statuses(index):
    src = "docs/index.md"
    expected = {
        "./guides/setup.md#install": ("ok", "docs/guides/setup.md"),
        "guides/": ("ok", "docs/guides/index.mdx"),
        "guides/setup.md#config": ("ok", "docs/guides/setup.md"),
        "guides/setup.md#nope": ("broken_anchor", "docs/guides/setup.md"),
        "./missing.md": ("broken_page", None),
        "../../outside.md": ("broken_page", None),
        "https://example.com/docs": ("external", None),
        "/docs/somewhere": ("unchecked", None),
        "../README.md": ("unchecked", "README.md"),
    }
    for target, (status, resolved) in expected.items():
        found = link(index, src, target)
        assert (found.status, found.resolved_path) == (status, resolved), target


def test_link_outside_indexed_folder_to_existing_file_is_unchecked():
    sub = build_index(FIXTURE / "docs")
    found = link(sub, "index.md", "../README.md")
    assert (found.status, found.note) == ("unchecked", "outside the indexed folder")
    missing = link(sub, "index.md", "../../outside.md")
    assert (missing.status, missing.note) == ("broken_page", "no file at this path")


def test_images_code_spans_and_fences_are_not_links(index):
    targets = {l.target for l in index.links}
    assert "./diagram.png" not in targets
    assert "nowhere.md" not in targets
    assert "also-nowhere.md" not in targets


def test_same_page_anchor_links(index):
    assert link(index, "docs/guides/setup.md", "#config").status == "ok"
    assert link(index, "docs/guides/setup.md", "#set-up-the-product").status == "ok"


def test_link_line_numbers(index):
    assert link(index, "docs/index.md", "./missing.md").line == 11


def test_broken_links_list(index):
    assert sorted(l.target for l in index.broken_links) == [
        "../../outside.md",
        "./missing.md",
        "guides/setup.md#nope",
    ]


def test_backlinks(index):
    assert index.backlinks == {
        "docs/guides/index.mdx": ["docs/index.md"],
        "docs/guides/setup.md": ["docs/guides/index.mdx", "docs/index.md"],
        "docs/index.md": ["docs/guides/index.mdx"],
    }


def test_missing_directory_is_an_error(tmp_path):
    with pytest.raises(DocsIndexError, match="not a directory"):
        build_index(tmp_path / "nope")


def test_index_does_not_write_to_folder(tmp_path):
    (tmp_path / "a.md").write_text("# A\n\n[b](b.md)\n", encoding="utf-8")
    before = sorted(p.name for p in tmp_path.iterdir())
    build_index(tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == before


def test_indexes_this_repos_output_folder():
    result = build_index(REPO / "output")
    paths = {p.path for p in result.pages}
    assert "quiet-hours/how-to/how-to.md" in paths
    assert len(paths) >= 24
    assert result.broken_links == []


# --- CLI -------------------------------------------------------------------


def write_config(tmp_path: Path) -> Path:
    path = tmp_path / "docforge.yaml"
    path.write_text(f"doc_collections:\n  {COLLECTION}:\n    filter: [docs/]\n", encoding="utf-8")
    return path


def test_cli_index_with_collection(tmp_path, capsys):
    config = write_config(tmp_path)
    code = main(["index", str(FIXTURE), "--collection", COLLECTION, "--config", str(config)])
    out, err = capsys.readouterr()
    assert code == 0
    data = json.loads(out)
    assert data["collection"] == COLLECTION
    assert len(data["pages"]) == 4
    assert "3 broken" in err


def test_cli_index_without_collection_needs_no_config(capsys):
    code = main(["index", str(FIXTURE)])
    out, _ = capsys.readouterr()
    assert code == 0
    assert len(json.loads(out)["pages"]) == 6


def test_cli_index_out_file_and_no_overwrite(tmp_path, capsys):
    out_file = tmp_path / "index.json"
    assert main(["index", str(FIXTURE), "--out", str(out_file)]) == 0
    assert len(json.loads(out_file.read_text(encoding="utf-8"))["pages"]) == 6
    before = out_file.read_text(encoding="utf-8")
    assert main(["index", str(FIXTURE / "docs"), "--out", str(out_file)]) == 1
    assert "refusing to overwrite" in capsys.readouterr().err
    assert out_file.read_text(encoding="utf-8") == before


def test_cli_unknown_collection(tmp_path, capsys):
    config = write_config(tmp_path)
    code = main(["index", str(FIXTURE), "--collection", "other/repo", "--config", str(config)])
    assert code == 1
    assert "not in" in capsys.readouterr().err


def test_cli_missing_path(capsys):
    assert main(["index", str(FIXTURE / "nope")]) == 1
    assert "not a directory" in capsys.readouterr().err
