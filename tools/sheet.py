#!/usr/bin/env python3
"""Translation sheets: every piece of text in one spreadsheet, English beside the translation.

    python3 tools/sheet.py export es         # writes sheets/es.csv (opens in Excel, Numbers, Google Sheets)
    python3 tools/sheet.py import es         # reads sheets/es.csv back into content/i18n/es.json
    python3 tools/sheet.py export all        # one sheet per language

Columns: key (where the text goes; don't change it), english, translation, notes.
Each story sentence is its own row, because each one becomes one caption. Keep the same number
of rows; leave a translation empty to keep it untranslated. When English changes later, export
again: rows whose English changed are marked "English changed – check" in notes.
"""
import csv, os, sys
from common import path, load, save, story, lang, codes

SKIP = {'about', 'cues'}


def flatten(node, prefix=''):
    out = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k in SKIP and not prefix:
                continue
            out += flatten(v, f'{prefix}{k}.' if prefix or k else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out += flatten(v, f'{prefix}{i}.')
    elif isinstance(node, str):
        out.append((prefix.rstrip('.'), node))
    return out


def ordered_keys(en, st):
    """English rows in reading order: title, pages in story order, then menu words."""
    rows = [('title', en['title'])]
    for pg in st['pages']:
        rows += flatten(en['pages'].get(pg['id'], {}), f'pages.{pg["id"]}.')
    rows += flatten(en.get('ui', {}), 'ui.')
    return rows


def set_key(doc, key, value, en):
    parts, node, ref = key.split('.'), doc, en
    for i, p in enumerate(parts):
        last = i == len(parts) - 1
        k = int(p) if isinstance(ref, list) else p
        nxt = None if last else ref[k]
        if isinstance(node, list):
            while len(node) <= k:
                node.append([] if isinstance(ref[len(node)], list) else {} if isinstance(ref[len(node)], dict) else '')
        if last:
            node[k] = value
        else:
            if isinstance(node, dict) and (k not in node or not isinstance(node[k], type(nxt))):
                node[k] = [] if isinstance(nxt, list) else {}
            node, ref = node[k], nxt


def get_key(doc, key):
    node = doc
    for p in key.split('.'):
        try:
            node = node[int(p)] if isinstance(node, list) else node[p]
        except (KeyError, IndexError, ValueError, TypeError):
            return ''
    return node if isinstance(node, str) else ''


def export(code, st, en):
    t = lang(code)
    os.makedirs(path('sheets'), exist_ok=True)
    old = {}
    f = path('sheets', f'{code}.csv')
    if os.path.exists(f):
        with open(f, encoding='utf-8-sig') as fh:
            old = {r['key']: r for r in csv.DictReader(fh)}
    with open(f, 'w', encoding='utf-8-sig', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['key', 'english', 'translation', 'notes'])
        for key, eng in ordered_keys(en, st):
            note = (old.get(key) or {}).get('notes', '')
            if key in old and old[key]['english'] != eng:
                note = ('English changed – check. ' + note).strip()
            w.writerow([key, eng, get_key(t, key) if code != 'en' else eng, note])
    print(f'  wrote sheets/{code}.csv')


def imp(code, en):
    t = lang(code)
    with open(path('sheets', f'{code}.csv'), encoding='utf-8-sig') as fh:
        n = 0
        for r in csv.DictReader(fh):
            v = (r.get('translation') or '').strip()
            if v:
                set_key(t, r['key'], v, en)
                n += 1
    # a page is only kept when all its parts are there, so half-done pages fall back to English
    for pid, ep in en['pages'].items():
        tp = t.get('pages', {}).get(pid)
        if tp is not None and len(flatten(tp)) != len(flatten(ep)):
            print(f'  ! {code}: page "{pid}" is only partly translated')
    save(f'content/i18n/{code}.json', t)
    print(f'  {code}: {n} pieces of text imported')


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ('export', 'import'):
        sys.exit(__doc__)
    st, en = story(), lang('en')
    for code in codes(sys.argv[2:]):
        export(code, st, en) if sys.argv[1] == 'export' else imp(code, en)


if __name__ == '__main__':
    main()
