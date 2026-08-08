"""Score badges, chips and meters — the small visual vocabulary of the app.

Everything returns an HTML string rather than calling st.* directly, so the
pieces compose inside cards and columns.

A recurring rule here: whenever a Nutri-Score grade is shown, its *source* is
shown with it. Roughly 45% of the grades in the catalog were computed by
NutriWeb rather than published by Open Food Facts, and presenting the two
identically would overstate what we know.
"""

from __future__ import annotations

import html

from nutriweb.util import num, tag_set

GRADE_LABEL = {
    "a": "A", "b": "B", "c": "C", "d": "D", "e": "E",
}
NOVA_LABEL = {
    1: "Unprocessed",
    2: "Culinary ingredient",
    3: "Processed",
    4: "Ultra-processed",
}


def esc(value) -> str:
    return html.escape(str(value)) if value is not None else ""


def nutriscore_badge(grade: str | None, source: str | None = None) -> str:
    """Nutri-Score pill. `source` is 'off' or 'nutriweb'."""
    if not grade or str(grade).lower() not in GRADE_LABEL:
        return '<span class="nw-badge nw-badge-neutral">Nutri-Score n/a</span>'
    g = str(grade).lower()
    chip = ""
    if source == "nutriweb":
        chip = '<span class="nw-source" title="Computed by NutriWeb from the nutrition facts, because Open Food Facts has no grade for this product">est.</span>'
    elif source == "off":
        chip = '<span class="nw-source" title="Published by Open Food Facts">OFF</span>'
    return (
        f'<span class="nw-badge ns-{g}"><span class="k">Nutri-Score</span> '
        f"{GRADE_LABEL[g]}</span>{chip}"
    )


def nova_badge(nova) -> str:
    value = num(nova)
    if value is None or int(value) not in NOVA_LABEL:
        return ""
    n = int(value)
    tone = {1: "chip-good", 2: "chip-good", 3: "chip-warn", 4: "chip-danger"}[n]
    return f'<span class="nw-chip {tone}" title="NOVA {n}">{NOVA_LABEL[n]}</span>'


def eco_badge(grade) -> str:
    if not grade or str(grade).lower() not in GRADE_LABEL:
        return ""
    g = str(grade).lower()
    return f'<span class="nw-badge ns-{g}"><span class="k">Eco</span> {GRADE_LABEL[g]}</span>'


def badge_row(product: dict) -> str:
    parts = [
        nutriscore_badge(product.get("nutriscore_grade"), product.get("nutriscore_source")),
        eco_badge(product.get("environmental_score_grade")),
        nova_badge(product.get("nova_group")),
    ]
    return '<div class="nw-badges">' + "".join(p for p in parts if p) + "</div>"


def health_meter(score, confidence: str | None = None) -> str:
    """The 0-100 NutriWeb health score with a coloured bar."""
    value = num(score)
    if value is None:
        return '<div class="nw-health"><span class="m">Not enough data to score</span></div>'

    colour = (
        "var(--ns-a)" if value >= 75
        else "var(--ns-b)" if value >= 55
        else "var(--ns-c)" if value >= 40
        else "var(--ns-d)" if value >= 25
        else "var(--ns-e)"
    )
    note = f" · {esc(confidence)} confidence" if confidence else ""
    return (
        '<div class="nw-health">'
        f'<span class="v">{value:.0f}</span><span class="m">/100 health score{note}</span>'
        "</div>"
        f'<div class="nw-meter"><span style="width:{max(2, min(100, value)):.0f}%;'
        f'background:{colour}"></span></div>'
    )


def thumb(product: dict) -> str:
    url = product.get("image_url")
    if url and not isinstance(url, float):
        return f'<img class="nw-thumb" src="{esc(url)}" loading="lazy" alt="">'
    return '<div class="nw-thumb nw-thumb-empty">🥫</div>'


def chips(tags, tone: str = "", limit: int = 12, strip_prefix: bool = True) -> str:
    """Render OFF tags as chips: 'en:peanuts' -> 'peanuts'."""
    items = sorted(tag_set(tags)) if not isinstance(tags, list) else list(tags)
    if not items:
        return ""
    out = []
    for tag in items[:limit]:
        label = tag.split(":", 1)[-1].replace("-", " ") if strip_prefix else tag
        out.append(f'<span class="nw-chip {tone}">{esc(label)}</span>')
    if len(items) > limit:
        out.append(f'<span class="nw-chip">+{len(items) - limit} more</span>')
    return '<div class="nw-chips">' + "".join(out) + "</div>"


def title_of(product: dict) -> str:
    name = product.get("product_name")
    return esc(name) if name and not isinstance(name, float) else "Unnamed product"


def brand_of(product: dict) -> str:
    brands = product.get("brands")
    if not brands or isinstance(brands, float):
        return ""
    # OFF stores brands as a comma-separated string, often with duplicates.
    seen, out = set(), []
    for b in str(brands).split(","):
        b = b.strip()
        if b and b.lower() not in seen:
            seen.add(b.lower())
            out.append(b)
    return esc(", ".join(out[:2]))
