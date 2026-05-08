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


# Static 404.html is genuinely bare — no nav, no footer, no description.
# We ship a properly chrome'd 404; nothing to compare for that page.
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
    # Built can add new services to the dropdown that weren't in the
    # prototype (e.g. S.C.O.U.T. added post-launch). Require every
    # static dropdown item to appear in built; allow extras.
    s_set, b_set = set(sn.services_dropdown), set(bn.services_dropdown)
    missing = s_set - b_set
    assert not missing, (
        f"services dropdown missing items from static on {page_key}\n"
        f"  static: {sn.services_dropdown}\n"
        f"  built : {bn.services_dropdown}\n"
        f"  missing: {sorted(missing)}"
    )


# Intentional divergences from the prototype, captured as content edits land.
# These are items the static prototype contains but the built site (post-launch)
# deliberately does not. Anything else missing is still a real failure.
FOOTER_INTENTIONAL_REMOVALS: dict[str, list[str]] = {
    # Client requested the location row collapse "Australia-wide · NSW" to
    # "Australia Wide" — strict superstring substitution would break the
    # extraction, so we just whitelist the old item as expected-absent.
    "Contact": ["Australia-wide · NSW"],
}


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
        intentional = FOOTER_INTENTIONAL_REMOVALS.get(heading, [])
        # Static is inconsistent — some pages list the office location in the
        # Contact column, others omit it. We standardize on the maximalist
        # version. Require every static item (minus intentional removals) to
        # appear in built; allow built to have extras.
        for item in s_items:
            if item in intentional:
                continue
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
    s, b = all_pages[page_key]
    s_n = X.gold_rules(s)
    b_n = X.gold_rules(b)
    # Built can add new sections (e.g. FAQ blocks on service detail pages)
    # that introduce additional gold-rules. The original test was a strict
    # equality gate during the 1:1 port; post-launch we relax to "at least
    # as many" so adding an FAQ section is not a regression.
    assert b_n >= s_n, f"gold-rule count regressed on {page_key}: static={s_n}, built={b_n}"


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
    # Built can add new service cards (e.g. SCOUT) to the home grid.
    # Require every static card title to appear in built; allow extras.
    s_titles = [c.title for c in s_cards]
    b_titles = [c.title for c in b_cards]
    missing_titles = [t for t in s_titles if t not in b_titles]
    assert not missing_titles, (
        f"home solutions card titles missing from built\n"
        f"  static: {s_titles}\n"
        f"  built : {b_titles}\n"
        f"  missing: {missing_titles}"
    )
    s_texts = [c.text for c in s_cards]
    b_texts = [c.text for c in b_cards]
    missing_texts = [t for t in s_texts if t not in b_texts]
    assert not missing_texts, (
        f"home solutions card body text missing from built: {missing_texts}"
    )


def test_home_about_strip(all_pages):
    s, b = all_pages["home"]
    sa, ba = X.home_about_strip(s), X.home_about_strip(b)
    assert ba.label == sa.label
    assert ba.title == sa.title
    assert ba.features == sa.features
    assert ba.badge_number == sa.badge_number
    assert ba.badge_label == sa.badge_label
    assert ba.cta_text == sa.cta_text


def test_home_about_strip_body_includes_static(all_pages):
    """Built body paragraph must include all of static's body text.

    Static HTML has only the first sentence (rest is JS-injected from
    `about_text` translation). Built bakes the canonical full text.
    Verify built is a superset.
    """
    s, b = all_pages["home"]
    sa, ba = X.home_about_strip(s), X.home_about_strip(b)
    assert sa.body, "static has no about-strip body text"
    assert sa.body in ba.body, (
        f"built about-strip body missing static text\n"
        f"  static: {sa.body!r}\n"
        f"  built : {ba.body!r}"
    )


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
    s, b = all_pages[page_key]
    sp, bp = X.page_hero(s), X.page_hero(b)
    assert bp.label == sp.label, (
        f"page-hero label differs on {page_key}\n  static: {sp.label!r}\n  built : {bp.label!r}"
    )


@pytest.mark.parametrize("page_key", PAGES_WITH_PAGE_HERO)
def test_page_hero_title(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    s, b = all_pages[page_key]
    sp, bp = X.page_hero(s), X.page_hero(b)
    assert bp.title == sp.title, (
        f"page-hero title differs on {page_key}\n  static: {sp.title!r}\n  built : {bp.title!r}"
    )


@pytest.mark.parametrize("page_key", PAGES_WITH_PAGE_HERO)
def test_page_hero_sub(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    s, b = all_pages[page_key]
    sp, bp = X.page_hero(s), X.page_hero(b)
    assert bp.sub == sp.sub, (
        f"page-hero sub differs on {page_key}\n  static: {sp.sub!r}\n  built : {bp.sub!r}"
    )
