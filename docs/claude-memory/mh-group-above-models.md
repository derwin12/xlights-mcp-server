---
name: mh-group-above-models
description: In generated MH sequences the Moving Heads Group element must be listed above the MH-n models in the master view
metadata:
  type: feedback
---

When building Moving Head sequences, list the "Moving Heads Group" element above the individual MH models (DisplayElements and ElementEffects order), not alphabetically below them.

**Why:** user asked for it while building the group-fan sequences (2026-10-03); alphabetical sorting put "MH-1.." before "Moving Heads Group".
**How to apply:** Plan(first=[group]) in scripts/prop_test_sequence.py now does this; keep it when writing new generators. See [[mh-group-fan-effects]].
