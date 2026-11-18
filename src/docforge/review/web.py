"""A small local web UI for reviewing DocForge suggestions.

Standard library only. Listens on 127.0.0.1 by default, escapes everything it
shows, sends a strict Content-Security-Policy, and requires a per-server token
on every action. Actions only write local files (see store.py); the matching
`gh` command is shown for a person to run.

Pages:
    /                         suggestions and their status
    /s/<run>?tab=diff         page changes on the suggestion branch
    /s/<run>?tab=analysis     claim gate, coverage, PRD vs code, QA, questions
    /s/<run>?tab=history      prepare/update/ready events and every feedback record
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hmac
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import secrets
import sys
from urllib.parse import parse_qs, quote, urlsplit

from docforge.publish.gate import COVERAGE_ROW
from docforge.publish.pr_body import QUESTION_HEADING, _readiness, source_origin

from .store import CLOSE_REASONS, ReviewError, close_suggestion, load_feedback, request_changes, suggestions

MAX_FORM_BYTES = 64 * 1024
TABS = ("diff", "analysis", "history")
CSP = "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"

STYLE = """
:root { --bg:#fff; --fg:#1f2328; --muted:#59636e; --line:#d1d9e0; --soft:#f6f8fa; --accent:#0969da;
        --add:#dafbe1; --del:#ffebe9; --hunk:#ddf4ff; --ok:#1a7f37; --bad:#cf222e; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#0d1117; --fg:#e6edf3; --muted:#9198a1; --line:#3d444d; --soft:#151b23; --accent:#4493f8;
          --add:#12261e; --del:#25171c; --hunk:#121d2f; --ok:#3fb950; --bad:#f85149; } }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:15px/1.5 system-ui, -apple-system, sans-serif; }
main { max-width: 1040px; margin: 0 auto; padding: 24px 16px 48px; }
a { color: var(--accent); }
h1 { font-size: 22px; margin: 0 0 4px; } h2 { font-size: 17px; margin: 28px 0 8px; }
.muted { color: var(--muted); }
table { border-collapse: collapse; width: 100%; margin: 8px 0; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }
.tabs { display:flex; gap:4px; border-bottom:1px solid var(--line); margin: 16px 0; flex-wrap: wrap; }
.tabs a { padding: 8px 12px; text-decoration:none; color: var(--muted); border-bottom: 2px solid transparent; }
.tabs a.on { color: var(--fg); border-color: var(--accent); }
.pill { display:inline-block; padding: 1px 8px; border-radius: 999px; border:1px solid var(--line); font-size: 13px; }
.ok { color: var(--ok); } .bad { color: var(--bad); }
pre.diff { background: var(--soft); border:1px solid var(--line); padding: 8px 0; overflow-x:auto; font-size: 13px; }
pre.diff span { display:block; padding: 0 12px; white-space: pre-wrap; overflow-wrap: anywhere; }
.add { background: var(--add); } .del { background: var(--del); } .hunk { background: var(--hunk); color: var(--muted); }
.file { font-weight: 600; }
form { border:1px solid var(--line); border-radius: 8px; padding: 12px; margin: 12px 0; background: var(--soft); }
label { display:block; margin: 8px 0 4px; font-weight: 600; }
input, select, textarea { width: 100%; font: inherit; padding: 6px 8px; border:1px solid var(--line); border-radius: 6px;
                          background: var(--bg); color: var(--fg); }
textarea { min-height: 90px; }
button { margin-top: 10px; font: inherit; padding: 6px 14px; border-radius: 6px; border:1px solid var(--line);
         background: var(--accent); color: #fff; cursor: pointer; }
code.cmd { display:block; white-space: pre-wrap; word-break: break-all; background: var(--soft); padding: 8px;
           border:1px solid var(--line); border-radius: 6px; }
.grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; }
"""


@dataclass
class ReviewApp:
    root: Path
    reviewer: str = ""
    token: str = field(default_factory=lambda: secrets.token_urlsafe(24))
    # One-time confirmations shown after an action redirects back (post/redirect/get).
    flash: dict = field(default_factory=dict)

    # --- data -------------------------------------------------------------------------

    def runs(self) -> dict:
        return {run.name: (run, plan) for run, plan in suggestions(self.root)}

    # --- rendering --------------------------------------------------------------------

    def page(self, title: str, body: str) -> str:
        return (f"<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
                f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
                f"<title>{escape(title)} · DocForge review</title><style>{STYLE}</style></head>"
                f"<body><main>{body}</main></body></html>")

    def index(self) -> str:
        rows = []
        for name, (_, plan) in sorted(self.runs().items()):
            rows.append(
                f"<tr><td><a href=\"/s/{quote(name)}\">{escape(name)}</a></td><td>{escape(plan.title)}</td>"
                f"<td><span class=\"pill\">{escape(plan.status)}</span></td>"
                f"<td>{'draft' if plan.draft else 'ready'}</td><td>{plan.revision}</td>"
                f"<td>{escape(plan.repo)}<br><span class=\"muted\">{escape(plan.branch)}</span></td></tr>")
        table = ("<table><tr><th>Run</th><th>Title</th><th>Status</th><th>PR</th><th>Revision</th>"
                 "<th>Docs repo and branch</th></tr>" + "".join(rows) + "</table>") if rows else \
            "<p>No prepared suggestions here. Run <code>docforge publish prepare</code> first.</p>"
        return self.page("Suggestions", f"<h1>Suggestions</h1><p class=\"muted\">{escape(str(self.root))}</p>{table}")

    def suggestion(self, name: str, tab: str, notice: str = "") -> str | None:
        found = self.runs().get(name)
        if found is None:
            return None
        run, plan = found
        tab = tab if tab in TABS else "diff"
        tabs = "".join(f"<a class=\"{'on' if t == tab else ''}\" href=\"/s/{quote(name)}?tab={t}\">{t.title()}</a>"
                       for t in TABS)
        header = (f"<p><a href=\"/\">All suggestions</a></p><h1>{escape(plan.title)}</h1>"
                  f"<p class=\"muted\">{escape(plan.repo)} · <code>{escape(plan.branch)}</code> at "
                  f"<code>{escape(plan.commit[:12])}</code> · revision {plan.revision} · "
                  f"{'draft' if plan.draft else 'ready for review'} · <span class=\"pill\">{escape(plan.status)}</span></p>")
        content = {"diff": self._diff, "analysis": self._analysis, "history": self._history}[tab](run, plan)
        return self.page(plan.title, header + notice + f"<nav class=\"tabs\">{tabs}</nav>" + content + self._forms(run, plan))

    def _diff(self, run: Path, plan) -> str:
        path = run / "publish" / "changes.diff"
        if not path.is_file():
            return "<p>No saved diff. Prepare the suggestion with this DocForge version to record one.</p>"
        # One chunk per file; pages first, the evidence manifest for CI last.
        chunks: list[list[str]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("diff --git") or not chunks:
                chunks.append([])
            chunks[-1].append(line)
        chunks.sort(key=lambda c: "/_docforge/" in c[0])
        spans = []
        for line in (line for chunk in chunks for line in chunk):
            cls = ("file" if line.startswith(("diff --git", "+++", "---")) else "hunk" if line.startswith("@@")
                   else "add" if line.startswith("+") else "del" if line.startswith("-") else "")
            spans.append(f"<span class=\"{cls}\">{escape(line) or ' '}</span>")
        return f"<pre class=\"diff\">{''.join(spans)}</pre>"

    def _analysis(self, run: Path, plan) -> str:
        parts = []
        try:
            sources = json.loads((run / "run.json").read_text(encoding="utf-8")).get("sources", [])
        except (OSError, ValueError):
            sources = []
        if sources:
            parts.append("<h2>Sources</h2><table><tr><th>ID</th><th>Path</th><th>Authority</th><th>Origin</th></tr>" +
                         "".join(f"<tr><td>{escape(str(src.get('id')))}</td><td>{escape(str(src.get('path')))}</td>"
                                 f"<td>{escape(str(src.get('authority', 'unconfirmed')))}</td>"
                                 f"<td>{escape(source_origin(src).replace(chr(92) + '|', '|'))}</td></tr>"
                                 for src in sources) + "</table>")
        gate_path = run / "qa" / "gate.json"
        if gate_path.is_file():
            gate = json.loads(gate_path.read_text(encoding="utf-8"))
            verdict = "<span class=\"ok\">PASS</span>" if gate["passed"] else "<span class=\"bad\">FAIL</span>"
            parts.append(f"<h2>Claim gate</h2><p>{verdict}: {gate['statements']} statements, {gate['cited']} backed "
                         f"by claims, {len(gate['exemptions'])} exempt, {len(gate['errors'])} errors.</p>")
            if gate.get("flow_steps") is not None:
                parts.append(f"<p>Numbered steps backed by flow steps: {gate['flow_backed_steps']}/{gate['flow_steps']}.</p>")
            if gate["exemptions"]:
                parts.append("<table><tr><th>Page</th><th>Line</th><th>Reason</th><th>Text</th></tr>" + "".join(
                    f"<tr><td>{escape(e['path'])}</td><td>{e['line']}</td><td>{escape(e['reason'])}</td>"
                    f"<td>{escape(e['text'])}</td></tr>" for e in gate["exemptions"]) + "</table>")
            if gate["errors"]:
                parts.append("<ul>" + "".join(f"<li class=\"bad\">{escape(e['path'])}:{e['line']} {escape(e['message'])}</li>"
                                              for e in gate["errors"]) + "</ul>")
        coverage = run / "analysis" / "COVERAGE.md"
        if coverage.is_file():
            rows = COVERAGE_ROW.findall(coverage.read_text(encoding="utf-8"))
            parts.append("<h2>Coverage</h2><table><tr><th>Claim</th><th>Disposition</th><th>Destination</th></tr>" +
                         "".join(f"<tr><td>{escape(c)}</td><td>{escape(d)}</td><td>{escape(dest.strip())}</td></tr>"
                                 for c, d, dest in rows) + "</table>")
        cross = run / "analysis" / "cross-source.json"
        results = json.loads(cross.read_text(encoding="utf-8")) if cross.is_file() else []
        if results:
            parts.append("<h2>PRD vs code</h2><table><tr><th>Claim</th><th>Status</th><th>Question</th></tr>" + "".join(
                f"<tr><td>{escape(r['claim_id'])}</td><td>{escape(r['status'])}</td>"
                f"<td>{escape(r.get('question') or '')}</td></tr>" for r in results) + "</table>")
        cleanup_path = run / "qa" / "cleanup.json"
        if cleanup_path.is_file():
            cleanup = json.loads(cleanup_path.read_text(encoding="utf-8"))
            parts.append(f"<h2>Clean-up ({escape(str(cleanup.get('pack')))})</h2>")
            rows = [(c["page"], c["line"], c["step"], c["action"], c["before"], c["after"]) for c in cleanup["changes"]]
            rows += [(f["page"], f["line"], f["step"], "finding", f["text"], f["message"]) for f in cleanup["findings"]]
            parts.append("<table><tr><th>Page</th><th>Line</th><th>Step</th><th>Action</th><th>Before</th><th>After</th></tr>"
                         + "".join("<tr>" + "".join(f"<td>{escape(str(v))}</td>" for v in row) + "</tr>" for row in rows)
                         + "</table>" if rows else "<p>No automatic changes.</p>")
        vale_path = run / "qa" / "vale.json"
        if vale_path.is_file():
            vale = json.loads(vale_path.read_text(encoding="utf-8"))
            alerts = vale.get("alerts", [])
            parts.append(f"<h2>Style (Vale {escape(str(vale.get('vale_version')))})</h2>")
            parts.append("<table><tr><th>Page</th><th>Line</th><th>Level</th><th>Rule</th><th>Message</th></tr>" + "".join(
                f"<tr><td>{escape(a['page'])}</td><td>{a['line']}</td><td>{escape(a['severity'])}</td>"
                f"<td>{escape(a['check'])}</td><td>{escape(a['message'])}</td></tr>" for a in alerts) + "</table>"
                if alerts else "<p>No alerts on changed prose.</p>")
        qa = run / "qa" / "QA-REPORT.md"
        readiness = _readiness(qa.read_text(encoding="utf-8")) if qa.is_file() else []
        parts.append("<h2>QA readiness</h2>" + ("".join(f"<p>{escape(re.sub(r'[*`]', '', l))}</p>" for l in readiness)
                                                 or "<p>No QA report.</p>"))
        register = run / "analysis" / "clarifications-and-assumptions.md"
        questions = QUESTION_HEADING.findall(register.read_text(encoding="utf-8")) if register.is_file() else []
        items = [f"<li><b>{escape(q)}</b> {escape(t)}</li>" for q, t in questions]
        items += [f"<li><b>{escape(r['question_id'])}</b> {escape(r['question'])}</li>" for r in results if r.get("question_id")]
        parts.append("<h2>Open questions</h2>" + (f"<ul>{''.join(items)}</ul>" if items else "<p>None recorded.</p>"))
        return "".join(parts)

    def _history(self, run: Path, plan) -> str:
        events = [(h.get("at", ""), h.get("event", ""), {k: v for k, v in h.items() if k not in ("at", "event")})
                  for h in plan.history]
        events += [(f.at, f"feedback: {f.action}", {"reviewer": f.reviewer, "reason": f.reason, "comment": f.comment,
                                                    "page": f.page, "line": f.line, "revision": f.revision})
                   for f in load_feedback(run)]
        rows = "".join(
            f"<tr><td>{escape(at)}</td><td>{escape(event)}</td><td>" + escape(
                "; ".join(f"{k}: {v}" for k, v in detail.items() if v not in (None, "", []))) + "</td></tr>"
            for at, event, detail in sorted(events, key=lambda e: e[0]))
        return f"<table><tr><th>When (UTC)</th><th>Event</th><th>Details</th></tr>{rows}</table>"

    def _forms(self, run: Path, plan) -> str:
        if plan.status == "closed":
            return "<p class=\"muted\">This suggestion is closed.</p>"
        token = escape(self.token)
        reviewer = escape(self.reviewer)
        pages = "".join(f"<option value=\"{escape(p['dest'])}\">{escape(p['dest'])}</option>" for p in plan.placements)
        reasons = "".join(f"<option value=\"{escape(k)}\">{escape(k)}: {escape(v)}</option>" for k, v in CLOSE_REASONS.items())
        name = quote(run.name)
        return (
            "<div class=\"grid\">"
            f"<form method=\"post\" action=\"/s/{name}/request-changes\"><h2>Request changes</h2>"
            f"<input type=\"hidden\" name=\"token\" value=\"{token}\">"
            f"<label for=\"rc-reviewer\">Reviewer</label><input id=\"rc-reviewer\" name=\"reviewer\" value=\"{reviewer}\" required>"
            f"<label for=\"rc-page\">Page (optional)</label><select id=\"rc-page\" name=\"page\"><option value=\"\">Whole suggestion</option>{pages}</select>"
            "<label for=\"rc-line\">Line (optional)</label><input id=\"rc-line\" name=\"line\" inputmode=\"numeric\" pattern=\"[0-9]*\">"
            "<label for=\"rc-comment\">What should change?</label><textarea id=\"rc-comment\" name=\"comment\" required></textarea>"
            "<button type=\"submit\">Request changes</button></form>"
            f"<form method=\"post\" action=\"/s/{name}/close\"><h2>Close suggestion</h2>"
            f"<input type=\"hidden\" name=\"token\" value=\"{token}\">"
            f"<label for=\"cl-reviewer\">Reviewer</label><input id=\"cl-reviewer\" name=\"reviewer\" value=\"{reviewer}\" required>"
            f"<label for=\"cl-reason\">Reason</label><select id=\"cl-reason\" name=\"reason\" required>{reasons}</select>"
            "<label for=\"cl-note\">Note (optional)</label><textarea id=\"cl-note\" name=\"note\"></textarea>"
            "<button type=\"submit\">Close</button></form></div>"
            "<p class=\"muted\">Actions only record feedback on this computer. Each one shows the GitHub command to run yourself.</p>"
        )

    # --- actions ----------------------------------------------------------------------

    def act(self, name: str, action: str, form: dict[str, str]) -> tuple[int, str]:
        """Returns (status, html); on success (303, location) after storing a one-time notice."""
        found = self.runs().get(name)
        if found is None:
            return 404, self.page("Not found", "<h1>Not found</h1>")
        if not hmac.compare_digest(form.get("token", ""), self.token):
            return 403, self.page("Forbidden", "<h1>Forbidden</h1><p>The form token is missing or out of date. Reload the page.</p>")
        run, _ = found
        try:
            if action == "request-changes":
                line = form.get("line", "").strip()
                feedback, order, commands = request_changes(
                    run, comment=form.get("comment", ""), reviewer=form.get("reviewer", ""),
                    page=form.get("page") or None, line=int(line) if line.isdigit() else None)
                done = (f"Recorded change request <code>{escape(feedback.feedback_id)}</code>. "
                        f"Revision work order: <code>{escape(str(order.relative_to(run)))}</code>.")
            elif action == "close":
                feedback, commands = close_suggestion(run, reason=form.get("reason", ""), note=form.get("note", ""),
                                                      reviewer=form.get("reviewer", ""))
                done = f"Closed with reason <code>{escape(feedback.reason)}</code>."
            else:
                return 404, self.page("Not found", "<h1>Not found</h1>")
        except ReviewError as exc:
            return 400, self.suggestion(name, "history", f"<p class=\"bad\">{escape(str(exc))}</p>")
        self.flash[name] = (f"<form><p class=\"ok\">{done}</p><p>To mirror this on GitHub, run:</p>"
                            + "".join(f"<code class=\"cmd\">{escape(c)}</code>" for c in commands) + "</form>")
        return 303, f"/s/{quote(name)}?tab=history"


def make_handler(app: ReviewApp):
    class Handler(BaseHTTPRequestHandler):
        server_version = "docforge-review"

        def _send(self, status: int, html: str) -> None:
            body = html.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Security-Policy", CSP)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            url = urlsplit(self.path)
            if url.path == "/":
                return self._send(200, app.index())
            match = re.fullmatch(r"/s/([A-Za-z0-9._-]+)", url.path)
            if match:
                tab = parse_qs(url.query).get("tab", ["diff"])[0]
                html = app.suggestion(match.group(1), tab, app.flash.pop(match.group(1), ""))
                if html is not None:
                    return self._send(200, html)
            self._send(404, app.page("Not found", "<h1>Not found</h1>"))

        def do_POST(self):  # noqa: N802
            match = re.fullmatch(r"/s/([A-Za-z0-9._-]+)/(request-changes|close)", urlsplit(self.path).path)
            if not match:
                return self._send(404, app.page("Not found", "<h1>Not found</h1>"))
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = -1
            if length < 0 or length > MAX_FORM_BYTES:
                return self._send(413, app.page("Too large", "<h1>Form too large</h1>"))
            raw = self.rfile.read(length).decode("utf-8", "replace")
            form = {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}
            status, result = app.act(match.group(1), match.group(2), form)
            if status == 303:
                self.send_response(303)
                self.send_header("Location", result)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self._send(status, result)

        def log_message(self, fmt, *args):
            sys.stderr.write(f"{self.address_string()} {fmt % args}\n")

    return Handler


def serve(app: ReviewApp, host: str = "127.0.0.1", port: int = 8790) -> None:
    server = ThreadingHTTPServer((host, port), make_handler(app))
    print(f"DocForge review UI on http://{host}:{server.server_address[1]}/ (Ctrl-C to stop)", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
