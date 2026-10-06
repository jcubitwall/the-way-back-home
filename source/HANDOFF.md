# The Way Back Home — handoff for a new chat

Live site: https://thewaybackhome.net (GitHub Pages, repo jcubitwall/the-way-back-home, branch `main`).
This branch (`build-kit`) holds everything needed to keep building. The working folder in the old chat was /home/claude/book.

## Rebuild the workspace
1. Clone: `git clone -b main https://github.com/jcubitwall/the-way-back-home.git site` and `git clone -b build-kit ... kit`
2. Recreate /home/claude/book with: `site/` (main branch), `kit/source/` (this branch),
   `imgs.json` (kit/source/state/imgs.json = base64 page illustrations; index i = story page i+1, index 15 = cover hug),
   `i18n/data.py` (= translations.py), `fonts/` (kit/source/fonts), `mixes/` (kit/source/mixes), `cues/` (kit/source/cues),
   `s*_at.json` / `s*_vs.json` (kit/source/state).
3. Regenerate `clipframes/sNN_###.png` from `site/scenes/sNN.mp4`:
   `ffmpeg -i site/scenes/sNN.mp4 -vf "fps=12,scale=992:H:flags=lanczos,crop=992:1290:0:OFFSET" clipframes/sNN_%03d.png`
   (H = 992/width*height of the clip, e.g. 1764 for 720x1280, 1742 for 720x1264; OFFSET per scene below).
4. Publishing needs a GitHub fine-grained token (repo-only, Contents + Pages read/write). Ask the user for it.

## Book structure
- 18 pages per language: 01 cover, 02–16 story pages 1–15, 17 "follow Jesus" (A-B-C/1-2-3 + prayer), 18 grown-ups.
- Site files: pages/<lang>/NN.jpg + NN.webp + NN-720.webp ; audio/<lang>/NN.mp3 (+ NN-1/NN-2 for pause scenes 02,04,05);
  scenes/sNN.mp4 + sNN.mp3 ; music/cue_c1..c8.mp3 ; video/The-Way-Back-Home_<LANG>.mp4.
- multi.py renders page images (Playwright). `ONLY=10 python3 multi.py en ...` renders just one file number. FOC dict sets crops.
- vid.py builds downloadable videos (one language per run, ~90–120 s each; run one or two per step).
- Reader = read.html (copied into index.html and <lang>/index.html, keeping each file's own <head>). Bump `const VER` on every change.

## Languages
Narrated (ElevenLabs, ready): en zh hi es fr ar bn pt ru ur de he sw pa ko.
Hidden until narrated: ja (Option B: kanji + furigana via [漢字|かな] markup; awaiting friend's choice 神/神さま and plain vs です・ます; may move to Bible-style),
ki (Kikuyu, draft translation, human narrator), pdt (Plautdietsch, human narrator).
New language narration: two blocks A (pages 1–9) and B (10–18) with [long pause] between pages; split on 8 long silences each.

## Scenes (key = story page; reader SCENES table)
| scene | page | type | crop y% / offset | notes |
| s01 | 1 creation | pause (lead .2, resume .35 before end) | 46.24 / 209 | Eve's laugh only (bird chirp muted) |
| s02 | 2 forbidden tree | straight-through | 27.65 / 125 | synthesized soft glow sound |
| s03 | 3 serpent+Eve tempted | pause (lead .35, rb .4) | 12.83 / 58 | first 2 s of sound muted |
| s04 | 4 bite, sky darkens | pause (lead 2.85, rb .68) | 0.21 / 1 | user-edited sound, used as-is |
| s05 | 5 angel sends them out | straight, freeze at "But God already had a plan" | 25.74 / 122 | silent |
| s06 | 6 Ten-Commandments mirror | straight, freeze at "Sin is like marks" | 0 / 0 | silent; crop keeps tablet tops |
| s07 | 7 washing | straight, freeze at "But no matter how hard" | 51.9 / 246 | |
| s08 | 8 wall crowd, sun breaks | straight, freeze at last sentence | 96.68 / 437 | |
| s09 | 9 preacher, cross glows red | straight, freeze at "Come and see!" | 0 / 0 | silent |
| s10 | 10 kids at the cross | straight, freeze at last sentence | 14.6 / 66 | silent |
| s11 | 11 marks move onto cross | straight, freeze at last sentence | 27.64 / 131 | |
| s13 | 13 Sally runs into Jesus' arms | straight, freeze at "You can still see the scars" | 48.1 / 228 | |
| s14 | 14 George joins hug (10 s) | starts 0.3 s after page opens | 16.46 / 78 | |
| s15 | 15 new Earth (user-trimmed, 8.3 s) | starts 0.1 s after page opens | 64.98 / 308 | crop keeps joined hands |
Page 12 (empty tomb) has no scene yet — check the children appear WITHOUT marks.
Scene sound levels: clip audio loudnorm -33 LUFS (quiet clips -35, never boost > +12 dB), fades in/out.
Cue timing per language lives in s*_at.json (narration time of the cue sentence) and s*_vs.json (clip start time).

## Reader engine (important, hard-won)
- All sound through one Web Audio context (music cues c1–c8 crossfade per section, duck under narration; narration as AudioBuffers).
- Scene sound is driven by the video: starts on 'playing', re-synced if drift > 0.08 s, stops on stall. Pause scenes play NN-1, clip, then NN-2 when clip nears end.
- Android: clips become visible on 'loadeddata' (Chrome won't start invisible muted video); failure -> show final frame.
- Swipe pager (one swipe = one page), WebP pictures, service worker caches versioned files.
- Menu: Download app / Download video / Share / Message us (hello@thewaybackhome.net, Cloudflare Email Routing) / Languages.

## Pending
- Page 12 scene. Japanese finalisation + narration. Kikuyu/Plautdietsch narration. Native-speaker checks.
- Optional final polish: soft crossfades at page turns in the downloadable videos only (user said: later).
- Squash main's git history when the repo nears ~900 MB (keep Pages site under 1 GB). GitHub token expires 2026-11-03.
