import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const services = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/services' }),
  schema: z.object({
    title: z.string(),
    hero_tag: z.string(),
    hero_sub: z.string(),
    lead: z.string(),
    features: z.array(z.object({ icon: z.string(), text: z.string() })),
    clients: z.array(z.string()).optional(),
    order: z.number(),
    coming_soon: z.boolean().default(false),
    home_card: z.object({
      icon: z.string(),
      title: z.string().optional(),
      body: z.string(),
    }),
  }),
});

export const collections = { services };
