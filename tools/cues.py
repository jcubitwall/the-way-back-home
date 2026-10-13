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
import math, os, re, subprocess, sys
from common import path, save, story, lang, spoken


def silences(mp3, noise='-32dB', dur=0.18):
    p = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', mp3, '-af', f'silencedetect=noise={noise}:d={dur}', '-f', 'null', '-'],
                       capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', p.stderr)]
    ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', p.stderr)]
    length = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp3],
                                  capture_output=True, text=True).stdout.strip())
    return list(zip(starts, ends)), length


def guided(inner, gaps, length, lines, lam=0.6, pad=6, stop=15):
    """Choose one pause per sentence break so the speaking pace (letters per second) stays as even
    as possible across the page, preferring longer pauses. A full stop inside a caption counts as a
    little extra time, so a pause there is not mistaken for the break. Matches the hand-checked
    English captions on every page."""
    lead = gaps[0][1] if gaps and gaps[0][0] < 0.05 else 0.0
    tail = gaps[-1][0] if gaps and gaps[-1][1] > length - 0.05 else length
    n = len(lines)
    sz = [len(l) + pad + stop * len(re.findall(r'[.!?。！？][”“»"]?\s+\S', l)) for l in lines]
    R, m = sum(sz) / max(0.1, tail - lead), sum(sz) / n
    G = [g for g in inner if lead < g[0] < tail]
    if len(G) < n - 1:
        return None
    INF = float('inf')

    def seg(i, a, b):  # sentence i spoken from a to b
        d = b - a
        return INF if d <= 0.15 else min(sz[i] / m, 1.5) * math.log((sz[i] / d) / R) ** 2

    bonus = [lam * math.log(1 + (g[1] - g[0]) / 0.3) for g in G]
    prev, back = [seg(0, lead, g[0]) - bonus[j] for j, g in enumerate(G)], []
    for k in range(1, n - 1):
        cur, bk = [INF] * len(G), [-1] * len(G)
        for j, g in enumerate(G):
            for i in range(j):
                if prev[i] < INF:
                    c = prev[i] + seg(k, G[i][1], g[0]) - bonus[j]
                    if c < cur[j]:
                        cur[j], bk[j] = c, i
        back.append(bk)
        prev = cur
    tot = [p + seg(n - 1, G[j][1], tail) if p < INF else INF for j, p in enumerate(prev)]
    j = min(range(len(G)), key=lambda j: tot[j])
    if tot[j] == INF:
        return None
    path_ = [j]
    for bk in reversed(back):
        j = bk[j]
        path_.append(j)
    return [G[j] for j in reversed(path_)]


def detect(mp3, n, lines=None):
    gaps, length = silences(mp3)
    inner = [(s, e) for s, e in gaps if s > 0.3 and e < length - 0.3]  # ignore silence at the very start/end
    if lines and len(lines) == n and len(inner) >= n - 1:
        best = guided(inner, gaps, length, lines)
        if best:
            return [0.0] + [round(e - 0.1, 2) for s, e in best]
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
        lines = spoken(pg['kind'], d, code)
        n = len(lines)
        c = detect(mp3, n, lines)
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
