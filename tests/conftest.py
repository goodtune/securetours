"""Shared fixtures for HTML-alignment tests."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest
from bs4 import BeautifulSoup


REPO = Path(__file__).resolve().parent.parent
STATIC_ROOT = (REPO.parent / "securetours").resolve()
BUILT_ROOT = (REPO / "site").resolve()


def _build_zensical() -> None:
    """Build the Zensical site once per test session unless ALIGN_SKIP_BUILD=1."""
    if os.environ.get("ALIGN_SKIP_BUILD") == "1":
        return
    result = subprocess.run(
        ["uvx", "zensical", "build"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Zensical build failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )


@pytest.fixture(scope="session", autouse=True)
def build_once():
    """Build Zensical site exactly once before any test runs."""
    _build_zensical()


def _read_soup(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


@pytest.fixture(scope="session")
def static_root() -> Path:
    if not STATIC_ROOT.exists():
        pytest.skip(f"Static site root not found at {STATIC_ROOT}")
    return STATIC_ROOT


@pytest.fixture(scope="session")
def built_root() -> Path:
    if not BUILT_ROOT.exists():
        pytest.fail(f"Built site root not found at {BUILT_ROOT}")
    return BUILT_ROOT


# --- Page mapping ----------------------------------------------------------
# (page_key, static_path, built_path)
PAGE_MAP = [
    ("home", "index.html", "index.html"),
    ("about", "about.html", "about/index.html"),
    ("services_index", "services/index.html", "services/index.html"),
    ("event_solutions", "event-solutions.html", "event-solutions/index.html"),
    ("articles_index", "articles.html", "articles/index.html"),
    ("resources", "resources.html", "resources/index.html"),
    ("contact", "contact.html", "contact/index.html"),
    ("svc_tours", "services/tours-travel-solutions.html", "services/tours-travel-solutions/index.html"),
    ("svc_egm", "services/executive-guest-management.html", "services/executive-guest-management/index.html"),
    ("svc_eta", "services/exclusive-transfer-assistance.html", "services/exclusive-transfer-assistance/index.html"),
    ("svc_pass_athlete", "services/pass-athlete.html", "services/pass-athlete/index.html"),
    ("svc_pass_artist", "services/pass-artist.html", "services/pass-artist/index.html"),
    ("svc_cc", "services/concierge-chaperone.html", "services/concierge-chaperone/index.html"),
    ("svc_bereavement", "services/bereavement-travel-support.html", "services/bereavement-travel-support/index.html"),
    ("svc_solo", "services/solo-traveller-assist.html", "services/solo-traveller-assist/index.html"),
    ("svc_stage", "services/stage.html", "services/stage/index.html"),
    ("art_carriageworks", "articles/carriageworks.html", "articles/carriageworks/index.html"),
    ("art_vivid", "articles/vivid-sydney.html", "articles/vivid-sydney/index.html"),
    ("art_gary", "articles/gary-oriordan-endorsement.html", "articles/gary-oriordan-endorsement/index.html"),
    ("art_janene", "articles/janene-rees-endorsement.html", "articles/janene-rees-endorsement/index.html"),
    ("art_matthew", "articles/matthew-harrison-profile.html", "articles/matthew-harrison-profile/index.html"),
    ("notfound", "404.html", "404.html"),
]


@pytest.fixture(scope="session")
def page_pairs(static_root: Path, built_root: Path):
    """Return list of (key, static_soup, built_soup) for every mapped page."""
    pairs = []
    for key, s_rel, b_rel in PAGE_MAP:
        s = static_root / s_rel
        b = built_root / b_rel
        if not s.exists() or not b.exists():
            continue
        pairs.append((key, _read_soup(s), _read_soup(b)))
    return pairs


@pytest.fixture(scope="session")
def all_pages(page_pairs):
    """Map of page_key → (static_soup, built_soup)."""
    return {key: (s, b) for key, s, b in page_pairs}


def normalize_text(s: str | None) -> str:
    if s is None:
        return ""
    return re.sub(r"\s+", " ", s).strip()


def text_of(node) -> str:
    if node is None:
        return ""
    return normalize_text(node.get_text(" ", strip=True))


def texts_of(nodes) -> list[str]:
    return [text_of(n) for n in nodes]
