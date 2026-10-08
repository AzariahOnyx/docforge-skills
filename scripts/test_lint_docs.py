#!/usr/bin/env python3
"""Test Markdown lint heuristics with deliberately good and bad examples."""
import unittest
from lint_docs import lint

class MarkdownLintTests(unittest.TestCase):
    def test_clean(self):
        source = "# Title\n\n## Steps\n\nSee [the setup guide](setup.md).\n"
        self.assertEqual(lint(source), [])
    def test_generic_link(self):
        self.assertIn("generic-link", [x[1] for x in lint("# Title\n\n[click here](guide.md)")])
    def test_empty_image_alt(self):
        self.assertIn("image-alt", [x[1] for x in lint("# Title\n\n![](image.png)")])
    def test_heading_skip(self):
        self.assertIn("heading-level-skip", [x[1] for x in lint("# Title\n\n### Jump")])
    def test_terminology(self):
        self.assertIn("terminology", [x[1] for x in lint("# Title\n\nAdd to the whitelist.")])
    def test_code_ignored(self):
        self.assertEqual(lint("# Title\n\n```md\n[click here](test)\n```"), [])
    def test_subjective_wording(self):
        self.assertIn("wording", [x[1] for x in lint("# Title\n\nSimply select it.")])

if __name__ == "__main__":
    unittest.main(verbosity=2)
