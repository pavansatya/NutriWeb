"""Hard safety filters — the rules a recommendation must never violate.

These are deliberately separate from ranking. A product that fails any of these
is removed, never merely demoted, so an allergen can't be outweighed by a good
health score.

The same functions power the "why this is / isn't for you" panel on the product
page, so what the user is told always matches what the engine actually did.
"""

from __future__ import annotations

from dataclasses import dataclass

from nutriweb.profile.model import (
    SALT_CEILING_G_100G,
    SATURATED_FAT_CEILING_G_100G,
    UserProfile,
)
from nutriweb.scoring import additives as additives_mod
from nutriweb.util import num, tag_set


@dataclass
class Verdict:
    """Why a product passed or failed, in the user's terms."""

    passed: bool
    blockers: list[str]
    warnings: list[str]

    @property
    def summary(self) -> str:
        if self.blockers:
            return "Not suitable for you"
        if self.warnings:
            return "Check before buying"
        return "Fits your profile"


def _tags(product: dict, key: str) -> set[str]:
    return tag_set(product.get(key))


def _num(product: dict, key: str) -> float | None:
    return num(product.get(key))


def evaluate(product: dict, profile: UserProfile) -> Verdict:
    """Check a product against a profile.

    Blockers exclude a product outright. Warnings are surfaced but do not
    exclude -- traces and health-condition ceilings are advisory, because a
    "may contain" label and a genuine ingredient are different risks.
    """
    blockers: list[str] = []
    warnings: list[str] = []

    allergens = set(profile.allergens)
    if allergens:
        contains = allergens & _tags(product, "allergens_tags")
        if contains:
            blockers.append(f"Contains {_label(contains)}")

        traces = allergens & _tags(product, "traces_tags")
        if traces:
            warnings.append(f"May contain traces of {_label(traces)}")

    analysis = _tags(product, "ingredients_analysis_tags")
    if profile.wants_vegan:
        if "en:non-vegan" in analysis:
            blockers.append("Not vegan")
        elif "en:vegan" not in analysis:
            warnings.append("Vegan status unconfirmed")
    elif profile.wants_vegetarian:
        if "en:non-vegetarian" in analysis:
            blockers.append("Not vegetarian")
        elif "en:vegetarian" not in analysis:
            warnings.append("Vegetarian status unconfirmed")

    if profile.wants_palm_oil_free and "en:palm-oil" in analysis:
        blockers.append("Contains palm oil")

    if profile.high_blood_pressure:
        salt = _num(product, "salt_derived")
        if salt is not None and salt > SALT_CEILING_G_100G:
            warnings.append(f"High in salt ({salt:.1f} g/100 g) — you flagged high blood pressure")

    if profile.high_cholesterol:
        satfat = _num(product, "saturated_fat_100g")
        if satfat is not None and satfat > SATURATED_FAT_CEILING_G_100G:
            warnings.append(
                f"High in saturated fat ({satfat:.1f} g/100 g) — you flagged high cholesterol"
            )

    if profile.avoid_flagged_additives:
        flagged = additives_mod.concerns(list(_tags(product, "additives_tags")))
        high = [a for a in flagged if a["concern"] == "high"]
        if high:
            blockers.append(
                "Contains additives flagged by EFSA: "
                + ", ".join(a["name"] for a in high[:3])
            )

    return Verdict(passed=not blockers, blockers=blockers, warnings=warnings)


def _label(tags: set[str]) -> str:
    """Turn OFF tags into readable text: {'en:peanuts'} -> 'peanuts'."""
    return ", ".join(sorted(t.split(":", 1)[-1].replace("-", " ") for t in tags))


def sql_exclusions(profile: UserProfile) -> tuple[str, list]:
    """Push the blocking filters into SQL so candidates are excluded up front.

    Mirrors the blockers in `evaluate`. Doing this in the database avoids
    pulling thousands of rows into Python only to discard them, and keeps the
    candidate pool honest -- filtering after a LIMIT would silently shrink it.
    """
    clauses: list[str] = []
    params: list = []

    if profile.allergens:
        clauses.append(
            "NOT list_has_any(COALESCE(allergens_tags, []::VARCHAR[]), ?::VARCHAR[])"
        )
        params.append(list(profile.allergens))

    if profile.wants_vegan:
        clauses.append(
            "NOT list_contains(COALESCE(ingredients_analysis_tags, []::VARCHAR[]), 'en:non-vegan')"
        )
    elif profile.wants_vegetarian:
        clauses.append(
            "NOT list_contains(COALESCE(ingredients_analysis_tags, []::VARCHAR[]), "
            "'en:non-vegetarian')"
        )

    if profile.wants_palm_oil_free:
        clauses.append(
            "NOT list_contains(COALESCE(ingredients_analysis_tags, []::VARCHAR[]), 'en:palm-oil')"
        )

    if profile.high_blood_pressure:
        clauses.append(f"(salt_derived IS NULL OR salt_derived <= {SALT_CEILING_G_100G})")

    if profile.high_cholesterol:
        clauses.append(
            f"(saturated_fat_100g IS NULL OR "
            f"saturated_fat_100g <= {SATURATED_FAT_CEILING_G_100G})"
        )

    return (" AND ".join(clauses) if clauses else "TRUE"), params
