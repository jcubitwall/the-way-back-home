#!/usr/bin/env python3
"""Find when each sentence starts in a recording made by a person (not ElevenLabs).

    python3 tools/cues.py pdt              # every page that has a recording
    python3 tools/cues.py pdt garden       # one page
    python3 tools/cues.py pdt garden --show   # print the times without saving

Put the recordings at audio/<lang>/<page id>.mp3 (any normal mp3). The narrator should pause
briefly between sentences; this finds those pauses and takes the longest ones as the sentence
breaks. Check the result in the reader; to fix one by hand, edit the numbers (seconds) under
"cues" in content/i18n/<lang>.json.
"""
import os, re, subprocess, sys
from common import path, save, story, lang, spoken


def silences(mp3, noise='-32dB', dur=0.18):
    p = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', mp3, '-af', f'silencedetect=noise={noise}:d={dur}', '-f', 'null', '-'],
                       capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', p.stderr)]
    ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', p.stderr)]
    length = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp3],
                                  capture_output=True, text=True).stdout.strip())
    return list(zip(starts, ends)), length


def detect(mp3, n):
    gaps, length = silences(mp3)
    inner = [(s, e) for s, e in gaps if s > 0.3 and e < length - 0.3]  # ignore silence at the very start/end
    best = sorted(sorted(inner, key=lambda g: g[1] - g[0], reverse=True)[:n - 1])
    cues = [0.0] + [round(e - 0.1, 2) for s, e in best]
    return cues if len(cues) == n else None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    code, only, show = args[0], set(args[1:]), '--show' in sys.argv
    st, t = story(), lang(code)
    t.setdefault('cues', {})
    for pg in st['pages']:
        if only and pg['id'] not in only:
            continue
        mp3 = path('audio', code, pg['id'] + '.mp3')
        d = t.get('pages', {}).get(pg['id'])
        if not os.path.exists(mp3) or not d:
            continue
        n = len(spoken(pg['kind'], d, code))
        c = detect(mp3, n)
        if not c:
            print(f'  ! {pg["id"]}: found fewer pauses than its {n} sentences; captions will be spaced by sentence length instead')
            continue
        print(f'  {pg["id"]}: ' + ', '.join(f'{x:.2f}' for x in c))
        t['cues'][pg['id']] = c
    if not show:
        save(f'content/i18n/{code}.json', t)
        print('Saved. Run tools/build.py to update the site.')


if __name__ == '__main__':
    main()
