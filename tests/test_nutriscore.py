"""Nutri-Score 2023 unit tests.

The full-catalog validation lives in `pipeline/03_score.py`, which compares our
grades against Open Food Facts' own on ~317k products. These tests pin the
specific behaviours that validation could not isolate: variant selection, the
protein-capping rules, and the boundaries between grades.
"""

from __future__ import annotations

import pytest

from nutriweb.scoring import nutriscore
from nutriweb.scoring.nutriscore import CategoryFlags

GENERAL = CategoryFlags()
BEVERAGE = CategoryFlags(is_beverage=True)


def score(**kwargs):
    defaults = dict(
        energy_kj=0, sugars=0, saturated_fat=0, salt=0,
        fiber=0, proteins=0, fruits_vegetables_legumes=0,
    )
    return nutriscore.compute(**{**defaults, **kwargs})


class TestPoints:
    def test_thresholds_are_strictly_greater(self):
        """A value exactly on a threshold does not earn the point."""
        assert score(sugars=3.4).detail["sugars"] == 0
        assert score(sugars=3.41).detail["sugars"] == 1

    def test_energy_points_ramp(self):
        assert score(energy_kj=335).detail["energy"] == 0
        assert score(energy_kj=336).detail["energy"] == 1
        assert score(energy_kj=99999).detail["energy"] == 10  # capped at table length

    def test_salt_scale_runs_to_twenty(self):
        assert score(salt=4.1).detail["salt"] == 20

    def test_beverages_use_their_own_tables(self):
        """2 g of sugar is nothing in a solid food but real in a drink."""
        assert score(sugars=2.0, flags=GENERAL).detail["sugars"] == 0
        assert score(sugars=2.0, flags=BEVERAGE).detail["sugars"] == 1

    def test_fruit_points_reward_above_eighty_percent(self):
        """The threshold table repeats 80 so >80% earns the full five points."""
        assert score(fruits_vegetables_legumes=80).detail["fruits_vegetables_legumes"] == 2
        assert score(fruits_vegetables_legumes=81).detail["fruits_vegetables_legumes"] == 5


class TestProteinRules:
    def test_protein_ignored_when_heavily_penalised(self):
        """Above 11 negative points protein stops counting for general foods."""
        result = score(energy_kj=3400, sugars=55, saturated_fat=11, salt=5, proteins=20)
        assert result.negative_points >= 11
        assert not result.counted_proteins

    def test_cheese_always_counts_protein(self):
        flags = CategoryFlags(is_cheese=True)
        result = nutriscore.compute(
            energy_kj=3400, sugars=55, saturated_fat=11, salt=5,
            fiber=0, proteins=20, fruits_vegetables_legumes=0, flags=flags,
        )
        assert result.counted_proteins

    def test_red_meat_protein_capped_at_two(self):
        lean = dict(energy_kj=500, sugars=0, saturated_fat=1, salt=0.1,
                    fiber=0, proteins=25, fruits_vegetables_legumes=0)
        assert nutriscore.compute(**lean, flags=GENERAL).detail["proteins"] == 7
        red = nutriscore.compute(**lean, flags=CategoryFlags(is_red_meat_product=True))
        assert red.detail["proteins"] == 2


class TestFatsVariant:
    def test_uses_saturates_ratio_not_absolute(self):
        """Olive oil is almost all fat but a low share of it is saturated."""
        flags = CategoryFlags(is_fat_oil_nuts_seeds=True)
        result = nutriscore.compute(
            energy_kj=3700, sugars=0, saturated_fat=14, salt=0,
            fiber=0, proteins=0, fruits_vegetables_legumes=0, fat=100, flags=flags,
        )
        # 14% saturates ratio -> 1 point, versus 10 on the absolute scale.
        assert result.detail["saturated_fat"] == 1

    def test_ratio_boundary_is_inclusive(self):
        """The saturated-fat-ratio table is the one that uses >=."""
        flags = CategoryFlags(is_fat_oil_nuts_seeds=True)
        result = nutriscore.compute(
            energy_kj=0, sugars=0, saturated_fat=10, salt=0, fiber=0, proteins=0,
            fruits_vegetables_legumes=0, fat=100, flags=flags,
        )
        assert result.detail["saturated_fat"] == 1  # exactly 10% still scores


class TestGrades:
    @pytest.mark.parametrize(
        "value,expected", [(-5, "a"), (0, "a"), (1, "b"), (2, "b"), (3, "c"),
                          (10, "c"), (11, "d"), (18, "d"), (19, "e")],
    )
    def test_general_food_cutoffs(self, value, expected):
        assert nutriscore.grade_for(value, GENERAL) == expected

    @pytest.mark.parametrize(
        "value,expected", [(2, "b"), (6, "c"), (9, "d"), (10, "e")],
    )
    def test_beverage_cutoffs(self, value, expected):
        assert nutriscore.grade_for(value, BEVERAGE) == expected

    def test_only_water_gets_an_a_among_beverages(self):
        water = CategoryFlags(is_beverage=True, is_water=True)
        assert nutriscore.grade_for(99, water) == "a"
        assert nutriscore.grade_for(-99, BEVERAGE) == "b"


class TestSweetenerPenalty:
    def test_diet_drink_penalised_four_points(self):
        base = dict(energy_kj=0, sugars=0, saturated_fat=0, salt=0,
                    fiber=0, proteins=0, fruits_vegetables_legumes=0, flags=BEVERAGE)
        plain = nutriscore.compute(**base, has_non_nutritive_sweeteners=False)
        diet = nutriscore.compute(**base, has_non_nutritive_sweeteners=True)
        assert diet.score - plain.score == 4

    def test_penalty_does_not_apply_to_solid_food(self):
        base = dict(energy_kj=0, sugars=0, saturated_fat=0, salt=0,
                    fiber=0, proteins=0, fruits_vegetables_legumes=0, flags=GENERAL)
        assert (
            nutriscore.compute(**base, has_non_nutritive_sweeteners=True).score
            == nutriscore.compute(**base, has_non_nutritive_sweeteners=False).score
        )


class TestDataSufficiency:
    def test_returns_none_without_the_core_nutrients(self):
        """A record with no nutrition must be unscored, never a clean 'A'.

        Upstream treats missing nutrients as zero points, which would grade an
        empty record as A. We refuse instead.
        """
        assert nutriscore.compute(
            energy_kj=None, sugars=None, saturated_fat=None, salt=None,
            fiber=None, proteins=None, fruits_vegetables_legumes=None,
        ) is None

    def test_optional_nutrients_may_be_missing(self):
        result = score(energy_kj=500, sugars=5, saturated_fat=2, salt=0.5,
                       proteins=3, fiber=None, fruits_vegetables_legumes=None)
        assert result is not None


class TestCategoryFlags:
    def test_dairy_drinks_are_beverages_under_2023(self):
        assert nutriscore.category_flags(["en:milks"]).is_beverage

    def test_soups_are_not_beverages(self):
        flags = nutriscore.category_flags(["en:beverages", "en:soups"])
        assert not flags.is_beverage

    def test_flavoured_water_is_not_water(self):
        assert nutriscore.category_flags(["en:spring-waters"]).is_water
        assert not nutriscore.category_flags(
            ["en:spring-waters", "en:flavored-waters"]
        ).is_water

    def test_chestnuts_excluded_from_fats_variant(self):
        assert not nutriscore.category_flags(
            ["en:chestnuts"], frozenset({"en:chestnuts"})
        ).is_fat_oil_nuts_seeds

    def test_salt_and_spices_are_exempt(self):
        assert nutriscore.is_exempt(["en:salts"])
        assert nutriscore.is_exempt(["en:alcoholic-beverages"])
        assert not nutriscore.is_exempt(["en:snacks"])

    def test_iced_tea_is_not_exempt_despite_being_a_tea(self):
        assert not nutriscore.is_exempt(["en:beverages", "en:iced-teas"])
