/* Penname Mobile service worker — offline-first app shell.
 * The app makes no network requests of its own; this worker only serves the
 * app's own files so it keeps working with no connection at all. */
"use strict";

const CACHE = "penname-v6";
const ASSETS = [
  "./",
  "./index.html",
  "./style.css",
  "./app.js",
  "./gazetteer.js",
  "./engine.js",
  "./activity.js",
  "./manifest.webmanifest",
  "./icons/apple-touch-icon.png",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./fonts/Urbanist-Variable.woff2",
  "./fonts/IBMPlexMono-Regular.woff2",
  "./fonts/IBMPlexMono-Medium.woff2",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(
    caches.match(event.request, { ignoreSearch: true }).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).then((response) => {
        // Cache same-origin responses for future offline use.
        if (response.ok && new URL(event.request.url).origin === self.location.origin) {
          const clone = response.clone();
          caches.open(CACHE).then((cache) => cache.put(event.request, clone));
        }
        return response;
      });
    })
  );
});