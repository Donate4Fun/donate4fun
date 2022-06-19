import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: {
      '/api/': {
        target: 'http://localhost:8000',
      },
      '/api/v1/donation/subscribe/': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
})
