"""Analyze a fixed-camera light show video and extract per-head moving head beams.

For each known head origin, casts rays at candidate angles and scores them by the
brightness found along the ray. The best angle, color and intensity per frame are
written to a JSON timeline. Beam length is ignored (only direction matters).

Usage:
    python scripts/video_beam_analysis.py VIDEO OUT.json [--overlay OUT.mp4]
        [--start S] [--duration D] [--heads x,y;x,y;...]
"""
import argparse
import json
import math

import cv2
import numpy as np

W, H = 1280, 720  # analysis resolution
# Head origins (in 1280x720 space), left to right. y is just above the fixture tops.
DEFAULT_HEADS = [(399, 280), (431, 280), (464, 280), (497, 280),
                 (651, 280), (678, 280), (706, 280), (733, 280)]
ANGLES = np.arange(-75.0, 75.01, 0.5)  # degrees from vertical, +ve = right
MIN_SCORE = 18.0  # mean ray brightness (0-255) below which the head counts as off
COVER_LEVEL = 10.0  # brightness (0-255) a ray sample needs to count as lit
MIN_COVER = 0.6  # share of the whole ray that must be lit: a crossing beam lights only a few samples
BASE_SAMPLES = 12  # leading ray samples (~8-30 px from the head) that must also be lit
MIN_BASE_COVER = 0.75  # a ray running alongside another head's beam is lit mid-way but not at its own head
FINE_WINDOW = 4  # +- candidate rays (0.5 deg each) searched for the precise angle


def build_rays(origin):
    """Return (xs, ys) integer sample arrays shaped (n_angles, n_samples)."""
    ox, oy = origin
    ts = np.arange(8, oy - 2, 2.0)
    a = np.radians(ANGLES)[:, None]
    xs = ox + np.sin(a) * ts[None, :]
    ys = oy - np.cos(a) * ts[None, :]
    valid = (xs >= 0) & (xs < W - 1) & (ys >= 0)
    xs = np.clip(xs, 0, W - 1).astype(int)
    ys = np.clip(ys, 0, H - 1).astype(int)
    return xs, ys, valid


def analyze_frame(img, rays):
    gray = img.max(axis=2).astype(np.float32)
    # Beams are a pixel or two wide near the fixture, so a 5x5 max makes ray sampling tolerant of
    # the 0.5 deg angular step when judging how much of the ray is lit.
    gray_d = cv2.dilate(gray, np.ones((5, 5), np.uint8))
    # The base test needs more lateral slack: the assumed head origin is a few px off the real
    # beam base. Neighbouring heads are ~27 px apart, so 7x7 still cannot borrow their beams.
    gray_b = cv2.dilate(gray, np.ones((7, 7), np.uint8))
    out = []
    for xs, ys, valid in rays:
        nvalid = np.maximum(valid.sum(axis=1), 1)
        # Whole-beam test: the fraction of the ray that is lit and its mean brightness. A real
        # beam is lit along its full length; another head's beam crossing the ray is not.
        dvals = gray_d[ys, xs] * valid
        cover = (dvals > COVER_LEVEL).sum(axis=1) / nvalid
        base = ((gray_b[ys[:, :BASE_SAMPLES], xs[:, :BASE_SAMPLES]] * valid[:, :BASE_SAMPLES])
                > COVER_LEVEL).mean(axis=1)
        coarse = np.where((valid.sum(axis=1) > 20) & (cover >= MIN_COVER) & (base >= MIN_BASE_COVER),
                          dvals.sum(axis=1) / nvalid, 0)
        i0 = int(coarse.argmax())
        if coarse[i0] < MIN_SCORE:
            out.append(None)
            continue
        # Precise angle: undilated mean brightness among rays near the coarse winner
        raw = (gray[ys, xs] * valid).sum(axis=1) / nvalid
        lo, hi = max(0, i0 - FINE_WINDOW), min(len(raw), i0 + FINE_WINDOW + 1)
        i = lo + int(raw[lo:hi].argmax())
        if raw[i] < MIN_SCORE:
            out.append(None)
            continue
        lo, hi = max(0, i - 3), min(len(raw), i + 4)
        w = raw[lo:hi]
        ang = float((ANGLES[lo:hi] * w).sum() / w.sum())
        m = valid[i]
        px = img[ys[i][m], xs[i][m]].astype(np.float32)
        bright = px[px.max(axis=1) > 0.5 * px.max()].mean(axis=0)  # BGR
        b, g, r = (float(v) for v in bright)
        hsv = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV)[0, 0]
        out.append({"angle": round(ang, 2), "intensity": round(float(raw[i]) / 255, 3),
                    "rgb": [int(r), int(g), int(b)], "hue": int(hsv[0]) * 2, "sat": int(hsv[1]),
                    "cover": round(float(cover[i]), 2)})
    return out


def draw_overlay(img, heads, res):
    o = img.copy()
    for (ox, oy), r in zip(heads, res):
        if r is None:
            cv2.circle(o, (ox, oy), 4, (0, 0, 255), -1)
            continue
        a = math.radians(r["angle"])
        ex, ey = int(ox + math.sin(a) * 300), int(oy - math.cos(a) * 300)
        cv2.line(o, (ox, oy), (ex, ey), (0, 255, 0), 1)
        cv2.putText(o, f'{r["angle"]:.0f}', (ex - 12, max(ey, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
    return o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out")
    ap.add_argument("--overlay")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--duration", type=float, default=0.0)
    ap.add_argument("--heads", help="x,y;x,y;... in 1280x720 space")
    args = ap.parse_args()

    heads = DEFAULT_HEADS
    if args.heads:
        heads = [tuple(int(v) for v in p.split(",")) for p in args.heads.split(";")]
    rays = [build_rays(h) for h in heads]

    cap = cv2.VideoCapture(args.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    first = int(args.start * fps)
    last = total if not args.duration else min(total, first + int(args.duration * fps))
    cap.set(cv2.CAP_PROP_POS_FRAMES, first)

    writer = None
    if args.overlay:
        writer = cv2.VideoWriter(args.overlay, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))

    frames = []
    for n in range(first, last):
        ok, f = cap.read()
        if not ok:
            break
        img = cv2.resize(f, (W, H), interpolation=cv2.INTER_AREA)
        res = analyze_frame(img, rays)
        frames.append({"t": round(n / fps, 4), "heads": res})
        if writer:
            writer.write(draw_overlay(img, heads, res))
        if (n - first) % 300 == 0:
            print(f"frame {n}/{last}", flush=True)

    json.dump({"video": args.video, "fps": fps, "heads": heads, "frames": frames},
              open(args.out, "w"))
    if writer:
        writer.release()
    print(f"wrote {len(frames)} frames -> {args.out}")


if __name__ == "__main__":
    main()
