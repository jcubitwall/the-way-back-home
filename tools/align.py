#!/usr/bin/env python3
"""Cut one long English recording into pages by matching the speech to the script, word by word.

    pip install pocketsphinx          # once (includes an English model, works offline)
    python3 tools/align.py en recording.mp3
    python3 tools/align.py en recording.mp3 --show    # only show the page boundaries

Use this when the recording has no long pauses between pages (ElevenLabs sometimes ignores
<break> tags). Every word of the script must be in the recording, in order. It saves
audio/<lang>/<page>.mp3 and the exact start of every caption. English only: the bundled model is
English. For other languages record page by page (tools/narrate.py) or use tools/split.py.
"""
import os, re, subprocess, sys, tempfile
from common import path, save, story, lang, spoken


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) < 2:
        sys.exit(__doc__)
    code, mp3, show = args[0], args[1], '--show' in sys.argv
    from pocketsphinx import Decoder, get_model_path
    st, t = story(), lang(code)
    pages = [p for p in st['pages'] if t.get('pages', {}).get(p['id'])]
    words = []
    for pg in pages:
        for li, line in enumerate(spoken(pg['kind'], t['pages'][pg['id']], code)):
            for w in re.findall(r"[A-Za-z’']+(?:-[A-Za-z]+)?", line):
                words.append((pg['id'], li, w.lower().replace('’', "'")))
    mp = get_model_path()
    d = Decoder(hmm=os.path.join(mp, 'en-us', 'en-us'), dict=os.path.join(mp, 'en-us', 'cmudict-en-us.dict'), loglevel='FATAL')
    unknown = sorted({w for *_, w in words if d.lookup_word(w) is None})
    if unknown:
        sys.exit('These words are not in the aligner dictionary: ' + ', '.join(unknown))
    with tempfile.NamedTemporaryFile(suffix='.raw') as raw:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mp3, '-ac', '1', '-ar', '16000', '-f', 's16le', raw.name], check=True)
        d.set_align_text(' '.join(w for *_, w in words))
        d.start_utt(); d.process_raw(open(raw.name, 'rb').read(), full_utt=True); d.end_utt()
    segs = [(s.start_frame / 100, s.end_frame / 100) for s in d.seg() if s.word not in ('<s>', '</s>', '<sil>', '(NULL)')]
    if len(segs) != len(words):
        sys.exit(f'Could only match {len(segs)} of {len(words)} words. Is the recording exactly the current script?')
    info = []
    for (pid, li, _), (s, e) in zip(words, segs):
        if not info or info[-1]['id'] != pid:
            info.append({'id': pid, 'start': s, 'end': e, 'lines': {}})
        info[-1]['end'] = e
        info[-1]['lines'].setdefault(li, s)
    total = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp3],
                                 capture_output=True, text=True).stdout.strip())
    for k, p in enumerate(info):  # cut halfway through the pause between pages
        p['a'] = 0.0 if k == 0 else (info[k - 1]['end'] + p['start']) / 2
        p['b'] = total if k == len(info) - 1 else (p['end'] + info[k + 1]['start']) / 2
        print(f"  {p['id']:<10} {p['a']:7.2f} – {p['b']:7.2f}  ({p['b'] - p['a']:5.1f} s, {len(p['lines'])} captions)")
    if show:
        return
    os.makedirs(path('audio', code), exist_ok=True)
    t.setdefault('cues', {})
    for p in info:
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', f"{p['a']:.3f}", '-to', f"{p['b']:.3f}", '-i', mp3,
                        '-af', f"afade=t=in:d=0.04,afade=t=out:st={max(0, p['b'] - p['a'] - 0.06):.3f}:d=0.06",
                        '-c:a', 'libmp3lame', '-b:a', '128k', path('audio', code, p['id'] + '.mp3')], check=True)
        t['cues'][p['id']] = [0.0 if li == 0 else round(max(0.0, s - p['a'] - 0.08), 2) for li, s in sorted(p['lines'].items())]
    save(f'content/i18n/{code}.json', t)
    print(f'Saved {len(info)} pages to audio/{code}/ with caption timings. Run tools/build.py to update the site.')


if __name__ == '__main__':
    main()
