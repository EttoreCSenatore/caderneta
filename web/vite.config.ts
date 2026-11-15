import react from '@vitejs/plugin-react';
import {defineConfig} from 'vite';
import {VitePWA} from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icon.svg'],
      manifest: {
        name: 'Caderneta',
        short_name: 'Caderneta',
        description: 'Notas, avisos e calendário da escola num só lugar.',
        lang: 'pt-BR',
        theme_color: '#1d4ed8',
        background_color: '#f7f9fe',
        display: 'standalone',
        start_url: '/',
        icons: [
          {src: 'icon-192.png', sizes: '192x192', type: 'image/png'},
          {src: 'icon-512.png', sizes: '512x512', type: 'image/png'},
          {src: 'icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable'},
        ],
      },
      workbox: {
        // Dados da API nunca vão para o cache do service worker (são pessoais).
        navigateFallbackDenylist: [/^\/api\//],
        runtimeCaching: [],
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: {'/api': 'http://127.0.0.1:8000'},
  },
  build: {sourcemap: false},
});
