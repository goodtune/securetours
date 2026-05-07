# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Marketing site for **Secure Tours & Travel** (a division of Australian Frontline Solutions). Pure static HTML/CSS/JS — no framework, no build step, no tests, no `package.json`. Deployed to DigitalOcean App Platform; staging at `securetours.staging-site.au`.

## Running locally

There is nothing to build. Open any `.html` directly in a browser, or serve the directory with any static server, e.g. `python3 -m http.server` from the repo root. The contact form requires a real Formspree endpoint (see "Contact form" below) — the rest works offline.

Playwright MCP is pre-allowlisted in `.claude/settings.local.json` for `browser_navigate` and `browser_take_screenshot`, so visual checks via Playwright don't need extra approval.

## Architecture

Every page is a self-contained, standalone HTML document. There is **no template engine and no shared partials** — the `<nav>` and `<footer>` blocks are duplicated verbatim in every `.html` file. Changes to navigation, footer links, or the brand bar must be applied to every page (top-level + `services/` + `articles/`).

Three shared assets do all the cross-cutting work:

- `css/style.css` — single design system (~1070 lines). Brand tokens live in the `:root` block at the top: Navy `#1E2E78`, Gold `#B8952A`, Playfair Display (headings) + Open Sans (body). Use the CSS custom properties (`var(--navy)`, `var(--gold)`, etc.) rather than hardcoding hex values.
- `js/main.js` — IIFE wired up on `DOMContentLoaded`. Handles nav scroll/mobile toggle, contact-form submit, scroll-reveal animations, and applies translations.
- `js/translations.js` — defines a global `TRANSLATIONS` object keyed by language (`en`, `zh`). Page elements opt in via `data-i18n="key"` attributes; `applyTranslations(lang)` in `main.js` swaps `el.innerHTML` from the table.

Page categories:
- Top-level pages: `index.html`, `about.html`, `contact.html`, `articles.html`, `resources.html`, `event-solutions.html`, `404.html`.
- `services/` — service detail pages plus `services/index.html` ("Tourism Solutions" hub).
- `articles/` — case studies, endorsements, profiles linked from `articles.html`.

## Conventions and gotchas

**i18n.** New user-facing copy that is exposed via `data-i18n` must have keys added to **both** the `en` and `zh` blocks in `js/translations.js`. Hardcoded text without a `data-i18n` attribute is fine — it just won't translate. The `:lang(zh)` selector in `style.css` switches body font to PingFang SC / Noto Sans SC.

**Two animation systems, don't confuse them:**
- `.reveal` — inline `<style>` block at the top of each page sets `opacity: 0`, then `js/main.js` uses an `IntersectionObserver` to add `.visible` on scroll. `main.js` also auto-tags `.service-card`, `.why-item`, `.stat-item`, and `.feature-list li` with `.reveal`. **Trap:** any element that ends up with class `reveal` but never enters the viewport (or that lives on a page where the inline `<style>` block is missing) stays invisible. Multiple commits in history (`5fb9ae5`, `a860574`) fix exactly this — be wary of adding stray `reveal` classes.
- `.fade-up` + `.fade-up-1/2/3` — CSS keyframe with staggered `animation-delay`, used for the hero entrance. Self-running, no JS observer required.

**Contact form.** `js/main.js` line ~47 has `FORMSPREE_ENDPOINT = 'https://formspree.io/f/FORMSPREE_FORM_ID'` — `FORMSPREE_FORM_ID` is a placeholder that must be replaced with a real Formspree form ID before the contact page works in production. Don't commit a real key by accident.

**Sitemap is hand-maintained.** When adding a new page under `services/` or `articles/`, also add a `<url>` entry to `sitemap.xml`. Existing entries follow priority conventions: home `1.0`, hub pages `0.9`, service detail `0.85`, articles `0.7–0.75`.

**Commit style.** Conventional prefixes (`feat:`, `fix:`, `chore:`, `revert:`, `merge:`), frequently with a Linear-style ticket reference like `TOU-155`. Match this style.

**Path conventions.** Pages in subdirectories (`services/*`, `articles/*`) reference shared assets with `../` prefixes (`../css/style.css`, `../js/main.js`, `../assets/...`). Top-level pages reference them without the prefix. Easy to get wrong when copy-pasting a page between directories.

**Do not use `git add -A`.** Per the user's global rule: always `git add <path>` for specific files. The repo regularly contains scratch artifacts (`.playwright-mcp/`) that should not be staged.
