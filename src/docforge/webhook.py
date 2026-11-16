"""Receive GitHub webhooks, check their signature, and log a docs decision.

The receiver only records decisions. It never comments on, opens, or merges
anything. The shared secret comes from the DOCFORGE_WEBHOOK_SECRET environment
variable and is never logged. By default it listens on 127.0.0.1 only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from typing import Mapping

from docforge.agent import append_decision, decide
from docforge.config import DocForgeConfig
from docforge.sources import DiffError, EventError, changes_for_event, parse_event
from docforge.sources.github_event import SUPPORTED_EVENTS

SECRET_ENV = "DOCFORGE_WEBHOOK_SECRET"
MAX_BODY_BYTES = 5 * 1024 * 1024
PATHS = ("/", "/webhook")


def sign(secret: bytes, body: bytes) -> str:
    """The X-Hub-Signature-256 value GitHub sends for this body."""
    return "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()


def verify_signature(secret: bytes, body: bytes, header: str | None) -> bool:
    if not secret or not header or not header.startswith("sha256="):
        return False
    return hmac.compare_digest(sign(secret, body), header)


@dataclass
class Receiver:
    config: DocForgeConfig
    secret: bytes
    log: Path
    # Local checkouts used to diff a PR's base and head commits, keyed by owner/repo.
    checkouts: dict[str, Path] = field(default_factory=dict)

    def handle(self, headers: Mapping[str, str], body: bytes) -> tuple[int, dict]:
        """Process one delivery. Returns (HTTP status, JSON response)."""
        lower = {k.lower(): v for k, v in headers.items()}
        if not verify_signature(self.secret, body, lower.get("x-hub-signature-256")):
            return 401, {"error": "invalid or missing signature"}
        github_event = lower.get("x-github-event", "")
        if github_event == "ping":
            return 200, {"ok": True, "pong": True}
        if github_event not in SUPPORTED_EVENTS:
            return 202, {"ignored": f"event {github_event!r} is not handled"}
        try:
            payload = json.loads(body.decode("utf-8"))
            event = parse_event(github_event, payload)
        except (ValueError, UnicodeDecodeError) as exc:
            return 400, {"error": f"invalid JSON: {exc}"}
        except EventError as exc:
            return 400, {"error": str(exc)}

        changed, source, error = None, None, None
        checkout = self.checkouts.get(event.repo.casefold())
        if checkout is not None and event.base_sha and event.head_sha:
            try:
                changed, source = changes_for_event(event.base_sha, event.head_sha, checkout=checkout)
            except DiffError as exc:
                source, error = f"local checkout of {event.repo}", str(exc)
        decision = decide(self.config, event, changed, diff_source=source, diff_error=error)
        append_decision(self.log, decision)
        return 200, {"decision_id": decision.decision_id, "docs_needed": decision.docs_needed,
                     "summary": decision.summary}


def make_handler(receiver: Receiver):
    class Handler(BaseHTTPRequestHandler):
        server_version = "docforge-webhook"

        def _reply(self, status: int, data: dict) -> None:
            body = json.dumps(data).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):  # noqa: N802 (http.server naming)
            if self.path.split("?", 1)[0] not in PATHS:
                return self._reply(404, {"error": "not found"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                return self._reply(400, {"error": "invalid Content-Length"})
            if length < 0 or length > MAX_BODY_BYTES:
                return self._reply(413, {"error": "body too large"})
            status, data = receiver.handle(dict(self.headers.items()), self.rfile.read(length))
            self._reply(status, data)

        def do_GET(self):  # noqa: N802
            self._reply(405, {"error": "POST GitHub webhooks to this address"})

        def log_message(self, fmt, *args):
            # One line per request; never the body, headers or secret.
            sys.stderr.write(f"{self.address_string()} {fmt % args}\n")

    return Handler


def serve(receiver: Receiver, host: str = "127.0.0.1", port: int = 8787) -> None:
    server = ThreadingHTTPServer((host, port), make_handler(receiver))
    print(f"Listening for GitHub webhooks on http://{host}:{port}/webhook; decisions go to {receiver.log}",
          file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
