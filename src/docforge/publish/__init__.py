"""Publishing: evidence markers, the claim gate, suggestion branches and PR drafts."""

from .branch import BRANCH_PREFIX, BranchResult, PublishError, create_branch, diff_commits, update_branch
from .gate import (
    EvidenceManifest,
    EvidenceRules,
    GateError,
    GateResult,
    check_pages,
    gate_manifest,
    gate_run,
    rules_for_run,
)
from .markers import Statement, read_marker, statements
from .place import pack_placements
from .plan import (
    PrPlan,
    apply_ready,
    load_plan,
    mark_ready,
    open_pr,
    prepare_publish,
    resolve_commands,
    save_plan,
    update_publish,
)
from .pr_body import default_title, render_body

__all__ = [
    "apply_ready",
    "open_pr",
    "pack_placements",
    "BRANCH_PREFIX",
    "BranchResult",
    "EvidenceManifest",
    "EvidenceRules",
    "GateError",
    "GateResult",
    "PrPlan",
    "PublishError",
    "Statement",
    "check_pages",
    "create_branch",
    "default_title",
    "gate_manifest",
    "gate_run",
    "mark_ready",
    "prepare_publish",
    "read_marker",
    "render_body",
    "rules_for_run",
    "statements",
    "update_publish",
    "save_plan",
    "resolve_commands",
    "load_plan",
    "update_branch",
    "diff_commits",
]
