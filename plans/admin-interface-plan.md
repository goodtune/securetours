# Admin interface — review and plan (build on the existing static site)

**Date:** 2026-07-08
**Decision context:** The Astro rewrite (PR #4) has been closed and will not be used. The plan below layers a safe content-editing interface **on top of the existing static HTML site on `main`** — no framework, no rewrite.

---

## 1. Where things stand today

### Deployed state

- `main` is the customer-approved static site: 22 standalone HTML pages, duplicated nav/footer per page, `css/style.css` design system, `js/main.js` + `js/translations.js`. Deployed to DigitalOcean App Platform; staging at `securetours.staging-site.au`.
- The DO app spec is **not in the repo** — the live configuration exists only in the DO dashboard.
- The contact form is **non-functional**: `js/main.js:47` still carries the `FORMSPREE_FORM_ID` placeholder.
- No CI of any kind — nothing runs on push.

### The key finding: the site already has a content layer

This is what makes a no-rewrite admin interface viable. Content on `main` is not uniformly hardcoded — a large share of it already flows through **`js/translations.js`**:

- **`TRANSLATIONS`** — 114 keyed strings (en + zh, key sets identical): nav labels, home hero/stats/about/why-choose, contact page, footer. Applied at runtime by `applyTranslations('en')` in `main.js`, which swaps `el.innerHTML` for every `[data-i18n]` element.
- **`SERVICE_TRANSLATIONS`** — 9 services × `{hero_tag, title, sub, lead, features[]}`. Every `services/*.html` page has a small inline script that renders its hero, lead paragraphs, and feature list from this object at runtime.

Coverage today (count of `data-i18n` bindings per page):

| Well covered | Zero coverage (fully hardcoded HTML) |
|---|---|
| `index.html` (65), `contact.html` (34), `about.html` (34), all 9 `services/*.html` (13–20 each + `SERVICE_TRANSLATIONS`), `services/index.html` (20) | `resources.html`, `event-solutions.html`, `articles.html`, `articles/*.html` (5 pages), `404.html` |

So the seam we need — **content as data, design as code** — already exists for the home page, about, contact, and all nine service pages. The admin interface job is to (a) turn that data into files a CMS can edit, and (b) progressively widen the seam to the hardcoded pages.

### Two problems with the current mechanism to fix along the way

1. **`translations.js` is code, not data.** It's a JS source file with string-escaping rules; a non-technical editor (or a CMS) shouldn't write JS.
2. **Content only appears via JavaScript at runtime.** The inline HTML holds default copy that `applyTranslations` overwrites on load. If content is edited only in the data layer, the raw HTML drifts stale — crawlers and no-JS visitors see old copy. (The service-page hero/lead/features are worse: empty placeholders until JS runs.)

Both are fixed by one small build step (Step 2 below) — a script, not a framework.

---

## 2. The admin interface: recommendation

**Sveltia CMS editing JSON content files, with a tiny Node build script that bakes the content into the existing HTML at deploy time.** The HTML pages stay exactly as they are — they become the templates. No SSG, no components, no rewrite.

Why this shape:

- **Git-based, no backend.** Sveltia CMS is a single static admin page (`/admin`) that commits directly to GitHub. No database, no CMS server; edits are commits — full history, trivial rollback, and they flow through the same deploy pipeline as code.
- **Design safety is structural.** The admin edits only values in JSON files. Layout, classes (including the fragile `.reveal` animation classes), nav, and footer live in HTML/CSS the CMS never touches. A content edit *cannot* change markup structure.
- **It reuses the site's own mechanism.** The build script does at build time exactly what `main.js` already does at runtime: find `[data-i18n]`, substitute the keyed string; render the service hero/lead/features blocks. Behaviour is already specified by working code — the script mirrors it.
- **Deploy gate.** DO App Platform static sites accept a `build_command`. If the build script fails (malformed JSON, unknown key, missing field), the deploy fails and **the last good version stays live**. A bad edit can never take the site down.

Alternatives considered:

- **CloudCannon** — hosted CMS with visual editing over plain HTML; the closest "zero work" fit for this architecture, but paid SaaS (from ~US$49/mo), content workflow tied to a vendor. Worth a look if budget beats build effort; not recommended as default.
- **Decap CMS** — same architecture as Sveltia, weaker maintenance and UX; Sveltia is its actively-developed successor.
- **Contentful/Sanity etc.** — monthly cost, content leaves git, and still needs the same build step. Overkill for ~20 pages.
- **Custom admin app** — build and maintain burden nobody wants for a marketing site.

**One real prerequisite: authentication.** Sveltia's GitHub backend needs an OAuth token exchange — the only server-ish piece:

- Register a **GitHub OAuth App** and deploy **`sveltia-cms-auth`** (a tiny token-exchange endpoint; ships as a Cloudflare Worker, free tier fine).
- The admin needs a **GitHub account added as collaborator** on `goodtune/securetours` (write). They never see GitHub — only the CMS UI — but their edits land as their own attributable commits.

**Publish flow decision** (recommend A):

- **A. Commit straight to `main`; rely on the build gate.** Save → live in a couple of minutes, or (on validation failure) nothing changes. Simplest mental model for a non-technical admin.
- **B. CMS commits to a `content` branch; staging app deploys that branch for preview; a person merges to `main`.** Real preview + review, at the cost of a merge step per wording tweak. Viable later if A proves too loose.

**Honest scope statement:** with this model the admin edits *copy on existing pages* — headings, paragraphs, feature lists, service descriptions, contact details. Creating new pages, changing navigation, or altering layout stays developer work. That is the "safely without blowing up the site design" contract.

---

## 3. Sequenced next steps

### Step 0 — Housekeeping from the rewrite decision

- [ ] PR #4 closed (done). Archive or delete `feature/astro` and `feature/zensical` branches so nobody builds on them.
- [ ] Nothing needs salvaging for this plan; two ideas from that branch are worth borrowing later if needs grow (Playwright layout-regression checks; a first-party contact API).

### Step 1 — Bring the deployment under version control

- [ ] Export the current DO app spec (dashboard → app → Settings → App Spec, or `doctl apps spec get`) and commit it as `.do/app.yaml`. Infra changes become reviewable, and the build step in Step 2 is a one-line diff instead of dashboard clicking.
- [ ] Document which apps/branches serve staging (`securetours.staging-site.au`) and production, and what `securetours.com.au` currently points at.

### Step 2 — Content becomes data + a build step (the enabling move)

No visual change; pure refactor of where content lives:

- [ ] Convert `js/translations.js` into JSON under `content/`: e.g. `content/site.en.json`, `content/site.zh.json` (the 114 `TRANSLATIONS` keys) and `content/services/*.en.json` (+ `.zh.json`) for the 9 `SERVICE_TRANSLATIONS` entries.
- [ ] Write `scripts/build.js` (Node, cheerio or similar — a dependency, not a framework) that copies the site into `dist/` and:
  1. **Regenerates `js/translations.js`** from the JSON, so runtime behaviour is byte-for-byte unchanged.
  2. **Bakes the `en` content into the HTML** — substitutes every `[data-i18n]` element's innerHTML and renders the service hero/lead/features blocks — fixing the stale-HTML/no-JS/SEO problem as a side effect.
  3. **Fails loudly** on malformed JSON, a `data-i18n` key with no JSON entry, en/zh key-set mismatch, or a missing service field. This is the schema gate.
- [ ] DO app: set `build_command: npm ci && node scripts/build.js`, `output_dir: dist` (roll out on staging first).
- [ ] Escape values as text by default when baking; keep an explicit allowlist of keys permitted to carry markup (e.g. `hero_title` with its `<em>`), so a CMS edit can't inject broken markup site-wide.

### Step 3 — CI before the admin gets keys

- [ ] GitHub Actions on PRs and pushes to `main`: run `node scripts/build.js` (which validates everything above). Fast — seconds, not minutes.
- [ ] Branch protection on `main` requiring that check.
- [ ] Optional: Playwright smoke screenshots of key pages as an artifact — a cheap eyeball diff, borrowing the idea (not the code) from the closed rewrite.

### Step 4 — Sveltia CMS integration (the admin interface itself)

- [ ] Add `admin/index.html` (loads Sveltia from CDN) + `admin/config.yml`.
- [ ] Model collections over the JSON files: a "Site copy" file collection for `content/site.en.json` grouped by page (Home, About, Contact, Nav/Footer) using string/text widgets; a "Services" folder collection over `content/services/*.en.json` with fields `title`, `hero_tag`, `sub`, `lead` (text), `features` (list of strings). Label fields in plain English ("Home page — main headline"), not key names.
- [ ] Register the GitHub OAuth App; deploy `sveltia-cms-auth` (Cloudflare Worker); wire it in `config.yml`.
- [ ] Add the admin as repo collaborator; walk through login → edit → save → auto-deploy → rollback (revert commit) once, together.
- [ ] Decide zh handling: expose the `.zh.json` files as a second collection if the admin maintains Mandarin copy, or leave zh developer-maintained (the language selector was removed in TOU-133; zh is currently dormant).

### Step 5 — Widen the editable surface (incremental, page by page)

Same recipe each time — add `data-i18n` keys (or a small render block) to a hardcoded page, move its copy into JSON, expose in the CMS config:

- [ ] `event-solutions.html` and `resources.html` — currently zero coverage; likely the most-edited marketing pages.
- [ ] `articles.html` hub — consider driving the article *cards* (title, blurb, link) from a JSON list so the admin can reorder/retitle; article pages themselves stay developer work.
- [ ] Contact details (phone number, email) as content keys — they appear on many pages and are exactly what a company admin wants to self-serve.
- [ ] Keep the sitemap developer-owned (the admin can't create pages in this model, so hand-maintained `sitemap.xml` stays accurate by construction).

### Step 6 — Fix the contact form (independent, do anytime)

- [ ] Create the real Formspree form and replace the `FORMSPREE_FORM_ID` placeholder in `js/main.js` — one line, no architecture change. (If Formspree is unwanted, a small first-party endpoint like the closed PR's Resend service is the fallback; bigger lift.)

---

## 4. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Admin enters malformed content | JSON edited via CMS widgets (not raw text); build script validates; failed build ≠ failed site |
| Content injected as HTML (`innerHTML`) | Escape-by-default at bake time; explicit allowlist for the few markup-bearing keys |
| Copy looks wrong even though build passed | Publish flow B (content branch + staging preview) is the upgrade path; start with A + easy revert |
| en/zh drift | Build fails on key-set mismatch (today they're identical at 114 keys — keep it that way) |
| `.reveal` animation trap (elements stuck invisible) | Admin never touches classes or markup — content edits structurally can't introduce it |
| Duplicated nav/footer across 22 pages | Out of scope for the admin interface (developer concern); the build script gives us a natural place to add shared-partial injection later *if* we ever want it |

---

## 5. Open questions / decisions needed

1. **Publish flow A or B?** Recommendation: A (direct to `main`, build-gated), with B as the later upgrade.
2. **Where does `sveltia-cms-auth` run** — Cloudflare Worker (free, reference deployment) or somewhere already in use?
3. **Does the admin have / want a GitHub account?** Required for Sveltia's auth; they only ever see the CMS UI.
4. **Is zh content live or dormant?** The selector was removed in TOU-133 and `main.js` hardcodes `'en'`. Decide whether the CMS exposes zh or it stays developer-maintained.
5. **Formspree vs first-party contact endpoint** for Step 6.
6. **Production domain state** — confirm what `securetours.com.au` points at today so Step 1's app spec capture covers both staging and production.
