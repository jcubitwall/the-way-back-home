# CLAUDE.md: The Way Back Home (v2)

Read this first in every new conversation about the book. It says where the project stands, how the
owner wants things done, and how the tools work. **Update the "Status" and "Open items" sections
before you finish any session that changes something**, so the next conversation starts where this
one stopped.

## What this is

An illustrated, narrated children's Bible story (ages 6–12) by Johnny Wall, from Creation to the new
earth. It is read full screen on a phone: each page is a picture or a short animated clip, the words
appear one sentence at a time with the narrator, and each chapter has its own music.

- **Test site:** https://jcubitwall.github.io/the-way-back-home-v2/ (this repo, branch `main`, GitHub Pages).
- **Public site:** thewaybackhome.net. **16 Oct 2026: Johnny decided to go live with v2** (16 languages; Kikuyu and
  Plautdietsch stay unlisted until recorded). Prep is pushed (old-address `/assets/` copies, sw.js clears the old cache).
  The switch itself is two GitHub Pages settings Johnny makes by hand (the Pages API is blocked from this environment):
  remove the custom domain from `jcubitwall/the-way-back-home`, then set it on this repo and tick Enforce HTTPS.
  Keep the old repo (archive it, don't delete it). See "Going live" in README.md.
- **Characters:** three kids, Sally (red top, jeans, long red-brown wavy hair, glasses),
  George (yellow polo, curly black hair), Chase (black T-shirt, spiky black hair). They are never named
  in the text. Johnny makes the stills with ChatGPT (it knows the characters and art style) and the
  clips with Grok.

## How Johnny wants things done

- **Just do it, then report briefly.** Commit and push straight to `main`. He tests on his phone at the
  test site. Say in plain words what changed; skip the technical detail unless he asks.
- **Translations go for meaning, not word for word.** Write what a native children's author would write.
  Replace English-only idioms with local ones. Never soften sin, hell or the gospel.
- **Script wording must work in every language.** No English-only sound words (e.g. "Scrub, scrub, scrub!" was dropped).
- **Clips:** the characters never speak (wordless expressions and gestures). Clips carry only their own
  sound effects, never music. They must stay true to the Bible. Each clip holds its first frame, plays,
  then freezes on its last frame while the narration continues.
- **Narration:** only real recordings. ElevenLabs v3 for most languages; a human narrator for Plautdietsch.
  A language is listed only once it has a recording.
- **Dramatic pause:** in every language there must be a hush where Adam bites the fruit and the lightning
  strikes, before "Uh-oh" (handled automatically, see Tools).

## Status (15 Oct 2026)

| | |
|---|---|
| English | Finished and public: 18 pages, v3 narration, 15 clips, 14 music tracks |
| German (de) | Finished and public: text, ElevenLabs v3 recording, captions timed |
| Hebrew (he) | Finished and public 15 Oct 2026: reviewed modern text, ElevenLabs v3 recording (6:51), captions timed, pace even (10–12 chars/s) |
| Chinese (zh) | Finished and public 15 Oct 2026: ElevenLabs v3 recording (6:48), captions timed, pace even (about 4–5 chars/s). Page 7 caption 2 moved by hand to 4.2 s (the auto break landed on the comma inside sentence 1) |
| Hindi (hi) | Finished and public 15 Oct 2026: ElevenLabs v3 recording (7:47), captions timed, pace even (about 6–7 letters/s), no hand fixes needed |
| Spanish (es) | Finished and public 15 Oct 2026: ElevenLabs v3 recording (6:55), captions timed, pace even (about 10–12 letters/s), no hand fixes needed |
| French (fr) | Finished and public 15 Oct 2026: ElevenLabs v3 recording (6:48), captions timed, pace even (about 10–14 letters/s), every caption break checked against a real pause, no hand fixes needed |
| Arabic (ar) | Finished and public 15 Oct 2026: ElevenLabs v3 recording, Jordanian voice (6:51), captions timed, pace even (about 8–9 letters/s). From page 8 on, ElevenLabs made the page gaps only ~0.5 s (same as sentence gaps), so the auto cut slipped; the breaks were found by lining up every phrase with the speech and forced with `split.py --at=locked:189.8,scrub:215.5,door:239.6,cross:256.2,choice:282.4,tomb:298.6,gates:317.9,new-earth:334.6,prayer:373.0`. Page 11 caption 3 moved by hand to 8.8 s |
| Bengali (bn) | Finished and public 15 Oct 2026: ElevenLabs v3 recording (8:39), clean page gaps, captions timed, pace even (about 5–6 letters/s), every caption break on a real pause, no hand fixes needed |
| Portuguese (pt) | Finished and public 15 Oct 2026: ElevenLabs v3 recording (7:16), clean page gaps, captions timed, pace even (about 9–12 letters/s), every caption break on a real pause, no hand fixes needed |
| Russian (ru) | Finished and public 15 Oct 2026: ElevenLabs v3 recording (7:45), clean page gaps, captions timed, pace even (about 8–10 letters/s). New-earth caption 2 moved by hand to 1.2 s (auto put it after the first phrase of sentence 2) |
| Urdu (ur) | Finished and public 15 Oct 2026: ElevenLabs v3 recording (8:58), clean page gaps, captions timed, pace even (about 7–10 letters/s), every caption break on a real pause, no hand fixes needed. A native speaker's read of the text is still worth having |
| Japanese (ja) | Finished and public 16 Oct 2026: ElevenLabs v3 recording (8:59), clean page gaps, captions timed, pace even (about 6 chars/s), every caption break on a real pause, no hand fixes needed. Furigana above every kanji |
| Swahili (sw) | Finished and public 15 Oct 2026: ElevenLabs v3 recording (8:22), captions timed, pace even (about 9–11 letters/s). The tomb/gates page break was a short gap, so it was forced with `split.py --at=tomb:373.0`; checked by phrase alignment. A native speaker's read of the text is still worth having |
| Punjabi (pa) | Finished and public 16 Oct 2026: new narrator, recorded in four ElevenLabs v3 pieces (`scripts/The-Way-Back-Home_PA_narration_v3_part0..3.txt`), joined with 2.5 s gaps (7:51 total). Page gaps inside the pieces were short, so breaks were found by phrase alignment and forced with `split.py pa joined.mp3 --at=fruit:103.5,exile:135.97,road:152.07,test:179.07,locked:208.57,scrub:229.4,door:265.97,cross:291.07,choice:325.17,tomb:342.17,gates:360.8,new-earth:378.31,prayer:432.11`. Captions on road, test, scrub, choice, gates and prayer set by hand from the Hindi sentence pattern (auto timing is unreliable here because Gurmukhi vowel signs throw off letter counts). Law page re-cut so the crack hush sits before "Like Adam and Eve…". A native speaker's read is still worth having |
| Korean (ko) | Finished and public 16 Oct 2026: ElevenLabs v3 recording (7:52), clean page gaps, captions timed, pace even (about 5–6 syllables/s), every caption break on a real pause, no hand fixes needed |
| Kikuyu (ki) | Text written (careful draft). ElevenLabs has no Kikuyu (checked 16 Oct 2026; a Swahili voice would flatten ĩ/ũ and tone), so Johnny chose a **human narrator**, who should also check the text before recording. Narrator script (with instructions, asks them to correct the text first): `scripts/The-Way-Back-Home_KI_narrator-script.txt`. Not listed until recorded |
| Plautdietsch (pdt) | Text written; plain script for his human narrator (no v3 tags) |

- The narration scripts, with a Copy button per language, are on the artifact page
  "Way Back Home Narration Scripts" (https://claude.ai/artifact/M8PZotoUtoTfAYmjkoUGbx). The same files
  are in `scripts/The-Way-Back-Home_<CODE>_narration_v3.txt`. If you change a language's text, rebuild that
  script and republish the page.
- **Translation choices:**
  - Prayer page: A-B-C only in German (Anerkennen, Bekennen, Christus folgen). Every other language uses steps 1-2-3.
  - Hebrew uses ישוע (Yeshua). Reviewed 15 Oct 2026 for plain modern Israeli Hebrew: no archaic Bible phrasing (e.g. "אם תאכלו ממנו, תמותו", "אלוהים באמת אמר את זה?"); "Bible" = כתבי הקודש (not הכתובים, which also means the Writings section); "goodness" = הטוב של ישוע (not צדקה, which now means charity); "church" = בית הכנסת או כנסייה; "bad news" = בשורה רעה, to mirror הבשורה הטובה; grown-ups page = למבוגרים.
  - Japanese has furigana (16 Oct 2026, suggested by Johnny's Japanese friend): small hiragana above every kanji, as in Japanese picture books. The text in ja.json is unchanged (so scripts, cues and narration are unaffected); the readings live in `"ruby"` in ja.json as [kanji run, kana that must follow, reading] rules, e.g. 大+すき=だい, 大+き=おお, 来+る=く, 来=き, 生+まれ=う, 生+き=い, 出+エジプト=しゅつ, 何+だ=なん. app.js `tx()` draws them as `<ruby>` on every book page (cover, story, captions, prayer, grown-ups). If the Japanese text changes, check every kanji still has a rule (any language can use the same mechanism).
  - The Hindi, Punjabi and Urdu titles avoid "ghar wapsi" (the name of a political reconversion campaign) and say "the way to return home" instead.
- **Meaning review (15 Oct 2026):** es fr pt ru zh hi ar bn ur ja were each re-checked line by line against the English for meaning, archaic Bible phrasing and words with a misleading modern sense, and the v3 scripts updated to match. Notable choices: Arabic and Urdu say "God's commands" (وصايا الله / خدا کے حکم) not شريعة/شریعت (heard as Islamic sharia); Urdu uses جنت for heaven's gates; Bengali "Jesus' goodness" = নিখুঁত পবিত্রতা (ধার্মিকতা reads as "religiosity"); Hindi भलाई → अच्छाई; Japanese 方 → お方 so TTS reads かた; Portuguese avoids "seu" (could mean "your").
- **Need a native speaker's read before recording:** Kikuyu and Plautdietsch are careful drafts. Urdu,
  Punjabi and Swahili would also benefit from one. Record one Kikuyu page as a test first, because
  ElevenLabs may not pronounce Kikuyu well.
- **Music:** 14 tracks, `music/cue_m01..m14.mp3`. m14 "Welcome Home" plays across gates and new-earth.
  Prayer and grown-ups use m12b. Tracks are level-matched to about −21.5 LUFS.

## When a recording comes back (the usual job)

Tip: after `split.py`, check each caption break against the real pauses (`ffmpeg -af silencedetect=n=-32dB:d=0.15`). Short languages like Chinese can let the auto timing pick a comma pause inside a sentence (and for Indic scripts a sister language's verified cues, e.g. Hindi for Punjabi, are a good guide to where sentence breaks fall); fix that cue by hand in `content/i18n/<code>.json`. If a page comes out far too long or short (ElevenLabs sometimes shortens the [long pause] to a sentence-sized gap), find the real breaks and pass them with `split.py <code> file.mp3 --at=<page>:<seconds>,…` (seconds = inside the pause that ends that page).

1. Save the upload, then cut it: `python3 tools/split.py <code> recording.mp3`. This finds the page
   breaks, saves `audio/<code>/<page>.mp3`, times every caption and adds the fruit-page hush.
2. Check the result: every caption's pace should look even. Only deliberate slow lines are slow
   ("Uh-oh", "A, B, C", "But who?").
3. Set `"ready": true` for the language in `content/languages.json` (Johnny wants it listed as soon as it's recorded).
4. Run `python3 tools/build.py`, then commit and push. Preview any language with `?lang=<code>&preview=1`.

## Tools (all in `tools/`, run from the repo root)

- `build.py`: makes the web pictures, writes the per-language pages and stamps a new version so phones fetch new files. Run it after every change. `--check` prints a table of what each language still needs.
- `script.py <code>`: writes the plain narration script. The v3 tagged scripts are hand-tagged. With the tags removed they must say exactly the book's words.
- `split.py <code> file.mp3`: cuts a one-take recording into pages. ElevenLabs v3 makes the [long pause] only 1–2 s long, so the cuts are guided by each page's text length.
- `cues.py <code>`: times the captions. It chooses the sentence breaks that keep the speaking pace even. This matches every hand-checked English cue within 0.2 s.
- `pauses.py <code>`: holds the silences a page asks for (`"pauses"` in `story.json`). The fruit page needs at least 1.6 s before "Uh-oh". `split.py` runs this automatically.
- `clips.py`, `video.py`, `narrate.py`, `sheet.py`, `align.py`: see README.md.
- `content/story.json`: page order, art, clips and music. Clip start = that sentence's cue + `offset`.
  The fruit clip is anchored to "Uh-oh" (sentence 2, offset −7.89), so its lightning follows each language's pace.

## Working in this environment

- Clone with git: `git clone https://github.com/jcubitwall/the-way-back-home-v2`. The site itself
  (github.io) is blocked from the shell, so to look at clips use the files in `scenes/`. ffmpeg is installed.
  To see what a clip shows, make a contact sheet with ffmpeg (`fps=1,tile=…`) and view the image.
- To push, the repo must be attached to the session with push access. Before pushing, run
  `git fetch origin main && git rebase origin/main`.
- Commit messages end with the Co-Authored-By / Claude-Session lines the session provides.

## Open items

- **Page 7 (law, page id `test`): DONE 14 Oct 2026.** New 14 s clip: the ivy-wall tablets show the short Ten Commandments in real Hebrew (checked letter by letter); the lower stone is a mirror; the kids keep their backs to the camera and only their reflected faces change from happy to shocked; the stone cracks loudly.
  - Two clips cut from one Grok take, sharing a frame at the join. Clip 1 (0–7.1 s) plays as the narration starts and freezes just before the crack. Clip 2 (from the crack on) is anchored to the last sentence ("Like Adam and Eve…", offset −1.30 s), and `pauses` holds at least 1.4 s before it. So in every language the crack lands in silence right after "only two of the ten", and the narrator then says "we have all broken God's law".
  - The crack sound was made louder on purpose (peak −1 dB, about 7 dB louder than the other scene sounds), and the music hushes at the crack, then rises again before the page turns.
  - Grok tip: never write "turn around" in a prompt. Describe the backs as fixed, put every emotion on the reflections, and put turning words only in the negative prompt.
- **Page 2 (rule): new clip 15 Oct 2026.** Adam and Eve from behind by the tree; Adam raises his arm and points at it, then lowers it. Replaced 15 Oct with a cleaner take, trimmed to 10.5 s (ends with his arm at rest). Anchored to "Adam pointed to the tree…" (sentence 2, offset −2.6 s), so his finger reaches the tree on those words in every language. Silent clip.
- **Page 6 (road): new clip 14 Oct 2026.** Same story, from Adam and Eve to a growing crowd, but it ends with the three kids walking up the road toward the law stones, which leads into page 7. It is anchored to "Look at all these people!" (sentence 1, offset −6.6 s), so the busy road appears on those words in every language; in English the kids appear about 0.4 s before "we have all sinned".
- **Page 8 (locked): replaced 15 Oct 2026 with Johnny's second take.** The take runs: shocked reflections, then heaven appears in the mirror, then a boom (3.6 s) as golden bars slam shut, then it darkens (7.25 s) and fire rises (8 s). The text is unchanged.
  - Two clips cut at 7.0 s. Clip 1 is anchored to "Sin locks us out…" (sentence 1, offset −4.69 s), and `pauses` holds ≥1.4 s before sentence 1, so the boom lands in silence right before those words. It then freezes on the bars.
  - Clip 2 is anchored to "The Bible says that if we die…" (sentence 3, offset +2.5 s), so the fire is full around "punished in a place called hell".
  - The earlier pause before sentence 3 was removed: the en/de recordings were restored from git and re-paused.
  - Sound: the opening ring sits at 12%; the boom is at full volume (−1 dB peak) and drops to 12% when the narrator resumes; clip 2's rumble is −12 dB.
  - Still in this take: two Hebrew words warp briefly around 4–7 s, and red spots flicker around 3.75–4.5 s.
- **Music between pages (fixed 15 Oct 2026).** In app.js:
  - When the next page has a different piece, the crossfade (3.5 s) starts while the current page holds and slides away, instead of at the next page's first word.
  - When a page outlasts its piece (long or slow languages; German prayer + grown-ups already do), a fresh copy fades in 5 s before the end instead of jumping back to the loud start.
  - Tested in a browser: tomb → gates handover, and the German prayer pages running past 85 s.
  - Page 7 → 8 (changed again 15 Oct 2026; Johnny disliked a silent turn): the music hushes at the crack (`hush`), then swells back from 4 s into clip 2 (`rise`, over `riseFor` s, default 4) under "we have all broken God's law", and m07 crossfades into m08 across the turn like every other page. A page still hushed when its narration ends swells back anyway.
- **Scenes that didn't start (fixed 15 Oct 2026).** Page 7's first scene sometimes stayed a still picture; replaying fixed it. Cause: iPhones ignore preload, so a clip only began downloading when it had to play, and if it took more than 2.5 s the page gave up on *all* its scenes. Now each next page's clips are downloaded whole in advance (fetch → blob) and played from memory; while reading aloud a clip may take 7 s to start; and a slow clip only skips itself (only a broken file skips the page's later scenes).
- **Loading sweep (15 Oct 2026).** Johnny is happy with the pictures and music, so nothing was re-compressed (the clips are already at CRF 28 and re-encoding only grew them or lost quality; the music has no lossless originals). Changes:
  - A scene that must play while its download is under half done stops the download and streams instead, so no clip is fetched twice.
  - On phones, pages with a scene use the 720-wide picture, the same width as the clip that replaces it (tablets still get 942).
  - The browser-tab icon is a 7 KB 48 px file instead of the 75 KB app icon.
  - The service worker now keeps downloaded clips, so a second read is instant and works offline.
  - Measured: the cover opens on about 0.35 MB (picture, fonts, code); a full read is about 26 MB, of which the clips are 23 MB.
- **Sharp hold frame (15 Oct 2026).** Johnny saw page 4 (fruit) settle on a soft last frame. Cause: the clips are compressed (CRF 28), which costs about 25–30% of the fine detail; the frozen last video frame showed it. Now every clip's last frame is also kept as a sharp still (`art/<end>-720.webp`, made by build.py from `art/src/<end>.jpg`, which clips.py takes from the original upload), and app.js lays it over the video the moment the clip ends (hidden again when the next clip on the page starts, or the page resets). Checked: every end still is exactly the video's last frame, so there is no jump. Costs about 150 KB per clip page.
- **Pages 5, 6 and 7, check the music by ear.** Page 6's track may be too bright for "our sin keeps us far from God"; page 7 could use more tension; page 5's opening could be sadder.
- **Scene timing in other languages.** Clip offsets were tuned to the English. Spot-check pages 6–8 in each new language.
- **"Message us" email** (hello@thewaybackhome.net, Cloudflare routing): a test sent from iCloud bounced. A test from a non-iCloud account is still pending. An in-book form is an option.
- **Buttons over long pages (fixed 16 Oct 2026).** On small phones the button stack covered the first lines of the prayer and grown-ups pages (de fr ko ur pa, and ja on every phone once furigana was added). fitAll() in app.js now keeps those pages' text below ~236 px from the top, shrinking it a little more where needed. Checked 16 languages at 390×844, 375×667 and 360×640: no overlap.
- **Smaller items:**
  - Page numbers don't match.
  - Check the bottom edge on an iPhone.
  - Rebuild the downloadable videos once languages are recorded (`video.py`).
- **Decided:** the cover, prayer and grown-ups pages keep still pictures (no clips).

## Cover layout (15 Oct 2026)

- Everything is in thumb reach at the bottom right: the ⋯ menu beside the subtitle (it opens upward), then Listen, Read and the language (globe icon + name, opens languages.html) stacked, all three in the same glassy outline style Johnny chose (`.cta.alt`). Languages is no longer in the ⋯ menu. These are part of the cover page itself (app.js moves the menu into `.mslot` on the cover and back to the top bar on story pages), so they can never overlap on phones whose bottom edge differs. The top bar shows only the pause button while the cover is read aloud.
- Bottom left is a QR code for the same language's link (`<site>/<code>/`, plus `?preview=1` for a language not yet listed). Tapping it shows it large for a friend to scan. It is drawn on the phone from `qr.js` (qrcode-generator 1.4.4, MIT), so it is right on the test site and on the real domain.
- When reading or listening starts, the cover buttons and QR fade away as before.
- Story pages (15 Oct 2026, Johnny's choice after trying a mid-screen column and a bottom row): menu, sound and home stacked on the right edge, home lowest, floating just above where the page's text starts. `placeBar()` in app.js sets `--bb` from the text's position on each page (also in listening mode, where the caption is lower), so the buttons never cover a word and the text keeps its full width. The menu opens to their left; the page count stays at top left.

## Future idea (decided 13 Oct 2026: keep the current timing for now)

**Full-page clips with per-language time-stretch.** Rebuild later, not now.

- **Idea:** each clip is about as long as its English page (15–25 s, two or three Grok pieces joined) and starts the instant the page opens.
- **Anchors:** each clip gets 1–3 anchor points, for example "clip 6.4 s = start of 'Uh-oh'". The player sets `playbackRate` per section from each language's cues, so key moments land on their words.
- **Speed limits:** keep each section within about ±15–25% of normal speed, and hold a frame rather than crawl. German runs 2–35% longer than English per page.
- **Why it waits:** the current clips are 6–14 s against 13–25 s pages, so they can't simply be stretched.
