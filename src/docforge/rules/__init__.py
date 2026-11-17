"""Learned rules: proposed from review feedback, tried against past runs, approved by a person."""

from .live import guidance_lines, lint_config, live_rules, sync_live, vale_rule
from .model import Rule, RuleError, TrialReport, approve, close, load_rule, load_rules, propose, rules_dir, save_rule
from .suggest import feedback_digest
from .trial import find_runs, run_pages, try_rule

__all__ = [
    "Rule",
    "RuleError",
    "TrialReport",
    "approve",
    "close",
    "feedback_digest",
    "find_runs",
    "guidance_lines",
    "lint_config",
    "live_rules",
    "load_rule",
    "load_rules",
    "propose",
    "rules_dir",
    "run_pages",
    "save_rule",
    "sync_live",
    "try_rule",
    "vale_rule",
]
