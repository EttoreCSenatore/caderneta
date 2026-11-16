/* Eventos de push (importado pelo service worker gerado pelo vite-plugin-pwa).
 * A mensagem chega SEM conteúdo, por privacidade: mostramos sempre o mesmo aviso genérico e o conteúdo fica no app, atrás do login. */
self.addEventListener('push', (event) => {
  event.waitUntil(
    self.registration.showNotification('Caderneta', {
      body: 'Você tem novidades. Toque para abrir.',
      icon: '/icon-192.png',
      badge: '/icon-192.png',
      tag: 'caderneta-novidades',
      data: {url: '/notificacoes'},
    }),
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || '/notificacoes';
  event.waitUntil(
    self.clients.matchAll({type: 'window', includeUncontrolled: true}).then((lista) => {
      for (const c of lista) {
        if ('focus' in c) {
          if ('navigate' in c) c.navigate(url);
          return c.focus();
        }
      }
      return self.clients.openWindow(url);
    }),
  );
});
