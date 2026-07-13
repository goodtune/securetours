import type { APIRoute } from 'astro';

// Sveltia CMS configuration, generated at build time so each deployment
// targets the right branch. JSON is valid YAML, so we can serve the
// config as JSON without a YAML dependency.
//
// Environment variables (set in the DO build environment):
//   CMS_BRANCH        — branch the CMS commits to. Production: main.
//                       Staging must set this to its own deploy branch so
//                       edits show up on staging, not production.
//   CMS_AUTH_BASE_URL — URL of the deployed sveltia-cms-auth helper
//                       (GitHub OAuth token exchange). Until it is set,
//                       editors can sign in with a GitHub personal access
//                       token from the CMS login screen.
//
// KEEP FIELDS IN SYNC with the Zod schemas: src/content.config.ts
// (services), src/lib/pages.ts (pages + site), src/lib/articles.ts
// (articles). The schemas are the build-time gate that stops a bad CMS
// edit from deploying.
const branch = import.meta.env.CMS_BRANCH || 'main';
// base_url must be the Worker root: Sveltia appends /auth itself. Strip a
// pasted /callback suffix (that path belongs only in the GitHub OAuth App
// settings) and trailing slashes, both of which 404 the sign-in flow.
const authBase = (import.meta.env.CMS_AUTH_BASE_URL || '')
  .replace(/\/+$/, '')
  .replace(/\/callback$/, '')
  .replace(/\/+$/, '');

/* ---------- field builders (Decap/Sveltia field objects) ---------- */

type Field = Record<string, unknown>;

const str = (name: string, label: string, opts: Field = {}): Field => ({
  name,
  label,
  widget: 'string',
  ...opts,
});
const txt = (name: string, label: string, opts: Field = {}): Field => ({
  name,
  label,
  widget: 'text',
  ...opts,
});
const obj = (name: string, label: string, fields: Field[], opts: Field = {}): Field => ({
  name,
  label,
  widget: 'object',
  fields,
  ...opts,
});
const listObj = (name: string, label: string, fields: Field[], opts: Field = {}): Field => ({
  name,
  label,
  widget: 'list',
  fields,
  ...opts,
});
const listStr = (name: string, label: string, itemLabel: string, opts: Field = {}): Field => ({
  name,
  label,
  widget: 'list',
  field: str('item', itemLabel),
  ...opts,
});

const linkObj = (name: string, label: string, opts: Field = {}): Field =>
  obj(name, label, [str('label', 'Text'), str('href', 'Link target')], opts);

const metaObj = obj('meta', 'SEO (browser tab & search results)', [
  str('title', 'Page title'),
  txt('description', 'Search result description'),
]);

const heroObj = (withLabel = true): Field =>
  obj('hero', 'Page banner (hero)', [
    ...(withLabel ? [str('label', 'Small tag line above the title')] : []),
    str('title', 'Title'),
    txt('sub', 'Subtitle'),
  ]);

const ctaBandObj = (name = 'cta_band'): Field =>
  obj(name, 'Bottom call-to-action band', [
    str('title', 'Title'),
    txt('body', 'Body'),
    linkObj('primary', 'Primary (gold) button'),
    linkObj('outline', 'Secondary (outline) button'),
  ]);

const sectionHeading = [str('label', 'Small section label'), str('title', 'Section heading')];

const articleCommon = {
  before: [
    metaObj,
    str('crumb', 'Breadcrumb label'),
    heroObj(),
  ],
  after: [
    obj('nav', 'Previous / next links at the bottom', [
      linkObj('prev', 'Left link'),
      linkObj('next', 'Right link'),
    ]),
    ctaBandObj(),
  ],
};

/* ---------- collections ---------- */

const servicesCollection = {
  name: 'services',
  label: 'Service pages',
  label_singular: 'Service page',
  description:
    'The nine service detail pages (also feeds each service’s card on the home page). Text only — page layout and design are managed in code.',
  folder: 'src/content/services',
  extension: 'md',
  format: 'yaml-frontmatter',
  // New services need routes, nav and footer entries — developer work.
  create: false,
  delete: false,
  identifier_field: 'title',
  summary: '{{title}}',
  sortable_fields: ['order', 'title'],
  fields: [
    str('title', 'Page title'),
    txt('meta_description', 'Search result description (SEO)', {
      hint: 'Shown by search engines under the page title. One or two sentences.',
    }),
    str('hero_tag', 'Hero tag line', {
      hint: 'Small line above the main heading in the page banner.',
    }),
    str('hero_sub', 'Hero subtitle'),
    txt('lead', 'Opening paragraphs'),
    str('opening_quote', 'Opening quote', { required: false }),
    str('banner_statement', 'Banner statement', { required: false }),
    str('features_heading', 'Features heading', { required: false }),
    listObj('features', 'Features', [str('icon', 'Icon (emoji)'), str('text', 'Text')]),
    listStr('clients', 'Who this is for', 'Client type', { required: false }),
    str('clients_label', '“Who this is for” heading', { required: false }),
    str('tcs_note', 'Terms & conditions note', { required: false }),
    {
      name: 'related_services',
      label: 'Related services',
      widget: 'relation',
      collection: 'services',
      value_field: '{{slug}}',
      display_fields: ['{{title}}'],
      search_fields: ['title'],
      multiple: true,
      required: false,
    },
    listObj('faqs', 'FAQs', [str('question', 'Question'), txt('answer', 'Answer')], {
      required: false,
    }),
    obj(
      'cta',
      'Call to action',
      [str('title', 'Title', { required: false }), txt('body', 'Body', { required: false })],
      { required: false },
    ),
    {
      name: 'order',
      label: 'Display order',
      widget: 'number',
      value_type: 'int',
      hint: 'Position in service listings — lower numbers appear first.',
    },
    {
      name: 'coming_soon',
      label: 'Coming soon',
      widget: 'boolean',
      required: false,
      hint: 'Marks the service as not yet available.',
    },
    obj('home_card', 'Home page card', [
      str('icon', 'Icon (emoji)'),
      str('title', 'Card title (leave blank to use the page title)', { required: false }),
      txt('body', 'Card text'),
    ]),
    { name: 'body', label: 'Additional page sections (markdown)', widget: 'markdown', required: false },
  ],
};

const pagesCollection = {
  name: 'pages',
  label: 'Pages',
  description:
    'Copy for every other page of the site, plus the shared footer and call-to-action band. Text only — layout and design are managed in code.',
  editor: { preview: false },
  files: [
    {
      name: 'home',
      label: 'Home page',
      file: 'src/content/pages/home.yaml',
      fields: [
        metaObj,
        obj('hero', 'Hero (top banner)', [
          str('tag', 'Small tag line above the headline'),
          str('title', 'Main headline', {
            hint: 'May contain <em>…</em> around words to italicise them.',
          }),
          txt('sub', 'Sub-headline'),
          linkObj('cta_primary', 'Primary (gold) button'),
          linkObj('cta_secondary', 'Secondary (outline) button'),
        ]),
        listObj('stats', 'Statistics bar', [str('number', 'Big figure'), str('label', 'Caption')]),
        obj('solutions', 'Solutions section', [
          ...sectionHeading,
          txt('intro', 'Intro paragraph'),
          str('featured_tag', 'Tag on the featured (flagship) panel'),
          str('featured_cta_label', 'Featured panel button text'),
        ]),
        obj('about', 'About strip', [
          ...sectionHeading,
          txt('text', 'Paragraph'),
          listStr('features', 'Feature bullet list', 'Bullet'),
          str('cta_label', 'Button text'),
          obj('badge', 'Gold badge panel', [
            str('number', 'Big number'),
            str('label', 'Caption'),
            txt('footnote', 'Footnote paragraph'),
            str('footnote_tag', 'Footnote tag line'),
          ]),
        ]),
        obj('why', '“Why choose us” section', [
          ...sectionHeading,
          listObj('items', 'Items', [
            str('icon', 'Icon (emoji)'),
            str('title', 'Title'),
            txt('text', 'Text'),
          ]),
        ]),
      ],
    },
    {
      name: 'about',
      label: 'About page',
      file: 'src/content/pages/about.yaml',
      fields: [
        metaObj,
        heroObj(),
        obj('who', '“Who we are” section', [
          ...sectionHeading,
          txt('lead', 'Lead paragraph'),
          obj('badge', 'Gold badge panel', [
            str('number', 'Big number'),
            str('label', 'Caption'),
            txt('footnote', 'Footnote paragraph'),
          ]),
        ]),
        obj('values', 'Values section', [
          ...sectionHeading,
          listObj('items', 'Value cards', [str('title', 'Title'), txt('body', 'Text')]),
        ]),
        obj('clients', '“Who we serve” section', [
          ...sectionHeading,
          listStr('items', 'Client chips', 'Client type'),
        ]),
        obj('parent', 'AFS parent-brand section', [
          ...sectionHeading,
          txt('intro', 'Intro paragraph'),
          str('cta_label', 'Button text'),
          listObj('creds', 'Credential tiles (pair)', [
            str('value', 'Big value'),
            str('label', 'Caption'),
          ]),
          obj('creds_wide', 'Wide credential tile', [
            str('value', 'Big value'),
            str('label', 'Caption'),
          ]),
          listStr('features', 'Feature bullets', 'Bullet'),
        ]),
      ],
    },
    {
      name: 'contact',
      label: 'Contact page',
      file: 'src/content/pages/contact.yaml',
      fields: [
        metaObj,
        heroObj(false),
        obj('info', 'Contact information column', [
          ...sectionHeading,
          txt('intro', 'Intro paragraph'),
          str('phone', 'Phone number'),
          str('email', 'Email address'),
          str('location', 'Location line'),
          txt('languages_note', 'Languages note (gold box)'),
        ]),
        obj('form', 'Enquiry form messages', [
          str('success_title', 'Success heading'),
          txt('success_body', 'Success message'),
        ]),
      ],
    },
    {
      name: 'event_solutions',
      label: 'Event Solutions page',
      file: 'src/content/pages/event-solutions.yaml',
      fields: [
        metaObj,
        heroObj(),
        obj('lead', 'Lead section', [
          ...sectionHeading,
          txt('lead', 'Lead paragraph'),
          listStr('paragraphs', 'Further paragraphs', 'Paragraph'),
          str('cta_label', 'Button text'),
          obj('credentials', 'Credentials panel', [
            str('title', 'Panel heading'),
            listStr('items', 'Credential bullets', 'Bullet'),
          ]),
        ]),
        obj('offerings', 'Event service offerings', [
          ...sectionHeading,
          txt('intro', 'Intro paragraph'),
          listObj('events', 'Offering cards', [
            str('icon', 'Icon (emoji)'),
            str('title', 'Title'),
            txt('body', 'Text'),
          ]),
        ]),
        obj('film_tv', 'Film & TV section', [
          ...sectionHeading,
          txt('intro', 'Intro paragraph'),
          obj('panel', 'Navy panel', [
            str('label', 'Small label'),
            str('title', 'Panel heading'),
            listStr('paragraphs', 'Paragraphs', 'Paragraph'),
            listObj('capabilities', 'Capability tiles', [
              str('title', 'Title'),
              txt('body', 'Text'),
            ]),
            str('cta_label', 'Button text'),
          ]),
        ]),
        obj('portfolio', 'Full services portfolio', [
          ...sectionHeading,
          txt('intro', 'Intro paragraph'),
          listStr('items', 'Service list items', 'Service'),
        ]),
        obj('differentiators', '“What sets us apart” section', [
          ...sectionHeading,
          listObj('items', 'Items', [
            str('icon', 'Icon (emoji)'),
            str('title', 'Title'),
            txt('body', 'Text'),
          ]),
        ]),
        obj('case_studies', 'Case studies section', [
          ...sectionHeading,
          txt('intro', 'Intro paragraph'),
          listObj('cards', 'Cards', [
            str('label', 'Small label'),
            str('title', 'Title'),
            txt('text', 'Text'),
            str('href', 'Link target (leave blank for “coming soon”)', { required: false }),
            str('cta', 'Link/status text'),
          ]),
          str('all_link_label', '“View all” button text'),
        ]),
        ctaBandObj(),
      ],
    },
    {
      name: 'resources',
      label: 'Resources page',
      file: 'src/content/pages/resources.yaml',
      fields: [
        metaObj,
        heroObj(),
        str('library_heading', 'Hidden accessibility heading'),
        listObj('categories', 'Download categories', [
          str('heading', 'Category heading (with emoji)'),
          txt('note', 'Intro note (optional)', { required: false }),
          listObj('cards', 'Download cards', [
            str('name', 'Document name'),
            str('meta', 'Meta line (type · language · format)'),
            str('badge', 'Badge text (e.g. Download / On Request)'),
            str('href', 'File link (leave blank for non-download cards)', { required: false }),
            str('aria_label', 'Screen-reader label (optional)', { required: false }),
          ]),
          txt('footnote', 'Footnote (optional; may contain a link)', { required: false }),
        ]),
        ctaBandObj(),
      ],
    },
    {
      name: 'services_index',
      label: 'Tourism Solutions (services index)',
      file: 'src/content/pages/services-index.yaml',
      fields: [
        metaObj,
        heroObj(),
        obj('featured', 'Featured (flagship) panel', [
          str('tag', 'Small tag line'),
          str('title', 'Title'),
          txt('text', 'Text'),
          str('cta_label', 'Button text'),
          str('href', 'Button link target'),
          str('icon', 'Watermark icon (emoji)'),
        ]),
        listObj('cards', 'Service cards', [
          str('icon', 'Icon (emoji)'),
          str('title', 'Title'),
          txt('body', 'Text', {
            hint: 'This prose is deliberately different from the home-page cards and the service pages.',
          }),
          str('href', 'Link target'),
        ]),
        str('card_link_label', 'Card link text'),
        obj('cta_band', 'Bottom call-to-action band', [
          str('title', 'Title'),
          txt('body', 'Body'),
          linkObj('button', 'Button'),
        ]),
      ],
    },
    {
      name: 'articles_index',
      label: 'Articles hub page',
      file: 'src/content/pages/articles-index.yaml',
      fields: [
        metaObj,
        heroObj(),
        str('library_heading', 'Hidden accessibility heading'),
        obj('testimonials', 'Testimonials section', [
          ...sectionHeading,
          listObj('cards', 'Testimonial cards', [
            str('avatar', 'Avatar letter'),
            str('name', 'Name'),
            str('title', 'Role / organisation'),
            str('badge', 'Badge text'),
            str('date', 'Date line'),
            txt('quote', 'Quote (include the quotation marks)'),
            str('cta_label', 'Link text'),
            str('cta_href', 'Link target'),
          ]),
        ]),
        obj('case_studies', 'Case studies section', [
          ...sectionHeading,
          linkObj('view_link', 'Heading-row link'),
          listObj('cards', 'Cards', [
            str('label', 'Small label'),
            str('title', 'Title'),
            txt('text', 'Text'),
            str('href', 'Link target (leave blank for “coming soon”)', { required: false }),
            str('cta', 'Link/status text'),
          ]),
        ]),
        obj('audio', 'Audio interviews section', [
          ...sectionHeading,
          txt('intro', 'Intro paragraph'),
          obj('panel', 'Dark audio panel', [
            str('label', 'Small label'),
            str('title', 'Panel heading'),
            txt('body', 'Panel paragraph'),
            listObj('items', 'Audio items', [
              str('title', 'Title'),
              str('meta', 'Meta line'),
              str('placeholder', 'Placeholder text'),
            ]),
            txt('note', 'Small-print note'),
            str('cta_label', 'Button text'),
          ]),
        ]),
        obj('articles', 'Articles section', [
          ...sectionHeading,
          txt('intro', 'Intro paragraph'),
          listObj('cards', 'Article cards', [
            str('category', 'Category label'),
            str('title', 'Title'),
            txt('text', 'Text'),
            str('href', 'Link target (leave blank for “coming soon”)', { required: false }),
            str('badge', 'Badge (e.g. Coming Soon; optional)', { required: false }),
          ]),
        ]),
        ctaBandObj(),
      ],
    },
    {
      name: 'faq',
      label: 'FAQ page',
      file: 'src/content/pages/faq.yaml',
      fields: [
        metaObj,
        heroObj(),
        listObj('faqs', 'Questions & answers', [
          str('question', 'Question'),
          txt('answer', 'Answer'),
        ]),
        ctaBandObj(),
      ],
    },
    {
      name: 'not_found',
      label: '404 (page not found)',
      file: 'src/content/pages/not-found.yaml',
      fields: [
        metaObj,
        str('title', 'Heading'),
        txt('body', 'Message'),
        linkObj('primary', 'Primary button'),
        linkObj('outline', 'Secondary button'),
      ],
    },
    {
      name: 'site',
      label: 'Site-wide (footer & CTA band)',
      file: 'src/content/pages/site.yaml',
      fields: [
        obj('cta_band', 'Default call-to-action band (most pages)', [
          str('title', 'Title'),
          txt('body', 'Body'),
          linkObj('primary', 'Primary (gold) button'),
          linkObj('outline', 'Secondary (outline) button'),
        ]),
        obj('footer', 'Footer', [
          str('brand_blurb', 'Brand tagline under the logo'),
          str('abn_note', 'ABN note'),
          str('phone', 'Phone number'),
          str('email', 'Email address'),
          str('location', 'Location line'),
          str('copyright', 'Copyright line'),
        ]),
        obj('afs_strip', 'AFS strip above the footer', [
          str('division', '“A division of …” text', {
            hint: 'May contain <strong>…</strong> for bold.',
          }),
          str('credentials', 'Credentials text'),
        ]),
      ],
    },
  ],
};

const articleNavAndCta = articleCommon.after;

const articlesCollection = {
  name: 'articles',
  label: 'Articles',
  description:
    'The five published article pages. Their cards on the Articles hub are edited separately under Pages → Articles hub page. New articles are developer work.',
  editor: { preview: false },
  files: [
    ...['gary-oriordan-endorsement', 'janene-rees-endorsement'].map((slug, i) => ({
      name: slug.replace(/-/g, '_'),
      label: i === 0 ? "Endorsement — Gary O'Riordan" : 'Endorsement — Janene Rees',
      file: `src/content/articles/${slug}.yaml`,
      fields: [
        ...articleCommon.before,
        obj('context', '“About this endorsement” box', [
          str('title', 'Heading'),
          txt('body', 'Text'),
        ]),
        obj('letter', 'Endorsement letter', [
          str('avatar', 'Avatar letter'),
          str('author_name', 'Author name'),
          str('author_title', 'Author role'),
          str('date', 'Date line'),
          listStr('paragraphs', 'Letter paragraphs', 'Paragraph'),
          listStr('salutation_lines', 'Sign-off lines', 'Line'),
          obj(
            'download',
            'Original letter download (optional)',
            [str('label', 'Link text'), str('href', 'File link'), str('size', 'File size')],
            { required: false },
          ),
        ]),
        ...articleNavAndCta,
      ],
    })),
    ...[
      { slug: 'vivid-sydney', label: 'Case study — Vivid Sydney' },
      { slug: 'carriageworks', label: 'Case study — Carriageworks' },
    ].map(({ slug, label }) => ({
      name: slug.replace(/-/g, '_'),
      label,
      file: `src/content/articles/${slug}.yaml`,
      fields: [
        ...articleCommon.before,
        listObj('meta_items', 'Fact box (top of page)', [
          str('label', 'Label'),
          str('value', 'Value'),
        ]),
        obj('background', 'Background', [
          str('title', 'Heading'),
          listStr('paragraphs', 'Paragraphs', 'Paragraph'),
        ]),
        obj(
          'event_types',
          'Event types grid (optional)',
          [
            str('title', 'Heading'),
            listObj('items', 'Tiles', [str('icon', 'Icon (emoji)'), str('label', 'Label')]),
          ],
          { required: false },
        ),
        obj('challenge', 'The challenge', [
          str('title', 'Heading'),
          listStr('paragraphs', 'Paragraphs', 'Paragraph'),
          listStr('bullets', 'Bullet points', 'Bullet'),
        ]),
        obj('approach', 'Our approach', [
          str('title', 'Heading'),
          listStr('paragraphs', 'Paragraphs', 'Paragraph'),
        ]),
        obj('services', 'Services delivered', [
          str('title', 'Heading'),
          listStr('items', 'Bullet points', 'Service'),
        ]),
        obj('outcomes', 'Outcomes', [
          str('title', 'Heading'),
          listObj('stats', 'Stat tiles', [str('num', 'Big figure'), str('label', 'Caption')]),
          listStr('paragraphs', 'Closing paragraphs', 'Paragraph'),
        ]),
        txt('confidentiality', 'Confidentiality note', {
          hint: 'May contain <strong> and a link.',
        }),
        ...articleNavAndCta,
      ],
    })),
    {
      name: 'matthew_harrison_profile',
      label: 'Feature profile — Matthew Harrison',
      file: 'src/content/articles/matthew-harrison-profile.yaml',
      fields: [
        ...articleCommon.before,
        listObj('meta_items', 'Meta line (top of article)', [
          str('label', 'Label'),
          str('value', 'Value'),
        ]),
        listObj('sections', 'Article sections', [
          str('title', 'Section heading'),
          listStr('paragraphs', 'Paragraphs', 'Paragraph'),
          txt('pull_quote', 'Pull quote after this section (optional)', { required: false }),
        ]),
        ...articleNavAndCta,
      ],
    },
  ],
};

const config = {
  backend: {
    name: 'github',
    repo: 'goodtune/securetours',
    branch,
    ...(authBase ? { base_url: authBase } : {}),
  },

  // Uploads land in their own folder so the CMS can never overwrite the
  // design assets (logo, hero) that live directly in public/assets.
  media_folder: 'public/assets/uploads',
  public_folder: '/assets/uploads',

  site_url: 'https://securetours.com.au',

  collections: [pagesCollection, servicesCollection, articlesCollection],
};

export const GET: APIRoute = () =>
  new Response(JSON.stringify(config, null, 2), {
    headers: { 'Content-Type': 'text/yaml; charset=utf-8' },
  });
