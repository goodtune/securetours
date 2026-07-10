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
const branch = import.meta.env.CMS_BRANCH || 'main';
const authBase = import.meta.env.CMS_AUTH_BASE_URL;

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

  collections: [
    {
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
        { name: 'title', label: 'Page title', widget: 'string' },
        {
          name: 'meta_description',
          label: 'Search result description (SEO)',
          widget: 'text',
          hint: 'Shown by search engines under the page title. One or two sentences.',
        },
        {
          name: 'hero_tag',
          label: 'Hero tag line',
          widget: 'string',
          hint: 'Small line above the main heading in the page banner.',
        },
        { name: 'hero_sub', label: 'Hero subtitle', widget: 'string' },
        { name: 'lead', label: 'Opening paragraphs', widget: 'text' },
        { name: 'opening_quote', label: 'Opening quote', widget: 'string', required: false },
        { name: 'banner_statement', label: 'Banner statement', widget: 'string', required: false },
        { name: 'features_heading', label: 'Features heading', widget: 'string', required: false },
        {
          name: 'features',
          label: 'Features',
          widget: 'list',
          fields: [
            { name: 'icon', label: 'Icon (emoji)', widget: 'string' },
            { name: 'text', label: 'Text', widget: 'string' },
          ],
        },
        {
          name: 'clients',
          label: 'Who this is for',
          widget: 'list',
          required: false,
          field: { name: 'client', label: 'Client type', widget: 'string' },
        },
        {
          name: 'clients_label',
          label: '“Who this is for” heading',
          widget: 'string',
          required: false,
        },
        { name: 'tcs_note', label: 'Terms & conditions note', widget: 'string', required: false },
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
        {
          name: 'faqs',
          label: 'FAQs',
          widget: 'list',
          required: false,
          fields: [
            { name: 'question', label: 'Question', widget: 'string' },
            { name: 'answer', label: 'Answer', widget: 'text' },
          ],
        },
        {
          name: 'cta',
          label: 'Call to action',
          widget: 'object',
          required: false,
          fields: [
            { name: 'title', label: 'Title', widget: 'string', required: false },
            { name: 'body', label: 'Body', widget: 'text', required: false },
          ],
        },
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
        {
          name: 'home_card',
          label: 'Home page card',
          widget: 'object',
          fields: [
            { name: 'icon', label: 'Icon (emoji)', widget: 'string' },
            {
              name: 'title',
              label: 'Card title (leave blank to use the page title)',
              widget: 'string',
              required: false,
            },
            { name: 'body', label: 'Card text', widget: 'text' },
          ],
        },
        {
          name: 'body',
          label: 'Additional page sections (markdown)',
          widget: 'markdown',
          required: false,
        },
      ],
    },
  ],
};

export const GET: APIRoute = () =>
  new Response(JSON.stringify(config, null, 2), {
    headers: { 'Content-Type': 'text/yaml; charset=utf-8' },
  });
