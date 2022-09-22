import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import alias from '@rollup/plugin-alias';
import path from 'path';

export default defineConfig({
  build: {
    rollupOptions: {
      plugins: [
        alias({
          entries: {
            '$lib': path.resolve('src/lib'),
          },
        }),
      ],
    },
  },
  plugins: [svelte()],
  resolve: {
    alias: {
      "$lib": path.resolve('src/lib'),
    },
  },
  server: {
    proxy: {
      '/sitemap.xml': {
        target: 'http://localhost:8000',
      },
      '/api/v1/subscribe': {
        target: 'ws://localhost:8000',
        ws: true
      },
      '/api/': {
        target: 'http://localhost:8000',
      },
      '/d/': {
        target: 'http://localhost:8000',
      },
    },
  },
})
