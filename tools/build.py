#!/usr/bin/env python3
"""Get the site ready to publish, and report what is still missing in each language.

    python3 tools/build.py            # pictures, language pages, version stamp, report
    python3 tools/build.py --check    # report only, change nothing

What it does:
  * makes web pictures from art/src/*.jpg (art/<name>-720.webp and art/<name>.webp)
  * writes a page for every language at <code>/index.html, so links like thewaybackhome.net/es/ work
  * stamps a new version on pictures, sound and code so phones fetch the new files
  * marks a language "narration": true when every page has a recording, and "video": true when
    its downloadable video exists (it never marks a language "ready"; you decide that)
  * prints a table of what each language still needs
"""
import os, re, sys, time
from common import ROOT, path, load, save, story, languages, lang, spoken

CHECK = '--check' in sys.argv


def build_art(st):
    from PIL import Image
    used = {p['art'] for p in st['pages']} | {'hug'}
    made = 0
    for name in sorted(used):
        src = path('art', 'src', name + '.jpg')
        if not os.path.exists(src):
            print(f'  ! missing picture art/src/{name}.jpg')
            continue
        for suffix, width, q in (('-720', 720, 80), ('', None, 84)):
            out = path('art', f'{name}{suffix}.webp')
            if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(src):
                continue
            im = Image.open(src).convert('RGB')
            if width and im.width > width:
                im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
            im.save(out, 'WEBP', quality=q, method=6)
            made += 1
    print(f'  pictures: {made} made, {len(used)} in use')


def stamp(html, v):
    return re.sub(r'(app\.(?:js|css)|fonts/fonts\.css)(\?v=[\w.-]+)?', lambda m: f'{m.group(1)}?v={v}', html)


def build_pages(langs, v):
    tpl = open(path('index.html'), encoding='utf-8').read()
    open(path('index.html'), 'w', encoding='utf-8').write(stamp(tpl, v))
    page = stamp(tpl, v).replace('<!--BASE-->', '<base href="../">')
    for code in langs['order']:
        meta = langs['langs'][code]
        os.makedirs(path(code), exist_ok=True)
        html = page.replace('<html lang="en">', f'<html lang="{code}" dir="{meta.get("dir", "ltr")}">')
        html = html.replace('content="https://thewaybackhome.net/"', f'content="https://thewaybackhome.net/{code}/"')
        open(path(code, 'index.html'), 'w', encoding='utf-8').write(html)
    print(f'  language pages: {len(langs["order"])}')


def report(st, langs):
    en = lang('en')
    rows, changed = [], False
    for code in langs['order']:
        meta, t = langs['langs'][code], lang(code)
        pages = t.get('pages', {})
        missing, shape, audio, cues = [], [], 0, 0
        for pg in st['pages']:
            d, e = pages.get(pg['id']), en['pages'].get(pg['id'])
            if not d:
                missing.append(pg['id'])
                continue
            n, ne = len(spoken(pg['kind'], d, code)), len(spoken(pg['kind'], e))
            if n != ne:
                shape.append(f'{pg["id"]} ({n} lines, English has {ne})')
            if os.path.exists(path('audio', code, pg['id'] + '.mp3')):
                audio += 1
            c = t.get('cues', {}).get(pg['id'])
            if c and len(c) == n:
                cues += 1
        total = len(st['pages'])
        narr = audio == total
        video = os.path.exists(path('video', f'The-Way-Back-Home_{code.upper()}.mp4'))
        if meta.get('narration', False) != narr or meta.get('video', False) != video:
            meta['narration'], meta['video'] = narr, video
            changed = True
        rows.append((code, meta['english'], total - len(missing), total, audio, cues, video, meta.get('ready', False), missing, shape))
    if changed and not CHECK:
        save('content/languages.json', langs)
    print()
    print(f'  {"lang":<5}{"":<20}{"text":>8}{"audio":>8}{"cues":>7}{"video":>7}{"public":>8}')
    for code, name, have, total, audio, cues, video, ready, missing, shape in rows:
        print(f'  {code:<5}{name[:19]:<20}{have:>5}/{total:<2}{audio:>5}/{total:<2}{cues:>4}/{total:<2}{"yes" if video else "-":>5}{"yes" if ready else "-":>8}')
    print()
    for code, name, have, total, audio, cues, video, ready, missing, shape in rows:
        if shape:
            print(f'  ! {code}: line count differs from English on ' + '; '.join(shape))
        if ready and (have < total or audio < total):
            print(f'  ! {code} is public but still missing ' + ', '.join(x for x in [f'{total - have} pages of text' if have < total else '', f'{total - audio} recordings' if audio < total else ''] if x))


def main():
    st, langs = story(), languages()
    if not CHECK:
        v = time.strftime('%Y%m%d%H%M%S')
        print(f'Building version {v}')
        build_art(st)
        st['version'] = v
        save('content/story.json', st)
        build_pages(langs, v)
    report(st, langs)


if __name__ == '__main__':
    main()
