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


def detect_grid(src: str, w: int, h: int, cols: int, rows: int) -> tuple[tuple[float, float], float, float]:
    """Find the LED grid of the left-hand matrix: max-over-time projection of the left half, dot peaks per axis.

    Returns ((first_x, first_y), last_x, last_row_y). Raises if the peak counts don't match cols x rows."""
    x1, y0, y1 = int(w * 0.5) // 2 * 2, int(h * 0.08) // 2 * 2, int(h * 0.755) // 2 * 2
    raw = subprocess.check_output(
        ["ffmpeg", "-v", "error", "-i", src, "-vf", f"fps=2,crop={x1}:{y1 - y0}:0:{y0},format=gray",
         "-f", "rawvideo", "-"])
    mx = np.frombuffer(raw, np.uint8).reshape(-1, y1 - y0, x1).max(axis=0).astype(float)

    def axis(profile: np.ndarray, n: int) -> tuple[float, float]:
        """First/last LED centre along one axis = the outermost lit dots. Columns/rows that never light up in between
        are fine; the span must match n positions at the typical dot pitch."""
        idx = np.where(profile > 0.25 * profile.max())[0]
        c = np.array([g.mean() for g in np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)])
        d = np.diff(c)
        typical = float(np.median(d[d < 1.5 * np.percentile(d, 25)]))
        pitch = (c[-1] - c[0]) / (n - 1)
        if abs(pitch - typical) > 0.04 * typical:
            raise SystemExit(f"grid detection: span gives pitch {pitch:.2f} but dots are {typical:.2f} apart "
                             f"(outer dots may never light, or n={n} is wrong)")
        return float(c[0]), float(c[-1])

    fx, lx = axis(mx.max(axis=0), cols)
    fy, ly = axis(mx.max(axis=1), rows)
    return (fx, fy + y0), lx, ly + y0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--cols", type=int, required=True)
    ap.add_argument("--rows", type=int, required=True)
    ap.add_argument("--first", type=float, nargs=2, metavar=("X", "Y"))
    ap.add_argument("--last", type=float, metavar="X", help="x of the last column")
    ap.add_argument("--last-row-y", type=float)
    ap.add_argument("--auto", action="store_true",
                    help="detect --first/--last/--last-row-y for a left-hand matrix (as in Pixel Pro previews)")
    ap.add_argument("--scale", type=int, default=20, help="output pixels per LED (default 20)")
    ap.add_argument("--filter", choices=["bicubic", "neighbor"], default="bicubic",
                    help="upscale filter: bicubic = smooth, neighbor = crisp square pixels (e.g. --scale 16 for 800x384)")
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

    if args.auto:
        args.first, args.last, args.last_row_y = detect_grid(args.src, w, h, args.cols, args.rows)
        print(f"grid: first={args.first} last_x={args.last:.1f} last_row_y={args.last_row_y:.1f}")
    elif args.first is None or args.last is None or args.last_row_y is None:
        ap.error("give --first, --last and --last-row-y, or --auto")
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
           "-vf", f"scale={ow}:{oh}:flags={args.filter}", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p",
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
