"""Side-by-side comparison of up to three products."""

from __future__ import annotations

import streamlit as st

from components import badges, cards
from nutriweb.data import catalog
from nutriweb.reco import filters
from views import state

st.markdown(
    """<div class="nw-hero">
        <h1>Compare</h1>
        <p>Put up to three products side by side, scored the same way.</p>
    </div>""",
    unsafe_allow_html=True,
)

codes: list[str] = st.session_state.compare_codes

if not codes:
    st.info("Nothing to compare yet. Open a product and choose **Add to compare**.")
    if st.button("Go to Search"):
        st.switch_page(state.SEARCH)
    st.stop()

products = [p for code in codes if (p := catalog.get_product(code))]
profile = state.profile()

columns = st.columns(len(products), gap="large")
for column, product in zip(columns, products):
    with column:
        st.markdown(
            f'<div class="nw-card">{badges.thumb(product)}'
            f"<h4>{badges.title_of(product)}</h4>"
            f'<div class="nw-brand">{badges.brand_of(product) or "&nbsp;"}</div>'
            f"{badges.badge_row(product)}"
            f'{badges.health_meter(product.get("health_score"))}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(cards.nutrient_table(product), unsafe_allow_html=True)

        verdict = filters.evaluate(product, profile)
        if not state.profile_is_empty():
            cards.verdict_panel(verdict)

        if st.button("Remove", key=f"rm_{product['code']}", width='stretch'):
            st.session_state.compare_codes.remove(product["code"])
            st.rerun()

st.divider()
if st.button("Clear all"):
    st.session_state.compare_codes = []
    st.rerun()
