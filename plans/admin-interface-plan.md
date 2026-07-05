# Admin interface — review and plan

**Date:** 2026-07-05
**Scope:** How the company admin gets a safe content-editing interface, what is already in flight, what deployments look like today, and the sequenced steps to get there.

---

## 1. Where things stand today

### Deployed state (production/staging)

- **`main`** is the customer-approved static HTML prototype: 22 bespoke pages, duplicated nav/footer in every file, `js/translations.js` as the JS-injected content source, hand-maintained `sitemap.xml`. Deployed to DigitalOcean App Platform; staging at `securetours.staging-site.au`.
- The DO app spec for the *current* static deployment is **not in the repo** — `main` has no `.do/app.yaml`. The live app configuration exists only in the DO dashboard (click-ops).
- The contact form on `main` is **non-functional**: `js/main.js:47` still has the `FORMSPREE_FORM_ID` placeholder.
- There is nothing an admin can safely edit here. Every content change means hand-editing HTML duplicated across ~22 files (plus `translations.js`), which is exactly the "blow up the site design" risk we want to remove.

### In flight: PR #4 — Astro rewrite (`feature/astro`, TOU-159)

Open, mergeable-clean, 27 commits ahead of `main`, `main` has **not** moved since it branched (0 behind). No reviews yet, no comments, and **no CI** (no `.github/workflows` on either branch — the parity harness is local-only).

What it establishes:

- **Astro 5.18, `output: 'static'`** — the deployed site remains fully static; no runtime server for pages.
- **Content collections as the editor surface.** The 9 service pages are generated from `src/content/services/*.md` (front-matter + markdown body), validated by a Zod schema in `src/content.config.ts`. This is the foundation the admin interface sits on.
- **Visual parity harness** (pytest + Playwright) comparing built DOM against `static-prototype/` (the approved design, kept in-tree as the reference). This is the design-safety gate.
- **`contact-api/`** — a small Express + Resend service replacing the dead Formspree wiring, with honeypot, validation, and a 503 fallback until `RESEND_API_KEY` is set.
- **`.do/app.yaml`** targeting the production domains (`securetours.com.au` / `www`) as a static site built from **branch `feature/astro`** plus the `contact-api` service (`/api` route, Sydney region). Note: the app is still named `secure-tours-zensical` (leftover from the abandoned PR #3 attempt).
- The PR names **Sveltia CMS integration as the next task ("#56")** — that reference doesn't resolve to anything in this repo (issues are empty, PRs stop at #4); it presumably points at an external tracker and should be re-anchored to a real ticket.

The abandoned alternative (PR #3, Zensical/MkDocs) was closed for insufficient layout fidelity — the Astro direction is the settled one.

### Deliberate content decisions already made on the Astro branch

- The JS language toggle (`en`/`zh`) is gone; Mandarin survives as downloadable PDFs on Resources plus "languages we support" copy. Consistent with the earlier TOU-133 "remove lang selector" decision — flagging so it's confirmed, not accidental.
- Service-page FAQs exist in the schema but are commented out in the markdown pending real answers from the client.

---

## 2. The admin interface: recommendation

**Sveltia CMS on top of the Astro content collections** — confirming the direction already named in PR #4. Rationale:

- **Git-based, no backend.** Sveltia is a single static admin page (`/admin`) that commits directly to GitHub. No database, no CMS server to run or patch; the site stays a static build. Content edits are commits — full history, trivial rollback, and they flow through the same build pipeline as code.
- **Design safety is structural, not behavioural.** The admin edits only the fields the CMS config exposes (title, lead, features list, etc.). Layout lives in `.astro` components the CMS never touches. Three independent guards:
  1. **Zod schema** in `content.config.ts` — a malformed edit fails the build.
  2. **DO App Platform semantics** — a failed build does not deploy; the last good version stays live. A bad edit can never take the site down.
  3. **Parity harness in CI** (to be added, step 2 below) — catches structural drift.
- **The alternative paths are worse for this site**: Decap CMS (same architecture, less maintained, weaker UX), a hosted CMS (Contentful/Sanity — monthly cost, content leaves git, overkill for ~20 pages), or a custom admin app (build + maintain burden nobody wants for a marketing site).

**One real prerequisite: authentication.** Sveltia's GitHub backend needs an OAuth flow — this is the only server-ish piece:

- Register a **GitHub OAuth App** and deploy **`sveltia-cms-auth`** (the tiny token-exchange endpoint). It ships as a Cloudflare Worker (free tier is fine); alternatively it can be run as a second small service on the existing DO app alongside `contact-api` to keep infrastructure in one place.
- The admin needs a **GitHub account added as a collaborator** on `goodtune/securetours` (write access). Their edits land as their own commits — attributable and auditable.

**Publish flow decision** (recommend A):

- **A. Commit straight to `main`, rely on the build gate.** Simplest mental model for a non-technical admin: save → live in ~2 minutes, or (on schema failure) nothing changes. Recommended given guards 1–3 above.
- **B. Commit to a `content` branch, auto-PR to `main`.** Adds a human review step but requires someone to merge every wording tweak — friction that tends to kill CMS adoption. Keep as fallback if A proves too loose.

---

## 3. Sequenced next steps

### Step 0 — Review and merge PR #4 (blocker for everything)

The admin interface targets the Astro content collections, so nothing ships until the rewrite lands. Pre-merge checklist:

- [ ] Review + client sign-off on the built site (the parity harness is the evidence).
- [ ] Confirm the zh-toggle removal is an accepted decision.
- [ ] Rename the DO app in `.do/app.yaml` (`secure-tours-zensical` → e.g. `secure-tours`).
- [ ] Merge. Then immediately change `.do/app.yaml` `branch: feature/astro` → `branch: main` (both components) — as written, post-merge pushes to `main` would not deploy.

### Step 1 — Align deployments with the repo

- [ ] Point the **staging** app (`securetours.staging-site.au`) at `main` building the Astro site; verify end-to-end (build, routes, 404, downloads).
- [ ] Set the real `RESEND_API_KEY` in the DO dashboard (encrypted env var on `contact-api`); verify DKIM/SPF for `noreply@securetours.com.au` in Resend; test the contact form. This also fixes the currently-dead form.
- [ ] Production cutover of `securetours.com.au`/`www` per the domains block in `app.yaml` (DNS/zone timing to be scheduled with the client).

### Step 2 — CI as the safety net (before the admin gets keys)

- [ ] GitHub Actions workflow on PRs and pushes to `main`: `npm ci && npm run build` + the pytest/Playwright parity harness.
- [ ] Branch protection on `main` requiring the build check. (If publish flow A is chosen, require only the build — the harness can stay advisory on content-only commits so a slow check doesn't block copy edits; revisit once timings are known.)
- [ ] Optional: `@astrojs/sitemap` so the sitemap stops being hand-maintained — one less thing content edits can silently break.

### Step 3 — Sveltia CMS integration (the admin interface itself)

- [ ] `public/admin/index.html` (loads Sveltia) + `public/admin/config.yml`.
- [ ] Model the **services** collection in `config.yml` mirroring the Zod schema: string/text widgets for `title`, `meta_description`, `hero_tag`, `hero_sub`, `lead`; list-of-object widget for `features` (`icon`, `text`) and `faqs`; object widget for `home_card` and `cta`; markdown body for the "How It Works" prose. Keep `order`, `coming_soon`, `related_services` exposed but clearly labelled.
- [ ] Register the GitHub OAuth App; deploy `sveltia-cms-auth` (Cloudflare Worker, or DO service next to `contact-api`); wire `base_url` in `config.yml`.
- [ ] Add the admin as a repo collaborator; walk through login → edit → save → auto-deploy → rollback (revert commit) once, together.
- [ ] Ticket this properly to replace the dangling "#56" reference in PR #4's description.

### Step 4 — Widen the editable surface (incremental, schema-first)

Each of these follows the same recipe — extract to a content collection with a Zod schema first, then expose it in `config.yml`:

- [ ] **Articles/case studies** (currently 6 bespoke `.astro` pages) → an `articles` collection.
- [ ] **FAQs** — already schema'd; once the client supplies answers, uncomment and let them own the copy via the CMS.
- [ ] **Resources/downloads** — a `downloads` collection (title, language, file) with file uploads to `public/assets/downloads/`.
- [ ] **Site globals** — phone number, enquiry email, footer copy — as a singleton data file, so contact details stop being hardcoded in components.
- [ ] Home/about hero copy last, and conservatively: the more layout-adjacent the field, the more it stays code.

### Step 5 — Retire scaffolding (later)

- [ ] Once the client has signed off the Astro build in production, decide the future of `static-prototype/` + the parity harness: keep as the design contract (recommended for now — it's what makes CMS-era changes verifiable), revisit after the CMS has been in use for a while.

---

## 4. Open questions / decisions needed

1. **Publish flow A or B** (direct-to-`main` vs. PR-per-edit)? Recommendation: A.
2. **Where does `sveltia-cms-auth` run** — Cloudflare Worker (free, Sveltia's reference deployment) or a third component on the DO app (single-vendor)?
3. **Does the admin have / want a GitHub account?** Required for Sveltia's auth model; they never see GitHub itself, only the CMS UI.
4. **What does "#56" in PR #4 refer to?** Needs re-anchoring to a real ticket (TOU-###?) so the CMS work is tracked.
5. **Production cutover timing** for `securetours.com.au` — DNS zone changes need scheduling with whoever controls the domain.
