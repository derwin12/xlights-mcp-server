---
name: song-to-package
description: Turn a YouTube song link into a singing-faces xLights sequence in F:\ShowFolderAI and a .xsqz package ready to sell - Whisper words checked against lrclib.net lyrics, word timing from NUSAutoLyrixAlign (karaokeer Docker container), Faces on the 4 singing props. Use when the user gives a YouTube link to sequence/package for sale or for xlightsseq.com, asks to re-run lyrics/alignment for such a song, or asks about the Vimeo / Google Drive / xlightsseq.com upload steps.
---

# YouTube link -> singing faces sequence -> .xsqz (-> Vimeo, Drive, xlightsseq.com)

One command from the repo root:
```
python scripts/song_to_package.py "https://www.youtube.com/watch?v=..." [--name "Artist - Title"] [--track T] [--artist A] [--faces-only] [--with-media] [--cues cues.json] [--lrclib-id N] [--redo words|fix|xsq|package]
```
About 2.5 min for a 2-4 min song. Writes into `F:\ShowFolderAI` (the user's chosen layout):
- `<name>.mp3`, `<name>.xsq` - 4 lyric timing tracks + one Faces effect per singing prop (Singing Tree Male/Female,
  Singing bulb Red (Left)/Green (Right)); the trees split phrases by pitch, both bulbs sing everything.
- `SongWork\<name>\words.json` (Whisper), `fixed.json` (corrected + aligned), `song16k.wav`.
- `packages\<name>.xsqz` - rgbeffects, networks, the .xsq; **no audio** unless `--with-media` (for sale, buyers supply the song).
Each step is skipped when its output exists; `--redo STEP` re-runs from that step on (e.g. `--redo fix` after changing lyrics).
The Eclipse6 house effects are on by default (enhance_layout.py, see the eclipse-song-pipeline skill: moving heads, Radio_EFL,
Mega Tree/matrix shaders, Lyrics Matrix words, Trees/Stars/Arches/Outline...). The user wants this for every song ("the basic
sequencing we did with the Eclipse videos"); `--faces-only` leaves just the singing props. The radio shows the real artist.
For validating in xLights the user imports the .xsqz, so it needs the audio: use `--with-media` for review builds.

## Pipeline
`fetch_video.py` -> `transcribe_words.py` (Whisper small.en) -> `lyrics_align.py` -> `song_to_singing_props.py` -> `package_xsqz.py --no-media`

**Name / lrclib lookup** (`guess` in song_to_package.py): YouTube music tags first, else the video title with (...)/[...], quotes,
"by <channel>" and credit parts (Official/Lyric/Animation/Video) removed; the channel name or an lrclib hit decides which side of
"A - B" is the artist. Check the printed `lrclib track=... artist=...` line; override with `--track/--artist/--name` when wrong.

**lyrics_align.py - why it is built this way (tested on Eclipse6 This Christmas):**
- lrclib lyrics of the *original* recording differ from covers/remixes (repeats, ad-libs, cut verses). Feeding lrclib's text
  straight to the forced aligner drifted words by up to 100 s. So Whisper decides *what was sung and in what order*; lrclib
  fixes words only inside phrases that clearly match a lyric line (similarity >= 0.5 and >= 3 shared words): each differing
  stretch of up to 4 words takes lrclib's words (HIM REAL->AMARILLO, OUT OF THE MORNING->AS A WARNIN, A->FROM). Stretches only
  one side has are never added or dropped. Letter similarity is useless for mishearings (HIM REAL/AMARILLO share nothing) -
  the matching rest of the phrase is the signal. Replacing whole phrases with lrclib lines overwrote real cover lines; a
  one-for-one look-alike rule missed AMARILLO (user caught it at 1:08 of Choosin Texas). Regression check: This Christmas
  (cover) must still get only CAROLING and VERY.
- Rule details (2026-10-25, after the user caught "I wasn't a match FOR THAT KIND OF SPARK" heard as "BUT BACK ON FORK"):
  a phrase takes fixes when similarity >= 0.5 with >= 3 shared words, OR >= 0.4 with >= 4 shared words; a differing stretch
  is replaced when it is <= 5 words and the word counts differ by <= 2 (stops WE'LL -> HOW MUCH FUN IT'S GONNA BE).
- Long Whisper phrases (> 7 s, >= 8 words) are split at the widest gap between words (>= 3 words a side) before matching.
- **Transcription** (`transcribe_words.py --separate`, used by the pipeline): Spleeter vocals in the karaokeer container, then
  three Whisper passes merged - vocals at temperature 0 (fullest but loops "ba-ba-ba" over whole verses), vocals with
  temperature retries (no loops, skips passages), the full mix - base = most words after removing looped phrases, gaps filled
  from the others; phrases over a silent vocal stem (< 0.05 of its 90th pct) are dropped. Any single setting lost a verse,
  the chant or the ending of This Christmas; a fixed ctranslate2 seed did not make retries repeatable; Silero VAD cut singing.
  The 16 kHz wav kept in SongWork is the vocal stem (better for the male/female pitch split).
- **Uploader lyrics first**: the video's manual English captions (`fetch_video.captions`, never auto-captions), else lyrics
  pasted in its description (`description_lyrics`), are saved as SongWork\<name>\lyrics.txt and used instead of lrclib
  (`--lyrics-file`; `--lyrics` to pass your own). Eclipse 6 uploads manual captions = their parody lyrics: Mean Grinch went
  from no lyric source to 0.79 similarity and 29 real fixes (CRINGIFICATION->GRINCHIFICATION, Mount CRUMPIT). For an mp3 on
  disk pass `--source-url` (Mean Grinch: https://www.youtube.com/watch?v=eu0PrA10i1I).
- **Missed lines** (`fill_gaps`, needs `--vocals` = the stem): a gap where the vocal stem shows >= 1.5 s of singing gets the
  lyric lines between its neighbours' matched lines (max 2, 0.35-1.2 s per word), then the aligner times them. Whisper
  missed This Christmas's opening HANG ALL THE MISTLETOE (sung from 6.5 s). Line matching follows song order (a near-equal
  line at/after the position reached wins, so repeated choruses map forward); the words are still fixed from the best line.
- **Aligner = timing only**: words missing from NUSAutoLyrixAlign's ~207k-word dictionary come back labelled `BREATH*`
  (This Christmas "BOOYAH" at 1:05; 19 in Mean Grinch: Whoville, Grinchification...). `rebuild` keeps our own word as the
  label and takes only the start/end from the aligner (one output row per input word, checked by count).
- **Onset snap** (`snap_onsets`): word starts move to the nearest voice onset in the stem within 0.12 s.
- lrclib candidates are searched by track (artist only if `--artist` is given) and the one closest to Whisper's text wins;
  covers are listed under the original artist. Similarity ~0.45 is normal for a full song; below 0.35 lrclib is ignored.
- lrclib's free-text `q=` search often returns 503 ServerOverloaded; use track_name/artist_name (retries built in).
  Records also carry `hasWordSync` / `lyricsfile` (word-level sync) - not used yet.
- Alignment: `docker exec -w /NUSAutoLyrixAlign karaokeer ./RunAlignment.sh <wav> <lyrics.txt> <out>` -> `start end WORD` lines,
  one per input word (~80 s per 4 min). From Git Bash set `MSYS_NO_PATHCONV=1` or the container paths get rewritten.
  The container's own web service (YouTube/Genius) is stale - only the aligner inside it is used. The script starts the container.
- A phrase whose aligned words land >1.5 s outside Whisper's phrase window keeps Whisper's timing.
- Dropped-g spellings (NOTHIN, DRINKIN') fall back to the -ING pronunciation for phonemes.

**Sections track** (`song_sections.py`, step `sections`, after enhance_layout so it is not overwritten): a timing track
"Sections" (first timing row) with Verse 1 / Chorus 1 / Bridge / Intro / Instrumental / Ending.
- Labels come from the Genius page's `[Verse 1]`/`[Chorus]` headers. Genius has **no lyrics API** (api.genius.com is metadata
  only) and gives scripted requests 403, so headless Chromium (Python Playwright, installed) reads `[data-lyrics-container]`.
  URL guessed as genius.com/<Artist-title>-lyrics; `--genius-url` when wrong. Text is cached in SongWork\<name>\genius.txt.
  If the page is missing, the step is skipped with a message and the sequence is still fine.
- Phrases walk the sections in order (may skip ahead - the Choosin Texas remix drops the Bridge); a phrase matching the
  current section's *next* line stays in it even when sung differently (remix chorus ending "cause she's from Texas" had
  restarted the chorus 4 s early). Silent gaps >= 5 s become Intro / Instrumental / Ending.
- Covers that rearrange the song (Eclipse6 This Christmas) map roughly (post-chorus/verse 3 merged into a long chorus).
- enhance_layout still uses its own audio-detected sections for effects; feeding it these labels is a possible next step.

**Lyric pictures** (`lyric_images.py`, runs with the sections step; `--no-images` skips): sung words listed in
`scripts/lyric_icons.json` (word/phrase -> emoji; edit it to add words) become Noto Emoji pictures (Apache 2.0, pinned
v2.047 via jsdelivr, cached in ~/.cache/xlights-mcp/noto) on Mega Tree (20x38 picture on the 20x75 tree), Matrix (56x56 of
120x60) and Matrix 2 (28x28 of 40x30). Each lands on its word, holds 2.4 s, never overlaps; 0.4 s `vector` entrance
(grow / slide-left / slide-right / rise / drop, fixed per emoji so choruses repeat) then a static hold with 0.3 s fade.
One new TOP layer per model with Transparent Black on (level 30), so the shader/tint keeps running around the picture.
User decision: pictures lie ON TOP of the background effects - no Off/blackout under them (tried first, removed).
Verified in xLights source (PicturesEffect.cpp): Start/End Scale only apply with Scaling "No Scaling", so PNGs are made at the
on-model size; a missing picture renders solid RED - package_xsqz.py packs the referenced Images/LyricIcons files at the same
show-relative path. Re-running replaces its own layers. Choosin Texas: 26 pictures (love, Texas star, two-steppin', smile,
crystal ball, cowboy, drinkin', mountain, tunes, sing, morning).

**House preview** (step `preview`, before package): `render_preview` in song_to_package.py drives the running xLights over
automation (port 49914 here, `--port`): closeSequence (never forced - unsaved work makes it skip), loadSequence, renderAll,
exportVideoPreview at 1920x1058 to `F:\ShowFolderAI\HousePreviewVideos\<name>.mp4`, ffprobe check, one retry on a short or
truncated file. The user must have xLights on the F:\ShowFolderAI show folder with the normal house preview selected (not MH
Preview); if xLights is not reachable the step is skipped and `--redo preview` renders it later. Two xLights instances can be
open (e.g. one on an imported .xsqz's temp folder) - only the one with automation on the port is used; check which one that is
before rendering, and don't render into the user's validation session.

## Checks before handing over
- Read the correction report: every swap should be a real mishearing.
- The .xsq: sequenceDuration = song length, 4 Faces effects, 4 lyric tracks. The user likes to open one in xLights to check
  mouth timing before trusting a batch.
- Voice split is a pitch heuristic; for a solo singer both trees still sing alternate phrases. Use `--cues` to force voices.

## Upload steps (not built yet - status 2026-10-25)
Credentials live in the repo's git-ignored `.env`.
- **Vimeo**: `VIMEO_TOKEN` is valid (account Daryl Erwin, free plan) but has no `upload` scope; the user requested upload access
  for the app (Vimeo reviews by hand, days). When approved: generate a new token with Upload ticked, verify with
  `GET https://api.vimeo.com/oauth/verify` (scope list must include upload). The preview video to upload is a render
  (render_clip, see eclipse-song-pipeline step 5), not the YouTube download.
- **Google Drive**: rclone is installed (winget); the user still has to run `rclone config create gdrive drive scope=drive`
  and name the folder (`GDRIVE_REMOTE`, `GDRIVE_FOLDER` in .env). Then `rclone copy <xsqz> "gdrive:<folder>"` and
  `rclone link` for the share link.
- **xlightsseq.com**: XenForo Resource Manager; the user is NOT an admin, so no API key. Plan: Playwright with a saved logged-in
  session fills the add-resource form (paid category, title, description, Vimeo embed, Drive link) and stops before Submit for the
  user to review. The form's fields have not been inspected yet (needs the user logged in).
