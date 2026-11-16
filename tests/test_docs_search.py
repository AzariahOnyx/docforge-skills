import json
from pathlib import Path

from docforge.cli import main
from docforge.config import DocCollection
from docforge.docs_index import search

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "docs-repo"
OUTPUT = Path(__file__).resolve().parent.parent / "output"


def paths(hits):
    return [h.path for h in hits]


# --- sample docs repo ------------------------------------------------------


def test_keyword_finds_best_section():
    hits = search(FIXTURE, "install")
    # Link URLs are not text, so docs/index.md's link to setup.md#install does not match.
    assert paths(hits) == ["docs/guides/setup.md"]
    hit = hits[0]
    # "Install" heading (2) + "First install." in its text (1).
    assert (hit.anchor, hit.score, hit.line, hit.snippet) == ("install", 3, 5, "First install.")


def test_heading_search_points_at_heading_line():
    hits = search(FIXTURE, "install", field="heading")
    assert [(h.path, h.anchor, h.line, h.snippet) for h in hits] == [
        ("docs/guides/setup.md", "install", 3, "Install")
    ]


def test_title_search():
    assert paths(search(FIXTURE, "guides", field="title")) == ["docs/guides/index.mdx"]


def test_title_ranks_above_body_mention():
    assert paths(search(FIXTURE, "guides")) == ["docs/guides/index.mdx", "docs/index.md"]


def test_phrase_bonus():
    hits = search(FIXTURE, "set up")
    # Title: 3 per word + phrase 2 = 8. H1 heading: 2 per word + phrase 2 = 6.
    assert [(h.path, h.score) for h in hits] == [("docs/guides/setup.md", 14)]


def test_all_words_must_match():
    assert paths(search(FIXTURE, "install configure")) == ["docs/guides/setup.md"]
    assert search(FIXTURE, "install draft") == []


def test_case_insensitive_whole_words():
    assert paths(search(FIXTURE, "WELCOME")) == ["docs/index.md"]
    assert search(FIXTURE, "welc") == []


def test_empty_query_and_limit():
    assert search(FIXTURE, "  ?! ") == []
    assert len(search(FIXTURE, "the", limit=2)) == 2
    assert len(search(FIXTURE, "the", limit=0)) > 2


def test_collection_filter_limits_search():
    assert paths(search(FIXTURE, "draft notes")) == ["drafts/notes.md"]
    assert search(FIXTURE, "draft notes", collection=DocCollection(filter=["docs/"])) == []


# --- this repo's output/ ---------------------------------------------------


def test_output_keyword_search_finds_quiet_hours_guides():
    hits = search(OUTPUT, "quiet hours", limit=3)
    assert len(hits) == 3
    assert all(h.path.endswith("feature/feature-guide.md") for h in hits)


def test_output_heading_search_finds_how_to_steps():
    hits = search(OUTPUT, "steps", field="heading", limit=0)
    assert {"quiet-hours/how-to/how-to.md", "quiet-hours-v2/how-to/how-to.md"} <= set(paths(hits))
    assert all(h.anchor == "steps" for h in hits if h.path.endswith("how-to.md"))


# --- CLI -------------------------------------------------------------------


def test_cli_search_text(capsys):
    assert main(["search", str(FIXTURE), "install"]) == 0
    out = capsys.readouterr().out
    assert "docs/guides/setup.md#install:5" in out
    assert "First install." in out


def test_cli_search_json(capsys):
    assert main(["search", str(FIXTURE), "guides", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert [d["path"] for d in data] == ["docs/guides/index.mdx", "docs/index.md"]


def test_cli_search_no_matches(capsys):
    assert main(["search", str(FIXTURE), "zebra"]) == 0
    assert capsys.readouterr().out.strip() == "No matches."


def test_cli_search_missing_path(capsys):
    assert main(["search", str(FIXTURE / "nope"), "x"]) == 1
    assert "not a directory" in capsys.readouterr().err


def test_any_mode_ranks_by_matched_words():
    hits = search(FIXTURE, "install draft", match="any")
    # "draft": notes.md title (3) + H1 heading (2). "install": setup.md heading (2) + text (1).
    assert [(h.path, h.score) for h in hits] == [("drafts/notes.md", 5), ("docs/guides/setup.md", 3)]
    assert search(FIXTURE, "install draft") == []


def test_any_mode_ignores_common_words():
    assert paths(search(FIXTURE, "the install", match="any")) == ["docs/guides/setup.md"]
    assert search(FIXTURE, "the of and", match="any") == []


def test_any_mode_title_and_heading():
    assert paths(search(FIXTURE, "guides zebra", field="title", match="any")) == ["docs/guides/index.mdx"]
    hits = search(FIXTURE, "configure zebra", field="heading", match="any")
    assert [(h.path, h.anchor) for h in hits] == [("docs/guides/setup.md", "config")]


def test_cli_search_match_any(capsys):
    assert main(["search", str(FIXTURE), "install draft", "--match", "any", "--json"]) == 0
    assert [d["path"] for d in json.loads(capsys.readouterr().out)] == ["drafts/notes.md", "docs/guides/setup.md"]
