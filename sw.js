// The Way Back Home: keeps what a reader has already seen on the phone, so pages reopen
// instantly and work on a weak or missing connection. Files with ?v=… never change, so they are
// kept; the pages themselves always try the network first.
const C = 'twbh-v2';
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  const r = e.request, u = new URL(r.url);
  if (r.method !== 'GET' || u.origin !== location.origin) return;
  if (r.destination === 'audio' || r.destination === 'video' || r.headers.has('range')) return; // streamed media
  if (r.mode === 'navigate' || u.pathname.endsWith('.json') && !u.search.includes('v=')) {
    e.respondWith(fetch(r).then(res => { const cp = res.clone(); caches.open(C).then(c => c.put(r, cp)); return res; })
      .catch(() => caches.match(r, { ignoreSearch: r.mode === 'navigate' }).then(m => m || caches.match(new URL('./', self.registration.scope).href))));
    return;
  }
  if (u.search.includes('v=') || u.pathname.includes('/fonts/')) {
    e.respondWith(caches.open(C).then(async c => {
      const hit = await c.match(r); if (hit) return hit;
      const res = await fetch(r);
      if (res.ok) { c.put(r, res.clone()); const base = u.origin + u.pathname; (await c.keys()).forEach(k => { if (k.url.startsWith(base + '?') && k.url !== r.url) c.delete(k); }); }
      return res;
    }));
  }
});
