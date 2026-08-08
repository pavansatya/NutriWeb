"""Read access to the curated DuckDB catalog.

The catalog is built offline by `pipeline/` and downloaded from the Hugging
Face Hub at app startup. Everything here is read-only and query-time.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CATALOG = REPO_ROOT / "data" / "nutriweb-us.duckdb"

# Set to a HF dataset repo id to fetch the catalog at startup instead of
# expecting it on local disk (this is how the Space runs).
CATALOG_REPO = os.environ.get("NUTRIWEB_CATALOG_REPO", "")
CATALOG_FILENAME = "nutriweb-us.duckdb"

# Columns the UI needs. Selecting explicitly keeps result frames small --
# `catalog` carries the full tag arrays, which are heavy to materialise.
PRODUCT_COLUMNS = """
    code, product_name, generic_name, brands, quantity, serving_size,
    image_url, ingredients_text, primary_category, categories_tags,
    ingredients_tags, allergens_tags, traces_tags, additives_tags,
    labels_tags, ingredients_analysis_tags, nutrient_levels_tags,
    energy_kcal_100g, energy_kj_derived, fat_100g, saturated_fat_100g,
    carbohydrates_100g, sugars_100g, fiber_100g, proteins_100g,
    salt_derived, sodium_100g, fruits_veg_derived,
    nova_group, environmental_score_grade,
    nutriscore_grade, nutriscore_grade_off, nutriscore_grade_computed,
    nutriscore_score_computed, nutriscore_source,
    health_score, health_confidence, additive_penalty, n_flagged_additives,
    is_beverage, unique_scans_n
"""


def catalog_path() -> Path:
    """Local path to the catalog, downloading it from the Hub if configured."""
    if CATALOG_REPO:
        from huggingface_hub import hf_hub_download

        return Path(
            hf_hub_download(
                repo_id=CATALOG_REPO, filename=CATALOG_FILENAME, repo_type="dataset"
            )
        )
    return DEFAULT_CATALOG


@lru_cache(maxsize=1)
def connect() -> duckdb.DuckDBPyConnection:
    """Open the catalog read-only. Cached so we hold a single connection."""
    path = catalog_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Catalog not found at {path}. Build it with:\n"
            "  python pipeline/01_download.py\n"
            "  python pipeline/02_curate.py\n"
            "  python pipeline/03_score.py"
        )
    con = duckdb.connect(str(path), read_only=True)
    con.execute("LOAD fts")
    return con


def get_product(code: str) -> dict | None:
    """Fetch one product by barcode, tolerating leading-zero variants.

    OFF stores EAN-13, but a scanner or a user may supply the UPC-A form
    without the leading zero, so we try both.
    """
    code = str(code).strip()
    con = connect()
    row = con.execute(
        f"SELECT {PRODUCT_COLUMNS} FROM catalog WHERE code = ?", [code]
    ).fetchdf()
    if row.empty and code.isdigit():
        variants = [code.lstrip("0"), code.zfill(13), code.zfill(12)]
        row = con.execute(
            f"SELECT {PRODUCT_COLUMNS} FROM catalog WHERE code IN "
            f"({','.join('?' * len(variants))}) LIMIT 1",
            variants,
        ).fetchdf()
    return None if row.empty else row.iloc[0].to_dict()


def search(query: str, limit: int = 30) -> list[dict]:
    """Full-text search over product name and brand.

    Uses the BM25 index built in the pipeline. The app this replaces scanned
    every row with `str.contains`, which does not rank and cannot use an index.
    Results are biased toward products we can actually score and toward
    popular items, so the first page is useful rather than merely matching.
    """
    query = (query or "").strip()
    if not query:
        return []

    con = connect()
    # A bare digit string is a barcode, not a search term.
    if query.isdigit() and len(query) >= 8:
        product = get_product(query)
        return [product] if product else []

    df = con.execute(
        f"""
        WITH scored AS (
            SELECT code, fts_main_products.match_bm25(code, ?) AS relevance
            FROM products
        )
        SELECT {PRODUCT_COLUMNS}, relevance
        FROM scored JOIN catalog USING (code)
        WHERE relevance IS NOT NULL
        ORDER BY
            relevance * (CASE WHEN health_score IS NOT NULL THEN 1.0 ELSE 0.4 END)
                * (1 + ln(1 + COALESCE(unique_scans_n, 0)) / 10) DESC
        LIMIT ?
        """,
        [query, limit],
    ).fetchdf()
    return df.to_dict("records")


@lru_cache(maxsize=1)
def macro_stats() -> dict[str, tuple[float, float]]:
    """Per-nutrient (mean, std) used to z-score the macro vector."""
    from pipeline.config import MACRO_COLUMNS

    row = connect().execute("SELECT * FROM macro_stats").fetchdf().iloc[0]
    return {
        col: (float(row[f"{col}_mean"]), float(row[f"{col}_std"]) or 1.0)
        for col in MACRO_COLUMNS
    }


def category_sizes(tags: list[str]) -> dict[str, int]:
    """How many scored products sit under each of these category tags."""
    if not tags:
        return {}
    placeholders = ",".join("?" * len(tags))
    rows = connect().execute(
        f"SELECT tag, n FROM category_sizes WHERE tag IN ({placeholders})", list(tags)
    ).fetchall()
    return dict(rows)


def stats() -> dict:
    """Headline catalog numbers, shown on the Insights page."""
    return connect().execute("""
        SELECT
            count(*) AS products,
            count(health_score) AS scored,
            count(*) FILTER (WHERE nutriscore_source = 'off') AS graded_by_off,
            count(*) FILTER (WHERE nutriscore_source = 'nutriweb') AS graded_by_nutriweb,
            count(*) FILTER (WHERE image_url IS NOT NULL) AS with_image,
            count(DISTINCT primary_category) AS categories
        FROM catalog
    """).fetchdf().iloc[0].to_dict()
