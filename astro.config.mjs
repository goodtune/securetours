import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import yaml from '@rollup/plugin-yaml';

// https://astro.build/config
export default defineConfig({
  site: 'https://securetours.com.au',
  // Output static HTML — no SSR, no JS framework, plain HTML + the
  // static prototype's CSS verbatim.
  output: 'static',
  build: {
    format: 'directory',
  },
  integrations: [
    sitemap({
      // The CMS admin shell is not site content.
      filter: (page) => !page.includes('/admin/'),
    }),
  ],
  vite: {
    // Page copy lives in src/content/pages/*.yaml (CMS-edited);
    // this lets pages import it as plain objects.
    plugins: [yaml()],
  },
});
