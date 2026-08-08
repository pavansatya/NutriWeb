"""Step 5 — publish the curated catalog to the Hugging Face Hub.

The Space must not rebuild from the 7.2 GB source on every cold start, so the
finished ~400 MB catalog is pushed to a dataset repo and downloaded at startup
by `nutriweb/data/catalog.py`. That download is in-network on Spaces and takes
seconds.

This replaces the Google Drive + gdown + zip arrangement the previous version
used, which had no versioning and no checksum.

Usage:
    python pipeline/05_publish.py <your-hf-username>/nutriweb-us-catalog
    python pipeline/05_publish.py <your-hf-username>/nutriweb-us-catalog --private

Repos are created public by default, which is what a Space on the free tier
needs in order to download the catalog without a token. Pass --private to keep
it unlisted; the Space will then need an HF_TOKEN secret to read it.
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
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    private = "--private" in sys.argv
    if not args:
        raise SystemExit(
            "Usage: python pipeline/05_publish.py <hf-username>/nutriweb-us-catalog [--private]"
        )
    repo_id = args[0]

    if not CATALOG_PATH.exists():
        raise SystemExit(f"{CATALOG_PATH} missing. Run steps 01-04 first.")

    from huggingface_hub import HfApi

    api = HfApi()

    # Fail early with a clear message rather than a 403 midway through a
    # 400 MB upload.
    user = api.whoami().get("name")
    owner = repo_id.split("/")[0]
    if owner != user and owner not in {o.get("name") for o in api.whoami().get("orgs", [])}:
        raise SystemExit(
            f"You are logged in as '{user}', but the repo id starts with '{owner}'.\n"
            f"Use '{user}/{repo_id.split('/')[-1]}' instead."
        )

    size_mb = CATALOG_PATH.stat().st_size / 1024**2
    visibility = "private" if private else "public"
    print(f"Publishing {CATALOG_PATH.name} ({size_mb:.0f} MB) to {repo_id} [{visibility}] ...")

    api.create_repo(repo_id, repo_type="dataset", exist_ok=True, private=private)
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
