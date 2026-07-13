# Admin interface — plan (on the Astro production baseline)

**Date:** 2026-07-10
**Context:** The Astro build from `feature/astro` was found to be what actually serves `securetours.com.au` (verified byte-identical, 24/24 pages, against the branch HEAD build). `feature/astro` has therefore been merged into `main` (`--no-ff`, trees identical), and the DO app is being repointed from `feature/astro` to `main` — a content no-op. The admin interface is built on this baseline.

---

## 1. Baseline after the merge

- **Astro 5.18, fully static output** on `main`: 14 page sources + `services/[slug].astro` generating 9 service pages from `src/content/services/*.md` (front-matter validated by the Zod schema in `src/content.config.ts`). **This markdown collection is the editor surface.**
- **`contact-api/`** (Express + Resend) deployed as a second DO component at `/api`; `/api/health` is live.
- **Parity harness** (`tests/`, pytest + Playwright) comparing built DOM to `static-prototype/` — the customer-approved design contract. Local-only today; no CI exists.
- **DO App Platform** (app id `9e902f6a…`, behind Cloudflare) serving `securetours.com.au` / `www`. Deployment is managed in the DO dashboard; the checked-in `.do/app.yaml` is **not** used to deploy.

### Known issues on the baseline (fix on the admin branch — decisions confirmed)

1. **Delete `.do/app.yaml`** — it isn't used for deployment and is stale on both counts (`branch: feature/astro`, app name `secure-tours-zensical`), so it's misleading. After the dashboard repoint, keep a fresh spec export (`doctl apps spec get`) outside the repo as disaster-recovery reference.
2. **`robots.txt` is not served** (it sits at repo root, not `public/`) and **there is no `sitemap.xml`** — both 404 in production. Fix: move `robots.txt` into `public/`, add `@astrojs/sitemap`, reference it from robots.txt.
3. `RESEND_API_KEY` — confirmed real in production. Staging will not run `contact-api` at all (see §3).
4. **Untrack `tmp/`** (add to `.gitignore`) as part of this work.

---

## 2. The admin interface: approach

**Sveltia CMS over the existing content collections.** A static `/admin` page that commits to GitHub — no database, no CMS server; edits are attributable, revertible commits that flow through the same build pipeline as code.

Safety model (three independent guards):

1. **Zod schema** — a malformed edit fails `astro build`.
2. **DO build gate** — a failed build never deploys; the last good version stays live.
3. **Parity harness in CI** — catches structural/design drift.

The admin edits *content fields* (titles, leads, features, FAQs, prose). Layout, components, nav, and CSS are never reachable from the CMS. New pages/routes stay developer work.

**Prerequisite — auth:** Sveltia's GitHub backend needs an OAuth token exchange:
- Register a GitHub OAuth App; deploy `sveltia-cms-auth` (reference deployment is a free Cloudflare Worker; a third small DO component is the single-vendor alternative).
- The admin gets a GitHub account added as collaborator (write). They only ever see the CMS UI.

---

## 3. Delivery model (agreed)

Work happens on a long-lived branch (working name `feature/admin-cms`) deployed as a **staging site** (second DO app, its own subdomain). When accepted, merge to `main` → production.

Staging specifics to get right:

- **Sveltia `backend.branch`** must point at the staging branch while on staging, and at `main` in production. Drive it from an env var at build time so the same code deploys to both.
- **Staging is static-only** (decided): no `contact-api` component, no running-app cost. Consequence: the contact form on staging has no `/api/contact` endpoint and will show its failure message — acceptable; test the form on production.
- The OAuth callback points at the auth helper, not the site, so one OAuth App + one `sveltia-cms-auth` serves both domains (list both in its allowed origins).
- While staging is live, the admin's CMS edits land on the staging branch and arrive in production with the final merge. Avoid parallel content edits on `main` during that window, or merge them across promptly.
- Keep the branch rebased on `main` regularly.

---

## 4. Sequenced steps

### Step 0 — Cutover hygiene (this week)

- [x] Merge `feature/astro` → `main` (`--no-ff`, empty diff verified).
- [x] Repoint the DO app components to `main` (dashboard — Gary).
- [x] First commits on the admin branch (`feature/admin-cms`, PR #6): delete `.do/app.yaml`, move `robots.txt` to `public/`, add `@astrojs/sitemap`, untrack `tmp/`.
- [ ] Delete `feature/astro` and `feature/zensical` **only after** the repoint is confirmed.

### Step 1 — CI before the admin gets keys

- [x] GitHub Actions on PRs + pushes to `main`: `npm ci && npm run build`, then the pytest/Playwright parity harness (first run green: 402 passed, 6 skipped, ~90s).
- [ ] Branch protection on `main` requiring the build check (harness advisory at first if it proves slow on content-only commits).

### Step 2 — Sveltia CMS integration

- [x] `/admin` shell (`src/pages/admin/index.astro`) + build-time generated `/admin/config.yml` (`config.yml.ts`; `CMS_BRANCH` selects the commit branch per environment, `CMS_AUTH_BASE_URL` wires the OAuth helper).
- [x] Model the **services** collection mirroring the Zod schema: strings for `title`, `meta_description`, `hero_tag`, `hero_sub`; text for `lead`; list-of-object for `features` (`icon`, `text`) and `faqs`; objects for `home_card`, `cta`; markdown body. Expose `order`, `coming_soon`, `related_services` with clear labels. Plain-English field labels throughout.
- [ ] GitHub OAuth App + `sveltia-cms-auth`; wire `base_url` in `config.yml`.
- [x] Staging DO app live at https://securetours-staging-6i7a4.ondigitalocean.app (static-only, `CMS_BRANCH=feature/admin-cms` verified).
- [ ] Walk the admin through login → edit → save → deploy → rollback once, together.

### Step 3 — Widen the editable surface (schema-first, incremental)

- [ ] **Articles/case studies** — currently 6 bespoke `.astro` pages; extract an `articles` collection (the biggest win after services).
- [ ] **FAQs** — schema exists; when the client supplies answers, they own the copy via the CMS.
- [ ] **Resources/downloads** — a `downloads` collection with file uploads to `public/assets/downloads/`.
- [ ] **Site globals** — phone, enquiry email, footer copy as a singleton data file (they're currently hardcoded in components).
- [ ] Home/about hero copy last and conservatively — the more layout-adjacent, the more it stays code.

### Step 4 — Later

- [ ] Revisit `static-prototype/` + harness once the CMS has been in use (keep for now — it's the design contract that makes CMS-era changes verifiable).
- [ ] Publish-flow upgrade if needed: CMS commits to a content branch + auto-PR instead of direct-to-`main`.

---

## 5. Open decisions

1. **Publish flow:** direct-to-`main` with the build gate (recommended) vs. PR-per-edit.
2. **`sveltia-cms-auth` hosting:** Cloudflare Worker (free, reference) vs. third DO component.
3. **Admin's GitHub account** — needed as collaborator; confirm they have/want one.
4. **Staging domain** for the second DO app (e.g. `staging.securetours.com.au`).
5. **zh/Mandarin:** the rewrite dropped the language toggle (Mandarin remains as PDFs). Confirm this is accepted; if zh pages ever return, it becomes an i18n content-collection design question.
