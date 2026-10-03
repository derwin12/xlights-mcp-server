"""Read which way each moving head faces from the head bodies in a light show video.

Yoke: the two yoke arms are the clearest pan cue. With the arms either side of the head (pan ~0 or 180) the dark body
pixels sit ~10 px from the head's centre; turned sideways (pan ~90) the arms hide and the dark mass is a central arch, ~3.6 px.
The mean |dx| of the dark body pixels ("yoke spread") is written per head and frame; video_beams_to_xsq.py turns it into |cos pan|.

A head whose beam points toward the camera shows its lens (a teal disc on top of the yoke); a head
pointing away shows its back (a dark housing, no lens). A beam's on-screen lean cannot tell the two
apart (pan 15 and pan 165 lean the same way), but the head body can. For every frame this counts the
teal pixels in each head's patch; video_beams_to_xsq.py --pan-mode orient turns that into a pan in
the front (toward the camera) or back half-turn.

Usage:
    python scripts/video_head_facing.py VIDEO OUT.json [--heads x,y;x,y;...] [--start S] [--duration D]
VIDEO may be a URL (see fetch_video.py). Coordinates are in a 1280x720 frame; the default heads are
the Pixel Pro Displays roofline rig. OUT.json: {"fps", "heads", "lens": [[teal fraction per head]...], "yoke": [[yoke spread per head]...]}.
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import fetch_video  # noqa: E402

W, H = 1280, 720
DEFAULT_HEADS = [(426, 180), (474, 180), (522, 180), (570, 180), (618, 180), (666, 180)]
PATCH = (-20, 21, -14, 22)  # x0, x1, y0, y1 around a head origin: the whole head body
TEAL_HUE = (78, 105)  # OpenCV hue (0-180) of the lens, dark or lit
TEAL_SAT = 35
YOKE_ROWS = (8, 27)  # rows below the head origin that hold the yoke arms
YOKE_HALF = 20  # columns each side of the head origin
YOKE_DARK = 34  # grey level below which a body pixel counts as yoke/housing
YOKE_MIN_PIXELS = 25
FRONT_FRACTION = 0.02  # lens fraction at or above which a head counts as facing the camera


def lens_fractions(img, heads):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    out = []
    for x, y in heads:
        p = hsv[y + PATCH[2]:y + PATCH[3], x + PATCH[0]:x + PATCH[1]]
        m = (p[..., 0] >= TEAL_HUE[0]) & (p[..., 0] <= TEAL_HUE[1]) & (p[..., 1] >= TEAL_SAT)
        out.append(round(float(m.mean()), 4))
    return out


def yoke_spreads(img, heads):
    """Mean |dx| (px) of the dark body pixels per head: ~10 arms either side, ~3.6 an arch; -1 when too few dark pixels."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    out = []
    for x, y in heads:
        m = g[y + YOKE_ROWS[0]:y + YOKE_ROWS[1], x - YOKE_HALF:x + YOKE_HALF + 1] < YOKE_DARK
        if m.sum() < YOKE_MIN_PIXELS:
            out.append(-1.0)
        else:
            out.append(round(float(np.abs(np.nonzero(m)[1] - YOKE_HALF).mean()), 2))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("out")
    ap.add_argument("--heads", help="x,y;x,y;... in 1280x720 space")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--duration", type=float, default=0.0)
    args = ap.parse_args()

    heads = DEFAULT_HEADS
    if args.heads:
        heads = [tuple(int(v) for v in p.split(",")) for p in args.heads.split(";")]
    video = str(fetch_video.fetch(args.video)) if fetch_video.is_url(args.video) else args.video

    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    first = int(args.start * fps)
    last = total if not args.duration else min(total, first + int(args.duration * fps))
    cap.set(cv2.CAP_PROP_POS_FRAMES, first)
    lens, yoke = [], []
    for _ in range(first, last):
        ok, f = cap.read()
        if not ok:
            break
        small = cv2.resize(f, (W, H), interpolation=cv2.INTER_AREA)
        lens.append(lens_fractions(small, heads))
        yoke.append(yoke_spreads(small, heads))
    json.dump({"video": video, "fps": fps, "start": first / fps, "heads": heads, "lens": lens, "yoke": yoke}, open(args.out, "w"))
    print(f"wrote {len(lens)} frames -> {args.out}")


if __name__ == "__main__":
    main()
