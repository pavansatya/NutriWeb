"""Safety filter tests.

These encode the rules that must never fail: an allergen must never reach a
recommendation, and a stated diet must be respected.
"""

from __future__ import annotations

from nutriweb.profile.model import UserProfile
from nutriweb.reco import filters


def product(**kwargs) -> dict:
    base = {
        "code": "1", "product_name": "Test", "allergens_tags": [], "traces_tags": [],
        "ingredients_analysis_tags": [], "additives_tags": [],
        "salt_derived": 0.1, "saturated_fat_100g": 1.0,
    }
    return {**base, **kwargs}


class TestAllergens:
    def test_declared_allergen_blocks(self):
        verdict = filters.evaluate(
            product(allergens_tags=["en:peanuts"]),
            UserProfile(allergens=["en:peanuts"]),
        )
        assert not verdict.passed
        assert "peanuts" in verdict.blockers[0].lower()

    def test_traces_warn_but_do_not_block(self):
        """A 'may contain' label is a different risk from an ingredient."""
        verdict = filters.evaluate(
            product(traces_tags=["en:peanuts"]),
            UserProfile(allergens=["en:peanuts"]),
        )
        assert verdict.passed
        assert verdict.warnings

    def test_unrelated_allergen_passes(self):
        verdict = filters.evaluate(
            product(allergens_tags=["en:milk"]), UserProfile(allergens=["en:peanuts"])
        )
        assert verdict.passed

    def test_no_substring_false_positive(self):
        """The old regex matcher flagged 'milk' inside 'milk thistle'.

        Matching on OFF's canonical tags makes that impossible.
        """
        verdict = filters.evaluate(
            product(allergens_tags=["en:milk-thistle"]), UserProfile(allergens=["en:milk"])
        )
        assert verdict.passed


class TestDiet:
    def test_non_vegan_blocked_for_vegan(self):
        verdict = filters.evaluate(
            product(ingredients_analysis_tags=["en:non-vegan"]),
            UserProfile(diets=["Vegan"]),
        )
        assert not verdict.passed

    def test_unconfirmed_vegan_warns_only(self):
        verdict = filters.evaluate(
            product(ingredients_analysis_tags=["en:maybe-vegan"]),
            UserProfile(diets=["Vegan"]),
        )
        assert verdict.passed and verdict.warnings

    def test_vegan_implies_vegetarian(self):
        assert UserProfile(diets=["Vegan"]).wants_vegetarian

    def test_vegetarian_profile_allows_vegetarian_product(self):
        verdict = filters.evaluate(
            product(ingredients_analysis_tags=["en:vegetarian", "en:non-vegan"]),
            UserProfile(diets=["Vegetarian"]),
        )
        assert verdict.passed

    def test_palm_oil_blocked_when_requested(self):
        verdict = filters.evaluate(
            product(ingredients_analysis_tags=["en:palm-oil"]),
            UserProfile(diets=["Palm-oil free"]),
        )
        assert not verdict.passed


class TestHealthConditions:
    def test_high_salt_warns_for_hypertension(self):
        """The replaced code tested sodium > 5 g/100 g, which never fired."""
        verdict = filters.evaluate(
            product(salt_derived=2.0), UserProfile(high_blood_pressure=True)
        )
        assert verdict.warnings and "salt" in verdict.warnings[0].lower()

    def test_normal_salt_is_silent(self):
        verdict = filters.evaluate(
            product(salt_derived=0.2), UserProfile(high_blood_pressure=True)
        )
        assert not verdict.warnings

    def test_saturated_fat_warns_for_cholesterol(self):
        verdict = filters.evaluate(
            product(saturated_fat_100g=12.0), UserProfile(high_cholesterol=True)
        )
        assert verdict.warnings


class TestSqlMirrorsPython:
    def test_empty_profile_produces_no_filter(self):
        where, params = filters.sql_exclusions(UserProfile())
        assert where == "TRUE" and params == []

    def test_allergen_profile_emits_clause(self):
        where, params = filters.sql_exclusions(UserProfile(allergens=["en:peanuts"]))
        assert "allergens_tags" in where
        assert params == [["en:peanuts"]]

    def test_missing_values_are_not_excluded(self):
        """A NULL nutrient must not silently drop a product from the pool."""
        where, _ = filters.sql_exclusions(UserProfile(high_blood_pressure=True))
        assert "salt_derived IS NULL" in where


class TestVerdictSummary:
    def test_summary_reflects_worst_finding(self):
        assert filters.Verdict(False, ["x"], []).summary == "Not suitable for you"
        assert filters.Verdict(True, [], ["x"]).summary == "Check before buying"
        assert filters.Verdict(True, [], []).summary == "Fits your profile"
