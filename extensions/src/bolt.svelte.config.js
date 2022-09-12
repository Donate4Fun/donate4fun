export default {
  // svelte options
  extensions: ['.svelte'],
  compilerOptions: {
    accessors: true,
    css: true,
  },
  preprocess: [],
  onwarn: (warning, handler) => handler(warning),
  // plugin options
  vitePlugin: {
    //include: ["Bolt.svelte"],
    // experimental options
    experimental: {},
  }
};
