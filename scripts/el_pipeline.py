"""EasyxLights PRO Display video -> MH sequence, the repeatable steps (see the video-to-moving-heads skill).

    python scripts/el_pipeline.py prep  YOUTUBE_ID SLUG      # fetch, find the 8 heads, full beam analysis (~5-10 min)
    python scripts/el_pipeline.py build SLUG "EL_Title v1"   # pick --white / wheel palette from the beams, write the .xsq
    python scripts/el_pipeline.py side  SLUG RENDER.mp4 OUT  # side-by-side video (source brightened | render)

Files live in test_videos/<slug>.mp4/.mp3/_beams.json/_heads.txt. The head row is measured on the first frame with eight
evenly spaced vertical beams (x from the beams, y = beam bottom + 12 px, 1280x720 coordinates).
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
VID = ROOT / "test_videos"
CACHE = Path.home() / ".cache" / "xlights-mcp" / "videos"
ANALYSIS = ["--background", "--max-angle", "70", "--min-score", "8", "--cover-level", "5", "--base-slack", "7"]
UPRIGHT = ["--pan-mode", "upright", "--upright-full", "20", "--upright-cap", "45"]


def gray_frame(video, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(video), "-frames:v", "1", "-vf",
                          "scale=1280:720,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(720, 1280).astype(int) if len(raw) == 921600 else None


def find_heads(video):
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(video)], capture_output=True, text=True).stdout)
    for t in np.arange(1, dur - 1, 0.5):
        g = gray_frame(video, t)
        if g is None:
            continue
        rows = []
        for yy in (150, 200):  # two heights: a vertical beam has the same x at both
            xs = np.where(g[yy, 300:700] > 35)[0] + 300
            groups = np.split(xs, np.where(np.diff(xs) > 3)[0] + 1) if len(xs) else []
            rows.append([float(x.mean()) for x in groups if len(x)])
        if len(rows[0]) == 8 and len(rows[1]) == 8 and np.abs(np.array(rows[0]) - rows[1]).max() < 2.0:
            c = rows[1]
        else:
            continue
        if np.ptp(np.diff(c)) < 4:
            bottoms = []
            for x in c:
                xi, y = int(round(x)), 200
                while y < 719 and g[y + 1, xi - 1:xi + 2].max() > 35:
                    y += 1
                bottoms.append(y)
            y = int(np.median(bottoms)) + 12
            return ";".join(f"{int(round(x))},{y}" for x in c), t
    sys.exit(f"{video.name}: no frame with 8 evenly spaced vertical beams; measure the heads by hand")


def prep(vid, slug):
    subprocess.run([sys.executable, str(ROOT / "scripts" / "fetch_video.py"), f"https://www.youtube.com/watch?v={vid}",
                    "--audio"], check=True, capture_output=True)
    for ext in ("mp4", "mp3"):
        src = CACHE / f"{vid}.{ext}"
        if not src.exists():
            sys.exit(f"missing {src} (a video with no audio track cannot be sequenced)")
        (VID / f"{slug}.{ext}").write_bytes(src.read_bytes())
    heads, t = find_heads(VID / f"{slug}.mp4")
    (VID / f"{slug}_heads.txt").write_text(heads)
    print(f"{slug}: heads {heads} (found at {t:.0f} s)", flush=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "video_beam_analysis.py"), str(VID / f"{slug}.mp4"),
                    str(VID / f"{slug}_beams.json"), "--heads", heads] + ANALYSIS, check=True,
                   stdout=open(VID / f"{slug}_analysis.log", "w"), stderr=subprocess.STDOUT)
    print(f"{slug}: analysis done", flush=True)


def reanalyze(slug):
    """Re-measure the heads (strict vertical-beam test) and re-run the beam analysis on a video already in test_videos."""
    heads, t = find_heads(VID / f"{slug}.mp4")
    (VID / f"{slug}_heads.txt").write_text(heads)
    print(f"{slug}: heads {heads} (found at {t:.0f} s)", flush=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "video_beam_analysis.py"), str(VID / f"{slug}.mp4"),
                    str(VID / f"{slug}_beams.json"), "--heads", heads] + ANALYSIS, check=True,
                   stdout=open(VID / f"{slug}_analysis.log", "w"), stderr=subprocess.STDOUT)
    print(f"{slug}: analysis done", flush=True)


def beam_stats(slug):
    b = json.load(open(VID / f"{slug}_beams.json"))
    det = [h for fr in b["frames"] for h in fr["heads"] if h]
    sat = np.array([h["sat"] for h in det])
    ang = np.abs([h["angle"] for h in det])
    return len(det), float(ang.max()), float((sat > 120).mean())


def build(slug, title):
    n, amax, colored = beam_stats(slug)
    white = colored < 0.02
    print(f"{slug}: {n} detections, max |angle| {amax:.1f}, saturated share {colored:.3f} -> "
          f"{'--white' if white else 'colour wheel palette'}")
    cmd = [sys.executable, str(ROOT / "scripts" / "video_beams_to_xsq.py"), str(VID / f"{slug}_beams.json"), title,
           "--audio", str(VID / f"{slug}.mp3")] + UPRIGHT + (["--white"] if white else [])
    out = subprocess.run(cmd, capture_output=True, text=True)
    print(out.stdout.strip().splitlines()[-1] if out.stdout.strip() else out.stderr[-500:])


def side(slug, render, out):
    heads = (VID / f"{slug}_heads.txt").read_text().split(";")
    y = int(heads[0].split(",")[1]) - 147
    white = beam_stats(slug)[2] < 0.02
    src = ("lutyuv=y='clip(val*10-80,0,255)':u=128:v=128" if white else "eq=gamma=0.5:brightness=0.04:saturation=1.4")
    fc = (f"[0:v]scale=1280:720,crop=300:180:340:{y},{src},fps=25,scale=1000:600:flags=bicubic,setsar=1[a];"
          f"[1:v]fps=25,crop=1500:700:190:300,eq=brightness=0.08:gamma=0.7,scale=1286:600,setsar=1[b];[a][b]hstack=inputs=2[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(VID / f"{slug}.mp4"), "-i", render, "-filter_complex", fc,
                    "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-shortest",
                    str(VID / f"{out}_side_by_side.mp4")], check=True)
    print(VID / f"{out}_side_by_side.mp4")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prep"); p.add_argument("vid"); p.add_argument("slug")
    r = sub.add_parser("reanalyze"); r.add_argument("slug")
    b = sub.add_parser("build"); b.add_argument("slug"); b.add_argument("title")
    s = sub.add_parser("side"); s.add_argument("slug"); s.add_argument("render"); s.add_argument("out")
    a = ap.parse_args()
    if a.cmd == "prep":
        prep(a.vid, a.slug)
    elif a.cmd == "reanalyze":
        reanalyze(a.slug)
    elif a.cmd == "build":
        build(a.slug, a.title)
    else:
        side(a.slug, a.render, a.out)


if __name__ == "__main__":
    main()
