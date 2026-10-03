"""Fan detection and group-effect planning for video beam timelines.

Many moving head shows drive each bank of heads with one Moving Head effect on a model group: the
heads of a bank sit at  base + (slot - centre) * offset  (Tilt and TiltOffset). When both banks
(heads 1-4 and 5-8) are even fans at the same time, one group effect reproduces the span instead of
a pan/tilt path per head. See video_beams_to_xsq.py, which tries fans first and falls back to
per-head effects for everything else.

Pan stays at 90 deg so the on-screen lean equals tilt (see mh_calibration_sequence.py). Slots of a
group effect are keyed by fixture number (MH-1..MH-8 = fixtures 1..8) and each carries its own
"Heads:" list, so the two banks can have independent curves inside one effect.
"""
import colorsys
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import video_beams_to_xsq as v2x  # noqa: E402

PAN = 90.0
BANKS = ([1, 2, 3, 4], [5, 6, 7, 8])  # fixture numbers fanned together
SLOTS = np.arange(1, 5) - 2.5  # position of each head relative to the centre of its bank
MAX_RESID = 1.5  # deg: worst head-vs-fan error for a frame to count as an even fan
MIN_FAN_S = 0.4
BRIDGE_FRAMES = 5  # dropout length bridged inside a fan span
SINE_MEAN_ERR = 1.3  # deg: accept a sine fit below this mean / 95th-percentile error
SINE_P95_ERR = 3.5
STATIC_RANGE = 1.5  # deg: base and spread both move less than this -> static pose
OFFSET_ID = "ID_VALUECURVE_MHTiltOffset"


def fit_bank(A, heads, min_heads=4):
    """Per-frame fan fit of one bank: lean = c + slot * o. Returns (c, o, worst residual).

    NaN where fewer than min_heads heads are lit.
    """
    n = len(A)
    c, o, r = (np.full(n, np.nan) for _ in range(3))
    for i, row in enumerate(A[:, [h - 1 for h in heads]]):
        ok = ~np.isnan(row)
        if ok.sum() >= min_heads:
            o[i], c[i] = np.polyfit(SLOTS[ok], row[ok], 1)
            r[i] = np.abs(row[ok] - (c[i] + SLOTS[ok] * o[i])).max()
    return c, o, r


def interp_nan(y):
    ok = ~np.isnan(y)
    if ok.all():
        return y
    x = np.arange(len(y))
    return np.interp(x, x[ok], y[ok])


def detect_spans(A, fps, cls=None):
    """(first, last) frame index of each span where both banks are even fans together.

    cls: optional per-frame colour class; a span is split wherever it changes.
    """
    n = len(A)
    ok = np.ones(n, bool)
    for heads in BANKS:
        r = fit_bank(A, heads)[2]
        ok &= ~np.isnan(r) & (r <= MAX_RESID)
    i = 0
    while i < n:  # bridge short dropouts (the frames inside stay NaN and get interpolated)
        if ok[i]:
            i += 1
            continue
        j = i
        while j < n and not ok[j]:
            j += 1
        if i > 0 and j < n and j - i <= BRIDGE_FRAMES:
            ok[i:j] = True
        i = j
    spans, i = [], 0
    while i < n:
        if not ok[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and ok[j + 1] and (cls is None or cls[j + 1] == cls[i]):
            j += 1
        if j - i + 1 >= MIN_FAN_S * fps:
            spans.append((i, j))
        i = j + 1
    return spans


def fit_sine(x, y, cycles_range=(0.5, 8.0)):
    """Least-squares y ~ A + R*sin(2*pi*n*x + phi) over a grid of cycle counts n -> (A, R, phi, n)."""
    best = None
    for n in np.arange(cycles_range[0], cycles_range[1], 0.01):
        w = 2 * np.pi * n
        M = np.stack([np.ones(len(x)), np.sin(w * x), np.cos(w * x)], axis=1)
        coef, *_ = np.linalg.lstsq(M, y, rcond=None)
        err = float(((M @ coef - y) ** 2).mean())
        if best is None or err < best[0]:
            best = (err, coef, n)
    _, (a, s, c), n = best
    return a, float(np.hypot(s, c)), float(np.arctan2(c, s)), n


def eval_sine(x, a, r, phi, n):
    return a + r * np.sin(2 * np.pi * n * x + phi)


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


def slot_text(heads, tilt_cmd, offset_cmd, dimmer, hsv, lit):
    h, s, v = hsv
    return (f"Color: {h:.6f}&comma;{s:.6f}&comma;{v:.6f};{dimmer};Pan: {PAN:.1f};{tilt_cmd};"
            f"PanOffset: 0.0;{offset_cmd};Groupings: 1.0;Cycles: 1.0;"
            f"Heads: {'&comma;'.join(map(str, heads))}" + (";Shutter: On" if lit else ""))


def group_settings(slots):
    """Effect settings for a group effect; slots maps fixture number -> slot text."""
    head = ("B_CHOICE_BufferStyle=Per Model Default,E_CHECKBOX_MHIgnorePan=0,E_CHECKBOX_MHIgnoreTilt=0,"
            "E_NOTEBOOK1=Position,E_NOTEBOOK2=Color,E_SLIDER_MHCycles=10,E_SLIDER_MHGroupings=1,"
            "E_SLIDER_MHPan=0,E_SLIDER_MHPanOffset=0,E_SLIDER_MHPathScale=0,E_SLIDER_MHTilt=0,"
            "E_SLIDER_MHTiltOffset=0,E_SLIDER_MHTimeOffset=0")
    return head + "".join(f",E_TEXTCTRL_MH{n}_Settings={t}" for n, t in sorted(slots.items()))


def _static(name, value):
    return f"{name}: {value:.2f}"


def _bank_slots(heads, tilt_cmd, offset_cmd, dimmer, hsv):
    return {h: slot_text(heads, tilt_cmd, offset_cmd, dimmer, hsv, True) for h in heads}


def plan_span(t, A, I, rgb, i0, i1, t0, frame_dt, tolerance):
    """Plan one fan span as group effects.

    t, A (n x 8 lean), I (n x 8 intensity normalised per head), rgb (n x 8 x 3, NaN where off) are
    whole-video arrays. Returns a dict: effects [(start_ms, end_ms, slots)], start_tilt/end_tilt
    (8 head poses for gap filling), hsv, kind ("static" / "sine" / "ramps").
    """
    sl = slice(i0, i1 + 1)
    ts, As = t[sl], A[sl]
    x = (ts - ts[0]) / max(ts[-1] - ts[0], 1e-6)
    banks = []
    for heads in BANKS:
        c, o, _ = fit_bank(As, heads, min_heads=2)
        banks.append((v2x.median_filter(interp_nan(c), 5), v2x.median_filter(interp_nan(o), 5)))

    with np.errstate(all="ignore"):
        m = interp_nan(np.nanmean(I[sl], axis=1))
    w = np.nan_to_num(I[sl], nan=0.0)
    mean_rgb = (np.nan_to_num(rgb[sl]) * w[..., None]).sum((0, 1)) / max(w.sum(), 1e-6)
    hh, ss, _ = colorsys.rgb_to_hsv(*(c / 255 for c in mean_rgb))
    hsv = (hh, 0.0 if ss < 0.25 else min(ss, 1.0), 1.0)

    start_ms = v2x.snap((ts[0] - t0) * 1000)
    end_ms = v2x.snap((ts[-1] - t0 + frame_dt) * 1000)
    effects, kind = [], "ramps"

    static = all(np.ptp(c) < STATIC_RANGE and np.ptp(o) < STATIC_RANGE for c, o in banks)
    sines = None
    if not static and end_ms - start_ms >= 1500:
        sines = []
        for (c, o), heads in zip(banks, BANKS):
            a, r, phi, n = fit_sine(x, o)
            c0 = float(c.mean())
            pred = c0 + SLOTS[None, :] * eval_sine(x, a, r, phi, n)[:, None]
            err = np.abs(pred - As[:, [h - 1 for h in heads]])
            err = err[~np.isnan(err).any(axis=1)]
            good = (err.mean() <= SINE_MEAN_ERR and np.percentile(err, 95) <= SINE_P95_ERR and r > 1.5
                    and np.ptp(c) < 6.0)
            sines.append((a, r, phi, n, c0, good))
        if not all(s[-1] for s in sines):
            sines = None

    dimmer_all = v2x.fmt_dimmer(ts, m) if len(ts) > 1 else "Dimmer: 0.0&comma;1.0&comma;1.0&comma;1.0"
    if static:
        kind = "static"
        slots = {}
        for (c, o), heads in zip(banks, BANKS):
            slots.update(_bank_slots(heads, _static("Tilt", float(c.mean())), _static("TiltOffset", float(o.mean())),
                                     dimmer_all, hsv))
        effects.append((start_ms, end_ms, slots))
        start = [[c.mean() + s * o.mean() for s in SLOTS] for c, o in banks]
        end = start
    elif sines is not None:
        kind = "sine"
        slots = {}
        for (a, r, phi, n, c0, _), heads in zip(sines, BANKS):
            slots.update(_bank_slots(heads, _static("Tilt", c0), sine_vc(a, r, phi, n), dimmer_all, hsv))
        effects.append((start_ms, end_ms, slots))
        start = [[s[4] + k * eval_sine(0.0, *s[:4]) for k in SLOTS] for s in sines]
        end = [[s[4] + k * eval_sine(1.0, *s[:4]) for k in SLOTS] for s in sines]
    else:
        series = np.stack([banks[0][0], banks[0][1], banks[1][0], banks[1][1]], axis=1)
        idx = v2x.douglas_peucker(ts, series, tolerance)
        keep = [idx[0]]
        for i in idx[1:-1]:  # drop vertices closer than the minimum segment length
            if (ts[i] - ts[keep[-1]]) * 1000 >= v2x.MIN_SEG_MS:
                keep.append(i)
        if len(idx) > 1:
            keep.append(idx[-1])
        for a, b in zip(keep[:-1], keep[1:]):
            s_ms = v2x.snap((ts[a] - t0) * 1000)
            e_ms = v2x.snap((ts[b] - t0 + (frame_dt if b == len(ts) - 1 else 0)) * 1000)
            if e_ms <= s_ms:
                continue
            dim = v2x.fmt_dimmer(ts[a:b + 1], m[a:b + 1]) if b > a else dimmer_all
            slots = {}
            for k, heads in enumerate(BANKS):
                c, o = banks[k]
                tilt_cmd = v2x._axis("Tilt", c[a], c[b])[0]
                off_cmd = v2x._axis("TiltOffset", o[a], o[b])[0]
                slots.update(_bank_slots(heads, tilt_cmd, off_cmd, dim, hsv))
            effects.append((s_ms, e_ms, slots))
        start = [[c[0] + s * o[0] for s in SLOTS] for c, o in banks]
        end = [[c[-1] + s * o[-1] for s in SLOTS] for c, o in banks]

    return {"effects": effects, "start_tilt": np.concatenate(start), "end_tilt": np.concatenate(end),
            "hsv": hsv, "kind": kind, "start_ms": start_ms, "end_ms": end_ms}
