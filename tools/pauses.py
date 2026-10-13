#!/usr/bin/env python3
"""Hold the dramatic pauses a page asks for, in every language.

    python3 tools/pauses.py de         # one language
    python3 tools/pauses.py all        # every language with recordings
    python3 tools/pauses.py de --show  # only report

A page in content/story.json can ask for silence before one of its sentences, e.g. the fruit page:
    "pauses": [{"before": 2, "min": 1.6}]
means at least 1.6 s of silence before sentence 2 ("Uh-oh"), so the lightning in the scene strikes
after the narrator has finished and there is a hush before the next line. Where a recording's pause
is shorter, silence is added in the middle of it and the later captions move by the same amount.
tools/split.py runs this automatically after cutting a new recording.
"""
import os, re, shutil, subprocess, sys, tempfile
from common import path, save, story, lang, codes


def gaps(mp3):
    p = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', mp3, '-af', 'silencedetect=noise=-35dB:d=0.1', '-f', 'null', '-'],
                       capture_output=True, text=True)
    return list(zip([float(x) for x in re.findall(r'silence_start: ([\d.]+)', p.stderr)],
                    [float(x) for x in re.findall(r'silence_end: ([\d.]+)', p.stderr)]))


def insert(mp3, at, secs):
    tmp = tempfile.mktemp(suffix='.mp3')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', mp3, '-filter_complex',
                    f'[0:a]atrim=0:{at:.3f},asetpts=N/SR/TB[a];anullsrc=r=44100:cl=mono,atrim=0:{secs:.3f}[s];'
                    f'[0:a]atrim={at:.3f},asetpts=N/SR/TB[b];[a][s][b]concat=n=3:v=0:a=1',
                    '-ac', '1', '-ar', '44100', '-c:a', 'libmp3lame', '-b:a', '64k', tmp], check=True)
    shutil.move(tmp, mp3)


def hold(code, pg, t, show=False):
    """Apply one page's pauses for one language; returns a list of what changed."""
    mp3, c, done = path('audio', code, pg['id'] + '.mp3'), t.get('cues', {}).get(pg['id']), []
    if not os.path.exists(mp3) or not c:
        return done
    for p in pg.get('pauses', []):
        k, need = p['before'], p['min']
        if k >= len(c):
            continue
        speech = c[k] + 0.1                     # cues sit 0.1 s before the voice starts
        g = min(gaps(mp3), key=lambda g: abs(g[1] - speech), default=None)
        if not g or abs(g[1] - speech) > 0.4:
            done.append(f'{pg["id"]}: could not find the pause before sentence {k}')
            continue
        add = round(need - (g[1] - g[0]), 2)
        if add < 0.05:
            continue
        done.append(f'{pg["id"]}: +{add:.2f}s before sentence {k}')
        if not show:
            insert(mp3, (g[0] + g[1]) / 2, add)
            c = c[:k] + [round(x + add, 2) for x in c[k:]]
            t['cues'][pg['id']] = c
    return done


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    show = '--show' in sys.argv
    for code in codes(args):
        t, msgs = lang(code), []
        for pg in story()['pages']:
            msgs += hold(code, pg, t, show)
        for m in msgs:
            print(f'  {code} {m}')
        if msgs and not show:
            save(f'content/i18n/{code}.json', t)


if __name__ == '__main__':
    main()
