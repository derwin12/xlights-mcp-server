"""Convert a beam timeline (from video_beam_analysis.py) into a Moving Head .xsq.

Calibration (see mh_calibration_sequence.py): a head seen by a fixed front camera shows a lean
from vertical of atan(tan(tilt) * sin(pan)); with pan held at 90 deg, tilt equals the lean
(positive = right). A single camera cannot tell which pan/tilt pair produced a lean, so pan is a
free choice: --pan-mode fixed keeps 90 deg, --pan-mode lean swivels pan with the beam
(pan = 90 - gain * lean) and solves tilt so the on-screen lean is unchanged.

Per head the lean timeline is smoothed, split into runs (beam on, same color) and simplified
into linear segments; each segment becomes one Moving Head effect with Pan/Tilt ramps.

Usage:
    python scripts/video_beams_to_xsq.py BEAMS.json "Sequence Name" [--show F:/ShowFolderAI]
        [--models MH-1,...,MH-8 (default: MH-1..8 for 8 heads, MH-2..7 for 6)] [--tolerance 2.0] [--pan-mode fixed|lean] [--pan-gain 0.8]
"""
import argparse
import colorsys
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import prop_test_sequence as pts  # noqa: E402  (reuses its .xsq writer)

PAN = 90.0
FRAME_MS = 25  # xLights sequence timing
MIN_SEG_MS = 100
MAX_BRIDGE_S = 0.2  # longest lone beam dropout (s) treated as detector noise and bridged
SHIMMER_GAPS = 2  # this many other gaps within SHIMMER_WINDOW_S makes a gap part of a shimmer, not noise
SHIMMER_WINDOW_S = 0.6
SHIMMER_MAX_GAP_S = 0.3  # longest gap that can belong to a shimmer
MAX_TILT = 90.0
PRE_POSITION_MS = 1500  # orient mode: dark head moves to the next beam's pose this long before it
STEER_TILT = 45.0  # --pan-mode steer: tilt held here (rises only when a wide lean needs it)
HIDDEN_LENS_MODE = "edge"  # what a hidden lens means: "edge" (head sideways) or "away" (turned from the camera)
HIDDEN_LENS = 0.12  # share of the beam toward the camera below which the lens counts as hidden
LENS_FULL = 0.115  # lens fraction (video_head_facing.py) when the lens faces the camera head-on
STEER_PAN_LIMIT = 60.0  # deg: pan never needs to exceed this
STROBE_DIMMER_POINTS = 400  # a strobe needs a dimmer point per flicker, not the usual 8
DARK_DIMMER = "Dimmer: 0.0&comma;0.0&comma;1.0&comma;0.0"


def median_filter(a, k=5):
    pad = k // 2
    p = np.pad(a, pad, mode="edge")
    return np.array([np.median(p[i:i + k]) for i in range(len(a))])


def douglas_peucker(xs, ys, eps):
    """Indices of a piecewise-linear simplification of (xs, ys) within eps (vertical error)."""
    keep = {0, len(xs) - 1}
    stack = [(0, len(xs) - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        t = (xs[a + 1:b] - xs[a]) / (xs[b] - xs[a])
        if ys.ndim > 1:
            t = t[:, None]
        err = np.abs(ys[a + 1:b] - (ys[a] + t * (ys[b] - ys[a])))
        if ys.ndim > 1:
            err = err.max(axis=1)  # worst channel decides
        i = int(err.argmax())
        if err[i] > eps:
            m = a + 1 + i
            keep.add(m)
            stack += [(a, m), (m, b)]
    return sorted(keep)


def hue_class(rgb):
    """-1 = white/grey, else hue bucket (30 deg)."""
    r, g, b = (c / 255 for c in rgb)
    h, s, _ = colorsys.rgb_to_hsv(r, g, b)
    return -1 if s < 0.25 else int(h * 360 // 30) % 12


def build_runs(frames, head, ref):
    """Yield runs of consecutive on-frames sharing a color class: dict of arrays."""
    t = np.array([f["t"] for f in frames])
    on = np.array([f["heads"][head] is not None for f in frames])
    ang = np.array([f["heads"][head]["angle"] if on[i] else 0.0 for i, f in enumerate(frames)])
    inten = np.array([f["heads"][head]["intensity"] if on[i] else 0.0 for i, f in enumerate(frames)])
    rgbs = [f["heads"][head]["rgb"] if on[i] else [0, 0, 0] for i, f in enumerate(frames)]
    # A beam flickering on/off every other frame is a strobe, not detector noise: its dark frames
    # keep zero intensity (the dimmer curve reproduces the flicker) instead of being bridged.
    strobe = np.zeros(len(on), bool)
    for i in range(3, len(on) - 3):
        if not on[i] and on[i - 1] and on[i + 1] and (
                (not on[i + 2] and on[i + 3]) or (not on[i - 2] and on[i - 3])):
            strobe[i] = True
    # Dropouts. A beam does not go dark for a few frames unless it shimmers, so a lone gap up to MAX_BRIDGE_S is
    # the detector missing a faint frame and is bridged. Short gaps that repeat (SHIMMER_GAPS others within
    # SHIMMER_WINDOW_S, each up to SHIMMER_MAX_GAP_S) are a shimmer: the run stays one continuous beam whose dark
    # frames get zero intensity, so the dimmer curve reproduces the on/off pattern (the 1-frame strobe is the same).
    gaps, i = [], 1
    while i < len(on) - 1:
        if not on[i] and on[i - 1]:
            j = i
            while j < len(on) and not on[j]:
                j += 1
            if j < len(on):
                gaps.append((i, j))
            i = j
        else:
            i += 1
    short = [g for g in gaps if t[g[1]] - t[g[0] - 1] <= SHIMMER_MAX_GAP_S + 1e-6]
    starts = np.array([t[g[0]] for g in short])
    for i, j in gaps:
        dur = t[j] - t[i - 1]
        near = int((np.abs(starts - t[i]) <= SHIMMER_WINDOW_S).sum()) - 1 if dur <= SHIMMER_MAX_GAP_S + 1e-6 else 0
        shimmer = near >= SHIMMER_GAPS
        if shimmer:
            strobe[i:j] = True
        if j - i <= 2 or shimmer or dur <= MAX_BRIDGE_S + 1e-6:
            for k in range(i, j):
                w = (k - i + 1) / (j - i + 1)
                ang[k] = ang[i - 1] * (1 - w) + ang[j] * w
                inten[k] = 0.0 if strobe[k] else inten[i - 1] * (1 - w) + inten[j] * w
                rgbs[k] = rgbs[i - 1]
                on[k] = True
    cls = median_filter(np.array([hue_class(c) if o else -2 for c, o in zip(rgbs, on)], float), 5)
    runs, i = [], 0
    while i < len(on):
        if not on[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(on) and on[j + 1] and cls[j + 1] == cls[i]:
            j += 1
        sl = slice(i, j + 1)
        runs.append({"t": t[sl], "ang": median_filter(ang[sl], 5), "int": inten[sl] / ref,
                     "rgb": np.array(rgbs[sl], float), "w": inten[sl], "strobe": strobe[sl]})
        i = j + 1
    return runs, t


def fmt_vc(axis, a0, a1):
    return (f"{axis} VC: Active=TRUE|Id=ID_VALUECURVE_MH{axis}|Type=Ramp|Min=-1800.00|Max=1800.00|"
            f"P1={a0 * 10:.2f}|P2={a1 * 10:.2f}|RV=TRUE|")


def merge_short_segments(t, idx, min_ms):
    """Drop path vertices so every segment lasts at least min_ms; the neighbours absorb the short ones.

    Dropping a short segment outright would leave a hole inside a beam that the gap fill turns into a
    dark effect, which shows as a flicker where the source beam stays lit.
    """
    keep = [idx[0]]
    for i in idx[1:-1]:
        if (t[i] - t[keep[-1]]) * 1000 >= min_ms:
            keep.append(i)
    if len(keep) > 1 and (t[idx[-1]] - t[keep[-1]]) * 1000 < min_ms:
        keep.pop()  # short tail: fold it into the previous segment
    keep.append(idx[-1])
    return keep


def yoke_to_cos(spread):
    """|cos pan| from the yoke spread (arms ~10 px out = 1, hidden arch ~3.6 = 0); NaN where it was not measurable."""
    spread = np.asarray(spread, float)
    return np.where(spread < 0, np.nan, np.clip((spread - YOKE_ARCH) / (YOKE_ARMS - YOKE_ARCH), 0.0, 1.0))


# candidate pans; 0 is handled apart. Out to +-175 (the layout pan range is +-180): a head turning from facing the camera through
# sideways to facing away keeps rotating the same way (pan 85 -> 135), where a -90..90 range could only flip to pan -80 / tilt -59.
PAN_STATES = np.array(sorted({*np.arange(-175.0, 176.0, 5.0), -2.5, 2.5} - {0.0}))
YOKE_ARCH = 3.6  # yoke spread (video_head_facing.py) of a head turned sideways: arms hidden
YOKE_ARMS = 10.4  # ... and with the arms either side of the head (pan ~0 or 180)
YOKE_WEIGHT = 1.0  # weight of the |cos pan| match in the pan path
AWAY_LEAN_FULL = 12.0  # --hidden away: lean (deg) up to which a hidden lens means turned fully away
AWAY_LEAN_EDGE = 30.0  # ... and from which it means turned sideways
TILT_PRIOR = 0.06  # cost of tilt^2 (fraction of 90 deg squared) in the pan path
TILT_SOFT_LIMIT = 65.0  # deg: beyond this the tilt cost climbs steeply
GROUP_WEIGHT = 0.1  # pull of a head's pan toward the group's median pan (per 90 deg squared) while its readings match the group's
GROUP_LEAN_TOL = 15.0  # deg: lean, and lens share / yoke |cos pan| (GROUP_SHARE_TOL), within which a head counts as doing what the group does
GROUP_SHARE_TOL = 0.25
GROUP_MIN_HEADS = 3
PAN_JUMP = 0.5  # cost of a pan change over PAN_JUMP_DEG within one video frame (25 ms): the motors cannot do it, so it is a mirror-pose flip ((p, t) and (p +- 180, -t) show the same lean and lens share)
PAN_JUMP_DEG = 45.0
PAN_START_BACK = 0.05  # a run's first frame starts on the front pose unless the data clearly says turned away (the mirror pose is a coin toss otherwise)
PAN_LAMBDA = 0.04  # cost of a 90 deg pan change, in squared lens-share units: a pan moves only when the lens data clearly asks


def viterbi_pose(lean, r, c=None, group=None):
    """Per-frame (pan, tilt) from the lean, the lens share r (0..1 toward the camera) and the yoke |cos pan| c, as one smooth path.

    c (from the yoke arms, see yoke_to_cos) is the strongest pan cue: arms either side of the head mean pan ~0/180, a hidden
    arch means pan ~90. With c the hidden-lens heuristics (edge/away) are not needed: a hidden lens just means bc ~ 0.

    Beam unit vector (right, toward camera, up) = (sin t sin p, sin t cos p, cos t). For a candidate pan p the
    lean fixes the tilt (tan t = tan L / sin p) and so predicts the toward-camera share bc = sin t cos p; the
    state whose bc best matches r wins, but changing pan costs PAN_LAMBDA per 90 deg, so noise in r around the
    hidden threshold cannot flip the head between two poses (a flip is a 180 deg swing the motors cannot follow).
    group = (pan array, weight array) pulls the path toward the other heads' median pan where they are doing the same thing.
    A hidden lens means bc ~ 0 (head sideways; HIDDEN_LENS_MODE "edge") or bc <= 0 (turned away; "away").
    """
    n, K = len(lean), len(PAN_STATES)
    L = np.radians(np.clip(lean, -80.0, 80.0))
    P = np.radians(PAN_STATES)
    t = np.arctan(np.tan(L)[:, None] / np.sin(P)[None, :])  # n x K, tilt per candidate pan
    bc = np.sin(t) * np.cos(P)[None, :]
    # extra state: pan 0, only for a vertical beam, where the lean does not fix the tilt (lens share does)
    use_yoke = c is not None
    away = (not use_yoke) and HIDDEN_LENS_MODE == "away" and (r < HIDDEN_LENS)
    # upright (tilt 0) is the natural pose of a hidden-lens head with its arms showing and a vertical beam
    t0 = np.where(away, -np.radians(STEER_TILT), np.where(use_yoke & (r < HIDDEN_LENS), 0.0, np.arcsin(np.clip(r, 0.0, 1.0))))
    t = np.concatenate([t, t0[:, None]], axis=1)
    bc = np.concatenate([bc, np.sin(t0)[:, None]], axis=1)
    pans = np.concatenate([PAN_STATES, [0.0]])
    vis = r[:, None]
    if use_yoke:
        hid = (r < HIDDEN_LENS)[:, None]
        D = np.where(hid, 0.5 * bc ** 2 + 10 * np.maximum(bc - 0.03, 0.0) ** 2,
                     (np.maximum(bc, 0.0) - vis) ** 2 + 10 * np.maximum(-bc - 0.03, 0.0) ** 2)
        cp = np.abs(np.cos(np.radians(pans)))[None, :]
        cc = np.asarray(c, float)[:, None]
        D = D + YOKE_WEIGHT * np.where(np.isnan(cc), 0.0, (cp - cc) ** 2)
    elif HIDDEN_LENS_MODE == "away":
        # A hidden lens means turned away (yoke arms showing) for a near-vertical beam, and turned sideways (the arch,
        # arms hidden) once the lean is steep: the target toward-camera share goes from -sin(steer tilt) to 0 as
        # |lean| grows from AWAY_LEAN_FULL to AWAY_LEAN_EDGE.
        blend = np.clip((np.abs(np.degrees(L)) - AWAY_LEAN_FULL) / (AWAY_LEAN_EDGE - AWAY_LEAN_FULL), 0.0, 1.0)
        target = (-np.sin(np.radians(STEER_TILT)) * (1.0 - blend))[:, None]
        hid = (r < HIDDEN_LENS)[:, None]
        D = np.where(hid, (bc - target) ** 2,
                     (np.maximum(bc, 0.0) - vis) ** 2 + 10 * np.maximum(-bc - 0.03, 0.0) ** 2)
    else:
        D = (np.maximum(bc, 0.0) - vis) ** 2 + 10 * np.maximum(-bc - 0.03, 0.0) ** 2
    # Extreme tilts (head nearly horizontal, pointing straight at or away from the camera) are physically odd and, with
    # fast motors, visibly wrong; without this the smooth-pan cost makes a steep lean from pan ~0 with tilt ~-85.
    ta = np.abs(t) / (np.pi / 2)
    D = D + 10.0 * (np.abs(t) > np.radians(MAX_TILT - 1.0)) + 1e-3 * ta + TILT_PRIOR * ta ** 2         + 0.5 * np.maximum(np.abs(np.degrees(t)) - TILT_SOFT_LIMIT, 0.0) ** 2 / 15.0 ** 2
    if group is not None:
        gp, gw = group
        gp = np.nan_to_num(np.asarray(gp, float))[:, None]
        D = D + GROUP_WEIGHT * np.asarray(gw, float)[:, None] * ((pans[None, :] - gp) / 90.0) ** 2
    D[:, -1] += 10.0 * (np.abs(np.degrees(L)) > 2.0)  # pan 0 cannot lean
    dpan = np.abs(pans[:, None] - pans[None, :])
    trans = PAN_LAMBDA * dpan / 90.0 + PAN_JUMP * (dpan > PAN_JUMP_DEG)
    D[0] += PAN_START_BACK * (np.abs(pans) > 90.0)
    cost, back = D[0].copy(), np.zeros((n, K + 1), dtype=int)
    for i in range(1, n):
        cand = cost[:, None] + trans
        back[i] = cand.argmin(0)
        cost = D[i] + cand.min(0)
    path = np.empty(n, dtype=int)
    path[-1] = cost.argmin()
    for i in range(n - 1, 0, -1):
        path[i - 1] = back[i][path[i]]
    return pans[path], np.degrees(t[np.arange(n), path])


def steer_pose(lean):
    """Tilt held near STEER_TILT with pan steering the beam (rising only for wide leans)."""
    need = np.degrees(np.arctan(np.tan(np.radians(np.abs(lean))) / np.sin(np.radians(STEER_PAN_LIMIT))))
    tilt = np.minimum(np.maximum(STEER_TILT, need), MAX_TILT)
    pan = np.degrees(np.arcsin(np.clip(np.tan(np.radians(lean)) / np.tan(np.radians(tilt)), -1.0, 1.0)))
    return pan, tilt


def pose_from_lean(lean, mode, gain, toward=None, yoke_cos=None, group=None):
    """(pan, tilt) arrays in degrees that show the given on-screen lean to a front camera.

    toward (orient mode): per-frame 0..1 share of the beam that points at the camera, read from how
    much of the head's lens shows (video_head_facing.py); see viterbi_pose.
    """
    lean = np.clip(lean, -80.0, 80.0)
    if mode == "fixed":
        return np.full_like(lean, PAN), lean
    if mode == "orient" and toward is not None:
        return viterbi_pose(lean, np.clip(toward, 0.0, 1.0), yoke_cos, group)
    if mode in ("steer", "orient"):
        # Tilt is held near STEER_TILT and pan steers the beam: lean = atan(tan(tilt) * sin(pan)).
        # The yoke arms then show on both sides of the lens, as on a PixelPro-style rig, instead of
        # hiding behind the head at pan 90. A beam cannot lean past the tilt, so the tilt rises just
        # enough that pan stays within +-STEER_PAN_LIMIT.
        need = np.degrees(np.arctan(np.tan(np.radians(np.abs(lean))) / np.sin(np.radians(STEER_PAN_LIMIT))))
        tilt = np.minimum(np.maximum(STEER_TILT, need), MAX_TILT)
        pan = np.degrees(np.arcsin(np.clip(np.tan(np.radians(lean)) / np.tan(np.radians(tilt)), -1.0, 1.0)))
        return pan, tilt
    pan = np.clip(PAN - gain * lean, 30.0, 150.0)
    tilt = np.degrees(np.arctan(np.tan(np.radians(lean)) / np.sin(np.radians(pan))))
    return pan, np.clip(tilt, -MAX_TILT, MAX_TILT)


def fmt_dimmer(ts, ys, max_points=8, grid=None):
    """Dimmer curve points as "Dimmer: x,y,x,y,...".

    By default the curve is stretched over the first-to-last frame. grid: the effect's own frame
    times (s) for frame-exact curves (strobes): xLights samples a curve at frame j of N at
    x = j / (N - 1), so the intensity is resampled onto those frames and placed at those x.
    """
    if grid is not None:
        ys = np.interp(grid, ts, ys)
        x = np.arange(len(grid)) / max(len(grid) - 1, 1)
    else:
        x = (ts - ts[0]) / max(ts[-1] - ts[0], 1e-6)
    idx = douglas_peucker(x, ys, 0.06)
    flat = []
    for i in idx[:max_points]:
        flat += [f"{x[i]:.4f}", f"{min(max(ys[i], 0.0), 1.0):.4f}"]
    return "Dimmer: " + "&comma;".join(flat)


def _axis(axis, a0, a1):
    """Settings text and slider value for one axis: static if it barely moves, else a ramp."""
    if abs(a1 - a0) < 1.0:
        mid = (a0 + a1) / 2
        return f"{axis}: {mid:.1f}", int(mid * 10)
    return fmt_vc(axis, a0, a1), 0


def mh_settings(p0, p1, t0, t1, color_hsv, dimmer, lit=True, link=False):
    pan_cmd, pan_slider = _axis("Pan", p0, p1)
    tilt_cmd, tilt_slider = _axis("Tilt", t0, t1)
    h, s, v = color_hsv
    slot = (f"Color: {h:.6f}&comma;{s:.6f}&comma;{v:.6f};{dimmer};{pan_cmd};{tilt_cmd};"
            "PanOffset: 0.0;TiltOffset: 0.0;Groupings: 1.0;Cycles: 1.0;Heads: 1" + (";Shutter: On" if lit else ""))
    return ("B_CHOICE_BufferStyle=Per Model Default,E_CHECKBOX_MHIgnorePan=0,E_CHECKBOX_MHIgnoreTilt=0,"
            "E_NOTEBOOK1=Position,E_NOTEBOOK2=Color,E_SLIDER_MHCycles=10,E_SLIDER_MHGroupings=1,"
            f"E_SLIDER_MHPan={pan_slider},E_SLIDER_MHPanOffset=0,E_SLIDER_MHPathScale=0,"
            f"E_SLIDER_MHTilt={tilt_slider},E_SLIDER_MHTiltOffset=0,E_SLIDER_MHTimeOffset=0,"
            + ("E_CHECKBOX_MHLinkToNext=1," if link else "")
            + f"E_TEXTCTRL_MH1_Settings={slot}")


def snap(ms):
    return int(round(ms / FRAME_MS)) * FRAME_MS


def add_beats(plan, audio, total_ms):
    """Add a 'Beats' timing track (1-2-3-4 by bar) from beat detection on the audio."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from xlights_mcp.audio.beats import detect_beats

    bm = detect_beats(audio)
    beats = bm.beat_times_ms
    downs = set(bm.downbeat_times_ms)
    pos = 0
    for i, b in enumerate(beats):
        pos = 1 if b in downs else (pos % bm.beats_per_bar) + 1
        end = beats[i + 1] if i + 1 < len(beats) else min(b + 500, total_ms)
        if b < total_ms:
            plan.label("Beats", str(pos), b, min(end, total_ms))
    print(f"beats: {len(beats)} at {bm.tempo:.0f} BPM")


def set_media(xsq, audio):
    """Point the sequence at its audio file and mark it as a media sequence."""
    import xml.etree.ElementTree as ET

    # xLights resolves a relative mediaFile against the show folder; a missing file leaves the open
    # sequence waiting on a media prompt (renders hang), so always store an absolute, existing path.
    audio = Path(audio).resolve()
    if not audio.is_file():
        sys.exit(f"audio file not found: {audio}")
    tree = ET.parse(xsq)
    head = tree.getroot().find("head")
    head.find("mediaFile").text = str(audio)
    head.find("sequenceType").text = "Media"
    ET.indent(tree, space="  ")
    with open(xsq, "w", encoding="UTF-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(f, encoding="unicode", xml_declaration=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("beams")
    ap.add_argument("name")
    ap.add_argument("--show", default="F:/ShowFolderAI")
    ap.add_argument("--models", help="one MH model per detected head, left to right (default: MH-1..MH-8 for 8 heads; "
                    "the middle six, MH-2..MH-7, for 6 heads)")
    ap.add_argument("--audio", help="audio file (video's soundtrack, aligned to video t=0): sets the "
                    "sequence media file and adds a Beats timing track")
    ap.add_argument("--pan-mode", choices=["fixed", "lean", "steer", "orient"], default="fixed",
                    help="fixed: pan 90 deg, tilt = lean; lean: pan swivels with the beam; steer: tilt held near "
                         "--steer-tilt and pan steers the beam (heads look like the source's, yoke arms visible). "
                         "steer disables group fans, which are tilt fans at pan 90; orient: pan and tilt from the lean plus "
                         "how much of each head's lens shows (--facing from video_head_facing.py)")
    ap.add_argument("--hidden", choices=["edge", "away"], default="edge",
                    help="orient mode: a head with no lens showing is turned sideways (edge: arch, the Doors/Dolly) "
                         "or away from the camera with its yoke arms showing (away: Fireflies)")
    ap.add_argument("--facing", help="orient mode: JSON from video_head_facing.py (lens visibility per head and frame)")
    ap.add_argument("--steer-tilt", type=float, default=STEER_TILT, help="steer mode: base tilt in deg (default 45)")
    ap.add_argument("--steer-pan-limit", type=float, default=STEER_PAN_LIMIT,
                    help="steer mode: widest pan in deg; tilt rises to keep pan within it (default 60)")
    ap.add_argument("--pan-gain", type=float, default=0.8, help="deg of pan per deg of lean (lean mode)")
    ap.add_argument("--tolerance", type=float, default=2.0, help="max angle error (deg) per segment")
    ap.add_argument("--group", default="Moving Heads Group",
                    help="model group holding MH-1..MH-8 (fixtures 1-8): uniform fans become group effects")
    ap.add_argument("--no-group", action="store_true", help="orient mode: do not pull each head's pan toward the group's")
    ap.add_argument("--no-fans", action="store_true", help="skip fan detection; per-head effects only")
    ap.add_argument("--fan-banks", help="heads fanned together, left to right, e.g. 4,4 or 6 or 3,3 (default: 4,4 for 8 "
                                        "heads, otherwise every head in one bank)")
    args = ap.parse_args()
    globals().update(STEER_TILT=args.steer_tilt, STEER_PAN_LIMIT=args.steer_pan_limit, HIDDEN_LENS_MODE=args.hidden)

    data = json.load(open(args.beams))
    frames = data["frames"]
    facing = None
    if args.pan_mode == "orient":
        if not args.facing:
            sys.exit("--pan-mode orient needs --facing FILE (python scripts/video_head_facing.py VIDEO OUT.json)")
        fdata = json.load(open(args.facing))
        yoke = yoke_to_cos(np.array(fdata["yoke"])) if fdata.get("yoke") else None  # |cos pan| per frame/head
        if yoke is None:
            print("note: the facing file has no yoke data; falling back to lens-only pans (re-run video_head_facing.py)")
        facing = (np.array(fdata["lens"]), fdata["fps"], yoke)
    nheads = len(frames[0]["heads"])
    if args.models:
        models = args.models.split(",")
    else:  # centre the heads on the 8-head rig when the video shows fewer
        first = (8 - nheads) // 2 + 1 if nheads < 8 else 1
        models = [f"MH-{i}" for i in range(first, first + nheads)]
    assert len(models) == nheads, f"{nheads} heads in timeline but {len(models)} models given"
    t0 = frames[0]["t"]
    frame_dt = 1.0 / data["fps"]

    plan = pts.Plan(first=[args.group])  # group above the MH models in the master view
    n_eff = 0
    refs = []
    for h in range(nheads):
        ints = [f["heads"][h]["intensity"] for f in frames if f["heads"][h]]
        refs.append(float(np.percentile(ints, 95)) if ints else 1.0)

    # Uniform fans (every bank of heads fanned evenly at once) become group effects; their
    # frames are then hidden from the per-head pass, which only pre-positions heads for them.
    fans = []
    nums = [re.search(r"(\d+)$", name) for name in models]  # MH-n is fixture n in the group effect
    fixtures = [int(m.group(1)) for m in nums] if all(nums) else []
    import mh_fan
    banks = (mh_fan.parse_banks(args.fan_banks, nheads) if args.fan_banks else mh_fan.default_banks(nheads))
    if args.pan_mode in ("steer", "orient") and not args.no_fans:
        print(f"{args.pan_mode} mode: group fans are tilt fans at pan 90, so they are skipped (per-head effects only)")
    if not args.no_fans and args.pan_mode not in ("steer", "orient") and banks and len(fixtures) == nheads:
        T = np.array([f["t"] for f in frames])
        A = np.array([[h["angle"] if h else np.nan for h in f["heads"]] for f in frames])
        I = np.array([[h["intensity"] / refs[k] if h else np.nan for k, h in enumerate(f["heads"])]
                      for f in frames])
        RGB = np.array([[h["rgb"] if h else [np.nan] * 3 for h in f["heads"]] for f in frames], float)
        mean_rgb = np.nan_to_num(np.nanmean(RGB, axis=1)) if len(frames) else RGB
        cls = median_filter(np.array([hue_class(c) for c in mean_rgb], float), 5)
        for i0, i1 in mh_fan.detect_spans(A, data["fps"], banks, cls):
            fans.append((i0, i1, mh_fan.plan_span(T, A, I, RGB, i0, i1, t0, frame_dt, args.tolerance, banks, fixtures)))
        for i0, i1, _ in fans:
            for f in frames[i0:i1 + 1]:
                f["heads"] = [None] * nheads
        for _, _, fp in fans:
            for s_ms, e_ms, slots in fp["effects"]:
                plan.add(args.group, "Moving Head", s_ms, e_ms, mh_fan.group_settings(slots), ["#FFFFFF"])
                n_eff += 1
        covered = sum(i1 - i0 + 1 for i0, i1, _ in fans)
        kinds = {k: sum(1 for *_, fp in fans if fp["kind"] == k) for k in ("static", "sine", "ramps")}
        print(f"fans: {len(fans)} spans ({kinds}), {covered / data['fps']:.1f}s of {len(frames) / data['fps']:.1f}s "
              f"-> {sum(len(fp['effects']) for *_, fp in fans)} group effects")

    def run_features(h, r):
        """(facing-frame index, lens share, yoke |cos pan|) of a run of head h; the last two are None without a facing file."""
        if facing is None:
            return None, None, None
        lens, ffps, yoke = facing
        idx_f = np.clip(np.round(r["t"] * ffps).astype(int), 0, len(lens) - 1)
        toward, yoke_cos = median_filter(lens[idx_f, h] / LENS_FULL, 9), None
        if yoke is not None:  # yoke arms: the direct pan cue; fill unmeasured frames from the last good value
            yc = yoke[idx_f, h].copy()
            good = ~np.isnan(yc)
            if good.any():
                yc = np.interp(np.arange(len(yc)), np.nonzero(good)[0], yc[good])
                yoke_cos = median_filter(yc, 9)
        return idx_f, toward, yoke_cos

    # Heads often do the same move together. A first pass poses every head alone; the median pan of the heads whose
    # readings (lean, lens, yoke) agree with the group's median then pulls each head's second pass toward it, so a
    # noisy head follows its neighbours instead of picking the mirror pose.
    group_pan = group_w = None
    all_runs = [build_runs(frames, h, refs[h])[0] for h in range(nheads)]
    if args.pan_mode == "orient" and facing is not None and facing[2] is not None and nheads >= GROUP_MIN_HEADS and not args.no_group:
        nf = len(facing[0])
        PAN1, LEAN, SHARE, COS = (np.full((nheads, nf), np.nan) for _ in range(4))
        for h in range(nheads):
            for r in all_runs[h]:
                idx_f, toward, yoke_cos = run_features(h, r)
                if yoke_cos is None:
                    continue
                pan1, _ = pose_from_lean(r["ang"], "orient", args.pan_gain, toward, yoke_cos)
                PAN1[h, idx_f], LEAN[h, idx_f], SHARE[h, idx_f], COS[h, idx_f] = pan1, r["ang"], toward, yoke_cos
        # peers of head h at a frame: the other heads whose lean, lens and yoke readings are all within tolerance of h's
        # own (so the two halves of a symmetric fan never pull on each other); the pull needs GROUP_MIN_HEADS - 1 of them
        group_pan, group_w = np.full((nheads, nf), np.nan), np.zeros((nheads, nf))
        for h in range(nheads):
            peers = np.stack([(np.abs(LEAN[j] - LEAN[h]) <= GROUP_LEAN_TOL) & (np.abs(SHARE[j] - SHARE[h]) <= GROUP_SHARE_TOL)
                              & (np.abs(COS[j] - COS[h]) <= GROUP_SHARE_TOL) if j != h else np.zeros(nf, bool) for j in range(nheads)])
            with np.errstate(all="ignore"):
                med = np.nanmedian(np.where(peers, PAN1, np.nan), axis=0)
            ok = peers.sum(0) >= GROUP_MIN_HEADS - 1
            group_pan[h], group_w[h] = np.where(ok, med, np.nan), ok.astype(float)
        print(f"group pull: {100 * group_w[np.isfinite(PAN1)].mean():.0f}% of lit head-frames have {GROUP_MIN_HEADS - 1}+ peers doing the same")

    for h, model in enumerate(models):
        ref = refs[h]
        runs = all_runs[h]
        segs = []  # (start_ms, end_ms, pan0, pan1, tilt0, tilt1, hsv, dimmer)
        for r in runs:
            t = r["t"]
            idx_f, toward, yoke_cos = run_features(h, r)  # lens share toward the camera and yoke |cos pan|, smoothed
            group = (group_pan[h][idx_f], group_w[h][idx_f]) if group_pan is not None else None
            pan, tilt = pose_from_lean(r["ang"], args.pan_mode, args.pan_gain, toward, yoke_cos, group)
            pose = np.stack([pan, tilt], axis=1)
            idx = douglas_peucker(t, pose, args.tolerance) if len(t) > 2 else [0, len(t) - 1]
            idx = merge_short_segments(t, idx, MIN_SEG_MS)
            w = r["w"]
            sel = w >= 0.5 * w.max()
            mean_rgb = (r["rgb"][sel] * w[sel, None]).sum(0) / w[sel].sum()
            hh, ss, _ = colorsys.rgb_to_hsv(*(c / 255 for c in mean_rgb))
            ss = 0.0 if ss < 0.25 else min(ss, 1.0)
            for a, b in zip(idx[:-1], idx[1:]):
                start = snap((t[a] - t0) * 1000)
                end = snap((t[b] - t0 + (frame_dt if b == idx[-1] and b == len(t) - 1 else 0)) * 1000)
                if end - start < MIN_SEG_MS:
                    continue
                sl = slice(a, b + 1)
                cap = STROBE_DIMMER_POINTS if r["strobe"][sl].any() else 8
                grid = (t0 + start / 1000 + np.arange((end - start) // FRAME_MS) * FRAME_MS / 1000) if cap > 8 else None
                dimmer = (fmt_dimmer(t[sl], r["int"][sl], cap, grid) if b > a
                          else "Dimmer: 0.0&comma;1.0&comma;1.0&comma;1.0")
                segs.append((start, end, pan[a], pan[b], tilt[a], tilt[b], (hh, ss, 1.0), dimmer, True))
        # A fan span owns this head's time but is emitted as a group effect: keep it as a
        # placeholder so the gaps around it park the head at the fan's start/end pose.
        for *_, fp in fans:
            segs.append((fp["start_ms"], fp["end_ms"], PAN, PAN, fp["start_tilt"][h], fp["end_tilt"][h],
                         fp["hsv"], DARK_DIMMER, False))
        segs.sort(key=lambda sg: sg[:2])
        # Fill dark gaps with a dimmed effect that pre-positions the head at the next beam's
        # start angle: the motors have a slew limit, so an unaddressed head would still be
        # swinging when the next beam appears.
        total_ms = snap((frames[-1]["t"] - t0 + frame_dt) * 1000)
        filled, cursor, prev = [], 0, (PAN, 0.0)
        for seg in segs + [(total_ms, total_ms, None, None, None, None, None, None, False)]:
            if seg[0] - cursor >= FRAME_MS:
                pp, tt = prev if seg[2] is None else (seg[2], seg[4])
                hsv_gap = seg[6] or (0.0, 0.0, 1.0)
                link = seg[2] is not None and seg[8]
                split = seg[0]  # end of the part parked the way the source looks while dark
                if facing is not None and seg[2] is not None and seg[0] - cursor > PRE_POSITION_MS:
                    # orient mode: while dark the head parks the way the source head looks (same lean as the
                    # next beam, turned toward or away from the camera as seen in the gap) ...
                    lens, ffps, yoke = facing
                    gi = np.clip(np.round(np.arange(cursor, seg[0], FRAME_MS) / 1000.0 * ffps).astype(int), 0, len(lens) - 1)
                    lean_n = float(np.degrees(np.arctan(np.tan(np.radians(tt)) * np.sin(np.radians(pp)))))
                    r_gap = float(np.median(lens[gi, h])) / LENS_FULL
                    c_gap = None
                    if yoke is not None and not np.all(np.isnan(yoke[gi, h])):
                        c_gap = np.array([float(np.nanmedian(yoke[gi, h]))])
                    if r_gap >= HIDDEN_LENS or c_gap is not None:  # the source head shows a lens or a yoke: pose it like that
                        gp, gt = pose_from_lean(np.array([lean_n]), "orient", args.pan_gain, np.array([r_gap]), c_gap)
                        gpp, gtt = float(gp[0]), float(gt[0])
                    else:  # nothing readable: park at the next beam's own pose (same pan side, no sweep)
                        gpp, gtt = pp, tt
                    split = seg[0] - PRE_POSITION_MS
                    filled.append((cursor, split, gpp, gpp, gtt, gtt, hsv_gap, DARK_DIMMER, False, False))
                    cursor = split
                # ... and for the last PRE_POSITION_MS (the whole gap when it is shorter) it moves to the next
                # beam's start pose: the motors have a slew limit, so a head still turning when the beam
                # appears would sweep it through the wrong angles. Mirrors xLights' "Link end position to
                # next Moving Head effect" (Link flag set so the editor keeps it in step).
                filled.append((cursor, seg[0], pp, pp, tt, tt, hsv_gap, DARK_DIMMER, False, link))
            if seg[2] is not None:
                if seg[8]:
                    filled.append(seg[:8] + (True, False))
                cursor, prev = seg[1], (seg[3], seg[5])
        for start, end, p0, p1, t0_, t1_, hsv, dimmer, lit, link in filled:
            plan.add(model, "Moving Head", start, end, mh_settings(p0, p1, t0_, t1_, hsv, dimmer, lit, link),
                     ["#FFFFFF"])
            n_eff += 1

    total = snap((frames[-1]["t"] - t0 + frame_dt) * 1000)
    out = Path(args.show) / f"{args.name}.xsq"
    if args.audio:
        if t0 > 0.05:
            print(f"warning: timeline starts at {t0:.2f}s but audio is assumed to start at 0; "
                  "media will be offset")
        add_beats(plan, Path(args.audio), total)
    pts.write(plan, total, out)
    if args.audio:
        set_media(out, Path(args.audio))
    print(f"wrote {out}: {n_eff} effects across {nheads} heads, {total / 1000:.1f}s "
          f"({len(frames)} video frames)")


if __name__ == "__main__":
    main()
