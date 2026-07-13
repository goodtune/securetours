// YAML files are imported as plain objects via @rollup/plugin-yaml.
// Runtime validation happens in src/lib/pages.ts (Zod), so `any` here is fine.
declare module '*.yaml' {
  const data: any;
  export default data;
}
