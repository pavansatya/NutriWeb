"""Shared session state and small navigation helpers."""

from __future__ import annotations

import streamlit as st

from nutriweb.profile.model import UserProfile

# Page paths, so navigation targets are declared in one place.
SEARCH = "views/search.py"
PRODUCT = "views/product.py"
RECOMMEND = "views/recommend.py"
COMPARE = "views/compare.py"
PROFILE = "views/profile_page.py"


def init() -> None:
    st.session_state.setdefault("profile", UserProfile())
    st.session_state.setdefault("selected_code", None)
    st.session_state.setdefault("compare_codes", [])
    st.session_state.setdefault("last_query", "")


def profile() -> UserProfile:
    return st.session_state.profile


def profile_is_empty() -> bool:
    """True when the user has told us nothing we could filter on."""
    p = profile()
    return not (
        p.allergens or p.diets or p.high_blood_pressure
        or p.high_cholesterol or p.avoid_flagged_additives
    )


def open_product(code: str) -> None:
    st.session_state.selected_code = code
    st.switch_page(PRODUCT)


def open_recommendations(code: str) -> None:
    st.session_state.selected_code = code
    st.switch_page(RECOMMEND)


def add_to_compare(code: str) -> str:
    codes: list[str] = st.session_state.compare_codes
    if code in codes:
        return "already"
    if len(codes) >= 3:
        return "full"
    codes.append(code)
    return "added"


def sign_out() -> None:
    st.session_state.profile = UserProfile()
    st.session_state.selected_code = None
    st.session_state.compare_codes = []


def require_selection() -> str | None:
    """Guard for pages that need a chosen product."""
    code = st.session_state.get("selected_code")
    if not code:
        st.info("Pick a product from Search first.")
        if st.button("Go to Search"):
            st.switch_page(SEARCH)
        return None
    return code
