---
name: xlights-mask-blend-needs-underlying-effect
description: "xLights layer blend modes (Unmask/True Unmask) are ignored when no lower layer has an active effect; use near-black #010101 state color"
metadata:
  node_type: memory
  type: reference
  originSessionId: 125314e0-2129-4bf6-8f05-4ecf97dea917
  modified: 2026-09-26T01:36:38.016Z
---

In xLights, layer blending (e.g. "1 is True Unmask") only applies when a lower layer on the same element has an effect active at that moment (PixelBuffer.cpp GetMixedColor: `if (cnt > 0) mixColors(...)`). Otherwise the top layer renders as-is — a mask State effect shows its own (white) color in gaps.

True Unmask tests only the mask pixel's brightness (value > 0), so pure black masks everything. Fix used for ShowMathewH bats: state definition "Force Custom Colors" with each state row = #010101 (near-black passes the >0 test but is effectively off in gaps).

Related: [[test-one-sequence-first]]
