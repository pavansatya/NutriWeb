"""Additive concern lookup, backed by OFF's EFSA/ANSES-sourced taxonomy.

Replaces the substring matching in the old `nutriweb/risk_levels.py`. Lookups
are exact on OFF's canonical additive tags (`en:e250`), so "sugar-free" can no
longer be flagged as containing sugar.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "additives.json"

# How much each concern level costs in the health score, in points out of 100.
CONCERN_PENALTY = {"high": 6.0, "moderate": 3.0, "watch": 1.5, "none": 0.0}

# Cap the total additive penalty so a long ingredient list cannot dominate the
# nutrition signal outright.
MAX_ADDITIVE_PENALTY = 18.0


@lru_cache(maxsize=1)
def _table() -> dict[str, dict]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"{DATA_PATH} missing. Run: python pipeline/additives_taxonomy.py"
        )
    return json.loads(DATA_PATH.read_text())


def lookup(tag: str) -> dict | None:
    """Return the concern record for an OFF additive tag, or None if unflagged."""
    return _table().get(tag)


def concerns(additives_tags: list[str] | None) -> list[dict]:
    """Flagged additives in a product, worst first, for display."""
    order = {"high": 0, "moderate": 1, "watch": 2}
    found = [
        {"tag": tag, **meta}
        for tag in (additives_tags or ())
        if (meta := lookup(tag)) and meta["concern"] != "none"
    ]
    return sorted(found, key=lambda a: order.get(a["concern"], 9))


def penalty(additives_tags: list[str] | None) -> float:
    """Total health-score penalty from a product's additives, capped."""
    total = sum(CONCERN_PENALTY.get(a["concern"], 0.0) for a in concerns(additives_tags))
    return min(total, MAX_ADDITIVE_PENALTY)


def has_non_nutritive_sweetener(additives_tags: list[str] | None) -> bool:
    """Whether any additive is a non-nutritive sweetener.

    Drives the Nutri-Score 2023 beverage penalty of 4 negative points.
    """
    return any(
        (meta := lookup(tag)) and meta.get("non_nutritive_sweetener")
        for tag in (additives_tags or ())
    )
