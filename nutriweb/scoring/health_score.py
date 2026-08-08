"""The NutriWeb health score — one 0-100 number used to rank alternatives.

Why a composite rather than the Nutri-Score alone
-------------------------------------------------
Nutri-Score grades nutrition but says nothing about processing or additives:
a diet cola and a sparkling water can land in the same band. NOVA grades
processing but ignores nutrition entirely. Ranking "healthier" on either one
alone produces swaps users don't accept.

So the score blends three sourced signals, each weighted and each individually
explainable in the UI:

  * Nutri-Score 2023 (70) — nutritional quality, computed by us when OFF has
    no grade, which covers 1.7x more of the US catalog.
  * NOVA group   (30)     — degree of industrial processing.
  * Additives    (-18 max) — EFSA/ANSES-flagged additives, subtracted.

Higher is better. The weights are deliberately blunt and declared in one place
so they can be tuned and justified rather than buried in the ranking code.
"""

from __future__ import annotations

from dataclasses import dataclass

from nutriweb.scoring import additives as additives_mod

NUTRISCORE_WEIGHT = 70.0
NOVA_WEIGHT = 30.0

# Nutri-Score letters map onto the nutrition component linearly.
GRADE_POINTS = {"a": 1.0, "b": 0.75, "c": 0.5, "d": 0.25, "e": 0.0}

# NOVA 1 (unprocessed) is best, NOVA 4 (ultra-processed) worst.
NOVA_POINTS = {1: 1.0, 2: 0.75, 3: 0.4, 4: 0.0}

# Neutral prior for products with no NOVA group.
#
# The obvious alternative -- rescaling the Nutri-Score component to the full
# 0-100 range when NOVA is absent -- breaks comparability, which is fatal here
# because these scores are used to *rank*. It gave a grade-B diet soda with no
# NOVA data a 75 while a grade-A product known to be NOVA 4 scored 70, so
# missing metadata beat measured quality. A neutral prior keeps every product
# on one scale; the cost is visible in `confidence`, not hidden in the number.
NOVA_PRIOR = 0.5


@dataclass
class HealthScore:
    value: float
    nutriscore_component: float | None
    nova_component: float | None
    additive_penalty: float
    confidence: str  # 'high' | 'medium' | 'low'

    def __post_init__(self) -> None:
        self.value = round(self.value, 1)


def compute(
    *,
    grade: str | None,
    nova_group: int | None,
    additives_tags: list[str] | None,
    grade_is_computed: bool = False,
    category_known: bool = True,
) -> HealthScore | None:
    """Blend the available signals into a 0-100 score.

    Returns None when neither a Nutri-Score grade nor a NOVA group is known —
    we would be inventing a number, and an invented number would rank.

    When only one of the two is present its weight is rescaled to the full
    range, so a product with a grade but no NOVA is not penalised for OFF's
    missing metadata.
    """
    ns_component = (
        GRADE_POINTS.get(grade.lower()) * NUTRISCORE_WEIGHT
        if grade and grade.lower() in GRADE_POINTS
        else None
    )
    nova_component = (
        NOVA_POINTS.get(int(nova_group)) * NOVA_WEIGHT
        if nova_group is not None and int(nova_group) in NOVA_POINTS
        else None
    )

    if ns_component is None and nova_component is None:
        return None

    # Substitute neutral priors for whichever signal is missing so every
    # product is scored on the same 0-100 scale and remains comparable.
    base = (
        (ns_component if ns_component is not None else 0.5 * NUTRISCORE_WEIGHT)
        + (nova_component if nova_component is not None else NOVA_PRIOR * NOVA_WEIGHT)
    )

    penalty = additives_mod.penalty(additives_tags)
    value = max(0.0, min(100.0, base - penalty))

    return HealthScore(
        value=value,
        nutriscore_component=ns_component,
        nova_component=nova_component,
        additive_penalty=penalty,
        confidence=_confidence(
            has_nutriscore=ns_component is not None,
            has_nova=nova_component is not None,
            grade_is_computed=grade_is_computed,
            category_known=category_known,
        ),
    )


def _confidence(
    *,
    has_nutriscore: bool,
    has_nova: bool,
    grade_is_computed: bool,
    category_known: bool,
) -> str:
    """How much to trust this score, surfaced in the UI rather than hidden.

    A grade we computed for a product with no category is the weakest case: we
    had to assume the general-food variant, and a mis-assumed beverage or fat
    is graded on the wrong thresholds entirely.
    """
    if grade_is_computed and not category_known:
        return "low"
    if has_nutriscore and has_nova:
        return "high"
    return "medium"
