# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Marketing site for **Secure Tours & Travel** (a division of Australian Frontline Solutions). This branch (`feature/astro`) is a rewrite of the customer-approved static prototype on top of **Astro 5.18 + content collections**. The customer signed off on the static design — every change here is gated by a pytest alignment harness that compares the built DOM to the static prototype's post-JS DOM. **Visual parity is the contract.** If a page diverges from the prototype, the harness must catch it before commit.

The earlier Zensical attempt on `feature/zensical` was abandoned because we couldn't get sufficient layout fidelity.

## Repository layout

- `static-prototype/` — the customer-approved HTML/CSS/JS prototype, kept in-tree as the harness reference. **Do not modify this directory** unless the customer signs off on a design change.
- `src/pages/` — Astro routes. `[slug].astro` files are dynamic routes generated from collections.
- `src/components/` — reusable `.astro` components. Pure, prop-driven; no inline data.
- `src/content/services/` — markdown front-matter files for the 9 service detail pages, validated by `src/content.config.ts`. **This is the editor surface** the non-technical client will manage via Sveltia CMS (planned).
- `src/styles/global.css` — verbatim port of `static-prototype/css/style.css`. The only intentional change is the hero background URL (absolute `/assets/`). Don't bypass tokens — use `var(--navy)`, `var(--gold)`, etc.
- `src/layouts/BaseLayout.astro` — `<head>` + `<body>` shell shared by every page.
- `tests/` — pytest harness:
  - `conftest.py` — Playwright session fixture pre-renders every `static-prototype/*.html` with Chromium, captures the post-JS DOM, and serves it as the "static" side of the comparison.
  - `test_alignment.py`, `test_body_alignment.py` — DOM equivalence tests (page hero, h2 outline, footer columns, meta description, etc.)
  - `test_service_content.py` — asserts every canonical service feature/lead/title from `translations_data.py` ends up in the built HTML (i.e. our pages are equal-or-better than the static for non-JS clients).
- `public/assets/` — copied from `static-prototype/assets/`; logo, hero image, downloads, favicon.

## Running locally

```sh
npm install
npm run build         # writes dist/
npm run dev           # localhost:4321 with HMR
```

Harness:
```sh
source .venv/bin/activate                     # one-time: python -m venv .venv && pip install -r requirements.txt && playwright install chromium
ALIGN_SKIP_BUILD=1 python -m pytest tests/    # skip rebuild if dist/ is current
ALIGN_USE_RAW_STATIC=1 python -m pytest tests/  # debug only — bypass Playwright pre-render
```

The harness builds Astro once per session (autouse fixture) unless `ALIGN_SKIP_BUILD=1` is set. CI (`.github/workflows/ci.yml`) runs the build plus the full harness on every PR and push to `main`.

## Admin CMS (Sveltia)

`/admin` is a Sveltia CMS shell (`src/pages/admin/index.astro`); its config is generated at build time by `src/pages/admin/config.yml.ts` so each deployment targets the right branch:

- `CMS_BRANCH` — branch the CMS commits to. Defaults to `main` (production). A staging deployment must set this to its own deploy branch.
- `CMS_AUTH_BASE_URL` — URL of the deployed `sveltia-cms-auth` OAuth helper. Until set, editors sign in with a GitHub personal access token.

The CMS edits `src/content/services/*.md` only. Keep `config.yml.ts` field definitions in sync with the Zod schema in `src/content.config.ts` — the schema is the build-time gate that stops a bad CMS edit from deploying. `create`/`delete` are off: new services are developer work (routes, nav, footer). CMS media uploads go to `public/assets/uploads/`, never over the design assets.

## Architecture conventions

**Components go in `src/components/`. Don't extract one until it has at least 2 call sites** (or one call site driven by a content collection — that counts). The home and services-index pages have different prose for the same service cards on purpose; that's what content collections vs. inline data is for. The schema in `src/content.config.ts` covers the home-card data and the service-detail data; services-index card prose is hardcoded inline because it's a third copy and adding a third schema field would be churn.

**Footer variants.** `SiteFooter.astro` props (`showAbn`, `showLocation`, `showLegal`) match per-page variation in the static. `test_footer_columns_match` requires every static footer item to appear in built — extras are allowed. When in doubt, default to showing the items.

**Page-specific CSS** that didn't make it into `static-prototype/css/style.css` (e.g. `.value-card` for about, `.download-card` for resources) lives in `<style is:global>` blocks at the bottom of the page that uses it. This mirrors the static's pattern of inline page-specific CSS in `<head>`.

**The harness is the gate, not eyeballing.** Don't iterate on visual details by hand — verify against the harness, fix the mismatch, re-run. After any change, run the relevant subset (`-k home`, `-k svc_tours`, etc.) before committing.

## Commit and git

**Conventional commits with a `(TOU-159)` ticket suffix.** Examples in history: `feat: port Contact page (TOU-159)`, `fix: AFS strip text colours match static (TOU-159)`. Match this style.

**Never use `git add -A` or `git add .`** — always `git add <specific paths>`. Scratch artifacts (`.playwright-mcp/`, `dist/`, `tmp/`, `.venv/`) must never get staged.

**Push regularly.** Each green-harness milestone is a commit-and-push checkpoint. Don't sit on multiple commits.

## Working with the static prototype reference

The static prototype is **JS-driven** for several pages — service detail and articles index sections have empty placeholder elements that get filled at runtime from `static-prototype/js/translations.js` (`SERVICE_TRANSLATIONS.en`, `TRANSLATIONS.en`). The harness handles this by pre-rendering with Chromium so the comparison is post-JS DOM vs. built DOM.

When extracting content from the static for a new collection or page, the canonical source is **`static-prototype/js/translations.js`**, not the raw HTML (which often has empty `<span id="...">` placeholders).

`tests/translations_data.py` (`SERVICE_PAGES`) is the harness's hand-curated copy of the canonical service-detail content — keep it consistent with the markdown collection.
