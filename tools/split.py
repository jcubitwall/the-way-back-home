#!/usr/bin/env python3
"""Cut one long recording of the whole book into one file per page, then time the captions.

    python3 tools/split.py en recording.mp3           # cut, save audio/en/<page>.mp3, find caption times
    python3 tools/split.py en recording.mp3 --show    # only show where it would cut

Record the whole book in one go from tools/script.py's script: the pages are separated by
<break time="3.0s" /> (ElevenLabs) or a clear pause of 2–3 seconds (a person reading). This finds
the longest pauses, one fewer than the number of pages, and cuts there.
"""
import os, re, subprocess, sys
from common import path, save, story, lang, spoken
from cues import detect


def silences(mp3, noise='-35dB', dur=1.2):
    p = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', mp3, '-af', f'silencedetect=noise={noise}:d={dur}', '-f', 'null', '-'],
                       capture_output=True, text=True)
    s = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', p.stderr)]
    e = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', p.stderr)]
    return list(zip(s, e))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) < 2:
        sys.exit(__doc__)
    code, mp3, show = args[0], args[1], '--show' in sys.argv
    st, t = story(), lang(code)
    pages = [p for p in st['pages'] if t.get('pages', {}).get(p['id'])]
    total = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp3],
                                 capture_output=True, text=True).stdout.strip())
    gaps = [g for g in silences(mp3) if 0.5 < g[0] and g[1] < total - 0.5]
    if len(gaps) < len(pages) - 1:
        sys.exit(f'Found only {len(gaps)} long pauses but there are {len(pages)} pages. Check the recording has a 2–3 second pause between pages.')
    cuts = sorted(sorted(gaps, key=lambda g: g[1] - g[0], reverse=True)[:len(pages) - 1])
    bounds, start = [], 0.0
    for s, e in cuts:
        bounds.append((start, s + 0.25))
        start = max(0.0, e - 0.15)
    bounds.append((start, total))
    for pg, (a, b) in zip(pages, bounds):
        print(f'  {pg["id"]:<10} {a:7.2f} – {b:7.2f}  ({b - a:5.1f} s)')
    if show:
        return
    os.makedirs(path('audio', code), exist_ok=True)
    t.setdefault('cues', {})
    for pg, (a, b) in zip(pages, bounds):
        out = path('audio', code, pg['id'] + '.mp3')
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', f'{a:.3f}', '-to', f'{b:.3f}', '-i', mp3,
                        '-af', 'afade=t=in:d=0.05', '-c:a', 'libmp3lame', '-b:a', '128k', out], check=True)
        n = len(spoken(pg['kind'], t['pages'][pg['id']], code))
        c = detect(out, n) if n > 1 else [0.0]
        if c:
            t['cues'][pg['id']] = c
        else:
            print(f'  ! {pg["id"]}: could not find every sentence break; captions will be spaced by length')
    save(f'content/i18n/{code}.json', t)
    print(f'Saved {len(pages)} pages to audio/{code}/. Run tools/build.py to update the site.')


if __name__ == '__main__':
    main()
