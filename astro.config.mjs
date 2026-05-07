import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  site: 'https://securetours.com.au',
  // Output static HTML — no SSR, no JS framework, plain HTML + the
  // static prototype's CSS verbatim.
  output: 'static',
  build: {
    format: 'directory',
  },
});
