"""Score a video-derived Moving Head sequence against the vendor's own sequence (ground truth).

    python scripts/compare_to_vendor.py OURS.xsq VENDOR_DECODED.json [--models MH-2,...,MH-7] [--frames N] [--slew 120]

VENDOR_DECODED.json comes from vendor_dmx_decode.py. The vendor geometry (fitted on Pixel Pro's Livingston Shadow): pan = DMX*540/255 from
the pan zero, tilt = DMX*220/255 - 110 (vertical at DMX ~128); beam direction (x right, y up, z toward the camera) =
(sin t sin p, cos t, sin t cos p). The vendor's motors are slew limited (120 deg/s) so the video shows the slewed motion.
Reports: lit/dark agreement per head, then for frames lit in both: screen-lean error and 3D beam-direction error of our poses.
"""
import argparse
import json
import re
import xml.etree.ElementTree as ET

import numpy as np


def slewed(c, limit_dps, dt):
    out = np.zeros(len(c))
    cur = c[0]
    for k, x in enumerate(c):
        cur += np.clip(x - cur, -limit_dps * dt, limit_dps * dt)
        out[k] = cur
    return out


def our_tracks(xsq, models, n, step_ms=50):
    """Per model: pan, tilt (deg) and lit arrays at step_ms from the generated Moving Head effects (linear within an effect)."""
    root = ET.parse(xsq).getroot()
    db = [(e.text or "").replace("&comma;", "|") for e in root.find("EffectDB")]
    res = {}
    for el in root.iter("Element"):
        name = el.get("name")
        if name not in models or name in res or el.find("EffectLayer") is None:
            continue
        pan = np.full(n, np.nan)
        tilt = np.full(n, np.nan)
        lit = np.zeros(n, bool)
        for e in el.iter("Effect"):
            a, b = int(e.get("startTime")), int(e.get("endTime"))
            s = db[int(e.get("ref"))]
            m = re.search(r"E_TEXTCTRL_MH1_Settings=(.*?),E_TEXTCTRL_MH2", s)
            slot = m.group(1) if m else ""
            ends = {}
            for axis in ("Pan", "Tilt"):
                vc = re.search(rf"{axis} VC: Active=TRUE\|Id=[^|]*\|Type=Ramp\|Min=[^|]*\|Max=[^|]*\|P1=([-\d.]+)\|P2=([-\d.]+)", slot)
                fx = re.search(rf"{axis}: ([-\d.]+)", slot)
                ends[axis] = (float(vc.group(1)) / 10, float(vc.group(2)) / 10) if vc else ((float(fx.group(1)),) * 2 if fx else None)
            i0, i1 = a // step_ms, min(n, max(a // step_ms + 1, b // step_ms))
            for k in range(i0, i1):
                u = (k * step_ms - a) / max(1, b - a)
                if ends["Pan"]:
                    pan[k] = ends["Pan"][0] + (ends["Pan"][1] - ends["Pan"][0]) * u
                if ends["Tilt"]:
                    tilt[k] = ends["Tilt"][0] + (ends["Tilt"][1] - ends["Tilt"][0]) * u
                lit[k] = "Shutter: On" in slot
        res[name] = (pan, tilt, lit)
    return res


def vec(p_deg, t_deg):
    p, t = np.radians(p_deg), np.radians(t_deg)
    return np.stack([np.sin(t) * np.sin(p), np.cos(t), np.sin(t) * np.cos(p)], axis=-1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ours")
    ap.add_argument("vendor")
    ap.add_argument("--models", default="MH-2,MH-3,MH-4,MH-5,MH-6,MH-7")
    ap.add_argument("--slew", type=float, default=120.0)
    a = ap.parse_args()
    v = json.load(open(a.vendor))
    step = v["step_ms"]
    models = a.models.split(",")
    n = len(v["heads"]["MH1"]["pan"])
    ours = our_tracks(a.ours, set(models), n, step)
    tot = np.zeros(3)
    leans, ang3, signs, depth_err = [], [], [], []
    for i, m in enumerate(models):
        vh = v["heads"][f"MH{i + 1}"]
        pan = np.array([np.nan if x is None else x for x in vh["pan"]])
        tilt = np.array([np.nan if x is None else x for x in vh["tilt"]])
        pan = np.where(np.isnan(pan), np.nanmedian(pan), pan)
        tilt = np.where(np.isnan(tilt), np.nanmedian(tilt), tilt)
        vp = slewed(pan * 540 / 255, a.slew, step / 1000)
        vt = slewed(tilt * 220 / 255 - 110, a.slew, step / 1000)
        vlit = (np.array(vh["dimmer"]) > 5) | (np.array(vh["intensity"]) > 0)
        op, ot, olit = ours[m]
        ok = olit & vlit & ~np.isnan(op) & ~np.isnan(ot)
        tp, fp, fn = int((olit & vlit).sum()), int((olit & ~vlit).sum()), int((~olit & vlit).sum())
        tot += (tp, fp, fn)
        print(f"{m} (vendor MH{i + 1}): lit agree {tp:5d} extra {fp:4d} missed {fn:4d}  F1 {2 * tp / max(1, 2 * tp + fp + fn):.2f}")
        vv = vec(vp[ok], vt[ok])
        ov = vec(op[ok], ot[ok])
        lean_v = np.degrees(np.arctan2(vv[:, 0], vv[:, 1]))
        lean_o = np.degrees(np.arctan2(ov[:, 0], ov[:, 1]))
        d = np.abs(lean_v - lean_o)
        leans.append(np.minimum(d, 360 - d))
        # depth sign convention differs between the vendor model and xLights' own: take whichever sign agrees better overall
        ang3.append((vv, ov))
    lean = np.concatenate(leans)
    vv = np.concatenate([x[0] for x in ang3])
    ov = np.concatenate([x[1] for x in ang3])
    best = None
    for s in (1, -1):
        o2 = ov * np.array([1, 1, s])
        cosang = np.clip((vv * o2).sum(1), -1, 1)
        err = np.degrees(np.arccos(cosang))
        if best is None or np.median(err) < np.median(best[1]):
            best = (s, err)
    s, err = best
    print(f"\nlit/dark overall: agree {int(tot[0])} extra {int(tot[1])} missed {int(tot[2])}  F1 {2 * tot[0] / max(1, 2 * tot[0] + tot[1] + tot[2]):.3f}")
    print(f"frames lit in both: {len(lean)}")
    print(f"screen-lean error (deg): median {np.median(lean):.2f}  p75 {np.percentile(lean, 75):.2f}  p90 {np.percentile(lean, 90):.2f}  within 3: {(lean < 3).mean():.3f}  within 5: {(lean < 5).mean():.3f}")
    print(f"3D beam-direction error (deg, depth sign {s:+d}): median {np.median(err):.2f}  p75 {np.percentile(err, 75):.2f}  p90 {np.percentile(err, 90):.2f}  within 5: {(err < 5).mean():.3f}  within 10: {(err < 10).mean():.3f}")
    dv, do = vv[:, 2], ov[:, 2] * s
    big = np.abs(dv) > 0.2
    print(f"toward/away-from-camera component: where the vendor's |depth| > 0.2 ({int(big.sum())} frames) the sign matches in {(np.sign(dv[big]) == np.sign(do[big])).mean():.3f}")


if __name__ == "__main__":
    main()
