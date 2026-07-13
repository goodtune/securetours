"""Body-section alignment tests.

Structure (H2 counts, links, form fields) is compared against the static
prototype; text is compared against the content files in `src/content/`
(what the CMS edits). An H2 is acceptable if it comes from the page's
content files, or is a code-owned heading unchanged from the prototype.
"""
from __future__ import annotations

import pytest

from conftest import normalize_text, text_of
import content_data as C
import extract as X


def _assert_h2s_from_content(page_key: str, s_h2: list[str], b_h2: list[str]):
    assert len(b_h2) >= len(s_h2), (
        f"{page_key} H2 count regressed\n  static: {s_h2}\n  built : {b_h2}"
    )
    allowed = C.content_strings(page_key) | set(s_h2)
    unknown = [h for h in b_h2 if h not in allowed]
    assert not unknown, (
        f"{page_key} H2s not sourced from content files (or prototype): {unknown}"
    )


# ---------------------------------------------------------------------------
# About page
# ---------------------------------------------------------------------------

def test_about_h2_outline(all_pages):
    s, b = all_pages["about"]
    _assert_h2s_from_content("about", X.h2s(s), X.h2s(b))


def test_about_values_present(all_pages):
    _, b = all_pages["about"]
    b_text = normalize_text(b.get_text(" ", strip=True))
    for item in C.PAGES["about"]["values"]["items"]:
        title = normalize_text(item["title"])
        assert title in b_text, f"built missing value card {title!r}"


def test_about_clients_list(all_pages):
    _, b = all_pages["about"]
    b_text = normalize_text(b.get_text(" ", strip=True))
    for client in C.PAGES["about"]["clients"]["items"]:
        assert normalize_text(client) in b_text, (
            f"built missing client type {client!r}"
        )


# ---------------------------------------------------------------------------
# Articles index — content sections
# ---------------------------------------------------------------------------

def test_articles_index_h2_outline(all_pages):
    s, b = all_pages["articles_index"]
    s_h2 = [
        text_of(h) for h in s.find_all("h2")
        if "sr-only" not in (h.get("class") or [])
    ]
    _assert_h2s_from_content("articles_index", s_h2, X.h2s(b))


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


def test_articles_index_testimonial_cards(all_pages):
    """Testimonial card copy comes from articles-index.yaml."""
    _, b = all_pages["articles_index"]
    b_text = normalize_text(b.get_text(" ", strip=True))
    for card in C.PAGES["articles_index"]["testimonials"]["cards"]:
        for field in ("name", "quote"):
            value = C.strip_html(card[field])
            assert value in b_text, (
                f"articles_index missing testimonial {field}: {value[:60]!r}…"
            )


# ---------------------------------------------------------------------------
# Event Solutions — content
# ---------------------------------------------------------------------------

def test_event_solutions_h2_outline(all_pages):
    s, b = all_pages["event_solutions"]
    _assert_h2s_from_content("event_solutions", X.h2s(s), X.h2s(b))


def test_event_solutions_offering_cards(all_pages):
    """Offering card copy comes from event-solutions.yaml."""
    _, b = all_pages["event_solutions"]
    b_text = normalize_text(b.get_text(" ", strip=True))
    for event in C.PAGES["event_solutions"]["offerings"]["events"]:
        title = normalize_text(event["title"])
        assert title in b_text, f"event_solutions missing offering {title!r}"


# ---------------------------------------------------------------------------
# Resources page
# ---------------------------------------------------------------------------

def test_resources_lists_downloads(all_pages):
    """Every category heading and card name from resources.yaml renders."""
    _, b = all_pages["resources"]
    b_text = normalize_text(b.get_text(" ", strip=True))
    for cat in C.PAGES["resources"]["categories"]:
        heading = normalize_text(cat["heading"])
        assert heading in b_text, f"resources missing category {heading!r}"
        for card in cat["cards"]:
            name = normalize_text(card["name"])
            assert name in b_text, f"resources missing download {name!r}"


def test_resources_download_links(all_pages):
    """Every download card with a file link must render as an anchor."""
    _, b = all_pages["resources"]
    hrefs = {a.get("href", "") for a in b.find_all("a")}
    for cat in C.PAGES["resources"]["categories"]:
        for card in cat["cards"]:
            if card.get("href"):
                assert card["href"] in hrefs, (
                    f"resources missing link to {card['href']!r}"
                )


# ---------------------------------------------------------------------------
# Contact page
# ---------------------------------------------------------------------------

def test_contact_phone_email_present(all_pages):
    _, b = all_pages["contact"]
    b_text = normalize_text(b.get_text(" ", strip=True))
    info = C.PAGES["contact"]["info"]
    assert normalize_text(info["phone"]) in b_text
    assert normalize_text(info["email"]) in b_text


def test_contact_form_present(all_pages):
    _, b = all_pages["contact"]
    form = b.find("form")
    assert form is not None, "contact form missing"
    inputs = form.find_all(["input", "textarea", "select"])
    names = {i.get("name", "") for i in inputs}
    for required in {"first_name", "last_name", "email", "phone", "service", "message"}:
        assert required in names, f"contact form missing field '{required}'"


# ---------------------------------------------------------------------------
# Article detail pages — text vs src/content/articles/*.yaml
# ---------------------------------------------------------------------------

ARTICLE_KEYS = ["art_carriageworks", "art_vivid", "art_gary", "art_janene", "art_matthew"]


@pytest.mark.parametrize("page_key", ARTICLE_KEYS)
def test_article_h1(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    _, b = all_pages[page_key]
    assert X.h1s(b) == [C.expected_h1(page_key)]


@pytest.mark.parametrize("page_key", ARTICLE_KEYS)
def test_article_hero_sub(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    _, b = all_pages[page_key]
    bp = X.page_hero(b)
    _, _, sub = C.expected_page_hero(page_key)
    assert bp.sub == sub


@pytest.mark.parametrize("page_key", ARTICLE_KEYS)
def test_article_body_text_from_content(all_pages, page_key):
    """Spot-check that article body copy renders from the YAML: every
    paragraph-bearing list in the article file must appear in the page."""
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    _, b = all_pages[page_key]
    b_text = normalize_text(b.get_text(" ", strip=True))
    article = C.ARTICLES[page_key]

    def paragraphs(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in ("paragraphs", "bullets", "items") and isinstance(v, list):
                    for item in v:
                        if isinstance(item, str):
                            yield item
                else:
                    yield from paragraphs(v)
        elif isinstance(node, list):
            for item in node:
                yield from paragraphs(item)

    missing = [
        p for p in paragraphs(article)
        if C.strip_html(p) not in b_text
    ]
    assert not missing, (
        f"{page_key} body text missing from built page:\n  "
        + "\n  ".join(m[:80] for m in missing)
    )
