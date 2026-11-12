# house_show: a lights video -> xLights sequence, plus drawn matrix art and moving-head choreography

Built for "Christmas Techno Mix 2011" (YouTube `vtZ5pX00MfI`, fixed camera on a house) and the show in `F:\ShowFolderQA`.
Everything is tuned to that one video and layout (prop boxes, group names, matrix sizes, paths), so treat it as a worked
example to copy and adapt, not a general tool. Constants to change are at the top of each script or inline in `build_sequence.py`.

## Pipeline (run from the repo root; `S` = a scratch folder that holds the intermediate arrays)
1. `python scripts/fetch_video.py URL --audio` downloads the video and mp3 (cached in `~/.cache/xlights-mcp/videos`).
2. `segment_video.py S` loads every frame at 640x360 into `S/F.npy`, finds the lit regions (`S/seg.pkl`).
3. `cluster_cells.py S 14` groups cells that flash together (`S/clus.pkl`, `S/cells.npy`).
4. `roof_mask.py S` accumulates the red roofline mask over time (`S/roofmask.npy`).
5. Draw the matrix art into `F:\ShowFolderQA\Videos` (all beat-locked via `xlights_mcp.audio.beats`):
   `spectrum_bars.py` (96x16), `abstract_bounce.py` (96x16), `santa_and_minis.py` (Santa 48x27, mini snowflakes 50x12,
   append `mini` to skip Santa), `bells.py` (48x27), `columns.py` (8x40 barber pole / bouncing ornament),
   `garage_snowflake_rings.py` (older 48x27 snowflake and rings, no longer used).
6. `build_sequence.py S OUT.xsq AUDIO.mp3` writes the sequence: On effects per prop (the `MAP` dict maps video
   regions `O1..O16`, `H*`, hand-placed boxes such as `E`/`R`/`W`/`T` to models and groups), Video effects on the
   matrices and TV-Right, beat/bar/section timing tracks, and the moving-head effects.

## Moving heads (`mhmarks.py` + the MH block at the end of `build_sequence.py`)
- Sections come from bass/treble/loudness changes per bar: CALM, GROOVE, BUILD, DROP -> `MH Sections` track.
- `MH Chase`: one head per beat, 1..8 then 7..2 (no repeated end head). Each lit effect is white, full dimmer, auto shutter,
  pan 0 / tilt +15 (the project's pose: tilt 0 = straight up, positive tilt at pan 0 leans toward the camera).
- A linked effect (pan/tilt only, holds pan 0 / tilt 15) runs from the end of the head's previous effect to the next lit one.
- Flick beats (`MH Accents`): all eight heads, green (wheel green), tilt 15 -> 40, replacing that beat's single chase head.
- CALM sections get a staggered sine sweep per head (pan +-45 x2, tilt 15 +-8 x4, starts/ends at the chase pose).
- Not built yet: the BUILD fan and the strobe marks (timing marks only).

## Gotchas learned
- `render_clip` exports whichever sequence version xLights has loaded and the selected House Preview; reload the sequence
  after every rebuild, and do not use xLights while a render runs.
- The layout's colour wheel here is red/green/blue/white only; other colours render white.
- Beat 1 = the detector's first beat; it may sit half a beat off the music.
