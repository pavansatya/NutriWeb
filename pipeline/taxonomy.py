"""Resolve OFF category-taxonomy properties needed by the Nutri-Score variants.

Two Nutri-Score flags cannot be read off `categories_tags` directly:

  * `is_fat_oil_nuts_seeds` — nuts and seeds are identified by WCO Harmonized
    System headings (08.01, 08.02, 12.02, 12.04, 12.06, 12.07) and codes
    (2008.11, 2008.19), not by a single parent category.
  * `is_red_meat_product` — identified by HS headings 02.01–02.06.

Upstream reads these via taxonomy *inheritance*: a category inherits
`wco_hs_heading` from its ancestors. We reproduce that by downloading OFF's
categories taxonomy once and propagating the property down the parent graph.

The result is two flat sets of category ids, cached to JSON so the curate step
stays offline and deterministic.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

TAXONOMY_URL = "https://static.openfoodfacts.org/data/taxonomies/categories.json"

FAT_OIL_NUTS_SEEDS_HEADINGS = {"08.01", "08.02", "12.02", "12.04", "12.06", "12.07"}
FAT_OIL_NUTS_SEEDS_CODES = {"2008.11", "2008.19"}
RED_MEAT_HEADINGS = {"02.01", "02.02", "02.03", "02.04", "02.05", "02.06"}

CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "nutriscore_categories.json"


def _download() -> dict:
    print(f"Fetching category taxonomy from {TAXONOMY_URL} ...")
    with urllib.request.urlopen(TAXONOMY_URL, timeout=300) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _direct_property(entry: dict, prop: str) -> str | None:
    """Read a taxonomy property, which OFF stores as {prop: {lang: value}}."""
    block = entry.get(prop)
    if isinstance(block, dict):
        value = block.get("en")
        return str(value) if value is not None else None
    return str(block) if block is not None else None


def _resolve_inherited(taxonomy: dict, prop: str) -> dict[str, str]:
    """Resolve `prop` for every category, walking up parents when unset.

    OFF's taxonomy is a DAG (a category may have several parents), so we memoise
    and guard against cycles. First parent with a value wins, matching upstream's
    depth-first get_inherited_property_from_categories_tags.
    """
    resolved: dict[str, str] = {}
    in_progress: set[str] = set()

    def visit(cid: str) -> str | None:
        if cid in resolved:
            return resolved[cid]
        if cid in in_progress:  # cycle guard
            return None
        entry = taxonomy.get(cid)
        if entry is None:
            return None

        in_progress.add(cid)
        value = _direct_property(entry, prop)
        if value is None:
            for parent in entry.get("parents", []) or []:
                value = visit(parent)
                if value is not None:
                    break
        in_progress.discard(cid)

        if value is not None:
            resolved[cid] = value
        return value

    for cid in taxonomy:
        visit(cid)
    return resolved


def build(force: bool = False) -> dict[str, list[str]]:
    """Return {'fat_oil_nuts_seeds': [...], 'red_meat': [...]} category ids."""
    if CACHE_PATH.exists() and not force:
        return json.loads(CACHE_PATH.read_text())

    taxonomy = _download()
    headings = _resolve_inherited(taxonomy, "wco_hs_heading")
    codes = _resolve_inherited(taxonomy, "wco_hs_code")

    fat_ids = {
        cid for cid, h in headings.items() if h in FAT_OIL_NUTS_SEEDS_HEADINGS
    } | {
        cid for cid, c in codes.items() if c in FAT_OIL_NUTS_SEEDS_CODES
    }
    # Chestnuts are explicitly excluded from the fats/nuts/seeds category.
    fat_ids.discard("en:chestnuts")

    red_meat_ids = {cid for cid, h in headings.items() if h in RED_MEAT_HEADINGS}

    result = {
        "fat_oil_nuts_seeds": sorted(fat_ids),
        "red_meat": sorted(red_meat_ids),
    }
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(result, indent=1))
    print(
        f"Resolved {len(fat_ids)} fat/oil/nuts/seeds and "
        f"{len(red_meat_ids)} red-meat categories -> {CACHE_PATH}"
    )
    return result


def load() -> tuple[frozenset[str], frozenset[str]]:
    """Convenience accessor returning the two sets."""
    data = build()
    return frozenset(data["fat_oil_nuts_seeds"]), frozenset(data["red_meat"])


if __name__ == "__main__":
    build(force=True)
