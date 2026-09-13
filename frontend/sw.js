const CACHE_NAME = 'me-vents-v14';
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
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  // 1. API: Red siempre primero
  if (e.request.url.includes('/api/')) {
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request))
    );
    return;
  }

  // 2. Todos los recursos: Network-First con fallback a Caché offline
  e.respondWith(
    fetch(e.request)
      .then((networkRes) => {
        if (networkRes && networkRes.status === 200) {
          const clone = networkRes.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(e.request, clone));
        }
        return networkRes;
      })
      .catch(() => caches.match(e.request))
  );
});

