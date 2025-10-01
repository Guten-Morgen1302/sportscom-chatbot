import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/chat': 'http://localhost:5000',
      '/health': 'http://localhost:5000',
      '/keep-alive': 'http://localhost:5000'
    }
  },
  build: {
    outDir: 'static',
    emptyOutDir: true,
    assetsDir: 'assets'
  }
})
