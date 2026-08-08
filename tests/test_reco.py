"""Recommendation engine tests, run against the real catalog.

These are integration tests: they need `data/nutriweb-us.duckdb`, and they skip
cleanly if it has not been built yet. They assert the properties that the app
promises rather than specific products, since the catalog is refreshed from a
live upstream dataset.
"""

from __future__ import annotations

import pytest

from nutriweb.data import catalog
from nutriweb.profile.model import UserProfile
from nutriweb.reco import engine, similarity
from nutriweb.util import tag_set

pytestmark = pytest.mark.skipif(
    not catalog.DEFAULT_CATALOG.exists(),
    reason="catalog not built; run pipeline/01..03 first",
)


def _popular_in(category: str) -> dict:
    frame = catalog.connect().execute(
        f"""SELECT {catalog.PRODUCT_COLUMNS} FROM catalog
            WHERE list_contains(categories_tags, ?) AND health_score IS NOT NULL
            ORDER BY COALESCE(unique_scans_n, 0) DESC LIMIT 1""",
        [category],
    ).fetchdf()
    if frame.empty:
        pytest.skip(f"no scored products in {category}")
    return frame.iloc[0].to_dict()


@pytest.fixture(scope="module")
def soda() -> dict:
    return _popular_in("en:sodas")


class TestHealthierGuarantee:
    def test_every_result_is_strictly_healthier(self, soda):
        recommendations, _ = engine.recommend(soda, UserProfile(), top_n=8)
        assert recommendations
        for rec in recommendations:
            assert rec.health_gain > 0
            assert rec.product["health_score"] > soda["health_score"]

    def test_source_product_is_never_recommended(self, soda):
        recommendations, _ = engine.recommend(soda, UserProfile(), top_n=8)
        assert all(r.product["code"] != soda["code"] for r in recommendations)


class TestCategoryConstraint:
    def test_soda_does_not_return_confectionery(self, soda):
        """The failure this rebuild set out to fix.

        The previous engine searched embeddings across the whole catalog with no
        category constraint, so a drink could return a candy bar.
        """
        recommendations, basis = engine.recommend(soda, UserProfile(), top_n=10)
        assert basis["mode"] == "category"
        for rec in recommendations:
            tags = tag_set(rec.product["categories_tags"])
            assert not (tags & {"en:confectioneries", "en:chocolates", "en:biscuits"})

    def test_candidates_share_the_chosen_category(self, soda):
        recommendations, basis = engine.recommend(soda, UserProfile(), top_n=6)
        for rec in recommendations:
            assert basis["category"] in tag_set(rec.product["categories_tags"])

    def test_chosen_category_is_specific_not_generic(self, soda):
        """Widening must stop at the most specific viable pool."""
        chosen = engine.choose_category(soda)
        sizes = catalog.category_sizes([chosen])
        assert sizes[chosen] >= engine.MIN_POOL
        # A soda should not fall back to a catch-all like en:beverages.
        assert chosen not in ("en:groceries", "en:snacks")


class TestProfileIsRespected:
    def test_allergen_never_appears_in_results(self):
        product = _popular_in("en:biscuits")
        profile = UserProfile(allergens=["en:gluten", "en:milk"])
        recommendations, _ = engine.recommend(product, profile, top_n=10)
        for rec in recommendations:
            assert not (tag_set(rec.product["allergens_tags"]) & set(profile.allergens))

    def test_vegan_profile_excludes_non_vegan(self):
        product = _popular_in("en:biscuits")
        recommendations, _ = engine.recommend(
            product, UserProfile(diets=["Vegan"]), top_n=10
        )
        for rec in recommendations:
            assert "en:non-vegan" not in tag_set(rec.product["ingredients_analysis_tags"])

    def test_filters_shrink_rather_than_grow_the_pool(self, soda):
        _, wide = engine.recommend(soda, UserProfile(), top_n=5)
        _, narrow = engine.recommend(
            soda, UserProfile(allergens=["en:milk"], diets=["Vegan"]), top_n=5
        )
        assert narrow["pool"] <= wide["pool"]


class TestRanking:
    def test_results_are_ordered_by_score(self, soda):
        recommendations, _ = engine.recommend(soda, UserProfile(), top_n=8)
        scores = [r.score for r in recommendations]
        assert scores == sorted(scores, reverse=True)

    def test_no_duplicate_products(self, soda):
        recommendations, _ = engine.recommend(soda, UserProfile(), top_n=10)
        codes = [r.product["code"] for r in recommendations]
        assert len(codes) == len(set(codes))

    def test_every_result_can_explain_itself(self, soda):
        recommendations, _ = engine.recommend(soda, UserProfile(), top_n=5)
        for rec in recommendations:
            assert rec.why and "health points" in rec.why

    def test_unscored_product_returns_a_reason(self):
        frame = catalog.connect().execute(
            f"SELECT {catalog.PRODUCT_COLUMNS} FROM catalog WHERE health_score IS NULL LIMIT 1"
        ).fetchdf()
        if frame.empty:
            pytest.skip("every product is scored")
        recommendations, basis = engine.recommend(frame.iloc[0].to_dict(), UserProfile())
        assert recommendations == []
        assert "message" in basis


class TestSimilarity:
    def test_jaccard_bounds(self):
        a = {"en:water", "en:sugar"}
        assert similarity.jaccard(a, [a])[0] == pytest.approx(1.0)
        assert similarity.jaccard(a, [{"en:salt"}])[0] == 0.0

    def test_macro_similarity_prefers_closer_products(self):
        stats = {c: (0.0, 1.0) for c in
                 __import__("pipeline.config", fromlist=["x"]).MACRO_COLUMNS}
        source = similarity.macro_vector({"proteins_100g": 10.0}, stats)
        near = similarity.macro_vector({"proteins_100g": 11.0}, stats)
        far = similarity.macro_vector({"proteins_100g": 60.0}, stats)
        import numpy as np

        sims = similarity.macro_similarity(source, np.vstack([near, far]))
        assert sims[0] > sims[1]
