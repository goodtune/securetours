"""Static-vs-built HTML alignment tests.

These compare normalized region extracts from each page in `../securetours/`
to the same page in `./site/`. They focus on equivalence, not equality:
class names differ between the two builds and that's fine — the tests assert
that the page exposes the same logical content in each region.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import PAGE_MAP
import extract as X


# Service-detail body content is JS-driven on the static site
# (filled at runtime from `js/translations.js`). The static HTML for service
# detail pages has empty hero label/title/sub and zero rendered cards. We
# bake the same content into Markdown front-matter — equal-or-better content
# availability — so we skip body comparisons but keep head/title/desc tests.
# Article detail pages have static HTML content, so they are NOT in this set.
JS_DRIVEN = {
    "svc_tours", "svc_egm", "svc_eta", "svc_pass_athlete", "svc_pass_artist",
    "svc_cc", "svc_bereavement", "svc_solo", "svc_stage",
}

# Static 404.html is bare — no nav, no footer, no description. Skip those
# tests for that page; we ship a properly chrome'd 404.
BARE_PAGES = {"notfound"}


# ---------------------------------------------------------------------------
# Build the parametrise list once, lazily, to skip pages that aren't yet
# present in either tree.
# ---------------------------------------------------------------------------

def _ids(pairs):
    return [p[0] for p in pairs]


# ---------------------------------------------------------------------------
# Site-wide invariants
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("page_key", [m[0] for m in PAGE_MAP])
def test_nav_top_links_match(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    if page_key in BARE_PAGES:
        pytest.skip("static 404 has no nav")
    s, b = all_pages[page_key]
    sn, bn = X.nav(s), X.nav(b)
    assert bn.logo_present, "built nav missing logo"
    assert bn.has_toggle, "built nav missing mobile toggle"
    assert bn.top_links == sn.top_links, (
        f"top nav links differ\n  static: {sn.top_links}\n  built : {bn.top_links}"
    )


@pytest.mark.parametrize("page_key", [m[0] for m in PAGE_MAP])
def test_nav_dropdown_matches(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    s, b = all_pages[page_key]
    sn, bn = X.nav(s), X.nav(b)
    assert bn.services_dropdown == sn.services_dropdown, (
        f"services dropdown differs\n  static: {sn.services_dropdown}\n  built : {bn.services_dropdown}"
    )


@pytest.mark.parametrize("page_key", [m[0] for m in PAGE_MAP])
def test_footer_columns_match(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    if page_key in BARE_PAGES:
        pytest.skip("static 404 has no footer")
    s, b = all_pages[page_key]
    sf, bf = X.footer(s), X.footer(b)
    assert bf.column_headings == sf.column_headings, (
        f"footer column headings differ\n  static: {sf.column_headings}\n  built : {bf.column_headings}"
    )
    for heading in sf.column_headings:
        s_items = sf.column_items.get(heading) or []
        b_items = bf.column_items.get(heading) or []
        # Static is inconsistent — some pages list the office location ("Australia-wide · NSW")
        # in the Contact column, others omit it. We standardize on the maximalist version.
        # Require every static item to appear in built; allow built to have extras.
        for item in s_items:
            assert item in b_items, (
                f"footer column '{heading}' missing item from static\n"
                f"  static: {s_items}\n"
                f"  built : {b_items}\n"
                f"  missing: {item!r}"
            )


@pytest.mark.parametrize("page_key", [m[0] for m in PAGE_MAP])
def test_footer_afs_strip(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    if page_key in BARE_PAGES:
        pytest.skip("static 404 has no footer")
    s, b = all_pages[page_key]
    sf, bf = X.footer(s), X.footer(b)
    assert bf.afs_division == sf.afs_division
    assert bf.afs_credentials == sf.afs_credentials


@pytest.mark.parametrize("page_key", [m[0] for m in PAGE_MAP])
def test_footer_bottom_text(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    if page_key in BARE_PAGES:
        pytest.skip("static 404 has no footer")
    s, b = all_pages[page_key]
    sf, bf = X.footer(s), X.footer(b)
    assert bf.bottom_text == sf.bottom_text


@pytest.mark.parametrize("page_key", [m[0] for m in PAGE_MAP])
def test_single_h1(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    s, b = all_pages[page_key]
    b_h1 = X.h1s(b)
    # Built site should always have exactly one h1 per page (head of content).
    # Static counts vary: JS-driven pages have an empty h1 in static HTML.
    assert len(b_h1) == 1, f"built {page_key} should have exactly one h1, got {b_h1}"


@pytest.mark.parametrize("page_key", [m[0] for m in PAGE_MAP])
def test_h1_text(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    if page_key in JS_DRIVEN:
        pytest.skip("static h1 is JS-injected; built has baked content")
    s, b = all_pages[page_key]
    assert X.h1s(b) == X.h1s(s)


@pytest.mark.parametrize("page_key", [m[0] for m in PAGE_MAP])
def test_meta_description_present(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    if page_key in BARE_PAGES:
        pytest.skip("static 404 has no description")
    s, b = all_pages[page_key]
    sh, bh = X.header(s), X.header(b)
    assert bh.description, f"built page {page_key} missing description"
    assert bh.description == sh.description, (
        f"description mismatch on {page_key}\n  static: {sh.description!r}\n  built : {bh.description!r}"
    )


@pytest.mark.parametrize("page_key", [m[0] for m in PAGE_MAP])
def test_canonical_present(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    s, b = all_pages[page_key]
    sh, bh = X.header(s), X.header(b)
    if not sh.canonical:
        pytest.skip("static has no canonical")
    assert bh.canonical, f"built page {page_key} missing canonical"


@pytest.mark.parametrize("page_key", [m[0] for m in PAGE_MAP])
def test_title_text(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    s, b = all_pages[page_key]
    sh, bh = X.header(s), X.header(b)
    assert bh.title == sh.title, (
        f"<title> mismatch on {page_key}\n  static: {sh.title!r}\n  built : {bh.title!r}"
    )


@pytest.mark.parametrize("page_key", [m[0] for m in PAGE_MAP])
def test_section_labels_match(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    if page_key in JS_DRIVEN:
        pytest.skip("static section labels are JS-injected; built has baked content")
    s, b = all_pages[page_key]
    s_labels = X.section_labels(s)
    b_labels = X.section_labels(b)
    assert b_labels == s_labels, (
        f"section labels differ on {page_key}\n  static: {s_labels}\n  built : {b_labels}"
    )


@pytest.mark.parametrize("page_key", [m[0] for m in PAGE_MAP])
def test_gold_rule_count(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    if page_key in JS_DRIVEN:
        pytest.skip("static gold-rules are JS-injected; built has baked content")
    s, b = all_pages[page_key]
    s_n = X.gold_rules(s)
    b_n = X.gold_rules(b)
    assert b_n == s_n, f"gold-rule count differs on {page_key}: static={s_n}, built={b_n}"


# ---------------------------------------------------------------------------
# Home page
# ---------------------------------------------------------------------------

def test_home_hero(all_pages):
    s, b = all_pages["home"]
    sh, bh = X.home_hero(s), X.home_hero(b)
    assert bh.tag_label == sh.tag_label
    assert bh.h1 == sh.h1
    assert bh.sub == sh.sub
    assert bh.cta_labels == sh.cta_labels
    assert bh.has_tagline_image == sh.has_tagline_image


def test_home_stats_bar(all_pages):
    s, b = all_pages["home"]
    s_stats = X.stats_bar(s)
    b_stats = X.stats_bar(b)
    assert b_stats == s_stats


def test_home_featured_solution(all_pages):
    s, b = all_pages["home"]
    sf, bf = X.featured_solution(s), X.featured_solution(b)
    assert sf is not None and bf is not None
    assert bf.title == sf.title
    assert bf.text == sf.text


def test_home_solutions_cards(all_pages):
    s, b = all_pages["home"]
    s_cards = X.home_solutions_cards(s)
    b_cards = X.home_solutions_cards(b)
    s_titles = [c.title for c in s_cards]
    b_titles = [c.title for c in b_cards]
    assert b_titles == s_titles, (
        f"home solutions card titles differ\n  static: {s_titles}\n  built : {b_titles}"
    )
    s_texts = [c.text for c in s_cards]
    b_texts = [c.text for c in b_cards]
    assert b_texts == s_texts, "home solutions card body text differs"


def test_home_about_strip(all_pages):
    s, b = all_pages["home"]
    sa, ba = X.home_about_strip(s), X.home_about_strip(b)
    assert ba.label == sa.label
    assert ba.title == sa.title
    assert ba.features == sa.features
    assert ba.badge_number == sa.badge_number
    assert ba.badge_label == sa.badge_label
    assert ba.cta_text == sa.cta_text


def test_home_why_grid(all_pages):
    s, b = all_pages["home"]
    s_items = X.why_grid(s)
    b_items = X.why_grid(b)
    s_pairs = [(i.title, i.text) for i in s_items]
    b_pairs = [(i.title, i.text) for i in b_items]
    assert b_pairs == s_pairs


def test_home_cta_band(all_pages):
    s, b = all_pages["home"]
    sc, bc = X.cta_band(s), X.cta_band(b)
    assert bc.title == sc.title
    assert bc.text == sc.text
    assert bc.cta_labels == sc.cta_labels


# ---------------------------------------------------------------------------
# Inner-page hero block — every page that has one in static
# ---------------------------------------------------------------------------

PAGES_WITH_PAGE_HERO = [
    "about",
    "services_index",
    "event_solutions",
    "articles_index",
    "resources",
    "contact",
    "svc_tours",
    "svc_egm",
    "svc_eta",
    "svc_pass_athlete",
    "svc_pass_artist",
    "svc_cc",
    "svc_bereavement",
    "svc_solo",
    "svc_stage",
    "art_carriageworks",
    "art_vivid",
    "art_gary",
    "art_janene",
    "art_matthew",
]


@pytest.mark.parametrize("page_key", PAGES_WITH_PAGE_HERO)
def test_page_hero_label(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    if page_key in JS_DRIVEN:
        pytest.skip("static hero label is JS-injected; built has baked content")
    s, b = all_pages[page_key]
    sp, bp = X.page_hero(s), X.page_hero(b)
    assert bp.label == sp.label, (
        f"page-hero label differs on {page_key}\n  static: {sp.label!r}\n  built : {bp.label!r}"
    )


@pytest.mark.parametrize("page_key", PAGES_WITH_PAGE_HERO)
def test_page_hero_title(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    if page_key in JS_DRIVEN:
        pytest.skip("static hero title is JS-injected; built has baked content")
    s, b = all_pages[page_key]
    sp, bp = X.page_hero(s), X.page_hero(b)
    assert bp.title == sp.title, (
        f"page-hero title differs on {page_key}\n  static: {sp.title!r}\n  built : {bp.title!r}"
    )


@pytest.mark.parametrize("page_key", PAGES_WITH_PAGE_HERO)
def test_page_hero_sub(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    if page_key in JS_DRIVEN:
        pytest.skip("static hero sub is JS-injected; built has baked content")
    s, b = all_pages[page_key]
    sp, bp = X.page_hero(s), X.page_hero(b)
    assert bp.sub == sp.sub, (
        f"page-hero sub differs on {page_key}\n  static: {sp.sub!r}\n  built : {bp.sub!r}"
    )
