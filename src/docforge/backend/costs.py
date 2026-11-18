"""Estimate the cost of API calls from token usage.

Prices are US dollars per million tokens. The defaults are a dated snapshot and
can be overridden per model in docforge.yaml (`backend.prices`). Costs are
estimates for a person's information; the provider's bill is authoritative.
"""

from __future__ import annotations

from docforge.config import ModelPrice

PRICES_AS_OF = "2026-11-03"
# Cache writes: 1.25x input for the 5-minute TTL, 2x input for the 1-hour TTL. Cache reads as listed.
DEFAULT_PRICES: dict[str, ModelPrice] = {
    "claude-opus-5-5": ModelPrice(input=4.0, output=20.0, cache_read=0.20, cache_write_5m=5.0, cache_write_1h=8.0),
    "claude-opus-5": ModelPrice(input=5.0, output=25.0, cache_read=0.50, cache_write_5m=6.25, cache_write_1h=10.0),
    "claude-opus-4-8": ModelPrice(input=5.0, output=25.0, cache_read=0.50, cache_write_5m=6.25, cache_write_1h=10.0),
    "claude-sonnet-5-5": ModelPrice(input=2.0, output=10.0, cache_read=0.10, cache_write_5m=2.5, cache_write_1h=4.0),
    "claude-sonnet-5": ModelPrice(input=2.0, output=10.0, cache_read=0.20, cache_write_5m=2.5, cache_write_1h=4.0),
    "claude-haiku-5-5": ModelPrice(input=0.10, output=0.50, cache_read=0.01, cache_write_5m=0.125, cache_write_1h=0.20),
}


def price_for(model: str, overrides: dict[str, ModelPrice] | None = None) -> ModelPrice | None:
    overrides = overrides or {}
    return overrides.get(model) or DEFAULT_PRICES.get(model)


def _get(obj, name: str) -> int:
    value = obj.get(name) if isinstance(obj, dict) else getattr(obj, name, None)
    return int(value or 0)


def usage_cost(usage, model: str, overrides: dict[str, ModelPrice] | None = None) -> float | None:
    """Dollar cost of one usage record (top-level usage or one iteration). None if the model has no price."""
    price = price_for(model, overrides)
    if price is None:
        return None
    creation = usage.get("cache_creation") if isinstance(usage, dict) else getattr(usage, "cache_creation", None)
    write_1h = _get(creation, "ephemeral_1h_input_tokens") if creation else 0
    write_total = _get(usage, "cache_creation_input_tokens")
    write_5m = max(write_total - write_1h, 0)
    dollars = (_get(usage, "input_tokens") * price.input + _get(usage, "output_tokens") * price.output
               + _get(usage, "cache_read_input_tokens") * price.cache_read
               + write_5m * price.cache_write_5m + write_1h * price.cache_write_1h)
    return dollars / 1_000_000


def estimate_upper_bound(input_tokens: int, max_tokens: int, model: str,
                         overrides: dict[str, ModelPrice] | None = None) -> float | None:
    """Worst case for one call: every input token written to the 1-hour cache, and max_tokens of output."""
    price = price_for(model, overrides)
    if price is None:
        return None
    return (input_tokens * max(price.input, price.cache_write_1h) + max_tokens * price.output) / 1_000_000
