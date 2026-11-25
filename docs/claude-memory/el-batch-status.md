---
name: el-batch-status
description: "Where the EasyxLights + PPD batch stands (packaged sequences, in progress, how to resume)"
metadata:
  node_type: memory
  type: project
  originSessionId: 9004c0dd-be66-41b1-8cb7-d2dd6fc9d1ec
  modified: 2026-10-06T13:41:39.472Z
---

Update 2026-10-06: the todo file is the source of truth now (~79 packaged, most marked unreviewed). All 81 are now done or skipped (Wednesday Credit Titles packaged 2026-10-06 after hand-fitting heads; remaining work is only reviewing the "unreviewed" ones). EL_Tiesto The Business v1 was approved and packaged (prep slug was `tisto_the_business`; a fresh prep found 0 clusters, the older prep data was fine). Older note below is stale. State on 2026-10-05: 19 sequences packaged (the 16 below plus EL_Todo Es Posible En Navidad v1, EL_Muse You Make Me Feel Like Its Halloween v1, EL_Corpse Bride Remains of the Day v1; all approved at v1 with prep defaults, no hand tuning; `side` out arg is a prefix, not a path). 2026-10-04: 16 sequences packaged to `F:\ShowFolderAI\packages` (15 EL_ + 1 PPD_): Halloween Is Here v12, Sing Intro v2, Addams Family Theme v4, I Knew It PRO v2, Santa Claus Is Coming To Town v1, Jingle Bell Rock v2, American Horror Show v1, Beetlejuice v5, Made You Look v1, White Christmas v2, Wrap Me Up v2, When We Were Young v1, The Hockey Song v1, Drunken Sailor v1, Billie Eilish Merry Little Christmas v1, PPD_Livingston Shadow v1. On hold: Wednesday Credit Titles (video downloaded, heads still to be fitted by hand; user said hold). 61 EL videos not started, 1 skipped duplicate.

**Why:** the user is working through the 81 PRO videos of the EasyxLightsVideos channel (todo: `test_videos/PRO_VIDEOS_TODO.md`, git-ignored).
**How to resume:** `python scripts/el_pipeline.py prep ID slug` (or `reanalyze slug [--xs ..]`), `build slug "EL_Title v1"`, render with render_clip ONE at a time (two at once timed out), `side slug render.mp4 out`, user reviews, then `scripts/package_xsqz.py`. Check the per-head detection share before building. See [[el-head-measurement]], [[el-sequence-prefix]], [[ppd-sequence-prefix]], [[mh-color-wheel]].
