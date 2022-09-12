import { defineConfig } from 'vite';
import { resolve } from 'path';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, 'dff-bolt.js'),
      name: 'DffBolt',
      // the proper extensions will be added
      fileName: 'dff-bolt',
      formats: ['es'],
    },
  },
  plugins: [
    svelte({
      configFile: 'bolt.svelte.config.js',
    })
  ]
});
