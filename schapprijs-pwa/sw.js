// Schapprijs service worker: makes the app installable and usable offline.
// App files come from the cache first; price data is fetched fresh and falls back to the last copy when offline.
const APP = "schapprijs-app-v1";
const DATA = "schapprijs-data-v1";
const APP_FILES = ["./", "index.html", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png", "icons/icon-maskable-512.png", "icons/apple-touch-icon.png", "icons/favicon-32.png"];

self.addEventListener("install", event => {
  event.waitUntil(caches.open(APP).then(c => c.addAll(APP_FILES)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", event => {
  event.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== APP && k !== DATA).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  // Price data: network first, cached copy when offline.
  if (url.origin === location.origin && url.pathname.includes("/data/")) {
    event.respondWith(fetch(req).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(DATA).then(c => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req)));
    return;
  }

  // The page itself: network first so updates arrive, cache when offline.
  if (req.mode === "navigate") {
    event.respondWith(fetch(req).then(res => {
      const copy = res.clone(); caches.open(APP).then(c => c.put("index.html", copy));
      return res;
    }).catch(() => caches.match("index.html")));
    return;
  }

  // Icons, fonts and other static files: cache first.
  event.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
    if (res.ok && (url.origin === location.origin || url.hostname.endsWith("gstatic.com") || url.hostname.endsWith("googleapis.com"))) {
      const copy = res.clone(); caches.open(APP).then(c => c.put(req, copy));
    }
    return res;
  })));
});
