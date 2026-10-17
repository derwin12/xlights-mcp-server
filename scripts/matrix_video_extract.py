"""Extract a pixel matrix from a show video as a clean, gap-free video.

Samples the colour of every LED in a fixed-camera video of a pixel matrix (a small patch at each dot centre),
which removes the dark spacing between dots, then writes the cols x rows frames upscaled smoothly.

    python scripts/matrix_video_extract.py IN.mp4 OUT.mp4 \
        --cols 50 --rows 24 --first 21.5 265.5 --last 923 --last-row-y 788.9 [--scale 20] [--native NATIVE.mp4]

--first / --last: pixel (x, y) of the first LED (top-left) and x of the last column; --last-row-y is the y of the
last row. Find them by taking a max-over-time projection of the frames and reading the dot peaks.
Audio is copied from IN.mp4. --native also writes the cols x rows video itself (lossless-ish, yuv444).
"""
from __future__ import annotations

import argparse
import subprocess

import numpy as np


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--cols", type=int, required=True)
    ap.add_argument("--rows", type=int, required=True)
    ap.add_argument("--first", type=float, nargs=2, required=True, metavar=("X", "Y"))
    ap.add_argument("--last", type=float, required=True, metavar="X", help="x of the last column")
    ap.add_argument("--last-row-y", type=float, required=True)
    ap.add_argument("--scale", type=int, default=20, help="output pixels per LED (default 20)")
    ap.add_argument("--fps", type=float)
    ap.add_argument("--patch", type=int, default=1, help="half-size of the sampling patch (1 = 3x3 mean)")
    ap.add_argument("--agg", choices=["mean", "max"], default="mean",
                    help="mean of the patch (big dots) or its brightest pixel per channel (small/faint dots)")
    ap.add_argument("--native")
    args = ap.parse_args()

    info = subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
         "-of", "csv=p=0", args.src]).decode().strip().split(",")
    w, h = int(info[0]), int(info[1])
    num, den = info[2].split("/")
    fps = args.fps or float(num) / float(den)

    xs = np.rint(np.linspace(args.first[0], args.last, args.cols)).astype(int)
    ys = np.rint(np.linspace(args.first[1], args.last_row_y, args.rows)).astype(int)
    p = args.patch
    # crop to the matrix area (+ margin) so only that part is piped
    x0, y0 = max(int(xs[0]) - 20, 0), max(int(ys[0]) - 20, 0)
    x1, y1 = min(int(xs[-1]) + 21, w), min(int(ys[-1]) + 21, h)
    cw, ch = (x1 - x0) // 2 * 2, (y1 - y0) // 2 * 2
    xs, ys = xs - x0, ys - y0

    dec = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", args.src, "-vf", f"crop={cw}:{ch}:{x0}:{y0},format=rgb24",
         "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    ow, oh = args.cols * args.scale, args.rows * args.scale
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{args.cols}x{args.rows}",
           "-r", str(fps), "-i", "-", "-i", args.src, "-map", "0:v", "-map", "1:a?",
           "-vf", f"scale={ow}:{oh}:flags=bicubic", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", args.out]
    if args.native:
        cmd += ["-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "0", "-pix_fmt", "yuv444p",
                "-c:a", "aac", "-b:a", "192k", "-shortest", args.native]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    n = 0
    fsize = cw * ch * 3
    while True:
        buf = dec.stdout.read(fsize)
        if len(buf) < fsize:
            break
        f = np.frombuffer(buf, np.uint8).reshape(ch, cw, 3).astype(np.uint16)
        acc = np.zeros((args.rows, args.cols, 3), np.uint32)
        for dy in range(-p, p + 1):
            for dx in range(-p, p + 1):
                v = f[np.ix_(np.clip(ys + dy, 0, ch - 1), np.clip(xs + dx, 0, cw - 1))]
                acc = np.maximum(acc, v) if args.agg == "max" else acc + v
        if args.agg == "mean":
            acc //= (2 * p + 1) ** 2
        enc.stdin.write(acc.astype(np.uint8).tobytes())
        n += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print(f"{n} frames -> {args.out} ({ow}x{oh} @ {fps:g} fps)")


if __name__ == "__main__":
    main()
