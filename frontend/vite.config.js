import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Invisi-Scan Enterprise',
        short_name: 'Invisi-Scan',
        description: 'Advanced Network Intelligence Dashboard',
        theme_color: '#0A0A0B',
        background_color: '#0A0A0B',
        display: 'standalone',
        icons: [
          {
            src: '/pwa-192x192.svg',
            sizes: '192x192',
            type: 'image/svg+xml'
          },
          {
            src: '/pwa-512x512.svg',
            sizes: '512x512',
            type: 'image/svg+xml',
            purpose: 'any maskable'
          }
        ]
      },
      workbox: {
        importScripts: ['/custom-sw.js']
      }
    })
  ],
  build: {
    minify: false,
    chunkSizeWarningLimit: 2000,
  }
})
