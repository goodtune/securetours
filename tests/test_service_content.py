"""Service-detail content tests.

The canonical service content is the markdown collection in
`src/content/services/` — the same files the CMS edits. These tests
assert the built site bakes that content into HTML, i.e. our pages have
equal-or-better content availability than the JS-driven static prototype
for non-JS clients (search engines, archive tools, screen readers).
"""
from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

from conftest import normalize_text, text_of, BUILT_ROOT
import content_data as C
import extract as X


@pytest.fixture(scope="module")
def built_pages() -> dict[str, BeautifulSoup]:
    return {
        key: BeautifulSoup(
            (BUILT_ROOT / C.service_page_path(key)).read_text(encoding="utf-8"),
            "html.parser",
        )
        for key in C.SERVICES
    }


def _page_text(soup: BeautifulSoup) -> str:
    """Normalized text content of the main content area."""
    main = soup.find("main") or soup
    return normalize_text(main.get_text(" ", strip=True))


@pytest.mark.parametrize("key", C.SERVICES)
def test_service_hero_label(built_pages, key):
    bp = X.page_hero(built_pages[key])
    expected = C.strip_html(C.SERVICES[key]["hero_tag"])
    assert bp.label == expected, (
        f"hero label mismatch on {key}\n"
        f"  content: {expected!r}\n"
        f"  built  : {bp.label!r}"
    )


@pytest.mark.parametrize("key", C.SERVICES)
def test_service_hero_title(built_pages, key):
    bp = X.page_hero(built_pages[key])
    expected = C.strip_html(C.SERVICES[key]["title"])
    assert bp.title == expected, (
        f"hero title mismatch on {key}\n"
        f"  content: {expected!r}\n"
        f"  built  : {bp.title!r}"
    )


@pytest.mark.parametrize("key", C.SERVICES)
def test_service_hero_sub(built_pages, key):
    bp = X.page_hero(built_pages[key])
    expected = C.strip_html(C.SERVICES[key]["hero_sub"])
    assert bp.sub == expected, (
        f"hero sub mismatch on {key}\n"
        f"  content: {expected!r}\n"
        f"  built  : {bp.sub!r}"
    )


@pytest.mark.parametrize("key", C.SERVICES)
def test_service_lead_text(built_pages, key):
    lead = C.SERVICES[key].get("lead")
    if not lead:
        pytest.skip("no lead text in content")
    body = _page_text(built_pages[key])
    expected = normalize_text(lead)
    assert expected in body, (
        f"lead missing from {key}\n  expected substring: {expected[:100]!r}…"
    )


@pytest.mark.parametrize("key", C.SERVICES)
def test_service_all_features_present(built_pages, key):
    body = _page_text(built_pages[key])
    features = [f["text"] for f in C.SERVICES[key]["features"]]
    missing = [f for f in features if normalize_text(f) not in body]
    assert not missing, (
        f"features missing on {key}:\n  " + "\n  ".join(missing)
    )


@pytest.mark.parametrize("key", C.SERVICES)
def test_service_feature_count(built_pages, key):
    """Each canonical feature should appear once in the rendered list."""
    body = _page_text(built_pages[key])
    features = [f["text"] for f in C.SERVICES[key]["features"]]
    counts = {f: body.count(normalize_text(f)) for f in features}
    duplicated = {f: c for f, c in counts.items() if c > 1}
    assert not duplicated, (
        f"features duplicated on {key}: {duplicated}"
    )


@pytest.mark.parametrize("key", C.SERVICES)
def test_service_clients_present(built_pages, key):
    """The 'who this is for' list from the front matter must render."""
    clients = C.SERVICES[key].get("clients")
    if not clients:
        pytest.skip("no clients list in content")
    body = _page_text(built_pages[key])
    missing = [c for c in clients if normalize_text(c) not in body]
    assert not missing, (
        f"client types missing on {key}:\n  " + "\n  ".join(missing)
    )


@pytest.mark.parametrize("key", C.SERVICES)
def test_service_has_whats_included_section(built_pages, key):
    """Each service page should expose a 'What's Included' (or equivalent) section."""
    soup = built_pages[key]
    heading_texts = [text_of(h) for h in soup.find_all(["h2", "h3"])]
    # Service pages may use different headings for their "what's included"
    # equivalent. A custom features_heading from the front matter counts.
    expected_terms = [
        "what's included",
        "what we deliver",
        "service offerings",
        "what we offer",
        "reasons",
        "how it works",
    ]
    custom = C.SERVICES[key].get("features_heading")
    if custom:
        expected_terms.append(normalize_text(custom).lower())
    found = any(any(term in h.lower() for term in expected_terms) for h in heading_texts)
    assert found, f"{key} missing a 'what's included'-style heading; got {heading_texts}"


@pytest.mark.parametrize("key", C.SERVICES)
def test_service_has_cta_band(built_pages, key):
    """Each service page should end with a CTA band linking to contact."""
    soup = built_pages[key]
    band = soup.select_one(".st-band-navy, .cta-band")
    assert band is not None, f"{key} missing trailing CTA band"
    hrefs = [a.get("href", "") for a in band.find_all("a")]
    assert any("contact" in h for h in hrefs), (
        f"{key} CTA band missing link to contact; hrefs={hrefs}"
    )
