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
  Morph bars (percent coordinates, y up; see Morph patterns below), `ring()` is a Shockwave with Scale off so the radius is in pixels, plus
  `twinkle()`, `snow()` and `wash()`.
- **z order** (higher is in front) is packed into layers automatically. The reference uses BG 0, sweep 10,
  ring 12, back pictures 18, pictures 20, front 25, words 30.
- Times snap to the 25 ms frame grid.
- `--out` replaces everything on the model. Check what the original has first: a vendor's signature effects can be
  kept with `s.keep(t0, t1, kinds=("Pictures", "SingleStrand"), z=)`. It copies the source sequence's own effects
  that start in that window, unchanged, and skips MatrixScenes pictures, so re-runs are stable. Example: Feliz
  Navidad keeps its trumpet GIFs and horn chases on the garage during the horn verses (users notice when those
  vanish).

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

## Morph patterns (what SuperStar does with Morphs)
SuperStar's tree Morphs are rarely one full-width bar. About half are dots with short tails, and most of the rest
are short bar segments. They fire in mirrored groups of 2 to 8 and are chained beat after beat. The settings are
simple: 0.2 to 0.6 s, a 1 to 5 px head, no repeats or acceleration. `duration` controls the look: 100 gives a solid
moving bar, and around 33 gives a long fading tail that fills the area it swept.
- Pattern helpers draw one group inside `box=(x0,y0,x1,y1)`, which defaults to the whole matrix. Use a box per
  bush or garage door. The helpers are `quad` (split from the centre to the sides), `stripes`, `comets` (mirrored
  pairs), `burst` / converge, `corners` (diagonals collapsing into the corners), `frame` (edges closing to the
  centre) and `spin`.
- `morph_beats(t0, t1, colors, every=2)` chains them, alternating out and in. It replaces `bar_sweeps` where the
  tree has no patterns.
- `echo(t0, t1, box=, mirror=)` copies the tree's own SuperStar effects into the box. The tree is the model with
  the most Morphs in the same .xsq, read at build time. It copies Morphs, and also Galaxy, Fan and Shockwave, whose
  centre maps into the box and whose radius and width rescale to it (Scale to Buffer). Mirrored copies spin the
  other way. Copy Morphs only where the tree is pattern-heavy, which is usually instrumentals, bridges and finales.
  The round accents can be copied everywhere.
- Reference: `stories/scenes/morph_backdrop.py`, which every four-matrix story calls from `run()`. It uses one copy
  per garage door, per window and per half of the bushes, with every other copy mirrored, and a threshold of 8
  tree Morphs per scene. Some trees fire bursts of 100 to 190 Morphs at once, and copying those gave a 384 to 444
  layer garage. For those songs pass `backdrop(s, t0, t1, peak=16..24)`: busier scenes then keep only the round
  accents, and `pattern_sweeps` draws there instead.
- Echoes go on the main model, never on submodel layers. xLights draws submodels after the model's layers, so
  echoes there would cover the pictures. Every copy adds layers, about the tree's own count (up to 11). Eight
  per-bush copies came to about 10k effects and 144 layers, so use 2.
- The preview renders Morphs with the algorithm ported from MorphEffect.cpp, so the sheet shows the real head and
  tail.

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
