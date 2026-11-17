"""Vale style linting on changed prose, with safe automatic fixes."""

from .fix import Fix, FixPlan, apply_fixes, plan_fixes
from .vale import DEFAULT_CONFIG, Alert, LintError, LintResult, changed_lines, find_vale, lint_run, run_vale

__all__ = [
    "Alert",
    "DEFAULT_CONFIG",
    "Fix",
    "FixPlan",
    "LintError",
    "LintResult",
    "apply_fixes",
    "changed_lines",
    "find_vale",
    "lint_run",
    "plan_fixes",
    "run_vale",
]
