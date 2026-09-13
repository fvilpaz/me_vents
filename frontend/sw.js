const CACHE_NAME = 'me-vents-v5';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/css/style.css',
  '/css/tokens.css',
  '/css/base.css',
  '/css/header.css',
  '/css/timeline.css',
  '/css/cards.css',
  '/css/modals.css',
  '/css/glossary.css',
  '/js/app.js',
  '/js/modules/state.js',
  '/js/modules/timeline.js',
  '/js/modules/cards.js',
  '/js/modules/gestures.js',
  '/js/modules/uploader.js',
  '/js/modules/glossary.js',
  '/manifest.json',
  '/assets/images/Logo_Me_dark.png',
  '/assets/images/Logo_cañitas_dark.png',
  '/assets/images/fai.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  if (e.request.url.includes('/api/')) {
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request))
    );
    return;
  }

  e.respondWith(
    caches.match(e.request).then((cached) => {
      return cached || fetch(e.request);
    })
  );
});
