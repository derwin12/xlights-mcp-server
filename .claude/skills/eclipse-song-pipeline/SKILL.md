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
  - Pixel Forest (group of Pixel Forest 1-5, 10x5 matrices): exactly the Trees effects (`TREE_LIKE`), same palettes (user, 2026-10-25).
  - Trees Stars (TreeStar 1-4): Shockwave on beats 2 and 4 in choruses (ping-pong with the Trees), a Ripple per bar
    outside choruses, a Pinwheel under each chorus run, and a full-size Shockwave on the first beat of each section.
  - Mega Tree: a shader per Trees block (rotated per section story from the user's own favourites: verses Continua
    Variation / Fly Through / Aurora; chorus A Vortex V2 / Hex Vortex; chorus B Spiral Over Beams / Blue Streaks /
    Audio - PlasmaLike; the loudest choruses Black Cherry Cosmos / InnerDimensionalMatrix; outro Aurora / Continua)
    with the settings copied from his own sequences, under a one-colour On layer (Average blend) in the Trees' colour.
    The tree changes colour/shader ONLY when the Trees VU block changes (per-bar/beat switching was far too busy).
  - Arches: chase every other bar, Ripple on top at section changes. Stars: Shockwave on chorus downbeats, Per Model
    Default buffer (each star fires on its own); Mega Topper: same Shockwave, single model.
  - Radio_EFL (`add_radio`, submodel rows = `SubModelEffectLayer` inside the model's Element; `--no-radio` skips): "Tune to Matrix"
    (36x6) scrolling white Text "NOW PLAYING: <song> - ECLIPSE 6" (artist is always Eclipse 6; song = xsq `song`; 5-5x5 Mono,
    Dir left; checked in a render, legible); "Large matrix" (20x10) VU Meter with 20 bars on the Trees VU blocks (Spectrogram /
    Volume Bars alternating); Outline + Handle chase per bar; speakers: circles on beats 1,3 and star on 2,4 in choruses
    (Per Preview Shockwaves, like the user's own sequences), one pulse per bar elsewhere; 5x5 Spinners Shockwave per bar and a
    music Strobe at peak choruses. The user's older sequences use lyrics on the text matrix and shaders/spirals on the Large matrix.
  - Matrix and Matrix 2 carry the same Mega Tree effects (shader per Trees block + one-colour On tint, `MEGA_TREE_LIKE`).
  - Lyrics Matrix (`add_lyric_words`; 30x120 nodes, `--no-lyrics` skips): one Text effect per sung word, **upper case**,
    punctuation stripped (`_NO_PUNCT`), font `12-15x15 Bold` (about 13 px per letter on the 120 px wide matrix; wide letters like EVERYBODY clip without a drift),
    colour = the story's star colour 1 (`lyric` role) on a dark 30% shade of the story's flood colour (`lyricbg` role, an On
    layer under the text, per Trees block). Words wider than the matrix get a short **left-to-right drift** (`lyric_drift`:
    Text XStart = -d, XEnd = +d percent of width; the text effect's position sliders act per effect, hence one effect per word).
    Words come from a timing track named exactly **"Lyrics"** with phrase/word/phoneme layers, copied from the fullest
    singing-prop track (the text effect's "Lyrics - Words" choice only exists for a track so named; a single-layer track under
    another name showed nothing). Check with `render_model_frame` on "Lyrics Matrix" at a sung word.
  - Rows that gain effects are made visible (Matrix, Matrix 2 and Lyrics Matrix are hidden in the layout).
  - Master view row order (`order_rows`): model groups first (A-Z), then models (A-Z), timing rows keep their slots. User requirement.
  - SS Spinner / SS Snowflake (`add_showstoppers`, `--no-showstoppers` skips; 2026-10-26): styled on the user's SS Spinner
    L/M/R sequences in E:/2023/ShowFolder3D (196 songs: mostly ~1 s SingleStrand chases on submodels, short Shockwaves on
    rings, On flashes on Starburst, Pinwheels; settings copied). Each section picks two chase submodels (alternating per bar,
    beats 1-2), choruses add a ring Shockwave on beats 2 and 4 and a whole-prop Pinwheel on the first chorus bar, peak bars
    flash a centre piece. Seeded by song name. ShowFolder3D has no SS Snowflake, so it mirrors the spinner on its own
    submodels. Both props are drawn with pixel size 1, so they look faint in the house preview; `render_model_frame` on
    them is the check (pick a time inside a chase).
  - Video on a matrix: colour-panel brightness 150 (`--video-brightness`, user 2026-10-26; videos are filmed dark).
  - Icicles: On wash per 2 bars. FloodLights: On wash per section.
  - Music Sparkles ("Sparkles reflect music") on, frequency 0, in a contrasting colour per section, on everything except the
    FloodLights and the Mega Tree tint layer. Unused rows hidden. Length stretched to the audio.
  - Moving heads MH-1..MH-8, white only (user: "don't bother with any colour"), one layer, dark between effects, pan fixed
    at 90 so tilt = left/right lean (`add_moving_heads`, uses `mh_settings` from `video_beams_to_xsq.py` for the full key set):
    verses = soft fan "pool" fading up/down per 2 bars; first bar of each new section = sweep wide -> narrow; chorus beats =
    ping-pong (heads 1,3,5,7 on beats 1,3; 2,4,6,8 on beats 2,4, mirroring Trees/Trees Stars); peak-chorus downbeat =
    straight-up strobe burst; last 2 bars = converge and fade. `--no-heads` leaves them blank.
    **Pre-positioning (user requirement):** before every beam a dark pan/tilt-only Moving Head effect with "Link end position to
    next Moving Head effect" (`E_CHECKBOX_MHLinkToNext=1`, via `mh_settings(..., link=True)`) is placed in the gap, up to 1 s long,
    so the head is already in place when the light comes on. No colour/dimmer in it (a dark dimmer in a linked effect leaked a beam).
- **Per-song look (2026-10-26, user: songs looked identical)**: `song_look.py`. The song's name (xsq stem) seeds the shader
  rotation from `scripts/shader_pool.json` (42 of the user's own shaders + Mega Tree settings mined from E:/2023/ShowFolder3D,
  grouped calm/drive/peak by measured motion; dark or flat ones dropped after a Mega Tree test render); `--look-video <mp4>`
  turns the video's main hues into the colour story (song_to_package passes it automatically). `--classic-look` = the old
  fixed look. Regenerating an older song from its .bak now changes its shaders too.
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
   (skip dropped songs), then render. A very long render can stall: if `render_clip` says it was silent for 30 min, the mp4 may be
   truncated (`ffprobe` says "moov atom not found" and the old good video is already overwritten): re-run it (The Greatest Snowman,
   579 s, stalled once and then rendered fine on the retry).

### Loading a regenerated file into xLights
xLights keeps an open sequence in memory, so after regenerating a `.xsq` close and reopen it before looking or rendering:
`curl -s http://127.0.0.1:<port>/xlDoAutomation -X POST -H "Content-Type: application/json" -d '{"cmd":"closeSequence","force":true,"quiet":true}'`
then `{"cmd":"openSequence","seq":"F:/ShowFolderAI/Eclipse6-<Name>.xsq","force":true,"promptIssues":false}`. The user likes to inspect one
file in the editor before the batch is rendered. `render_model_frame` (model + time) is the quick way to check one model's pixels.

### Preview selection and checking the moving heads
- `render_clip` exports whichever preview is selected in the House Preview pane (the user must select it; the API cannot).
  Pass `width=1920, height=1058`: that sets the output size, so the pane does not need to be maximised.
- **Final house videos need the normal house preview selected, NOT "MH Preview"** (MH Preview frames only the head row).
- To check head motion, select **MH Preview**, render a clip to the scratchpad (not HousePreviewVideos), and crop the head row
  `crop=1500:110:190:870` at 1920x1058 (pilot This Christmas 0-100 s looked right). Then switch back before the real renders.

## 6. Hand-off
Tell the user which song is ready to verify in xLights. Update the status row in the doc (Pilot / Applied / Done: Done
only after the user has reviewed the render). Commit script changes only; the show folder is outside the repo.

## State of the show folder (Oct 2026)
2026-10-17: 18 Eclipse6 songs regenerated and re-rendered with everything above (moving heads with pre-positioning, Radio_EFL,
Matrix/Matrix 2 shaders, Lyrics Matrix words, groups-first row order); `Please-Dont-Cancel-Christmas` was dropped by the user (its
.xsq is regenerated but it is not rendered); `Deck-the-Halls-layout` is the older file and is skipped. All use the default colour
story; the user reviewed This Christmas in the editor ("working quite well") but not the other videos.
Non-Eclipse song added: `Eclipse6-Raining-Tacos-Again` (Parry Gripp, YouTube e6Q7s8Zr93Q). It has a video on the Matrix:
`enhance_layout.py ... --artist "Parry Gripp" --video "Videos/Eclipse6-Raining-Tacos-Again.mp4" --video-model Matrix --video-crop 6`
(Matrix is 120x60 = 2:1, a 16:9 video is cropped 6% top and bottom; the video file lives in `F:\ShowFolderAI\Videos`; pass the
same flags when regenerating from the `.bak`, and that matrix then gets no Mega Tree effects). Whisper heard a few words wrong.
Videos: `F:\ShowFolderAI\HousePreviewVideos\`. Plan doc: Claude doc "Eclipse6 Sequence Enhancement Plan".
Candidate next songs the user is considering: a "top 10 Christmas" list (Jingle Bell Rock, Rockin' Around the Christmas Tree, Last
Christmas, It's Beginning to Look a Lot Like Christmas, Carol of the Bells, Let It Snow, Santa Claus Is Comin' to Town, Rudolph,
Sleigh Ride, Wonderful Christmastime); waiting on YouTube links/choices.

## Lessons and user preferences
- The user wants effects to follow the music's structure and prefers you to keep going without waiting between steps; confirm only real design choices.
- A "peak" cut-off of energy 0.9 marks most choruses on some songs; use relative thresholds for variety (the shader peak is 97% of the loudest chorus).
- Mega Tree look = user's own technique: a palette-aware or fixed-colour shader under an Average-blend single-colour On tint.
- Sparkles: enable "reflect music" only, never set a frequency; exclude the floods.
- Layer order: first EffectLayer in the xsq is the top layer. Palettes are written as `ColorPalettes` entries referenced by a 0-based `palette=` index; effects without it render in the default colour.
- Automatic tempo/section detection is unverified; if a song's bars look half/double speed, say so and check.
