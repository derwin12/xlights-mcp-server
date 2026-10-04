"""Decode a vendor Moving Head sequence made of DMX effects into a per-head timeline (ground truth for the video -> sequence process).

    python scripts/vendor_dmx_decode.py VENDOR.xsq OUT.json [--step-ms 50]

The vendor (Pixel Pro Displays) drives each head with DMX effects: channel 9 = pan, 11 = tilt, 1 = dimmer (value curves: Ramp,
Ramp Up/Down, Saw Tooth, Custom) and a sub-model layer ("MH Intensity") of On / Color Wash effects that turns the beam on.
OUT.json: {"step_ms", "heads": {"MH1": {"pan": [DMX 0-255 or null], "tilt": [...], "dimmer": [0-255], "intensity": [0/1]}}}.
A channel is null where no DMX effect covers the time (xLights writes 0 there, which is not a meaningful pose).
"""
import argparse
import json
import re
import xml.etree.ElementTree as ET

import numpy as np


def curve_value(spec, u):
    """Value of an xLights value curve string at u in 0..1 through the effect, scaled to Min..Max."""
    kv = dict(p.split("=", 1) for p in spec.split("|") if "=" in p)
    t = kv.get("Type", "")
    lo, hi = float(kv.get("Min", 0)), float(kv.get("Max", 255))
    p1, p2, p3 = (float(kv.get(k, 0)) for k in ("P1", "P2", "P3"))
    if t == "Ramp":
        return p1 + (p2 - p1) * u
    if t == "Ramp Up/Down":
        return p1 + (p2 - p1) * (u * 2) if u < 0.5 else p2 + (p3 - p2) * ((u - 0.5) * 2)
    if t == "Saw Tooth":
        cycles = max(1.0, p3)
        return p1 + (p2 - p1) * ((u * cycles) % 1.0)
    if t == "Custom":
        pts = sorted((float(a), float(b)) for a, b in (q.split(":") for q in kv["Values"].split(";") if q))
        return lo + (hi - lo) * float(np.interp(u, [a for a, _ in pts], [b for _, b in pts]))
    if t == "Flat":
        return p1
    raise ValueError(f"unhandled value curve type {t!r}")


def decode(path, step_ms=50):
    root = ET.parse(path).getroot()
    dur = float(root.find("head").find("sequenceDuration").text)
    n = int(dur * 1000 // step_ms) + 1
    db = [(e.text or "") for e in root.find("EffectDB")]
    out = {}
    for el in root.iter("Element"):
        name = el.get("name") or ""
        if el.get("type") != "model" or not re.fullmatch(r"MH\d+", name) or name in out or el.find("EffectLayer") is None:
            continue  # the display list also names each head, without effects
        pan = np.full(n, np.nan)
        tilt = np.full(n, np.nan)
        dim = np.zeros(n)
        inten = np.zeros(n)
        for lay in reversed(el.findall("EffectLayer")):  # layer 1 is the baseline pose, layer 0 (the moves) is applied on top
            for e in lay.iter("Effect"):
                if e.get("name") != "DMX":
                    continue
                a, b = int(e.get("startTime")), int(e.get("endTime"))
                s = db[int(e.get("ref"))]
                i0, i1 = a // step_ms, min(n, max(a // step_ms + 1, b // step_ms))
                for ch, arr in ((9, pan), (11, tilt), (1, dim)):
                    vc = re.search(rf"E_VALUECURVE_DMX{ch}=(Active=TRUE[^,]*)", s)
                    fixed = re.search(rf"E_SLIDER_DMX{ch}=(\d+)", s)
                    for k in range(i0, i1):
                        u = (k * step_ms - a) / max(1, b - a)
                        if vc:
                            arr[k] = curve_value(vc.group(1), min(1.0, max(0.0, u)))
                        elif fixed:
                            arr[k] = float(fixed.group(1))
        for sub in el.findall("SubModelEffectLayer"):
            for e in sub.iter("Effect"):
                a, b = int(e.get("startTime")), int(e.get("endTime"))
                inten[a // step_ms:min(n, b // step_ms)] = 1
        out[name] = {"pan": [None if np.isnan(v) else round(float(v), 2) for v in pan],
                     "tilt": [None if np.isnan(v) else round(float(v), 2) for v in tilt],
                     "dimmer": [round(float(v), 2) for v in dim], "intensity": [int(v) for v in inten]}
    return {"step_ms": step_ms, "heads": out}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("xsq")
    ap.add_argument("out")
    ap.add_argument("--step-ms", type=int, default=50)
    a = ap.parse_args()
    d = decode(a.xsq, a.step_ms)
    json.dump(d, open(a.out, "w"))
    for k, h in d["heads"].items():
        lit = sum(1 for dm, it in zip(h["dimmer"], h["intensity"]) if dm > 5 or it)
        print(k, "frames", len(h["pan"]), "lit", lit, "with pan", sum(v is not None for v in h["pan"]))


if __name__ == "__main__":
    main()
