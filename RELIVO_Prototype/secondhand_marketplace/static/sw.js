const CACHE = 'relivo-static-v1';
self.addEventListener('install', event => { event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(['/static/style.css','/static/manifest.json']))); self.skipWaiting(); });
self.addEventListener('activate', event => { event.waitUntil(self.clients.claim()); });
self.addEventListener('fetch', event => { if (event.request.method !== 'GET') return; const url = new URL(event.request.url); if (url.origin === self.location.origin && url.pathname.startsWith('/static/')) event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request))); });
