"""Service-detail content tests.

Static service-detail pages are JS-driven and contain no rendered content
in their HTML. The canonical content lives in `js/translations.js`. These
tests assert that the built site bakes that canonical content into HTML —
i.e. our pages have equal-or-better content availability than the static
site for non-JS clients (search engines, archive tools, screen readers).
"""
from __future__ import annotations

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from conftest import normalize_text, text_of, BUILT_ROOT
import extract as X
from translations_data import SERVICE_PAGES


@pytest.fixture(scope="module")
def built_pages() -> dict[str, BeautifulSoup]:
    return {
        key: BeautifulSoup(
            (BUILT_ROOT / spec["page_path"]).read_text(encoding="utf-8"),
            "html.parser",
        )
        for key, spec in SERVICE_PAGES.items()
    }


def _page_text(soup: BeautifulSoup) -> str:
    """Normalized text content of the main content area."""
    main = soup.find("main") or soup
    return normalize_text(main.get_text(" ", strip=True))


@pytest.mark.parametrize("key,spec", SERVICE_PAGES.items())
def test_service_hero_label(built_pages, key, spec):
    bp = X.page_hero(built_pages[key])
    assert bp.label == spec["hero_label"], (
        f"hero label mismatch on {key}\n"
        f"  expected: {spec['hero_label']!r}\n"
        f"  built   : {bp.label!r}"
    )


@pytest.mark.parametrize("key,spec", SERVICE_PAGES.items())
def test_service_hero_title(built_pages, key, spec):
    bp = X.page_hero(built_pages[key])
    assert bp.title == spec["title"], (
        f"hero title mismatch on {key}\n"
        f"  expected: {spec['title']!r}\n"
        f"  built   : {bp.title!r}"
    )


@pytest.mark.parametrize("key,spec", SERVICE_PAGES.items())
def test_service_hero_sub(built_pages, key, spec):
    bp = X.page_hero(built_pages[key])
    assert bp.sub == spec["sub"], (
        f"hero sub mismatch on {key}\n"
        f"  expected: {spec['sub']!r}\n"
        f"  built   : {bp.sub!r}"
    )


@pytest.mark.parametrize("key,spec", SERVICE_PAGES.items())
def test_service_lead_text(built_pages, key, spec):
    if "lead" not in spec:
        pytest.skip("no lead text in canonical")
    body = _page_text(built_pages[key])
    expected = normalize_text(spec["lead"])
    assert expected in body, (
        f"lead missing from {key}\n  expected substring: {expected!r}"
    )


@pytest.mark.parametrize("key,spec", SERVICE_PAGES.items())
def test_service_all_features_present(built_pages, key, spec):
    body = _page_text(built_pages[key])
    missing = [f for f in spec["features"] if normalize_text(f) not in body]
    assert not missing, (
        f"features missing on {key}:\n  " + "\n  ".join(missing)
    )


@pytest.mark.parametrize("key,spec", SERVICE_PAGES.items())
def test_service_feature_count(built_pages, key, spec):
    """Each canonical feature should appear once in the rendered list."""
    soup = built_pages[key]
    body = _page_text(soup)
    counts = {f: body.count(normalize_text(f)) for f in spec["features"]}
    duplicated = {f: c for f, c in counts.items() if c > 1}
    assert not duplicated, (
        f"features duplicated on {key}: {duplicated}"
    )
