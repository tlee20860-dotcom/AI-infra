// 將版號提升到 v10，強迫手機清空舊快取並載入最新的 index.html
const CACHE_NAME = 'ai-console-v10'; 
const ASSETS_TO_CACHE = [
  './',
  './index.html',
  './manifest.json'
];

self.addEventListener('install', (event) => {
  self.skipWaiting(); // 強制立刻接管
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
});

self.addEventListener('activate', (event) => {
  // 清除所有非當前版號的舊快取
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim()) // 立刻控制所有開啟的網頁
  );
});

self.addEventListener('fetch', (event) => {
  // 遇到 API 請求或非 GET 請求，直接放行，絕對不攔截快取
  if (event.request.method !== 'GET' || event.request.url.includes('api.github.com') || event.request.url.includes('raw.githubusercontent.com')) {
    return;
  }

  // 針對 HTML 網頁，採用「網路優先」策略
  if (event.request.mode === 'navigate' || event.request.url.endsWith('index.html') || event.request.url.endsWith('/')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
          return response;
        })
        .catch(() => {
          return caches.match(event.request);
        })
    );
    return;
  }

  // 其他靜態資源
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      return cachedResponse || fetch(event.request);
    })
  );
});

/* ═══ EOF ═══
F: AI-infra/sw.js
V: 1792910300
W: ai-system-004
═══ */