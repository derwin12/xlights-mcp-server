---
name: matrix-video-extract
description: Turn a show-preview video of a pixel matrix (e.g. Pixel Pro Displays "24x50 Matrix" previews from YouTube) into a clean gap-free matrix video - one sample per LED, no dark spacing - as a 50x24 native file and a crisp 800x384 file. Use when asked to crop/extract a matrix from a video, remove the pixel spacing, or work through the list of Pixel Pro matrix sequences.
---

# Matrix preview video -> gap-free matrix video

Tool: `scripts/matrix_video_extract.py` (run from the repo root; on Windows Python pass `C:/...` paths, not `/c/...`).

```
python scripts/fetch_video.py URL --out-dir <new empty dir>          # untrusted download: keep it in its own dir
python scripts/matrix_video_extract.py IN.mp4 OUT.mp4 --auto --cols 50 --rows 24 --agg max \
    --scale 16 --filter neighbor --native NATIVE.mp4
```
- Layout of the Pixel Pro previews: the **24x50 matrix is on the left half** (50 columns x 24 rows of LEDs), the 6x4 P10 matrix
  on the right, a "24x50 Matrix" caption under the left one (~77% down). Resolution varies (1280x672 .. 1920x1080), so the grid
  is measured per video: `--auto` takes a max-over-time projection of the left half and uses the outermost lit dots
  (columns/rows that never light are fine). It aborts if the span doesn't match 50x24 at the dot pitch; then give
  `--first X Y --last X --last-row-y Y` by hand (read the dot peaks from the projection).
- Each LED = brightest pixel of a 3x3 patch (`--agg max`; small/faint dots) or the mean (`--agg mean`, big dots). Audio is copied.
- Outputs the user wants: `<Name>-24x50-matrix-native-50x24.mp4` (true 50x24, for xLights Video effects) and
  `<Name>-24x50-matrix-800x384.mp4` (16x nearest-neighbour = sharp square pixels; the user prefers this for viewing).
  The smooth bicubic upscale (1000x480) was rejected. The LEDs are treated as square pixels (50:24).
- Verify: ffprobe duration vs source, and a side-by-side frame (source crop vs output scaled with `flags=neighbor`).
- To watch: `Start-Process <file>` in PowerShell (native 50x24 plays tiny; open the 800x384 one).

## Batch
`python scripts/matrix_batch.py CSV OUT_DIR WORK_DIR [--limit N]` runs every `todo` row of the CSV: downloads the preview, runs the
extractor with `--auto --agg max --scale 16 --filter neighbor --native`, checks length vs source and that the output isn't black,
updates the CSV (`done` / `failed` + note) and deletes the download. A failure never stops the batch; rerun after fixing by
setting `failed` rows back to `todo`. Run it in the background (about 2-3 minutes per video).

Detection handles (learned the hard way): faint 1px compression slivers (ignored), a neighbouring P10 matrix's edge (dropped by
choosing the best window of exactly 50 positions), dark columns that never light, and videos that crop the matrix at the frame
edge (missing columns are extrapolated and sampled as black; the CSV note says how many).

## Source list and progress
`F:\ShowFolderAI\Videos\pixelpro-matrix-sequences.csv`: the 45 Pixel Pro Displays sequences with "matrix" in the name, filtered
from `https://xlights.info/search?query=Pixel%20Pro%20Displays` (a server-rendered table; each product page links its YouTube
preview). Columns include `status`, `output_prefix`, `note`. **Result (2026-10-17): 44 done, 1 skipped** - `Chris Tomlin ... Noel` is
a whole-house preview where the matrix is a small scene element, not the two-matrix layout. Outputs (native 50x24 + 800x384 per
song, ~1.6 GB total) are in `F:\ShowFolderAI\Videos\`. The user confirmed they own/may use these sequences.
