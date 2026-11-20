"""The "docs needed?" decision for code pull requests: path rules, then a model, then a person."""

from .decide import TriageResult, triage
from .rules import DEFAULT_PATHS, apply_rules, glob_regex

__all__ = ["DEFAULT_PATHS", "TriageResult", "apply_rules", "glob_regex", "triage"]
