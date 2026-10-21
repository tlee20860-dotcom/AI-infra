const CACHE_NAME = 'ai-console-v2';
const ASSETS_TO_CACHE = [
  './',
  './index.html',
  './manifest.json'
];

// 安裝 Service Worker 並快取基本檔案
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// 啟用並清理舊快取
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// 攔截請求，優先使用網路，失敗則使用快取
self.addEventListener('fetch', (event) => {
  // 只快取 GET 請求，且排除 GitHub API 呼叫
  if (event.request.method !== 'GET' || event.request.url.includes('api.github.com')) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // 如果請求成功，複製一份到快取
        const responseClone = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseClone);
        });
        return response;
      })
      .catch(() => {
        // 如果網路失敗，從快取讀取
        return caches.match(event.request);
      })
  );
});

/* ═══ EOF ═══
F: AI-infra/sw.js
V: 1792581601
W: ai-system-20261021-005#2
═══ */