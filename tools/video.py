#!/usr/bin/env python3
"""Make the downloadable video for a language: every page full screen, captions fading in
sentence by sentence with the narration, music underneath.

    python3 tools/video.py es              # needs audio/es/*.mp3 (tools/narrate.py)
    python3 tools/video.py es --no-music
    python3 tools/video.py en --silent     # no recordings yet: captions at reading pace, music only (for checking)

Writes video/The-Way-Back-Home_ES.mp4 (1080×1920, H.264). Pages are photographed from the real
reader (the same layout people see), so the video always matches the site.
Not yet included: the animated scenes. They will play in the site; the video shows the picture still.
"""
import http.server, os, shutil, subprocess, sys, tempfile, threading
from common import path, story, lang, spoken, ROOT

W, H, FPS = 1080, 1920, 25
FADE = 0.35      # crossfade between captions
TURN = 0.6       # crossfade between pages
GAP = 0.9        # quiet moment after each page's narration
MUSIC = 0.21     # music level under the narrator


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


def photograph(code, plan, tmp):
    """Open the real reader once and photograph every page and caption at 1080×1920."""
    from playwright.sync_api import sync_playwright
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Quiet)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{srv.server_address[1]}/'
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': W // 3, 'height': H // 3}, device_scale_factor=3, is_mobile=True)  # a phone screen, photographed sharp
        # only the book's own files (and Google Fonts for non-Latin scripts); no analytics
        pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith(base) or 'fonts.g' in r.request.url else r.abort())
        pg.goto(f'{base}index.html?lang={code}&render=1&p=1')
        pg.wait_for_selector('body[data-ready]', timeout=30000)
        for i, page in enumerate(plan):
            for k, st in enumerate(page['states']):
                pg.evaluate('([p, s]) => window.__show(p, s)', [i, k if page['kind'] == 'story' else None])
                st['png'] = os.path.join(tmp, f'{i:02d}-{k:02d}.png')
                pg.screenshot(path=st['png'])
            print(f'  photographed page {i + 1}/{len(plan)}', end='\r', flush=True)
        b.close()
    srv.shutdown()
    print()


def assemble(stills, out):
    """One pass: every still shows for its time, then crossfades into the next.
    stills = [(png, seconds shown, crossfade into the next)]."""
    cmd, fc = ['ffmpeg', '-y', '-hide_banner'], []
    for k, (f, d, fade) in enumerate(stills):
        cmd += ['-i', f]
        L = d + (fade if k < len(stills) - 1 else 0)
        # the picture is read once and repeated (reading it again for every frame is very slow)
        fc.append(f'[{k}:v]format=yuv420p,setsar=1,fps={FPS},tpad=stop_mode=clone:stop_duration={L:.3f},trim=duration={L:.3f},setpts=PTS-STARTPTS[s{k}]')
    prev, t = '[s0]', 0.0
    for k in range(1, len(stills)):
        t += stills[k - 1][1]
        fc.append(f'{prev}[s{k}]xfade=transition=fade:duration={stills[k - 1][2]}:offset={t:.3f}[x{k}]')
        prev = f'[x{k}]'
    script = out + '.filter'
    open(script, 'w').write(';\n'.join(fc))
    run(cmd + ['-filter_complex_script', script, '-map', prev, '-c:v', 'libx264', '-preset', 'fast', '-tune', 'stillimage',
               '-crf', '21', '-pix_fmt', 'yuv420p', '-r', str(FPS), out])


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    code, silent, music = args[0], '--silent' in sys.argv, '--no-music' not in sys.argv
    st, t, en = story(), lang(code), lang('en')
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
        total = a + GAP
        if pg['kind'] == 'story':
            starts = cues + [total]
            states = [{'len': max(0.5, starts[k + 1] - starts[k])} for k in range(len(lines))]
        else:
            states = [{'len': total}]
        plan.append({'id': pg['id'], 'kind': pg['kind'], 'mood': pg['mood'], 'mp3': mp3, 'len': total, 'states': states})
    tmp = tempfile.mkdtemp(prefix='twbh-video-')
    try:
        print(f'Making the {code} video ({sum(p["len"] for p in plan) / 60:.1f} minutes)')
        photograph(code, plan, tmp)
        stills = []
        for i, p in enumerate(plan):
            for k, st_ in enumerate(p['states']):
                last_on_page = k == len(p['states']) - 1
                stills.append((st_['png'], st_['len'], TURN if last_on_page else FADE))
        picture = os.path.join(tmp, 'picture.mp4')
        print('  joining pictures…', flush=True)
        assemble(stills, picture)

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

        audio = voice
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
            audio = os.path.join(tmp, 'mix.wav')
            run(['ffmpeg', '-y', '-i', voice, '-i', mus, '-filter_complex', 'amix=inputs=2:duration=first:normalize=0', audio])

        os.makedirs(path('video'), exist_ok=True)
        out = path('video', f'The-Way-Back-Home_{code.upper()}.mp4')
        run(['ffmpeg', '-y', '-i', picture, '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k',
             '-shortest', '-movflags', '+faststart', out])
        print(f'Saved video/{os.path.basename(out)} ({os.path.getsize(out) / 1e6:.0f} MB). Run tools/build.py so the menu offers it.')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
