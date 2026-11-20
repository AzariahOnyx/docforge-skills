"""The "docs needed?" decision for one code pull request: path rules first, the model only when they cannot
decide, and a person confirms whenever neither can. Every outcome comes with its reasons."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

from docforge.config import DocForgeConfig
from docforge.sources import ChangedFile, PrEvent

from .model import judge
from .rules import apply_rules


@dataclass
class TriageResult:
    outcome: str  # quiet, act, confirm
    category: str
    reasons: list[str]
    layer: str  # rules, model, none
    files: dict[str, str] = field(default_factory=dict)
    products: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    owners: list[str] = field(default_factory=list)
    model: dict | None = None
    cost_usd: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def _docs_matches(config: DocForgeConfig, collection: str | None, config_path: Path | None, query: str) -> list[dict]:
    if not collection or config_path is None or not query.strip():
        return []
    target = config.doc_collections.get(collection)
    if target is None or not target.checkout:
        return []
    root = (config_path.parent / target.checkout).resolve()
    if not root.is_dir():
        return []
    from docforge.docs_index import DocsIndexError, search

    try:
        hits = search(root, query, collection=target, limit=5, match="any")
    except DocsIndexError:
        return []
    return [{"path": h.path, "text": f"{h.title}" + (f" > {h.heading}" if h.heading else "")} for h in hits]


def triage(config: DocForgeConfig, event: PrEvent, changed: list[ChangedFile] | None, *, diff_text: str = "",
           ledger: Path, config_path: Path | None = None, client=None) -> TriageResult:
    repo = config.code_repos.get(event.repo) or next(
        (r for name, r in config.code_repos.items() if name.casefold() == event.repo.casefold()), None)
    if repo is None:
        return TriageResult("confirm", "unmapped_repo", [f"{event.repo} is not in the dependency map (code_repos); "
                                                         "a person decides"], "none")
    rules = apply_rules(repo, config.triage, changed)
    result = TriageResult(rules.outcome, rules.category, list(rules.reasons), "rules", rules.files, rules.products,
                          rules.features, rules.owners)
    if rules.outcome != "undecided":
        return result
    area = {"repo": event.repo, "products": rules.products, "features": rules.features}
    from .model import build_user

    user = build_user(title=event.title, body=event.body, files=rules.files, diff=diff_text,
                      max_diff=config.triage.max_diff_chars, area=area,
                      docs=_docs_matches(config, repo.doc_collection, config_path, event.title))
    judgement = judge(config.triage, user=user, ledger=ledger, client=client)
    flagged = [r for r in rules.reasons if r.endswith("changed too")]
    outcome = judgement.outcome
    if outcome == "quiet" and flagged:
        outcome = "confirm"  # UI text or flags changed: a person confirms, whatever the model thought
        flagged = [f"{r}; a person confirms" for r in flagged]
    result.outcome, result.category = outcome, judgement.category
    result.reasons += [judgement.reason] + flagged
    result.layer = "model" if judgement.model and judgement.error is None and judgement.cost_usd is not None else "none"
    result.model = {"model": judgement.model, "evidence": judgement.evidence, "request_id": judgement.request_id,
                    "error": judgement.error}
    result.cost_usd = round(judgement.cost_usd or 0.0, 6)
    return result
