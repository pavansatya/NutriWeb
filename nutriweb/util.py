"""Coercion helpers for values coming out of DuckDB via pandas.

DuckDB list and numeric columns surface as several different "missing" sentinels
depending on the column's type and whether the frame went through Arrow: None,
float('nan'), and pandas.NA all appear. `pd.NA` in particular raises on both
`bool()` and `iter()`, so a plain `if value is not None` guard is not enough.
These two helpers are the single place that knows about it.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def is_missing(value: Any) -> bool:
    """True for None, NaN, and pandas.NA — without raising on arrays."""
    if value is None:
        return True
    try:
        result = pd.isna(value)
    except (TypeError, ValueError):
        return False
    # pd.isna returns an array for list-likes; a present list is not missing.
    return bool(result) if isinstance(result, bool) else False


def tag_set(value: Any) -> set[str]:
    """Coerce a DuckDB list column to a set of strings."""
    if is_missing(value):
        return set()
    try:
        return {str(v) for v in value}
    except TypeError:
        return set()


def num(value: Any) -> float | None:
    """Coerce a numeric column to float, mapping every missing form to None."""
    if is_missing(value):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return None if pd.isna(result) else result
