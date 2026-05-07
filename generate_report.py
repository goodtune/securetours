#!/usr/bin/env python3
"""Generate comparison-report.html for Zensical parity review."""

import base64
import os
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent
BUGS_MD = (REPO / "BUGS.md").read_text()
TMP = REPO / "tmp"
TMP.mkdir(exist_ok=True)
OUTPUT = TMP / "comparison-report.html"

STATIC_BASE = "https://securetours.staging-site.au"
ZENSICAL_BASE = "http://localhost:8000"

# (title, static_path, zensical_path)
PAGES = [
    ("Home", "/", "/"),
    ("About", "/about.html", "/about/"),
    ("Services Index", "/services/index.html", "/services/"),
    ("Service: Tours & Travel Solutions", "/services/tours-travel-solutions/", "/services/tours-travel-solutions/"),
    ("Service: Executive Guest Management", "/services/executive-guest-management/", "/services/executive-guest-management/"),
    ("Service: Exclusive Transfer Assistance", "/services/exclusive-transfer-assistance/", "/services/exclusive-transfer-assistance/"),
    ("Service: PASS Athlete", "/services/pass-athlete/", "/services/pass-athlete/"),
    ("Service: PASS Artist", "/services/pass-artist/", "/services/pass-artist/"),
    ("Service: Concierge & Chaperone", "/services/concierge-chaperone/", "/services/concierge-chaperone/"),
    ("Service: Bereavement Travel Support", "/services/bereavement-travel-support/", "/services/bereavement-travel-support/"),
    ("Service: Solo Traveller Assist", "/services/solo-traveller-assist/", "/services/solo-traveller-assist/"),
    ("Service: Stage", "/services/stage/", "/services/stage/"),
    ("Event Solutions", "/event-solutions/", "/event-solutions/"),
    ("Articles Index", "/articles.html", "/articles/"),
    # For article details, static ref is the articles index
    ("Article: Gary O'Riordan Endorsement", "/articles.html", "/articles/gary-oriordan-endorsement/"),
    ("Article: Janene Rees Endorsement", "/articles.html", "/articles/janene-rees-endorsement/"),
    ("Article: Matthew Harrison Profile", "/articles.html", "/articles/matthew-harrison-profile/"),
    ("Article: Vivid Sydney", "/articles.html", "/articles/vivid-sydney/"),
    ("Article: Carriageworks", "/articles.html", "/articles/carriageworks/"),
    ("Resources", "/resources.html", "/resources/"),
    ("Contact", "/contact.html", "/contact/"),
]

FEATURE_ROWS = [
    ("Navigation — desktop layout & dropdown", "Pass", "Matches static nav structure and dropdown behaviour"),
    ("Navigation — mobile hamburger menu", "Pass", "Responsive hamburger opens correctly at ≤768px"),
    ("Navigation — active state on current page", "Pass", "Active link highlighted via MkDocs Material"),
    ("Footer — columns, links, copyright", "Pass", "Three-column layout with all links and copyright text"),
    ("Footer — social icons", "Pass", "LinkedIn, Facebook, Instagram icons render"),
    ("Hero — full-bleed image + overlay", "Pass", "Hero renders correctly with dark overlay"),
    ("Hero — title & breadcrumb", "Pass", "Title and breadcrumb pulled from page.meta.hero_title"),
    ("Hero — label strip", "Pass", "Hero now triggered by hero_title; hero_label optional. Contact page hero has no label, matching static."),
    ("Stats bar — 4 metrics with dividers", "Pass", "Number, label, divider structure matches static"),
    ("Cards — flagship card grid (home)", "Pass", "3-column flagship card grid with gold borders"),
    ("Cards — service cards on Services index", "Pass", "Service card grid renders with descriptions"),
    ("Cards — 'Other Solutions' on service detail", "Intentional divergence", "Full cards instead of compact chips (BUGS.md)"),
    ("Home — 'What Sets Us Apart' section", "Pass", "Icons and copy render correctly"),
    ("Home — 'Built on Trust' client logos section", "Pass", "Logo pill grid renders"),
    ("Articles — tab navigation vs scroll layout", "Intentional divergence", "Sectioned scroll layout instead of JS tabs (BUGS.md)"),
    ("Service — feature list ('What's Included')", "Intentional divergence", "Gold tile grid without per-item emoji (BUGS.md)"),
    ("Service — section labels (gold uppercase)", "Pass", "Section labels render in gold above feature list"),
    ("Scroll reveal animation", "Pass", "Selectors fixed to use st- prefix classes; 3-second failsafe ensures content always visible"),
    ("Resources page layout", "Pass", "Resource cards/list render correctly"),
    ("Contact page layout", "Pass", "Contact form and details render"),
    ("Event Solutions page layout", "Pass", "Event solutions content renders"),
    ("About page layout", "Pass", "About page with team section renders"),
    ("Meta strip hidden on service pages", "Pass", "st-meta strip suppressed on service detail pages"),
    ("Duplicate H1 suppressed in content", "Pass", "Hero H1 not duplicated in content area"),
    ("Gap between nav and hero eliminated", "Pass", "No visual gap between sticky nav and page hero"),
]

def take_screenshots():
    from playwright.sync_api import sync_playwright

    screenshots = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page_obj = context.new_page()

        for title, static_path, zensical_path in PAGES:
            static_url = STATIC_BASE + static_path
            zensical_url = ZENSICAL_BASE + zensical_path

            print(f"  Static:  {static_url}", flush=True)
            try:
                page_obj.goto(static_url, wait_until="networkidle", timeout=30000)
                page_obj.wait_for_timeout(1000)
                static_bytes = page_obj.screenshot(full_page=False, type="jpeg", quality=80)
                static_b64 = base64.b64encode(static_bytes).decode()
            except Exception as e:
                print(f"    FAILED: {e}", flush=True)
                static_b64 = None

            print(f"  Zensical: {zensical_url}", flush=True)
            try:
                page_obj.goto(zensical_url, wait_until="networkidle", timeout=30000)
                page_obj.wait_for_timeout(1000)
                zen_bytes = page_obj.screenshot(full_page=False, type="jpeg", quality=80)
                zen_b64 = base64.b64encode(zen_bytes).decode()
            except Exception as e:
                print(f"    FAILED: {e}", flush=True)
                zen_b64 = None

            screenshots[title] = (static_b64, zen_b64)

        context.close()
        browser.close()

    return screenshots


def build_html(screenshots):
    today = date.today().isoformat()

    # Feature table rows
    feature_rows_html = ""
    for feature, status, notes in FEATURE_ROWS:
        if status == "Pass":
            badge = '<span class="badge pass">Pass</span>'
        elif status == "Intentional divergence":
            badge = '<span class="badge diverge">Intentional divergence</span>'
        else:
            badge = f'<span class="badge bug">Bug</span>'
        feature_rows_html += f"""
        <tr>
          <td>{feature}</td>
          <td>{badge}</td>
          <td>{notes}</td>
        </tr>"""

    # Page comparison sections
    page_sections_html = ""
    failed_pages = []
    captured = 0
    for title, static_path, zensical_path in PAGES:
        static_b64, zen_b64 = screenshots.get(title, (None, None))

        static_img = (
            f'<img src="data:image/jpeg;base64,{static_b64}" alt="Static: {title}" />'
            if static_b64
            else '<div class="img-placeholder">Screenshot failed</div>'
        )
        zen_img = (
            f'<img src="data:image/jpeg;base64,{zen_b64}" alt="Zensical: {title}" />'
            if zen_b64
            else '<div class="img-placeholder">Screenshot failed</div>'
        )

        static_label = STATIC_BASE + static_path
        zen_label = ZENSICAL_BASE + zensical_path

        if static_b64 and zen_b64:
            captured += 1
        else:
            failed_pages.append(title)

        anchor = title.lower().replace(" ", "-").replace(":", "").replace("'", "").replace("&", "and").replace(",", "")
        page_sections_html += f"""
    <section class="page-comparison" id="{anchor}">
      <div class="page-title">
        <h2>{title}</h2>
        <div class="page-urls">
          <span class="url-label">Static:</span> <code>{static_label}</code>
          &nbsp;&nbsp;|&nbsp;&nbsp;
          <span class="url-label">Zensical:</span> <code>{zen_label}</code>
        </div>
      </div>
      <div class="comparison-grid">
        <div class="col">
          <div class="col-header">Static Site</div>
          {static_img}
        </div>
        <div class="col">
          <div class="col-header">Zensical (feature/zensical)</div>
          {zen_img}
        </div>
      </div>
    </section>"""

    # BUGS.md as HTML (simple preformatted block with minimal markdown rendering)
    import html as html_mod
    bugs_escaped = html_mod.escape(BUGS_MD)
    # Convert markdown headers to bold spans
    import re
    bugs_lines = []
    for line in bugs_escaped.split('\n'):
        if line.startswith('### '):
            bugs_lines.append(f'<strong style="font-size:1rem">{line[4:]}</strong>')
        elif line.startswith('## '):
            bugs_lines.append(f'<strong style="font-size:1.1rem">{line[3:]}</strong>')
        elif line.startswith('# '):
            bugs_lines.append(f'<strong style="font-size:1.2rem">{line[2:]}</strong>')
        elif line.startswith('**') and line.endswith('**'):
            bugs_lines.append(f'<strong>{line[2:-2]}</strong>')
        elif line == '---':
            bugs_lines.append('<hr style="border-color:#555;margin:1rem 0">')
        else:
            bugs_lines.append(line)
    bugs_html = '\n'.join(bugs_lines)

    toc_items = ""
    for title, _, _ in PAGES:
        anchor = title.lower().replace(" ", "-").replace(":", "").replace("'", "").replace("&", "and").replace(",", "")
        toc_items += f'<li><a href="#{anchor}">{title}</a></li>\n'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Secure Tours — Zensical Parity Comparison Report</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; }}
  :root {{
    --navy: #0a1628;
    --gold: #b8973e;
    --light: #f5f5f0;
    --mid: #2a3a52;
    --pass: #1a7a4a;
    --bug: #8b1a1a;
    --diverge: #7a5a00;
  }}
  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #1a1a1a;
    color: #e0e0e0;
    line-height: 1.5;
  }}
  a {{ color: var(--gold); }}
  a:hover {{ color: #d4af5a; }}

  /* Header */
  .report-header {{
    background: var(--navy);
    border-bottom: 3px solid var(--gold);
    padding: 2rem;
    text-align: center;
  }}
  .report-header h1 {{
    margin: 0 0 0.5rem;
    font-size: 1.8rem;
    color: var(--gold);
  }}
  .report-header .meta {{
    font-size: 0.85rem;
    color: #9ab;
  }}

  /* TOC */
  .toc {{
    background: #222;
    border: 1px solid #333;
    padding: 1.5rem 2rem;
    margin: 1.5rem auto;
    max-width: 900px;
    border-radius: 4px;
  }}
  .toc h2 {{ margin: 0 0 1rem; font-size: 1rem; color: var(--gold); text-transform: uppercase; letter-spacing: 0.05em; }}
  .toc ol {{ margin: 0; padding-left: 1.5rem; columns: 2; column-gap: 2rem; }}
  .toc li {{ margin-bottom: 0.3rem; font-size: 0.85rem; break-inside: avoid; }}

  /* Feature table */
  .feature-section {{
    max-width: 1000px;
    margin: 2rem auto;
    padding: 0 1rem;
  }}
  .feature-section h2 {{
    color: var(--gold);
    border-bottom: 1px solid var(--gold);
    padding-bottom: 0.5rem;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }}
  th {{
    background: var(--navy);
    color: var(--gold);
    padding: 0.6rem 1rem;
    text-align: left;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 0.75rem;
  }}
  td {{
    padding: 0.55rem 1rem;
    border-bottom: 1px solid #333;
    vertical-align: top;
  }}
  tr:nth-child(even) td {{ background: #1e1e1e; }}
  tr:hover td {{ background: #252530; }}

  .badge {{
    display: inline-block;
    padding: 0.2em 0.6em;
    border-radius: 3px;
    font-size: 0.75rem;
    font-weight: 600;
    white-space: nowrap;
  }}
  .badge.pass {{ background: rgba(26,122,74,0.2); color: #4caf7d; border: 1px solid rgba(76,175,125,0.4); }}
  .badge.bug {{ background: rgba(139,26,26,0.2); color: #f57c7c; border: 1px solid rgba(245,124,124,0.4); }}
  .badge.diverge {{ background: rgba(122,90,0,0.2); color: #d4af5a; border: 1px solid rgba(212,175,90,0.4); }}

  /* Page comparisons */
  .page-comparison {{
    max-width: 1400px;
    margin: 2rem auto;
    padding: 0 1rem;
  }}
  .page-title {{
    position: sticky;
    top: 0;
    z-index: 10;
    background: #111;
    border-left: 4px solid var(--gold);
    padding: 0.75rem 1rem;
    margin-bottom: 1rem;
  }}
  .page-title h2 {{
    margin: 0 0 0.3rem;
    font-size: 1.1rem;
    color: var(--gold);
  }}
  .page-urls {{
    font-size: 0.78rem;
    color: #888;
  }}
  .url-label {{ color: #aaa; }}
  code {{ font-family: 'SF Mono', Menlo, monospace; font-size: 0.85em; }}

  .comparison-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2px;
    background: #333;
    border: 1px solid #333;
  }}
  .col {{
    background: #1a1a1a;
    overflow: hidden;
  }}
  .col-header {{
    background: var(--navy);
    color: #ccc;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.4rem 0.8rem;
    border-bottom: 2px solid var(--gold);
  }}
  .col img {{
    width: 100%;
    display: block;
  }}
  .img-placeholder {{
    background: #2a0a0a;
    color: #f57c7c;
    padding: 2rem;
    text-align: center;
    font-size: 0.9rem;
  }}

  /* BUGS section */
  .bugs-section {{
    max-width: 900px;
    margin: 3rem auto 2rem;
    padding: 0 1rem;
  }}
  .bugs-section h2 {{
    color: var(--gold);
    border-bottom: 1px solid var(--gold);
    padding-bottom: 0.5rem;
  }}
  .bugs-content {{
    background: #111;
    border: 1px solid #333;
    padding: 1.5rem;
    border-radius: 4px;
    font-size: 0.85rem;
    line-height: 1.7;
    white-space: pre-wrap;
    font-family: 'SF Mono', Menlo, monospace;
    color: #ccc;
  }}

  /* Footer */
  .report-footer {{
    text-align: center;
    padding: 2rem;
    font-size: 0.8rem;
    color: #555;
    border-top: 1px solid #333;
    margin-top: 3rem;
  }}
</style>
</head>
<body>

<header class="report-header">
  <h1>Secure Tours — Zensical Parity Comparison Report</h1>
  <div class="meta">
    Generated: {today} &nbsp;|&nbsp;
    Branch: <code>feature/zensical</code> &nbsp;|&nbsp;
    Post-rebuild: custom theme (Material removed) &nbsp;|&nbsp;
    Pages captured: {captured} / {len(PAGES)} &nbsp;|&nbsp;
    Static: <code>{STATIC_BASE}</code> &nbsp;|&nbsp;
    Zensical: <code>{ZENSICAL_BASE}</code>
  </div>
</header>

<nav class="toc">
  <h2>Contents</h2>
  <ol>
    <li><a href="#feature-evaluation">Feature Evaluation Summary</a></li>
    {toc_items}
    <li><a href="#bugs-md">BUGS.md</a></li>
  </ol>
</nav>

<section class="feature-section" id="feature-evaluation">
  <h2>Feature Evaluation Summary</h2>
  <table>
    <thead>
      <tr>
        <th style="width:35%">Feature</th>
        <th style="width:20%">Status</th>
        <th>Notes</th>
      </tr>
    </thead>
    <tbody>
      {feature_rows_html}
    </tbody>
  </table>
</section>

{page_sections_html}

<section class="bugs-section" id="bugs-md">
  <h2>BUGS.md — Outstanding Divergences</h2>
  <div class="bugs-content">{bugs_html}</div>
</section>

<footer class="report-footer">
  Secure Tours · Zensical Parity Report · {today}
</footer>

</body>
</html>"""
    return html, captured, failed_pages


def main():
    print("Taking screenshots...", flush=True)
    screenshots = take_screenshots()

    print("\nBuilding HTML report...", flush=True)
    html, captured, failed_pages = build_html(screenshots)

    OUTPUT.write_text(html, encoding="utf-8")
    size_mb = OUTPUT.stat().st_size / 1024 / 1024
    print(f"\nReport written to: {OUTPUT}", flush=True)
    print(f"File size: {size_mb:.2f} MB", flush=True)
    print(f"Pages captured: {captured} / {len(PAGES)}", flush=True)
    if failed_pages:
        print(f"Failed pages: {', '.join(failed_pages)}", flush=True)
    else:
        print("All pages captured successfully.", flush=True)


if __name__ == "__main__":
    main()
