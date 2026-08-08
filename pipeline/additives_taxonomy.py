"""Derive additive concern levels from Open Food Facts' additives taxonomy.

The app this replaces classified additives with a hand-written dictionary of
~90 substrings (`nutriweb/risk_levels.py`), matched with `if key in name`. That
produced both false positives ("sugar" matching "sugar-free") and unsourced
verdicts.

OFF's additives taxonomy carries properties backed by real regulatory
assessments, which we use instead:

  * `efsa_evaluation_overexposure_risk` — EFSA's finding on whether normal
    consumption can exceed the acceptable daily intake (high / moderate / no).
  * `anses_additives_of_interest` — ANSES' watch list.
  * `non_nutritive_sweetener` — required by the Nutri-Score 2023 beverage
    penalty, which adds 4 negative points when one is present.

Every verdict the app shows is therefore attributable to a named authority.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

TAXONOMY_URL = "https://static.openfoodfacts.org/data/taxonomies/additives.json"
CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "additives.json"


def _prop(entry: dict, name: str) -> str | None:
    block = entry.get(name)
    if isinstance(block, dict):
        value = block.get("en")
        return str(value) if value is not None else None
    return str(block) if block is not None else None


def build(force: bool = False) -> dict:
    """Emit {tag: {name, e_number, concern, reasons[], non_nutritive_sweetener}}."""
    if CACHE_PATH.exists() and not force:
        return json.loads(CACHE_PATH.read_text())

    print(f"Fetching additives taxonomy from {TAXONOMY_URL} ...")
    with urllib.request.urlopen(TAXONOMY_URL, timeout=120) as resp:
        taxonomy = json.loads(resp.read().decode("utf-8"))

    out: dict[str, dict] = {}
    for tag, entry in taxonomy.items():
        overexposure = (_prop(entry, "efsa_evaluation_overexposure_risk") or "").lower()
        anses = (_prop(entry, "anses_additives_of_interest") or "").lower() == "yes"
        sweetener = (_prop(entry, "non_nutritive_sweetener") or "").lower() == "yes"

        reasons: list[str] = []
        if overexposure.endswith("high"):
            concern = "high"
            reasons.append("EFSA: high risk of exceeding the acceptable daily intake")
        elif overexposure.endswith("moderate"):
            concern = "moderate"
            reasons.append("EFSA: moderate risk of exceeding the acceptable daily intake")
        else:
            concern = "none"

        if anses:
            reasons.append("On ANSES' list of additives of interest")
            if concern == "none":
                concern = "watch"

        # Only keep entries that carry a signal worth surfacing.
        if concern == "none" and not sweetener:
            continue

        out[tag] = {
            "name": _prop(entry, "name") or tag,
            "e_number": _prop(entry, "e_number"),
            "concern": concern,
            "reasons": reasons,
            "non_nutritive_sweetener": sweetener,
        }

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(out, indent=1, sort_keys=True))

    counts: dict[str, int] = {}
    for meta in out.values():
        counts[meta["concern"]] = counts.get(meta["concern"], 0) + 1
    print(f"Wrote {len(out)} additives to {CACHE_PATH}: {counts}")
    return out


if __name__ == "__main__":
    build(force=True)
