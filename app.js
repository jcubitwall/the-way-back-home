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
// fonts for scripts that Andika/Grandstander don't cover: [Google Fonts family, line height]
const SCRIPT = {
  ar: ['Noto Naskh Arabic', 1.7], ur: ['Noto Nastaliq Urdu', 2.05], he: ['Noto Sans Hebrew', 1.5],
  hi: ['Noto Sans Devanagari', 1.6], bn: ['Noto Sans Bengali', 1.6], pa: ['Noto Sans Gurmukhi', 1.6],
  zh: ['Noto Sans SC', 1.6], ja: ['Noto Sans JP', 1.6], ko: ['Noto Sans KR', 1.55]
};

let S, LANGS, META, T, EN, L, V = 'dev', UI;
let secs = [], cur = 0, trk = null, N = 0;
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
  N = S.pages.length;
  document.documentElement.style.setProperty('--artw', S.art.width);
  document.documentElement.style.setProperty('--arth', S.art.height);
  setupLanguage();
  build();
  setupControls();
  if (RENDER) return renderMode();
  const p = parseInt(Q.get('p') || '1', 10) || 1;
  goTo(Math.max(0, Math.min(N - 1, p - 1)), false);
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
const ARROW = '<svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5v14M6 13l6 6 6-6"/></svg>';

function pageHTML(pg, i) {
  const { d, fb } = text(pg.id);
  const art = `art/${pg.art}`;
  let body = '';
  if (pg.kind === 'cover') {
    body = `<h1>${esc(T.pages.cover ? T.pages.cover.title : T.title)}</h1><p class="sub">${esc(d.subtitle)}</p><button class="cta" data-go="1">${esc(d.cta)} ${ARROW}</button>`;
  } else if (pg.kind === 'story') {
    const lines = d.text.flat();
    body = `<div class="full"><p class="num">${i}</p>${d.text.map(p => `<p class="para">${p.map(esc).join(J())}</p>`).join('')}<p class="ref">${esc(d.ref)}</p></div>` +
      `<div class="caps" aria-hidden="true">${lines.map((s, k) => `<p class="cap" data-k="${k}">${esc(s)}</p>`).join('')}</div>`;
  } else if (pg.kind === 'prayer') {
    body = `<h2 class="big">${esc(d.title)}</h2><p class="intro">${esc(d.intro)}</p><ol class="steps">${d.steps.map(s => `<li><span class="key">${esc(s.key)}</span><span><b>${esc(s.word)}</b>${J()}${esc(s.rest)}</span></li>`).join('')}</ol><p class="pray">${esc(d.prayer)}</p><p class="note">${esc(d.note)} ${esc(d.ref || '')}</p>`;
  } else if (pg.kind === 'grownups') {
    body = `<h2 class="big">${esc(d.title)}</h2><p class="intro">${esc(d.intro)}</p><ol class="qs">${d.questions.map(q => `<li>${esc(q)}</li>`).join('')}</ol><p class="note">${esc(d.note)}</p>`;
  }
  const chip = pg.kind === 'cover' ? `<a class="chip" href="${ROOT}languages.html">${esc(META.name)}</a>` : '';
  const sh = mix(pg.tint, 0.42), sm = mix(pg.tint, 0.5), lazy = i > 1 ? 'loading="lazy"' : '';
  return `<section class="pg ${pg.kind}" data-i="${i}" aria-label="${esc(UI.page || 'Page')} ${i + 1}" style="--tint:${pg.tint};--shade:${rgb(sh, .93)};--shade-mid:${rgb(sm, .55)}">
<img class="bg" alt="" aria-hidden="true" decoding="async" ${lazy} src="${url(art + '-soft.webp')}">
<div class="stage"><div class="art"><img class="pic" alt="" draggable="false" decoding="async" ${lazy} sizes="(min-width:520px) 942px, 100vw" srcset="${url(art + '-720.webp')} 720w, ${url(art + '.webp')} 942w" src="${url(art + '-720.webp')}"></div>
<div class="soft" aria-hidden="true"><img class="ext" alt="" decoding="async" ${lazy} src="${url(art + '-soft.webp')}"><img class="top" alt="" decoding="async" ${lazy} src="${url(art + '-soft.webp')}"></div><div class="shade"></div>${chip}
<div class="txt${fb && L !== 'en' ? ' untranslated' : ''}">${body}</div></div></section>`;
}

function build() {
  book.innerHTML = '<div class="track" id="track">' + S.pages.map(pageHTML).join('') + '</div>';
  trk = $('#track'); secs = [...trk.children];
  secs.forEach((sec, i) => {
    const img = sec.querySelector('.pic');
    (S.pages[i].clips || []).forEach((c, j) => {
      const v = document.createElement('video');
      v.muted = true; v.defaultMuted = true; v.playsInline = true; v.preload = 'none';
      v.setAttribute('muted', ''); v.setAttribute('playsinline', '');
      v.dataset.src = url(c.src); v.dataset.j = j;
      sec.querySelector('.art').appendChild(v);
    });
    measure.observe(sec.querySelector('.txt'));
  });
  book.addEventListener('click', e => { const g = e.target.closest('[data-go]'); if (g) goTo(+g.dataset.go); });
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
    let k = 1; sec.style.setProperty('--k', k);
    const max = st.clientHeight * (sec.classList.contains('story') ? 0.56 : 0.82);
    while (t.offsetHeight > max && k > 0.62) { k -= 0.04; sec.style.setProperty('--k', k.toFixed(2)); }
  });
}

/* the soft layer is a blurred copy of the picture made ahead of time (art/<name>-soft.webp),
   so the blur looks the same on every phone. During an animated scene it stays still. */
function paint() {}

/* ---------------- page turning: one swipe = one page ---------------- */
const H = () => book.clientHeight;
function setY(y, anim) { trk.classList.toggle('anim', !!anim); trk.style.transform = `translate3d(0,${y}px,0)`; }
let settleT = null, prev = 0;
function goTo(n, anim = true) {
  if (!trk) return;
  n = Math.max(0, Math.min(N - 1, n)); const changed = n !== cur; cur = n;
  setY(-n * H(), anim);
  if (changed || !anim) {
    setCount(); if (prev !== cur) { resetClips(prev); setCap(prev, -1); prev = cur; }
    preload();
    if (reading) speak();
  }
  clearTimeout(settleT);
  settleT = setTimeout(() => { if (!reading) autoClips(cur); }, anim ? 520 : 60);
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
function preload() {
  [cur + 1, cur + 2].forEach(i => secs[i] && secs[i].querySelectorAll('img[loading=lazy]').forEach(im => { im.loading = 'eager'; }));
  [cur, cur + 1].forEach(i => secs[i] && secs[i].querySelectorAll('video').forEach(v => { if (!v.src) { v.preload = 'auto'; v.src = v.dataset.src; } }));
}
function setCount() {
  const c = $('#count'); c.textContent = `${cur + 1} / ${N}`; c.classList.toggle('hide', cur === 0);
  if (TRACK) { const p = `${ROOT.pathname}${L}/p${cur + 1}`; if (location.pathname !== p) history.pushState({ p: cur }, '', p); }
}
addEventListener('popstate', () => { const m = location.pathname.match(/p(\d+)$/); if (m && secs.length) goTo(+m[1] - 1); });

/* ---------------- captions ---------------- */
function setCap(i, k) {
  const sec = secs[i]; if (!sec) return;
  sec.querySelectorAll('.cap').forEach(p => p.classList.toggle('on', +p.dataset.k === k));
}

/* ---------------- sound: narration, scene sounds and music share one audio clock ---------------- */
let actx = null, narrBus = null, mBus = null, mPlaying = null, reading = false, run = 0, narr = null;
const bufs = new Map(), moods = {};
function ensureAudio() {
  try {
    if (!actx) {
      const C = window.AudioContext || window.webkitAudioContext; if (!C) return;
      actx = new C();
      mBus = actx.createGain(); mBus.gain.value = 0; mBus.gain._lvl = 0; mBus.connect(actx.destination);
      narrBus = actx.createGain(); narrBus.connect(actx.destination);
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
const MUSIC_UP = 0.6, MUSIC_DUCK = 0.28, XFADE = 4;
const musicLevel = (x, s = 0.8) => mBus && glide(mBus.gain, x, s);
async function setMood(n) {
  if (!actx || !n || (mPlaying && mPlaying.name === n)) return;
  let buf; try { buf = await (moods[n] || (moods[n] = loadBuf(url(`music/cue_${n}.mp3`)))); } catch (e) { return; }
  if (!reading || S.pages[cur].mood !== n || (mPlaying && mPlaying.name === n)) return;
  const now = actx.currentTime, src = actx.createBufferSource(), g = actx.createGain();
  src.buffer = buf; src.loop = true; g.gain.setValueAtTime(0, now); g.gain._lvl = 0; glide(g.gain, 1, XFADE);
  src.connect(g); g.connect(mBus); src.start(now);
  if (mPlaying) { const o = mPlaying; glide(o.g.gain, 0, XFADE); try { o.src.stop(now + XFADE * 1.6); } catch (e) {} }
  mPlaying = { name: n, src, g };
}
function musicStop() { musicLevel(0, 1.5); const p = mPlaying; mPlaying = null; if (p) setTimeout(() => { try { p.src.stop(); } catch (e) {} }, 1700); }
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
  setMood(pg.mood);
  let buf = null, cues, dur;
  if (META.narration && !DEMO) {
    try { buf = await loadBuf(url(`audio/${L}/${pg.id}.mp3`)); } catch (e) { buf = null; }
    if (!live()) return;
  }
  if (buf) { dur = buf.duration; const c = (T.cues || {})[pg.id]; cues = c && c.length === lines.length ? c : estimate(lines, dur); }
  else { dur = lines.reduce((a, s) => a + 1.2 + s.length / 14, 0) || 3; cues = estimate(lines, dur); }
  const clips = (pg.clips || []).map((c, j) => ({ ...c, j, t: (cues[c.sentence || 0] || 0) + (c.offset || 0), done: false }));
  let t0 = 0, paused = false, ended = false;
  const start = off => {
    if (!live()) return; paused = false; t0 = actx.currentTime - off;
    if (buf) { const s = actx.createBufferSource(); s.buffer = buf; s.connect(narrBus); s.start(actx.currentTime, off); s.onended = () => { if (narr === s && !paused) { narr = null; ended = true; } }; narr = s; }
    musicLevel(MUSIC_DUCK, .6);
  };
  const finish = () => { musicLevel(MUSIC_UP, 1.2); setTimeout(() => { if (live()) { if (cur < N - 1) goTo(cur + 1); else setRead(false); } }, 1600); };
  const tick = () => {
    if (!live()) return;
    if (!paused) {
      const pos = actx.currentTime - t0 - lat();
      let k = 0; while (k + 1 < cues.length && pos >= cues[k + 1] - 0.05) k++;
      setCap(me, k);
      for (const c of clips) if (!c.done && pos >= c.t) {
        c.done = true;
        if (c.pause) { paused = true; stopNarr(); playClip(me, c.j, true).then(() => start(Math.max(0, pos - (c.overlap || 0)))); }
        else playClip(me, c.j, true);
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
  if (on) { ensureAudio(); speak(); } else { run++; stopNarr(); musicStop(); setCap(cur, -1); resetClips(cur); }
  fitAll();
}

/* ---------------- animated scenes: the picture moves, then freezes on its last frame ---------------- */
function resetClips(i) {
  const sec = secs[i]; if (!sec) return;
  sec.querySelectorAll('video').forEach(v => { v._gen = (v._gen || 0) + 1; v.pause(); v.classList.remove('on'); try { v.currentTime = 0; } catch (e) {} });
  paint(i);
}
function playClip(i, j, withSound) {
  const sec = secs[i], v = sec && sec.querySelectorAll('video')[j], c = S.pages[i].clips[j];
  if (!v) return Promise.resolve();
  return new Promise(res => {
    const gen = v._gen = (v._gen || 0) + 1, stale = () => v._gen !== gen;
    if (!v.src) { v.preload = 'auto'; v.src = v.dataset.src; }
    let snd = null, done = false;
    const end = () => { if (done) return; done = true; if (snd) { try { snd.stop(); } catch (e) {} } paint(i, v); res(); };
    const repaint = () => { if (stale() || done) return; if (v.readyState >= 2) paint(i, v); (v.requestVideoFrameCallback ? v.requestVideoFrameCallback(repaint) : setTimeout(repaint, 120)); };
    v.onplaying = () => {
      if (stale()) { v.pause(); return; } v.classList.add('on'); repaint();
      if (withSound && c.sound && actx) loadBuf(url(c.sound)).then(b => { if (stale() || done) return; snd = actx.createBufferSource(); snd.buffer = b; snd.connect(narrBus); snd.start(actx.currentTime, Math.min(b.duration, v.currentTime + lat())); }).catch(() => {});
    };
    v.onended = end;
    try { v.currentTime = 0; } catch (e) {}
    v.play().catch(() => { // a phone that refuses to play shows the final frame instead
      const last = () => { try { v.currentTime = Math.max(0, v.duration - 0.05); } catch (e) {} v.classList.add('on'); setTimeout(end, 300); };
      v.readyState >= 1 ? last() : v.addEventListener('loadedmetadata', last, { once: true });
    });
    setTimeout(end, 20000);
  });
}
function autoClips(i) {
  if (reading || RENDER) return; const pg = S.pages[i]; if (!pg.clips || !pg.clips.length) return;
  const v0 = secs[i].querySelector('video'); if (!v0 || v0.classList.contains('on')) return;
  const snd = !!(navigator.userActivation && navigator.userActivation.hasBeenActive);
  if (snd) ensureAudio();
  (async () => { for (let j = 0; j < pg.clips.length; j++) { if (cur !== i || reading) return; await playClip(i, j, snd); } })();
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

function setupControls() {
  const read = $('#read');
  read.hidden = !(META.narration || DEMO);
  read.innerHTML = ICON.speaker; read.setAttribute('aria-label', UI.read); read.title = UI.read;
  read.onclick = () => setRead(!reading);
  $('#menuBtn').setAttribute('aria-label', UI.more || 'More');
  document.querySelectorAll('#menu [data-k]').forEach(e => { e.textContent = UI[e.dataset.k] || e.textContent; });
  if (META.dir === 'rtl') { $('#menu').dir = 'rtl'; $('#msgMenu').dir = 'rtl'; }
  const menu = $('#menu'), mb = $('#menuBtn');
  mb.onclick = e => { e.stopPropagation(); const o = menu.hidden; closeMenus(); menu.hidden = !o; mb.setAttribute('aria-expanded', o); };
  document.addEventListener('click', e => { if (!e.target.closest('.menu') && !e.target.closest('#menuBtn')) closeMenus(); });
  $('#mLangs').href = ROOT + 'languages.html';

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
  fitAll(); paint(p);
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  return true;
}
async function renderMode() {
  document.body.classList.add('render');
  window.__show = show;
  const s = Q.get('s');
  await show((parseInt(Q.get('p') || '1', 10) || 1) - 1, s === null ? null : +s);
  document.body.dataset.ready = '1';
}

boot().catch(e => { console.error(e); book.innerHTML = '<p style="padding:24px;font:16px system-ui;color:#fff">The book could not load. Please check your connection and try again.</p>'; });
})();
