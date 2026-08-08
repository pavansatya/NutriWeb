"""Similarity between products, on two axes the user cares about.

The app this replaces used sentence-transformer embeddings over ingredient
text, searched with FAISS. That approach had three problems: the index was
rebuilt on every query, the embeddings had to be downloaded from Google Drive,
and the similarity it measured was over free text that OFF has *already*
canonicalised.

Open Food Facts resolves every ingredient to a taxonomy tag, so set overlap on
`ingredients_tags` measures the same thing exactly, in microseconds, with no
model. Macro similarity is a plain distance over the nutrient vector. Both are
explainable to the user, which embeddings never were.
"""

from __future__ import annotations

import numpy as np

from nutriweb.util import num
from pipeline.config import MACRO_COLUMNS


def macro_vector(product: dict, stats: dict[str, tuple[float, float]]) -> np.ndarray:
    """Z-scored nutrient vector. Missing nutrients sit at the mean (z = 0).

    Standardising matters because the raw units are wildly different: energy is
    hundreds of kcal while salt is under a gram, so an unscaled distance would
    be energy and nothing else.
    """
    out = np.zeros(len(MACRO_COLUMNS), dtype=np.float32)
    for i, col in enumerate(MACRO_COLUMNS):
        value = num(product.get(col))
        if value is None:
            continue
        mean, std = stats.get(col, (0.0, 1.0))
        out[i] = (value - mean) / (std or 1.0)
    return out


def macro_matrix(frame, stats: dict[str, tuple[float, float]]) -> np.ndarray:
    """Vectorised `macro_vector` over a DataFrame of candidates."""
    cols = []
    for col in MACRO_COLUMNS:
        mean, std = stats.get(col, (0.0, 1.0))
        values = frame[col].astype("float32").to_numpy()
        cols.append(np.nan_to_num((values - mean) / (std or 1.0), nan=0.0))
    return np.column_stack(cols).astype(np.float32)


def macro_similarity(source: np.ndarray, candidates: np.ndarray) -> np.ndarray:
    """Similarity in [0, 1] from Euclidean distance in z-space.

    Distance rather than cosine: for nutrition, *magnitude* matters. Cosine
    would call a 500 kcal bar and a 50 kcal snack identical if their nutrient
    ratios matched, which is exactly the swap a user would reject.
    """
    distance = np.linalg.norm(candidates - source[None, :], axis=1)
    # Scaled so a distance of one standard deviation lands near 0.5.
    return 1.0 / (1.0 + distance / np.sqrt(len(MACRO_COLUMNS)))


def jaccard(source_tags: set[str], candidate_tags: list[set[str]]) -> np.ndarray:
    """Ingredient-set overlap: |A ∩ B| / |A ∪ B| for each candidate."""
    if not source_tags:
        return np.zeros(len(candidate_tags), dtype=np.float32)
    out = np.zeros(len(candidate_tags), dtype=np.float32)
    for i, tags in enumerate(candidate_tags):
        if not tags:
            continue
        union = len(source_tags | tags)
        if union:
            out[i] = len(source_tags & tags) / union
    return out


def shared_macros(source: dict, candidate: dict, tolerance: float = 0.25) -> list[str]:
    """Which macros are within `tolerance` relative difference — for the "why" line."""
    labels = {
        "energy_kcal_100g": "calories",
        "proteins_100g": "protein",
        "carbohydrates_100g": "carbs",
        "fat_100g": "fat",
        "sugars_100g": "sugar",
        "fiber_100g": "fibre",
    }
    matches = []
    for col, label in labels.items():
        a, b = num(source.get(col)), num(candidate.get(col))
        if a is None or b is None:
            continue
        scale = max(abs(a), abs(b), 1e-6)
        if abs(a - b) / scale <= tolerance:
            matches.append(label)
    return matches
