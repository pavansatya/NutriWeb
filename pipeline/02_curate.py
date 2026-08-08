"""Step 2 — curate the raw OFF parquet into a compact US catalog.

One DuckDB pass over the 7.2 GB source that:
  * filters to non-obsolete US products with a usable name,
  * collapses the multilingual list<struct{lang,text}> fields to one language,
  * pivots the long-format `nutriments` list into per-100g columns,
  * derives the primary category and the front-image URL,
  * keeps OFF's curated tag arrays for set operations downstream.

DuckDB streams the parquet, so peak memory stays well under the file size.

Usage:
    python pipeline/02_curate.py
"""

from __future__ import annotations

import os
import sys
import time

import duckdb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.config import (  # noqa: E402
    CATALOG_PATH,
    COUNTRY_TAG,
    DATA_DIR,
    DISQUALIFYING_QUALITY_ERRORS,
    KJ_PER_KCAL,
    NUTRIENT_MAP,
    SALT_PER_SODIUM,
    SOURCE_FILE,
    SOURCE_REPO,
)


def source_path() -> str:
    """Locate the downloaded parquet in the HF cache."""
    from huggingface_hub import hf_hub_download

    return hf_hub_download(
        repo_id=SOURCE_REPO, filename=SOURCE_FILE, repo_type="dataset",
        local_files_only=True,
    )


def _pick_lang(column: str) -> str:
    """SQL to collapse a list<struct{lang,text}> to a single string.

    Prefers English, then OFF's 'main' pseudo-language, then whatever is first.
    """
    def first_where(cond: str) -> str:
        return (
            f"list_extract(list_transform(list_filter({column}, x -> {cond}), "
            f"x -> x.text), 1)"
        )

    en = first_where("x.lang = 'en'")
    main = first_where("x.lang = 'main'")
    any_lang = f"list_extract(list_transform({column}, x -> x.text), 1)"
    return f"COALESCE({en}, {main}, {any_lang})"


def _pivot_nutrient(off_name: str, alias: str) -> str:
    """SQL to pull one nutrient's per-100g value out of the `nutriments` list."""
    return (
        "list_extract(list_transform("
        f"list_filter(nutriments, x -> x.name = '{off_name}'), x -> x.\"100g\"), 1"
        f") AS {alias}"
    )


def build_sql(parquet: str) -> str:
    nutrient_cols = ",\n        ".join(
        _pivot_nutrient(off, alias) for off, alias in NUTRIENT_MAP.items()
    )
    bad_quality = ", ".join(f"'{t}'" for t in DISQUALIFYING_QUALITY_ERRORS)

    return f"""
    CREATE OR REPLACE TABLE products AS
    WITH src AS (
        SELECT
            code,
            {_pick_lang('product_name')} AS product_name,
            {_pick_lang('generic_name')} AS generic_name,
            {_pick_lang('ingredients_text')} AS ingredients_text,
            brands,
            quantity,
            serving_size,
            categories_tags,
            -- The last English tag is usually the most specific one. 'en:null'
            -- and 'en:undefined' are data-entry artifacts in the source and
            -- must not be treated as categories.
            list_extract(
                list_filter(
                    categories_tags,
                    x -> starts_with(x, 'en:')
                         AND x NOT IN ('en:null', 'en:undefined')
                ), -1
            ) AS primary_category,
            ingredients_tags,
            allergens_tags,
            traces_tags,
            additives_tags,
            labels_tags,
            ingredients_analysis_tags,
            nutrient_levels_tags,
            additives_n,
            nova_group,
            nutriscore_grade AS nutriscore_grade_off,
            nutriscore_score AS nutriscore_score_off,
            environmental_score_grade,
            environmental_score_score,
            with_non_nutritive_sweeteners,
            unique_scans_n,
            popularity_key,
            completeness,
            last_modified_t,
            {nutrient_cols},
            -- Front image URL. OFF splits barcodes longer than 8 digits into
            -- 3/3/3/rest path segments on its image CDN.
            CASE
                WHEN length(code) > 8
                    THEN regexp_replace(code, '^(...)(...)(...)(.*)$', '\\1/\\2/\\3/\\4')
                ELSE code
            END AS code_path,
            -- Prefer the English front photo; fall back to any front photo
            -- (front_fr, front_es, ...) which lifts image coverage materially.
            COALESCE(
                list_extract(list_filter(images, i -> i.key = 'front_en'), 1),
                list_extract(list_filter(images, i -> starts_with(i.key, 'front')), 1)
            ) AS front_image
        FROM read_parquet('{parquet}')
        WHERE NOT obsolete
          AND list_contains(countries_tags, '{COUNTRY_TAG}')
          AND NOT list_has_any(
                COALESCE(data_quality_errors_tags, []::VARCHAR[]),
                [{bad_quality}]
          )
    )
    SELECT
        * EXCLUDE (code_path, front_image),
        CASE
            WHEN front_image IS NOT NULL AND front_image.rev IS NOT NULL
                THEN 'https://images.openfoodfacts.org/images/products/'
                     || code_path || '/' || front_image.key || '.'
                     || CAST(front_image.rev AS VARCHAR) || '.400.jpg'
        END AS image_url,
        -- Nutri-Score works in kJ but US labels report kcal, so derive it.
        COALESCE(energy_kj_100g, energy_kcal_100g * {KJ_PER_KCAL}) AS energy_kj_derived,
        -- Salt and sodium are interconvertible; fill whichever is missing.
        COALESCE(salt_100g, sodium_100g * {SALT_PER_SODIUM}) AS salt_derived,
        COALESCE(fruits_veg_legumes_100g, fruits_veg_nuts_100g) AS fruits_veg_derived
    FROM src
    WHERE product_name IS NOT NULL
      AND trim(product_name) <> ''
      -- A product needs ingredients, a category, or nutrition facts to be
      -- useful. Records with none of the three are empty barcode stubs --
      -- roughly 209k of the US rows -- and are pure noise in search results.
      AND (len(COALESCE(ingredients_tags, []::VARCHAR[])) > 0
           OR len(COALESCE(categories_tags, []::VARCHAR[])) > 0
           OR energy_kcal_100g IS NOT NULL
           OR proteins_100g IS NOT NULL)
    -- The source carries a handful of genuinely duplicated barcodes; keep the
    -- most recently edited record so the choice is deterministic.
    QUALIFY row_number() OVER (
        PARTITION BY code ORDER BY last_modified_t DESC, completeness DESC
    ) = 1
    """


def main() -> None:
    parquet = source_path()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if CATALOG_PATH.exists():
        CATALOG_PATH.unlink()

    con = duckdb.connect(str(CATALOG_PATH))
    con.execute("SET preserve_insertion_order = false")
    con.execute("SET memory_limit = '6GB'")

    print(f"Curating {parquet}\n     -> {CATALOG_PATH}")
    start = time.time()
    con.execute(build_sql(parquet))
    elapsed = time.time() - start

    n = con.execute("SELECT count(*) FROM products").fetchone()[0]
    print(f"products: {n:,} rows in {elapsed:.0f}s")

    print("Building indexes...")
    con.execute("CREATE UNIQUE INDEX idx_products_code ON products(code)")
    con.execute("CREATE INDEX idx_products_category ON products(primary_category)")

    # Full-text search over name + brand, replacing the old str.contains scan.
    con.execute("INSTALL fts; LOAD fts;")
    con.execute(
        "PRAGMA create_fts_index('products', 'code', 'product_name', 'brands', "
        "overwrite=1)"
    )

    con.close()
    size_mb = CATALOG_PATH.stat().st_size / 1024**2
    print(f"Done. Catalog is {size_mb:.0f} MB")


if __name__ == "__main__":
    main()
