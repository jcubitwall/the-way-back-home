#!/usr/bin/env python3
"""Add an animated scene to a page.

    python3 tools/clips.py fruit fruit-take3.mp4                      # plays when the page's narration starts
    python3 tools/clips.py fruit fruit-take3.mp4 --sentence 1 --offset 0.6 --sound
    python3 tools/clips.py fruit second.mp4 --add --sentence 3          # a second clip on the same page
    python3 tools/clips.py fruit --remove                               # back to the still picture

What it does:
  * shrinks the clip for phones (720 px wide, no sound track, starts playing before it has fully loaded)
    and saves it as scenes/<page>.mp4
  * saves the clip's first frame as the page's picture (art/src/<page>-clip.jpg), so the page looks
    exactly like the start of the clip until it plays
  * saves the last frame (art/src/<page>-end.jpg); the soft blur under the text switches to it when
    the clip ends, because the page stays frozen on that frame
  * with --sound, keeps the clip's sound effects as scenes/<page>.mp3. They play only while the book
    is being read aloud; without narration every clip is silent
  * --sentence N starts the clip when sentence N of the page is spoken (counting from 0);
    --offset adds seconds. Without narration the clip plays half a second after the page arrives

Then run tools/build.py.
"""
import json, os, subprocess, sys
from common import path, save, story

WIDTH = 720      # video width on phones
STILL = 942      # the still pictures are this wide


def run(*a):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *a], check=True)


def probe(src):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height:format=duration',
                          '-of', 'json', src], capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    v = next(s for s in d['streams'] if s['codec_type'] == 'video')
    return float(d['format']['duration']), v['width'], v['height'], any(s['codec_type'] == 'audio' for s in d['streams'])


def arg(name, default=None, cast=str):
    if name in sys.argv:
        return cast(sys.argv[sys.argv.index(name) + 1])
    return default


def main():
    args = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith('--') and not sys.argv[i - 1] in ('--sentence', '--offset')]
    if not args:
        sys.exit(__doc__)
    pid = args[0]
    st = story()
    pg = next((p for p in st['pages'] if p['id'] == pid), None)
    if not pg:
        sys.exit(f'No page "{pid}". Pages: ' + ', '.join(p['id'] for p in st['pages']))

    if '--remove' in sys.argv:
        pg['clips'] = []
        if pg.get('still'):
            pg['art'] = pg.pop('still')
        save('content/story.json', st)
        print(f'{pid}: back to the still picture ({pg["art"]}). Run tools/build.py.')
        return
    if len(args) < 2:
        sys.exit(__doc__)
    src = os.path.expanduser(args[1])
    dur, w, h, has_audio = probe(src)
    add = '--add' in sys.argv and pg.get('clips')
    n = len(pg['clips']) + 1 if add else 1
    name = pid if n == 1 else f'{pid}-{n}'
    os.makedirs(path('scenes'), exist_ok=True)

    # the clip, small enough for a slow phone connection; "faststart" lets it begin before it has all arrived
    run('-i', src, '-map', '0:v:0', '-an', '-vf', f'scale={WIDTH}:-2:flags=lanczos,format=yuv420p', '-c:v', 'libx264', '-profile:v', 'high',
        '-preset', 'slow', '-crf', '28', '-movflags', '+faststart', path('scenes', name + '.mp4'))
    # first and last frames as stills
    scale = f'scale={min(STILL, w)}:-2:flags=lanczos'
    if n == 1:
        run('-i', src, '-map', '0:v:0', '-vf', scale, '-frames:v', '1', '-q:v', '2', path('art', 'src', f'{pid}-clip.jpg'))
    run('-sseof', '-0.6', '-i', src, '-map', '0:v:0', '-vf', scale, '-q:v', '2', '-update', '1', path('art', 'src', f'{name}-end.jpg'))

    clip = {'src': f'scenes/{name}.mp4', 'sentence': arg('--sentence', 0, int), 'offset': arg('--offset', 0.0, float), 'end': f'{name}-end'}
    snd = path('scenes', name + '.mp3')
    if '--sound' in sys.argv:
        if not has_audio:
            print('  ! this clip has no sound track; it will play silent')
        else:
            run('-i', src, '-vn', '-ac', '2', '-ar', '44100', '-af', 'loudnorm=I=-20:TP=-2', '-c:a', 'libmp3lame', '-b:a', '128k', snd)
            clip['sound'] = f'scenes/{name}.mp3'
    elif os.path.exists(snd):
        os.remove(snd)

    if n == 1:
        if not pg.get('still'):
            pg['still'] = pg['art']          # remember the original picture for --remove
        pg['art'] = f'{pid}-clip'
        pg['clips'] = [clip]
    else:
        pg['clips'].append(clip)
    save('content/story.json', st)
    kb = os.path.getsize(path('scenes', name + '.mp4')) // 1024
    print(f'{pid}: clip {n} saved ({dur:.1f} s, {kb} KB{", with sound" if "sound" in clip else ", silent"}), '
          f'starts on sentence {clip["sentence"]}{f" + {clip["offset"]} s" if clip["offset"] else ""}. Run tools/build.py.')


if __name__ == '__main__':
    main()
