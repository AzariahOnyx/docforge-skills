import pytest

from docforge.evidence import (
    ClaimClass,
    CodeEvidence,
    EvidenceStatus,
    QuoteEvidence,
    ReviewMethod,
    ReviewStatus,
    parse_evidence,
    parse_line_range,
    parse_manifest,
)

SHA = "a" * 64
COMMIT = "b" * 40


def manifest(**overrides):
    data = {
        "schema_version": 1,
        "profile": "custom",
        "audience": "developers",
        "sources": [{"id": "S1", "path": "demo/mock-prd.md", "sha256": SHA, "authority": "primary"}],
        "deliverables": ["api/reference.md"],
        "review": {
            "method": "not_reviewed",
            "source_fidelity": "pending",
            "product_verification": "pending",
            "human_approval": "pending",
        },
    }
    data.update(overrides)
    return data


def code_row(**overrides):
    row = {
        "claim_id": "C02",
        "kind": "code",
        "repo": "example-org/product-web",
        "commit": COMMIT,
        "path": "src/quiet_hours.py",
        "lines": "L3-L5",
        "excerpt_sha256": SHA,
        "status": "included",
        "destinations": ["api/reference.md"],
    }
    row.update(overrides)
    return row


# --- claim classes ---------------------------------------------------------


def test_five_claim_classes():
    assert [c.value for c in ClaimClass] == ["FACT", "ASSUMPTION", "INFERENCE", "UNKNOWN", "CONTRADICTION"]


# --- run.json --------------------------------------------------------------


def test_valid_manifest_is_typed():
    parsed, errors = parse_manifest(manifest())
    assert errors == []
    assert parsed.sources[0].id == "S1"
    assert parsed.sources[0].sha256 == SHA
    assert parsed.sources[0].authority == "primary"
    assert parsed.review.method is ReviewMethod.NOT_REVIEWED
    assert parsed.review.human_approval is ReviewStatus.PENDING


def test_manifest_collects_every_error():
    _, errors = parse_manifest(
        manifest(schema_version=2, profile="other", audience=" ", sources=[], deliverables=[], review={})
    )
    assert errors == [
        "schema_version must be 1",
        "profile must be default or custom",
        "audience is required",
        "sources must be a nonempty list",
        "deliverables must be a nonempty list",
        "review.method must identify reviewer method",
        "review.source_fidelity has invalid status",
        "review.product_verification has invalid status",
        "review.human_approval has invalid status",
    ]


def test_manifest_must_be_an_object():
    _, errors = parse_manifest([])
    assert errors[0] == "run.json must contain an object"


def test_source_without_valid_hash_keeps_source_but_errors():
    parsed, errors = parse_manifest(manifest(sources=[{"id": "S1", "path": "x.md", "sha256": "ABC"}]))
    assert "S1: sha256 is required" in errors
    assert parsed.sources[0].sha256 is None


def test_bad_and_duplicate_source_ids():
    sources = [
        {"id": "S1", "path": "a.md", "sha256": SHA},
        {"id": "S1", "path": "b.md", "sha256": SHA},
        {"id": "1bad", "path": "c.md", "sha256": SHA},
        "not an object",
    ]
    parsed, errors = parse_manifest(manifest(sources=sources))
    assert [s.path for s in parsed.sources] == ["a.md"]
    assert {"duplicate source ID S1", "invalid source ID", "source entry must be an object"} <= set(errors)


def test_human_approval_needs_source_fidelity():
    review = {
        "method": "human_reviewer",
        "source_fidelity": "pending",
        "product_verification": "passed",
        "human_approval": "passed",
    }
    _, errors = parse_manifest(manifest(review=review))
    assert errors == ["human approval cannot pass with source fidelity pending or failed"]


# --- evidence.json ---------------------------------------------------------


def test_row_without_kind_is_quote_evidence():
    rows, errors = parse_evidence(
        [{"claim_id": "C01", "source_id": "S1", "quote": "x", "status": "included", "destinations": ["a.md"]}]
    )
    assert errors == []
    assert isinstance(rows[0], QuoteEvidence)
    assert rows[0].status is EvidenceStatus.INCLUDED
    assert rows[0].claim_class is None


@pytest.mark.parametrize("data", [[], {}, "x", None])
def test_evidence_must_be_nonempty_array(data):
    assert parse_evidence(data) == ([], ["evidence must be a nonempty array"])


def test_non_object_row():
    _, errors = parse_evidence(["oops"])
    assert errors == ["invalid evidence.json: row 1 is not an object"]


def test_shared_row_checks():
    rows = [
        {"claim_id": "X1", "source_id": "S1", "quote": "q", "status": "maybe", "destinations": "a.md"},
        {"claim_id": "C01", "source_id": "S1", "quote": "q", "status": "context", "destinations": []},
        {"claim_id": "C01", "source_id": "S1", "quote": "q", "status": "context", "destinations": []},
    ]
    _, errors = parse_evidence(rows)
    assert errors == [
        "invalid or duplicate evidence claim X1",
        "X1: invalid evidence status",
        "X1: destinations must be a list",
        "invalid or duplicate evidence claim C01",
    ]


def test_code_row_is_typed():
    rows, errors = parse_evidence([code_row()])
    assert errors == []
    row = rows[0]
    assert isinstance(row, CodeEvidence)
    assert (row.repo, row.commit, row.path, row.start_line, row.end_line) == (
        "example-org/product-web",
        COMMIT,
        "src/quiet_hours.py",
        3,
        5,
    )
    assert row.lines == "L3-L5"


@pytest.mark.parametrize(
    "field, value, message",
    [
        ("repo", "product-web", "repo must be owner/repo"),
        ("commit", "abc123", "full 40-character lowercase SHA"),
        ("commit", "B" * 40, "full 40-character lowercase SHA"),
        ("path", "/etc/passwd", "path must be relative"),
        ("path", "../secrets.txt", "path must be relative"),
        ("path", "src/../../x.py", "path must be relative"),
        ("path", "", "path must be relative"),
        ("lines", "10-20", "lines must look like L10 or L10-L24"),
        ("lines", "L0", "lines must look like L10 or L10-L24"),
        ("lines", "L9-L3", "lines must look like L10 or L10-L24"),
        ("excerpt_sha256", None, "excerpt_sha256 is required"),
    ],
)
def test_bad_code_fields(field, value, message):
    rows, errors = parse_evidence([code_row(**{field: value})])
    assert rows == []
    assert any(message in e for e in errors), errors


def test_unknown_kind():
    _, errors = parse_evidence([code_row(kind="screenshot")])
    assert errors == ["C02: unknown evidence kind 'screenshot'"]


def test_invalid_claim_class():
    _, errors = parse_evidence([code_row(claim_class="GUESS")])
    assert errors == ["C02: invalid claim_class 'GUESS'"]


@pytest.mark.parametrize("cls", ["UNKNOWN", "CONTRADICTION"])
def test_unknown_or_contradiction_cannot_be_included(cls):
    _, errors = parse_evidence([code_row(claim_class=cls)])
    assert errors == [f"C02: {cls} claim cannot be included"]


@pytest.mark.parametrize("cls", ["UNKNOWN", "CONTRADICTION"])
def test_unknown_or_contradiction_may_be_blocked(cls):
    rows, errors = parse_evidence([code_row(claim_class=cls, status="blocked", destinations=[])])
    assert errors == []
    assert rows[0].claim_class is ClaimClass(cls)


def test_fact_can_be_included():
    rows, errors = parse_evidence([code_row(claim_class="FACT")])
    assert errors == []
    assert rows[0].claim_class is ClaimClass.FACT


@pytest.mark.parametrize(
    "value, expected",
    [("L7", (7, 7)), ("L3-L5", (3, 5)), ("L3-5", (3, 5)), ("L5-L3", None), ("L0", None), ("7", None), (7, None)],
)
def test_parse_line_range(value, expected):
    assert parse_line_range(value) == expected
