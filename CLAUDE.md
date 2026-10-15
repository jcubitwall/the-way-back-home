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
- **Public site:** thewaybackhome.net still serves the OLD version from `jcubitwall/the-way-back-home`.
  Switch the domain only when every language is finished (see "Going live" in README.md).
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

## Status (13 Oct 2026)

| | |
|---|---|
| English | Finished and public: 18 pages, v3 narration, 15 clips, 14 music tracks |
| German (de) | Finished and public: text, ElevenLabs v3 recording, captions timed |
| zh hi es fr ar bn pt ru ur he sw pa ko ja ki | Text and v3 narration scripts written; **waiting for Johnny's ElevenLabs recordings** |
| Plautdietsch (pdt) | Text written; plain script for his human narrator (no v3 tags) |

- The narration scripts, with a Copy button per language, are on the artifact page
  "Way Back Home Narration Scripts" (https://claude.ai/artifact/M8PZotoUtoTfAYmjkoUGbx). The same files
  are in `scripts/The-Way-Back-Home_<CODE>_narration_v3.txt`. If you change a language's text, rebuild that
  script and republish the page.
- **Translation choices:**
  - Prayer page: A-B-C only in German (Anerkennen, Bekennen, Christus folgen). Every other language uses steps 1-2-3.
  - Hebrew uses ישוע (Yeshua).
  - The Hindi, Punjabi and Urdu titles avoid "ghar wapsi" (the name of a political reconversion campaign) and say "the way to return home" instead.
- **Need a native speaker's read before recording:** Kikuyu and Plautdietsch are careful drafts. Urdu,
  Punjabi and Swahili would also benefit from one. Record one Kikuyu page as a test first, because
  ElevenLabs may not pronounce Kikuyu well.
- **Music:** 14 tracks, `music/cue_m01..m14.mp3`. m14 "Welcome Home" plays across gates and new-earth.
  Prayer and grown-ups use m12b. Tracks are level-matched to about −21.5 LUFS.

## When a recording comes back (the usual job)

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
  - The crack sound was made louder on purpose (peak −1 dB, about 7 dB louder than the other scene sounds), and the music hushes from the crack onward.
  - Grok tip: never write "turn around" in a prompt. Describe the backs as fixed, put every emotion on the reflections, and put turning words only in the negative prompt.
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
  - After a page whose scene hushed the music (page 7, from the crack onward), there is no swell and no early handover: the silence carries across the turn, and the next piece fades in over 9 s (FROM_HUSH) under the narration. Johnny wanted the 7 → 8 change less abrupt and the hush kept.
- **Pages 5, 6 and 7, check the music by ear.** Page 6's track may be too bright for "our sin keeps us far from God"; page 7 could use more tension; page 5's opening could be sadder.
- **Scene timing in other languages.** Clip offsets were tuned to the English. Spot-check pages 6–8 in each new language.
- **"Message us" email** (hello@thewaybackhome.net, Cloudflare routing): a test sent from iCloud bounced. A test from a non-iCloud account is still pending. An in-book form is an option.
- **Smaller items:**
  - Page numbers don't match.
  - Check the bottom edge on an iPhone.
  - Rebuild the downloadable videos once languages are recorded (`video.py`).
- **Decided:** the cover, prayer and grown-ups pages keep still pictures (no clips).

## Future idea (decided 13 Oct 2026: keep the current timing for now)

**Full-page clips with per-language time-stretch.** Rebuild later, not now.

- **Idea:** each clip is about as long as its English page (15–25 s, two or three Grok pieces joined) and starts the instant the page opens.
- **Anchors:** each clip gets 1–3 anchor points, for example "clip 6.4 s = start of 'Uh-oh'". The player sets `playbackRate` per section from each language's cues, so key moments land on their words.
- **Speed limits:** keep each section within about ±15–25% of normal speed, and hold a frame rather than crawl. German runs 2–35% longer than English per page.
- **Why it waits:** the current clips are 6–14 s against 13–25 s pages, so they can't simply be stretched.
