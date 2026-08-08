"""Step 4 — measure what is actually in the catalog.

The point of this script is to replace assumptions with numbers. The app makes
claims ("healthier alternative", "safe for your allergies") that are only as
good as the coverage underneath them, so coverage is measured rather than
hoped for. Run it after any pipeline change and read the output before
trusting a recommendation.

Usage:
    python pipeline/04_audit.py
"""

from __future__ import annotations

import os
import sys

import duckdb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.config import CATALOG_PATH  # noqa: E402


def rule(title: str) -> None:
    print(f"\n{'=' * 66}\n{title}\n{'=' * 66}")


def pct(part: int, whole: int) -> str:
    return f"{part:>9,}  ({part / whole * 100:5.1f}%)" if whole else f"{part:>9,}"


def main() -> None:
    if not CATALOG_PATH.exists():
        raise SystemExit(f"{CATALOG_PATH} missing. Run steps 01-03 first.")

    con = duckdb.connect(str(CATALOG_PATH), read_only=True)
    total = con.execute("SELECT count(*) FROM catalog").fetchone()[0]

    rule("CATALOG")
    print(f"{'products':<42}{total:>9,}")
    size = CATALOG_PATH.stat().st_size / 1024**2
    print(f"{'catalog size':<42}{size:>8.0f} MB")

    rule("FIELD COVERAGE")
    fields = {
        "product name": "product_name IS NOT NULL",
        "brand": "brands IS NOT NULL",
        "front image": "image_url IS NOT NULL",
        "ingredients text": "ingredients_text IS NOT NULL",
        "ingredient tags (used for similarity)": "len(COALESCE(ingredients_tags,[]::VARCHAR[])) > 0",
        "category (used for candidate generation)": "primary_category IS NOT NULL",
        "allergen tags": "len(COALESCE(allergens_tags,[]::VARCHAR[])) > 0",
        "energy": "energy_kcal_100g IS NOT NULL",
        "sugars": "sugars_100g IS NOT NULL",
        "saturated fat": "saturated_fat_100g IS NOT NULL",
        "salt or sodium": "salt_derived IS NOT NULL",
        "protein": "proteins_100g IS NOT NULL",
        "fibre": "fiber_100g IS NOT NULL",
        "fruit/veg estimate": "fruits_veg_derived IS NOT NULL",
        "NOVA group": "nova_group IS NOT NULL",
        "Eco-Score": "environmental_score_grade IS NOT NULL",
    }
    for label, condition in fields.items():
        n = con.execute(f"SELECT count(*) FROM catalog WHERE {condition}").fetchone()[0]
        print(f"{label:<42}{pct(n, total)}")

    rule("SCORING — the reason this pipeline exists")
    off = con.execute(
        "SELECT count(*) FROM catalog WHERE nutriscore_source = 'off'"
    ).fetchone()[0]
    ours = con.execute(
        "SELECT count(*) FROM catalog WHERE nutriscore_source = 'nutriweb'"
    ).fetchone()[0]
    health = con.execute("SELECT count(health_score) FROM catalog").fetchone()[0]

    print(f"{'Nutri-Score published by Open Food Facts':<42}{pct(off, total)}")
    print(f"{'Nutri-Score computed by NutriWeb':<42}{pct(ours, total)}")
    print(f"{'total graded':<42}{pct(off + ours, total)}")
    print(f"{'with a health score':<42}{pct(health, total)}")
    if off:
        print(f"\n  Computing grades ourselves increased scored coverage {(off + ours) / off:.2f}x.")

    rule("VALIDATION — computed grades vs Open Food Facts' own")
    print(
        con.execute("""
        WITH v AS (
            SELECT nutriscore_grade_off AS off, nutriscore_grade_computed AS ours
            FROM catalog
            WHERE nutriscore_grade_off NOT IN ('unknown','not-applicable')
              AND nutriscore_grade_off IS NOT NULL
              AND nutriscore_grade_computed IS NOT NULL
        )
        SELECT count(*) AS compared,
               round(100.0*count(*) FILTER (WHERE off=ours)/count(*), 2) AS exact_pct,
               round(100.0*count(*) FILTER (WHERE abs(ascii(off)-ascii(ours))<=1)/count(*), 2)
                   AS within_one_pct
        FROM v
    """).fetchdf().T.to_string(header=False)
    )

    rule("CONFIDENCE — how much to trust each health score")
    print(
        con.execute("""
        SELECT COALESCE(health_confidence,'unscored') AS confidence, count(*) AS n
        FROM catalog GROUP BY 1 ORDER BY n DESC
    """).fetchdf().to_string(index=False)
    )
    print(
        "\n  'low' means the Nutri-Score was computed for a product with no category,\n"
        "  so the general-food thresholds were assumed. Surfaced in the UI."
    )

    rule("RECOMMENDABILITY — can we actually serve a swap?")
    print(
        con.execute("""
        SELECT
            count(*) FILTER (WHERE health_score IS NOT NULL
                             AND primary_category IS NOT NULL) AS category_path,
            count(*) FILTER (WHERE health_score IS NOT NULL
                             AND primary_category IS NULL
                             AND len(COALESCE(ingredients_tags,[]::VARCHAR[]))>0)
                AS ingredient_fallback_path,
            count(*) FILTER (WHERE health_score IS NULL) AS cannot_recommend_from
        FROM catalog
    """).fetchdf().T.to_string(header=False)
    )

    rule("TOP CATEGORIES")
    print(
        con.execute("""
        SELECT replace(split_part(primary_category,':',2),'-',' ') AS category,
               count(*) AS products, round(avg(health_score),1) AS avg_health
        FROM catalog WHERE primary_category IS NOT NULL AND health_score IS NOT NULL
        GROUP BY 1 ORDER BY products DESC LIMIT 12
    """).fetchdf().to_string(index=False)
    )

    con.close()


if __name__ == "__main__":
    main()
