"""Choosin Texas - middle upper window (Matrix Seeds, 28x41): the living-room tree, decorated across the song.

Verse 1 bare tree; chorus 1 lights come on one per beat; verse 2 ornaments go on; chorus 2 gold tinsel winds on;
last chorus the Lone Star goes on top on TEXAS and presents appear; lights flash white on every TELL.
    python matrix_storybook.py stories/choosin_window_tree.py SEQ.xsq OUT.mp4 --size 28x41 --k 1 --ss 4 --scale 20 --flat --fps 40 --jobs 10
"""

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matrix_storybook as mb  # noqa: E402
from choosin_windows_common import C1, C2, C3, P, V2, fade_end, outside_snow, tm_after, window, words  # noqa: E402
from matrix_storybook import Scene, ease, glow, icon, kick  # noqa: E402
from PIL import ImageDraw  # noqa: E402

BLACK = mb.fill((0, 0, 0))
CX, TOP, BASE = 14.0, 6.0, 33.0
LIGHT_COLS = [(255, 40, 40), (40, 220, 60), (255, 210, 40), (60, 140, 255), (255, 80, 220)]
ORN_COLS = [(230, 30, 40), (255, 200, 40), (60, 120, 255), (220, 220, 230)]


def half_width(y):
    """Tree half-width at height y (three tiers)."""
    if y < TOP or y > BASE:
        return -1
    tiers = [(TOP, 15.0, 6.5), (13.0, 23.5, 9.5), (20.0, BASE, 12.0)]
    w = -1
    for t0, t1, wmax in tiers:
        if t0 <= y <= t1:
            w = max(w, wmax * (y - t0) / (t1 - t0) + 1.0)
    return w


def inside_points(n, seed, margin=1.2):
    rnd = random.Random(seed)
    pts = []
    while len(pts) < n:
        y = rnd.uniform(TOP + 3, BASE - 1)
        hw = half_width(y) - margin
        if hw > 0.5:
            pts.append((CX + rnd.uniform(-hw, hw), y))
    pts.sort(key=lambda p: p[1])  # top to bottom: lights/ornaments fill downward
    return pts


def tree_body() -> mb.Layer:
    def draw(f):
        d = ImageDraw.Draw(f.img)
        d.rectangle([P(CX - 1.5), P(BASE), P(CX + 1.5), P(BASE + 3)], fill=(110, 60, 25, 255))
        for y10 in range(int(TOP * 10), int(BASE * 10) + 1, 2):
            y = y10 / 10
            hw = half_width(y)
            if hw > 0:
                shade = (20, 105, 40) if (y10 // 25) % 2 else (25, 125, 50)
                d.line([P(CX - hw), P(y), P(CX + hw), P(y)], fill=shade + (255,), width=max(1, mb.SS // 4))
    return draw


def lights(pts, on_times, tells) -> mb.Layer:
    def draw(f):
        d = ImageDraw.Draw(f.img)
        flash = kick(tells, f.t, 0.3)
        for i, ((x, y), t_on) in enumerate(zip(pts, on_times)):
            if f.t < t_on:
                continue
            c = LIGHT_COLS[i % len(LIGHT_COLS)]
            b = 0.7 + 0.3 * (0.5 + 0.5 * math.sin(f.t * 3 + i * 1.7)) ** 2
            if f.t - t_on < 0.2:
                b = 1.0
            c = tuple(min(255, round(v * b + (255 - v * b) * flash)) for v in c)
            mb.dot(d, x, y, c + (255,), 0.75)
    return draw


def ornaments(pts, on_times) -> mb.Layer:
    def draw(f):
        d = ImageDraw.Draw(f.img)
        for i, ((x, y), t_on) in enumerate(zip(pts, on_times)):
            if f.t < t_on:
                continue
            r = 0.9 + 0.5 * max(0.0, 1 - (f.t - t_on) / 0.25)
            c = ORN_COLS[i % len(ORN_COLS)]
            d.ellipse([P(x - r), P(y - r), P(x + r), P(y + r)], fill=c + (255,))
            mb.dot(d, x - 0.3, y - 0.4, (255, 255, 255, 255), 0.25)
    return draw


def tinsel(start, dur=3.0) -> mb.Layer:
    """Three gold swags winding down the tree, drawn in over dur seconds."""
    swags = [(10.5, 14.0), (17.5, 21.5), (25.0, 30.5)]

    def draw(f):
        if f.t < start:
            return
        d = ImageDraw.Draw(f.img)
        k = min(1.0, (f.t - start) / dur)
        for i, (ya, yb) in enumerate(swags):
            kk = max(0.0, min(1.0, k * 3 - i))
            if kk <= 0:
                continue
            steps = 24
            pts = []
            for j in range(int(steps * kk) + 1):
                u = j / steps
                y = ya + (yb - ya) * u
                hw = half_width(y) - 0.3
                x = CX - hw + 2 * hw * u
                y += math.sin(u * math.pi * 3) * 0.5
                pts.append((P(x), P(y)))
            if len(pts) > 1:
                glint = 0.8 + 0.2 * math.sin(f.t * 6 + i)
                d.line(pts, fill=(round(255 * glint), round(200 * glint), 40, 255), width=mb.LW())
    return draw


def star(at, pulses) -> mb.Layer:
    def draw(f):
        if f.t < at:
            return
        e = ease(min(1.0, (f.t - at) / 0.35))
        r = 2.6 * e * (1 + 0.35 * kick(pulses, f.t, 0.3))
        glow(CX, TOP - 0.5, 6 * e, (255, 200, 60), 0.4)(f)
        d = ImageDraw.Draw(f.img)
        pts = []
        for j in range(10):
            a = -math.pi / 2 + j * math.pi / 5
            rr = r if j % 2 == 0 else r * 0.45
            pts.append((P(CX + rr * math.cos(a)), P(TOP - 0.5 + rr * math.sin(a))))
        d.polygon(pts, fill=(255, 215, 50, 255))
    return draw


def build(tm):
    beats = tm.beats
    tells = words(tm, "TELL")
    light_pts = inside_points(22, seed=5)
    light_on = [b for b in beats if b >= C1][:len(light_pts)]
    orn_pts = inside_points(12, seed=9, margin=1.6)
    orn_on = [b for b in beats if b >= V2 + 0.2][::2][:len(orn_pts)]
    star_at = tm_after(tm, "TEXAS", C3)
    gifts = [b for b in beats if b >= tm_after(tm, "BY", C3)]
    layers = [BLACK, outside_snow(10, seed=31),
              glow(CX, 22, 16, (255, 170, 80), lambda f: 0.12 if f.t >= C1 else 0.05),
              tree_body(), tinsel(C2 + 0.2), ornaments(orn_pts, orn_on), lights(light_pts, light_on, tells),
              star(star_at, tells),
              icon("🎁", 7, 8.0, 35.0, at=gifts[0], enter="drop", enter_s=0.3),
              icon("🎁", 6, 20.5, 35.5, at=gifts[2], enter="drop", enter_s=0.3),
              icon("🎁", 5, 14.0, 36.5, at=gifts[4], enter="drop", enter_s=0.3),
              window(curtain_w=3.0, sill_h=2.0), fade_end(tm)]
    return [Scene(0.0, layers, "tree")]
