# The Way Back Home (version 2)

A true Bible story for children, read and listened to full screen on a phone. Each picture fills the
screen; the bottom of the page softens into a blur in the chapter's colour, and the words sit on it.
While the narrator reads, the words appear one sentence at a time.

This repository is the new version, live for testing at
https://jcubitwall.github.io/the-way-back-home-v2/ . The public site (thewaybackhome.net) still runs the
old version from the `the-way-back-home` repository until this one is finished in every language.

## Where things are

| What | Where |
| --- | --- |
| Page order, which picture goes on which page, chapter colours, music | `content/story.json` |
| The words, in each language | `content/i18n/<code>.json` (`en.json`, `es.json`, …) |
| Which languages are public | `content/languages.json` (`"ready": true`) |
| Pictures (originals) | `art/src/<name>.jpg` |
| Narration | `audio/<code>/<page id>.mp3` |
| Animated scenes (optional) | `scenes/` and the `clips` list on a page in `story.json` |
| Music | `music/cue_c1.mp3` … `cue_c8.mp3` |
| Downloadable videos | `video/The-Way-Back-Home_<CODE>.mp4` |
| Reader | `index.html`, `app.js`, `app.css` |
| Language list page | `languages.html` |

## Everyday tasks

All tools run from the repository folder with Python 3 (and `ffmpeg` for sound and video).

**Change the words.** Edit `content/i18n/en.json`. Each story page is a list of paragraphs, and each
paragraph is a list of sentences; every sentence becomes one caption. Then run
`python3 tools/build.py`.

**Swap or reorder pictures.** Put the picture in `art/src/` as a `.jpg` and set `"art"` on the page in
`content/story.json` (moving a line moves the page). Run `python3 tools/build.py`.

**Translate.** `python3 tools/sheet.py export es` writes `sheets/es.csv` with English beside an empty
column for Spanish. Fill it in (or have a reviewer check it), then `python3 tools/sheet.py import es`.
When the English changes later, export again and changed rows are marked for checking.

**Record narration (ElevenLabs).** Put a voice ID for the language in `tools/voices.json`, then:

```
export ELEVENLABS_API_KEY=...
python3 tools/narrate.py es
```

Each page is read in one take, and ElevenLabs reports when every word is spoken, so the captions
are timed exactly.

**Narration recorded by a person** (for example Plautdietsch). Save each page as
`audio/pdt/<page id>.mp3` (page ids are in `story.json`), pausing briefly between sentences, then
`python3 tools/cues.py pdt` finds the sentence breaks.

**Add an animated scene.** `python3 tools/clips.py fruit fruit.mp4 --sentence 1 --offset 0.6 --sound`
shrinks the clip for phones, makes its first frame the page's picture and its last frame the blur under
the text, and wires it to the page. With narration on, it starts when that sentence is spoken
(counting from 0), and the page turns only after the narration is finished and the clip has frozen on
its last frame. Without narration it plays silently half a second after the page arrives. `--sound`
keeps the clip's sound effects (heard only with narration on); leave it off for a silent clip.
`--add` puts a second clip on the same page; `python3 tools/clips.py fruit --remove` goes back to the
still picture. Then run `python3 tools/build.py`. On a slow connection or with data saver on, readers
simply see the still pictures.

**Make the downloadable video.** `python3 tools/video.py es` photographs every page and caption from
the real reader and joins them with the narration and music (1080×1920). It takes a few minutes per
language.

**Check what's missing.** `python3 tools/build.py --check` prints a table of text, recordings, caption
timings and videos for every language.

**Make a language public.** When its text, narration and video are done, set `"ready": true` for it in
`content/languages.json`. Only ready languages appear in the list. You can preview any language
before then at `…/?lang=es&preview=1`.

## Useful links while working

- `?demo=1`: shows the read-aloud button even without a recording, and plays the captions
  silently at reading pace with the music, to judge the timing and the look.
- `?p=7`: opens at page 7.
- `languages.html?preview=1`: lists every language, marking the unfinished ones as drafts.

## Going live

When every language is done:

1. Set `"ready": true` on the finished languages in `content/languages.json` and run `python3 tools/build.py`.
2. In the old repository (`the-way-back-home`) → Settings → Pages, remove the custom domain `thewaybackhome.net`.
3. In this repository → Settings → Pages, enter `thewaybackhome.net` as the custom domain and tick "Enforce HTTPS"
   (GitHub adds a `CNAME` file). Cloudflare needs no change: the domain already points at GitHub Pages.

Old links like `thewaybackhome.net/es/p7` keep working.
