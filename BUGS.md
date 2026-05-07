# BUGS.md — Zensical Parity: Outstanding Divergences

**Post-rebuild note:** The Zensical theme was fully rebuilt from scratch in Task 1 of the clean-theme plan — all Material for MkDocs dependencies were removed and replaced with a hand-crafted custom theme (`overrides/main.html` + `docs/stylesheets/extra.css`). Many prior divergences tracked during the Material-based pass became moot as a result (footer bullets, nav active state, hero alignment, stats bar dividers, flagship card, Built on Trust pill, What Sets Us Apart icons, scroll reveal selectors). Those items have been removed from this list.

---

## Articles Page — Tab Navigation

**Status:** Intentional divergence — sectioned scroll instead of tabs

**Static behaviour:** `articles.html` uses a JavaScript tab UI (Testimonials / Case Studies / Articles / Audio). Clicking a tab shows/hides the corresponding section.

**Zensical behaviour:** All four sections render simultaneously as scrollable blocks with H2 dividers (`Insights & Endorsements`, `Operational Case Studies`, `Audio Interviews`, etc.).

**Reason retained:** The tab UI was generated client-side from `js/translations.js`. Replicating it in MkDocs would require a custom JS overlay. The sectioned layout preserves all content, is more accessible, and supports direct deep-linking.

**Recommendation:** If tab UI is required for production, add a small custom JS toggle in `overrides/main.html` that hides/shows sections by data attribute.

---

## Service Detail — "Other Solutions" Layout

**Status:** Intentional divergence — full cards instead of compact chips

**Static behaviour:** Service detail pages render the "Other Solutions" sibling-nav block as a row of compact navy chips (service name only), generated dynamically by JS.

**Zensical behaviour:** Full `.st-card` 3-column grid with descriptions on each sibling card.

**Reason retained:** The card layout reuses the existing `.st-card` component and provides more context. Service markdown files use `.st-cards.st-cards-3` with `.st-card` elements (full card layout); no `.sibling-cards` or `.st-sibling-cards` chip markup is present.

**Recommendation:** If the chip layout is required, add a `.st-card--chip` modifier that strips padding/border and renders a compact label-only variant.

---

## Service Detail — Feature List Icons

**Status:** Intentional divergence — clean tile grid without per-item icons

**Static behaviour:** "What's Included" feature lists on service pages render as `<li><span class="icon">{emoji}</span><span>{text}</span></li>`, where each item carries an emoji injected from `js/translations.js` (✈️ 🛡️ 🚗 etc.).

**Zensical behaviour:** Plain markdown list rendered via `.st-content-no-first-h1 ul:not([class])` as a gold-bordered tile grid; no per-item emoji.

**Reason retained:** The static feature emojis are inconsistent across services and rely on JS injection. The Zensical tile grid is visually cleaner and matches the gold-rule design language used across the site.

**Recommendation:** If icons are required, port the `f.icon` attribute from `translations.js` into each markdown bullet (e.g. `- ✈️ Private terminal solutions`).

---

## Static Site — JS-Driven Content (Informational)

**Static behaviour:** Several sections of the static site (services index card grid, articles tabs detail, service feature lists, audio section) inject content dynamically from `js/translations.js` and per-page inline `<script>` blocks. These sections appear blank in screenshots without JS execution and are not visible to non-JS clients (search bots, archival tools, screen readers in some configurations).

**Zensical behaviour:** All content is baked into Markdown and renders without JavaScript. Scroll-reveal animation is the only JS-driven enhancement, and it has a 3-second failsafe so content is never permanently hidden.

**Result:** Zensical has equal-or-better content availability than the static site for crawlers, archival tools, and JS-disabled clients.
