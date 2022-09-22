import { defineConfig } from 'vite';
import { resolve } from 'path';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import path from 'path';

export default defineConfig({
  resolve: {
    alias: [
      {find: "$lib", replacement: path.resolve(__dirname, "../../frontend/src/lib")},
    ],
  },
  build: {
    lib: {
      entry: resolve(__dirname, 'dff-bolt.js'),
      name: 'DffBolt',
      // the proper extensions will be added
      fileName: 'dff-bolt',
      formats: ['es'],
    },
    rollupOptions: {
      input: {
        popup: resolve(__dirname, 'popup.html'),
        options: resolve(__dirname, 'options.html'),
        // walcome: resolve(__dirname, 'welcome.html'),
      },
    },
  },
  plugins: [
    svelte({
      configFile: 'svelte.config.js',
    }),
  ],
});
