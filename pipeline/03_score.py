"""Step 3 — compute Nutri-Score and the NutriWeb health score for every product.

Runs after 02_curate. Reads the catalog in batches, scores each product in
Python (the algorithm is branchy enough that SQL would obscure it), and writes
a `scores` table back into the same DuckDB file.

Also validates our Nutri-Score implementation against OFF's own grades on the
~347k products where OFF published one. That agreement rate is the single most
important correctness signal in the pipeline, so it is printed every run.

Usage:
    python pipeline/03_score.py
"""

from __future__ import annotations

import os
import sys
import time

import duckdb
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nutriweb.scoring import additives as additives_mod  # noqa: E402
from nutriweb.scoring import health_score, nutriscore  # noqa: E402
from pipeline import taxonomy  # noqa: E402
from pipeline.config import CATALOG_PATH  # noqa: E402

BATCH = 100_000

SELECT_COLS = """
    code, categories_tags, additives_tags, nova_group,
    nutriscore_grade_off, nutriscore_score_off,
    energy_kj_derived, sugars_100g, saturated_fat_100g, salt_derived,
    fiber_100g, proteins_100g, fruits_veg_derived, fat_100g,
    with_non_nutritive_sweeteners
"""


def _f(value) -> float | None:
    """Coerce a DuckDB/pandas value to float, mapping NaN and NULL to None."""
    if value is None or pd.isna(value):
        return None
    return float(value)


def _list(value) -> list[str]:
    """Coerce a DuckDB list column to a plain list.

    Missing lists arrive as None, pd.NA, or a NumPy array depending on the
    column, so `is not None` alone is not enough.
    """
    if value is None:
        return []
    if isinstance(value, float) or value is pd.NA:
        return []
    return list(value)


def score_row(row, fat_ids: frozenset[str], red_meat_ids: frozenset[str]) -> dict:
    tags = _list(row.categories_tags)
    additive_tags = _list(row.additives_tags)
    category_known = len(tags) > 0

    flags = nutriscore.category_flags(tags, fat_ids, red_meat_ids)

    # OFF's own boolean is authoritative where present; fall back to reading the
    # additive list, which is what matters for the beverage sweetener penalty.
    sweeteners = row.with_non_nutritive_sweeteners
    if sweeteners is None or pd.isna(sweeteners):
        has_sweetener = additives_mod.has_non_nutritive_sweetener(additive_tags)
    else:
        has_sweetener = int(sweeteners) > 0

    result = None
    if not nutriscore.is_exempt(tags):
        result = nutriscore.compute(
            energy_kj=_f(row.energy_kj_derived),
            sugars=_f(row.sugars_100g),
            saturated_fat=_f(row.saturated_fat_100g),
            salt=_f(row.salt_derived),
            fiber=_f(row.fiber_100g),
            proteins=_f(row.proteins_100g),
            fruits_vegetables_legumes=_f(row.fruits_veg_derived),
            fat=_f(row.fat_100g),
            has_non_nutritive_sweeteners=has_sweetener,
            flags=flags,
        )

    computed_grade = result.grade if result else None
    off_grade = row.nutriscore_grade_off
    if off_grade is None or pd.isna(off_grade):
        off_grade = None
    elif str(off_grade) in ("unknown", "not-applicable", ""):
        off_grade = None

    # Prefer OFF's published grade; ours fills the gap it leaves.
    effective_grade = off_grade or computed_grade
    grade_is_computed = off_grade is None and computed_grade is not None

    nova = None if row.nova_group is None or pd.isna(row.nova_group) else int(row.nova_group)
    hs = health_score.compute(
        grade=effective_grade,
        nova_group=nova,
        additives_tags=additive_tags,
        grade_is_computed=grade_is_computed,
        category_known=category_known,
    )

    return {
        "code": row.code,
        "nutriscore_grade_computed": computed_grade,
        "nutriscore_score_computed": result.score if result else None,
        "nutriscore_grade": effective_grade,
        "nutriscore_source": (
            "off" if off_grade else ("nutriweb" if computed_grade else None)
        ),
        "is_beverage": flags.is_beverage,
        "is_fat_oil_nuts_seeds": flags.is_fat_oil_nuts_seeds,
        "is_red_meat_product": flags.is_red_meat_product,
        "health_score": hs.value if hs else None,
        "health_confidence": hs.confidence if hs else None,
        "additive_penalty": hs.additive_penalty if hs else None,
        "n_flagged_additives": len(additives_mod.concerns(additive_tags)),
    }


def main() -> None:
    if not CATALOG_PATH.exists():
        raise SystemExit(f"{CATALOG_PATH} missing. Run pipeline/02_curate.py first.")

    fat_ids, red_meat_ids = taxonomy.load()
    additives_mod._table()  # fail fast if the additives cache is missing

    con = duckdb.connect(str(CATALOG_PATH))
    total = con.execute("SELECT count(*) FROM products").fetchone()[0]
    print(f"Scoring {total:,} products...")

    start = time.time()
    frames: list[pd.DataFrame] = []
    for offset in range(0, total, BATCH):
        batch = con.execute(
            f"SELECT {SELECT_COLS} FROM products LIMIT {BATCH} OFFSET {offset}"
        ).fetchdf()
        frames.append(
            pd.DataFrame(
                [score_row(r, fat_ids, red_meat_ids) for r in batch.itertuples()]
            )
        )
        print(f"  {min(offset + BATCH, total):,}/{total:,}", end="\r")

    scores = pd.concat(frames, ignore_index=True)
    print(f"\nScored in {time.time() - start:.0f}s")

    con.execute("DROP TABLE IF EXISTS scores")
    con.register("scores_df", scores)
    con.execute("CREATE TABLE scores AS SELECT * FROM scores_df")
    con.execute("CREATE UNIQUE INDEX idx_scores_code ON scores(code)")

    build_derived_tables(con)
    report(con)
    con.close()


def build_derived_tables(con: duckdb.DuckDBPyConnection) -> None:
    """Derived structures the app queries at request time.

    `catalog`        — the single joined view the app reads from.
    `category_sizes` — how many scored products sit under each category tag.
                       Candidate generation picks the *smallest* pool that is
                       still big enough, which is a robust proxy for "most
                       specific category" -- `categories_tags` is not reliably
                       ordered general-to-specific, so position cannot be used.
    `macro_stats`    — per-nutrient mean and standard deviation, used to
                       z-score the macro vector before comparing products.
    """
    print("\nBuilding derived tables...")

    con.execute("""
        CREATE OR REPLACE VIEW catalog AS
        SELECT p.*, s.* EXCLUDE (code)
        FROM products p JOIN scores s USING (code)
    """)

    con.execute("""
        CREATE OR REPLACE TABLE category_sizes AS
        SELECT tag, count(*) AS n
        FROM (
            SELECT unnest(categories_tags) AS tag
            FROM catalog
            WHERE health_score IS NOT NULL
        )
        WHERE tag NOT IN ('en:null', 'en:undefined')
        GROUP BY tag
    """)
    con.execute("CREATE UNIQUE INDEX idx_category_sizes_tag ON category_sizes(tag)")

    from pipeline.config import MACRO_COLUMNS

    stats = ", ".join(
        f"avg({c}) AS {c}_mean, coalesce(stddev_samp({c}), 1.0) AS {c}_std"
        for c in MACRO_COLUMNS
    )
    con.execute(f"CREATE OR REPLACE TABLE macro_stats AS SELECT {stats} FROM catalog")

    n_cat = con.execute("SELECT count(*) FROM category_sizes").fetchone()[0]
    print(f"  category_sizes: {n_cat:,} tags")


def report(con: duckdb.DuckDBPyConnection) -> None:
    """Print coverage and, critically, agreement with OFF's published grades."""
    print("\n" + "=" * 62)
    print("NUTRI-SCORE COVERAGE")
    print("=" * 62)
    print(
        con.execute("""
        SELECT
            count(*) AS products,
            count(nutriscore_grade) AS graded,
            count(*) FILTER (WHERE nutriscore_source = 'off') AS from_off,
            count(*) FILTER (WHERE nutriscore_source = 'nutriweb') AS from_nutriweb,
            count(health_score) AS with_health_score
        FROM scores
        """).fetchdf().T.to_string(header=False)
    )

    print("\n" + "=" * 62)
    print("VALIDATION vs OFF's own grades (ground truth)")
    print("=" * 62)
    agree = con.execute("""
        WITH v AS (
            SELECT p.nutriscore_grade_off AS off, s.nutriscore_grade_computed AS ours,
                   p.nutriscore_score_off AS off_score, s.nutriscore_score_computed AS our_score
            FROM products p JOIN scores s USING (code)
            WHERE p.nutriscore_grade_off NOT IN ('unknown','not-applicable')
              AND p.nutriscore_grade_off IS NOT NULL
              AND s.nutriscore_grade_computed IS NOT NULL
        )
        SELECT count(*) AS compared,
               round(100.0 * count(*) FILTER (WHERE off = ours) / count(*), 2) AS exact_grade_pct,
               round(100.0 * count(*) FILTER (
                   WHERE abs(ascii(off) - ascii(ours)) <= 1) / count(*), 2) AS within_one_letter_pct,
               round(100.0 * count(*) FILTER (WHERE off_score = our_score) / count(*), 2) AS exact_score_pct
        FROM v
    """).fetchdf()
    print(agree.T.to_string(header=False))

    print("\nDisagreements by OFF grade:")
    print(
        con.execute("""
        SELECT p.nutriscore_grade_off AS off_grade, s.nutriscore_grade_computed AS our_grade,
               count(*) AS n
        FROM products p JOIN scores s USING (code)
        WHERE p.nutriscore_grade_off NOT IN ('unknown','not-applicable')
          AND s.nutriscore_grade_computed IS NOT NULL
          AND p.nutriscore_grade_off <> s.nutriscore_grade_computed
        GROUP BY 1,2 ORDER BY n DESC LIMIT 10
        """).fetchdf().to_string(index=False)
    )


if __name__ == "__main__":
    main()
