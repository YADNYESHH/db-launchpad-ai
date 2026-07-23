import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/auth': 'http://localhost:8080',
      '/profiles': 'http://localhost:8080',
      '/recommendations': 'http://localhost:8080',
      '/audit': 'http://localhost:8080',
      '/weights': 'http://localhost:8080',
      '/api': 'http://localhost:8080',
    },
  },
})
