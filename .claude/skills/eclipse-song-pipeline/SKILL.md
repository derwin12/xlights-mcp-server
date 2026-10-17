---
name: eclipse-song-pipeline
description: Turn a YouTube song video into a finished Eclipse6-style xLights sequence in F:\ShowFolderAI - singing-prop lyric tracks and Faces, beat/section layout effects on the house props, and a house preview video. Use when asked to sequence a new song/video for the AI show folder, re-run or re-tune the layout effects on an existing Eclipse6 song, change the colour story, or render the house preview videos.
---

# YouTube song -> Eclipse6 sequence

Show folder: `F:\ShowFolderAI`. Every song ends up as `Eclipse6-<Name>.xsq` + `.mp3` there. The plan, recipe, colour
story and per-song status live in the Claude doc "Eclipse6 Sequence Enhancement Plan"; update its status table when a
song moves along.

```
fetch_video.py -> transcribe_words.py -> song_to_singing_props.py -> enhance_layout.py -> render_clip
 (mp3)             (words.json)           (Faces + lyric tracks)     (house layout fx)     (preview mp4)
```

Run everything from the repo root with `PYTHONPATH=src`.

## 1. Audio
`python scripts/fetch_video.py URL --audio --out-dir <dir>` (needs current yt-dlp and Node on PATH; a 403 means one is
stale). Copy the mp3 to `F:\ShowFolderAI\Eclipse6-<Name>.mp3`.

## 2. Words
`python scripts/transcribe_words.py <mp3> words.json --wav16k <tmp.wav>` (Whisper word timestamps).

## 3. Singing props (base sequence)
`python scripts/song_to_singing_props.py --audio <mp3> --wav16k <tmp.wav> --words words.json --show F:\ShowFolderAI --out F:\ShowFolderAI\Eclipse6-<Name>.xsq --title "<Name>" [--cues cues.json]`
Do NOT pass `--layout-effects`: that older option writes effects without palettes. Step 4 replaces it.
Result: 4 lyric tracks (Tree Male/Female, Red/Green bulb, voices split by pitch) and one full-length Faces effect each.

## 4. Layout effects
`python scripts/enhance_layout.py F:\ShowFolderAI\Eclipse6-<Name>.xsq [--palettes story.json]`
- Makes `Eclipse6-<Name>.xsq.bak` once. To re-run (new colours, script change) copy the `.bak` over the `.xsq` first.
- Adds, from detected bars/sections (bars/beats are the bar split in 4; "chorus" = detected chorus sections):
  - House Outline: Single Strand chase every bar, direction alternating.
  - Trees: VU Meter per section (split at 16 bars) on the lower layer; in chorus bars a Shockwave on beats 1 and 3 above it.
  - Trees Stars (TreeStar 1-4): Shockwave on beats 2 and 4 in choruses (ping-pong with the Trees), a Ripple per bar
    outside choruses, a Pinwheel under each chorus run, and a full-size Shockwave on the first beat of each section.
  - Mega Tree: a shader per Trees block (rotated per section story from the user's own favourites: verses Continua
    Variation / Fly Through / Aurora; chorus A Vortex V2 / Hex Vortex; chorus B Spiral Over Beams / Blue Streaks /
    Audio - PlasmaLike; the loudest choruses Black Cherry Cosmos / InnerDimensionalMatrix; outro Aurora / Continua)
    with the settings copied from his own sequences, under a one-colour On layer (Average blend) in the Trees' colour.
    The tree changes colour/shader ONLY when the Trees VU block changes (per-bar/beat switching was far too busy).
  - Arches: chase every other bar, Ripple on top at section changes. Stars: Shockwave on chorus downbeats, Per Model
    Default buffer (each star fires on its own); Mega Topper: same Shockwave, single model.
  - Icicles: On wash per 2 bars. FloodLights: On wash per section.
  - Music Sparkles ("Sparkles reflect music") on, frequency 0, in a contrasting colour per section, on everything except the
    FloodLights and the Mega Tree tint layer. Moving heads untouched. Unused rows hidden. Length stretched to the audio.
- Default colour story = the pilot's (amber verses, red/gold and green choruses, white/gold peak, red/white outro).
  Per song, pass `--palettes story.json`, e.g. `{"chorusA": {"trees": ["#2060FF", "#A0D0FF"]}, "sparkle": {"chorusA": "#FFD700"}}`
  (roles: outline, trees, arches, stars, topper, icicles, flood, megatree - 3 colours; sparkle keys are the section names
  verse, chorusA, chorusB, peak, outro).
- Do not run it on `Eclipse6-Deck-the-Halls-layout.xsq` (older, has its own outline/VU).

## 5. Render the house preview video
1. xLights must be running, idle, with the ShowFolderAI folder open and the house preview selected.
2. Find the automation port: it was **49914**, not the default 49913. `xlights_status(port=...)` /
   `Get-NetTCPConnection -State Listen` on the xLights process. Pass `port` to every live tool.
3. `switch_show("ShowFolderAI")`, then `render_clip(sequence_name="Eclipse6-<Name>", start_ms=0, end_ms=<duration_ms>, output_path="F:\\ShowFolderAI\\HousePreviewVideos\\Eclipse6-<Name>.mp4", port=...)`.
   Full-song renders take 2-10 minutes (one 8-minute medley took 30) and move to the background; xLights exports one
   at a time, so render sequentially. The MCP tool aborts after 30 minutes of silence and reports "failed" even if the
   export finished: check the mp4 with ffprobe before re-running. Re-render after any change to the .xsq (videos go stale).
4. Check with ffprobe (duration = sequence length, audio present) and a cropped frame before telling the user.
   After changing the script, regenerate every song from its `.bak` first:
   `for bk in F:/ShowFolderAI/Eclipse6-*.xsq.bak; do cp "$bk" "${bk%.bak}"; PYTHONPATH=src python scripts/enhance_layout.py "${bk%.bak}"; done`
   (skip dropped songs), then render.

## 6. Hand-off
Tell the user which song is ready to verify in xLights. Update the status row in the doc (Pilot / Applied / Done: Done
only after the user has reviewed the render). Commit script changes only; the show folder is outside the repo.

## State of the show folder (Oct 2026)
18 songs enhanced and rendered; `Please-Dont-Cancel-Christmas` was dropped by the user (left untouched, not rendered);
`Deck-the-Halls-layout` is the older file and is skipped. All use the default colour story; none reviewed by the user yet.
Videos: `F:\ShowFolderAI\HousePreviewVideos\`. Plan doc: Claude doc "Eclipse6 Sequence Enhancement Plan".

## Lessons and user preferences
- The user wants effects to follow the music's structure and prefers you to keep going without waiting between steps; confirm only real design choices.
- A "peak" cut-off of energy 0.9 marks most choruses on some songs; use relative thresholds for variety (the shader peak is 97% of the loudest chorus).
- Mega Tree look = user's own technique: a palette-aware or fixed-colour shader under an Average-blend single-colour On tint.
- Sparkles: enable "reflect music" only, never set a frequency; exclude the floods.
- Layer order: first EffectLayer in the xsq is the top layer. Palettes are written as `ColorPalettes` entries referenced by a 0-based `palette=` index; effects without it render in the default colour.
- Automatic tempo/section detection is unverified; if a song's bars look half/double speed, say so and check.
