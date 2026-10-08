#!/usr/bin/env python3
"""Record narration with ElevenLabs, with exact timing for every caption.

    export ELEVENLABS_API_KEY=...            # from elevenlabs.io → Profile → API key
    python3 tools/narrate.py es              # every page of Spanish that has no recording yet
    python3 tools/narrate.py es garden rule  # just these pages
    python3 tools/narrate.py es --force      # record every page again

Each page is spoken in one take (so it sounds natural) using the "with timestamps" endpoint,
which returns when every letter is spoken. From that we store when each sentence starts in
content/i18n/<lang>.json → "cues", so captions appear exactly as the narrator says them.

Voices are set in tools/voices.json: copy a voice ID from your ElevenLabs Voice Library for each
language. Recordings are saved to audio/<lang>/<page id>.mp3.
"""
import base64, json, os, sys, urllib.request, urllib.error
from common import path, load, save, story, lang, spoken, CJK


def tts(text, voice, cfg, key):
    q = {'text': text, 'model_id': voice.get('model_id', cfg.get('model_id', 'eleven_multilingual_v2')),
         'voice_settings': {**cfg.get('voice_settings', {}), **voice.get('voice_settings', {})}}
    if voice.get('language_code'):
        q['language_code'] = voice['language_code']
    req = urllib.request.Request(
        f'https://api.elevenlabs.io/v1/text-to-speech/{voice["voice_id"]}/with-timestamps?output_format=mp3_44100_128',
        data=json.dumps(q).encode(), headers={'xi-api-key': key, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f'ElevenLabs said {e.code}: {e.read().decode()[:400]}')


def cue_times(lines, text, sep, alignment):
    """Start time of each line, from the per-letter timing ElevenLabs returns."""
    chars, starts = alignment['characters'], alignment['character_start_times_seconds']
    if ''.join(chars) != text:  # fall back to matching letters one by one
        idx, j, mapping = 0, 0, {}
        for i, ch in enumerate(text):
            while j < len(chars) and chars[j] != ch:
                j += 1
            if j < len(chars):
                mapping[i] = j
                j += 1
        get = lambda i: starts[mapping.get(i, min(len(starts) - 1, i))]
    else:
        get = lambda i: starts[i]
    cues, pos = [], 0
    for k, line in enumerate(lines):
        first = pos + (len(line) - len(line.lstrip()))
        cues.append(0.0 if k == 0 else max(0.0, round(get(first) - 0.08, 2)))
        pos += len(line) + len(sep)
    return cues


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    force = '--force' in sys.argv
    if not args:
        sys.exit(__doc__)
    code, only = args[0], set(args[1:])
    key = os.environ.get('ELEVENLABS_API_KEY') or sys.exit('Set ELEVENLABS_API_KEY first (see the top of this file).')
    cfg = load('tools/voices.json')
    voice = cfg['langs'].get(code) or sys.exit(f'Add a voice for "{code}" to tools/voices.json first.')
    if not voice.get('voice_id'):
        sys.exit(f'tools/voices.json has no voice_id for "{code}" yet.')
    st, t = story(), lang(code)
    os.makedirs(path('audio', code), exist_ok=True)
    t.setdefault('cues', {})
    sep = '' if code in CJK else ' '
    done = 0
    for pg in st['pages']:
        if only and pg['id'] not in only:
            continue
        out = path('audio', code, pg['id'] + '.mp3')
        if os.path.exists(out) and not force and pg['id'] in t['cues']:
            continue
        d = t.get('pages', {}).get(pg['id'])
        if not d:
            print(f'  - {pg["id"]}: no text yet, skipped')
            continue
        lines = [s.strip() for s in spoken(pg['kind'], d, code)]
        text = sep.join(lines)
        print(f'  ● {pg["id"]}: {len(lines)} lines, {len(text)} letters')
        r = tts(text, voice, cfg, key)
        open(out, 'wb').write(base64.b64decode(r['audio_base64']))
        t['cues'][pg['id']] = cue_times(lines, text, sep, r.get('alignment') or r['normalized_alignment'])
        save(f'content/i18n/{code}.json', t)  # save as we go, so a stopped run keeps its work
        done += 1
    print(f'Recorded {done} page(s). Run tools/build.py to update the site.')


if __name__ == '__main__':
    main()
