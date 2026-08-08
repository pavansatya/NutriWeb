"""NutriWeb — entry point.

Replaces the previous single 450-line script that routed pages by mutating
`st.session_state.page` and calling `st.stop()` at the end of each branch. This
uses Streamlit's own navigation, so the browser URL, the back button and the
sidebar all behave normally.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

st.set_page_config(
    page_title="NutriWeb",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def _styles() -> str:
    return (REPO_ROOT / "styles.css").read_text()


st.markdown(f"<style>{_styles()}</style>", unsafe_allow_html=True)

from nutriweb.profile.model import UserProfile  # noqa: E402
from views import state  # noqa: E402

state.init()

pages = [
    st.Page("views/search.py", title="Search", icon=":material/search:", default=True),
    st.Page("views/product.py", title="Product", icon=":material/nutrition:"),
    st.Page("views/recommend.py", title="Healthier swaps", icon=":material/swap_horiz:"),
    st.Page("views/compare.py", title="Compare", icon=":material/compare_arrows:"),
    st.Page("views/profile_page.py", title="My profile", icon=":material/person:"),
    st.Page("views/insights.py", title="Data insights", icon=":material/insights:"),
]

with st.sidebar:
    st.markdown("### 🥗 NutriWeb")
    st.caption("Personalised food choices, from the full Open Food Facts US catalog.")
    profile: UserProfile = st.session_state.profile
    if profile.user_id:
        st.success(f"Signed in as **{profile.user_id}**")
        if st.button("Sign out", use_container_width=True):
            state.sign_out()
            st.rerun()
    else:
        st.info("Browsing as a guest. Set a profile to get personalised results.")

st.navigation(pages).run()
