/**
 * Page copy loaded from src/content/pages/*.yaml (the CMS editor surface
 * for non-collection pages) and validated with Zod at build time.
 *
 * The schemas here are the gate that stops a bad CMS edit from deploying —
 * keep them in sync with the field definitions in
 * src/pages/admin/config.yml.ts, exactly like src/content.config.ts for
 * the services collection.
 */
import { z } from 'astro/zod';

import homeRaw from '../content/pages/home.yaml';
import aboutRaw from '../content/pages/about.yaml';
import contactRaw from '../content/pages/contact.yaml';
import eventSolutionsRaw from '../content/pages/event-solutions.yaml';
import resourcesRaw from '../content/pages/resources.yaml';
import faqRaw from '../content/pages/faq.yaml';
import notFoundRaw from '../content/pages/not-found.yaml';
import servicesIndexRaw from '../content/pages/services-index.yaml';
import articlesIndexRaw from '../content/pages/articles-index.yaml';
import siteRaw from '../content/pages/site.yaml';

const link = z.object({ label: z.string(), href: z.string() });
const meta = z.object({ title: z.string(), description: z.string() });

function parsePage<T extends z.ZodTypeAny>(schema: T, raw: unknown, file: string): z.infer<T> {
  const result = schema.safeParse(raw);
  if (!result.success) {
    throw new Error(
      `Invalid page content in src/content/pages/${file}:\n${result.error.issues
        .map((i) => `  ${i.path.join('.')}: ${i.message}`)
        .join('\n')}`,
    );
  }
  return result.data;
}

const homeSchema = z.object({
  meta,
  hero: z.object({
    tag: z.string(),
    title: z.string(),
    sub: z.string(),
    cta_primary: link,
    cta_secondary: link,
  }),
  stats: z.array(z.object({ number: z.string(), label: z.string() })),
  solutions: z.object({
    label: z.string(),
    title: z.string(),
    intro: z.string(),
    featured_tag: z.string(),
    featured_cta_label: z.string(),
  }),
  about: z.object({
    label: z.string(),
    title: z.string(),
    text: z.string(),
    features: z.array(z.string()),
    cta_label: z.string(),
    badge: z.object({
      number: z.string(),
      label: z.string(),
      footnote: z.string(),
      footnote_tag: z.string(),
    }),
  }),
  why: z.object({
    label: z.string(),
    title: z.string(),
    items: z.array(z.object({ icon: z.string(), title: z.string(), text: z.string() })),
  }),
});

export const home = parsePage(homeSchema, homeRaw, 'home.yaml');

const aboutSchema = z.object({
  meta,
  hero: z.object({ label: z.string(), title: z.string(), sub: z.string() }),
  who: z.object({
    label: z.string(),
    title: z.string(),
    lead: z.string(),
    badge: z.object({ number: z.string(), label: z.string(), footnote: z.string() }),
  }),
  values: z.object({
    label: z.string(),
    title: z.string(),
    items: z.array(z.object({ title: z.string(), body: z.string() })),
  }),
  clients: z.object({ label: z.string(), title: z.string(), items: z.array(z.string()) }),
  parent: z.object({
    label: z.string(),
    title: z.string(),
    intro: z.string(),
    cta_label: z.string(),
    creds: z.array(z.object({ value: z.string(), label: z.string() })),
    creds_wide: z.object({ value: z.string(), label: z.string() }),
    features: z.array(z.string()),
  }),
});

export const about = parsePage(aboutSchema, aboutRaw, 'about.yaml');

const contactSchema = z.object({
  meta,
  hero: z.object({ title: z.string(), sub: z.string() }),
  info: z.object({
    label: z.string(),
    title: z.string(),
    intro: z.string(),
    phone: z.string(),
    email: z.string(),
    location: z.string(),
    languages_note: z.string(),
  }),
  form: z.object({ success_title: z.string(), success_body: z.string() }),
});

export const contact = parsePage(contactSchema, contactRaw, 'contact.yaml');

const iconTitleBody = z.object({ icon: z.string(), title: z.string(), body: z.string() });
const titleBody = z.object({ title: z.string(), body: z.string() });

const eventSolutionsSchema = z.object({
  meta,
  hero: z.object({ label: z.string(), title: z.string(), sub: z.string() }),
  lead: z.object({
    label: z.string(),
    title: z.string(),
    lead: z.string(),
    paragraphs: z.array(z.string()),
    cta_label: z.string(),
    credentials: z.object({ title: z.string(), items: z.array(z.string()) }),
  }),
  offerings: z.object({
    label: z.string(),
    title: z.string(),
    intro: z.string(),
    events: z.array(iconTitleBody),
  }),
  film_tv: z.object({
    label: z.string(),
    title: z.string(),
    intro: z.string(),
    panel: z.object({
      label: z.string(),
      title: z.string(),
      paragraphs: z.array(z.string()),
      capabilities: z.array(titleBody),
      cta_label: z.string(),
    }),
  }),
  portfolio: z.object({
    label: z.string(),
    title: z.string(),
    intro: z.string(),
    items: z.array(z.string()),
  }),
  differentiators: z.object({
    label: z.string(),
    title: z.string(),
    items: z.array(iconTitleBody),
  }),
  case_studies: z.object({
    label: z.string(),
    title: z.string(),
    intro: z.string(),
    cards: z.array(
      z.object({
        label: z.string(),
        title: z.string(),
        text: z.string(),
        href: z.string().optional(),
        cta: z.string(),
      }),
    ),
    all_link_label: z.string(),
  }),
  cta_band: z.object({ title: z.string(), body: z.string(), primary: link, outline: link }),
});

export const eventSolutions = parsePage(
  eventSolutionsSchema,
  eventSolutionsRaw,
  'event-solutions.yaml',
);

const ctaBand = z.object({ title: z.string(), body: z.string(), primary: link, outline: link });

const resourcesSchema = z.object({
  meta,
  hero: z.object({ label: z.string(), title: z.string(), sub: z.string() }),
  library_heading: z.string(),
  categories: z.array(
    z.object({
      heading: z.string(),
      note: z.string().optional(),
      cards: z.array(
        z.object({
          name: z.string(),
          meta: z.string(),
          badge: z.string(),
          href: z.string().optional(),
          aria_label: z.string().optional(),
        }),
      ),
      footnote: z.string().optional(),
    }),
  ),
  cta_band: ctaBand,
});

export const resources = parsePage(resourcesSchema, resourcesRaw, 'resources.yaml');

const faqSchema = z.object({
  meta,
  hero: z.object({ label: z.string(), title: z.string(), sub: z.string() }),
  faqs: z.array(z.object({ question: z.string(), answer: z.string() })),
  cta_band: ctaBand,
});

export const faq = parsePage(faqSchema, faqRaw, 'faq.yaml');

const notFoundSchema = z.object({
  meta,
  title: z.string(),
  body: z.string(),
  primary: link,
  outline: link,
});

export const notFound = parsePage(notFoundSchema, notFoundRaw, 'not-found.yaml');

const servicesIndexSchema = z.object({
  meta,
  hero: z.object({ label: z.string(), title: z.string(), sub: z.string() }),
  featured: z.object({
    tag: z.string(),
    title: z.string(),
    text: z.string(),
    cta_label: z.string(),
    href: z.string(),
    icon: z.string(),
  }),
  cards: z.array(
    z.object({ icon: z.string(), title: z.string(), body: z.string(), href: z.string() }),
  ),
  card_link_label: z.string(),
  cta_band: z.object({ title: z.string(), body: z.string(), button: link }),
});

export const servicesIndex = parsePage(servicesIndexSchema, servicesIndexRaw, 'services-index.yaml');

const articlesIndexSchema = z.object({
  meta,
  hero: z.object({ label: z.string(), title: z.string(), sub: z.string() }),
  library_heading: z.string(),
  testimonials: z.object({
    label: z.string(),
    title: z.string(),
    cards: z.array(
      z.object({
        avatar: z.string(),
        name: z.string(),
        title: z.string(),
        badge: z.string(),
        date: z.string(),
        quote: z.string(),
        cta_label: z.string(),
        cta_href: z.string(),
      }),
    ),
  }),
  case_studies: z.object({
    label: z.string(),
    title: z.string(),
    view_link: link,
    cards: z.array(
      z.object({
        label: z.string(),
        title: z.string(),
        text: z.string(),
        href: z.string().optional(),
        cta: z.string(),
      }),
    ),
  }),
  audio: z.object({
    label: z.string(),
    title: z.string(),
    intro: z.string(),
    panel: z.object({
      label: z.string(),
      title: z.string(),
      body: z.string(),
      items: z.array(
        z.object({ title: z.string(), meta: z.string(), placeholder: z.string() }),
      ),
      note: z.string(),
      cta_label: z.string(),
    }),
  }),
  articles: z.object({
    label: z.string(),
    title: z.string(),
    intro: z.string(),
    cards: z.array(
      z.object({
        category: z.string(),
        title: z.string(),
        text: z.string(),
        href: z.string().optional(),
        badge: z.string().optional(),
      }),
    ),
  }),
  cta_band: ctaBand,
});

export const articlesIndex = parsePage(articlesIndexSchema, articlesIndexRaw, 'articles-index.yaml');

const siteSchema = z.object({
  cta_band: z.object({ title: z.string(), body: z.string(), primary: link, outline: link }),
  footer: z.object({
    brand_blurb: z.string(),
    abn_note: z.string(),
    phone: z.string(),
    email: z.string(),
    location: z.string(),
    copyright: z.string(),
  }),
  afs_strip: z.object({ division: z.string(), credentials: z.string() }),
});

export const site = parsePage(siteSchema, siteRaw, 'site.yaml');

/** "+61 414 499 778" → "tel:+61414499778" */
export const telHref = (phone: string) => `tel:${phone.replace(/\s+/g, '')}`;
