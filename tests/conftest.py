"""Shared fixtures for HTML-alignment tests.

The static reference site is JS-driven for several pages (service detail,
articles index sections, home about_text). Comparing raw static HTML to
built unfairly fails because static literally has empty placeholders that
JS fills at runtime. To compare apples to apples we pre-render the static
pages with a real headless browser (Playwright/Chromium), dump the post-JS
HTML to a session-scoped tmp dir, and use those rendered files as the
static side of the alignment harness.
"""
from __future__ import annotations

import os
import re
import socket
import subprocess
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import pytest
from bs4 import BeautifulSoup


REPO = Path(__file__).resolve().parent.parent
# Static prototype lives in the repo (self-contained), so the branch
# stays comparable even after main is replaced with the Astro build.
STATIC_SOURCE = (REPO / "static-prototype").resolve()
# Astro output
BUILT_ROOT = (REPO / "dist").resolve()


def _build_astro() -> None:
    """Build the Astro site once per test session unless ALIGN_SKIP_BUILD=1."""
    if os.environ.get("ALIGN_SKIP_BUILD") == "1":
        return
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Astro build failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )


@pytest.fixture(scope="session", autouse=True)
def build_once():
    """Build Astro site exactly once before any test runs."""
    _build_astro()


# --- Static pre-render via Playwright -------------------------------------
# The static site needs JS to fill its placeholders. We serve the source
# tree over HTTP, drive Chromium through every page, capture the post-JS
# DOM, and write each page to a session-scoped tmp dir. The rest of the
# harness then reads from this rendered tree as if it were the static src.

class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silence


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _serve(directory: Path, port: int) -> HTTPServer:
    handler = type(
        "Handler",
        (_QuietHandler,),
        {"directory": str(directory)},
    )
    # Stamp the directory onto the handler subclass so SimpleHTTPRequestHandler
    # serves from there (Python 3.7+ accepts directory= kwarg, but constructing
    # via type() avoids the per-request kwarg dance).
    server = HTTPServer(("127.0.0.1", port), handler)
    server.allow_reuse_address = True
    return server


def _render_static_with_js(source: Path, out: Path) -> None:
    """Walk every .html under `source`, render it with JS in Chromium, and
    write the post-JS DOM to the matching path under `out`."""
    from functools import partial

    from playwright.sync_api import sync_playwright

    SimpleHTTPRequestHandler.log_message = lambda self, *a, **kw: None  # type: ignore
    port = _free_port()
    server = HTTPServer(
        ("127.0.0.1", port),
        partial(SimpleHTTPRequestHandler, directory=str(source)),
    )
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        out.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            page = ctx.new_page()
            for html_path in sorted(source.rglob("*.html")):
                rel = html_path.relative_to(source)
                url = f"http://127.0.0.1:{port}/{rel.as_posix()}"
                page.goto(url, wait_until="networkidle", timeout=15000)
                # Give scroll-reveal IntersectionObserver / i18n a moment
                page.wait_for_timeout(150)
                target = out / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(page.content(), encoding="utf-8")
            browser.close()
    finally:
        server.shutdown()


@pytest.fixture(scope="session")
def static_root(tmp_path_factory) -> Path:
    """Return path to a tmp dir containing the static site rendered with JS.

    Set ALIGN_USE_RAW_STATIC=1 to skip the playwright pre-render and
    point at the raw source tree (faster, but JS-driven content will be
    empty — useful only for debugging extraction logic).
    """
    if not STATIC_SOURCE.exists():
        pytest.skip(f"Static source not found at {STATIC_SOURCE}")
    if os.environ.get("ALIGN_USE_RAW_STATIC") == "1":
        return STATIC_SOURCE
    rendered = tmp_path_factory.mktemp("static_rendered")
    _render_static_with_js(STATIC_SOURCE, rendered)
    # Also copy assets so any relative refs the harness might follow still resolve
    return rendered


def _read_soup(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


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
