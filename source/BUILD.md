# Build kit — The Way Back Home

- `art/page-01.png … page-15.png` — final illustrations (story pages 1–15, in order). The cover uses page-14 (the hug).
- `translations.py` — all text for 13 languages (en, zh, hi, es, fr, ar, bn, pt, ru, ur, de, he, pdt), Bible references per language, RTL flags.
- `build_pages.py` — renders each language as 18 phone-shaped pages (1080×1920: cover, 15 story pages, "Would you like to follow Jesus?", "For grown-ups") and assembles the PDFs. Uses Playwright + img2pdf. Before running, rebuild `imgs.json` (a JSON list of 15 base64 JPEG data URLs from `art/`, ~1400 px tall).
- `fonts/` — Andika, Grandstander, Noto Sans SC / Devanagari / Bengali / Hebrew, Noto Naskh Arabic, Noto Nastaliq Urdu (all SIL Open Font License).
- `narration-raw/en/` — original English ElevenLabs clips. Site copies are loudness-normalized in `/audio/en/`.
- Focus areas (FOC in build_pages.py) control how each picture is cropped into the page layout.
