/* The Way Back Home: reader.
   Everything the book shows comes from content/: story.json (page order, pictures, colours,
   music, animated scenes) and i18n/<lang>.json (the words, and when each sentence is spoken).
   All paths are relative, so the same files work at thewaybackhome.net/ or under a sub-folder. */
(() => {
'use strict';
const $ = s => document.querySelector(s);
const ROOT = new URL('./', document.baseURI);
const Q = new URLSearchParams(location.search);
const RENDER = Q.has('render');                 // used by tools/video.py to photograph pages
const PREVIEW = Q.has('preview') || RENDER;     // show languages that are not finished yet
const CFG = window.TWBH || {};                   // optional settings from the page (used by the preview copy)
const DEMO = Q.has('demo') || !!CFG.demo;      // try the captions with no recording (silent, reading pace)
const TRACK = /(^|\.)thewaybackhome\.net$|\.github\.io$/.test(location.hostname) && !RENDER;
const CJK = new Set(['zh', 'ja']);
// data saver or a very slow connection: show the still pictures only, never download the animated scenes
// iPads and computers show the book about 560 px wide or more: they get the sharper copy of a scene when there is one
const BIG = Math.min(innerWidth, innerHeight * 942 / 1670) >= 560;
const NOCLIPS = Q.has('noclips') || (() => { const c = navigator.connection; return !!(c && (c.saveData || /(^|-)2g$/.test(c.effectiveType || ''))); })();
// fonts for scripts that Andika/Grandstander don't cover: [Google Fonts family, line height]
const SCRIPT = {
  ar: ['Noto Naskh Arabic', 1.7], ur: ['Noto Nastaliq Urdu', 2.05], he: ['Noto Sans Hebrew', 1.5],
  hi: ['Noto Sans Devanagari', 1.6], bn: ['Noto Sans Bengali', 1.6], pa: ['Noto Sans Gurmukhi', 1.6],
  zh: ['Noto Sans SC', 1.6], ja: ['Noto Sans JP', 1.6], ko: ['Noto Sans KR', 1.55]
};

let S, LANGS, META, T, EN, L, V = 'dev', UI;
let secs = [], cur = 0, trk = null, N = 0, OFF = 0;  // OFF: the cover has no page number, so the first story page is page 1
const book = $('#book');

/* ---------------- loading ---------------- */
const url = p => ROOT + p + (p.includes('?') ? '&' : '?') + 'v=' + V;
// words and page lists are always fetched fresh (they are small); pictures and sound are versioned
const getJSON = p => fetch(ROOT + p, { cache: 'no-cache' }).then(r => { if (!r.ok) throw new Error(p); return r.json(); });

async function boot() {
  S = await getJSON('content/story.json'); V = S.version || 'dev';
  LANGS = await getJSON('content/languages.json');
  L = pickLang();
  META = LANGS.langs[L];
  if (!META.ready && !PREVIEW) { location.replace(ROOT + 'languages.html'); return; }
  const [t, en] = await Promise.all([getJSON(`content/i18n/${L}.json`), L === 'en' ? null : getJSON('content/i18n/en.json')]);
  T = t; EN = en || t;
  UI = Object.assign({}, EN.ui, T.ui);
  UI.message = (T.ui && T.ui.message) || EN.ui.message;
  N = S.pages.length; OFF = S.pages[0] && S.pages[0].kind === 'cover' ? 1 : 0;
  document.documentElement.style.setProperty('--artw', S.art.width);
  document.documentElement.style.setProperty('--arth', S.art.height);
  setupLanguage();
  build();
  setupControls();
  if (RENDER) return renderMode();
  goTo(pageIndex(Q.get('p')), false);
  if ('serviceWorker' in navigator && TRACK) { try { navigator.serviceWorker.register(ROOT + 'sw.js'); } catch (e) {} }
}

function pickLang() {
  const ok = c => c && LANGS.langs[c] && (LANGS.langs[c].ready || PREVIEW);
  const q = Q.get('lang'); if (ok(q)) return q;
  const seg = location.pathname.slice(ROOT.pathname.length).split('/')[0];
  if (ok(seg)) return seg;
  if (!seg || seg === 'index.html') { // the front door: open in the reader's own language when we have it
    for (const n of navigator.languages || []) { const c = n.toLowerCase().split('-')[0]; if (ok(c)) return c; }
  }
  return 'en';
}

function setupLanguage() {
  const h = document.documentElement;
  h.lang = L; h.dir = META.dir || 'ltr';
  document.title = T.title + (L === 'en' ? '' : ' · The Way Back Home');
  const f = SCRIPT[L];
  if (f) {
    const l = document.createElement('link'); l.rel = 'stylesheet';
    l.href = `https://fonts.googleapis.com/css2?family=${f[0].replace(/ /g, '+')}:wght@400;700;900&display=swap`;
    document.head.appendChild(l);
    h.style.setProperty('--body', `'Andika','${f[0]}',system-ui,sans-serif`);
    h.style.setProperty('--display', `'Grandstander','${f[0]}',system-ui,sans-serif`);
    document.body.style.lineHeight = f[1];
    h.style.setProperty('--lh', f[1]);
  }
}

/* ---------------- text ---------------- */
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const J = () => CJK.has(L) ? '' : ' ';
function text(id) { const a = T.pages && T.pages[id]; return a ? { d: a, fb: false } : { d: EN.pages[id], fb: true }; }
// every line the narrator says on a page, in order: one caption each, one cue each
function spoken(pg, d) {
  if (!d) return [];
  switch (pg.kind) {
    case 'story': return d.text.flat();
    case 'cover': return [d.title, d.subtitle];
    case 'prayer': return [d.title, d.intro, ...d.steps.map(s => s.word + J() + s.rest), d.prayer, d.note];
    case 'grownups': return [d.title, d.intro, ...d.questions, d.note];
  }
  return [];
}
const spokenAt = i => { const pg = S.pages[i], t = text(pg.id); return spoken(pg, t.fb && L !== 'en' ? null : t.d); };

/* ---------------- building the pages ---------------- */
function hex(c) { c = c.replace('#', ''); return [0, 2, 4].map(i => parseInt(c.substr(i, 2), 16)); }
const mix = (c, k) => hex(c).map(v => Math.round(v * k));
const rgb = (a, al) => `rgba(${a[0]},${a[1]},${a[2]},${al})`;
const BOOK = '<svg viewBox="0 0 24 24" width="1.15em" height="1.15em" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 6.5C10 5 7 4.5 3.5 5v13c3.5-.5 6.5 0 8.5 1.5 2-1.5 5-2 8.5-1.5V5C17 4.5 14 5 12 6.5z"/><path d="M12 6.5v13"/></svg>';
const ARROW = '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5v14M6 13l6 6 6-6"/></svg>';

function pageHTML(pg, i) {
  const { d, fb } = text(pg.id);
  const art = `art/${pg.art}`;
  let body = '';
  if (pg.kind === 'cover') {
    body = `<h1>${esc(T.pages.cover ? T.pages.cover.title : T.title)}</h1><div class="subrow"><p class="sub">${esc(d.subtitle)}</p><span class="mslot"></span></div><div class="cfoot"><button class="qr" id="qr" aria-label="${esc(UI.share || 'Share')}"></button><div class="ctas">${META.narration || DEMO ? `<button class="cta alt" data-listen>${ICON.speaker}<span>${esc(d.listen || UI.read)}</span></button>` : ''}<button class="cta alt" data-go="1">${BOOK}<span>${esc(d.cta)}</span></button></div></div>`;
  } else if (pg.kind === 'story') {
    const lines = d.text.flat();
    body = `<div class="full"><p class="num">${i + 1 - OFF}</p>${d.text.map(p => `<p class="para">${p.map(esc).join(J())}</p>`).join('')}<p class="ref">${esc(d.ref)}</p></div>` +
      `<div class="caps" aria-hidden="true">${lines.map((s, k) => `<p class="cap" data-k="${k}">${esc(s)}</p>`).join('')}</div>`;
  } else if (pg.kind === 'prayer') {
    body = `<h2 class="big">${esc(d.title)}</h2><p class="intro">${esc(d.intro)}</p><ol class="steps">${d.steps.map(s => `<li><span class="key">${esc(s.key)}</span><span><b>${esc(s.word)}</b>${J()}${esc(s.rest)}</span></li>`).join('')}</ol><p class="pray">${esc(d.prayer)}</p><p class="note">${esc(d.note)} ${esc(d.ref || '')}</p>`;
  } else if (pg.kind === 'grownups') {
    body = `<h2 class="big">${esc(d.title)}</h2><p class="intro">${esc(d.intro)}</p><ol class="qs">${d.questions.map(q => `<li>${esc(q)}</li>`).join('')}</ol><p class="note">${esc(d.note)}</p>`;
  }
  // a page with a scene only shows its picture until the 720-wide clip takes over, so on a phone the 720 picture is enough
  const vid = !NOCLIPS && !BIG && (pg.clips || []).length > 0;
  const chip = '';
  const sh = mix(pg.tint, 0.42), sm = mix(pg.tint, 0.5), lazy = i > 1 ? 'loading="lazy"' : '';
  return `<section class="pg ${pg.kind}" data-i="${i}" aria-label="${pg.kind === 'cover' ? esc(pg.kind) : esc(UI.page || 'Page') + ' ' + (i + 1 - OFF)}" style="--tint:${pg.tint};--shade:${rgb(sh, .72)};--shade-mid:${rgb(sm, .5)}">
<img class="bg" alt="" aria-hidden="true" decoding="async" ${lazy} src="${url(art + '-soft.webp')}">
<div class="stage"><div class="art"><img class="pic" alt="" draggable="false" decoding="async" ${lazy} ${vid ? '' : `sizes="(min-width:520px) 942px, 100vw" srcset="${url(art + '-720.webp')} 720w, ${url(art + '.webp')} 942w"`} src="${url(art + '-720.webp')}"></div>
<div class="soft" aria-hidden="true"><img class="ext" alt="" decoding="async" ${lazy} src="${url(art + '-soft.webp')}"><img class="top" alt="" decoding="async" ${lazy} src="${url(art + '-soft.webp')}"></div><div class="shade"></div>${chip}
<div class="txt${fb && L !== 'en' ? ' untranslated' : ''}">${body}</div></div></section>`;
}

function build() {
  book.innerHTML = '<div class="track" id="track">' + S.pages.map(pageHTML).join('') + '</div>';
  trk = $('#track'); secs = [...trk.children];
  secs.forEach((sec, i) => {
    const img = sec.querySelector('.pic');
    if (!NOCLIPS) (S.pages[i].clips || []).forEach((c, j) => {
      const v = document.createElement('video');
      v.muted = true; v.defaultMuted = true; v.playsInline = true; v.preload = 'none';
      v.setAttribute('muted', ''); v.setAttribute('playsinline', '');
      v.dataset.src = url(BIG && c.hd ? c.hd : c.src); v.dataset.j = j;
      sec.querySelector('.art').appendChild(v);
    });
    measure.observe(sec.querySelector('.txt'));
  });
  book.addEventListener('click', e => {
    const g = e.target.closest('[data-go]'); if (g) goTo(+g.dataset.go);
    if (e.target.closest('[data-listen]') && !reading) setRead(true);   // the cover's Listen button: read the book aloud from the start
  });
  (document.fonts ? document.fonts.ready : Promise.resolve()).then(fitAll);
  addEventListener('resize', () => { if (trk) setY(-cur * H(), false); fitAll(); });
}

// the blur and colour start just above the text, however tall the text is on this page and screen
const measure = new ResizeObserver(es => es.forEach(e => {
  const sec = e.target.closest('.pg'); sec.style.setProperty('--th', e.target.offsetHeight + 'px');
}));
// long pages (and long languages) shrink their text a little rather than covering the picture
function fitAll() {
  secs.forEach(sec => {
    const t = sec.querySelector('.txt'), st = sec.querySelector('.stage');
    const fit = () => {
      let k = 1; sec.style.setProperty('--k', k);
      const max = st.clientHeight * (sec.classList.contains('story') ? 0.56 : 0.82);
      while (t.offsetHeight > max && k > 0.62) { k -= 0.04; sec.style.setProperty('--k', k.toFixed(2)); }
    };
    fit();
  });
  placeBar();
}


/* ---------------- page turning: one swipe = one page ---------------- */
const H = () => book.clientHeight;
function setY(y, anim) { trk.classList.toggle('anim', !!anim); trk.style.transform = `translate3d(0,${y}px,0)`; }
let settleT = null, prev = 0;
function goTo(n, anim = true) {
  if (!trk) return;
  n = Math.max(0, Math.min(N - 1, n)); const changed = n !== cur; cur = n;
  setY(-n * H(), anim);
  if (changed || !anim) {
    // the page we just left keeps its frozen last frame while it slides away, and is reset once it is off screen
    setCount(); if (prev !== cur) { const was = prev; setCap(was, -1); prev = cur; setTimeout(() => { if (cur !== was) resetClips(was); }, anim ? 650 : 0); }
    preload();
    if (reading) speak();
  }
  clearTimeout(settleT);
  // reading without narration: the scene plays (silently) half a second after the page has landed
  settleT = setTimeout(() => { if (!reading) autoClips(cur); }, (anim ? 520 : 60) + 500);
}
let ty = null, tt = 0, dy = 0, moved = false;
book.addEventListener('touchstart', e => { if (e.touches.length !== 1) return; ty = e.touches[0].clientY; tt = performance.now(); dy = 0; moved = false; trk && trk.classList.remove('anim'); }, { passive: true });
book.addEventListener('touchmove', e => {
  if (ty === null || !trk) return; dy = e.touches[0].clientY - ty; if (Math.abs(dy) > 6) moved = true;
  let d = dy; if ((cur === 0 && d > 0) || (cur === N - 1 && d < 0)) d *= .3;
  setY(-cur * H() + d, false); e.preventDefault();
}, { passive: false });
book.addEventListener('touchend', () => {
  if (ty === null) return; const v = dy / Math.max(1, performance.now() - tt); ty = null;
  if (!moved) { setY(-cur * H(), false); return; }
  if (dy < -H() * .12 || v < -.35) goTo(cur + 1); else if (dy > H() * .12 || v > .35) goTo(cur - 1); else goTo(cur);
});
book.addEventListener('touchcancel', () => { ty = null; goTo(cur); });
let wheelAcc = 0, wheelLock = 0;
book.addEventListener('wheel', e => {
  e.preventDefault(); const now = performance.now(); if (now < wheelLock) return; wheelAcc += e.deltaY;
  if (Math.abs(wheelAcc) > 40) { goTo(cur + (wheelAcc > 0 ? 1 : -1)); wheelAcc = 0; wheelLock = now + 650; }
}, { passive: false });
addEventListener('keydown', e => {
  if (!secs.length || e.target.closest('input,textarea')) return;
  if (['ArrowDown', 'PageDown', ' '].includes(e.key)) { e.preventDefault(); goTo(cur + 1); }
  if (['ArrowUp', 'PageUp'].includes(e.key)) { e.preventDefault(); goTo(cur - 1); }
  if (e.key === 'Escape') closeMenus();
});
// clips downloaded ahead of time: url -> { p: promise of a blob url, got, total, stop }
const clipMem = {};
function fetchClip(v) {
  if (v.src || v._fetching) return; v._fetching = true;
  const u = v.dataset.src;
  let m = clipMem[u];
  if (!m) {
    const ctl = window.AbortController ? new AbortController() : null;
    m = clipMem[u] = { got: 0, total: 0, stop: () => ctl && ctl.abort() };
    m.p = fetch(u, ctl ? { signal: ctl.signal } : {}).then(async r => {
      if (!r.ok) throw 0;
      m.total = +r.headers.get('content-length') || 0;
      if (!r.body || !r.body.getReader) return URL.createObjectURL(await r.blob());
      const rd = r.body.getReader(), parts = [];
      for (;;) { const { done, value } = await rd.read(); if (done) break; parts.push(value); m.got += value.length; }
      return URL.createObjectURL(new Blob(parts, { type: 'video/mp4' }));
    });
    m.p.catch(() => { if (clipMem[u] === m) delete clipMem[u]; });
  }
  m.p.then(b => { if (!v.src) { v.preload = 'auto'; v.src = b; } }, () => {}).finally(() => { v._fetching = false; });
}
// when a scene has to play now: use the download if it is done or nearly done; otherwise stop it and stream the
// file instead, so it is never downloaded twice
function clipReady(v) {
  if (v.src) return Promise.resolve();
  const u = v.dataset.src, m = clipMem[u], direct = () => { if (!v.src) { v.preload = 'auto'; v.src = u; } };
  if (m && (!m.total || m.got / m.total > 0.5)) return m.p.then(b => { if (!v.src) { v.preload = 'auto'; v.src = b; } }, direct);
  if (m) { m.stop(); delete clipMem[u]; }
  direct(); return Promise.resolve();
}
function preload() {
  [cur + 1, cur + 2].forEach(i => secs[i] && secs[i].querySelectorAll('img[loading=lazy]').forEach(im => { im.loading = 'eager'; }));
  // decode the next page's pictures now, so the slide to it never waits on them
  secs[cur + 1] && secs[cur + 1].querySelectorAll('img').forEach(im => { if (im.decode) im.decode().catch(() => {}); });
  // iPhones ignore preload="auto" and only start fetching a video when it is told to play, so a scene could miss its
  // moment on a slow connection. So the next page's scenes are downloaded whole while this page is open (after its
  // pictures have had their turn) and played from memory. This page's own scene streams if it is not there yet.
  const load = i => secs[i] && secs[i].querySelectorAll('video').forEach(fetchClip);
  load(cur); const at = cur; setTimeout(() => { if (cur === at) load(at + 1); }, 1500);
  [cur, cur + 1].forEach(i => secs[i] && (S.pages[i].clips || []).forEach(c => { if (c.end && !NOCLIPS) new Image().src = url(`art/${c.end}-soft.webp`); }));
  // while reading aloud, the next page's music loads too, so it is ready when the page turns
  setTimeout(() => { if (cur === at && reading && actx) warmMood(); }, 2500);
}
/* phones can show a strip below the page (Safari's toolbar area, the home bar on some iPhones). Paint it in the
   colour of the bottom of the current page, measured from its blurred picture, so the page seems to run to the edge. */
const edge = {};
function edgeColor(i) {
  if (edge[i]) return Promise.resolve(edge[i]);
  return new Promise(res => {
    const im = new Image();
    im.onload = () => {
      try {
        const c = document.createElement('canvas'); c.width = c.height = 1; const x = c.getContext('2d');
        x.drawImage(im, 0, im.height * 0.88, im.width, im.height * 0.12, 0, 0, 1, 1);
        const d = x.getImageData(0, 0, 1, 1).data, s = mix(S.pages[i].tint, 0.42), k = 0.72;
        res(edge[i] = `rgb(${[0, 1, 2].map(j => Math.round(d[j] * (1 - k) + s[j] * k)).join(',')})`);
      } catch (e) { res(null); }
    };
    im.onerror = () => res(null); im.src = url(`art/${S.pages[i].art}-soft.webp`);
  });
}
function paintEdge() { const at = cur; edgeColor(at).then(c => { if (c && cur === at) document.documentElement.style.setProperty('--edge', c); }); }
// the round buttons float just above where this page's text starts (home lowest), never over the words
function placeBar() {
  const sec = secs[cur]; if (!sec) return;
  const t = sec.querySelector('.txt'), st = sec.querySelector('.stage'); if (!t || !st) return;
  const gap = Math.max(0, book.clientHeight - innerHeight);       // the part of the page hidden behind the browser's bar
  let b = st.clientHeight - t.offsetTop - gap + 12;
  b = Math.max(12, Math.min(b, innerHeight - 158 - 64));            // keep the whole stack on screen, below the page count
  document.documentElement.style.setProperty('--bb', Math.round(b) + 'px');
}
addEventListener('resize', () => setTimeout(placeBar, 50));
function setCount() {
  placeBar();
  paintEdge(); document.body.classList.toggle('at-cover', cur === 0);
  // on the cover the menu button sits beside the subtitle, in thumb reach; on the story pages it is back in the top bar
  const mw = $('.mwrap'), slot = document.querySelector('.mslot');
  if (mw && slot) { const to = cur === 0 ? slot : $('.bar'); if (mw.parentNode !== to) { closeMenus(); to.appendChild(mw); } }
  const c = $('#count'); c.textContent = `${cur + 1 - OFF} / ${N - OFF}`; c.classList.toggle('hide', cur === 0); $('#homeBtn').hidden = cur === 0;
  if (TRACK) { const p = `${ROOT.pathname}${L}/` + (cur < OFF ? '' : `p${cur + 1 - OFF}`); if (location.pathname !== p) history.pushState({ p: cur }, '', p); }
}
// page numbers in links (/en/p5, ?p=5) are the numbers printed on the pages; the cover is p0 (or no number)
function pageIndex(n) { return n === null || n === undefined || n === '' ? 0 : Math.max(0, Math.min(N - 1, (parseInt(n, 10) || 0) + OFF - 1)); }
addEventListener('popstate', () => { if (!secs.length) return; const m = location.pathname.match(/\/p(\d+)$/); goTo(m ? pageIndex(m[1]) : 0); });

/* ---------------- captions ---------------- */
function setCap(i, k) {
  const sec = secs[i]; if (!sec) return;
  sec.querySelectorAll('.cap').forEach(p => p.classList.toggle('on', +p.dataset.k === k));
}

/* ---------------- sound: narration, scene sounds and music share one audio clock ---------------- */
let actx = null, narrBus = null, sfxBus = null, mBus = null, mPlaying = null, reading = false, run = 0, narr = null;
const SFX = 0.75;  // scene sound effects sit a little under the narrator
const bufs = new Map(), moods = {};
function ensureAudio() {
  try {
    if (!actx) {
      const C = window.AudioContext || window.webkitAudioContext; if (!C) return;
      actx = new C();
      mBus = actx.createGain(); mBus.gain.value = 0; mBus.gain._lvl = 0; mBus.connect(actx.destination);
      narrBus = actx.createGain(); narrBus.connect(actx.destination);
      sfxBus = actx.createGain(); sfxBus.gain.value = SFX; sfxBus.connect(actx.destination);
      document.addEventListener('visibilitychange', () => { if (!document.hidden && reading && actx.state !== 'running') actx.resume(); });
    }
    if (actx.state !== 'running') actx.resume();
  } catch (e) {}
}
addEventListener('pointerdown', ensureAudio, { once: true });
function loadBuf(u) {
  if (bufs.has(u)) return bufs.get(u);
  const p = fetch(u).then(r => { if (!r.ok) throw new Error('load'); return r.arrayBuffer(); }).then(ab => new Promise((res, rej) => actx.decodeAudioData(ab, res, rej)));
  bufs.set(u, p); p.catch(() => bufs.delete(u));
  if (bufs.size > 12) bufs.delete(bufs.keys().next().value);
  return p;
}
const lat = () => actx ? (actx.outputLatency || 0) + (actx.baseLatency || 0) : 0;
function glide(p, to, secs) {
  const now = actx.currentTime;
  if (p.cancelAndHoldAtTime) p.cancelAndHoldAtTime(now); else { p.cancelScheduledValues(now); p.setValueAtTime(p._lvl != null ? p._lvl : p.value, now); }
  p.setTargetAtTime(to, now, Math.max(0.05, secs / 3)); p._lvl = to;
}
const MUSIC_UP = 0.63, MUSIC_DUCK = 0.294, XFADE = 3.5;
function fadeCurve(p, from, to, secs, at) {
  const n = 64, c = new Float32Array(n);
  for (let k = 0; k < n; k++) { const x = k / (n - 1); c[k] = from + (to - from) * (to > from ? Math.sin(x * Math.PI / 2) : 1 - Math.cos(x * Math.PI / 2)); }
  try { if (p.cancelAndHoldAtTime) p.cancelAndHoldAtTime(at); else p.cancelScheduledValues(at); p.setValueCurveAtTime(c, at, secs); }
  catch (e) { try { p.cancelScheduledValues(0); p.setValueAtTime(from, at); p.linearRampToValueAtTime(to, at + secs); } catch (e2) { p.value = to; } }
  p._lvl = to;
}
const musicLevel = (x, s = 0.8) => mBus && glide(mBus.gain, x, s);
// keep only this page's and the next page's music decoded (a decoded track is large on a phone)
function warmMood() {
  const keep = [S.pages[cur], S.pages[cur + 1]].filter(Boolean).map(p => p.mood);
  Object.keys(moods).forEach(k => { if (!keep.includes(k) && !(mPlaying && mPlaying.name === k)) { delete moods[k]; bufs.delete(url(`music/cue_${k}.mp3`)); } });
  keep.forEach(n => { if (n && !moods[n]) { moods[n] = loadBuf(url(`music/cue_${n}.mp3`)); moods[n].catch(() => delete moods[n]); } });
}
async function setMood(n, early) {
  if (!actx || !n || (mPlaying && mPlaying.name === n)) return;
  let buf; try { buf = await (moods[n] || (moods[n] = loadBuf(url(`music/cue_${n}.mp3`)))); } catch (e) { return; }
  // "early": the handover to the next page's piece, started during the page turn
  const want = early ? [S.pages[cur].mood, S.pages[cur + 1] && S.pages[cur + 1].mood] : [S.pages[cur].mood];
  if (!reading || !want.includes(n) || (mPlaying && mPlaying.name === n)) return;
  const now = actx.currentTime, g = actx.createGain();
  g.connect(mBus);
  // equal-power crossfade: the two pieces overlap without a dip or a bump in loudness;
  fadeCurve(g.gain, 0, 1, XFADE, now);
  if (mPlaying) { const o = mPlaying; fadeCurve(o.g.gain, o.g.gain.value, 0, XFADE, now); stopTrack(o, now + XFADE + 0.2); }
  const mp = { name: n, g, srcs: [], timer: 0 };
  mPlaying = mp;
  playCopy(mp, buf, now, false);
}
// a long page (or a slow language) can outlast its piece: instead of jumping from the piece's soft ending back
// to its start, a fresh copy fades in under the ending, so the music carries on without a seam
const LOOP_OVERLAP = 5, LOOP_FADE = 3;
function playCopy(mp, buf, at, fadeIn) {
  const s = actx.createBufferSource(), sg = actx.createGain();
  s.buffer = buf; s.connect(sg); sg.connect(mp.g);
  if (fadeIn) fadeCurve(sg.gain, 0, 1, LOOP_FADE, at); else sg.gain.value = 1;
  s.start(at); mp.srcs.push(s);
  s.onended = () => { mp.srcs = mp.srcs.filter(x => x !== s); };
  const next = at + Math.max(LOOP_OVERLAP + 1, buf.duration - LOOP_OVERLAP);
  mp.timer = setTimeout(() => { if (mPlaying === mp) playCopy(mp, buf, Math.max(next, actx.currentTime + 0.05), true); },
    Math.max(0, next - actx.currentTime - 0.4) * 1000);
}
function stopTrack(mp, when) { clearTimeout(mp.timer); mp.srcs.forEach(s => { try { s.stop(when); } catch (e) {} }); }
if (Q.has('debug')) window.__twbh = { get music() { return mPlaying && { name: mPlaying.name, gain: mPlaying.g.gain.value, hushed: !!mPlaying.hushed }; }, get sfx() { return !!sfxNow; } };
function hushMusic() { if (mPlaying) { glide(mPlaying.g.gain, 0, 2.5); mPlaying.hushed = true; } }
function riseMusic(t) { if (mPlaying && mPlaying.hushed) { glide(mPlaying.g.gain, 1, t); mPlaying.hushed = false; } }
function musicStop() { musicLevel(0, 1.5); const p = mPlaying; mPlaying = null; if (p) { clearTimeout(p.timer); setTimeout(() => stopTrack(p, 0), 1700); } }
function stopNarr() { if (narr) { try { narr.onended = null; narr.stop(); } catch (e) {} narr = null; } }

// when no cues were recorded, spread the sentences over the narration by their length
function estimate(lines, dur) {
  const w = lines.map(s => s.length + 10), tot = w.reduce((a, b) => a + b, 0) || 1; let t = 0;
  return lines.map((_, k) => { const at = t; t += dur * w[k] / tot; return at; });
}

// read the current page aloud: narration from the start, captions follow it, scenes start on their sentence
async function speak() {
  const id = ++run, me = cur, pg = S.pages[me];
  stopNarr(); resetClips(me); ensureAudio();
  const live = () => id === run && reading && cur === me;
  const lines = spokenAt(me);
  if (mPlaying && mPlaying.hushed && mPlaying.name === pg.mood) { glide(mPlaying.g.gain, 1, XFADE); mPlaying.hushed = false; }  // music back after a hushed scene
  setMood(pg.mood);
  let buf = null, cues, dur;
  if (META.narration && !DEMO) {
    try { buf = await loadBuf(url(`audio/${L}/${pg.id}.mp3`)); } catch (e) { buf = null; }
    if (!live()) return;
  }
  if (buf) { dur = buf.duration; const c = (T.cues || {})[pg.id]; cues = c && c.length === lines.length ? c : estimate(lines, dur); }
  else { dur = lines.reduce((a, s) => a + 1.2 + s.length / 14, 0) || 3; cues = estimate(lines, dur); }
  const clips = (pg.clips || []).map((c, j) => ({ ...c, j, t: (cues[c.sentence || 0] || 0) + (c.offset || 0), done: false }));
  let t0 = 0, paused = false, ended = false, scenes = Promise.resolve();
  // scenes on a page play one after another, never on top of each other
  const scene = c => { c.done = true; scenes = scenes.then(() => live() ? playClip(me, c.j, true) : false); return scenes; };
  const start = off => {
    if (!live()) return; paused = false; t0 = actx.currentTime - off;
    if (buf) { const s = actx.createBufferSource(); s.buffer = buf; s.connect(narrBus); s.start(actx.currentTime, off); s.onended = () => { if (narr === s && !paused) { narr = null; ended = true; } }; narr = s; }
    musicLevel(MUSIC_DUCK, .6);
  };
  // the page turns once the narration has finished and the last scene has frozen on its final frame
  const finish = () => {
    riseMusic(2.5);   // a hushed page still swells back before the turn
    musicLevel(MUSIC_UP, 1.2);
    clips.forEach(c => { if (!c.done) scene(c); });
    const t = performance.now();
    scenes.then(() => {
      // the next page's music starts fading in now, while this page holds and slides away, so the change of piece
      // happens across the page turn instead of at the first word of the next page
      const nx = S.pages[cur + 1];
      if (live() && nx && nx.mood && nx.mood !== pg.mood) setMood(nx.mood, true);
      setTimeout(() => { if (live()) { if (cur < N - 1) goTo(cur + 1); else setRead(false); } }, Math.max(900, 1600 - (performance.now() - t)));
    });
  };
  const tick = () => {
    if (!live()) return;
    if (!paused) {
      const pos = actx.currentTime - t0 - lat();
      let k = 0; while (k + 1 < cues.length && pos >= cues[k + 1] - 0.05) k++;
      setCap(me, k);
      for (const c of clips) if (!c.done && pos >= c.t) {
        if (c.pause) { paused = true; stopNarr(); scene(c).then(() => start(Math.max(0, pos - (c.overlap || 0)))); }
        else scene(c);
      }
      if (ended || (!buf && pos >= dur)) { finish(); return; }
    }
    setTimeout(tick, 40);
  };
  start(0); setCap(me, 0); tick();
  if (me + 1 < N && META.narration && !DEMO) loadBuf(url(`audio/${L}/${S.pages[me + 1].id}.mp3`)).catch(() => {});
}
function setRead(on) {
  reading = on; book.classList.toggle('listening', on);
  const b = $('#read'); b.setAttribute('aria-pressed', on); b.setAttribute('aria-label', on ? UI.stop : UI.read); b.title = on ? UI.stop : UI.read;
  b.innerHTML = on ? ICON.pause : ICON.speaker;
  if (on) { ensureAudio(); speak(); setTimeout(() => reading && warmMood(), 2500); } else { run++; stopNarr(); stopSfx(); musicStop(); setCap(cur, -1); }
  hud(!on); fitAll();
}
/* while the book reads aloud the buttons fade away after a moment; a touch anywhere brings them back */
let hudT = 0;
function hud(touched) {
  clearTimeout(hudT); document.body.classList.remove('hud-off');
  if (reading) hudT = setTimeout(() => {
    if (!reading) return;
    if ($('#menu').hidden && $('#msgMenu').hidden) document.body.classList.add('hud-off'); else hud(true);
  }, touched ? 3500 : 1500);
}
['pointerdown', 'touchstart', 'keydown'].forEach(ev => addEventListener(ev, () => hud(true), { passive: true, capture: true }));

/* ---------------- animated scenes ----------------
   The page's picture is the clip's first frame, so nothing jumps when the clip starts. The clip plays
   once and freezes on its last frame; the blur under the text switches to that frame too. A clip that
   has not arrived in time (slow connection) or that the phone refuses to play is skipped and the
   still picture stays, along with any later clips on that page. Sound effects play only while the
   book is read aloud. */
let sfxNow = null;
function stopSfx() { if (sfxNow) { try { sfxNow.stop(); } catch (e) {} sfxNow = null; } }
function setSoft(sec, name) {
  sec.querySelectorAll('.soft img, img.bg').forEach(im => {
    if (!im.dataset.orig) im.dataset.orig = im.src;
    const to = name ? url(`art/${name}-soft.webp`) : im.dataset.orig;
    if (im.src !== to) im.src = to;  // setting the same picture again would make it flicker
  });
}
function resetClips(i) {
  const sec = secs[i]; if (!sec) return;
  sec._skip = false; stopSfx();
  const vs = sec.querySelectorAll('video'); if (!vs.length) return;
  vs.forEach(v => { v._gen = (v._gen || 0) + 1; v.pause(); v.classList.remove('on'); try { v.currentTime = 0; } catch (e) {} });
  setSoft(sec, null);
}
const WAIT = 2500, WAIT_READ = 7000;  // how long a clip may take to start before the page carries on with the still picture
// (longer while reading aloud: the narration carries on regardless, and a scene that starts a little late is better than none)
function playClip(i, j, withSound) {
  const sec = secs[i], v = sec && sec.querySelectorAll('video')[j], c = S.pages[i].clips[j];
  if (!v || sec._skip) return Promise.resolve(false);
  return new Promise(res => {
    const gen = v._gen = (v._gen || 0) + 1, stale = () => v._gen !== gen;
    let done = false, started = false, giveUp = 0, cap = 0;
    const end = ok => {
      if (done) return; done = true; clearTimeout(giveUp); clearTimeout(cap);
      // a broken file skips the page's other scenes too; a slow one only gives up on itself
      if (!ok) { if (v.error || !reading) sec._skip = true; if (!started) { v.pause(); v.classList.remove('on'); } }
      else if (!stale() && c.end) setSoft(sec, c.end);
      res(ok);
    };
    v.onplaying = () => {
      if (stale()) { v.pause(); return; }
      if (started) return; started = true; clearTimeout(giveUp);
      v.classList.add('on');
      // "hush": seconds into the clip when the book's music fades away for the rest of the page (the scene's own sounds carry it)
      // "rise": seconds into the clip when the music swells back (over "riseFor" seconds, default 4) to carry into the next page
      if (reading && c.rise != null) setTimeout(() => { if (!stale() && reading && cur === i) riseMusic(c.riseFor || 4); }, Math.max(0, c.rise - (v.currentTime || 0)) * 1000);
      if (reading && c.hush != null) setTimeout(() => { if (!stale() && reading && cur === i) hushMusic(); }, Math.max(0, c.hush - (v.currentTime || 0)) * 1000);
      cap = setTimeout(() => end(true), ((v.duration || 12) + 6) * 1000);  // a clip that stalls part-way just stops there
      if (withSound && reading && c.sound && actx) loadBuf(url(c.sound)).then(b => {
        if (stale() || done || !reading) return; stopSfx();
        const s = actx.createBufferSource(); s.buffer = b; s.connect(sfxBus); s.start(actx.currentTime, Math.min(b.duration, v.currentTime + lat())); sfxNow = s;
      }).catch(() => {});
    };
    v.onended = () => { if (!stale()) end(true); };
    giveUp = setTimeout(() => { if (!started) end(false); }, reading ? WAIT_READ : WAIT);
    clipReady(v).then(() => {
      if (stale() || done) return;
      try { v.currentTime = 0; } catch (e) {}
      const p = v.play(); if (p && p.catch) p.catch(() => end(false));
    });
  });
}
function autoClips(i) {
  if (reading || RENDER) return; const pg = S.pages[i]; if (!pg.clips || !pg.clips.length) return;
  const v0 = secs[i].querySelector('video'); if (!v0 || v0.classList.contains('on')) return;
  (async () => { for (let j = 0; j < pg.clips.length; j++) { if (cur !== i || reading) return; if (!await playClip(i, j, false)) return; } })();
}

/* ---------------- controls & menu ---------------- */
const ICON = {
  speaker: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 5 6 9H3v6h3l5 4V5z" fill="currentColor"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/><path d="M18.5 5.5a9 9 0 0 1 0 13"/></svg>',
  pause: '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1.2" fill="currentColor"/><rect x="14" y="5" width="4" height="14" rx="1.2" fill="currentColor"/></svg>'
};
function toast(t) { const el = $('#toast'); el.textContent = t; el.classList.add('on'); setTimeout(() => el.classList.remove('on'), 1800); }
function closeMenus() { $('#menu').hidden = true; $('#msgMenu').hidden = true; $('#menuBtn').setAttribute('aria-expanded', 'false'); }
// count a tap as a visit to a made-up address, so it shows up in the anonymous visitor stats
function count(what) { if (!TRACK) return; try { const b = location.pathname; history.pushState(null, '', `${ROOT.pathname}dl/${L}-${what}`); history.replaceState(null, '', b); } catch (e) {} }

/* the cover's QR code opens this same language on a friend's phone; a tap shows it large for easy scanning */
function qrLink() {
  const u = new URL(L + '/', ROOT); if (!META.ready) u.searchParams.set('preview', '1');
  return u.href;
}
function qrSVG(text) {
  const q = qrcode(0, 'M'); q.addData(text); q.make();
  const n = q.getModuleCount(), m = 2; let d = '';
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) if (q.isDark(y, x)) d += `M${x + m} ${y + m}h1v1h-1z`;
  return `<svg viewBox="0 0 ${n + 2 * m} ${n + 2 * m}" shape-rendering="crispEdges" aria-hidden="true"><rect width="100%" height="100%" fill="#fff"/><path d="${d}" fill="#1d1a24"/></svg>`;
}
function sizeQR() {  // the QR code is exactly as tall as the stack of buttons beside it (capped so it never crowds them)
  const b = $('#qr'), c = document.querySelector('.cfoot .ctas'); if (!b || !c || !c.offsetHeight) return;
  const h = Math.min(c.getBoundingClientRect().height, innerWidth * 0.45) + 'px';
  b.style.width = h; b.style.height = h;
}
addEventListener('resize', sizeQR);
function setupQR() {
  const b = $('#qr'); if (!b) return;
  sizeQR(); if (document.fonts) document.fonts.ready.then(sizeQR);
  if (window.ResizeObserver) new ResizeObserver(sizeQR).observe(document.querySelector('.cfoot .ctas'));
  const draw = () => { b.innerHTML = qrSVG(qrLink()); };
  if (window.qrcode) draw();
  else { const sc = document.createElement('script'); sc.src = url('qr.js'); sc.onload = draw; sc.onerror = () => { b.hidden = true; }; document.head.appendChild(sc); }
  b.onclick = e => {
    e.stopPropagation(); if (!b.firstChild) return;
    const o = document.createElement('div'); o.className = 'qrbig'; o.innerHTML = `<div>${b.innerHTML}<p>${esc(META.name)}</p></div>`;
    o.onclick = () => o.remove(); document.body.appendChild(o);
  };
}
const GLOBE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 0 1 0 18a14 14 0 0 1 0-18"/></svg>';
function setupControls() {
  const read = $('#read');
  read.hidden = !(META.narration || DEMO);
  read.innerHTML = ICON.speaker; read.setAttribute('aria-label', UI.read); read.title = UI.read;
  read.onclick = () => setRead(!reading);
  const home = $('#homeBtn'); home.setAttribute('aria-label', UI.home || 'Home'); home.title = UI.home || 'Home';
  home.onclick = () => { if (reading) setRead(false); goTo(0); };
  $('#menuBtn').setAttribute('aria-label', UI.more || 'More');
  document.querySelectorAll('#menu [data-k]').forEach(e => { e.textContent = UI[e.dataset.k] || e.textContent; });
  if (META.dir === 'rtl') { $('#menu').dir = 'rtl'; $('#msgMenu').dir = 'rtl'; }
  const menu = $('#menu'), mb = $('#menuBtn');
  mb.onclick = e => { e.stopPropagation(); const o = menu.hidden; closeMenus(); menu.hidden = !o; mb.setAttribute('aria-expanded', o); };
  document.addEventListener('click', e => { if (!e.target.closest('.menu') && !e.target.closest('#menuBtn')) closeMenus(); });
  // on the cover the language name sits with the other buttons, bottom right, where the thumb is
  const chip = document.createElement('a'); chip.className = 'cta alt lang'; chip.href = ROOT + 'languages.html';
  chip.innerHTML = `${GLOBE}<span>${esc(META.name)}</span>`; chip.setAttribute('aria-label', `${UI.langs || 'Languages'}: ${META.name}`);
  const ctas = document.querySelector('.cfoot .ctas'); if (ctas) ctas.appendChild(chip);
  setupQR();

  const U = L.toUpperCase(), mv = $('#mVideo');
  if (META.video) { mv.href = ROOT + `video/The-Way-Back-Home_${U}.mp4`; mv.setAttribute('download', `The-Way-Back-Home_${U}.mp4`); }
  else mv.hidden = true;
  mv.addEventListener('click', () => { count('video'); toast(UI.downloading || '…'); });

  $('#mShare').onclick = async () => {
    closeMenus(); count('share');
    const link = `https://thewaybackhome.net/${L}/`, title = T.title;
    if (navigator.share) { try { await navigator.share({ title, url: link }); return; } catch (e) { if (e.name === 'AbortError') return; } }
    try { await navigator.clipboard.writeText(link); toast(UI.copied); } catch (e) { location.href = 'https://wa.me/?text=' + encodeURIComponent(title + ' ' + link); }
  };

  const m = UI.message, CAT = ['Prayer request', 'Language request', 'Thank you', 'How this book helped'], EMO = ['🙏', '🌍', '💛', '✨'];
  $('#mMsgT').textContent = m.title; $('#mMsgS').textContent = m.sub;
  $('#msgMenu').innerHTML = m.choices.map((c, i) => {
    const subj = `The Way Back Home – ${CAT[i]} (${META.name})`, body = `\n\n\n—\n${m.note}\n${META.name} · https://thewaybackhome.net/${L}/`;
    return `<a role="menuitem" href="mailto:hello@thewaybackhome.net?subject=${encodeURIComponent(subj)}&body=${encodeURIComponent(body)}"><span class="emo" aria-hidden="true">${EMO[i]}</span><span>${esc(c)}</span></a>`;
  }).join('') + `<div class="note">${esc(m.note)}</div>`;
  $('#mMsg').onclick = e => { e.stopPropagation(); closeMenus(); $('#msgMenu').hidden = false; };
  $('#msgMenu').addEventListener('click', e => { if (e.target.closest('a')) { count('message'); setTimeout(closeMenus, 200); } });

  // install the book as an app (home-screen icon, opens full screen)
  let installEvt = null; addEventListener('beforeinstallprompt', e => { e.preventDefault(); installEvt = e; });
  if (matchMedia('(display-mode: standalone)').matches || navigator.standalone) $('#mApp').hidden = true;
  $('#mApp').onclick = async e => {
    e.preventDefault(); closeMenus(); count('app');
    if (installEvt) { installEvt.prompt(); try { await installEvt.userChoice; } catch (_) {} installEvt = null; return; }
    const t = $('#tip'), ua = navigator.userAgent, iph = /iPhone|iPod/.test(ua), v = +((ua.match(/Version\/(\d+)/) || [])[1] || 0), bottom = iph && v >= 26;
    t.dir = META.dir; t.classList.toggle('bottom', bottom); t.textContent = bottom ? (UI.apptip26 || UI.apptip) : UI.apptip; t.hidden = false;
    clearTimeout(t._h); t._h = setTimeout(() => t.hidden = true, 7000);
  };
  $('#tip').onclick = e => e.currentTarget.hidden = true;
}

/* ---------------- render mode (for making the downloadable videos) ----------------
   tools/video.py opens the book once and calls __show(page, sentence) for every picture it needs. */
async function show(p, s) {
  p = Math.max(0, Math.min(N - 1, p));
  secs.forEach((_, i) => setCap(i, -1));
  goTo(p, false);
  const story = S.pages[p].kind === 'story' && s != null && s >= 0;
  book.classList.toggle('listening', story);
  if (story) setCap(p, s);
  secs[p].querySelectorAll('img').forEach(im => { im.loading = 'eager'; }); const img = secs[p].querySelector('.pic');
  if (!img.complete || !img.naturalWidth) await new Promise(r => { img.addEventListener('load', r, { once: true }); img.addEventListener('error', r, { once: true }); });
  if (document.fonts) await document.fonts.ready;
  fitAll();
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  return true;
}
async function renderMode() {
  document.body.classList.add('render');
  window.__show = show;
  const s = Q.get('s');
  await show(pageIndex(Q.get('p')), s === null ? null : +s);
  document.body.dataset.ready = '1';
}

boot().catch(e => { console.error(e); book.innerHTML = '<p style="padding:24px;font:16px system-ui;color:#fff">The book could not load. Please check your connection and try again.</p>'; });
})();
