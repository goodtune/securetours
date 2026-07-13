"""Canonical content expectations, loaded from the CMS editor surface.

Since the whole site renders from `src/content/` (pages YAML, articles
YAML, services markdown front matter), the harness sources expected TEXT
from those files: an admin edit through the CMS changes the expectation
and the built page together, so legitimate copy edits stay green.
Structure and design remain pinned to `static-prototype/` in the
alignment tests — this module only answers "what should the words be".
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml
from bs4 import BeautifulSoup

REPO = Path(__file__).resolve().parent.parent
PAGES_DIR = REPO / "src" / "content" / "pages"
ARTICLES_DIR = REPO / "src" / "content" / "articles"
SERVICES_DIR = REPO / "src" / "content" / "services"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def strip_html(s: str) -> str:
    """Content strings may carry inline markup (<em>, <strong>, links);
    DOM extraction sees only the text."""
    return _norm(BeautifulSoup(s, "html.parser").get_text(" "))


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.DOTALL)
    if not m:
        raise ValueError(f"no front matter in {path}")
    return yaml.safe_load(m.group(1))


# --- content keyed like conftest.PAGE_MAP page keys ------------------------

PAGES: dict[str, dict] = {
    key: _load_yaml(PAGES_DIR / fname)
    for key, fname in {
        "home": "home.yaml",
        "about": "about.yaml",
        "services_index": "services-index.yaml",
        "event_solutions": "event-solutions.yaml",
        "articles_index": "articles-index.yaml",
        "resources": "resources.yaml",
        "contact": "contact.yaml",
        "faq": "faq.yaml",
        "notfound": "not-found.yaml",
    }.items()
}

SITE: dict = _load_yaml(PAGES_DIR / "site.yaml")

ARTICLES: dict[str, dict] = {
    key: _load_yaml(ARTICLES_DIR / fname)
    for key, fname in {
        "art_carriageworks": "carriageworks.yaml",
        "art_vivid": "vivid-sydney.yaml",
        "art_gary": "gary-oriordan-endorsement.yaml",
        "art_janene": "janene-rees-endorsement.yaml",
        "art_matthew": "matthew-harrison-profile.yaml",
    }.items()
}

SERVICE_SLUGS: dict[str, str] = {
    "svc_tours": "tours-travel-solutions",
    "svc_egm": "executive-guest-management",
    "svc_eta": "exclusive-transfer-assistance",
    "svc_pass_athlete": "pass-athlete",
    "svc_pass_artist": "pass-artist",
    "svc_cc": "concierge-chaperone",
    "svc_stage": "stage",
    "svc_bereavement": "bereavement-travel-support",
    "svc_solo": "solo-traveller-assist",
    "svc_scout": "scout",
}

SERVICES: dict[str, dict] = {
    key: _load_front_matter(SERVICES_DIR / f"{slug}.md")
    for key, slug in SERVICE_SLUGS.items()
}


def service_page_path(key: str) -> str:
    return f"services/{SERVICE_SLUGS[key]}/index.html"


# --- derived expectations ----------------------------------------------------

def _collect_strings(node, out: set[str]) -> None:
    if isinstance(node, str):
        out.add(strip_html(node))
    elif isinstance(node, dict):
        for v in node.values():
            _collect_strings(v, out)
    elif isinstance(node, list):
        for v in node:
            _collect_strings(v, out)


def content_strings(page_key: str) -> set[str]:
    """Every normalized text string a page's content files can produce
    (page/article/service content plus the site-wide footer/CTA copy)."""
    out: set[str] = set()
    source = (
        PAGES.get(page_key)
        or ARTICLES.get(page_key)
        or SERVICES.get(page_key)
    )
    if source is None:
        raise KeyError(f"no content source for page key {page_key!r}")
    _collect_strings(source, out)
    _collect_strings(SITE, out)
    if page_key == "home":
        # The home page also renders every service's home card.
        for svc in SERVICES.values():
            _collect_strings(svc.get("home_card", {}), out)
            out.add(strip_html(svc["title"]))
    return out


def expected_header(page_key: str) -> tuple[str, str]:
    """(title, meta description) for any mapped page."""
    if page_key in PAGES:
        meta = PAGES[page_key]["meta"]
        return _norm(meta["title"]), _norm(meta["description"])
    if page_key in ARTICLES:
        meta = ARTICLES[page_key]["meta"]
        return _norm(meta["title"]), _norm(meta["description"])
    if page_key in SERVICES:
        data = SERVICES[page_key]
        return (
            f"{_norm(data['title'])} — Secure Tours & Travel",
            _norm(data["meta_description"]),
        )
    raise KeyError(page_key)


def expected_h1(page_key: str) -> str:
    if page_key in SERVICES:
        return strip_html(SERVICES[page_key]["title"])
    if page_key in ARTICLES:
        return strip_html(ARTICLES[page_key]["hero"]["title"])
    page = PAGES[page_key]
    if page_key == "notfound":
        return strip_html(page["title"])
    return strip_html(page["hero"]["title"])


def expected_page_hero(page_key: str) -> tuple[str, str, str]:
    """(label, title, sub) for pages using the shared PageHero."""
    if page_key in SERVICES:
        data = SERVICES[page_key]
        return (
            strip_html(data["hero_tag"]),
            strip_html(data["title"]),
            strip_html(data["hero_sub"]),
        )
    if page_key in ARTICLES:
        hero = ARTICLES[page_key]["hero"]
        return strip_html(hero["label"]), strip_html(hero["title"]), strip_html(hero["sub"])
    hero = PAGES[page_key]["hero"]
    return (
        strip_html(hero.get("label", "")),
        strip_html(hero["title"]),
        strip_html(hero["sub"]),
    )
