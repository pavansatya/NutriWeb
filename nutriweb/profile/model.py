"""The user profile that drives filtering and ranking."""

from __future__ import annotations

from dataclasses import dataclass, field

# Allergen options, mapped to OFF's canonical allergen tags. Using OFF's tags
# means we match on the curated `allergens_tags`/`traces_tags` arrays rather
# than guessing from ingredient text with regexes.
ALLERGEN_CHOICES: dict[str, str] = {
    "Gluten": "en:gluten",
    "Milk / Dairy": "en:milk",
    "Eggs": "en:eggs",
    "Peanuts": "en:peanuts",
    "Tree nuts": "en:nuts",
    "Soybeans": "en:soybeans",
    "Fish": "en:fish",
    "Crustaceans": "en:crustaceans",
    "Molluscs": "en:molluscs",
    "Sesame seeds": "en:sesame-seeds",
    "Celery": "en:celery",
    "Mustard": "en:mustard",
    "Sulphites": "en:sulphur-dioxide-and-sulphites",
    "Lupin": "en:lupin",
}

DIET_CHOICES = ["Vegetarian", "Vegan", "Palm-oil free"]

# Per-100g ceilings for health conditions.
#
# The app this replaces tested `sodium_100g > 5.0` -- five *grams* of sodium per
# 100 g, a level essentially no food reaches, so the rule never fired. These
# thresholds come from the FDA "high in" labelling guidance: a food is high in a
# nutrient at 20% of the Daily Value per serving. Expressed per 100 g against
# DVs of 2300 mg sodium and 20 g saturated fat.
SODIUM_CEILING_G_100G = 0.46  # 20% of the 2300 mg DV
SALT_CEILING_G_100G = SODIUM_CEILING_G_100G * 2.5
SATURATED_FAT_CEILING_G_100G = 4.0  # 20% of the 20 g DV


@dataclass
class UserProfile:
    """Everything the engine needs to know about a person.

    Allergens are stored as OFF tags, not display labels, so the filters are
    exact set operations.
    """

    user_id: str = ""
    age: int = 30
    gender: str = "Prefer not to say"
    allergens: list[str] = field(default_factory=list)  # OFF tags, e.g. 'en:peanuts'
    diets: list[str] = field(default_factory=list)  # from DIET_CHOICES
    high_blood_pressure: bool = False
    high_cholesterol: bool = False
    avoid_flagged_additives: bool = False

    @property
    def wants_vegan(self) -> bool:
        return "Vegan" in self.diets

    @property
    def wants_vegetarian(self) -> bool:
        # Vegan is stricter than vegetarian and implies it.
        return "Vegetarian" in self.diets or self.wants_vegan

    @property
    def wants_palm_oil_free(self) -> bool:
        return "Palm-oil free" in self.diets

    def to_dict(self) -> dict:
        return {
            "age": self.age,
            "gender": self.gender,
            "allergens": self.allergens,
            "diets": self.diets,
            "high_blood_pressure": self.high_blood_pressure,
            "high_cholesterol": self.high_cholesterol,
            "avoid_flagged_additives": self.avoid_flagged_additives,
        }

    @classmethod
    def from_dict(cls, data: dict) -> UserProfile:
        return cls(
            user_id=str(data.get("_id", data.get("user_id", ""))),
            age=int(data.get("age", 30)),
            gender=data.get("gender", "Prefer not to say"),
            allergens=list(data.get("allergens", [])),
            diets=list(data.get("diets", [])),
            high_blood_pressure=bool(data.get("high_blood_pressure", False)),
            high_cholesterol=bool(data.get("high_cholesterol", False)),
            avoid_flagged_additives=bool(data.get("avoid_flagged_additives", False)),
        )
