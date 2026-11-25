---
name: vendor-ground-truth-livingston
description: Ground-truth scoring of video->sequence against the Pixel Pro Displays Livingston Shadow MH sequence (DMX effects); decoder, geometry, scores
metadata:
  type: project
---

The vendor's MH zip (`C:\Users\daryl\Downloads\New Folder\Livingston-Shadow_Halloween-M\Livingston-Shadow_Halloween-MH.zip`, video 4c6-q5sc4u8) has 6 `DmxMovingHead3D` models (MH1..6, x 425.6..665.2) driven by DMX effects: ch 9 pan, 11 tilt, 1 dimmer (value curves Ramp / Ramp Up-Down / Saw Tooth / Custom) plus an "MH Intensity" sub-model layer of On/Color Wash that lights the beam. The first zip (`...MH -Pro.zip`) has no MH at all ("sold separately").

**Geometry (fitted 2026-10-04):** pan = DMX*540/255, tilt = DMX*220/255 - 110 (vertical at DMX ~128), beam = (sin t sin p, cos t, sin t cos p); layer 1 is a baseline pose, layer 0 overrides; the vendor's motors are slew limited at 120 deg/s (the video shows the slewed motion; 120 fits best).
**Scores of `PPD_Livingston Shadow v1` (orient + facing) vs vendor:** lit/dark F1 0.948 (zero time offset); screen-lean median 1.95 deg (78% within 5); 3D beam direction median 7.3 deg (59% within 10); toward/away-from-camera sign right 91% where it matters.
**How to apply:** `scripts/vendor_dmx_decode.py` (decode) + `scripts/compare_to_vendor.py` (score). Reuse for any vendor MH sequence with the sequence file. See [[ppd-sequence-prefix]], [[video-beam-to-moving-head-project]].
