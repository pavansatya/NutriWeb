"""Healthier swaps for the selected product."""

from __future__ import annotations

import streamlit as st

from components import badges, cards
from nutriweb.data import catalog
from nutriweb.reco import engine
from views import state

code = state.require_selection()
if not code:
    st.stop()

product = catalog.get_product(code)
if product is None:
    st.error(f"No product found for barcode {code}.")
    st.stop()

profile = state.profile()

st.markdown(
    f"""<div class="nw-hero">
        <h1>Healthier than {badges.title_of(product)}</h1>
        <p>Same kind of product, better health score, filtered against your profile.</p>
    </div>""",
    unsafe_allow_html=True,
)

col_left, col_right = st.columns([1, 3], gap="large")
with col_left:
    st.markdown(
        f'<div class="nw-card">{badges.thumb(product)}'
        f"<h4>{badges.title_of(product)}</h4>"
        f'<div class="nw-brand">{badges.brand_of(product) or "&nbsp;"}</div>'
        f"{badges.badge_row(product)}"
        f'{badges.health_meter(product.get("health_score"))}</div>',
        unsafe_allow_html=True,
    )
    if st.button("← Back to product", width='stretch'):
        state.open_product(code)

with col_right:
    top_n = st.slider("How many alternatives", 3, 12, 6, key="rec_n")

    with st.spinner("Finding alternatives..."):
        recommendations, basis = engine.recommend(product, profile, top_n=top_n)

    if state.profile_is_empty():
        st.info(
            "You have no profile set, so these results are not filtered for allergens "
            "or diet. Add them under **My profile** for personalised swaps."
        )

    if not recommendations:
        message = basis.get("message", "No healthier alternatives found.")
        # "Already the best option" is good news, not a failure.
        if basis.get("reason") == "already_best":
            st.success(f"✓ {message}")
        else:
            st.warning(message)
            if basis.get("reason") == "filtered_out":
                st.caption("Relaxing a dietary preference would surface these.")
        st.stop()

    # Be explicit about how the candidate set was chosen, rather than
    # presenting results as if they came from nowhere.
    if basis["mode"] == "category":
        label = str(basis["category"]).split(":", 1)[-1].replace("-", " ")
        st.caption(
            f"Compared against **{basis['pool']}** products in **{label}** that pass your filters."
        )
    else:
        st.caption(
            f"This product has no category in Open Food Facts, so alternatives were "
            f"matched by shared ingredients across **{basis['pool']}** candidates."
        )

    for start in range(0, len(recommendations), 3):
        row = recommendations[start : start + 3]
        for column, rec in zip(st.columns(3), row):
            with column:
                cards.recommendation_card(
                    rec,
                    key=f"rec_{rec.product['code']}",
                    on_open=state.open_product,
                )

    with st.expander("How these were ranked"):
        st.markdown(
            f"""
Candidates must be **healthier** than the original and must pass every hard
filter from your profile — allergens and diet are exclusions, never trade-offs.
Survivors are then ranked on a weighted blend:

| Signal | Weight | What it measures |
|---|---|---|
| Health gain | {engine.W_HEALTH_GAIN:.0%} | Improvement in the 0–100 NutriWeb health score |
| Macro similarity | {engine.W_MACRO:.0%} | Distance across energy, fat, carbs, sugar, fibre, protein and salt |
| Ingredient overlap | {engine.W_INGREDIENT:.0%} | Jaccard overlap of Open Food Facts' canonical ingredient tags |
| Popularity | {engine.W_POPULARITY:.0%} | Scan count, used only to break ties |

The health score itself is 70% Nutri-Score 2023, 30% NOVA processing group,
minus a penalty for additives flagged by EFSA or ANSES.
"""
        )
