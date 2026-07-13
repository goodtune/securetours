"""Static-vs-built HTML alignment tests.

Two kinds of assertion live here, with different sources of truth:

- STRUCTURE (element presence, counts, nav/footer link sets, ordering)
  is compared against the customer-approved prototype in
  `../static-prototype/` — the frozen design contract.
- TEXT is compared against the content files in `src/content/` (via
  `content_data`), because that is what the CMS edits. A legitimate copy
  edit changes the content file and the built page together, so these
  tests stay green; a template that hardcodes or invents copy fails.

Code-owned strings (nav labels, footer link/column labels) have no
content file, so they remain pinned to the prototype.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import PAGE_MAP, normalize_text
import content_data as C
import extract as X


# Static 404.html is genuinely bare — no nav, no footer, no description.
# We ship a properly chrome'd 404; nothing to compare for that page.
BARE_PAGES = {"notfound"}


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


# Footer columns whose link labels live in SiteFooter.astro (code-owned) —
# these stay pinned to the prototype. The Contact column is content-owned
# (site.yaml) and is asserted against content below.
CODE_OWNED_FOOTER_COLUMNS = {"Tourism Solutions", "Company"}


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
    for heading in CODE_OWNED_FOOTER_COLUMNS & set(sf.column_headings):
        s_items = sf.column_items.get(heading) or []
        b_items = bf.column_items.get(heading) or []
        # Require every static item to appear in built; allow extras
        # (new services get added to the footer post-launch).
        for item in s_items:
            assert item in b_items, (
                f"footer column '{heading}' missing item from static\n"
                f"  static: {s_items}\n"
                f"  built : {b_items}\n"
                f"  missing: {item!r}"
            )


@pytest.mark.parametrize("page_key", [m[0] for m in PAGE_MAP])
def test_footer_contact_details(all_pages, page_key):
    """Footer contact details come from site.yaml (CMS-edited)."""
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    if page_key in BARE_PAGES:
        pytest.skip("static 404 has no footer")
    _, b = all_pages[page_key]
    bf = X.footer(b)
    items = bf.column_items.get("Contact") or []
    footer = C.SITE["footer"]
    for value in (footer["phone"], footer["email"]):
        assert normalize_text(value) in items, (
            f"footer Contact column missing {value!r} from site.yaml\n  built: {items}"
        )


@pytest.mark.parametrize("page_key", [m[0] for m in PAGE_MAP])
def test_footer_afs_strip(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    if page_key in BARE_PAGES:
        pytest.skip("static 404 has no footer")
    _, b = all_pages[page_key]
    bf = X.footer(b)
    strip = C.SITE["afs_strip"]
    assert bf.afs_division == C.strip_html(strip["division"])
    assert bf.afs_credentials == C.strip_html(strip["credentials"])


@pytest.mark.parametrize("page_key", [m[0] for m in PAGE_MAP])
def test_footer_bottom_text(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    if page_key in BARE_PAGES:
        pytest.skip("static 404 has no footer")
    _, b = all_pages[page_key]
    bf = X.footer(b)
    copyright_line = normalize_text(C.SITE["footer"]["copyright"])
    assert copyright_line in bf.bottom_text, (
        f"footer bottom text missing copyright from site.yaml\n"
        f"  expected: {copyright_line!r}\n  built: {bf.bottom_text!r}"
    )


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
    _, b = all_pages[page_key]
    assert X.h1s(b) == [C.expected_h1(page_key)], (
        f"h1 differs from content file on {page_key}"
    )


@pytest.mark.parametrize("page_key", [m[0] for m in PAGE_MAP])
def test_meta_description(all_pages, page_key):
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    _, b = all_pages[page_key]
    bh = X.header(b)
    _, expected = C.expected_header(page_key)
    assert bh.description, f"built page {page_key} missing description"
    assert bh.description == expected, (
        f"description differs from content file on {page_key}\n"
        f"  content: {expected!r}\n  built  : {bh.description!r}"
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
    _, b = all_pages[page_key]
    bh = X.header(b)
    expected, _ = C.expected_header(page_key)
    assert bh.title == expected, (
        f"<title> differs from content file on {page_key}\n"
        f"  content: {expected!r}\n  built  : {bh.title!r}"
    )


@pytest.mark.parametrize("page_key", [m[0] for m in PAGE_MAP])
def test_section_labels_match(all_pages, page_key):
    """Structure: at least as many section labels as the prototype.
    Text: every label must come from the page's content files (or be a
    code-owned label unchanged from the prototype)."""
    if page_key not in all_pages:
        pytest.skip("page missing in one tree")
    s, b = all_pages[page_key]
    s_labels = X.section_labels(s)
    b_labels = X.section_labels(b)
    assert len(b_labels) >= len(s_labels), (
        f"section label count regressed on {page_key}\n"
        f"  static: {s_labels}\n  built : {b_labels}"
    )
    allowed = C.content_strings(page_key) | set(s_labels)
    unknown = [l for l in b_labels if l not in allowed]
    assert not unknown, (
        f"section labels on {page_key} not sourced from content files "
        f"(or prototype): {unknown}"
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
# Home page — text vs src/content/pages/home.yaml (+ services collection)
# ---------------------------------------------------------------------------

def test_home_hero(all_pages):
    s, b = all_pages["home"]
    sh, bh = X.home_hero(s), X.home_hero(b)
    hero = C.PAGES["home"]["hero"]
    assert bh.tag_label == normalize_text(hero["tag"])
    assert bh.h1 == C.strip_html(hero["title"])
    assert bh.sub == normalize_text(hero["sub"])
    assert bh.cta_labels == [hero["cta_primary"]["label"], hero["cta_secondary"]["label"]]
    assert bh.has_tagline_image == sh.has_tagline_image


def test_home_stats_bar(all_pages):
    _, b = all_pages["home"]
    b_stats = X.stats_bar(b)
    expected = [
        (normalize_text(s["number"]), normalize_text(s["label"]))
        for s in C.PAGES["home"]["stats"]
    ]
    assert b_stats == expected


def test_home_featured_solution(all_pages):
    _, b = all_pages["home"]
    bf = X.featured_solution(b)
    assert bf is not None
    tours = C.SERVICES["svc_tours"]
    assert bf.title == C.strip_html(tours["title"])
    assert bf.text == normalize_text(tours["home_card"]["body"])


def test_home_solutions_cards(all_pages):
    """Every non-flagship service's home card (from the services
    collection) must appear in the home grid, and nothing else."""
    _, b = all_pages["home"]
    b_cards = X.home_solutions_cards(b)
    expected = {}
    for key, svc in C.SERVICES.items():
        if key == "svc_tours":
            continue  # flagship — rendered as the featured panel
        card = svc["home_card"]
        title = C.strip_html(card.get("title") or svc["title"])
        expected[title] = normalize_text(card["body"])
    b_map = {c.title: c.text for c in b_cards}
    assert set(b_map) == set(expected), (
        f"home solutions cards differ from services collection\n"
        f"  content: {sorted(expected)}\n  built : {sorted(b_map)}"
    )
    for title, body in expected.items():
        assert b_map[title] == body, f"home card body differs for {title!r}"


def test_home_about_strip(all_pages):
    _, b = all_pages["home"]
    ba = X.home_about_strip(b)
    about = C.PAGES["home"]["about"]
    assert ba.label == normalize_text(about["label"])
    assert ba.title == normalize_text(about["title"])
    assert ba.features == [normalize_text(f) for f in about["features"]]
    assert ba.badge_number == normalize_text(about["badge"]["number"])
    assert ba.badge_label == normalize_text(about["badge"]["label"])
    assert ba.cta_text == normalize_text(about["cta_label"])


def test_home_about_strip_body(all_pages):
    _, b = all_pages["home"]
    ba = X.home_about_strip(b)
    assert ba.body == normalize_text(C.PAGES["home"]["about"]["text"])


def test_home_why_grid(all_pages):
    _, b = all_pages["home"]
    b_items = X.why_grid(b)
    b_pairs = [(i.title, i.text) for i in b_items]
    expected = [
        (normalize_text(i["title"]), normalize_text(i["text"]))
        for i in C.PAGES["home"]["why"]["items"]
    ]
    assert b_pairs == expected


def test_home_cta_band(all_pages):
    _, b = all_pages["home"]
    bc = X.cta_band(b)
    cta = C.SITE["cta_band"]
    assert bc.title == normalize_text(cta["title"])
    assert bc.text == normalize_text(cta["body"])
    assert bc.cta_labels == [cta["primary"]["label"], cta["outline"]["label"]]


# ---------------------------------------------------------------------------
# Inner-page hero block — text vs the page's content file
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
    "svc_stage",
    "svc_bereavement",
    "svc_solo",
    "svc_scout",
    "art_carriageworks",
    "art_vivid",
    "art_gary",
    "art_janene",
    "art_matthew",
]


@pytest.fixture(scope="session")
def hero_pages(all_pages, built_root):
    """all_pages plus built-only soups for pages outside PAGE_MAP
    (svc_stage was rewritten post-launch; svc_scout is post-launch)."""
    from bs4 import BeautifulSoup

    pages = {k: b for k, (_, b) in all_pages.items()}
    for key in ("svc_stage", "svc_scout"):
        path = built_root / C.service_page_path(key)
        if path.exists():
            pages[key] = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    return pages


@pytest.mark.parametrize("page_key", PAGES_WITH_PAGE_HERO)
def test_page_hero_label(hero_pages, page_key):
    if page_key not in hero_pages:
        pytest.skip("page missing")
    bp = X.page_hero(hero_pages[page_key])
    label, _, _ = C.expected_page_hero(page_key)
    assert bp.label == label, (
        f"page-hero label differs from content on {page_key}\n"
        f"  content: {label!r}\n  built  : {bp.label!r}"
    )


@pytest.mark.parametrize("page_key", PAGES_WITH_PAGE_HERO)
def test_page_hero_title(hero_pages, page_key):
    if page_key not in hero_pages:
        pytest.skip("page missing")
    bp = X.page_hero(hero_pages[page_key])
    _, title, _ = C.expected_page_hero(page_key)
    assert bp.title == title, (
        f"page-hero title differs from content on {page_key}\n"
        f"  content: {title!r}\n  built  : {bp.title!r}"
    )


@pytest.mark.parametrize("page_key", PAGES_WITH_PAGE_HERO)
def test_page_hero_sub(hero_pages, page_key):
    if page_key not in hero_pages:
        pytest.skip("page missing")
    bp = X.page_hero(hero_pages[page_key])
    _, _, sub = C.expected_page_hero(page_key)
    assert bp.sub == sub, (
        f"page-hero sub differs from content on {page_key}\n"
        f"  content: {sub!r}\n  built  : {bp.sub!r}"
    )
