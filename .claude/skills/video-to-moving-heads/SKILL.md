---
name: video-to-moving-heads
description: Reproduce the moving head (MH) beams of a fixed-camera light show video (YouTube URL or file) as an xLights .xsq on the MH-n models. Use when asked to analyze a show video's moving heads, convert beams to a sequence, match head pans/tilts to a source video, or "try another video".
---

# Video -> Moving Head sequence

Pipeline (all in `scripts/`, run from the repo root):

```
fetch_video.py  ->  video_beam_analysis.py  ->  video_head_facing.py  ->  video_beams_to_xsq.py  ->  render + compare
 (video, mp3)       (beams.json: lean/colour    (facing.json: lens        (.xsq on MH-n and the     (render_clip, then
                     /intensity per head/frame)   visibility per head)      Moving Heads Group)       look at head bodies)
```

Keep source videos and analysis JSON in `test_videos/` (git-ignored; `MANIFEST.txt` lists the flags that worked per video).
Finished sequences go in `F:\ShowFolderAI`; superseded versions get moved to `archive_beam_work\`, never deleted.

## Prerequisites
- xLights running with xFade automation: `xlights_status` must say reachable (`render_clip` needs it).
- `ffmpeg` on PATH. For YouTube: recent yt-dlp (`pip install -U yt-dlp`) **and Node.js** on PATH. Without them a download
  starts and then 403s partway; `fetch_video.py` already enables Node.
- The show layout needs `MH-1..MH-8` (DmxMovingHeadAdv) and a "Moving Heads Group", plus a layout group **"MH Preview"** framed on the
  head row. `render_clip` exports the **House Preview pane**: the *selected preview* in that pane sets the camera and framing, and the pane's
  pixel size sets the output size unless you pass `width`/`height` (xLights then renders that size regardless of the window). Always render
  with `width=1920, height=1058`. The user must have **"MH Preview" selected** in the House Preview pane; that cannot be set from the API
  (no automation command selects a preview or resizes the pane, and window enumeration is blocked).
  **Always verify the framing before comparing**: `python scripts/mh_frame_check.py write`, render `MH Frame Calibration` (0-6000 ms,
  width 1920, height 1058), then `python scripts/mh_frame_check.py check VIDEO`. It must print OK. "WRONG FRAME SIZE" = no width/height was
  passed and the pane is not maximised; a lens-position MISMATCH at 1920x1058 means the wrong preview is selected (the frame then shows the
  whole house layout instead of the head row). Head-row crop of a good frame (MH-2..MH-7): `crop=1100:110:340:870`.
  Beam length scales with model size (`DmxBeamLength` x scale).

## Steps
1. **Get the video**: `python scripts/fetch_video.py URL --audio` (cached in `~/.cache/xlights-mcp/videos`), then copy the mp4/mp3
   into `test_videos/` with a descriptive name and add a MANIFEST entry. Only download videos the user may use.
2. **Find the heads** (1280x720 coordinates). Pixel Pro Displays roofline rig (6 heads): `426,180;474,180;522,180;570,180;618,180;666,180`.
   For a new rig, find a frame where beams are vertical, measure the beam x positions (even spacing), and use those, not eyeballed
   head positions (hand estimates were off by 3-6 px and dropped beams). Head count != 8 maps to the middle models (6 heads = MH-2..MH-7).
3. **Window test** a 10-20 s stretch with `--overlay` and look at it before the full run:
   `python scripts/video_beam_analysis.py VIDEO out.json --heads "..." --background --max-angle 85 --min-score 8 --cover-level 5 --base-slack 9 --base-cover 0 --start S --duration D --overlay ov.mp4`
   Flags: `--background` for a lit sky; `--max-angle` for near-horizontal beams; `--base-cover 0` when beams fade in away from the
   lens and heads are well spaced (keep the default 0.75 and `--base-slack 7` in tight layouts like I Knew It, 27 px apart).
   Then run it for the full video (about 10 min per 4 minutes of video; run in the background and use Monitor).
4. **Facing pass** (Pixel Pro style heads with a teal lens): `python scripts/video_head_facing.py VIDEO facing.json`.
5. **Choose the pan mode**. A beam's lean cannot reveal the pan (many pan/tilt pairs lean the same), and the sources never hold a fixed
   pan. For Pixel Pro videos use `--pan-mode orient --facing facing.json`; the lens visibility fixes the pan.
   - Heads with no lens showing look like an **arch** with the cap leaning along the beam (no yoke arms): default `--hidden edge`
     (Doors, Dolly, Bow Wow). They look like a **housing between both yoke arms**: `--hidden away` (Fireflies). Compare a few
     lens-less heads in the source with probe renders if unsure.
   - Other rigs (e.g. the 4K I Knew It, different head mesh): `--pan-mode lean` (or `fixed`), group fans on (`--fan-banks 4,4`).
   - `steer` is the cruder version of orient (tilt ~45, pan steers). Fans are tilt fans at pan 90, so steer/orient skip them.
6. **Build**: `python scripts/video_beams_to_xsq.py beams.json "Name vN" --audio ABSOLUTE_OR_REPO_PATH.mp3 --pan-mode orient --facing facing.json [--hidden away]`.
   `--audio` is written as an absolute existing path (a missing media file makes xLights wait on a prompt and `render_clip` hangs).
   Use a **new sequence name for every revision**: xLights renders a same-named sequence from its stale open copy.
7. **Render**: `render_clip` with the full range and an `output_path` in the scratchpad.
8. **Verify** (do all of these, then show the user a side-by-side and open it):
   - Head bodies at several timestamps: crop the source heads (`scale=1280:720,crop=300:60:390:160`, then `scale=1650:330`) and the replica heads
     (`crop=1100:110:340:870`, then `scale=1650:165`) and stack them.
     Check lens visible / arch / housing-with-arms and the tilt direction. Pick moments with different facing states (see `facing.json`).
   - Flicker: count dark effects <= 200 ms in the .xsq (should be near 0), and compare beam turn-offs per head in the beams JSON
     (gaps <= 0.2 s bridged) with those in the sequence. A short dark gap in a steady beam is a detector dropout, never real, unless the
     source shimmers (1-frame alternating strobe is kept as a dense dimmer curve).
   - Pan jumps > 120 deg between consecutive effects should happen almost only while a head is dark.
   - Media exists and the sequence type is Media.
9. **Iterate on the user's timestamps.** Typical feedback is "at 1:27 the pans look off": compare that moment's head bodies and the
   effect list for that head (parse the .xsq EffectDB: effect settings contain `&comma;`, and a regex stopping at `;` truncates the dimmer).
10. **Wrap up**: save the finals, archive the rest, update `MANIFEST.txt` (and the project memory), commit scripts (not videos).

## How orient mode works (so you can debug it)
With r = lens fraction / 0.115 (share of the beam toward the camera) and the measured lean L, a candidate pan p fixes the tilt
(`tan t = tan L / sin p`) and predicts the toward-camera share `bc = sin t cos p`. `viterbi_pose` picks, per run of lit frames, the pan path
whose bc best matches r, with a cost for changing pan (`PAN_LAMBDA`), so noise in r near the hidden threshold cannot flip a head between two
poses (a flip is a 180 deg swing the motors cannot follow; it made beams cross at Bow Wow Wow 51 s). Hidden lens (r < 0.12): `edge` = bc ~ 0
(head sideways, arch); `away` = bc at or below -sin 45 (turned away, arms showing, pan near 0). Dark gaps park the head like the source,
then move to the next beam's pose for the last 1.5 s. A dark lens facing the camera is the same gray as a head's back, so colour cannot
separate them.

## Shimmer and strobe
The source flickers some beams: 1-frame alternation (Fireflies ~21 s, 20 Hz) and longer patterns (Bow Wow Wow 1:52: 3 frames on, 3 off,
neighbouring heads in opposite phase). A repeating short gap (>= 2 other gaps within 0.6 s, each <= 0.3 s) keeps the beam as one run with
zero intensity in the dark frames, and a dense dimmer curve (up to 400 points, sampled on the effect's own frame grid) reproduces it.
Lone gaps up to 0.2 s are detector dropouts and are bridged. Check shimmer by comparing each head's per-frame on/off pattern with the
source's (should match 100%). Layering an On effect with Shimmer over the MH effect was tried and does not work on these models: it
writes every channel, so Brightness kills the beam and Min/Max swing the pan/tilt.

## Traps seen so far
- Dropping short path segments left holes that the dark gap-fill turned into flicker; the converter now merges them.
- Preview `SlewLimit` is a speed cap on how the head is *drawn* (deg/s per motor; not the DMX values). It was 100 and the source sweeps
  reach ~185 deg/s, so fast moves lagged in renders; on 2026-10-03 the user's layout was changed to 250 for all 16 motors (backups in
  `archive_beam_work\layout_backups`). Do not change it again without asking. xLights' `setModelProperty` automation call only worked for
  MH-1 (other models silently unchanged), so layout edits were made in the file with xLights closed, after a backup, and verified by diff.
- Replica beams start at the lens, which shifts as heads tilt, so measuring replica angles by casting rays from fixed head positions is
  unreliable in dense fans; judge by eye (head bodies and beams).
- `git status` shows unrelated files (CLAUDE.md, other scripts): stage only your own.
