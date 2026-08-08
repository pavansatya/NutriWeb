"""Step 5 — publish the curated catalog to the Hugging Face Hub.

The Space must not rebuild from the 7.2 GB source on every cold start, so the
finished ~400 MB catalog is pushed to a dataset repo and downloaded at startup
by `nutriweb/data/catalog.py`. That download is in-network on Spaces and takes
seconds.

This replaces the Google Drive + gdown + zip arrangement the previous version
used, which had no versioning and no checksum.

Usage:
    python pipeline/05_publish.py <your-hf-username>/nutriweb-us-catalog
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.config import CATALOG_PATH  # noqa: E402

CARD = """---
license: odbl
tags:
  - food
  - nutrition
  - open-food-facts
---

# NutriWeb US catalog

A curated, scored subset of the [Open Food Facts product
database](https://huggingface.co/datasets/openfoodfacts/product-database),
built by the NutriWeb pipeline. One DuckDB file.

* US products only, non-obsolete, with a resolvable English name and at least
  ingredients, a category, or nutrition facts.
* Multilingual fields collapsed to English; `nutriments` pivoted to per-100g columns.
* Nutri-Score computed with the official 2023 algorithm where Open Food Facts
  publishes none, which raises scored coverage roughly 1.8x.
* Tables: `products`, `scores`, `category_sizes`, `macro_stats`; view `catalog`.

Product data (c) Open Food Facts contributors, licensed ODbL. This derived
catalog carries the same licence.

Rebuild with `pipeline/01_download.py` .. `pipeline/05_publish.py`.
"""


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(
            "Usage: python pipeline/05_publish.py <hf-username>/nutriweb-us-catalog"
        )
    repo_id = sys.argv[1]

    if not CATALOG_PATH.exists():
        raise SystemExit(f"{CATALOG_PATH} missing. Run steps 01-04 first.")

    from huggingface_hub import HfApi

    api = HfApi()
    size_mb = CATALOG_PATH.stat().st_size / 1024**2
    print(f"Publishing {CATALOG_PATH.name} ({size_mb:.0f} MB) to {repo_id} ...")

    api.create_repo(repo_id, repo_type="dataset", exist_ok=True)
    api.upload_file(
        path_or_fileobj=str(CATALOG_PATH),
        path_in_repo=CATALOG_PATH.name,
        repo_id=repo_id,
        repo_type="dataset",
    )
    api.upload_file(
        path_or_fileobj=CARD.encode(),
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="dataset",
    )

    print(
        f"Done: https://huggingface.co/datasets/{repo_id}\n\n"
        f"Point the Space at it by setting this variable:\n"
        f"  NUTRIWEB_CATALOG_REPO={repo_id}"
    )


if __name__ == "__main__":
    main()
