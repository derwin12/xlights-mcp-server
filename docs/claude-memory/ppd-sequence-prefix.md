---
name: ppd-sequence-prefix
description: Sequences made from Pixel Pro Displays videos (the 6-head roofline rig) are named with a PPD_ prefix, like EL_ for EasyxLights
metadata:
  type: feedback
---

Name sequences made from Pixel Pro Displays (PPD) videos `PPD_<title> vN`, e.g. `PPD_Livingston Shadow v1`.

**Why:** the user keeps vendors' sequences distinguishable in the show folder (EL_ = EasyxLights, PPD = Pixel Pro Displays).
**How to apply:** use it in the `video_beams_to_xsq.py` name argument. PPD videos use the 6-head Pixel Pro rig (426..666 step 48, y~180 at 1280x720; MH-2..MH-7) and the teal-lens facing pass (`--pan-mode orient --facing`), see [[video-beam-to-moving-head-project]] and [[el-sequence-prefix]]. The Livingston Shadow zip from PPD has no MH models/effects ("Moving Head sequence sold separately"), so there is no ground truth to score against yet.
