import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { replaceCodePlugin } from "vite-plugin-replace";
import alias from '@rollup/plugin-alias';
import path from 'path';

const apiUrl = process.env.API_URL || 'http://localhost:8000';
const dev = true;

const httpProxy = {
  target: apiUrl,
  changeOrigin: true,
  secure: false,
  cookieDomainRewrite: 'http://localhost',
};

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
  plugins: [
    svelte(),
    replaceCodePlugin({
      replacements: [{
        from: "process.env.DEV",
        to: JSON.stringify(dev),
      }],
    }),
  ],
  optimizeDeps: { exclude: ["svelte-navigator"] },
  resolve: {
    alias: {
      "$lib": path.resolve('src/lib'),
    },
  },
  server: {
    proxy: {
      '/sitemap.xml': httpProxy,
      '/api/v1/subscribe': {
        target: apiUrl.replace('http', 'ws'),
        ws: true,
        changeOrigin: true,
        secure: false,
      },
      '/api/': httpProxy,
      '/d/': httpProxy,
      '/js/script.js': httpProxy,
    },
  },
})
