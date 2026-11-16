import json
from pathlib import Path
import threading
import urllib.error
import urllib.request

import pytest

from docforge.cli import main
from docforge.config import load_config
from docforge.webhook import SECRET_ENV, Receiver, make_handler, sign, verify_signature

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "github"
SECRET = b"test-only-secret"


def body(name):
    return (FIXTURES / name).read_bytes()


@pytest.fixture
def receiver(tmp_path):
    return Receiver(config=load_config(FIXTURES / "triggers.yaml"), secret=SECRET, log=tmp_path / "decisions.jsonl")


def headers(payload: bytes, event="pull_request", secret=SECRET):
    return {"X-GitHub-Event": event, "X-Hub-Signature-256": sign(secret, payload)}


def test_signature_round_trip():
    payload = b'{"a": 1}'
    assert verify_signature(SECRET, payload, sign(SECRET, payload))
    assert not verify_signature(SECRET, payload + b" ", sign(SECRET, payload))
    assert not verify_signature(SECRET, payload, sign(b"other", payload))
    assert not verify_signature(SECRET, payload, None)
    assert not verify_signature(SECRET, payload, "sha1=abc")
    assert not verify_signature(b"", payload, sign(b"", payload))


def test_valid_delivery_is_decided_and_logged(receiver):
    payload = body("pr_merged.json")
    status, data = receiver.handle(headers(payload), payload)
    assert status == 200
    # Webhooks carry no diff, so the directory filter cannot pass without a checkout.
    assert data["docs_needed"] == "no"
    rows = [json.loads(l) for l in receiver.log.read_text(encoding="utf-8").splitlines()]
    assert [r["decision_id"] for r in rows] == [data["decision_id"]]
    assert rows[0]["research_trail"][1]["detail"]["note"] == "no diff supplied"


def test_topic_trigger_needs_no_diff(receiver):
    payload = body("pr_infra_merged.json")
    status, data = receiver.handle(headers(payload), payload)
    assert (status, data["docs_needed"]) == (200, "needs_research")


def test_bad_signature_is_rejected_and_not_logged(receiver):
    payload = body("pr_merged.json")
    status, _ = receiver.handle(headers(payload, secret=b"wrong"), payload)
    assert status == 401
    status, _ = receiver.handle({"X-GitHub-Event": "pull_request"}, payload)
    assert status == 401
    assert not receiver.log.exists()


def test_ping_and_unhandled_events(receiver):
    assert receiver.handle(headers(b"{}", event="ping"), b"{}") == (200, {"ok": True, "pong": True})
    status, data = receiver.handle(headers(b"{}", event="push"), b"{}")
    assert (status, data) == (202, {"ignored": "event 'push' is not handled"})
    assert not receiver.log.exists()


def test_malformed_payloads(receiver):
    assert receiver.handle(headers(b"not json"), b"not json")[0] == 400
    assert receiver.handle(headers(b"{}"), b"{}")[0] == 400


def test_checkout_diff_error_is_recorded(receiver, tmp_path):
    receiver.checkouts = {"example-org/product-web": tmp_path / "not-a-checkout"}
    payload = body("pr_merged.json")
    status, _ = receiver.handle(headers(payload), payload)
    assert status == 200
    trail = json.loads(receiver.log.read_text(encoding="utf-8"))["research_trail"]
    assert trail[1]["detail"]["source"] == "local checkout of example-org/product-web"
    assert trail[1]["detail"]["note"].startswith("diff could not be read: git diff failed")


def test_http_server_end_to_end(receiver):
    from http.server import ThreadingHTTPServer

    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(receiver))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/webhook"
        payload = body("pr_infra_merged.json")
        request = urllib.request.Request(url, data=payload, headers=headers(payload), method="POST")
        with urllib.request.urlopen(request, timeout=10) as response:
            assert response.status == 200
            assert json.loads(response.read())["docs_needed"] == "needs_research"
        bad = urllib.request.Request(url, data=payload, headers={"X-GitHub-Event": "pull_request"}, method="POST")
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(bad, timeout=10)
        assert exc.value.code == 401
    finally:
        server.shutdown()
        server.server_close()


def test_serve_refuses_to_start_without_secret(monkeypatch, capsys):
    monkeypatch.delenv(SECRET_ENV, raising=False)
    assert main(["serve", "--config", str(FIXTURES / "triggers.yaml")]) == 1
    assert SECRET_ENV in capsys.readouterr().err
