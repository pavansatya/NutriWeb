"""Nutri-Score 2023 (v2) — a faithful port of Open Food Facts' reference implementation.

Why this exists
---------------
58% of US products in Open Food Facts carry `nutriscore_grade = 'unknown'`. Nutri-Score
is a European scheme and OFF often cannot assign it to US items, usually because the
category needed to pick the algorithm variant is missing. Ranking "healthier alternatives"
on OFF's grade alone would therefore silently discard most of the US catalog.

So NutriWeb computes the grade itself wherever the input nutrients exist. We keep OFF's
own grade alongside ours and never merge the two — the UI always states which is which.

Provenance
----------
Ported from `lib/ProductOpener/Nutriscore.pm` (`compute_nutriscore_score_2023`) and the
category predicates in `lib/ProductOpener/Food.pm`, from openfoodfacts-server @ main.
Threshold tables are reproduced verbatim; the irregular steps (e.g. beverage energy
jumping 30/90/150/210 then by 30) are intentional and match upstream.

Reference: Nutri-Score 2023 main algorithm update, Santé publique France.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Threshold tables — verbatim from Nutriscore.pm %points_thresholds_2023
# --------------------------------------------------------------------------
# A value scores one point per threshold it exceeds (strictly greater than),
# except saturated_fat_ratio which uses >=.

THRESHOLDS: dict[str, list[float]] = {
    # negative
    "energy": [335, 670, 1005, 1340, 1675, 2010, 2345, 2680, 3015, 3350],  # kJ/100g
    "energy_beverages": [30, 90, 150, 210, 240, 270, 300, 330, 360, 390],
    "sugars": [3.4, 6.8, 10, 14, 17, 20, 24, 27, 31, 34, 37, 41, 44, 48, 51],  # g/100g
    "sugars_beverages": [0.5, 2, 3.5, 5, 6, 7, 8, 9, 10, 11],
    "saturated_fat": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # g/100g
    "salt": [0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.4, 1.6, 1.8, 2,
             2.2, 2.4, 2.6, 2.8, 3, 3.2, 3.4, 3.6, 3.8, 4],  # g/100g
    # fats/oils/nuts/seeds variant
    "energy_from_saturated_fat": [120, 240, 360, 480, 600, 720, 840, 960, 1080, 1200],
    "saturated_fat_ratio": [10, 16, 22, 28, 34, 40, 46, 52, 58, 64],  # %
    # positive
    # 80 repeats so that >80% earns the full 5 points; this is upstream's encoding.
    "fruits_vegetables_legumes": [40, 60, 80, 80, 80],  # %
    "fruits_vegetables_legumes_beverages": [40, 40, 60, 60, 80, 80],  # yields 0/2/4/6
    "fiber": [3.0, 4.1, 5.2, 6.3, 7.4],  # g/100g, AOAC
    "proteins": [2.4, 4.8, 7.2, 9.6, 12, 14, 17],  # g/100g
    "proteins_beverages": [1.2, 1.5, 1.8, 2.1, 2.4, 2.7, 3.0],
}

# Energy density of fat, used to derive energy-from-saturates for the fats variant.
KJ_PER_G_FAT = 37.0

# --------------------------------------------------------------------------
# Category predicates — from Food.pm
# --------------------------------------------------------------------------
# OFF's `categories_tags` is the *expanded* tag list: it already contains every
# ancestor category, so a plain membership test is equivalent to upstream's
# has_tag() walk up the taxonomy.

BEVERAGE_ROOTS = {"en:beverages", "en:beverage-preparations"}
NOT_BEVERAGES_2023 = {"en:meal-replacement", "en:soups"}
ALSO_BEVERAGES_2023 = {
    "en:milks", "en:plant-based-milk-alternatives", "en:dairy-drinks",
    "en:plant-based-beverages", "en:tea-based-beverages", "en:iced-teas",
    "en:herbal-tea-beverages", "en:coffee-beverages", "en:coffee-drinks",
    "en:coffees", "en:herbal-teas", "en:teas",
}
FAT_OIL_NUTS_SEEDS_ROOTS = {"en:fats", "en:creams", "en:seeds"}

# Products OFF exempts from Nutri-Score entirely. We honour the same list so we
# don't invent grades for salt, spices, or alcohol.
EXEMPTED = {
    "en:alcoholic-beverages", "en:baby-foods", "en:baby-milks", "en:chewing-gum",
    "en:food-additives", "en:dietary-supplements", "en:meal-replacements",
    "en:salts", "en:spices", "en:sugar-substitutes", "en:vinegars",
    "en:non-food-products",
}
NOT_EXEMPTED = {
    "en:tea-based-beverages", "en:iced-teas", "en:herbal-tea-beverages",
    "en:coffee-beverages", "en:coffee-drinks",
}


@dataclass
class CategoryFlags:
    """Which algorithm variant applies, derived from `categories_tags`."""

    is_beverage: bool = False
    is_water: bool = False
    is_cheese: bool = False
    is_fat_oil_nuts_seeds: bool = False
    is_red_meat_product: bool = False


def category_flags(
    categories_tags: list[str] | None,
    fat_oil_nuts_seeds_ids: frozenset[str] = frozenset(),
    red_meat_ids: frozenset[str] = frozenset(),
) -> CategoryFlags:
    """Derive the Nutri-Score variant flags from a product's category tags.

    `fat_oil_nuts_seeds_ids` and `red_meat_ids` come from
    `pipeline/taxonomy.py`, which resolves the WCO Harmonized-System properties
    that upstream reads via taxonomy inheritance. Passing empty sets falls back
    to the explicit root categories only.
    """
    tags = set(categories_tags or ())

    is_beverage = bool(tags & BEVERAGE_ROOTS) and not (tags & NOT_BEVERAGES_2023)
    if tags & ALSO_BEVERAGES_2023:
        is_beverage = True

    is_water = "en:spring-waters" in tags and not (
        tags & {"en:flavored-waters", "en:flavoured-waters"}
    )
    is_cheese = "en:cheeses" in tags and "fr:fromages-blancs" not in tags

    if "en:chestnuts" in tags:
        is_fat = False
    else:
        is_fat = bool(tags & FAT_OIL_NUTS_SEEDS_ROOTS) or bool(tags & fat_oil_nuts_seeds_ids)

    return CategoryFlags(
        is_beverage=is_beverage,
        is_water=is_water,
        is_cheese=is_cheese,
        is_fat_oil_nuts_seeds=is_fat,
        is_red_meat_product=bool(tags & red_meat_ids),
    )


def is_exempt(categories_tags: list[str] | None) -> bool:
    """True if OFF excludes this product from Nutri-Score (salt, spices, alcohol...)."""
    tags = set(categories_tags or ())
    return bool(tags & EXEMPTED) and not (tags & NOT_EXEMPTED)


# --------------------------------------------------------------------------
# Point assignment
# --------------------------------------------------------------------------


def _points(value: float | None, table_key: str) -> int:
    """One point per threshold exceeded. Missing values score 0, per upstream."""
    if value is None:
        return 0
    table = THRESHOLDS[table_key]
    # The saturated fat ratio table is the one that uses >= rather than >.
    if table_key == "saturated_fat_ratio":
        return sum(1 for t in table if value >= t)
    return sum(1 for t in table if value > t)


def _table(nutrient: str, is_beverage: bool) -> str:
    """Beverages use their own table where one exists."""
    key = f"{nutrient}_beverages"
    return key if is_beverage and key in THRESHOLDS else nutrient


@dataclass
class NutriScoreResult:
    score: int
    grade: str
    negative_points: int
    positive_points: int
    counted_proteins: bool
    detail: dict[str, int] = field(default_factory=dict)


def compute(
    *,
    energy_kj: float | None,
    sugars: float | None,
    saturated_fat: float | None,
    salt: float | None,
    fiber: float | None,
    proteins: float | None,
    fruits_vegetables_legumes: float | None,
    fat: float | None = None,
    has_non_nutritive_sweeteners: bool = False,
    flags: CategoryFlags | None = None,
) -> NutriScoreResult | None:
    """Compute the 2023 Nutri-Score. All nutrients are per 100 g / 100 ml.

    Returns None when there is too little data to score honestly — see
    `has_sufficient_data`. Absent *optional* nutrients (fiber, fruit content)
    score 0 points, matching upstream, which is a conservative penalty.
    """
    flags = flags or CategoryFlags()

    if not has_sufficient_data(
        energy_kj=energy_kj, sugars=sugars, saturated_fat=saturated_fat,
        salt=salt, proteins=proteins,
    ):
        return None

    # In the fats/oils/nuts/seeds variant, energy is replaced by energy-from-saturates
    # and saturated fat by the saturates-to-fat ratio.
    if flags.is_fat_oil_nuts_seeds:
        energy_value = (saturated_fat or 0.0) * KJ_PER_G_FAT
        energy_key = "energy_from_saturated_fat"
        satfat_value = (
            (saturated_fat / fat * 100.0) if fat not in (None, 0) and saturated_fat is not None
            else None
        )
        satfat_key = "saturated_fat_ratio"
    else:
        energy_value, energy_key = energy_kj, "energy"
        satfat_value, satfat_key = saturated_fat, "saturated_fat"

    bev = flags.is_beverage
    detail = {
        "energy": _points(energy_value, _table(energy_key, bev)),
        "sugars": _points(sugars, _table("sugars", bev)),
        "saturated_fat": _points(satfat_value, satfat_key),
        "salt": _points(salt, "salt"),
        "fiber": _points(fiber, "fiber"),
        "proteins": _points(proteins, _table("proteins", bev)),
        "fruits_vegetables_legumes": _points(
            fruits_vegetables_legumes, _table("fruits_vegetables_legumes", bev)
        ),
    }

    # Red meat products cap protein at 2 points, so a fatty sausage cannot
    # protein its way to a good grade.
    if flags.is_red_meat_product:
        detail["proteins"] = min(detail["proteins"], 2)

    negative = detail["energy"] + detail["sugars"] + detail["saturated_fat"] + detail["salt"]
    # Beverages carrying non-nutritive sweeteners take 4 extra negative points.
    if bev:
        detail["non_nutritive_sweeteners"] = 4 if has_non_nutritive_sweeteners else 0
        negative += detail["non_nutritive_sweeteners"]

    # Protein only counts when the product isn't already heavily penalised —
    # otherwise processed meats and cheeses would score as health foods.
    if bev or flags.is_cheese:
        count_proteins = True
    elif flags.is_fat_oil_nuts_seeds:
        count_proteins = negative < 7
    else:
        count_proteins = negative < 11

    positive = detail["fiber"] + detail["fruits_vegetables_legumes"]
    if count_proteins:
        positive += detail["proteins"]

    score = negative - positive
    return NutriScoreResult(
        score=score,
        grade=grade_for(score, flags),
        negative_points=negative,
        positive_points=positive,
        counted_proteins=count_proteins,
        detail=detail,
    )


def grade_for(score: int, flags: CategoryFlags) -> str:
    """Map a numeric score to a letter. Cutoffs differ by variant."""
    if flags.is_beverage:
        if flags.is_water:
            return "a"  # unflavoured spring water is graded A by definition
        if score <= 2:
            return "b"
        if score <= 6:
            return "c"
        if score <= 9:
            return "d"
        return "e"
    if flags.is_fat_oil_nuts_seeds:
        if score <= -6:
            return "a"
        if score <= 2:
            return "b"
        if score <= 10:
            return "c"
        if score <= 18:
            return "d"
        return "e"
    if score <= 0:
        return "a"
    if score <= 2:
        return "b"
    if score <= 10:
        return "c"
    if score <= 18:
        return "d"
    return "e"


def has_sufficient_data(
    *,
    energy_kj: float | None,
    sugars: float | None,
    saturated_fat: float | None,
    salt: float | None,
    proteins: float | None,
) -> bool:
    """Whether we have enough to compute a grade we're willing to show.

    Upstream treats every missing nutrient as 0 points, which would hand a
    product with no nutrition data whatsoever a clean 'A'. We require the four
    negative-side drivers plus protein to be present, so a sparse record is
    reported as unscored rather than as healthy.
    """
    return all(v is not None for v in (energy_kj, sugars, saturated_fat, salt, proteins))
