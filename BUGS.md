# BUGS.md — Zensical Parity: Unresolved Issues

Issues that could not be fully resolved in the Zensical build, or where the Zensical implementation intentionally diverges from the static site for technical reasons.

---

## Scroll Reveal Animations

**Status:** Not implemented  
**Static behaviour:** Cards, stats blocks, and section elements fade in and slide up as the user scrolls them into view (IntersectionObserver + `.reveal` CSS class).  
**Zensical behaviour:** All content is visible immediately on page load.  
**Attempts made:** Implemented IntersectionObserver script in `overrides/main.html` targeting `.st-card`, `.st-stats > div`, `.st-about-badge`. Removed after discovering that the initial `opacity: 0` state causes below-fold cards to appear invisible in full-page screenshots, server-side rendering contexts, and for users who arrive via anchor link or direct URL to a content section.  
**Recommendation:** Re-add with a `no-js` fallback (CSS-only visible state as default, JS enhancement only). Use a narrower selector (e.g. hero stats only) rather than all cards globally.

---

## Contact Page — Hero Label

**Status:** Minor difference  
**Static behaviour:** Contact page hero has no label strip — just breadcrumb + plain H1.  
**Zensical behaviour:** Contact page has `hero_label: "Contact"` which renders the full hero block with label, H1, and sub text.  
**Reason retained:** Zensical's template either renders a full hero (with label, breadcrumb, title) or falls through to the plain content block. A hybrid approach (breadcrumb + H1 without the label strip) would require template modifications. The current implementation provides a clearer UX for the contact page.

---

## Articles Page — Tab Navigation

**Status:** Not implemented  
**Static behaviour:** Articles index page has JavaScript tab navigation (Testimonials / Case Studies / Articles / Audio tabs). Clicking a tab shows/hides the corresponding section.  
**Zensical behaviour:** All sections are visible simultaneously as scrollable sections with H2 headings as dividers.  
**Attempts made:** Assessed MkDocs Material content tabs (`=== "Tab name"` syntax). Not attempted due to incompatibility with the mixed HTML/Markdown content used in the testimonial cards and case study cards.  
**Recommendation:** Add JS tab switching as a custom script in `overrides/main.html` targeting the section H2 elements, if tab navigation is required for production.

---

## "Other Solutions" Compact Chips on Service Pages

**Status:** Acceptable difference  
**Static behaviour:** "Other Solutions" section on service pages uses compact navy rectangular chips (service name only, no description, single row).  
**Zensical behaviour:** "Other Solutions" uses full `st-card` elements with descriptions, displayed in a 3-col grid.  
**Reason retained:** The Zensical card approach provides more information and is accessible. The compact chips from the static site are a navigation-only element that was generated dynamically from JS.

---

## Feature List Icons on Service Pages

**Status:** Acceptable difference  
**Static behaviour:** "What's Included" feature lists on service pages have emoji icons (✈️ 🛡️ etc.) rendered via JS from `i18n/en.js`.  
**Zensical behaviour:** Clean gold-border tile grid without icons.  
**Reason retained:** The Zensical tile grid is visually clean and accessible. Adding icons per-item would require adding them to each markdown file individually.

---

## Static Site — JS-Driven Content

**Status:** Informational  
**Static behaviour:** Several sections of the static site render content dynamically via JavaScript (`i18n/en.js`, `articles.html` tabs, `services/*.html` feature grids). These sections appear blank in screenshots if JS has not executed.  
**Zensical behaviour:** All content is baked into Markdown and renders without JavaScript.  
**Result:** Zensical actually has BETTER content availability than the static site for search engines, screenshot tools, and users with JS disabled.
