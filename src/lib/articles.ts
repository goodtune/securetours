/**
 * Article copy loaded from src/content/articles/*.yaml (the CMS editor
 * surface for the five article pages) and validated with Zod at build time.
 *
 * Three article shapes exist: endorsement letters, case studies, and the
 * feature profile. Keep these schemas in sync with the field definitions
 * in src/pages/admin/config.yml.ts.
 */
import { z } from 'astro/zod';

import garyRaw from '../content/articles/gary-oriordan-endorsement.yaml';
import janeneRaw from '../content/articles/janene-rees-endorsement.yaml';
import vividRaw from '../content/articles/vivid-sydney.yaml';
import carriageworksRaw from '../content/articles/carriageworks.yaml';
import matthewRaw from '../content/articles/matthew-harrison-profile.yaml';

const meta = z.object({ title: z.string(), description: z.string() });
const link = z.object({ label: z.string(), href: z.string() });
const hero = z.object({ label: z.string(), title: z.string(), sub: z.string() });
const ctaBand = z.object({ title: z.string(), body: z.string(), primary: link, outline: link });
const nav = z.object({ prev: link, next: link });

function parseArticle<T extends z.ZodTypeAny>(schema: T, raw: unknown, file: string): z.infer<T> {
  const result = schema.safeParse(raw);
  if (!result.success) {
    throw new Error(
      `Invalid article content in src/content/articles/${file}:\n${result.error.issues
        .map((i) => `  ${i.path.join('.')}: ${i.message}`)
        .join('\n')}`,
    );
  }
  return result.data;
}

const endorsementSchema = z.object({
  meta,
  crumb: z.string(),
  hero,
  context: z.object({ title: z.string(), body: z.string() }),
  letter: z.object({
    avatar: z.string(),
    author_name: z.string(),
    author_title: z.string(),
    date: z.string(),
    paragraphs: z.array(z.string()),
    salutation_lines: z.array(z.string()),
    download: z.object({ label: z.string(), href: z.string(), size: z.string() }).optional(),
  }),
  nav,
  cta_band: ctaBand,
});

const caseStudySchema = z.object({
  meta,
  crumb: z.string(),
  hero,
  meta_items: z.array(z.object({ label: z.string(), value: z.string() })),
  background: z.object({ title: z.string(), paragraphs: z.array(z.string()) }),
  event_types: z
    .object({
      title: z.string(),
      items: z.array(z.object({ icon: z.string(), label: z.string() })),
    })
    .optional(),
  challenge: z.object({
    title: z.string(),
    paragraphs: z.array(z.string()),
    bullets: z.array(z.string()),
  }),
  approach: z.object({ title: z.string(), paragraphs: z.array(z.string()) }),
  services: z.object({ title: z.string(), items: z.array(z.string()) }),
  outcomes: z.object({
    title: z.string(),
    stats: z.array(z.object({ num: z.string(), label: z.string() })),
    paragraphs: z.array(z.string()),
  }),
  confidentiality: z.string(),
  nav,
  cta_band: ctaBand,
});

const profileSchema = z.object({
  meta,
  crumb: z.string(),
  hero,
  meta_items: z.array(z.object({ label: z.string(), value: z.string() })),
  sections: z.array(
    z.object({
      title: z.string(),
      paragraphs: z.array(z.string()),
      pull_quote: z.string().optional(),
    }),
  ),
  nav,
  cta_band: ctaBand,
});

export const garyEndorsement = parseArticle(
  endorsementSchema,
  garyRaw,
  'gary-oriordan-endorsement.yaml',
);
export const janeneEndorsement = parseArticle(
  endorsementSchema,
  janeneRaw,
  'janene-rees-endorsement.yaml',
);
export const vividSydney = parseArticle(caseStudySchema, vividRaw, 'vivid-sydney.yaml');
export const carriageworks = parseArticle(caseStudySchema, carriageworksRaw, 'carriageworks.yaml');
export const matthewProfile = parseArticle(
  profileSchema,
  matthewRaw,
  'matthew-harrison-profile.yaml',
);
