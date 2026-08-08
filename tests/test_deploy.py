"""Guards against local/deployed environment drift.

Two deployment failures came from the same root cause: the environment the app
was developed in differed from the one it ran in.

  * `LOAD fts` succeeded locally because building the catalog installs the
    extension, and crashed on a fresh Space container.
  * `st.button(width=...)` worked against Streamlit 1.61 locally while the
    Space installed 1.40 from README frontmatter, where the argument does
    not exist.

Neither is visible from reading the code. Both are cheap to assert.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"
REQUIREMENTS = REPO_ROOT / "requirements.txt"


def frontmatter_value(key: str) -> str | None:
    """Read a key from the README's YAML frontmatter, which configures the Space."""
    text = README.read_text()
    match = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not match:
        return None
    found = re.search(rf"^{key}:\s*(.+)$", match.group(1), re.M)
    return found.group(1).strip() if found else None


def pinned_version(package: str) -> str | None:
    for line in REQUIREMENTS.read_text().splitlines():
        line = line.split("#")[0].strip()
        if line.lower().startswith(f"{package}=="):
            return line.split("==", 1)[1].strip()
    return None


class TestStreamlitVersionParity:
    def test_readme_declares_an_sdk_version(self):
        assert frontmatter_value("sdk_version"), "Spaces needs sdk_version in README"

    def test_installed_matches_readme(self):
        """The Space installs the README version, so develop against it."""
        assert st.__version__ == frontmatter_value("sdk_version"), (
            f"installed Streamlit {st.__version__} but README declares "
            f"{frontmatter_value('sdk_version')}; the deployed app would differ "
            "from the one tested here"
        )

    def test_requirements_matches_readme(self):
        assert pinned_version("streamlit") == frontmatter_value("sdk_version")


class TestWidgetApiAvailability:
    """Every widget argument the views use must exist in the pinned Streamlit."""

    def test_button_supports_width(self):
        assert "width" in inspect.signature(st.button).parameters

    def test_plotly_chart_supports_width(self):
        assert "width" in inspect.signature(st.plotly_chart).parameters

    def test_navigation_api_exists(self):
        assert hasattr(st, "navigation") and hasattr(st, "Page")

    @pytest.mark.parametrize("name", ["toast", "switch_page", "form_submit_button"])
    def test_apis_used_by_views_exist(self, name):
        assert hasattr(st, name)


class TestSpaceConfig:
    def test_app_file_points_at_an_existing_file(self):
        app_file = frontmatter_value("app_file")
        assert app_file, "Spaces needs app_file in README"
        assert (REPO_ROOT / app_file).is_file(), f"{app_file} does not exist"

    def test_runtime_data_files_are_present(self):
        """These are easy to forget and only fail once deployed."""
        for path in ("data/additives.json", "data/nutriscore_categories.json",
                     "pipeline/config.py", "styles.css", ".streamlit/config.toml"):
            assert (REPO_ROOT / path).is_file(), f"{path} is missing"

    def test_no_secrets_file_in_the_tree(self):
        """A committed secrets.toml is how the original credential leaked."""
        assert not (REPO_ROOT / ".streamlit" / "secrets.toml").exists(), (
            "delete .streamlit/secrets.toml — set MONGODB_URI as a Space secret"
        )

    def test_removed_dependencies_are_not_referenced(self):
        text = REQUIREMENTS.read_text().lower()
        for package in ("faiss", "sentence-transformers", "torch", "gdown", "passlib"):
            assert f"\n{package}" not in text, f"{package} should no longer be required"
