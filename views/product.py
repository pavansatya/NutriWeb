"""Product detail — scores, nutrients, and whether it suits this person."""

from __future__ import annotations

import streamlit as st

from components import badges, cards
from nutriweb.data import catalog
from nutriweb.reco import filters
from nutriweb.scoring import additives as additives_mod
from nutriweb.util import num, tag_set
from views import state

code = state.require_selection()
if not code:
    st.stop()


@st.cache_data(show_spinner=False, ttl=600)
def _load(code: str) -> dict | None:
    return catalog.get_product(code)


product = _load(code)
if product is None:
    st.error(f"No product found for barcode {code}.")
    st.stop()

profile = state.profile()
verdict = filters.evaluate(product, profile)

left, right = st.columns([1, 1.55], gap="large")

with left:
    st.markdown(
        f'<div class="nw-card">{badges.thumb(product)}'
        f"{badges.badge_row(product)}"
        f'{badges.health_meter(product.get("health_score"), product.get("health_confidence"))}'
        "</div>",
        unsafe_allow_html=True,
    )
    st.write("")
    if st.button("🔄 Find healthier swaps", type="primary", width='stretch'):
        state.open_recommendations(code)
    if st.button("➕ Add to compare", width='stretch'):
        outcome = state.add_to_compare(code)
        st.toast(
            {"added": "Added to compare.",
             "already": "Already in the compare list.",
             "full": "Compare holds three products; remove one first."}[outcome]
        )

with right:
    st.markdown(f"## {badges.title_of(product)}")
    brand = badges.brand_of(product)
    subtitle = " · ".join(
        x for x in (brand, product.get("quantity") if isinstance(product.get("quantity"), str) else None) if x
    )
    if subtitle:
        st.markdown(f'<div class="nw-sub">{badges.esc(subtitle)}</div>', unsafe_allow_html=True)
    st.caption(f"Barcode {product['code']}")

    cards.verdict_panel(verdict, profile_is_empty=state.profile_is_empty())

    # Be explicit when the grade is ours rather than Open Food Facts'.
    if product.get("nutriscore_source") == "nutriweb":
        confidence = product.get("health_confidence")
        note = (
            " Its category is unknown, so the general-food thresholds were assumed —"
            " treat this grade as indicative."
            if confidence == "low" else ""
        )
        st.info(
            "Open Food Facts has no Nutri-Score for this product. NutriWeb computed "
            f"**{str(product.get('nutriscore_grade', '')).upper()}** from the nutrition "
            f"facts using the official 2023 algorithm.{note}"
        )

    st.markdown("#### Nutrition per 100 g")
    st.markdown(cards.nutrient_table(product), unsafe_allow_html=True)
    st.caption("Bars show the share of an adult reference intake for a 100 g portion.")

st.divider()

col_a, col_b = st.columns(2, gap="large")

with col_a:
    st.markdown("#### Allergens")
    allergens = tag_set(product.get("allergens_tags"))
    traces = tag_set(product.get("traces_tags"))
    if allergens:
        st.markdown(badges.chips(sorted(allergens), "chip-danger"), unsafe_allow_html=True)
    if traces:
        st.caption("May contain traces of:")
        st.markdown(badges.chips(sorted(traces), "chip-warn"), unsafe_allow_html=True)
    if not allergens and not traces:
        st.caption("No allergens declared by Open Food Facts for this product.")

    st.markdown("#### Diet")
    analysis = tag_set(product.get("ingredients_analysis_tags"))
    diet_labels = {
        "en:vegan": ("Vegan", "chip-good"),
        "en:non-vegan": ("Not vegan", "chip-danger"),
        "en:maybe-vegan": ("Vegan status unclear", "chip-warn"),
        "en:vegetarian": ("Vegetarian", "chip-good"),
        "en:non-vegetarian": ("Not vegetarian", "chip-danger"),
        "en:maybe-vegetarian": ("Vegetarian status unclear", "chip-warn"),
        "en:palm-oil-free": ("Palm-oil free", "chip-good"),
        "en:palm-oil": ("Contains palm oil", "chip-danger"),
    }
    shown = [
        f'<span class="nw-chip {tone}">{label}</span>'
        for tag, (label, tone) in diet_labels.items()
        if tag in analysis
    ]
    st.markdown(
        '<div class="nw-chips">' + "".join(shown) + "</div>" if shown
        else "<span class='nw-sub'>Not analysed.</span>",
        unsafe_allow_html=True,
    )

with col_b:
    st.markdown("#### Additives")
    flagged = additives_mod.concerns(sorted(tag_set(product.get("additives_tags"))))
    if flagged:
        for item in flagged:
            tone = {"high": "chip-danger", "moderate": "chip-warn", "watch": ""}[item["concern"]]
            st.markdown(
                f'<div style="margin-bottom:.45rem"><span class="nw-chip {tone}">'
                f'{badges.esc(item["name"])}</span>'
                f'<div class="nw-sub" style="margin-top:.2rem">'
                f'{badges.esc("; ".join(item["reasons"]))}</div></div>',
                unsafe_allow_html=True,
            )
        st.caption("Assessments from EFSA and ANSES, via the Open Food Facts additives taxonomy.")
    else:
        total = num(product.get("n_flagged_additives"))
        st.caption(
            "No additives on the EFSA or ANSES watch lists."
            if total is not None else "No additive data for this product."
        )

    st.markdown("#### Ingredients")
    text = product.get("ingredients_text")
    if text and isinstance(text, str) and text.strip():
        st.markdown(f'<div class="nw-sub">{badges.esc(text)}</div>', unsafe_allow_html=True)
    else:
        st.caption("No ingredient list available.")

# Record the view for the profile history.
if profile.user_id:
    from nutriweb.profile import auth

    auth.log_view(profile.user_id, product, verdict.summary)
