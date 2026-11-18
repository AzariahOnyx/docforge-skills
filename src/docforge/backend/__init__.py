"""Run documentation stages through the Anthropic API (opt-in; see runner.py for the safety rules)."""

from .client import BackendError
from .context import ContextError, build_request
from .runner import StageOutcome, exec_run, recorded_calls, spent

__all__ = ["BackendError", "ContextError", "StageOutcome", "build_request", "exec_run", "recorded_calls", "spent"]
