import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [svelte()],
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
    }
  }
})
