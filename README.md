---
title: NutriWeb
emoji: 🥗
colorFrom: green
colorTo: blue
sdk: streamlit
sdk_version: 1.61.1
app_file: app.py
pinned: false
license: agpl-3.0
---

# NutriWeb

Find a packaged food, and get a **healthier alternative of the same kind** that
respects your allergens, your diet and your health profile.

Built on the full [Open Food Facts product
database](https://huggingface.co/datasets/openfoodfacts/product-database)
(4.66M products), filtered to **796,542 US products**.

---

## Why this was rebuilt

The previous version ran on a hand-cleaned CSV subset of unknown provenance,
downloaded from Google Drive at startup. Its recommendations weren't
trustworthy, and the data turned out to be only one of three causes:

| Problem | Old approach | Now |
|---|---|---|
| **Coverage** | A static CSV subset, no lineage | 796,542 US products from the live upstream dataset, rebuildable in one command |
| **Ingredient / allergen logic** | ~90 hardcoded substrings matched with `if key in name`, so `"sugar"` fired on *"sugar-free"* | Exact matching on Open Food Facts' canonical `allergens_tags`, `additives_tags`, `ingredients_analysis_tags` |
| **Additive risk** | A hand-written opinion list | EFSA overexposure ratings and the ANSES watch list, via the OFF additives taxonomy |
| **Retrieval** | FAISS index rebuilt **on every query**, with a positional slice applied to a filtered frame that misaligned scores against products | Category-constrained SQL candidate generation, ranked in NumPy |
| **Relevance** | No category constraint — a soda could return a candy bar | Candidates must share a category tag; regression-tested |
| **Blood-pressure rule** | `sodium_100g > 5.0` — five *grams* per 100 g, a level no food reaches, so it never fired | FDA-derived per-100g ceilings for salt and saturated fat |
| **Passwords** | Stored and compared in plaintext | bcrypt via passlib |
| **Dependencies** | torch + transformers + faiss ≈ 2 GB | None of them; ~40 MB of pure Python and DuckDB |

## What it does

**Health score (0–100)** — the single quantity used for ranking:
70% Nutri-Score 2023 + 30% NOVA processing group, minus a capped penalty for
additives flagged by EFSA or ANSES.

**Nutri-Score, computed where Open Food Facts has none.** Only 44% of US
products carry an OFF grade, because Nutri-Score is a European scheme and OFF
usually cannot assign one without a category. NutriWeb ports the official 2023
algorithm from OFF's own reference implementation and computes the rest:

| | products | share |
|---|---|---|
| Published by Open Food Facts | 352,295 | 44.2% |
| **Computed by NutriWeb** | **290,908** | **36.5%** |
| **Total graded** | **643,203** | **80.7%** |

Validated against OFF's own grades on **317,265 products where both exist**:
**98.37% exact agreement**, 99.73% within one letter, 95.99% exact numeric score.

Grades are never silently merged — the UI labels every grade with its source,
and grades computed for products with no category are marked *low confidence*.

**Recommendations** — three stages:

1. **Candidates** — products sharing a category tag, choosing the most specific
   tag whose pool clears a minimum size. Falls back to ingredient-tag overlap
   for the 49% of US products with no category.
2. **Hard filters** — allergens (including traces), diet, and health-condition
   ceilings, applied in SQL *before* the limit so the pool is filtered, not truncated.
   These exclude; they are never traded off against a good score.
3. **Ranking** — 45% health gain, 30% macro similarity, 20% ingredient overlap,
   5% popularity. Every component is shown to the user.

## Running it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Build the catalog (one-off; ~7.2 GB download, then about a minute)
python pipeline/01_download.py      # fetch food.parquet from the Hub
python pipeline/02_curate.py        # filter, flatten, pivot -> DuckDB
python pipeline/03_score.py         # Nutri-Score + health score + validation
python pipeline/04_audit.py         # coverage report — read this

streamlit run app.py
```

`01_download.py` needs a Hugging Face token (`hf auth login`, or `HF_TOKEN`):
anonymous requests get rate-limited on a file that size.

### Deploying to Spaces

Publish the built catalog so the Space doesn't rebuild from 7.2 GB on cold start:

```bash
python pipeline/05_publish.py <your-username>/nutriweb-us-catalog
```

Then set on the Space:
- `NUTRIWEB_CATALOG_REPO` = `<your-username>/nutriweb-us-catalog`
- `MONGODB_URI` *(optional)* — as a **repository secret**, never in a file.
  Without it the app runs with session-only profiles.

## Layout

```
app.py                  entry point; st.navigation
views/                  search · product · recommend · compare · profile · insights
components/             badges, cards, nutrient tables
nutriweb/
  data/catalog.py       DuckDB access, FTS search
  scoring/              nutriscore.py (2023 algorithm) · health_score.py · additives.py
  reco/                 engine.py · filters.py · similarity.py
  profile/              model.py · auth.py
pipeline/               01_download → 02_curate → 03_score → 04_audit → 05_publish
tests/                  64 tests: algorithm, filters, engine
```

## Tests

```bash
pytest
```

Covers Nutri-Score variant selection and grade boundaries, the safety filters
(an allergen must never reach a result), and engine guarantees — every
recommendation is strictly healthier, shares the source category, and a soda
never returns confectionery.

## Data and licence

Product data © Open Food Facts contributors, licensed
[ODbL](https://opendatacommons.org/licenses/odbl/). The Nutri-Score
implementation is ported from
[openfoodfacts-server](https://github.com/openfoodfacts/openfoodfacts-server)
(`lib/ProductOpener/Nutriscore.pm`), AGPL-3.0. This project is AGPL-3.0.

NutriWeb is an informational tool, not medical or dietary advice.
