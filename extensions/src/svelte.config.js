export default {
  // svelte options
  extensions: ['.svelte'],
  compilerOptions: {
    accessors: true,
    css: true,
  },
  preprocess: [],
  onwarn: (warning, handler) => handler(warning),
};
