// The Way Back Home: keep what a reader has already seen on the phone, so pages reopen
// instantly and work on weak or no connection. Versioned files (?v=...) never change, so
// they are kept; the pages themselves always try the network first.
const C='twbh-v1';
self.addEventListener('install',e=>self.skipWaiting());
self.addEventListener('activate',e=>e.waitUntil((async()=>{
  // keep the cache tidy: drop old versions of files when a newer version is stored
  await self.clients.claim();
})()));
self.addEventListener('fetch',e=>{
  const r=e.request,u=new URL(r.url);
  if(r.method!=='GET'||u.origin!==location.origin)return;
  // narration and scene clips stream in pieces; leave them to the browser
  if(r.destination==='audio'||r.destination==='video'||r.headers.has('range'))return;
  if(r.mode==='navigate'){ // book pages: fresh when online, saved copy when offline
    e.respondWith(fetch(r).then(res=>{const cp=res.clone();caches.open(C).then(c=>c.put(r,cp));return res}).catch(()=>caches.match(r,{ignoreSearch:true}).then(m=>m||caches.match('/'))));
    return;}
  if(u.search.includes('v=')||u.pathname.startsWith('/assets/')){ // pictures, music, data
    e.respondWith(caches.open(C).then(async c=>{const hit=await c.match(r);if(hit)return hit;
      const res=await fetch(r);if(res.ok){c.put(r,res.clone());
        // remove older versions of the same file
        const base=u.origin+u.pathname;(await c.keys()).forEach(k=>{if(k.url.startsWith(base)&&k.url!==r.url)c.delete(k)})}
      return res}));
  }
});
