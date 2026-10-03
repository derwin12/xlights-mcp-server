"""Test: reproduce a fan section of a video beam timeline with ONE group Moving Head effect.

In a group effect each head renders its own MH<n>_Settings slot. A slot lists the heads it fans
across ("Heads: 1,2,3,4") and head position = base + (slot - centre) * offset, so a fan is just
Tilt (base) plus TiltOffset (spread per head). Both can be value curves; the breathing fan seen in
"I Knew It" (35.7-49.6s) is a sine on TiltOffset.

Per side (heads 1-4, heads 5-8) the lean timeline is fitted as  lean_k = c + (k - 2.5) * o(t)  and
o(t) as a sine. Pan stays at 90 so tilt equals the on-screen lean (see mh_calibration_sequence.py).

Usage:
    python scripts/mh_group_fan_test.py BEAMS.json "Sequence Name" --start 35.7 --end 49.6
        [--group "Moving Heads Group"] [--show F:/ShowFolderAI] [--audio FILE]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import prop_test_sequence as pts  # noqa: E402
import video_beams_to_xsq as v2x  # noqa: E402

PAN = 90.0
SIDES = (("left", [1, 2, 3, 4]), ("right", [5, 6, 7, 8]))
OFFSET_ID = "ID_VALUECURVE_MHTiltOffset"
SLOTS = np.arange(1, 5) - 2.5  # head position relative to the centre of a 4-head fan


def fit_side(A, heads):
    """Per-frame (centre, spread) of a side: lean = c + slot * o. NaN where fewer than 2 heads."""
    c = np.full(len(A), np.nan)
    o = np.full(len(A), np.nan)
    cols = [h - 1 for h in heads]
    for i, row in enumerate(A[:, cols]):
        ok = ~np.isnan(row)
        if ok.sum() >= 2:
            o[i], c[i] = np.polyfit(SLOTS[ok], row[ok], 1)
    return c, o


def fit_sine(x, y, cycles_range=(0.5, 8.0)):
    """Least-squares y ~ A + R*sin(2*pi*n*x + phi) over a grid of cycle counts n. Returns A,R,phi,n."""
    ok = ~np.isnan(y)
    best = None
    for n in np.arange(cycles_range[0], cycles_range[1], 0.01):
        w = 2 * np.pi * n
        M = np.stack([np.ones(ok.sum()), np.sin(w * x[ok]), np.cos(w * x[ok])], axis=1)
        coef, *_ = np.linalg.lstsq(M, y[ok], rcond=None)
        err = float(((M @ coef - y[ok]) ** 2).mean())
        if best is None or err < best[0]:
            best = (err, coef, n)
    _, (a, s, c), n = best
    return a, float(np.hypot(s, c)), float(np.arctan2(c, s)), n


def sine_vc(a, r, phi, n):
    """TiltOffset value curve: centre a deg, amplitude r deg, n cycles.

    RV=TRUE makes P2 (amplitude) and P4 (centre) real values on the curve's +-1800 (tenths of a
    degree) scale; xLights normalises them to 0-100 and renders
    deg = 7.2 * (p4n - 50) + 1.8 * p2n * sin(...), which inverts to the two lines below. P1 (phase,
    percent of a cycle) and P3 (cycles x 10) are not rescaled.
    """
    p1 = (phi / (2 * np.pi) * 100.0) % 100.0
    p2 = 20.0 * r - 1800.0
    p3 = n * 10.0
    p4 = 5.0 * a
    return (f"TiltOffset VC: Active=TRUE|Id={OFFSET_ID}|Type=Sine|Min=-1800.00|Max=1800.00|"
            f"P1={p1:.4f}|P2={p2:.4f}|P3={p3:.4f}|P4={p4:.4f}|RV=TRUE|")


def eval_sine(x, a, r, phi, n):
    return a + r * np.sin(2 * np.pi * n * x + phi)


def slot_text(heads, tilt, offset_cmd, dimmer, lit):
    return (f"Color: 0.000000&comma;0.000000&comma;1.000000;{dimmer};Pan: {PAN:.1f};Tilt: {tilt:.2f};"
            f"PanOffset: 0.0;{offset_cmd};Groupings: 1.0;Cycles: 1.0;Heads: {'&comma;'.join(map(str, heads))}"
            + (";Shutter: On" if lit else ""))


def group_settings(slots):
    """slots: {fixture number: text}. Same effect-level defaults as video_beams_to_xsq.mh_settings."""
    head = ("B_CHOICE_BufferStyle=Per Model Default,E_CHECKBOX_MHIgnorePan=0,E_CHECKBOX_MHIgnoreTilt=0,"
            "E_NOTEBOOK1=Position,E_NOTEBOOK2=Color,E_SLIDER_MHCycles=10,E_SLIDER_MHGroupings=1,"
            "E_SLIDER_MHPan=0,E_SLIDER_MHPanOffset=0,E_SLIDER_MHPathScale=0,E_SLIDER_MHTilt=0,"
            "E_SLIDER_MHTiltOffset=0,E_SLIDER_MHTimeOffset=0")
    return head + "".join(f",E_TEXTCTRL_MH{n}_Settings={t}" for n, t in sorted(slots.items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("beams")
    ap.add_argument("name")
    ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--group", default="Moving Heads Group")
    ap.add_argument("--show", default="F:/ShowFolderAI")
    ap.add_argument("--audio")
    ap.add_argument("--lead", type=float, default=2.0, help="seconds of dark pre-position before the fan")
    args = ap.parse_args()

    data = json.load(open(args.beams))
    frames = [f for f in data["frames"] if args.start - 0.5 <= f["t"] <= args.end + 0.5]
    T = np.array([f["t"] for f in frames])
    A = np.array([[h["angle"] if h else np.nan for h in f["heads"]] for f in frames])
    I = np.array([[h["intensity"] if h else np.nan for h in f["heads"]] for f in frames])
    on = (~np.isnan(A)).sum(axis=1) >= 7  # the fan: (nearly) all heads lit together
    t_on, t_off = T[on][0], T[on][-1] + 1.0 / data["fps"]
    print(f"beams on {t_on:.2f}-{t_off:.2f}s")
    x = (T - t_on) / (t_off - t_on)  # effect position 0..1

    # shared dimmer from mean normalised intensity, same reference as the per-head converter
    ref = float(np.percentile(I[~np.isnan(I)], 95))
    m = np.where(on, np.nanmean(np.where(on[:, None], I, 0.0), axis=1) / ref, 0.0)
    sel = on & (x >= 0) & (x <= 1)
    dimmer = v2x.fmt_dimmer(T[sel], m[sel])

    slots_lit, slots_dark, report = {}, {}, []
    for side, heads in SIDES:
        c, o = fit_side(A, heads)
        sel = on & ~np.isnan(o)
        a, r, phi, n = fit_sine(x[sel], o[sel])
        c0 = float(np.nanmean(c[sel]))
        pred_o = eval_sine(x, a, r, phi, n)
        pred = c0 + SLOTS[None, :] * pred_o[:, None]
        err = np.abs(pred - A[:, [h - 1 for h in heads]])[sel]
        report.append(f"{side}: spread {a:.1f}+-{r:.1f} deg, {n:.2f} cycles ({(t_off - t_on) / n:.2f}s/cycle), "
                      f"centre {c0:.1f}; angle error mean {np.nanmean(err):.2f} max {np.nanmax(err):.2f}")
        vc = sine_vc(a, r, phi, n)
        # dark lead-in parks the heads at the pose the fan starts in
        start_off = float(eval_sine(0.0, a, r, phi, n))
        for h in heads:
            slots_lit[h] = slot_text(heads, c0, vc, dimmer, True)
            slots_dark[h] = slot_text(heads, c0, f"TiltOffset: {start_off:.2f}", v2x.DARK_DIMMER, False)
    print("\n".join(report))

    plan = pts.Plan(first=[args.group])
    s_ms, e_ms = v2x.snap(t_on * 1000), v2x.snap(t_off * 1000)
    lead_ms = max(0, s_ms - int(args.lead * 1000))
    plan.add(args.group, "Moving Head", lead_ms, s_ms, group_settings(slots_dark), ["#FFFFFF"])
    plan.add(args.group, "Moving Head", s_ms, e_ms, group_settings(slots_lit), ["#FFFFFF"])
    total = e_ms + 1000
    out = Path(args.show) / f"{args.name}.xsq"
    pts.write(plan, total, out)
    if args.audio:
        v2x.set_media(out, Path(args.audio))
    print(f"wrote {out}: 2 effects on '{args.group}', {total / 1000:.1f}s")


if __name__ == "__main__":
    main()
