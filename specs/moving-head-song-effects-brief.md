# Brief: song-driven moving-head effects for xLights

Audience: a Claude session working in the xLights source tree. Everything below describes a **working external
implementation** (a Python script) so that the same behaviour can be built inside xLights. Nothing here has been checked against
the xLights source: where a statement is about xLights internals it is marked **(unverified)**.

Reference implementation: `add_moving_heads()` in `scripts/enhance_layout.py` of the `xlights-mcp-server` repo (commit `6d1273b`),
and `mh_effect_settings()` / `mh_settings()` / `fmt_vc()` in `scripts/video_beams_to_xsq.py`. Read those two files first; the
numbers below are copied from them.

---

## 1. What the feature does (one paragraph)

Given a sequence with audio, add a small number of **white, un-coloured** Moving Head effects to the 8 head models `MH-1`..`MH-8`
(one effect row per head, no group effects), driven by the song's **bars, sections, chorus flags and a "peak" flag**. The effects
are deliberately sparse: five kinds of move, described in section 4. Before every beam a **dark, pan/tilt-only effect with
"Link end position to next Moving Head effect"** moves the head into position so the beam never appears while the head is still
swinging in.

## 2. Non-goals (do NOT add these)

- No colour. Every head effect is white (colour wheel / colour not used, HSV 0,0,1).
- No fan/group effects, no Moving Head Group row. Each head gets its own effects.
- No pan sweeping, no patterns (the effect's Pattern tab is disabled), no path (`MHPathDef` empty).
- No change to any other model's effects.
- No DMX channel work: only the standard Moving Head effect settings.

## 3. Inputs and how they are derived

All times are milliseconds from sequence start. The reference implementation derives these from the audio with its own analysis;
inside xLights they would come from whatever beat/section data xLights has **(unverified, see section 9)**.

| Input | Meaning | How the script gets it |
|---|---|---|
| `bars[0..n]` | bar start times; `bars[i]`..`bars[i+1]` is bar `i`; `n` = number of bars. The last entry is the song end (or last bar + one bar length). | detected **downbeats**, then one extra end point |
| beat `k` of bar `i` (k = 0..3) | **NOT a detected beat.** The bar is split into 4 equal parts: `q[k] = bars[i] + (bars[i+1]-bars[i]) * k // 4`, `q[4] = bars[i+1]` | computed |
| `sections` | list of `(start_ms, end_ms, kind, energy)`; `kind` is `chorus`, `outro` or other (other = "verse") | detected song structure |
| `bar_kind[i]` | `"chorus"` if the section containing the bar start is a chorus, else the section's kind | derived |
| `bar_peak[i]` | true if the containing section's energy >= 0.9 | derived |

Notes for the implementer:
- Because beats are bar/4, a song whose bar detection is half/double speed gets half/double-speed moves. That is accepted.
- `bar_peak` uses an absolute cut-off of 0.9. It marks most choruses on some songs; relative thresholds would be better.

## 4. The five moves (the actual algorithm)

Models: `MH-1`..`MH-8`. Head index `h` = 0..7 (`h` = 0 is `MH-1`). Define the **fan position**
`fan(h) = (h - 3.5) / 3.5`, i.e. -1 for MH-1 up to +1 for MH-8. This assumes MH-1 is the **leftmost** head and MH-8 the
rightmost as seen from the front (that is true in the author's layout, **unverified for others**).

**Pose convention (very important).** Every effect uses **Pan = 90.0 degrees constant**. With pan 90 the head's beam stays in the
plane facing the viewer, and **Tilt (degrees) is then the left/right lean of the beam on screen: 0 = straight up, positive = leaning
right, negative = leaning left.** The rest pose is pan 90, tilt 0. All numbers below are tilt in degrees.

Assign each bar `i` exactly one **kind**, with this precedence (later rules override earlier ones):

1. `pool` (default for every bar)
2. `chorus` if `bar_kind[i] == "chorus"`
3. `sweep` for the bar nearest (smallest |bars[j] - section_start|) to the start of **every section except the first**
   (this overrides `chorus` for that bar)
4. `outro` for the **last two bars** (`n-2` and `n-1`) if `n >= 6` (this overrides everything)

Effects per kind (all 8 heads unless stated):

### 4.1 pool (verses and everything not otherwise claimed)
- Consecutive `pool` bars are grouped into runs; each run is cut into chunks of **2 bars** (a final odd bar is a chunk of 1).
  A run is broken whenever a non-pool bar intervenes.
- One effect per chunk per head: start = `bars[first bar of chunk]`, end = `bars[last bar of chunk + 1]`.
- Tilt: constant `fan(h) * 12` (start = end, so a static pose; a gentle spread of +-12 degrees).
- Dimmer curve points (x = fraction of effect duration, y = brightness 0..1): `(0,0) (0.5,0.6) (1,0)`, i.e. fade up to 60% and back down.

### 4.2 sweep (first bar of each new section)
- One effect per head covering the whole bar: start = `bars[i]`, end = `bars[i+1]`.
- Tilt ramps from `fan(h) * 55` to `fan(h) * 10` (wide fan collapsing to a narrow one, "outside to inside").
- Dimmer: `(0,0) (0.15,1) (0.7,1) (1,0)`.

### 4.3 chorus (ping-pong on beats)
- For each of the 4 beats `k` of the bar, the effect covers `q[k]`..`q[k+1]` (one beat).
- **Which heads fire on which beat:** a head fires on beat `k` only if `h % 2 == k % 2`. With h = 0..7 meaning MH-1..MH-8:
  beats k = 0 and 2 (beats 1 and 3) fire MH-1, MH-3, MH-5, MH-7; beats k = 1 and 3 (beats 2 and 4) fire MH-2, MH-4, MH-6, MH-8.
  The other bank is dark (no effect) on that beat.
- Tilt ramps over the beat from `fan(h)*20 - swing` to `fan(h)*20 + swing`, where `swing = +18` if `(i + k)` is even else `-18`
  (`i` = bar index). So the swing direction alternates every beat and every bar.
- Dimmer: `(0,1) (1,0)` (full to dark over the beat).
- **Exception, peak chorus:** if `bar_peak[i]` and `k == 0` (the downbeat), do NOT use the ping-pong effect. Instead **all 8 heads**
  get a burst effect from `q[0]` to `min(q[0] + 500, q[1])`, tilt 0 -> 0 (straight up), dimmer
  `(0,1) (0.12,0) (0.25,1) (0.37,0) (0.5,1) (0.62,0) (0.75,1) (1,0)` (three quick flashes, ending dark). Beats 2-4 of that bar
  are normal ping-pong.

### 4.4 outro (last two bars)
- One effect per head spanning **both** bars (`bars[n-2]` to `bars[n]`): tilt ramps from `fan(h) * 40` to `0` (converge to straight up),
  dimmer `(0,0) (0.4,0.8) (1,0)`.
- Only one effect per head is created for the two bars (not one per bar).

### 4.5 Pre-position effects (the "link" step)
After all effects for a head are collected, sort them by start time and walk them with `cursor = 0`, `tilt = 0.0` (rest pose):

```
for each effect (start, end, tilt0, tilt1, dimmer) in time order:
    if start - cursor >= 25 ms:
        emit a LINKED effect from max(cursor, start - 1000 ms) to start,
             tilt ramping from `tilt` (the previous effect's end tilt, or 0 for the first) to tilt0
             (pan 90, NO dimmer, NO colour, NO shutter), with MHLinkToNext = 1
    emit the real effect (start, end, tilt0, tilt1, dimmer)   # MHLinkToNext = 0
    cursor = end ; tilt = tilt1
```

- The lead-in is **at most 1000 ms** (`MH_PRE_MS`) and **uses the gap before the beam**: in a chorus a head fires every other beat,
  so the gap is about one beat and the pre-position effect fills it.
- If two effects touch (gap < 25 ms) no pre-position effect is made.
- The pre-position effect carries **only Pan and Tilt**. Reason found in practice: a linked effect that also had an explicit dark
  Dimmer **leaked a stray beam**. Linked effects must not set Dimmer, Color or Shutter.
- The real effects never overlap on a head (checked), so each head's row is one layer, no overlaps.
- In the author's data (This Christmas, 81 bars) this yields 728 pre-position effects and 968 real effects over the 8 heads
  (1,696 effects in total; counted from the generated file).

## 5. Parameter table (all constants in one place)

| Name | Value | Where used |
|---|---|---|
| Pan | 90.0 deg constant | every effect |
| Rest pose | pan 90, tilt 0 | start of song, initial `tilt` in the link step |
| Pool tilt | `fan(h)*12` static | 4.1 |
| Pool chunk | 2 bars | 4.1 |
| Pool dimmer | (0,0)(0.5,0.6)(1,0) | 4.1 |
| Sweep tilt | `fan(h)*55` -> `fan(h)*10` | 4.2 |
| Sweep dimmer | (0,0)(0.15,1)(0.7,1)(1,0) | 4.2 |
| Chorus tilt | `fan(h)*20 -/+ swing`, swing = +-18 | 4.3 |
| Chorus dimmer | (0,1)(1,0) | 4.3 |
| Burst length | min(500 ms, one beat) | 4.3 |
| Burst dimmer | (0,1)(.12,0)(.25,1)(.37,0)(.5,1)(.62,0)(.75,1)(1,0) | 4.3 |
| Outro tilt | `fan(h)*40` -> 0 | 4.4 |
| Outro dimmer | (0,0)(0.4,0.8)(1,0) | 4.4 |
| Outro minimum song length | `n >= 6` bars | 4.4 |
| Peak threshold | section energy >= 0.9 | 4.3 |
| Lead-in max | 1000 ms | 4.5 |
| Minimum gap for a lead-in | 25 ms (one xLights frame at 25 ms timing) | 4.5 |

## 6. Exactly what an effect looks like (the wire format)

The reference writes `.xsq` XML directly. Each effect is an `<Effect name="Moving Head" startTime=".." endTime=".." ref=".."
palette=".."/>` whose `ref` points at an `EffectDB` line (comma-separated `key=value`, keys sorted). The palette is a single white colour
(`C_BUTTON_Palette1=#FFFFFF`, checkbox 1 on, the rest off). **Settings string of a real effect** (this is MH-2, first sweep, copied
from a generated file; a single head's settings always sit in slot `MH1_Settings` with `Heads: 1`):

```
B_CHOICE_BufferStyle=Per Model Default,E_CHECKBOX_AUTO_SHUTTER=1,E_CHECKBOX_MHIgnorePan=0,E_CHECKBOX_MHIgnoreTilt=0,
E_CHECKBOX_MHLinkToNext=0,E_CHECKBOX_MHPatternEnable=0,E_CHECKBOX_MHShutterEnable=1,E_CHOICE_MHPattern=Circle,
E_NOTEBOOK1=Position,E_NOTEBOOK2=Color,E_SLIDER_MHCycles=10,E_SLIDER_MHGroupings=1,E_SLIDER_MHPan=900,
E_SLIDER_MHPanOffset=0,E_SLIDER_MHPathScale=0,E_SLIDER_MHPatternHeight=45,E_SLIDER_MHPatternPhaseOffset=0,
E_SLIDER_MHPatternRotation=0,E_SLIDER_MHPatternStartOffset=0,E_SLIDER_MHPatternWidth=90,E_SLIDER_MHPatternXOffset=0,
E_SLIDER_MHPatternYOffset=0,E_SLIDER_MHTilt=0,E_SLIDER_MHTiltOffset=0,E_SLIDER_MHTimeOffset=0,
E_TEXTCTRL_MH1_Settings=Color: 0.000000&comma;0.000000&comma;1.000000;Dimmer: 0&comma;0&comma;0.15&comma;1&comma;0.7&comma;1&comma;1&comma;0;Pan: 90.0;Tilt VC: Active=TRUE|Id=ID_VALUECURVE_MHTilt|Type=Ramp|Min=-1800.00|Max=1800.00|P1=-392.86|P2=-71.43|RV=TRUE|;PanOffset: 0.0;TiltOffset: 0.0;Groupings: 1.0;Cycles: 1.0;Heads: 1;Shutter: On,
E_TEXTCTRL_MH2_Settings=,...,E_TEXTCTRL_MH8_Settings=,E_TEXTCTRL_MHPathDef=,
T_CHECKBOX_LayerMorph=0,T_CHOICE_LayerMethod=Normal,T_SLIDER_EffectLayerMix=0
```

**The pre-position (linked) effect** differs in two ways: `E_CHECKBOX_MHLinkToNext=1`, and its slot contains only
`Pan: 90.0;Tilt VC: ...|P1=<start tilt*10>|P2=<end tilt*10>|...;Heads: 1` (no `Color`, `Dimmer`, `PanOffset`, ..., `Shutter`).

Unit notes (as observed in the generator, not looked up in xLights code):
- `E_SLIDER_MHPan` / `E_SLIDER_MHTilt` hold the angle **times 10** when the axis is static (pan 90 -> `900`). When the axis ramps the
  slider is `0` and the slot carries a **value curve**: `Type=Ramp`, `Min=-1800.00`, `Max=1800.00`, `P1`/`P2` = start/end angle **times 10**
  (tilt -39.286 deg -> `P1=-392.86`). An axis that moves less than 1 degree is written as static.
- The dimmer is a list of `x,y,x,y,...` points written with `&comma;`; x is the fraction (0..1) of the effect's duration, y is 0..1.
- Every effect carries the **complete** key set above (including the layer-blend and the `MH5`..`MH8` slots). Dropping keys makes an
  effect render in the loading xLights but break after export/import until each effect is clicked. This is an xLights file-format fact the
  author hit; the xLights implementation must write what the editor writes anyway.

## 7. Layout assumptions

- Eight models named `MH-1`..`MH-8`, type DmxMovingHeadAdv, in a roof-line row left to right, plus a model group "Moving Heads Group".
- Preview motor `SlewLimit` is 0 (no limit) on all 16 motors in the author's layout, so previews show the commanded pose instantly. Real
  heads are slow, which is why the pre-position step exists.
- Pan range / tilt range of the layout's fixtures are not queried; poses stay within pan 90 and tilt +-55, which is inside any plausible range.

## 8. What has and has not been verified

Verified:
- The `.xsq` files load in xLights and render; renders show white beams, the fan, the alternating banks and upright dark heads (stills of the
  head row checked, not frame-by-frame video).
- In a generated file, every head's effects are in time order with no overlaps, the pre-position effects have `MHLinkToNext=1`, and the real
  effects have `MHLinkToNext=0`.

NOT verified (do not assume these):
- Whether xLights actually moves the head in the preview/hardware during the linked lead-in the way I describe. The behaviour comes from the
  author's earlier work and the xLights UI label "Link end position to next Moving Head effect"; it has not been compared frame by frame.
- Whether the chosen tilt amounts look good on real hardware. They were only judged in previews.
- The "peak" and "chorus" decisions are only as good as the author's own audio analysis.
- The 25 ms and 1000 ms constants are untested for other tempos.

## 9. Questions the xLights-side session must answer first (these decide the shape of the work)

1. **Where should this live?** Options: a new effect type, a sequence-level "generate" command on a selected set of models, or a Lua
   script (if xLights scripting can add effects to a sequence **(unverified)**). Pick one before writing code.
2. **What song data does xLights already have?** The script needs bar starts (downbeats), a section list with chorus/verse/outro labels,
   and a section energy. Does xLights expose these (timing tracks from Vamp/other analysis, section markers)? If not, the feature should take
   user-chosen timing tracks as inputs (a bars track, a sections track with labels) instead of analysing audio itself.
3. **How does the code represent a Moving Head effect and the link-to-next flag?** The generated settings strings above should be reproducible
   by calling the same code the editor uses, not by writing strings by hand.
4. **How should "head index" -> left-to-right order be defined?** The script assumes MH-1 is leftmost. xLights could use the model's X position
   instead of its name.
5. **Which values should be user options?** Candidates: tilt amounts (12/55/10/20/18/40), dimmer curves, lead-in length (1000 ms), peak
   threshold, which head banks alternate.

## 10. Acceptance checks for any implementation

Given a sequence with N bars and the sections described:
1. Every head row contains only `Moving Head` effects, none overlapping.
2. Every real effect has `Pan = 90`, a white colour, and one of the five shapes in section 4; the last two bars have exactly one outro effect per head.
3. In chorus bars, on beat `k`, only heads with `h % 2 == k % 2` have an effect (except on a peak chorus downbeat, where all 8 do).
4. Every real effect that starts >= 25 ms after the previous one ended is immediately preceded by a linked, pan/tilt-only effect that ends exactly
   where the real effect starts and is at most 1000 ms long.
5. No linked effect contains a Dimmer, Color or Shutter entry.
6. A head with no effect in a stretch is dark (no beam) in the preview.
7. Output for the reference song (`F:\ShowFolderAI\Eclipse6-This-Christmas.xsq`, 81 bars, 13 sections, 89 BPM) has 728 linked effects over the 8 heads when
   run with the reference script; an xLights implementation should be close, but exact equality depends on the bars/sections it is given.
