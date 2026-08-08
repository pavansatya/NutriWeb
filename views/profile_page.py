"""Profile — sign in, and set the preferences that drive every filter."""

from __future__ import annotations

import streamlit as st

from nutriweb.profile import auth
from nutriweb.profile.model import ALLERGEN_CHOICES, DIET_CHOICES, UserProfile
from views import state

st.markdown(
    """<div class="nw-hero">
        <h1>My profile</h1>
        <p>Everything here is used as a hard filter: allergens and diet exclude
        products outright rather than merely ranking them lower.</p>
    </div>""",
    unsafe_allow_html=True,
)

profile: UserProfile = state.profile()

if auth.demo_mode():
    st.caption(
        "No account database is configured, so profiles last for this session only. "
        "Set `MONGODB_URI` as a Space secret to persist them."
    )


def _preferences_form(current: UserProfile, key_prefix: str) -> UserProfile:
    """The shared preference widgets. Returns a profile built from the inputs."""
    label_for_tag = {v: k for k, v in ALLERGEN_CHOICES.items()}
    selected_labels = st.multiselect(
        "Allergens to avoid",
        list(ALLERGEN_CHOICES),
        default=[label_for_tag[t] for t in current.allergens if t in label_for_tag],
        key=f"{key_prefix}_allergens",
        help="Matched against Open Food Facts' curated allergen and traces tags.",
    )
    diets = st.multiselect(
        "Dietary preferences",
        DIET_CHOICES,
        default=current.diets,
        key=f"{key_prefix}_diets",
    )
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", 1, 120, current.age, key=f"{key_prefix}_age")
        high_bp = st.checkbox(
            "High blood pressure", current.high_blood_pressure, key=f"{key_prefix}_bp",
            help="Flags and filters products above 1.15 g salt per 100 g.",
        )
    with col2:
        gender = st.selectbox(
            "Gender",
            ["Prefer not to say", "Female", "Male", "Other"],
            index=["Prefer not to say", "Female", "Male", "Other"].index(current.gender)
            if current.gender in ["Prefer not to say", "Female", "Male", "Other"] else 0,
            key=f"{key_prefix}_gender",
        )
        high_chol = st.checkbox(
            "High cholesterol", current.high_cholesterol, key=f"{key_prefix}_chol",
            help="Flags and filters products above 4 g saturated fat per 100 g.",
        )
    avoid_additives = st.checkbox(
        "Exclude products with additives EFSA flags as high-risk",
        current.avoid_flagged_additives,
        key=f"{key_prefix}_additives",
    )

    return UserProfile(
        user_id=current.user_id,
        age=int(age),
        gender=gender,
        allergens=[ALLERGEN_CHOICES[label] for label in selected_labels],
        diets=diets,
        high_blood_pressure=high_bp,
        high_cholesterol=high_chol,
        avoid_flagged_additives=avoid_additives,
    )


if profile.user_id:
    st.success(f"Signed in as **{profile.user_id}**")
    with st.form("prefs"):
        updated = _preferences_form(profile, "signed")
        if st.form_submit_button("Save preferences", type="primary"):
            updated.user_id = profile.user_id
            st.session_state.profile = updated
            auth.save_profile(updated)
            st.toast("Preferences saved.")

    st.divider()
    st.markdown("### Recently viewed")
    history = auth.recent_views(profile.user_id)
    if not history:
        st.caption("Nothing viewed yet.")
    else:
        for entry in history[:15]:
            st.markdown(
                f"- **{entry.get('product_name') or 'Unnamed'}** "
                f"<span class='nw-sub'>{entry.get('brands') or ''} · "
                f"{entry.get('verdict') or ''}</span>",
                unsafe_allow_html=True,
            )
    st.stop()


tab_guest, tab_login, tab_register = st.tabs(
    ["Use without an account", "Sign in", "Create account"]
)

with tab_guest:
    st.caption(
        "Set preferences for this session only. Nothing is stored and no account is needed."
    )
    with st.form("guest"):
        guest_profile = _preferences_form(profile, "guest")
        if st.form_submit_button("Apply", type="primary"):
            st.session_state.profile = guest_profile
            st.toast("Preferences applied for this session.")
            st.rerun()

with tab_login:
    with st.form("login"):
        user_id = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Sign in", type="primary"):
            result = auth.login(user_id, password)
            if result.ok:
                st.session_state.profile = result.profile
                st.rerun()
            else:
                st.error(result.message)

with tab_register:
    with st.form("register"):
        new_id = st.text_input("Choose a username")
        new_pw = st.text_input("Choose a password", type="password", help="At least 8 characters.")
        new_profile = _preferences_form(UserProfile(), "reg")
        if st.form_submit_button("Create account", type="primary"):
            result = auth.register(new_id, new_pw, new_profile)
            if result.ok:
                st.session_state.profile = result.profile
                st.success(result.message)
                st.rerun()
            else:
                st.error(result.message)
