"""Receive GitHub webhooks, check their signature, and log a docs decision.

For source pull requests the receiver only records decisions. With --docs-runs it
also handles review on DocForge's own docs pull requests (see docforge.github.docs_pr):
revisions are pushed and replies posted only when the auto_create_pr policy allows.
It never merges anything. The shared secret comes from the DOCFORGE_WEBHOOK_SECRET environment
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
    # Review on DocForge's own docs pull requests, when serve is given --docs-runs.
    docs: "DocsPrEndpoint | None" = None

    def handle(self, headers: Mapping[str, str], body: bytes) -> tuple[int, dict]:
        """Process one delivery. Returns (HTTP status, JSON response)."""
        lower = {k.lower(): v for k, v in headers.items()}
        if not verify_signature(self.secret, body, lower.get("x-hub-signature-256")):
            return 401, {"error": "invalid or missing signature"}
        github_event = lower.get("x-github-event", "")
        if github_event == "ping":
            return 200, {"ok": True, "pong": True}
        if self.docs is not None:
            handled = self.docs.handle(github_event, body, lower.get("x-github-delivery"))
            if handled is not None:
                return handled
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
        if self.docs is not None and event.kind == "merge":
            self.docs.source_merged(event.repo, event.number)
        return 200, {"decision_id": decision.decision_id, "docs_needed": decision.docs_needed,
                     "summary": decision.summary}


@dataclass
class JiraEndpoint:
    """POST /jira/webhook: verify and decide at once; pending work runs on one background worker."""

    config: DocForgeConfig
    config_path: Path
    trigger: str
    state_root: Path
    client_factory: object = None
    run_work: bool = True

    def __post_init__(self):
        import queue
        import threading

        self.queue: "queue.Queue[str]" = queue.Queue()
        self._worker = threading.Thread(target=self._work, daemon=True)
        self._worker.start()

    def handle(self, headers: Mapping[str, str], body: bytes) -> tuple[int, dict]:
        from docforge.jira import HandleError, handle

        lower = {k.lower(): v for k, v in headers.items()}
        try:
            result = handle(body, config=self.config, trigger_name=self.trigger, state_root=self.state_root,
                            signature=lower.get("x-hub-signature"),
                            delivery_id=lower.get("x-atlassian-webhook-identifier"),
                            client_factory=self.client_factory)
        except HandleError as exc:
            status = 401 if "signature" in str(exc) or "not set" in str(exc) else 400
            return status, {"error": str(exc)}
        if self.run_work and result.get("action") in ("plan", "draft", "revise", "ship"):
            self.queue.put(result["issue"])
            result["queued"] = True
        return 202, result

    def _work(self) -> None:
        from docforge.jira.work import process

        while True:
            key = self.queue.get()
            try:
                process(key, config=self.config, config_path=self.config_path, trigger_name=self.trigger,
                        state_root=self.state_root, client_factory=self.client_factory)
            except Exception as exc:  # the worker must survive one ticket's failure
                sys.stderr.write(f"jira worker: {key}: {type(exc).__name__}: {exc}\n")
            finally:
                self.queue.task_done()


@dataclass
class DocsPrEndpoint:
    """Review on DocForge's own docs pull requests: record each delivery at once; revisions run on one
    background worker after the quiet period."""

    config: DocForgeConfig
    config_path: Path
    roots: list[Path]
    checkout: Path | None = None  # overrides each doc collection's checkout
    run_work: bool = True
    poll_seconds: float = 15.0
    jira: "JiraEndpoint | None" = None  # an approved plan pull request queues the ticket's drafting here

    def __post_init__(self):
        import queue
        import threading

        self.wake = threading.Event()
        self.merged: "queue.Queue[tuple[str, int]]" = queue.Queue()
        if self.run_work:
            threading.Thread(target=self._work, daemon=True).start()

    def checkout_for(self, repo: str) -> Path | None:
        if self.checkout is not None:
            return self.checkout
        collection = self.config.doc_collections.get(repo)
        return (self.config_path.parent / collection.checkout).resolve() if collection and collection.checkout else None

    def handle(self, github_event: str, body: bytes, delivery_id: str | None) -> tuple[int, dict] | None:
        """(status, response) for an event about one of DocForge's pull requests; None for any other event."""
        from docforge.github.docs_pr import DocsPrError, find_run, handle_docs_event
        from docforge.github.events import parse_docs_event

        try:
            payload = json.loads(body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None
        event = parse_docs_event(github_event, payload)
        if event is None:
            return None
        found = find_run(self.roots, event.repo, event.number, event.branch)
        if found is None:
            return None if github_event in SUPPORTED_EVENTS else (202, {"ignored": "not a DocForge pull request"})
        try:
            if found[1].kind == "plan-pr":
                from docforge.plan.review import handle_plan_event

                result = handle_plan_event(event, run=found[0], config=self.config, delivery_id=delivery_id)
            else:
                result = handle_docs_event(event, run=found[0], config=self.config, delivery_id=delivery_id)
        except (DocsPrError, OSError, ValueError) as exc:
            return 400, {"error": str(exc)}
        self.wake.set()
        return 202, result

    def source_merged(self, repo: str, number: int) -> None:
        self.merged.put((repo, number))
        self.wake.set()

    def _work(self) -> None:
        from docforge.github.docs_pr import find_runs, process_revision, source_merged

        while True:
            self.wake.wait(timeout=self.poll_seconds)
            self.wake.clear()
            while not self.merged.empty():
                repo, number = self.merged.get()
                try:
                    source_merged(self.roots, repo, number, config=self.config)
                except Exception as exc:  # the worker must survive one failure
                    sys.stderr.write(f"docs pr worker: {repo}#{number}: {type(exc).__name__}: {exc}\n")
            from docforge.plan.review import ACTIVE, process_plan_pr

            for run, plan in find_runs(self.roots, ("pr", "plan-pr")):
                try:
                    if plan.kind == "plan-pr":
                        if plan.status in ACTIVE:
                            process_plan_pr(run, config=self.config, checkout=self.checkout_for(plan.repo),
                                            on_approved=self.approved)
                    elif plan.status in ("changes_requested", "revised") and not plan.github_state:
                        process_revision(run, config=self.config, checkout=self.checkout_for(plan.repo))
                except Exception as exc:
                    sys.stderr.write(f"docs pr worker: {run.name}: {type(exc).__name__}: {exc}\n")

    def approved(self, run: Path) -> None:
        """A plan pull request was approved: queue the Jira ticket's drafting (Jira runs only)."""
        if self.jira is None:
            return
        from docforge.jira.work import queue_draft_after_approval

        key = (json.loads((run / "run.json").read_text(encoding="utf-8")).get("ia_plan") or {}).get("jira")
        if key and key != "none" and queue_draft_after_approval(self.jira.state_root, key):
            self.jira.queue.put(key)


def make_handler(receiver: Receiver | None, jira: JiraEndpoint | None = None):
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
            path = self.path.split("?", 1)[0]
            target = jira if path == "/jira/webhook" else (receiver if path in PATHS else None)
            if target is None:
                return self._reply(404, {"error": "not found"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                return self._reply(400, {"error": "invalid Content-Length"})
            if length < 0 or length > MAX_BODY_BYTES:
                return self._reply(413, {"error": "body too large"})
            status, data = target.handle(dict(self.headers.items()), self.rfile.read(length))
            self._reply(status, data)

        def do_GET(self):  # noqa: N802
            self._reply(405, {"error": "POST webhooks to this address"})

        def log_message(self, fmt, *args):
            # One line per request; never the body, headers or secret.
            sys.stderr.write(f"{self.address_string()} {fmt % args}\n")

    return Handler


def serve(receiver: Receiver | None, host: str = "127.0.0.1", port: int = 8787, jira: JiraEndpoint | None = None) -> None:
    server = ThreadingHTTPServer((host, port), make_handler(receiver, jira))
    if receiver:
        print(f"Listening for GitHub webhooks on http://{host}:{port}/webhook; decisions go to {receiver.log}",
              file=sys.stderr)
    if jira:
        print(f"Listening for Jira webhooks on http://{host}:{port}/jira/webhook (trigger {jira.trigger}); "
              f"ticket state in {jira.state_root}", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
