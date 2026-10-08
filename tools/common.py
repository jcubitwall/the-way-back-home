"""Shared helpers for the book tools. Run every tool from the repository root."""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CJK = {'zh', 'ja'}


def path(*p):
    return os.path.join(ROOT, *p)


def load(rel):
    with open(path(rel), encoding='utf-8') as f:
        return json.load(f)


def save(rel, data):
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if rel.endswith('story.json'):  # one line per page keeps the page list easy to read and reorder
        pages = ',\n'.join('    ' + json.dumps(p, ensure_ascii=False) for p in data['pages'])
        rest = {k: v for k, v in data.items() if k != 'pages'}
        text = json.dumps(rest, ensure_ascii=False, indent=2)[:-2] + ',\n  "pages": [\n' + pages + '\n  ]\n}'
    with open(path(rel), 'w', encoding='utf-8') as f:
        f.write(text + '\n')


def story():
    return load('content/story.json')


def languages():
    return load('content/languages.json')


def lang(code):
    return load(f'content/i18n/{code}.json')


def spoken(kind, d, code='en'):
    """Every line the narrator says on a page, in order. Must match spoken() in app.js:
    one caption and one cue per line."""
    if not d:
        return []
    j = '' if code in CJK else ' '
    if kind == 'story':
        return [s for para in d['text'] for s in para]
    if kind == 'cover':
        return [d['title'], d['subtitle']]
    if kind == 'prayer':
        return [d['title'], d['intro'], *[s['word'] + j + s['rest'] for s in d['steps']], d['prayer'], d['note']]
    if kind == 'grownups':
        return [d['title'], d['intro'], *d['questions'], d['note']]
    return []


def codes(args):
    """Language codes from the command line; 'all' means every language in languages.json."""
    allc = languages()['order']
    if not args or args == ['all']:
        return allc
    bad = [a for a in args if a not in allc]
    if bad:
        sys.exit(f'Unknown language code(s): {", ".join(bad)}. Known: {", ".join(allc)}')
    return args
