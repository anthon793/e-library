import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/uploads': 'http://localhost:8000',
      '/archive': 'http://localhost:8000',
      '/books': 'http://localhost:8000',
      '/pdf': 'http://localhost:8000',
    },
  },
})
