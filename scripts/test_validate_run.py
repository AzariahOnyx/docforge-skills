#!/usr/bin/env python3
"""Regression fixtures for custom profiles, provenance, citations and review gates.

These fixtures test the validator, not AI-generated documentation quality.
"""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from validate_run import validate

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "demo" / "mock-prd.md"

class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name) / "run"
        (self.run / "analysis").mkdir(parents=True)
        (self.run / "api").mkdir()
        self.manifest = {
            "schema_version": 1, "profile": "custom", "audience": "developers",
            "sources": [{"id": "S1", "path": "demo/mock-prd.md",
                         "sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest()}],
            "deliverables": ["api/reference.md"],
            "review": {"method": "same_agent_second_pass", "source_fidelity": "pending",
                       "product_verification": "pending", "human_approval": "pending"}
        }
        self.evidence = [{
            "claim_id": "C01", "source_id": "S1",
            "quote": "Quiet Hours lets a member pause their own in-app alerts for a selected period.",
            "status": "included", "destinations": ["api/reference.md"]
        }]
        self.body = ("# Quiet Hours reference\n\n"
                     "This is a fictional integration overview. Quiet Hours pauses a member's own "
                     "in-app alerts. Source: [S1#L8]. No endpoint is specified.\n")
        self.write()
    def write(self):
        (self.run / "run.json").write_text(json.dumps(self.manifest), encoding="utf-8")
        (self.run / "analysis" / "evidence.json").write_text(json.dumps(self.evidence), encoding="utf-8")
        (self.run / "api" / "reference.md").write_text(self.body, encoding="utf-8")
    def assert_invalid(self, needle):
        errors, _ = validate(self.run, REPO)
        self.assertTrue(any(needle in x for x in errors), errors)
    def test_valid_custom_profile(self):
        errors, warnings = validate(self.run, REPO)
        self.assertEqual(errors, [])
        self.assertTrue(any("not independent" in x for x in warnings))
    def test_source_hash_tampering(self):
        self.manifest["sources"][0]["sha256"] = "0" * 64
        self.write()
        self.assert_invalid("source hash mismatch")
    def test_fabricated_quote(self):
        self.evidence[0]["quote"] = "The API guarantees 99.99 percent uptime."
        self.write()
        self.assert_invalid("quotation not found")
    def test_unlisted_document(self):
        self.manifest["deliverables"] = ["api/missing.md"]
        self.write()
        self.assert_invalid("missing Markdown deliverable")
    def test_missing_approval_gate(self):
        self.manifest["review"]["human_approval"] = "passed"
        self.write()
        self.assert_invalid("human approval cannot pass")
    def test_invalid_source_locator(self):
        self.body = self.body.replace("S1#L8", "S1#L9999")
        self.write()
        self.assert_invalid("invalid or blank source locator")
    def test_untrusted_source_id(self):
        self.body = self.body.replace("S1#L8", "OTHER#L8")
        self.write()
        self.assert_invalid("unknown source ID")
    def test_duplicate_evidence(self):
        self.evidence.append(dict(self.evidence[0]))
        self.write()
        self.assert_invalid("duplicate evidence claim")
    def test_included_without_destination(self):
        self.evidence[0]["destinations"] = []
        self.write()
        self.assert_invalid("lacks an existing deliverable")
    def test_traversal(self):
        self.manifest["deliverables"] = ["../../README.md"]
        self.write()
        self.assert_invalid("Path escapes allowed root")
    def test_placeholder(self):
        self.body += "\nTODO: verify all endpoints.\n"
        self.write()
        self.assert_invalid("unresolved placeholder")
    def test_unclosed_fence(self):
        self.body += "\n```bash\nexample\n"
        self.write()
        self.assert_invalid("unclosed code fence")

if __name__ == "__main__":
    unittest.main(verbosity=2)
