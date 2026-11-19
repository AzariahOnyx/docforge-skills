"""A local stand-in for the GitHub API: pull requests, comments and the GraphQL ready mutation.

It keeps pull requests in memory, records every request (with headers) and never touches the network.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
import threading
from urllib.parse import parse_qs, urlsplit


class FakeGithub:
    def __init__(self, token: str = "fictional-github-token"):
        self.token = token
        self.pulls: dict[int, dict] = {}
        self.comments: list[dict] = []
        self.requests: list[tuple[str, str, dict, dict | None]] = []
        self.fail_next: int | None = None  # HTTP status for the next request, then cleared
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def _answer(self):
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b""
                body = json.loads(raw) if raw else None
                stub.requests.append((self.command, self.path, dict(self.headers), body))
                if stub.fail_next:
                    status, stub.fail_next = stub.fail_next, None
                    return self._send(status, {"message": "failure"})
                if self.headers.get("Authorization") != f"Bearer {stub.token}":
                    return self._send(401, {"message": "Bad credentials"})
                status, payload = stub.route(self.command, self.path, body)
                self._send(status, payload)

            def _send(self, status, payload):
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = do_POST = do_PATCH = _answer

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def route(self, method: str, path: str, body):
        parts = urlsplit(path)
        if parts.path == "/graphql" and method == "POST":
            node = (body or {}).get("variables", {}).get("id")
            pr = next((p for p in self.pulls.values() if p["node_id"] == node), None)
            if pr is None:
                return 200, {"errors": [{"message": "not found"}]}
            pr["draft"] = False
            return 200, {"data": {"markPullRequestReadyForReview": {"pullRequest": {"isDraft": False}}}}
        match = re.fullmatch(r"/repos/([^/]+)/([^/]+)/(pulls|issues)(?:/(\d+))?(/comments)?", parts.path)
        if not match:
            return 404, {"message": "Not Found"}
        owner, name, kind, number, comments = match.groups()
        repo = f"{owner}/{name}"
        if kind == "issues" and comments and method == "POST":
            comment = {"id": len(self.comments) + 1, "issue": int(number), "body": body["body"]}
            self.comments.append(comment)
            return 201, comment
        if kind == "pulls" and number is None and method == "GET":
            query = parse_qs(parts.query)
            head = query.get("head", [""])[0].split(":", 1)[-1]
            return 200, [p for p in self.pulls.values() if p["repo"] == repo and p["head"]["ref"] == head]
        if kind == "pulls" and number is None and method == "POST":
            if any(p["head"]["ref"] == body["head"] and p["state"] == "open" for p in self.pulls.values()):
                return 422, {"message": "A pull request already exists"}
            n = len(self.pulls) + 1
            self.pulls[n] = {"number": n, "repo": repo, "node_id": f"PR_node{n}", "state": "open",
                             "draft": bool(body.get("draft")), "title": body["title"], "body": body["body"],
                             "base": {"ref": body["base"]}, "head": {"ref": body["head"]},
                             "html_url": f"https://github.example/{repo}/pull/{n}"}
            return 201, self.pulls[n]
        if kind == "pulls" and number is not None:
            pr = self.pulls.get(int(number))
            if pr is None:
                return 404, {"message": "Not Found"}
            if method == "PATCH":
                pr.update({k: v for k, v in body.items() if k in ("body", "title")})
            return 200, pr
        return 404, {"message": "Not Found"}

    def close(self):
        self.server.shutdown()
        self.server.server_close()
