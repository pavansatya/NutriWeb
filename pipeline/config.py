"""Shared paths and constants for the NutriWeb data pipeline.

The pipeline runs offline on a workstation. It reads the full Open Food Facts
parquet (~7.8 GB) and emits a compact DuckDB catalog that the Streamlit app on
Hugging Face Spaces downloads at startup.
"""

from pathlib import Path

# Upstream source ---------------------------------------------------------
SOURCE_REPO = "openfoodfacts/product-database"
SOURCE_FILE = "food.parquet"

# Local artifacts ---------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
CATALOG_PATH = DATA_DIR / "nutriweb-us.duckdb"

# Scope -------------------------------------------------------------------
# US + English focus. OFF tags countries canonically, so this is an exact match
# rather than a string search.
COUNTRY_TAG = "en:united-states"

# Nutriments we pivot out of the long-format `nutriments` list<struct>.
# Keys are OFF's own nutrient names; values are the column names we emit.
NUTRIENT_MAP = {
    "energy-kcal": "energy_kcal_100g",
    # Nutri-Score works in kJ; we keep kcal too because that is what US labels show.
    "energy-kj": "energy_kj_100g",
    "fat": "fat_100g",
    "saturated-fat": "saturated_fat_100g",
    "carbohydrates": "carbohydrates_100g",
    "sugars": "sugars_100g",
    "fiber": "fiber_100g",
    "proteins": "proteins_100g",
    "salt": "salt_100g",
    "sodium": "sodium_100g",
    # Required by the Nutri-Score algorithm's positive-points side. The 2023
    # algorithm uses the "legumes" variant; the older "nuts" field is kept as a
    # fallback because some records carry only that one.
    "fruits-vegetables-legumes-estimate-from-ingredients": "fruits_veg_legumes_100g",
    "fruits-vegetables-nuts-estimate-from-ingredients": "fruits_veg_nuts_100g",
}

# US labels report kcal; Nutri-Score needs kJ. Only ~7% of US records carry an
# explicit energy-kj, so we derive it from kcal with the Codex conversion factor.
KJ_PER_KCAL = 4.184

# Salt and sodium are interconvertible; OFF uses this factor internally.
SALT_PER_SODIUM = 2.5

# The macro vector used for similarity ranking, in a fixed order.
# Uses salt_derived rather than salt_100g so products that report only sodium
# still contribute a salt value instead of silently sitting at the mean.
MACRO_COLUMNS = [
    "energy_kcal_100g",
    "fat_100g",
    "saturated_fat_100g",
    "carbohydrates_100g",
    "sugars_100g",
    "fiber_100g",
    "proteins_100g",
    "salt_derived",
]

# Data-quality errors that make a record unusable for recommendation.
# OFF publishes many quality tags; these are the ones that indicate the
# nutrition facts themselves are wrong, not merely incomplete.
DISQUALIFYING_QUALITY_ERRORS = [
    "en:nutrition-value-total-over-105",
    "en:nutrition-value-negative-energy",
    "en:nutrition-value-negative-fat",
    "en:nutrition-value-negative-carbohydrates",
    "en:nutrition-value-negative-proteins",
    "en:nutrition-value-negative-sugars",
    "en:nutrition-value-negative-salt",
    "en:energy-value-in-kcal-does-not-match-value-computed-from-other-nutrients",
]
