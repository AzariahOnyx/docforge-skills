from http.server import ThreadingHTTPServer
import threading
import urllib.error
from urllib.parse import urlencode
import urllib.request

import pytest
from test_gate import make_run
from test_publish import docs, prepare  # noqa: F401  (docs is a fixture)

from docforge.publish import load_plan
from docforge.review import load_feedback
from docforge.review.web import CSP, ReviewApp, make_handler


@pytest.fixture
def server(tmp_path, docs):  # noqa: F811
    out = make_run(tmp_path)
    prepare(tmp_path, docs, out=out)
    app = ReviewApp(root=out.parent, reviewer="Docs reviewer")
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(app))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}", app, out
    httpd.shutdown()
    httpd.server_close()


def get(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.status, response.headers, response.read().decode("utf-8")


def post(url, data):
    request = urllib.request.Request(url, data=urlencode(data).encode(), method="POST")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def test_index_lists_suggestions(server):
    base, _, _ = server
    status, headers, html = get(base + "/")
    assert status == 200
    assert headers["Content-Security-Policy"] == CSP
    assert "<script" not in html
    assert 'href="/s/qh-docs"' in html and "docs: Quiet Hours (DocForge draft)" in html
    assert '<span class="pill">open</span>' in html


def test_three_tabs(server):
    base, _, _ = server
    _, _, diff = get(base + "/s/qh-docs?tab=diff")
    assert '<span class="file">+++ b/site/quiet-hours/index.md</span>' in diff
    assert '<span class="add">+# Pause in-app alerts with Quiet Hours</span>' in diff
    assert "&lt;!-- evidence: C01, C02 --&gt;" in diff  # markers are shown, escaped
    _, _, analysis = get(base + "/s/qh-docs?tab=analysis")
    for expected in ["Claim gate", "PASS</span>: 17 statements", "navigation link", "<td>C08</td><td>BLOCKED</td>",
                     "Publication: conditional.", "<b>Q01</b> Until tomorrow boundary"]:
        assert expected in analysis, expected
    _, _, history = get(base + "/s/qh-docs?tab=history")
    assert "<td>prepared</td>" in history
    assert 'value="Docs reviewer"' in history


def test_request_changes_through_the_form(server):
    base, app, out = server
    status, html = post(base + "/s/qh-docs/request-changes", {
        "token": app.token, "reviewer": "Docs reviewer", "page": "site/quiet-hours/index.md", "line": "3",
        "comment": "Clarify <b>email</b> alerts"})
    assert status == 200
    assert "Revision work order: <code>prompts/revise-1.md</code>" in html
    assert "gh pr comment docforge/qh-docs" in html
    # The confirmation is shown once, after a redirect, so refreshing does not resubmit.
    _, _, again = get(base + "/s/qh-docs?tab=history")
    assert "Recorded change request" not in again
    assert "Clarify &lt;b&gt;email&lt;/b&gt; alerts" in html and "<b>email</b>" not in html
    [feedback] = load_feedback(out)
    assert (feedback.page, feedback.line, feedback.comment) == ("site/quiet-hours/index.md", 3, "Clarify <b>email</b> alerts")
    assert load_plan(out).status == "changes_requested"


def test_close_through_the_form(server):
    base, app, out = server
    status, html = post(base + "/s/qh-docs/close", {
        "token": app.token, "reviewer": "Docs reviewer", "reason": "wrong_place", "note": "Belongs in the admin guide."})
    assert status == 200
    assert "Closed with reason <code>wrong_place</code>" in html
    assert "This suggestion is closed." in html and 'action="/s/qh-docs/close"' not in html
    assert load_plan(out).status == "closed"
    status, _ = post(base + "/s/qh-docs/close", {"token": app.token, "reviewer": "r", "reason": "quality"})
    assert status == 400


def test_actions_need_the_token(server):
    base, _, out = server
    for data in ({"reviewer": "r", "comment": "x"}, {"token": "wrong", "reviewer": "r", "comment": "x"}):
        status, html = post(base + "/s/qh-docs/request-changes", data)
        assert status == 403 and "form token" in html
    assert load_feedback(out) == []


def test_validation_errors_are_shown(server):
    base, app, out = server
    status, html = post(base + "/s/qh-docs/close", {"token": app.token, "reviewer": "r", "reason": "meh"})
    assert status == 400 and "reason must be one of" in html
    status, html = post(base + "/s/qh-docs/request-changes", {"token": app.token, "reviewer": "r", "comment": " "})
    assert status == 400 and "comment is required" in html
    assert load_feedback(out) == []


@pytest.mark.parametrize("path", ["/s/missing", "/s/..%2f..%2fetc", "/nope", "/s/qh-docs/extra"])
def test_unknown_paths(server, path):
    base, _, _ = server
    with pytest.raises(urllib.error.HTTPError) as exc:
        get(base + path)
    assert exc.value.code == 404


def test_oversized_form(server):
    base, app, _ = server
    status, _ = post(base + "/s/qh-docs/request-changes", {"token": app.token, "reviewer": "r", "comment": "x" * 70000})
    assert status == 413
