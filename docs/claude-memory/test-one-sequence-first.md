---
name: test-one-sequence-first
description: "For bulk .xsq edits across a show folder, summarize first, apply to one sequence for user verification, then roll out"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 125314e0-2129-4bf6-8f05-4ecf97dea917
  modified: 2026-09-26T01:36:41.315Z
---

When bulk-editing many .xsq sequences, summarize the plan before changing anything, then apply to a single sequence so the user can verify in xLights before rolling out to the rest.

**Why:** User asked for a summary before changes and then "just change 1 sequence first, so I can verify" — caught a blend-mode issue ("1 is True Unmask") before it spread further.

**How to apply:** Check get_open_sequence before writing (xLights may overwrite an open file); back up to a sibling folder outside the show folder; verify XML parses after each write.

Related: [[xlights-mask-blend-needs-underlying-effect]]
