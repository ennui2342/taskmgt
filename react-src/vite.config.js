import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In Docker dev the Vite server proxies API calls to the api service.
// Locally, falls back to localhost:8081 (run `make api-up` separately).
const API_TARGET = process.env.VITE_API_TARGET || 'http://localhost:8081'

const apiRoutes = ['/tasks', '/tags', '/locations', '/counts', '/filters']

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: Object.fromEntries(
      apiRoutes.map(r => [r, { target: API_TARGET, changeOrigin: true }])
    ),
  },
})
