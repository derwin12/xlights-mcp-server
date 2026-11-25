---
name: video-beam-to-moving-head-project
description: Video beam -> Moving Head .xsq converter; calibration facts and xLights gotchas learned while building it
metadata:
  node_type: memory
  type: project
  originSessionId: 43797b90-c9d6-4ebd-85b9-a5d4a5d8cda3
  modified: 2026-10-03T16:12:43.322Z
---

Project (started 2026-10-03): analyze a fixed-camera light show video, detect moving head beams, regenerate them as Moving Head effects on F:\ShowFolderAI layout (MH-1..MH-8, DmxMovingHeadAdv). Scripts: scripts/video_beam_analysis.py -> beams JSON, scripts/video_beams_to_xsq.py -> .xsq (--audio adds media + Beats track), scripts/mh_calibration_sequence.py. Sample video: "I Knew It.mkv" (4K, 8 heads). Full-length result: median angle error 0.6 deg, 94% within 3 deg.

Key facts (not derivable from code):
- Calibration: with Pan=90, Tilt equals on-screen lean from vertical (positive = right). Camera lean = atan(tan(tilt)*sin(pan)).
- MH slot `Dimmer:` is x,y curve points; panel default `0,0,1,0` = OFF. Full on = `0,1,1,1`. Slot also needs `;Shutter: On` to open the shutter.
- Motor SlewLimit=100: an un-addressed head swings slowly toward its next pose, so gaps must be filled with a dark effect pre-positioned at the next start pose. xLights' own "Link end position to next Moving Head effect" (E_CHECKBOX_MHLinkToNext=1) does the same; the converter sets that flag on gap effects.
- render_clip/render_frame re-export xLights' already-open copy of a sequence: a rewritten .xsq with the same name renders STALE (byte-identical mp4). Write each revision under a new sequence name.
- render_model_frame returns a tiny pixel strip, useless for beam geometry; use render_clip on the house preview.
- ffmpeg drawtext segfaults here (no fontconfig); skip text overlays.

- Detector phantoms: a head's ray can lock onto its left neighbor's beam (e.g. heads 2/6 at 52.8s); fixed by the base-cover test (beam must be lit at its own head) in video_beam_analysis.py. Always regenerate beams JSON after detector changes; v3 was stale, v4 (beams_full3.json, --pan-mode lean, with --audio) validated by the user as "perfect" on 2026-10-03.

- Fewer heads than the 8-head rig: use the middle ones (6 heads -> MH-2..MH-7); user preference, now the converter default. Fireflies video (6 heads, lit sky) needs video_beam_analysis.py --background --max-angle 85 and lower --min-score/--cover-level.

- Head pan can't be read from beam lean alone (many pan/tilt pairs lean the same). Pixel Pro videos: read it from how much of each head's lens shows (scripts/video_head_facing.py -> teal fraction per head/frame). `--pan-mode orient --facing FILE`: r = lens fraction / LENS_FULL(0.115) is the beam's share toward the camera; sin^2 t = sin^2 L + r^2 cos^2 L, pan = atan2(tan L cos t, r). Lens hidden (r < 0.12) = edge-on: hold pan +-90 and let tilt change sign through zero (no 180-deg pan sweeps). User confirmed Doors "People Are Strange" and Dolly look right; source videos NEVER use a fixed pan. steer mode (tilt ~45, pan steers) is the cruder version.
- BUG fixed 2026-10-03: dropping path segments < 100 ms left holes that the dark gap-fill turned into flicker. Merge short segments (merge_short_segments) instead; bridge lone dropouts up to 0.2 s unless they repeat (shimmer). The 1-frame 20 Hz strobe (Fireflies ~21 s) is kept via a dense dimmer curve.
- --audio must be an absolute existing path (relative -> xLights waits on a media prompt and render_clip hangs; user had to switch the sequence to Animation).
- render_clip captures the house preview exactly as zoomed in xLights; if the user changes zoom the head positions in replica frames move, so recalibrate any replica measurement. Replica beams originate at the lens, which shifts as heads tilt, so ray-casting the replica from fixed head positions is unreliable in dense fans; compare head bodies/beams visually.
- Source videos kept (git-ignored) in test_videos/ with MANIFEST.txt; fetch_video.py needs recent yt-dlp + Node (YouTube 403s mid-download otherwise).
- Pixel Pro head positions in 1280x720: 426,474,522,570,618,666 at y~180 (measure from vertical beams, not by eye).

- Hidden lens means different things per show: Doors/Dolly = head turned sideways (arch, default `--hidden edge`); Fireflies = turned away with yoke arms showing (`--hidden away`: (tilt,pan)->(-tilt,-pan), same lean). Dark lens facing the camera is the same gray as a head's back, so colour cannot separate them. Final picks (promoted 2026-10-03, user approved): Doors v13, Dolly v11, Fireflies v12 (orient, away), I Knew It v8, Bow Wow Wow v2; older versions in F:\ShowFolderAIrchive_beam_work.

- Bow Wow Wow "I Want Candy" (youtu.be m5ryKut7r50) approved 2026-10-03: Bow Wow Wow I Want Candy Beams v2 (orient, edge; has a 3-on/3-off shimmer at 1:52 kept via dense dimmer). Pan path is now a Viterbi over pan states (viterbi_pose); Doors v13 / Dolly v11 / Fireflies v12 use it and are now the finals. User raised model size + beam length in the preview (beam length scales with model size); wants a dedicated House Preview layout group for stable framing; render_clip does not yet pass width/height to exportVideoPreview.

- SlewLimit raised 100 -> 250 on all 16 MH motors in F:\ShowFolderAI\xlights_rgbeffects.xml on 2026-10-03 (user asked; backups in archive_beam_work\layout_backups). Preview-only speed cap. setModelProperty only applied to MH-1, so the file was edited with xLights closed.

**Why:** these cost real debugging time. **How to apply:** reuse when touching MH sequence generation or render verification; planned next step is wrapping the scripts as MCP tools (analyze_video_beams, create_moving_head_sequence) and running scripts/gen_tools_reference.py.

**Pose estimation (2026-10-03, commits 8dd66a6, eb607db, be17681):** user said "you can't just look at the beam, look at the yoke position". Pan now comes from the yoke arms (video_head_facing.py `yoke`: ~10 px arms = pan 0/180, ~3.6 px arch = pan 90) plus lens share; Viterbi pan range is ±175 (not ±90), one-frame jumps >45° and mirror-pose run starts are penalised, and each head is pulled toward its *peers'* median pan (heads often move together; user hint). Finals: Doors v14, Dolly v12, Bow Wow v3 (all user-approved "perfect"/"excellent"); Fireflies v22 also approved. **Why:** mirror pairs (p,t)/(p±180,-t) look identical in lean+lens. **How to apply:** for new Pixel Pro videos use --pan-mode orient --facing (no --hidden); yoke constants are Pixel Pro mesh specific.

**Dancing With My Elf (Showstopper, Vimeo, 2026-10-03):** 8 black-silhouette heads, built with --pan-mode lean + group fans, user-approved ("pretty close"). User idea not yet done: fan pan + fan tilt group effects for uniform spreads (mh_fan fans are tilt fans at pan 90 only). Vimeo needs login for yt-dlp; user downloads the file by hand.

**Import/package finding (2026-10-03, corrected):** the "click each effect after import" problem was the 22 keys missing from generated effects (layer blend T_*, shutter/pattern keys, MH1-8 slots). xLights re-saves a file with the slot moved to the fixture number but does not add missing keys, so a package of the old Doors v14 needed a click per effect. Doors v16, regenerated with the full key set (mh_effect_settings), imports cleanly (MH-2->MH-1, MH-7->MH-8 into F:\ShowFolderQA\Test MH Import.xsq), both from my own .xsqz (F:\ShowFolderAI\packages) and from a package xLights built after a render. Slot form is irrelevant. My earlier claims that missing keys were harmless and that re-saved files must not be packaged were wrong. xLights repo H:\XlightsSourceDir\xlights: user said no commits there and any work on a new branch; branch mh-import-slot-mapping exists with no edits and no xLights change is needed. Final sequences: Doors v16, Dolly v14, Fireflies v24, Bow Wow v5, Elf v3, I Knew It v10.

- 2026-10-04: SlewLimit set to 0 (no limit) on all 16 MH motors by the user (was 250); tracks fast sequences frame by frame. Wheel now white/red/green/blue/magenta/orange/cyan/yellow, see [[mh-color-wheel]].
