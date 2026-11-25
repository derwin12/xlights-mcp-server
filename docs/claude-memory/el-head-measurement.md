---
name: el-head-measurement
description: EasyxLights videos: measure the 8 heads from a strictly vertical beam frame and check per-head detection share; a loose finder gave wrong heads twice
metadata:
  type: feedback
---

For each EasyxLights PRO video, measure the head x/y from a frame whose 8 beams are vertical (same x at two heights within 2 px) and never reuse another video's heads; then check that all 8 heads have a similar detection share.

**Why:** Beetlejuice (outer beams missed, user caught "missing lights at 48 s") and White Christmas (heads 50 px off) were analysed with heads from a loose finder; the rig shifts a few px per video.
**How to apply:** `scripts/el_pipeline.py reanalyze SLUG` does the strict measurement; compare per-head detection counts before building. Verified OK (<=1 px): Halloween, Addams, I Knew It, Santa, Made You Look; Sing within 4 px but uniform shares. Fallbacks added 2026-10-04: (1) videos that never show 8 vertical beams at once (When We Were Young, Hockey Song, Drunken Sailor): cluster beam x over the whole video and fit an even spacing; (2) videos whose beams are never vertical (Billie Eilish): fit an even 8-head grid to the head silhouettes in a median dark frame and pass `reanalyze --xs`. The head y must be tuned per video (`tune_y`: best of 13 y values on a fan window); a wrong y of ~10 px hid the outer beams of a fan (Wrap Me Up).
