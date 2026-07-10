"""Tolerant feature extraction from a page.

Each extractor returns a normalized representation of one logical UI region.
The same extractor is run against the static site and the Zensical build —
they should return equivalent values regardless of the underlying class names.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Tag

from conftest import normalize_text, text_of, texts_of


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def first(soup_or_tag, *selectors) -> Tag | None:
    """Return the first match for any of the selectors."""
    for sel in selectors:
        node = soup_or_tag.select_one(sel)
        if node is not None:
            return node
    return None


def all_(soup_or_tag, *selectors) -> list[Tag]:
    """Return every match for any of the selectors (flattened, in DOM order)."""
    results: list[Tag] = []
    seen = set()
    for sel in selectors:
        for n in soup_or_tag.select(sel):
            if id(n) in seen:
                continue
            seen.add(id(n))
            results.append(n)
    return results


def has_any(soup_or_tag, *selectors) -> bool:
    return first(soup_or_tag, *selectors) is not None


# ---------------------------------------------------------------------------
# Region extractors
# ---------------------------------------------------------------------------

@dataclass
class HeaderInfo:
    title: str
    description: str
    canonical: str
    has_og_title: bool
    has_og_description: bool
    has_favicon: bool


def header(soup: BeautifulSoup) -> HeaderInfo:
    title = text_of(soup.find("title"))
    desc = soup.find("meta", attrs={"name": "description"})
    canon = soup.find("link", attrs={"rel": "canonical"})
    return HeaderInfo(
        title=title,
        description=normalize_text(desc.get("content") if desc else ""),
        canonical=(canon.get("href") if canon else "") or "",
        has_og_title=soup.find("meta", attrs={"property": "og:title"}) is not None,
        has_og_description=soup.find("meta", attrs={"property": "og:description"}) is not None,
        has_favicon=soup.find("link", attrs={"rel": "icon"}) is not None,
    )


@dataclass
class NavInfo:
    logo_present: bool
    has_toggle: bool
    top_links: list[str]
    services_dropdown: list[str]


def nav(soup: BeautifulSoup) -> NavInfo:
    nav_el = first(soup, "nav.site-nav")
    if nav_el is None:
        return NavInfo(False, False, [], [])
    logo = first(nav_el, ".nav-logo img")
    toggle = first(nav_el, ".nav-toggle")
    links = first(nav_el, ".nav-links")
    top_links: list[str] = []
    sub_links: list[str] = []
    if links is not None:
        for li in links.find_all("li", recursive=False):
            a = li.find("a", recursive=False)
            if a is not None:
                top_links.append(text_of(a))
            sub = li.find("ul", recursive=False)
            if sub is not None:
                sub_links = [text_of(x) for x in sub.find_all("a")]
    return NavInfo(logo is not None, toggle is not None, top_links, sub_links)


@dataclass
class HeroInfo:
    tag_label: str
    h1: str
    sub: str
    cta_labels: list[str]
    has_tagline_image: bool


def home_hero(soup: BeautifulSoup) -> HeroInfo:
    """Home-page hero (index)."""
    region = first(
        soup,
        "section.hero",
        ".st-hero",
        ".home-hero",
    )
    if region is None:
        return HeroInfo("", "", "", [], False)
    tag = first(region, ".hero-tag", ".st-tag", ".st-hero-tag")
    h1 = first(region, "h1")
    sub = first(region, ".hero-sub", ".st-hero-sub")
    if sub is None:
        # fall back to the first <p> after h1
        if h1 is not None:
            sib = h1.find_next("p")
            sub = sib
    ctas = all_(region, ".hero-actions a", ".st-cta-group a", ".btn", ".st-btn")
    img = first(region, ".hero-tagline-img", ".st-tagline-img")
    return HeroInfo(
        tag_label=text_of(tag),
        h1=text_of(h1),
        sub=text_of(sub),
        cta_labels=[text_of(c) for c in ctas if text_of(c)],
        has_tagline_image=img is not None,
    )


@dataclass
class PageHeroInfo:
    label: str
    title: str
    sub: str
    breadcrumb: list[str]


def page_hero(soup: BeautifulSoup) -> PageHeroInfo:
    """Inner-page hero (about/services/articles/contact/...)."""
    region = first(
        soup,
        ".page-hero",
        ".st-page-hero",
        "section.hero[data-page-hero]",
    )
    if region is None:
        # Some static pages use `section.hero.hero--page` or similar
        region = first(soup, "section.hero")
    if region is None:
        return PageHeroInfo("", "", "", [])
    label = first(
        region,
        ".page-hero__label",
        ".hero-label",
        ".st-page-hero__label",
        ".section-label",
        ".st-section-label",
    )
    title = first(region, "h1") or first(region, ".page-hero__title", ".st-page-hero__title")
    sub = first(
        region,
        ".page-hero__sub",
        ".hero-sub",
        ".st-page-hero__sub",
    )
    if sub is None and title is not None:
        sib = title.find_next("p")
        if sib is not None:
            sub = sib
    bc_links = all_(region, ".breadcrumb a", ".st-breadcrumb a")
    return PageHeroInfo(
        label=text_of(label),
        title=text_of(title),
        sub=text_of(sub),
        breadcrumb=[text_of(a) for a in bc_links],
    )


def stats_bar(soup: BeautifulSoup) -> list[tuple[str, str]]:
    """Return list of (number, label) pairs.

    Static uses `.stats-bar .stat-item`; built uses `.st-stats > div`
    where each direct-child div carries .st-stat-value and .st-stat-label.
    """
    region = first(soup, ".stats-bar", ".st-stats")
    if region is None:
        return []
    pairs: list[tuple[str, str]] = []
    static_items = region.select(".stat-item")
    if static_items:
        items = static_items
    else:
        # Built `.st-stats` — each direct-child div is one stat
        items = [c for c in region.find_all("div", recursive=False)]
    for item in items:
        num = first(item, ".stat-item__number", ".st-stat-value")
        lab = first(item, ".stat-item__label", ".st-stat-label")
        if num is None or lab is None:
            continue
        pairs.append((text_of(num), text_of(lab)))
    return pairs


def section_labels(soup: BeautifulSoup) -> list[str]:
    """Every gold "eyebrow" label on the page, top-to-bottom."""
    return [text_of(n) for n in all_(soup, ".section-label", ".st-section-label") if text_of(n)]


def gold_rules(soup: BeautifulSoup) -> int:
    """Count of gold rule dividers."""
    return len(all_(soup, ".gold-rule", ".st-gold-rule"))


@dataclass
class CardInfo:
    title: str
    text: str
    link: str  # destination if present, else ""


def cards(soup: BeautifulSoup, scope_selectors: tuple[str, ...]) -> list[CardInfo]:
    """Cards inside any of the supplied scope selectors. Tolerant of static and built variants."""
    out: list[CardInfo] = []
    scopes: list[Tag] = []
    for sel in scope_selectors:
        scopes.extend(soup.select(sel))
    if not scopes:
        scopes = [soup]
    seen = set()
    for scope in scopes:
        # static: <article class="service-card">; built: <div class="st-card">
        for el in scope.select(".service-card, .st-card, .testimonial-card, .st-testimonial-card, .case-study-card, .st-case-study-card, .article-card, .st-article-card, .resource-card, .st-resource-card, .value-card, .st-value-card"):
            if id(el) in seen:
                continue
            seen.add(id(el))
            t = first(el, ".service-card__title", ".st-card__title", ".testimonial-card__name", ".st-testimonial-card__name", ".case-study-card__title", ".st-case-study-card__title", ".article-card__title", ".st-article-card__title", "h2", "h3", "h4")
            p = first(el, ".service-card__text", ".st-card__text", ".testimonial-card__quote", ".st-testimonial-card__quote", "p")
            a = first(el, "a")
            out.append(CardInfo(
                title=text_of(t),
                text=text_of(p),
                link=(a.get("href") or "") if a is not None else "",
            ))
    return out


def home_solutions_cards(soup: BeautifulSoup) -> list[CardInfo]:
    """Home-page Solutions grid cards (scoped to the 3-up grid only)."""
    return cards(
        soup,
        (
            ".services-grid",
            ".st-cards.st-cards-3",
        ),
    )


def featured_solution(soup: BeautifulSoup) -> CardInfo | None:
    el = first(soup, ".solutions-featured", ".st-solutions-featured")
    if el is None:
        return None
    t = first(el, ".solutions-featured__title", ".st-solutions-featured__title", "h3")
    p = first(el, ".solutions-featured__text", ".st-solutions-featured__text", "p")
    a = first(el, "a")
    return CardInfo(
        title=text_of(t),
        text=text_of(p),
        link=(a.get("href") or "") if a is not None else "",
    )


@dataclass
class AboutStripInfo:
    label: str
    title: str
    body: str
    features: list[str]
    badge_number: str
    badge_label: str
    cta_text: str


def home_about_strip(soup: BeautifulSoup) -> AboutStripInfo:
    region = first(soup, ".about-grid", ".st-about-grid")
    if region is None:
        return AboutStripInfo("", "", "", [], "", "", "")
    label = first(region, ".section-label", ".st-section-label")
    title = first(region, "h2")
    text_region = first(region, ".about-text", ".st-about-text") or region
    # Find the longest <p> text in the text region — skips <p>s that wrap a
    # single section-label span.
    body_text = ""
    for p in text_region.find_all("p"):
        txt = text_of(p)
        if len(txt) > len(body_text):
            body_text = txt
    features = [text_of(li) for li in all_(region, ".about-features li", ".st-about-text ul li")]
    badge_num = first(region, ".about-badge__number", ".st-badge-number")
    badge_lab = first(region, ".about-badge__label", ".st-badge-label")
    cta = first(region, ".btn", ".st-btn")
    return AboutStripInfo(
        label=text_of(label),
        title=text_of(title),
        body=body_text,
        features=features,
        badge_number=text_of(badge_num),
        badge_label=text_of(badge_lab),
        cta_text=text_of(cta),
    )


@dataclass
class WhyItem:
    title: str
    text: str


def why_grid(soup: BeautifulSoup) -> list[WhyItem]:
    region = first(soup, ".why-grid", ".st-cards-4")
    if region is None:
        return []
    items: list[WhyItem] = []
    for el in all_(region, ".why-item", ".st-card--why"):
        t = first(el, "h3")
        # Markdown wraps a leading icon span in its own <p>. Pick the
        # longest text-bearing <p> so we get the body, not the icon.
        candidates = el.find_all("p")
        body_text = ""
        for p in candidates:
            txt = text_of(p)
            if len(txt) > len(body_text):
                body_text = txt
        items.append(WhyItem(title=text_of(t), text=body_text))
    return items


@dataclass
class CtaBandInfo:
    title: str
    text: str
    cta_labels: list[str]


def cta_band(soup: BeautifulSoup) -> CtaBandInfo:
    region = first(soup, ".cta-band", ".st-band-navy", ".st-cta-band")
    if region is None:
        return CtaBandInfo("", "", [])
    title = first(region, "h2")
    text = first(region, "p")
    ctas = all_(region, ".btn", ".st-btn")
    return CtaBandInfo(
        title=text_of(title),
        text=text_of(text),
        cta_labels=[text_of(c) for c in ctas if text_of(c)],
    )


@dataclass
class FooterInfo:
    afs_division: str
    afs_credentials: str
    column_headings: list[str]
    column_items: dict[str, list[str]]
    bottom_text: str


def footer(soup: BeautifulSoup) -> FooterInfo:
    afs = first(soup, ".footer-afs")
    afs_div = first(afs, ".footer-afs__division") if afs else None
    afs_cred = first(afs, ".footer-afs__credentials") if afs else None
    grid = first(soup, ".footer-grid")
    headings: list[str] = []
    items: dict[str, list[str]] = {}
    if grid is not None:
        for col in grid.select(".footer-col"):
            h = first(col, "h4")
            heading = text_of(h)
            headings.append(heading)
            items[heading] = [text_of(li) for li in col.select("ul li")]
    bottom = first(soup, ".footer-bottom span")
    return FooterInfo(
        afs_division=text_of(afs_div),
        afs_credentials=text_of(afs_cred),
        column_headings=headings,
        column_items=items,
        bottom_text=text_of(bottom),
    )


def h1s(soup: BeautifulSoup) -> list[str]:
    return [text_of(h) for h in soup.find_all("h1")]


def h2s(soup: BeautifulSoup, scope: Tag | None = None) -> list[str]:
    base = scope if scope is not None else soup
    return [text_of(h) for h in base.find_all("h2")]
