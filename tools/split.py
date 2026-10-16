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


def guided_cuts(gaps, pages, t, code, total, window=12.0):
    """Pick one pause per page break: where the text says the break should be (by length),
    take the longest pause within `window` seconds of it, always moving forward."""
    sizes = [len(' '.join(spoken(p['kind'], t['pages'][p['id']], code))) for p in pages]
    cuts, done, last = [], 0, 0.0
    for n in sizes[:-1]:
        done += n
        guess = total * done / sum(sizes)
        near = [g for g in gaps if g[0] > last and abs((g[0] + g[1]) / 2 - guess) <= window]
        if not near:
            near = [min((g for g in gaps if g[0] > last), key=lambda g: abs((g[0] + g[1]) / 2 - guess))]
        best = max(near, key=lambda g: g[1] - g[0])
        cuts.append(best)
        last = best[1]
    return cuts


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
        # ElevenLabs v3 "[long pause]" gives only 1–2 s: look for shorter pauses, guided by text length
        gaps = [g for g in silences(mp3, dur=0.5) if 0.5 < g[0] and g[1] < total - 0.5]
    if len(gaps) < len(pages) - 1:
        sys.exit(f'Found only {len(gaps)} long pauses but there are {len(pages)} pages. Check the recording has a 2–3 second pause between pages.')
    cuts = guided_cuts(gaps, pages, t, code, total)
    # --at=locked:189.8,new-earth:334.5 forces the break after a page to the pause at that time
    # (use when ElevenLabs made some page gaps as short as sentence gaps and the guess went wrong)
    at = next((a[5:] for a in sys.argv if a.startswith('--at=')), '')
    if at:
        fine = silences(mp3, dur=0.2)
        ids = [p['id'] for p in pages]
        for item in at.split(','):
            pid, sec = item.split(':')
            sec = float(sec)
            g = min(fine, key=lambda g: 0 if g[0] <= sec <= g[1] else min(abs(g[0] - sec), abs(g[1] - sec)))
            cuts[ids.index(pid)] = g
        cuts.sort()
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
                        '-af', 'afade=t=in:d=0.05', '-ac', '1', '-c:a', 'libmp3lame', '-b:a', '64k', out], check=True)
        lines = spoken(pg['kind'], t['pages'][pg['id']], code)
        n = len(lines)
        c = detect(out, n, lines) if n > 1 else [0.0]
        if c:
            t['cues'][pg['id']] = c
        else:
            print(f'  ! {pg["id"]}: could not find every sentence break; captions will be spaced by length')
    from pauses import hold
    for pg in pages:
        for m in hold(code, pg, t):
            print(f'  {m}')
    save(f'content/i18n/{code}.json', t)
    print(f'Saved {len(pages)} pages to audio/{code}/. Run tools/build.py to update the site.')


if __name__ == '__main__':
    main()
