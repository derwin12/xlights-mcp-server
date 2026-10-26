"""Per-song look for enhance_layout.py: a colour story from the song's own video and a shader rotation picked per song.

    python scripts/song_look.py VIDEO.mp4 [--name "Artist - Title"]   # prints the hues, the story and the shaders

Colours: frames are sampled from the video, dark and grey pixels are ignored, and the strongest hues (at least 40 degrees
apart) become the story. Hue 1 leads the verses and chorus A, hue 2 leads chorus B, peaks are white with both, the outro
is hue 3 with white. Every colour is pushed to full LED saturation; the video only decides *which* hues. A video with one
strong hue gets its complement as hue 2 and a neighbour as hue 3. Sparkles are the complement of each section's lead hue.

Shaders: scripts/shader_pool.json (the user's own shaders and settings, grouped calm / drive / peak). The song name seeds
the choice, so a rebuild gives the same look and different songs get different sets.
"""
from __future__ import annotations

import argparse
import colorsys
import hashlib
import json
import random
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
POOL = HERE / "shader_pool.json"
WHITE = "#FFFFFF"


def video_hues(video: Path, n: int = 3, step_s: float = 2.0) -> list[tuple[float, float]]:
    """[(hue 0-360, share of the coloured light)] of the video's strongest hues, strongest first."""
    import numpy as np  # only needed here

    w, h = 48, 27
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={1 / step_s},scale={w}:{h}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    px = np.frombuffer(raw, np.uint8).reshape(-1, 3).astype(float) / 255
    mx, mn = px.max(1), px.min(1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    keep = (mx > 0.2) & (sat > 0.25)
    if keep.sum() < 50:
        return []
    r, g, b = px[keep].T
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    weight = sat[keep] * mx[keep]
    hist = np.bincount((hue // 10).astype(int) % 36, weights=weight, minlength=36)
    hist = np.convolve(np.r_[hist[-1:], hist, hist[:1]], [0.25, 0.5, 0.25], "valid")  # smooth, wrapping round
    total, picks = hist.sum(), []
    for i in np.argsort(hist)[::-1]:
        hd = i * 10 + 5
        if hist[i] < 0.04 * total or len(picks) == n:
            break
        if all(min(abs(hd - p), 360 - abs(hd - p)) >= 40 for p, _ in picks):
            picks.append((float(hd), float(hist[i] / total)))
    return picks


def hx(h: float, s: float = 1.0, v: float = 1.0) -> str:
    r, g, b = colorsys.hsv_to_rgb((h % 360) / 360, s, v)
    return "#" + "".join(f"{round(c * 255):02X}" for c in (r, g, b))


def _section(a: float, b: float | None, soft: bool = False, deep: bool = False) -> dict:
    """Roles for one section: hue a leads, b is the accent (None = white)."""
    v = 0.85 if deep else 1.0
    acc = (lambda s=1.0: WHITE) if b is None else (lambda s=1.0: hx(b, s, v))
    if soft:  # verses: shades of one hue
        return {"outline": (hx(a, 0.9), hx(a, 0.35)), "trees": (hx(a, 0.35), hx(a, 0.8)),
                "arches": (hx(a + 15), hx(a, 0.5)), "stars": (hx(a, 0.6), WHITE), "topper": (WHITE, hx(a, 0.9)),
                "icicles": (hx(a, 0.3), hx(a, 0.12)), "flood": (hx(a, 1, 0.75), hx(a, 0.9)),
                "megatree": (hx(a, 0.75), hx(a + 20), hx(a, 0.2))}
    return {"outline": (hx(a, 1, v), acc()), "trees": (hx(a, 1, v), acc(0.8)), "arches": (acc(), hx(a, 0.6, v)),
            "stars": (acc(0.5), WHITE), "topper": (WHITE, hx(a, 1, v)), "icicles": (hx(a, 0.5), WHITE),
            "flood": (hx(a, 1, 0.7), hx(a, 1, v)), "megatree": (hx(a, 1, v), acc(), WHITE)}


def make_story(hues: list[float]) -> tuple[dict, dict]:
    """(PALETTES-shaped dict, sparkle colour per section) from up to 3 hues."""
    h1 = hues[0]
    h2 = hues[1] if len(hues) > 1 else h1 + 180
    h3 = hues[2] if len(hues) > 2 else h1 - 45
    peak = _section(h2, h1)
    peak.update(outline=(WHITE, hx(h2)), arches=(WHITE, hx(h1)), stars=(WHITE, hx(h2)), topper=(hx(h2), WHITE),
                icicles=(hx(h2, 0.2), WHITE), flood=(hx(h2, 0.4), WHITE), megatree=(WHITE, hx(h2), hx(h1)))
    story = {"verse": _section(h1, None, soft=True), "chorusA": _section(h1, h2), "chorusB": _section(h2, h3),
             "peak": peak, "outro": _section(h3, None, deep=True)}
    lead = {"verse": h1, "chorusA": h1, "chorusB": h2, "peak": h2, "outro": h3}
    return story, {k: hx(h + 180) for k, h in lead.items()}


def shader_rotation(name: str) -> tuple[dict, dict]:
    """({story: [shader, ...]}, {shader: settings}) for this song: verse 3 calm, outro 2 calm, chorusA 2 drive,
    chorusB 3 drive, peak 2 peak, no shader in two stories."""
    pool = json.loads(POOL.read_text(encoding="utf-8"))["shaders"]
    rng = random.Random(int(hashlib.sha1(name.encode("utf-8")).hexdigest()[:12], 16))
    by = {m: sorted(n for n, v in pool.items() if v["mood"] == m) for m in ("calm", "drive", "peak")}
    for names in by.values():
        rng.shuffle(names)
    pick = {"verse": by["calm"][:3], "outro": by["calm"][3:5], "chorusA": by["drive"][:2],
            "chorusB": by["drive"][2:5], "peak": by["peak"][:2]}
    return pick, {n: v["settings"] for n, v in pool.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--name", default="")
    a = ap.parse_args()
    hues = video_hues(Path(a.video))
    print("hues:", [(round(h), round(w, 2)) for h, w in hues])
    story, sparkle = make_story([h for h, _ in hues] or [35])
    for k, roles in story.items():
        print(f"{k:8s}", roles["trees"], roles["megatree"], "sparkle", sparkle[k])
    if a.name:
        print(json.dumps(shader_rotation(a.name)[0], indent=1))


if __name__ == "__main__":
    main()
