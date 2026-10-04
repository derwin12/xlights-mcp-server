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
            find_heads.bottom = int(np.median(bottoms))
            return ";".join(f"{int(round(x))},{y}" for x in c), t
    sys.exit(f"{video.name}: no frame with 8 evenly spaced vertical beams; measure the heads by hand")


def find_heads_by_beams(video):
    """Fallback when no frame has all 8 beams vertical: collect the x of every tall vertical beam over the whole video, cluster the
    columns and expect 8 evenly spaced clusters. Returns (heads string, beam bottom y)."""
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(video)], capture_output=True, text=True).stdout)
    hist = np.zeros(800)
    bots = []
    for t in np.arange(0.5, dur - 0.5, 0.25):
        g = gray_frame(video, t)
        if g is None:
            continue
        for x0 in range(200, 800):
            if (g[30:200, x0] > 60).sum() >= 120:  # a tall vertical bright run above the head row
                hist[x0] += 1
                y = 200
                while y < 400 and g[y + 1, x0] > 35:
                    y += 1
                bots.append(y)
    clusters, cur = [], []
    for x in range(200, 800):
        if hist[x] > 0:
            cur.append(x)
        elif cur:
            clusters.append(cur)
            cur = []
    cent = [float(np.average(c, weights=hist[c])) for c in clusters if hist[c].sum() >= 8]
    # The 8 heads are evenly spaced: fit x = x0 + k * step to the clusters (a head that never fired leaves a gap; noisy
    # clusters sit a few px off) and generate all 8 from the fit.
    if len(cent) < 5:
        sys.exit(f"{video.name}: only {len(cent)} beam clusters {[round(c) for c in cent]}; measure by hand")
    step = float(np.median([d / max(1, round(d / 29.0)) for d in np.diff(cent)]))
    ks = [int(round((c - cent[0]) / step)) for c in cent]
    if len(set(ks)) != len(ks) or max(ks) > 7:
        sys.exit(f"{video.name}: beam clusters {[round(c) for c in cent]} do not fit 8 evenly spaced heads; measure by hand")
    A = np.polyfit(ks, cent, 1)  # slope = step, intercept = x of the first cluster
    resid = float(np.abs(np.polyval(A, ks) - cent).max())
    if resid > 5:
        sys.exit(f"{video.name}: even-spacing fit is {resid:.1f} px off; measure by hand")
    if max(ks) - min(ks) + 1 != 8:  # the clusters must span all 8 head slots (a missing one in the middle is fine)
        sys.exit(f"{video.name}: clusters {[round(c) for c in cent]} span {max(ks) - min(ks) + 1} head slots, not 8; measure by hand")
    cent = [float(A[1] + A[0] * k) for k in range(8)]
    bottom = int(np.median(bots))
    return ";".join(f"{int(round(x))},{bottom + 12}" for x in cent), bottom


def fan_window(video):
    """Start of a 3 s stretch with the most lit pixels above the head row (a wide fan), for tuning the head y."""
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(video)], capture_output=True, text=True).stdout)
    best = (0, 5.0)
    for t in np.arange(2, dur - 4, 1.0):
        g = gray_frame(video, t)
        if g is not None:
            lit = int((g[0:220, 250:760] > 60).sum())
            if lit > best[0]:
                best = (lit, float(t))
    return max(0.0, best[1] - 0.5)


def tune_y(video, heads, bottom):
    """Head y that finds the most beams on a fan window. For a strongly leaning beam a few px of y error shifts the expected beam
    sideways past the detector's tolerance, so the outer heads of a fan vanish (Wrap Me Up: bottom+12 found 87 of 176 frames on head 1,
    bottom+2 found 176)."""
    xs = [int(h.split(",")[0]) for h in heads.split(";")]
    start = fan_window(video)
    cands = [bottom + d for d in range(-4, 35, 3)]  # the beam bottom can sit well above the head when beams fade toward it
    procs = []
    for y in cands:
        hs = ";".join(f"{x},{y}" for x in xs)
        out = VID / f"_tune_{video.stem}_{y}.json"
        procs.append((y, out, subprocess.Popen([sys.executable, str(ROOT / "scripts" / "video_beam_analysis.py"), str(video), str(out),
                                                 "--heads", hs] + ANALYSIS + ["--start", str(start), "--duration", "3"],
                                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)))
    score = {}
    for y, out, pr in procs:
        pr.wait()
        b = json.load(open(out))
        score[y] = sum(1 for fr in b["frames"] for h in fr["heads"] if h)
        out.unlink()
    best = max(score.values())
    y = min((c for c in cands if score[c] >= 0.97 * best), key=lambda c: abs(c - sorted(k for k in cands if score[k] >= 0.97 * best)[len(sorted(k for k in cands if score[k] >= 0.97 * best)) // 2]))
    print(f"{video.stem}: y tuning on {start:.1f}-{start + 3:.1f} s {score} -> y={y}", flush=True)
    return ";".join(f"{x},{y}" for x in xs)


def locate_heads(video):
    """Strict vertical-beam frame if there is one, else cluster the beams over the whole video."""
    try:
        heads, t = find_heads(video)
        locate_heads.bottom = find_heads.bottom
        return heads, t
    except SystemExit:
        heads, bottom = find_heads_by_beams(video)
        locate_heads.bottom = bottom
        print(f"{video.stem}: no frame with 8 vertical beams; heads from beam clusters", flush=True)
        return heads, -1


def prep(vid, slug):
    subprocess.run([sys.executable, str(ROOT / "scripts" / "fetch_video.py"), f"https://www.youtube.com/watch?v={vid}",
                    "--audio"], check=True, capture_output=True)
    for ext in ("mp4", "mp3"):
        src = CACHE / f"{vid}.{ext}"
        if not src.exists():
            sys.exit(f"missing {src} (a video with no audio track cannot be sequenced)")
        (VID / f"{slug}.{ext}").write_bytes(src.read_bytes())
    heads, t = locate_heads(VID / f"{slug}.mp4")
    heads = tune_y(VID / f"{slug}.mp4", heads, locate_heads.bottom)
    (VID / f"{slug}_heads.txt").write_text(heads)
    print(f"{slug}: heads {heads} (found at {t:.0f} s)", flush=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "video_beam_analysis.py"), str(VID / f"{slug}.mp4"),
                    str(VID / f"{slug}_beams.json"), "--heads", heads] + ANALYSIS, check=True,
                   stdout=open(VID / f"{slug}_analysis.log", "w"), stderr=subprocess.STDOUT)
    print(f"{slug}: analysis done", flush=True)


def reanalyze(slug):
    """Re-measure the heads (strict vertical-beam test) and re-run the beam analysis on a video already in test_videos."""
    heads, t = locate_heads(VID / f"{slug}.mp4")
    heads = tune_y(VID / f"{slug}.mp4", heads, locate_heads.bottom)
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
