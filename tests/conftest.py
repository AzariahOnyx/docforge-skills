"""Shared fixtures: a made-up product repo with a base and a head commit."""

import json
from pathlib import Path
import shutil
import subprocess

import pytest

RESEARCH = Path(__file__).resolve().parent / "fixtures" / "research"
CODE_REPO = "example-org/pulseboard-web"


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=Test", "-c", "user.email=test@example.com",
         "-c", "commit.gpgsign=false", *args],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def _commit_tree(root: Path, tree: Path, message: str) -> str:
    for item in root.iterdir():
        if item.name != ".git":
            shutil.rmtree(item) if item.is_dir() else item.unlink()
    shutil.copytree(tree, root, dirs_exist_ok=True)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message)
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def research_repo(tmp_path):
    """(checkout path, base SHA, head SHA) for example-org/pulseboard-web."""
    root = tmp_path / "pulseboard-web"
    root.mkdir()
    git(root, "init", "-q")
    base = _commit_tree(root, RESEARCH / "base", "base")
    head = _commit_tree(root, RESEARCH / "head", "Add Quiet Hours")
    return root, base, head


def materialize_claims(root: Path, head: str) -> dict:
    """claims.template.json with each code entry's commit and excerpt hash filled in."""
    from docforge.research import code_ref

    data = json.loads((RESEARCH / "claims.template.json").read_text(encoding="utf-8"))
    data.pop("_comment", None)
    for claim in data["claims"]:
        for entry in claim.get("code", []):
            ref = code_ref(root, CODE_REPO, head, entry["path"], entry["lines"])
            entry.update(repo=ref.repo, commit=ref.commit, lines=ref.lines, excerpt_sha256=ref.excerpt_sha256)
    return data


@pytest.fixture(autouse=True)
def isolated_rules(tmp_path, monkeypatch):
    """Every test sees an empty learned-rules folder unless it sets one up."""
    folder = tmp_path / "learned-rules"
    monkeypatch.setenv("DOCFORGE_RULES_DIR", str(folder))
    return folder


class StubServer:
    """A local HTTP server for connector tests. Never touches the network.

    `routes` maps a path (with query) to (status, body bytes, extra headers).
    Every request is recorded as (method, path, headers dict, body bytes).
    """

    def __init__(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        import threading

        self.routes: dict[str, tuple[int, bytes, dict]] = {}
        self.requests: list[tuple[str, str, dict, bytes]] = []
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def _answer(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                stub.requests.append((self.command, self.path, dict(self.headers), body))
                status, payload, headers = stub.routes.get(self.path, (404, b"{}", {}))
                self.send_response(status)
                for key, value in {"Content-Type": "application/json", **headers}.items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = do_POST = _answer

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def json(self, path: str, data, status: int = 200, headers: dict | None = None):
        self.routes[path] = (status, json.dumps(data).encode(), headers or {})

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def stub_server():
    server = StubServer()
    yield server
    server.close()
