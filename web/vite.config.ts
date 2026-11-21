/// <reference types="vitest/config" />
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
        id: '/',
        start_url: '/',
        scope: '/',
        orientation: 'any',
        categories: ['education'],
        shortcuts: [
          {name: 'Avisos', url: '/avisos', icons: [{src: 'icon-192.png', sizes: '192x192'}]},
          {name: 'Calendário', url: '/calendario', icons: [{src: 'icon-192.png', sizes: '192x192'}]},
          {name: 'Notificações', url: '/notificacoes', icons: [{src: 'icon-192.png', sizes: '192x192'}]},
        ],
        icons: [
          {src: 'icon-192.png', sizes: '192x192', type: 'image/png'},
          {src: 'icon-512.png', sizes: '512x512', type: 'image/png'},
          {src: 'icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable'},
        ],
      },
      workbox: {
        // Dados da API nunca vão para o cache do service worker (são pessoais).
        // eventos de push (aviso genérico, sem conteúdo)
        importScripts: ['push-sw.js'],
        navigateFallbackDenylist: [/^\/api\//],
        runtimeCaching: [],
      },
    }),
  ],
  preview: {port: 4173, proxy: {'/api': 'http://127.0.0.1:8000'}},
  server: {
    port: 5173,
    proxy: {'/api': 'http://127.0.0.1:8000'},
  },
  build: {sourcemap: false},
  test: {
    // Cobertura (MO.7): só a lógica de src/lib; as telas são exercitadas pelos testes de ponta a ponta (Playwright).
    // Metas fixadas um pouco abaixo do número medido: subir quando novos testes entrarem, nunca baixar.
    coverage: {
      provider: 'v8',
      include: ['src/lib/**'],
      exclude: ['src/lib/**/*.test.*'],
      reporter: ['text-summary', 'text'],
      thresholds: {statements: 39, branches: 43, functions: 30, lines: 42},
    },
  },
});
