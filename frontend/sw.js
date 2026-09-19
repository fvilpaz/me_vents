const CACHE_NAME = 'me-vents-v33';
const STATIC_ASSETS = [
  './',
  './index.html',
  './css/style.css',
  './css/tokens.css',
  './css/base.css',
  './css/header.css',
  './css/timeline.css',
  './css/cards.css',
  './css/modals.css',
  './css/glossary.css',
  './css/theme.css',
  './js/app.js',
  './js/modules/security.js',
  './js/modules/state.js',
  './js/modules/timeline.js',
  './js/modules/cards.js',
  './js/modules/gestures.js',
  './js/modules/uploader.js',
  './js/modules/glossary.js',
  './data/hotel_spaces.json',
  './data/jargon_dictionary.json',
  './manifest.json',
  './assets/images/Logo_Me_dark.png',
  './assets/images/melia_hotels_international.svg'
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

  // 2. Todos los recursos: Network-First con fallback a Caché offline.
  // cache:'no-cache' revalida con el servidor: sin él, GitHub Pages servía el JS/CSS viejo hasta 10 min tras cada despliegue
  e.respondWith(
    fetch(e.request, { cache: 'no-cache' })
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

