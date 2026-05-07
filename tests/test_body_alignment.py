"""Body-section alignment tests for pages that are NOT JS-driven.

These compare the rendered body text of static pages to built pages —
H2 outlines, key paragraphs, list items.
"""
from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

from conftest import normalize_text, text_of, texts_of
import extract as X


# ---------------------------------------------------------------------------
# About page
# ---------------------------------------------------------------------------

def test_about_h2_outline(all_pages):
    s, b = all_pages["about"]
    s_h2 = X.h2s(s)
    b_h2 = X.h2s(b)
    assert b_h2 == s_h2, (
        f"about H2 outline differs\n  static: {s_h2}\n  built : {b_h2}"
    )


def test_about_values_present(all_pages):
    s, b = all_pages["about"]
    # Static "Our Values" has three value cards. Confirm all three titles are present.
    s_text = normalize_text(s.get_text(" ", strip=True))
    b_text = normalize_text(b.get_text(" ", strip=True))
    for v in ["Safety as Standard", "Discreet Professionalism", "Genuine Care"]:
        assert v in s_text, f"static missing '{v}'"
        assert v in b_text, f"built missing '{v}'"


def test_about_clients_list(all_pages):
    s, b = all_pages["about"]
    s_text = normalize_text(s.get_text(" ", strip=True))
    b_text = normalize_text(b.get_text(" ", strip=True))
    static_clients = [
        "International tourists & inbound groups",
        "Corporate executives & delegations",
        "Elite athletes & sports teams",
        "Touring musicians & performing artists",
        "Government & diplomatic visitors",
        "Families & student groups",
    ]
    for client in static_clients:
        # Static is JS-driven for "Who We Serve" — only check built.
        assert client in b_text, f"built missing client type '{client}'"


# ---------------------------------------------------------------------------
# Articles index — content sections
# ---------------------------------------------------------------------------

def test_articles_index_h2_outline(all_pages):
    s, b = all_pages["articles_index"]
    # Filter out screen-reader-only H2s (e.g. static's "Content Library" .sr-only)
    s_h2 = [
        text_of(h) for h in s.find_all("h2")
        if "sr-only" not in (h.get("class") or [])
    ]
    b_h2 = X.h2s(b)
    for h in s_h2:
        assert any(h.lower() in bh.lower() for bh in b_h2), (
            f"articles_index missing H2 from static: {h!r}\n  built: {b_h2}"
        )


def test_articles_index_links_to_each_article(all_pages):
    _, b = all_pages["articles_index"]
    # Each article detail page must be linked from the articles index
    expected = [
        "carriageworks",
        "vivid-sydney",
        "gary-oriordan-endorsement",
        "janene-rees-endorsement",
        "matthew-harrison-profile",
    ]
    hrefs = [a.get("href", "") for a in b.find_all("a")]
    for slug in expected:
        assert any(slug in h for h in hrefs), (
            f"articles_index missing link to {slug}"
        )


# ---------------------------------------------------------------------------
# Event Solutions — content
# ---------------------------------------------------------------------------

def test_event_solutions_h2_outline(all_pages):
    s, b = all_pages["event_solutions"]
    s_h2 = X.h2s(s)
    b_h2 = X.h2s(b)
    assert b_h2 == s_h2, (
        f"event_solutions H2 outline differs\n  static: {s_h2}\n  built : {b_h2}"
    )


# ---------------------------------------------------------------------------
# Resources page
# ---------------------------------------------------------------------------

def test_resources_lists_brochures(all_pages):
    _, b = all_pages["resources"]
    text = normalize_text(b.get_text(" ", strip=True))
    # The static resources page has these brochure references; verify built does too.
    expected_keywords = [
        "Brochures",
        "Mandarin",
    ]
    for kw in expected_keywords:
        assert kw in text, f"resources missing keyword '{kw}'"


# ---------------------------------------------------------------------------
# Contact page
# ---------------------------------------------------------------------------

def test_contact_phone_email_present(all_pages):
    s, b = all_pages["contact"]
    b_text = normalize_text(b.get_text(" ", strip=True))
    assert "+61 414 499 778" in b_text
    assert "enquiries@securetours.com.au" in b_text


def test_contact_form_present(all_pages):
    _, b = all_pages["contact"]
    form = b.find("form")
    assert form is not None, "contact form missing"
    inputs = form.find_all(["input", "textarea", "select"])
    names = {i.get("name", "") for i in inputs}
    for required in {"first_name", "last_name", "email", "phone", "service", "message"}:
        assert required in names, f"contact form missing field '{required}'"


# ---------------------------------------------------------------------------
# Article detail pages (static is hardcoded for these)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "page_key",
    ["art_carriageworks", "art_vivid", "art_gary", "art_janene", "art_matthew"],
)
def test_article_h1_matches_static(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    s, b = all_pages[page_key]
    assert X.h1s(b) == X.h1s(s)


@pytest.mark.parametrize(
    "page_key",
    ["art_carriageworks", "art_vivid", "art_gary", "art_janene", "art_matthew"],
)
def test_article_hero_sub_matches_static(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    s, b = all_pages[page_key]
    sp, bp = X.page_hero(s), X.page_hero(b)
    assert bp.sub == sp.sub
