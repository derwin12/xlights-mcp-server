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
- Adds, from detected bars/sections: House Outline chase per bar; Trees VU meter per section (max 16 bars); Mega Tree
  shader (rotated per section from the user's own favourites: Continua/Fly Through/Aurora in verses, Vortex V2/Hex Vortex and Spiral Over Beams/Blue Streaks/PlasmaLike in choruses, Black Cherry Cosmos/InnerDimensionalMatrix at the loudest; settings copied from his sequences) with an Average-blend one-colour On tint, both changing only on the Trees' blocks; Arches chase +
  Ripple at section changes; Stars/Mega Topper Shockwave on chorus downbeats (Stars use Per Model Default buffer); Trees (beats 1,3) and Trees Stars (beats 2,4) Shockwave ping-pong in chorus bars, with the Trees VU meter on the layer below; Trees Stars also get a Ripple per bar outside choruses, a Pinwheel under each chorus run and a full-size Shockwave at each section start; Icicles wash per 2 bars; FloodLights
  wash per section. Music Sparkles (contrasting colour, frequency 0) on everything except the FloodLights and the tint
  layer. Moving heads untouched. Unused rows hidden. Sequence length stretched to the audio.
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
   Full-song renders take several minutes and move to the background; xLights exports one at a time, so render
   sequentially. Re-render after any change to the .xsq (videos go stale).
4. Check with ffprobe (duration = sequence length, audio present) and a cropped frame before telling the user.

## 6. Hand-off
Tell the user which song is ready to verify in xLights. Update the status row in the doc (Pilot / Applied / Done: Done
only after the user has reviewed the render). Commit script changes only; the show folder is outside the repo.

## Lessons from the pilot
- Colour changes should track the section/phrase structure, not every bar or beat; per-bar tint on the Mega Tree was too busy.
- Layer order: first EffectLayer in the xsq is the top layer. Palettes are written as `ColorPalettes` entries referenced by a 0-based `palette=` index; effects without it render in the default colour.
- Automatic tempo/section detection is unverified; if a song's bars look half/double speed, say so and check.
