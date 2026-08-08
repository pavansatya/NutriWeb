"""The recommendation engine: healthier, similar, and safe for this person.

Three stages, in order:

  1. Candidate generation — products of the same *kind*. Constrained to a
     shared category tag, which is what stops a soda from returning a candy
     bar. Falls back to ingredient overlap for the ~49% of US products that
     carry no category at all.

  2. Hard filters — allergens, diet, and health-condition ceilings, applied in
     SQL before the LIMIT so the pool is filtered rather than truncated.

  3. Ranking — a weighted composite of health gain, macro similarity and
     ingredient overlap, with every component returned so the UI can explain
     each result rather than assert it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from nutriweb.data import catalog
from nutriweb.profile.model import UserProfile
from nutriweb.reco import filters, similarity

# Ranking weights. They sum to 1.0 and live here so they can be justified and
# tuned in one place rather than being scattered through the query.
W_HEALTH_GAIN = 0.45
W_MACRO = 0.30
W_INGREDIENT = 0.20
W_POPULARITY = 0.05

# A category tag must cover at least this many scored products to be a usable
# candidate pool; otherwise we widen to a more general tag.
MIN_POOL = 12

# Ceiling on how many candidates we pull into Python for ranking. Candidates
# are ordered by popularity so the cap keeps the well-known products.
MAX_CANDIDATES = 1500


@dataclass
class Recommendation:
    product: dict
    health_gain: float
    macro_similarity: float
    ingredient_similarity: float
    score: float
    shared_macros: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def why(self) -> str:
        """One line explaining this specific swap."""
        parts = [f"+{self.health_gain:.0f} health points"]
        if self.shared_macros:
            parts.append("similar " + ", ".join(self.shared_macros[:3]))
        if self.ingredient_similarity >= 0.3:
            parts.append(f"{self.ingredient_similarity * 100:.0f}% shared ingredients")
        return " · ".join(parts)


from nutriweb.util import tag_set as _tag_set  # noqa: E402


def choose_category(product: dict) -> str | None:
    """Pick the most specific category tag with a large enough candidate pool.

    `categories_tags` is not reliably ordered general-to-specific, so we rank
    the product's tags by how many products sit under each and take the
    smallest that still clears MIN_POOL. Smallest pool == most specific.
    """
    tags = [
        t for t in _tag_set(product.get("categories_tags"))
        if t not in ("en:null", "en:undefined")
    ]
    if not tags:
        return None

    sizes = catalog.category_sizes(tags)
    usable = [(n, t) for t, n in sizes.items() if n >= MIN_POOL]
    if usable:
        return min(usable)[1]  # smallest qualifying pool
    # Nothing clears the bar; use the broadest tag we have rather than nothing.
    return max(((n, t) for t, n in sizes.items()), default=(0, None))[1]


def _candidates_by_category(
    category: str, code: str, min_health: float, where: str, params: list
) -> pd.DataFrame:
    return catalog.connect().execute(
        f"""
        SELECT {catalog.PRODUCT_COLUMNS}
        FROM catalog
        WHERE list_contains(categories_tags, ?)
          AND code <> ?
          AND health_score IS NOT NULL
          AND health_score > ?
          AND {where}
        ORDER BY COALESCE(unique_scans_n, 0) DESC
        LIMIT {MAX_CANDIDATES}
        """,
        [category, code, min_health, *params],
    ).fetchdf()


def _candidates_by_ingredients(
    ingredient_tags: list[str], code: str, min_health: float, where: str, params: list
) -> pd.DataFrame:
    """Fallback for products with no category: nearest by ingredient overlap."""
    if not ingredient_tags:
        return pd.DataFrame()
    return catalog.connect().execute(
        f"""
        SELECT {catalog.PRODUCT_COLUMNS},
               len(list_intersect(ingredients_tags, ?::VARCHAR[])) AS overlap
        FROM catalog
        WHERE list_has_any(COALESCE(ingredients_tags, []::VARCHAR[]), ?::VARCHAR[])
          AND code <> ?
          AND health_score IS NOT NULL
          AND health_score > ?
          AND {where}
        ORDER BY overlap DESC, COALESCE(unique_scans_n, 0) DESC
        LIMIT {MAX_CANDIDATES}
        """,
        [ingredient_tags, ingredient_tags, code, min_health, *params],
    ).fetchdf()


def recommend(
    product: dict, profile: UserProfile, top_n: int = 8
) -> tuple[list[Recommendation], dict]:
    """Return ranked healthier alternatives plus a note on how they were found.

    The second element describes the search (which category was used, how many
    candidates survived filtering) so the UI can be honest when results are
    thin rather than silently showing three items.
    """
    source_health = product.get("health_score")
    if source_health is None or pd.isna(source_health):
        return [], {"reason": "unscored", "message": "This product has no health score, so we cannot compare it."}

    source_health = float(source_health)
    where, params = filters.sql_exclusions(profile)

    category = choose_category(product)
    if category:
        frame = _candidates_by_category(
            category, product["code"], source_health, where, params
        )
        basis = {"mode": "category", "category": category}
    else:
        frame = _candidates_by_ingredients(
            sorted(_tag_set(product.get("ingredients_tags"))),
            product["code"], source_health, where, params,
        )
        basis = {"mode": "ingredients", "category": None}

    basis["pool"] = len(frame)
    if frame.empty:
        basis["message"] = (
            "No healthier alternative passed your allergen and diet filters."
        )
        return [], basis

    ranked = _rank(product, frame, source_health, profile, top_n)
    basis["returned"] = len(ranked)
    return ranked, basis


def _rank(
    product: dict,
    frame: pd.DataFrame,
    source_health: float,
    profile: UserProfile,
    top_n: int,
) -> list[Recommendation]:
    stats = catalog.macro_stats()

    source_macros = similarity.macro_vector(product, stats)
    candidate_macros = similarity.macro_matrix(frame, stats)
    macro_sim = similarity.macro_similarity(source_macros, candidate_macros)

    source_ingredients = _tag_set(product.get("ingredients_tags"))
    ingredient_sim = similarity.jaccard(
        source_ingredients, [_tag_set(t) for t in frame["ingredients_tags"]]
    )

    health = frame["health_score"].astype(float).to_numpy()
    gain = health - source_health
    # Normalise gain against the best available so weights stay comparable.
    gain_norm = gain / gain.max() if gain.max() > 0 else np.zeros_like(gain)

    scans = frame["unique_scans_n"].fillna(0).astype(float).to_numpy()
    popularity = np.log1p(scans)
    popularity = popularity / popularity.max() if popularity.max() > 0 else popularity

    total = (
        W_HEALTH_GAIN * gain_norm
        + W_MACRO * macro_sim
        + W_INGREDIENT * ingredient_sim
        + W_POPULARITY * popularity
    )

    order = np.argsort(-total)[: top_n * 3]
    results: list[Recommendation] = []
    seen_names: set[str] = set()

    for i in order:
        row = frame.iloc[int(i)].to_dict()
        # OFF holds many near-identical listings of the same item; collapsing on
        # name keeps the results a real choice rather than one product repeated.
        key = (str(row.get("product_name") or "").strip().lower(), str(row.get("brands") or "").lower())
        if key in seen_names:
            continue
        seen_names.add(key)

        verdict = filters.evaluate(row, profile)
        if not verdict.passed:  # belt and braces; SQL should have excluded these
            continue

        results.append(
            Recommendation(
                product=row,
                health_gain=float(gain[i]),
                macro_similarity=float(macro_sim[i]),
                ingredient_similarity=float(ingredient_sim[i]),
                score=float(total[i]),
                shared_macros=similarity.shared_macros(product, row),
                warnings=verdict.warnings,
            )
        )
        if len(results) >= top_n:
            break

    return results
