"""Confluence fetching against a local stub server with fictional data. No network."""

import json
from pathlib import Path

import pytest

from docforge.config import ConfluenceSource
from docforge.sources import SourceFetchError, provenance
from docforge.sources.adf import storage_to_markdown
from docforge.sources.confluence import fetch_page

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "atlassian"
PAGE = json.loads((FIXTURES / "confluence-page.json").read_text(encoding="utf-8"))
TOKEN = "fictional-confluence-token"
PATH = "/wiki/rest/api/content/770001?expand=body.storage,version,space"


@pytest.fixture
def confluence(stub_server, monkeypatch):
    monkeypatch.setenv("TEST_CONF_TOKEN", TOKEN)
    stub_server.json(PATH, PAGE)
    source = ConfluenceSource(source_type="confluence", base_url=stub_server.url + "/wiki",
                              auth_token_env="TEST_CONF_TOKEN", space_keys=["PULSE"])
    return source, stub_server


def test_fetch_page_converts_storage_format(confluence):
    source, server = confluence
    text, meta = fetch_page(source, "770001")
    assert meta["version"] == 7 and meta["space"] == "PULSE"
    assert meta["url"] == f"{server.url}/wiki/spaces/PULSE/pages/770001/Quiet+Hours+design+notes"
    header = provenance.read(text)
    assert header["kind"] == "confluence" and header["version"] == "7" and header["space"] == "PULSE"
    assert "# Quiet Hours design notes" in text
    assert "## Scope" in text
    assert "Quiet Hours applies to **email** and *push* alerts." in text
    assert "- Critical alerts bypass it.\n\n- Times use the workspace time zone.\n\n  - Nested detail" in text
    assert "1. First\n\n2. Second" in text
    assert "| Channel | Held |\n| --- | --- |\n| Email | Yes |" in text
    assert '```\n{"quiet_hours": true}\n```' in text
    assert "[Confluence macro not converted: jira]" in text and "PULSE-42" not in text.split("-->", 1)[1].split("# ", 1)[1].split("macro")[0]
    assert "[the design](https://example.com/design)" in text
    assert "[Image not fetched]" in text
    assert "alert(1)" not in text
    assert server.requests[-1][2]["Authorization"] == f"Bearer {TOKEN}"


def test_page_comment_cannot_forge_a_provenance_header(confluence):
    text, _ = fetch_page(confluence[0], "770001")
    body = text.split("\n-->", 1)[1]
    assert "<!--" not in body
    assert provenance.read(text)["id"] == "770001"


def test_page_outside_allowed_spaces_is_refused(confluence):
    source, server = confluence
    server.json(PATH, {**PAGE, "space": {"key": "SECRET"}})
    with pytest.raises(SourceFetchError, match="space SECRET, which is not in space_keys"):
        fetch_page(source, "770001")


def test_non_page_content_is_refused(confluence):
    source, server = confluence
    server.json(PATH, {**PAGE, "type": "attachment"})
    with pytest.raises(SourceFetchError, match="not a page"):
        fetch_page(source, "770001")


@pytest.mark.parametrize("page_id", ["abc", "0", "770001/../1", "-1"])
def test_bad_page_ids_are_refused(confluence, page_id):
    with pytest.raises(SourceFetchError, match="not a Confluence page ID"):
        fetch_page(confluence[0], page_id)
    assert confluence[1].requests == []


def test_redirect_to_another_host_is_refused(confluence):
    source, server = confluence
    server.routes[PATH] = (301, b"", {"Location": "https://elsewhere.example.com/x"})
    with pytest.raises(SourceFetchError, match="another host") as info:
        fetch_page(source, "770001")
    assert TOKEN not in str(info.value)


def test_non_json_response_is_refused(confluence):
    source, server = confluence
    server.routes[PATH] = (200, b"<html>login</html>", {"Content-Type": "text/html"})
    with pytest.raises(SourceFetchError, match="did not return JSON"):
        fetch_page(source, "770001")


def test_storage_list_item_with_two_paragraphs_keeps_one_bullet():
    md = storage_to_markdown("<ul><li><p>One</p><p>More on one</p></li><li>Two</li></ul>")
    assert md == "- One\n\n  More on one\n\n- Two"
