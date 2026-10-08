#!/usr/bin/env python3
"""Write the narration script for a whole language, ready to paste into ElevenLabs.

    python3 tools/script.py en        # writes scripts/The-Way-Back-Home_EN_narration.txt

Pages are separated by <break time="3.0s" /> so tools/split.py can cut the recording back into pages.
Page numbers and Bible references are not read aloud.
"""
import os, sys
from common import path, story, lang, spoken

code = (sys.argv[1:] or sys.exit(__doc__))[0]
st, t = story(), lang(code)
fin = lambda s: s if s[-1:] in '.!?”"»。！？।۔' else s + '.'
pages = [' '.join(fin(l.strip()) for l in spoken(p['kind'], t['pages'][p['id']], code)) for p in st['pages'] if t.get('pages', {}).get(p['id'])]
os.makedirs(path('scripts'), exist_ok=True)
out = path('scripts', f'The-Way-Back-Home_{code.upper()}_narration.txt')
open(out, 'w', encoding='utf-8').write('\n\n<break time="3.0s" />\n\n'.join(pages) + '\n')
print(f'Wrote scripts/{os.path.basename(out)}: {len(pages)} pages, {sum(len(p) for p in pages)} characters')
