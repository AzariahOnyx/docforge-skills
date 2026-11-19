"""Place a run's drafts in the docs repository from the pack's `placement` templates.

The first template whose `applies_to` matches a deliverable gives its path. Values come from the run's product
key and the draft's front matter, made into lowercase slugs. A missing value is an error, never a guess.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re

from .branch import PublishError

SLUG_CHARS = re.compile(r"[^a-z0-9]+")


def slugify(value) -> str:
    return SLUG_CHARS.sub("-", str(value).casefold()).strip("-")[:80]


def _front_matter(path: Path) -> dict:
    from docforge.docs_index.build import split_front_matter

    warnings: list[str] = []
    data, _ = split_front_matter(path.read_text(encoding="utf-8").splitlines(), warnings)
    return data if isinstance(data, dict) else {}


def pack_placements(run: Path, *, now: datetime | None = None) -> list[tuple[str, str]]:
    """(deliverable, docs path) for every deliverable that exists, from the run's pack templates."""
    from docforge.packs import PackError
    from docforge.packs.load import run_manifest
    from docforge.packs.model import PLACEMENT_FIELD_RE, applies

    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    record = manifest.get("pack")
    if not record:
        raise PublishError("the run has no pack, so there are no placement templates; use --place")
    try:
        pack = run_manifest(run, record)
    except PackError as exc:
        raise PublishError(f"pack: {exc}") from None
    if not pack.placement:
        raise PublishError(f"pack {pack.name} has no placement templates; use --place")
    month = (now or datetime.now(timezone.utc)).strftime("%Y-%m")
    placements = []
    for deliverable in manifest.get("deliverables", []):
        if not (run / deliverable).is_file():
            continue
        template = next((p for p in pack.placement if applies(p.applies_to, deliverable)), None)
        if template is None:
            raise PublishError(f"no placement template in pack {pack.name} applies to {deliverable}")
        front = _front_matter(run / deliverable)
        values = {
            "product": record.get("product"),
            "category": front.get("category"),
            "slug": front.get("slug") or front.get("title"),
            "month": front.get("release_month") or month,
        }
        missing = []

        def fill(match: re.Match) -> str:
            name = match.group(1)
            value = slugify(values[name]) if values[name] else ""
            if not value:
                missing.append(name)
            return value

        path = PLACEMENT_FIELD_RE.sub(fill, template.path)
        if missing:
            where = {"product": "the run (start it with --product)", "month": "front matter release_month"}
            raise PublishError(f"{deliverable}: cannot place it with {template.path}: no "
                               + ", ".join(f"{m} (from {where.get(m, 'front matter')})" for m in missing))
        placements.append((deliverable, path))
    if not placements:
        raise PublishError("the run has no drafted deliverables to place")
    return placements
