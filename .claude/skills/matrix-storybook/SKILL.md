---
name: matrix-storybook
description: Make a "storybook" video for a pixel matrix in an xLights sequence - animated picture scenes that tell the song's story, timed to the sequence's Lyrics words and Beats (like the Pixel Pro Displays "turn your matrix into a storybook" reels) - and put it on the matrix's Video effect. Use when asked for a storybook / story video / animated scenes for a matrix in a sequence, to restage a story for another matrix size, or to retime/fix scenes in an existing story.
---

# Matrix storybook video

Tool: `scripts/matrix_storybook.py` (run from `scripts/`, so stories can `import matrix_storybook`). A story is a Python
file in `scripts/stories/` with `build(tm) -> list[Scene]`. Examples:
- `hippopotamus_for_christmas_mini.py`: **the reference.** This is the version the user approved, for a 25x24 mini matrix.
- `hippopotamus_for_christmas.py`: a 48x27 layout plus the drawn props: stairs, cape, garage, chalkboard, pond, Santa hat, `hatted_hippo`, `toss`, `falling`. The mini story imports these props.
- `shake_the_snow_globe.py`: 30x40. Its sequence's lyric labels have since changed, so it no longer runs as-is.

```
cd scripts
# contact sheet while designing (fast; check every scene)
python matrix_storybook.py stories/NAME.py "SHOW/SONG.xsq" x.mp4 --size WxH --flat --sheet SHEET.png --at 3,8.5,12,...
# final video: one story pixel per LED, 20x nearest-neighbour blocks
python matrix_storybook.py stories/NAME.py "SHOW/SONG.xsq" "SHOW/Videos/<Song> Storybook <Matrix>.mp4" \
    --size WxH --k 1 --ss 4 --scale 20 --flat --fps 40 --jobs 10
```

## What the user wants (learned on Hippopotamus, 2026-11-19)
- **Lay the story out at the target matrix's exact LED size** (`--size` = model width x height, `--k 1`). The
  Video effect runs with aspect ratio off, so a 16:9 video on a 25x24 matrix gets squashed and its text becomes unreadable.
  Get the size from `xlights_rgbeffects.xml`. For a Matrix model: strands = `NumStrings*StrandsPerString`, nodes per strand =
  `NodesPerString/StrandsPerString`. With `Vertical="false"` the strands are rows, so Matrix-mini = 25 wide x 24 tall.
  A Custom model uses `CustomWidth`/`CustomHeight`.
- **Pixel-art look, not HD.** The user rejected a 1080p version and a smooth 480x270 version as "too HD". They want
  **black backgrounds**, **one big picture per scene** (two at most), and flat colours (`--flat` posterises emoji to 8
  solid colours with hard edges). Use sparse stars, snow and sparkles, and at most a low ground strip.
- **Very few words**, and only words that fit the 3x5 LED font across the width (about 6 characters on 25 px). Never put
  words up before they are sung. Time them to the lyric words (`tm_after(tm, "word", t)`), not to the music intro.
  The intro instrumental gets a quiet scene with no text.
- Scenes change on the lyric phrases, and pictures pop, bounce or pulse on sung words and beats. Things in a list get one
  scene each (e.g. doll, then teddy, then train, each with a 🚫).
- Light-coloured parts of a picture vanish against white snow at this size: put feet on black, or lower the ground.

## Workflow
1. Read the sequence: `Timing(xsq)` gives `tm.words` (Lyrics word layer, labels are the sung case, e.g. "hippopotamus"),
   `tm.beats`, `tm.duration`. Print the phrase layer and the words with times to plan scenes against the lyrics.
2. Find the matrix and its current Video effect (`E_FILEPICKERCTRL_Video_Filename`). Note the model size (above).
3. Write the story: one scene per phrase. Copy the patterns from the mini reference. Pictures are Noto emoji (Apache 2.0,
   fine in sold sequences). Props are drawn with PIL in story pixels (`P(v) = v * mb.SS`; read `mb.SS`/`mb.LW()` at draw time).
4. Check with `--sheet` at the key times, and fix anything that doesn't read at LED size.
5. Render the video. Test it the way xLights shows it: `ffmpeg -i V -vf "fps=1/8,scale=W:H:flags=area,scale=8*W:8*H:flags=neighbor,tile=10x2" -frames:v 1 sim.png`.
   Fades and crossfades can make single frames look dark; check those with `-ss T` before treating them as bugs.
6. Wire it in, only with the sequence closed in xLights. Back up the .xsq (`.storybook.bak`), change the Video effect's
   filename, **and** change the matching `<SequenceMedia><Video path=...>` entry. Validate the XML. Tell the user to
   reopen the sequence, and that a stale copy open in xLights would overwrite the edit if saved.
7. Open the result for the user with `Start-Process <file>`. To render frames in xLights itself
   (`render_model_frame`), xLights must be on that show folder. Ask before switching show folders.

## Tool notes
- `--k N` = output pixels per story pixel; `--k 8+` switches words to a TrueType font (Luckiest Guy) and big pictures to
  Noto SVGs (needs `pip install resvg-py`). That is the HD path, which this user doesn't want for LED matrices.
- `--jobs` renders frames in parallel processes. Emoji and font downloads write their cache files atomically, because
  workers used to clash on the first fetch.
- The helpers in the library were written for 30x40 and scale with `f.W/f.H`, but `sparkles` and `rising` take explicit
  `box` ranges: pass ones that fit the grid.
