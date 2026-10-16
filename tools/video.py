#!/usr/bin/env python3
"""Make the downloadable video for a language: every page full screen, captions fading in
sentence by sentence with the narration, music underneath.

    python3 tools/video.py es              # needs audio/es/*.mp3 (tools/narrate.py)
    python3 tools/video.py es --no-music
    python3 tools/video.py en --silent     # no recordings yet: captions at reading pace, music only (for checking)

Writes video/The-Way-Back-Home_ES.mp4 (1080×1920, H.264). Pages are photographed from the real
reader (the same layout people see), so the video always matches the site.

Animated scenes play as in the book: each starts on its sentence (cue + offset, one after another),
then holds on the sharp still of its last frame. A scene page is built from three layers: the picture
(bottom), the clip laid into the picture's frame, and everything above the picture (soft blur, shade,
caption) photographed with a see-through background. Scene sounds, and the music hush/rise of a scene,
are mixed in as in the reader.
"""
import http.server, json, os, shutil, subprocess, sys, tempfile, threading
from common import path, story, lang, spoken, ROOT

W, H, FPS = 1080, 1920, 25
FADE = 0.35      # crossfade between captions
TURN = 0.6       # crossfade between pages
GAP = 0.9        # quiet moment after each page's narration
MUSIC = 0.21     # music level under the narrator
SFX = 0.75       # scene sounds, as in the reader
HOLD = 1.2       # a scene page holds this long after its last scene ends
SOFTX = 0.15     # crossfade when the blur behind the text switches to a scene's last frame


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        sys.exit('ffmpeg failed:\n' + p.stderr[-1500:])


def duration(f):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f],
                                capture_output=True, text=True).stdout.strip())


class Quiet(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def log_message(self, *a):
        pass


BOTTOM_CSS = '.pg .soft,.pg .shade,.pg .txt{visibility:hidden!important}'
TOP_CSS = ('.pg>.bg,.pg .art{visibility:hidden!important}'
           'html,body,.book,.track,.pg,.stage{background:transparent!important}')
JS_LAYER = "css => { let s = document.getElementById('vlayer'); if (!s) { s = document.createElement('style'); s.id = 'vlayer'; document.head.appendChild(s); } s.textContent = css; }"
JS_SOFT = """([i, name]) => { const sec = document.querySelectorAll('section.pg')[i];
  const ims = [...sec.querySelectorAll('.soft img')];
  ims.forEach(im => { if (!im.dataset.orig0) im.dataset.orig0 = im.src; im.src = name ? 'art/' + name + '-soft.webp' : im.dataset.orig0; });
  return Promise.all(ims.map(im => im.complete && im.naturalWidth ? 1 : new Promise(r => { im.onload = r; im.onerror = r; }))); }"""
JS_RECT = "i => { const r = document.querySelectorAll('section.pg')[i].querySelector('.art').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }"


def photograph(code, plan, tmp):
    """Open the real reader once and photograph every page and caption at 1080×1920. Scene pages get a bottom
    layer (the picture) and see-through top layers (blur, shade, caption) for every caption and blur variant."""
    from playwright.sync_api import sync_playwright
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Quiet)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{srv.server_address[1]}/'
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': W // 3, 'height': H // 3}, device_scale_factor=3, is_mobile=True)  # a phone screen, photographed sharp
        # only the book's own files (and Google Fonts for non-Latin scripts); no analytics
        pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(base) or 'fonts.g' in r.request.url else r.abort())
        pg.goto(f'{base}index.html?lang={code}&render=1&p=0')
        pg.wait_for_selector('body[data-ready]', timeout=30000)
        show = lambda i, k, kind: pg.evaluate('([p, s]) => window.__show(p, s)', [i, k if kind == 'story' else None])
        for i, page in enumerate(plan):
            if not page.get('clips'):
                for k, st in enumerate(page['states']):
                    show(i, k, page['kind'])
                    st['png'] = os.path.join(tmp, f'{i:02d}-{k:02d}.png')
                    pg.screenshot(path=st['png'])
            else:
                show(i, 0, page['kind'])
                pg.evaluate(JS_LAYER, BOTTOM_CSS)
                page['bottom'] = os.path.join(tmp, f'{i:02d}-bottom.png')
                pg.screenshot(path=page['bottom'])
                x, y, w, h = pg.evaluate(JS_RECT, i)
                page['rect'] = [round(v * 3) for v in (x, y, w, h)]
                pg.evaluate(JS_LAYER, TOP_CSS)
                page['tops'] = {}
                for v, name in enumerate(page['softs']):
                    pg.evaluate(JS_SOFT, [i, name])
                    for k in range(len(page['states'])):
                        show(i, k, page['kind'])
                        out = os.path.join(tmp, f'{i:02d}-top-{v}-{k:02d}.png')
                        pg.screenshot(path=out, omit_background=True)
                        page['tops'][(v, k)] = out
                pg.evaluate(JS_SOFT, [i, None])
                pg.evaluate(JS_LAYER, '')
            print(f'  photographed page {i + 1}/{len(plan)}', end='\r', flush=True)
        b.close()
    srv.shutdown()
    print()


def assemble(stills, out, alpha=False):
    """One pass: every still shows for its time, then crossfades into the next.
    stills = [(png, seconds shown, crossfade into the next)]. alpha=True keeps transparency (for a top layer)."""
    cmd, fc = ['ffmpeg', '-y', '-hide_banner'], []
    pix = 'rgba' if alpha else 'yuv420p'
    for k, (f, d, fade) in enumerate(stills):
        cmd += ['-i', f]
        L = d + (fade if k < len(stills) - 1 else 0)
        # the picture is read once and repeated (reading it again for every frame is very slow)
        fc.append(f'[{k}:v]format={pix},setsar=1,fps={FPS},tpad=stop_mode=clone:stop_duration={L:.3f},trim=duration={L:.3f},setpts=PTS-STARTPTS[s{k}]')
    prev, t = '[s0]', 0.0
    for k in range(1, len(stills)):
        t += stills[k - 1][1]
        fc.append(f'{prev}[s{k}]xfade=transition=fade:duration={stills[k - 1][2]}:offset={t:.3f}[x{k}]')
        prev = f'[x{k}]'
    script = out + '.filter'
    open(script, 'w').write(';\n'.join(fc))
    enc = ['-c:v', 'qtrle', '-pix_fmt', 'argb'] if alpha else ['-c:v', 'libx264', '-preset', 'fast', '-tune', 'stillimage', '-crf', '20', '-pix_fmt', 'yuv420p']
    run(cmd + ['-filter_complex_script', script, '-map', prev, *enc, '-r', str(FPS), out])


def scene_page(i, page, tmp):
    """A page with scenes: picture, clips laid into the picture's frame (then their sharp last frame), top layer."""
    T = page['len'] + TURN
    # the top layer: caption changes (and the blur switching to a scene's last frame) over the page's time
    cuts = sorted({0.0, *[c['end'] for c in page['clips']]})
    starts = [st['at'] for st in page['states']] + [T]
    pieces = []  # (from, to, soft variant, caption state)
    for k in range(len(page['states'])):
        a, b_ = starts[k], starts[k + 1]
        inner = [c for c in cuts if a < c < b_]
        for x, y in zip([a] + inner, inner + [b_]):
            v = sum(1 for c in page['clips'] if c['end'] <= x + 1e-6)
            pieces.append((x, y, v, k))
    stills = []
    for n, (x, y, v, k) in enumerate(pieces):
        nxt = pieces[n + 1] if n + 1 < len(pieces) else None
        fade = 0 if not nxt else (FADE if nxt[3] != k else SOFTX)
        stills.append((page['tops'][(v, k)], y - x, fade))
    top = os.path.join(tmp, f'{i:02d}-top.mov')
    assemble(stills, top, alpha=True)

    x0, y0, w, h = page['rect']
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loop', '1', '-t', f'{T:.3f}', '-i', page['bottom']]
    fc, n_in, cur = [f'[0:v]format=rgba,fps={FPS},setsar=1[b0]'], 1, '[b0]'
    for j, c in enumerate(page['clips']):
        cmd += ['-i', path(c['src'])]
        fc.append(f'[{n_in}:v]fps={FPS},scale={w}:{h},format=rgba,setpts=PTS-STARTPTS+{c["start"]:.3f}/TB[c{j}]')
        fc.append(f"{cur}[c{j}]overlay={x0}:{y0}:eof_action=pass:enable='between(t,{c['start']:.3f},{c['end'] - 0.02:.3f})'[o{j}]")
        n_in += 1; cur = f'[o{j}]'
        nxt_start = page['clips'][j + 1]['start'] if j + 1 < len(page['clips']) else T
        if c.get('hold'):
            cmd += ['-loop', '1', '-t', f'{T:.3f}', '-i', c['hold']]
            fc.append(f'[{n_in}:v]scale={w}:{h},format=rgba,fps={FPS}[h{j}]')
            fc.append(f"{cur}[h{j}]overlay={x0}:{y0}:enable='between(t,{c['end'] - 0.02:.3f},{nxt_start:.3f})'[g{j}]")
            n_in += 1; cur = f'[g{j}]'
    cmd += ['-i', top]
    fc.append(f'[{n_in}:v]format=rgba,fps={FPS}[top]')
    fc.append(f'{cur}[top]overlay=0:0,format=yuv420p,trim=duration={T:.3f},setpts=PTS-STARTPTS[out]')
    script = os.path.join(tmp, f'{i:02d}-scene.filter'); open(script, 'w').write(';\n'.join(fc))
    out = os.path.join(tmp, f'{i:02d}.mp4')
    run(cmd + ['-filter_complex_script', script, '-map', '[out]', '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
               '-pix_fmt', 'yuv420p', '-r', str(FPS), out])
    return out


def join(videos, lens, out):
    """Crossfade the pages into one picture track (each page video runs TURN seconds past its time)."""
    cmd, fc = ['ffmpeg', '-y', '-hide_banner'], []
    for k, v in enumerate(videos):
        cmd += ['-i', v]; fc.append(f'[{k}:v]fps={FPS},setsar=1,format=yuv420p,setpts=PTS-STARTPTS[p{k}]')
    prev, t = '[p0]', 0.0
    for k in range(1, len(videos)):
        t += lens[k - 1]
        fc.append(f'{prev}[p{k}]xfade=transition=fade:duration={TURN}:offset={t:.3f}[j{k}]'); prev = f'[j{k}]'
    fc.append(f'{prev}trim=duration={sum(lens):.3f}[v]')
    script = out + '.filter'; open(script, 'w').write(';\n'.join(fc))
    run(cmd + ['-filter_complex_script', script, '-map', '[v]', '-c:v', 'libx264', '-preset', 'medium', '-tune', 'stillimage',
               '-crf', '21', '-pix_fmt', 'yuv420p', '-r', str(FPS), out])


def envelope(events):
    """ffmpeg volume expression for the music: 1, except where a scene hushes it (to 0 over 2.5 s) and lets it rise again."""
    e = '1'
    for a, b, r in sorted(events, reverse=True):   # hush at a, rise at b over r seconds
        e = (f"if(lt(t,{a:.3f}),{e},if(lt(t,{a + 2.5:.3f}),1-(t-{a:.3f})/2.5,if(lt(t,{b:.3f}),0,"
             f"if(lt(t,{b + r:.3f}),(t-{b:.3f})/{r},1))))")
    return e


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    code, silent, music = args[0], '--silent' in sys.argv, '--no-music' not in sys.argv
    st, t = story(), lang(code)
    plan = []
    for pg in st['pages']:
        d = t.get('pages', {}).get(pg['id'])
        if not d:
            sys.exit(f'{code} has no text for page "{pg["id"]}" yet.')
        lines = spoken(pg['kind'], d, code)
        mp3 = path('audio', code, pg['id'] + '.mp3')
        if not silent and not os.path.exists(mp3):
            sys.exit(f'Missing recording audio/{code}/{pg["id"]}.mp3 (use --silent to check the video without narration).')
        if silent:
            a, mp3 = sum(1.2 + len(s) / 14 for s in lines), None
        else:
            a = duration(mp3)
        cues = t.get('cues', {}).get(pg['id'])
        if not cues or len(cues) != len(lines):
            w = [len(s) + 10 for s in lines]; tot = sum(w); acc = 0; cues = []
            for x in w:
                cues.append(a * acc / tot); acc += x
        # scenes one after another, each from its sentence's cue + offset (as the reader plays them)
        clips, prev = [], 0.0
        for c in pg.get('clips') or []:
            dur = duration(path(c['src']))
            start = max(0.0, (cues[c.get('sentence', 0)] if cues else 0) + c.get('offset', 0), prev)
            hold = path('art', 'src', c['end'] + '.jpg') if c.get('end') else None
            clips.append({**c, 'start': start, 'end': start + dur, 'hold': hold if hold and os.path.exists(hold) else None})
            prev = start + dur
        total = a + GAP
        if clips:
            total = max(total, clips[-1]['end'] + HOLD)
        if pg['kind'] == 'story':
            starts = cues + [total]
            states = [{'at': starts[k], 'len': max(0.5, starts[k + 1] - starts[k])} for k in range(len(lines))]
        else:
            states = [{'at': 0.0, 'len': total}]
        plan.append({'id': pg['id'], 'kind': pg['kind'], 'mood': pg['mood'], 'mp3': mp3, 'len': total, 'states': states,
                     'clips': clips, 'softs': [None] + [c['end'] for c in clips]})
    tmp = tempfile.mkdtemp(prefix='twbh-video-')
    try:
        print(f'Making the {code} video ({sum(p["len"] for p in plan) / 60:.1f} minutes, {sum(len(p["clips"]) for p in plan)} scenes)')
        photograph(code, plan, tmp)
        videos = []
        for i, p in enumerate(plan):
            print(f'  building page {i + 1}/{len(plan)}', end='\r', flush=True)
            if p['clips']:
                videos.append(scene_page(i, p, tmp))
            else:
                stills = [(s_['png'], s_['len'] + (TURN if k == len(p['states']) - 1 else 0), FADE) for k, s_ in enumerate(p['states'])]
                out = os.path.join(tmp, f'{i:02d}.mp4'); assemble(stills, out); videos.append(out)
        print()
        picture = os.path.join(tmp, 'picture.mp4')
        print('  joining pages…', flush=True)
        join(videos, [p['len'] for p in plan], picture)

        # narration: each page's recording followed by its quiet moment
        voice = os.path.join(tmp, 'voice.wav')
        parts = []
        for i, p in enumerate(plan):
            f = os.path.join(tmp, f'v{i:02d}.wav')
            src = ['-i', p['mp3']] if p['mp3'] else ['-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo']
            run(['ffmpeg', '-y', *src, '-af', f'apad,atrim=0:{p["len"]:.3f}', '-ar', '44100', '-ac', '2', f])
            parts.append(f)
        lst = os.path.join(tmp, 'v.txt'); open(lst, 'w').write(''.join(f"file '{x}'\n" for x in parts))
        run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', voice])

        # scene sounds and music hushes, at their place in the whole video
        sfx, hush, at = [], [], 0.0
        for p in plan:
            for c in p['clips']:
                if c.get('sound'):
                    sfx.append((path(c['sound']), at + c['start']))
                if c.get('hush') is not None:
                    rise = c['start'] + (c['rise'] if c.get('rise') is not None else (p['len'] - c['start'] - 3))
                    hush.append((at + c['start'] + c['hush'], at + rise, c.get('riseFor', 4)))
            at += p['len']

        mus = None
        if music:   # one continuous piece per run of pages with the same mood, faded at the joins
            groups = []
            for p in plan:
                if groups and groups[-1][0] == p['mood']:
                    groups[-1][1] += p['len']
                else:
                    groups.append([p['mood'], p['len']])
            mparts = []
            for k, (mood, L) in enumerate(groups):
                f = os.path.join(tmp, f'm{k:02d}.wav')
                run(['ffmpeg', '-y', '-stream_loop', '-1', '-i', path('music', f'cue_{mood}.mp3'), '-af',
                     f'atrim=0:{L:.3f},afade=t=in:d=1.5,afade=t=out:st={max(0, L - 1.5):.3f}:d=1.5,volume={MUSIC}', '-ar', '44100', '-ac', '2', f])
                mparts.append(f)
            ml = os.path.join(tmp, 'm.txt'); open(ml, 'w').write(''.join(f"file '{x}'\n" for x in mparts))
            mus = os.path.join(tmp, 'music.wav')
            run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', ml, '-c', 'copy', mus])
            if hush:
                m2 = os.path.join(tmp, 'music2.wav')
                run(['ffmpeg', '-y', '-i', mus, '-af', f"volume='{envelope(hush)}':eval=frame", m2]); mus = m2

        ins, fc, mix = ['-i', voice], [], ['[0:a]']
        if mus:
            ins += ['-i', mus]; mix.append('[1:a]')
        for k, (f, when) in enumerate(sfx):
            n = len(ins) // 2; ins += ['-i', f]; ms = int(when * 1000)
            fc.append(f'[{n}:a]aresample=44100,aformat=channel_layouts=stereo,volume={SFX},adelay={ms}|{ms}[s{k}]'); mix.append(f'[s{k}]')
        audio = os.path.join(tmp, 'mix.wav')
        if len(mix) > 1:
            fc.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:normalize=0[a]")
            run(['ffmpeg', '-y', *ins, '-filter_complex', ';'.join(fc), '-map', '[a]', audio])
        else:
            audio = voice

        os.makedirs(path('video'), exist_ok=True)
        out = path('video', f'The-Way-Back-Home_{code.upper()}.mp4')
        run(['ffmpeg', '-y', '-i', picture, '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k',
             '-shortest', '-movflags', '+faststart', out])
        print(f'Saved video/{os.path.basename(out)} ({os.path.getsize(out) / 1e6:.0f} MB). Set "video": true for {code} in content/languages.json and run tools/build.py so the menu offers it.')
    finally:
        if '--keep' not in sys.argv:
            shutil.rmtree(tmp, ignore_errors=True)
        else:
            print('kept', tmp)


if __name__ == '__main__':
    main()
