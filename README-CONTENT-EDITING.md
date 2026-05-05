# Content Editing Guide — Secure Tours & Travel

This guide is for editing the website content. All pages are plain text files — no coding required.

---

## Where to Find Each Page

All content lives in the `docs/` folder:

| Page | File |
|---|---|
| Home | `docs/index.md` |
| About Us | `docs/about.md` |
| Contact | `docs/contact.md` |
| Event Solutions | `docs/event-solutions.md` |
| Resources & Downloads | `docs/resources.md` |
| Tourism Services (overview) | `docs/services/index.md` |
| Tours & Travel Solutions | `docs/services/tours-travel-solutions.md` |
| Executive Guest Management | `docs/services/executive-guest-management.md` |
| Exclusive Transfer Assistance | `docs/services/exclusive-transfer-assistance.md` |
| P.A.S.S. — Athlete | `docs/services/pass-athlete.md` |
| P.A.S.S. — Performing Artist | `docs/services/pass-artist.md` |
| Concierge & Chaperone | `docs/services/concierge-chaperone.md` |
| S.T.A.G.E. | `docs/services/stage.md` |
| Bereavement Travel Support | `docs/services/bereavement-travel-support.md` |
| Solo Traveller Assist | `docs/services/solo-traveller-assist.md` |
| Articles & Case Studies | `docs/articles/index.md` |
| Matthew Harrison Profile | `docs/articles/matthew-harrison-profile.md` |
| Vivid Sydney Case Study | `docs/articles/vivid-sydney.md` |
| Carriageworks Case Study | `docs/articles/carriageworks.md` |
| Gary O'Riordan Endorsement | `docs/articles/gary-oriordan-endorsement.md` |
| Janene Rees Endorsement | `docs/articles/janene-rees-endorsement.md` |

---

## How to Edit Text

Open any `.md` file in a text editor (Notepad, TextEdit, or any editor you prefer). The content looks like this:

```
## Section Heading

This is a paragraph of text. Just edit it like a Word document.

- Bullet point one
- Bullet point two
```

**To change body text:** just type over it.

**To change a heading:** edit the line that starts with `##` or `###`.

**To change a bullet point:** edit the line that starts with `-`.

The `#` characters are just heading markers — don't remove them, just change the words after them.

---

## The Top Section of Each File

Every file starts with a short block between `---` lines:

```
---
title: Page Title Here
description: "Short description for search engines."
---
```

- **title** — the browser tab title and page heading
- **description** — the text Google shows in search results

You can safely edit both of these.

---

## Adding a New Article or Case Study

1. Create a new file in `docs/articles/` — e.g. `docs/articles/new-case-study.md`
2. Start it with the title block (copy from an existing article file)
3. Write your content using the same style as the other articles
4. Add a link to it in `docs/articles/index.md`
5. Add it to `zensical.toml` under the `[[nav]]` section for Articles

---

## Contact Form

The contact form in `docs/contact.md` uses Formspree. The form ID placeholder is `YOUR_FORM_ID`. To activate the form:

1. Create a free account at formspree.io
2. Create a new form and copy the form ID (looks like `xyzabcde`)
3. In `docs/contact.md`, replace `YOUR_FORM_ID` with your actual ID

---

## Images and Downloads

- Images are in `assets/` — replace files there to update photos
- PDF downloads are in `assets/downloads/` — drop replacement PDFs in with the same filename

---

## Previewing the Site Locally

If you have Python installed:

```
pip install zensical
zensical serve
```

Then open `http://localhost:8000` in your browser. Changes to `.md` files will reload automatically.

---

## Deploying

The site deploys automatically on DigitalOcean App Platform when changes are pushed to the `feature/zensical` branch on GitHub.
