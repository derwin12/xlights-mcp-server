---
name: window-matrices-own-story
description: "ShowFolder3D window matrices + Matrix Seeds get their own drawn \"window\" scenes, never a copy of the other matrices"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 8ebe5222-ad00-4409-a649-b3280c511349
  modified: 2026-11-24T22:24:04.560Z
---

ShowFolder3D has three upper-window matrices: Window Frame-Upper-1 Matrix (13x27, left), Matrix Seeds (28x41, middle), Window Frame-Upper-3 Matrix (17x27, right). The user wants these varied, not repeating what the other matrices show. For Choosin Texas (2026-11-24) they loved a window triptych: curtains + sill + snow outside, with a candle (left), a tree decorated over the song (middle), and a cowboy-boot stocking (right), each timed to lyric words. Stories: scripts/stories/choosin_window_*.py with shared choosin_windows_common.py.

**Why:** user said "try not to simply repeat what is on the other matrixes" and then "I love the preview".
**How to apply:** for new sequences, give these three their own slow, song-long story (drawn props, few emoji), render with matrix_storybook at each exact size, and show a side-by-side preview with audio. Related: [[mh-color-wheel]]
