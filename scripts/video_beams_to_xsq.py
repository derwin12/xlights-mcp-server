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
        [--models MH-1,...,MH-8] [--tolerance 2.0] [--pan-mode fixed|lean] [--pan-gain 0.8]
"""
import argparse
import colorsys
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import prop_test_sequence as pts  # noqa: E402  (reuses its .xsq writer)

PAN = 90.0
FRAME_MS = 25  # xLights sequence timing
MIN_SEG_MS = 100
MAX_TILT = 90.0
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
    # Bridge 1-2 frame dropouts
    for i in range(1, len(on) - 1):
        if not on[i]:
            j = i
            while j < len(on) and not on[j]:
                j += 1
            if j < len(on) and j - i <= 2 and on[i - 1]:
                for k in range(i, j):
                    w = (k - i + 1) / (j - i + 1)
                    ang[k] = ang[i - 1] * (1 - w) + ang[j] * w
                    inten[k] = inten[i - 1] * (1 - w) + inten[j] * w
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
                     "rgb": np.array(rgbs[sl], float), "w": inten[sl]})
        i = j + 1
    return runs, t


def fmt_vc(axis, a0, a1):
    return (f"{axis} VC: Active=TRUE|Id=ID_VALUECURVE_MH{axis}|Type=Ramp|Min=-1800.00|Max=1800.00|"
            f"P1={a0 * 10:.2f}|P2={a1 * 10:.2f}|RV=TRUE|")


def pose_from_lean(lean, mode, gain):
    """(pan, tilt) arrays in degrees that show the given on-screen lean to a front camera."""
    lean = np.clip(lean, -80.0, 80.0)
    if mode == "fixed":
        return np.full_like(lean, PAN), lean
    pan = np.clip(PAN - gain * lean, 30.0, 150.0)
    tilt = np.degrees(np.arctan(np.tan(np.radians(lean)) / np.sin(np.radians(pan))))
    return pan, np.clip(tilt, -MAX_TILT, MAX_TILT)


def fmt_dimmer(ts, ys):
    pts_ = np.arange(len(ts))
    x = (ts - ts[0]) / max(ts[-1] - ts[0], 1e-6)
    idx = douglas_peucker(x, ys, 0.06)
    flat = []
    for i in idx[:8]:
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
    ap.add_argument("--models", default=",".join(f"MH-{i}" for i in range(1, 9)))
    ap.add_argument("--audio", help="audio file (video's soundtrack, aligned to video t=0): sets the "
                    "sequence media file and adds a Beats timing track")
    ap.add_argument("--pan-mode", choices=["fixed", "lean"], default="fixed",
                    help="fixed: pan 90 deg; lean: pan swivels with the beam, tilt solved to keep lean")
    ap.add_argument("--pan-gain", type=float, default=0.8, help="deg of pan per deg of lean (lean mode)")
    ap.add_argument("--tolerance", type=float, default=2.0, help="max angle error (deg) per segment")
    ap.add_argument("--group", default="Moving Heads Group",
                    help="model group holding MH-1..MH-8 (fixtures 1-8): uniform fans become group effects")
    ap.add_argument("--no-fans", action="store_true", help="skip fan detection; per-head effects only")
    args = ap.parse_args()

    data = json.load(open(args.beams))
    frames = data["frames"]
    models = args.models.split(",")
    nheads = len(frames[0]["heads"])
    assert len(models) == nheads, f"{nheads} heads in timeline but {len(models)} models given"
    t0 = frames[0]["t"]
    frame_dt = 1.0 / data["fps"]

    plan = pts.Plan()
    n_eff = 0
    refs = []
    for h in range(nheads):
        ints = [f["heads"][h]["intensity"] for f in frames if f["heads"][h]]
        refs.append(float(np.percentile(ints, 95)) if ints else 1.0)

    # Uniform fans (both banks of four heads fanned evenly at once) become group effects; their
    # frames are then hidden from the per-head pass, which only pre-positions heads for them.
    fans = []
    if not args.no_fans and nheads == 8:
        import mh_fan
        T = np.array([f["t"] for f in frames])
        A = np.array([[h["angle"] if h else np.nan for h in f["heads"]] for f in frames])
        I = np.array([[h["intensity"] / refs[k] if h else np.nan for k, h in enumerate(f["heads"])]
                      for f in frames])
        RGB = np.array([[h["rgb"] if h else [np.nan] * 3 for h in f["heads"]] for f in frames], float)
        mean_rgb = np.nan_to_num(np.nanmean(RGB, axis=1)) if len(frames) else RGB
        cls = median_filter(np.array([hue_class(c) for c in mean_rgb], float), 5)
        for i0, i1 in mh_fan.detect_spans(A, data["fps"], cls):
            fans.append((i0, i1, mh_fan.plan_span(T, A, I, RGB, i0, i1, t0, frame_dt, args.tolerance)))
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

    for h, model in enumerate(models):
        ref = refs[h]
        runs, _ = build_runs(frames, h, ref)
        segs = []  # (start_ms, end_ms, pan0, pan1, tilt0, tilt1, hsv, dimmer)
        for r in runs:
            t = r["t"]
            pan, tilt = pose_from_lean(r["ang"], args.pan_mode, args.pan_gain)
            pose = np.stack([pan, tilt], axis=1)
            idx = douglas_peucker(t, pose, args.tolerance) if len(t) > 2 else [0, len(t) - 1]
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
                dimmer = fmt_dimmer(t[sl], r["int"][sl]) if b > a else "Dimmer: 0.0&comma;1.0&comma;1.0&comma;1.0"
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
                # Mirrors xLights' "Link end position to next Moving Head effect": dark, parked at
                # the next effect's start pose, carrying its color, with the Link flag set so the
                # editor keeps it in step if the next effect is moved later.
                filled.append((cursor, seg[0], pp, pp, tt, tt, seg[6] or (0.0, 0.0, 1.0), DARK_DIMMER,
                               False, seg[2] is not None and seg[8]))
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
