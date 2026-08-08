"""Search — the landing page."""

from __future__ import annotations

import streamlit as st

from components import cards
from nutriweb.data import catalog
from views import state

st.markdown(
    """<div class="nw-hero">
        <h1>Find a product, get a healthier swap</h1>
        <p>Search by name or scan a barcode. Every result is checked against your
        allergens, your diet and your health profile before it is recommended.</p>
    </div>""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False, ttl=600)
def _search(query: str, limit: int) -> list[dict]:
    return catalog.search(query, limit=limit)


@st.cache_data(show_spinner=False)
def _stats() -> dict:
    return catalog.stats()


query = st.text_input(
    "Search",
    placeholder="e.g. peanut butter, greek yogurt, or a barcode like 0049000028911",
    label_visibility="collapsed",
    key="search_box",
)

if not query:
    stats = _stats()
    st.caption(
        f"{stats['products']:,} US products · {stats['scored']:,} with a health score · "
        f"{stats['graded_by_nutriweb']:,} graded by NutriWeb where Open Food Facts had no grade"
    )
    st.markdown("##### Try one of these")
    examples = ["greek yogurt", "peanut butter", "granola bar", "tortilla chips", "sparkling water"]
    columns = st.columns(len(examples))
    for column, example in zip(columns, examples):
        if column.button(example, width='stretch', key=f"eg_{example}"):
            st.session_state.search_box = example
            st.rerun()
    st.stop()

with st.spinner("Searching..."):
    results = _search(query, 24)

if not results:
    st.warning(
        f"Nothing matched **{query}**. Try a brand name, a simpler term, or a full barcode."
    )
    st.stop()

st.caption(f"{len(results)} results for **{query}**")

for start in range(0, len(results), 4):
    row = results[start : start + 4]
    for column, product in zip(st.columns(4), row):
        with column:
            cards.product_card(
                product,
                key=f"open_{product['code']}",
                on_open=state.open_product,
            )
