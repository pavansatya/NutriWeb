"""Product cards and the verdict panel."""

from __future__ import annotations

import streamlit as st

from components import badges
from nutriweb.reco.engine import Recommendation
from nutriweb.reco.filters import Verdict


def product_card(product: dict, *, key: str, on_open, cta: str = "View details") -> None:
    """A search-result card with an action button beneath it."""
    st.markdown(
        f"""<div class="nw-card">
            {badges.thumb(product)}
            <h4>{badges.title_of(product)}</h4>
            <div class="nw-brand">{badges.brand_of(product) or "&nbsp;"}</div>
            {badges.badge_row(product)}
            {badges.health_meter(product.get("health_score"))}
        </div>""",
        unsafe_allow_html=True,
    )
    if st.button(cta, key=key, width='stretch'):
        on_open(product["code"])


def recommendation_card(rec: Recommendation, *, key: str, on_open) -> None:
    """A recommendation card. Always states why this specific swap was chosen."""
    product = rec.product
    warning = ""
    if rec.warnings:
        warning = (
            '<div class="nw-why" style="color:#8A6D00">⚠︎ '
            + badges.esc("; ".join(rec.warnings))
            + "</div>"
        )

    st.markdown(
        f"""<div class="nw-card">
            {badges.thumb(product)}
            <h4>{badges.title_of(product)}</h4>
            <div class="nw-brand">{badges.brand_of(product) or "&nbsp;"}</div>
            <span class="nw-gain">+{rec.health_gain:.0f} health</span>
            {badges.badge_row(product)}
            <div class="nw-why">{badges.esc(rec.why)}</div>
            {warning}
        </div>""",
        unsafe_allow_html=True,
    )
    if st.button("View details", key=key, width='stretch'):
        on_open(product["code"])


def verdict_panel(verdict: Verdict, profile_is_empty: bool = False) -> None:
    """The "is this for you" panel.

    Driven by the same `filters.evaluate` the engine uses, so what the user is
    told here always matches what the recommender actually did.
    """
    if profile_is_empty:
        st.markdown(
            '<div class="nw-verdict v-warn"><h5>No profile set</h5>'
            "<div>Add your allergens and dietary preferences to see whether this "
            "product suits you.</div></div>",
            unsafe_allow_html=True,
        )
        return

    tone = "v-block" if verdict.blockers else ("v-warn" if verdict.warnings else "v-ok")
    icon = "✕" if verdict.blockers else ("!" if verdict.warnings else "✓")
    items = "".join(
        f"<li>{badges.esc(m)}</li>" for m in (*verdict.blockers, *verdict.warnings)
    )
    body = f"<ul>{items}</ul>" if items else "<div>Nothing in your profile conflicts with this product.</div>"

    st.markdown(
        f'<div class="nw-verdict {tone}"><h5>{icon} {badges.esc(verdict.summary)}</h5>{body}</div>',
        unsafe_allow_html=True,
    )


def nutrient_table(product: dict, reference: dict | None = None) -> str:
    """Per-100g nutrient table with bars scaled to a reference intake.

    Bars are relative to a rough per-100g share of an adult reference intake,
    so they answer "is this a lot?" rather than just restating the number.
    """
    rows = [
        ("Energy", "energy_kcal_100g", "kcal", 200.0),
        ("Fat", "fat_100g", "g", 17.5),
        ("  of which saturates", "saturated_fat_100g", "g", 5.0),
        ("Carbohydrates", "carbohydrates_100g", "g", 45.0),
        ("  of which sugars", "sugars_100g", "g", 22.5),
        ("Fibre", "fiber_100g", "g", 7.5),
        ("Protein", "proteins_100g", "g", 25.0),
        ("Salt", "salt_derived", "g", 1.5),
    ]
    from nutriweb.util import num

    out = ['<table class="nw-nutri">']
    for label, col, unit, high in rows:
        value = num(product.get(col))
        if value is None:
            out.append(
                f'<tr><td class="n">{badges.esc(label)}</td>'
                f'<td class="v nw-sub">—</td><td></td></tr>'
            )
            continue
        pct = max(2.0, min(100.0, value / high * 100.0))
        over = " over" if value > high else ""
        out.append(
            f'<tr><td class="n">{badges.esc(label)}</td>'
            f'<td class="v">{value:.1f} {unit}</td>'
            f'<td><div class="nw-bar"><span class="{over.strip()}" '
            f'style="width:{pct:.0f}%"></span></div></td></tr>'
        )
    out.append("</table>")
    return "".join(out)
