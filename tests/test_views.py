"""View tests that exercise interaction, not just page load.

An earlier smoke test only rendered each page, so it never clicked anything and
missed a crash on the example-search buttons: assigning to `search_box` after
the widget existed raised StreamlitAPIException. These tests click.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from nutriweb.data import catalog
from nutriweb.profile.model import UserProfile

# AppTest resolves relative paths against the file that calls it, which is this
# one, so page paths must be absolute.
REPO_ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.skipif(
    not catalog.DEFAULT_CATALOG.exists(),
    reason="catalog not built; run pipeline/01..03 first",
)

TIMEOUT = 90


def run(path: str, **session) -> AppTest:
    at = AppTest.from_file(str(REPO_ROOT / path), default_timeout=TIMEOUT)
    at.session_state["profile"] = session.pop("profile", UserProfile())
    at.session_state["selected_code"] = session.pop("selected_code", None)
    at.session_state["compare_codes"] = session.pop("compare_codes", [])
    at.session_state["last_query"] = ""
    at.run()
    return at


def assert_clean(at: AppTest, label: str) -> None:
    assert not at.exception, f"{label}: {[str(e.value)[:400] for e in at.exception]}"


@pytest.fixture(scope="module")
def sample_code() -> str:
    row = catalog.connect().execute(
        """SELECT code FROM catalog
           WHERE health_score IS NOT NULL AND primary_category IS NOT NULL
           ORDER BY COALESCE(unique_scans_n, 0) DESC LIMIT 1"""
    ).fetchone()
    return row[0]


class TestSearchPage:
    def test_loads(self):
        assert_clean(run("views/search.py"), "search load")

    def test_example_buttons_do_not_crash(self):
        """The regression. Clicking an example seeds the box and re-runs."""
        at = run("views/search.py")
        assert at.button, "no example buttons rendered"
        at.button[0].click().run()
        assert_clean(at, "example click")
        assert at.session_state["search_box"]

    def test_typing_a_query_returns_results(self):
        at = run("views/search.py")
        at.text_input[0].set_value("yogurt").run()
        assert_clean(at, "typed query")
        # Result cards render as buttons ("View details").
        assert at.button, "query produced no result cards"

    def test_nonsense_query_warns_instead_of_crashing(self):
        at = run("views/search.py")
        at.text_input[0].set_value("zzzzqqqxnotathing").run()
        assert_clean(at, "nonsense query")
        assert at.warning


class TestSearchResilience:
    """Search must survive a missing full-text-search extension.

    The extension is present on the machine that builds the catalog but not in
    a fresh container. An unconditional `LOAD fts` took the deployed Space down
    on startup with an IOException before the first page could render.
    """

    def test_loading_fts_never_raises(self):
        import duckdb

        con = duckdb.connect(str(catalog.DEFAULT_CATALOG), read_only=True)
        con.execute("SET autoinstall_known_extensions=false")
        con.execute("SET autoload_known_extensions=false")
        con.execute("SET extension_directory='/nonexistent/nutriweb-test'")
        # Returns a bool either way; the point is that it does not raise.
        assert catalog._try_load_fts(con) in (True, False)

    def test_fallback_search_returns_results(self):
        results = catalog._search_without_fts("yogurt", 5)
        assert results
        assert all(r.get("code") for r in results)

    def test_fallback_matches_brand_as_well_as_name(self):
        assert catalog._search_without_fts("kellogg", 5)

    def test_fallback_respects_the_limit(self):
        assert len(catalog._search_without_fts("a", 3)) <= 3

    def test_fallback_handles_no_match(self):
        assert catalog._search_without_fts("zzzqqqxnotathing", 5) == []

    def test_barcode_lookup_does_not_depend_on_fts(self):
        product = catalog.get_product("7622210449283")
        assert product is None or product.get("code")


class TestProductPage:
    def test_renders_for_a_real_product(self, sample_code):
        assert_clean(run("views/product.py", selected_code=sample_code), "product")

    def test_renders_with_a_full_profile(self, sample_code):
        profile = UserProfile(
            allergens=["en:milk", "en:gluten"], diets=["Vegan"],
            high_blood_pressure=True, high_cholesterol=True,
            avoid_flagged_additives=True,
        )
        at = run("views/product.py", selected_code=sample_code, profile=profile)
        assert_clean(at, "product with profile")

    def test_guards_when_nothing_selected(self):
        at = run("views/product.py", selected_code=None)
        assert_clean(at, "product with no selection")
        assert at.info


class TestOtherPages:
    def test_recommend(self, sample_code):
        assert_clean(run("views/recommend.py", selected_code=sample_code), "recommend")

    def test_compare(self, sample_code):
        assert_clean(run("views/compare.py", compare_codes=[sample_code]), "compare")

    def test_compare_empty(self):
        assert_clean(run("views/compare.py", compare_codes=[]), "compare empty")

    def test_profile_page(self):
        assert_clean(run("views/profile_page.py"), "profile")

    def test_profile_guest_form_applies(self):
        at = run("views/profile_page.py")
        assert_clean(at, "profile load")
        assert at.multiselect, "no preference widgets rendered"

    def test_insights(self):
        assert_clean(run("views/insights.py"), "insights")
