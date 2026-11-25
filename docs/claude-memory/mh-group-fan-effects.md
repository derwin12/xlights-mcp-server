---
name: mh-group-fan-effects
description: How to express MH fans as ONE group Moving Head effect (slots, offsets, sine value curves) and the unit gotchas; validated 2026-10-03
metadata:
  type: project
---

Finding: the "I Knew It" show is built from group fans, not per-head paths. Each side (heads 1-4, 5-8) is an even fan, lean = c + (slot-2.5)*offset; sides mostly identical. 35.7-49.6s is a breathing fan (offset 15-30 deg, ~5.05s period) that one group effect on "Moving Heads Group" reproduces (v4 needs 96 per-head effects there). Script: scripts/mh_group_fan_test.py (test sequence "MH Group Fan Test 4"). User validated it visually. Fan-aware converter now built into scripts/video_beams_to_xsq.py via scripts/mh_fan.py (fans tried first; static/sine/ramp-segment group effects, per-head fallback; --no-fans, --group). v5 ('I Knew It Beams v5', 20 fan spans, 1115 vs 1321 effects) validated by user as "perfect" on 2026-10-03; angle error equals v4 (0.7 deg). Next idea: generalise to shared-breakpoint group effects for symmetric (L==R in 1553 of 2345 uncovered frames) stretches; ~1088 per-head effects remain.

Gotchas (from xLights source + probes):
- Group effect: slot MH<n>_Settings drives the model whose fixture = n (MH-1..8 = fixtures 1..8). Each slot has its own "Heads:" list; position = base + (slot - centre)*offset, centre = len(heads)/2+0.5. Different slots can carry different curves (left vs right fan).
- Commas inside a slot (Heads list) must be written "&comma;" or the effect settings parse breaks (beams just vanish).
- Value curve with RV=TRUE: Sine P2 (amplitude) and P4 (centre) are real values on the +-1800 (tenths of deg) scale: P2 = 20*amp_deg - 1800, P4 = 5*centre_deg. P1 = phase % of cycle, P3 = cycles*10 (not rescaled). Custom curves are unusable inside a slot (their ';' separators collide with the slot's).
- Motor slew: a dark lead-in of 2s was too short from rest; use ~6s or beams show heads still travelling.

**Why:** these took many render iterations to find. **How to apply:** reuse when building group/fan effects or the fan-aware converter; see [[video-beam-to-moving-head-project]].
