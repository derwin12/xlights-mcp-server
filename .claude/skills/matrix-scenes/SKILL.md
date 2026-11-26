---
name: matrix-scenes
description: Make a SuperStar-style picture story for a pixel matrix in an xLights sequence, built from short xLights effects instead of a video - embedded LED-size pictures on Pictures effects (slide, pop, hop on beats), Morph bar sweeps, Shockwave rings, Twinkle/Snowflakes - timed to the song's lyric words and beats, so it matches SuperStar imports on the MegaTree. Use when asked for matrix scenes / a SuperStar-style story / effects-based (not video) storybook for a matrix, or to restage or retime one.
---

# Matrix scenes (effects, not video)

Tool: `scripts/matrix_scenes.py` (run from `scripts/`). A story is a Python file in `scripts/stories/scenes/` with
`build(s: Story)`, plus optional `cues(xsq)` and `PREFIX`. **Reference (approved 2026-11-25):**
`stories/scenes/hippopotamus_window.py`, Hippo on a 40x48 window matrix.

Use this rather than matrix-storybook when the sequence has SuperStar imports on the tree, or when the user wants
fast renders and editable effects. matrix-storybook makes one full-length MP4 for a Video effect.

```
cd scripts
# contact sheet (rough local preview: pictures exact, Morph/Shockwave/Twinkle/Snow approximated)
python matrix_scenes.py stories/scenes/NAME.py "SHOW/SONG.xsq" --model MODEL --size WxH --sheet SHEET.png --at 3,8.5,12
# preview video with audio
python matrix_scenes.py stories/scenes/NAME.py "SHOW/SONG.xsq" --model MODEL --size WxH --preview P.mp4 --audio SONG.mp3
# write the sequence (a new copy first; only replace the original once the user has approved)
python matrix_scenes.py stories/scenes/NAME.py "SHOW/SONG.xsq" --model MODEL --size WxH --out "SHOW/SONG-MatrixScenes.xsq"
```

## How it maps to xLights
- **Pictures** are tight-cropped RGBA PNGs at LED size with hard alpha: emoji posterised by matrix_storybook's
  `icon_image` (FLAT), words in the 3x5 font (`s.word`, which has no Q, Z or digits; use `font=6` for those), and props drawn with PIL
  (`s.drawn`). They are embedded in `<SequenceMedia>` as `MatrixScenes/<PREFIX>/<name>.png` with `<Data>` base64,
  the same way the SuperStar importer stores its pictures. Re-running replaces that prefix's entries.
- Positions are sprite centres in LED pixels (x right, y down). `_offsets` converts them to Pictures pixel offsets
  using PicturesEffect.cpp's NONE/VECTOR mapping (C++ truncating division). Use `vector` to slide, `none` to hold,
  and start/end scale (No Scaling) to pop around the sprite's own centre.
- `show()` handles enter (left/right/top/bottom/pop/fade), hold with hops on `hits`, and exit. Other helpers:
  `glide()` moves through keyframes, `flash()` does quick SuperStar-style image swaps, `sweep()`/`morph()` draw
  Morph bars (percent coordinates, y up), `ring()` is a Shockwave with Scale off so the radius is in pixels, plus
  `twinkle()`, `snow()` and `wash()`.
- **z order** (higher is in front) is packed into layers automatically. The reference uses BG 0, sweep 10,
  ring 12, back pictures 18, pictures 20, front 25, words 30.
- Times snap to the 25 ms frame grid.

## Text styles (from the Burl Ives "Holly Jolly Christmas" 50x24 matrix video)
- **Two-tone shaded text:** `s.word("CHRISTMAS", WHITE, font=6, shade=RED)` draws a coloured copy `off` px
  (default `(scale, 0)`) behind a white face, so every stroke reads as a candy-cane stripe. `font=6` is a bold
  6-row font with A-Z, 0-9 and punctuation; 9 letters fit across 50 LEDs. The 3x5 font takes `shade` too.
  `color`/`shade` may be lists, cycled per letter (`[PURPLE, WHITE]`).
- **Per-letter motion:** `s.letters("HOLLY", t0, t1, x, y, shade=GREEN, hits=beats, motion=...)` makes one picture
  per letter. `motion="alternate"` makes odd and even letters take turns hopping up; use `phase=1` on a second line
  so it hops opposite. `"wave"` hops one letter after another, `"jumble"` gives wobbly random heights each hit, and
  `"still"` holds. `enter="drop"/"rise"/"pop"` brings the letters in one by one, `stagger` s apart.
- Demos: `stories/scenes/text_styles_demo.py` (every style, 50x24) and `stories/scenes/hippo_words_demo.py`
  (Hippo lyrics, two lines, each appearing as sung). Slide letters in from the edge nearest their line (`drop` for
  the top line, `rise` for the bottom line) so they never pass through the other line.

## Several matrices as one stage
`--model A,B` (comma-separated) builds a `Stage` from the layout (`xlights_rgbeffects.xml` next to the sequence,
or `--layout`). Each matrix is placed by its front-view WorldPosX/Y divided by the first model's ScaleX/Y (world
units per LED). For example, two 40x48 windows side by side become stage columns 0-39, then 24 LEDs of wall, then
the second window at 64-103. The story draws in stage coordinates, and each picture goes to every model it reaches,
using that model's own pixel offsets. A slide therefore crosses one window, disappears behind the wall and comes out
in the next. An image wider than one window (stairs, a pond, a garage) shows the right slice in each.
`sweep` left/right is one bar timed to cross each model in turn. `ring` goes to the model that contains its centre.
`twinkle`/`snow`/`wash` go to every model. `s.on(model)` is that model's own Story, in local coordinates.
`s.center(model)` gives a model's centre in stage coordinates. The layout warns about rotated models or a
different LED spacing, since pictures won't line up across those. Reference:
`stories/scenes/hippopotamus_windows.py`: the kid in one window and the hippo in the other, a ball tossed over the
wall, the hippo walking from the left window to the right window's door, one staircase across both, the windows as
a pair of eyes, and the two-car garage with a door in each.

## Timing
- If the sequence has a Lyrics track (word layer) and Beats, `Cues.from_xsq` reads them. Otherwise write
  `cues(xsq)` using `Cues.from_files`: words from `transcribe_words.py` (faster-whisper; the venv needs Python
  3.14 because 3.15 has no onnxruntime yet) and beats from librosa `beat_track`, saved under `stories/lyrics/`.
- `s.cues.w("word", after)` matches by prefix, so whisper splits like "hippo" / "-bottamus" still work.
  Print every word with its time before planning scenes.

## What the user liked (Hippo, 2026-11-25)
- One scene per lyric phrase on a black background: one big picture (about 30 px on 40x48), short words in the
  pixel font timed to when they're sung, a ring on the key word, and bar sweeps in Christmas colours.
- Lists get one item each, with a red 🚫 popping over it on the word. Instrumentals get their own small stories
  (skating, presents stacking, a tree with quick swaps at the end).
- Drawn props: stairs with the kid stepping down one step per beat, a cape behind the hero hippo, a garage.

## Workflow
1. Get the matrix size from `xlights_rgbeffects.xml`: strands = NumStrings x StrandsPerString, nodes per strand =
   NodesPerString / StrandsPerString. With `Vertical="true"` the strands are columns.
2. Check what's already on the matrix in the sequence. `--out` replaces every effect on `--model` in the output file.
3. Write the story, check the contact sheet, then send the user the preview MP4.
4. Write a `-MatrixScenes.xsq` copy and check it in xLights. Opening it switches the open sequence, so ask first if
   the user has another sequence open. Only touch the original after approval, with xLights closed on it and a
   backup made.
