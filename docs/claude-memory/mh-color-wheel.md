---
name: mh-color-wheel
description: "MH-1..8 use a colour WHEEL, not RGB mixing; colours off the wheel render white, so beam colours must snap to the wheel"
metadata:
  node_type: memory
  type: project
  originSessionId: 03606653-565a-4b39-b21c-35932e409058
  modified: 2026-10-04T16:33:33.697Z
---

The Moving Head models (DmxColorType=1) only show colours on their wheel (`DmxColorWheelColorN` / `DmxColorWheelDMXN` in `xlights_rgbeffects.xml`). Any other hue renders white (probe 2026-10-04: orange, yellow, cyan, purple, magenta all white; red/green/blue fine). Wheel as of 2026-10-04: white, red, green, blue, magenta (#ff00ff, DMX 80), orange (#ffa500, DMX 30, same DMX as red: flagged to the user).

**Why:** Addams Family beams (magenta/red/green) rendered mostly gray before the wheel was understood. The user wants one consistent palette: the same green for every green beam.
**How to apply:** `video_beams_to_xsq.py` snaps each beam to the nearest wheel colour read from MH-1 in the layout (`--palette wheel`, default). Beams that cross house outlines pick up the outline colour, so for white-beam shows use `--white`. Layout edits need xLights closed, a backup in `archive_beam_work\layout_backups`, and a diff check; the user copied MH-1's wheel to MH-2..8 this way. See [[video-beam-to-moving-head-project]].
