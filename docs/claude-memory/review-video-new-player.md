---
name: review-video-new-player
description: "When showing review videos, never overwrite the previous file and open each in a fresh player window"
metadata:
  node_type: memory
  type: feedback
  originSessionId: a5c47959-bac5-4a30-a3ff-a24f2c653333
  modified: 2026-10-05T14:49:53.461Z
---

When showing side-by-side/review videos, write each to a new, versioned filename (never overwrite the one the user may have open) and open it in a new video player process (e.g. `Start-Process` the file) rather than reusing the existing one.

**Why:** the user's player held the current video; overwriting it replaced what they were reviewing (2026-10-05).
**How to apply:** `side slug render.mp4 out` with a fresh `out` name per video/version (e.g. `<slug>_v1_side_by_side.mp4`), then `Start-Process` it. Related: [[el-batch-status]].
