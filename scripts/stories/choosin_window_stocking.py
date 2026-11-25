"""Choosin Texas - right upper window (Window Frame-Upper-3 Matrix, 17x27): a red cowboy-boot stocking on a hook.

It sways in the verses and kicks on the beat in the choruses. Notes float up on the Hank tunes line, a glass of Jack
sits on the sill for "drinkin Jack", and a present pops into the stocking at the end.
    python matrix_storybook.py stories/choosin_window_stocking.py SEQ.xsq OUT.mp4 --size 17x27 --k 1 --ss 4 --scale 20 --flat --fps 40 --jobs 10
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matrix_storybook as mb  # noqa: E402
from choosin_windows_common import C1, C2, P, V2, fade_end, outside_snow, tm_after, window, words  # noqa: E402
from matrix_storybook import Scene, icon, kick, sparkles  # noqa: E402
from PIL import ImageDraw  # noqa: E402

BLACK = mb.fill((0, 0, 0))
RED, CUFF, GOLD = (210, 25, 35), (245, 245, 245), (255, 200, 40)


def rot(pts, cx, cy, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def stocking(hx, hy, beats, chorus_spans) -> mb.Layer:
    """Boot-shaped stocking hanging from a hook at (hx, hy); swings gently, kicks on beats inside chorus_spans."""

    def angle(t):
        a = 5 * math.sin(t * 2 * math.pi * 0.45)
        if any(s <= t < e for s, e in chorus_spans):
            n = sum(1 for b in beats if b <= t)
            sgn = 1 if n % 2 else -1
            a += sgn * 14 * kick(beats, t, 0.22)
        return a

    def draw(f):
        d = ImageDraw.Draw(f.img)
        g = angle(f.t)
        d.line([P(hx), P(hy - 1.5), P(hx), P(hy)], fill=(200, 200, 210, 255), width=mb.LW())  # hook
        leg = [(hx - 2.2, hy + 3), (hx + 2.2, hy + 3), (hx + 2.2, hy + 12), (hx + 1.6, hy + 14.5),
               (hx - 4.8, hy + 14.5), (hx - 5.8, hy + 12.8), (hx - 4.6, hy + 11), (hx - 2.2, hy + 10.5)]
        cuff = [(hx - 2.8, hy), (hx + 2.8, hy), (hx + 2.8, hy + 3), (hx - 2.8, hy + 3)]
        heel = [(hx + 2.2, hy + 12.5), (hx + 2.2, hy + 14.5), (hx + 0.6, hy + 14.5)]
        d.polygon([(P(x), P(y)) for x, y in rot(leg, hx, hy, g)], fill=RED + (255,))
        d.polygon([(P(x), P(y)) for x, y in rot(heel, hx, hy, g)], fill=(120, 70, 30, 255))
        d.polygon([(P(x), P(y)) for x, y in rot(cuff, hx, hy, g)], fill=CUFF + (255,))
        # gold Lone Star on the leg
        (sx, sy), = rot([(hx - 0.2, hy + 7)], hx, hy, g)
        pts = []
        for j in range(10):
            a = -math.pi / 2 + j * math.pi / 5
            r = 1.6 if j % 2 == 0 else 0.7
            pts.append((P(sx + r * math.cos(a)), P(sy + r * math.sin(a))))
        d.polygon(pts, fill=GOLD + (255,))
    return draw


def notes(at, n=3, color=(255, 200, 40)) -> mb.Layer:
    """Gold eighth notes drifting up from the sill (the emoji note is too dark on LEDs)."""
    def draw(f):
        if f.t < at:
            return
        d = ImageDraw.Draw(f.img)
        for i in range(n):
            k = ((f.t - at) * 0.35 + i / n) % 1
            x = 4.5 + i * 4 + math.sin(k * 7 + i) * 1.0
            y = 23 - k * 22
            d.ellipse([P(x - 0.9), P(y - 0.6), P(x + 0.6), P(y + 0.6)], fill=color + (255,))
            d.line([P(x + 0.5), P(y), P(x + 0.5), P(y - 3)], fill=color + (255,), width=mb.LW())
            d.line([P(x + 0.5), P(y - 3), P(x + 1.6), P(y - 2.2)], fill=color + (255,), width=mb.LW())
    return draw


def build(tm):
    end = tm.duration
    spans = [(C1, V2), (C2, end)]
    beats = tm.beats
    layers = [BLACK, outside_snow(7, seed=21), stocking(8.5, 4.5, beats, spans)]
    # Hank tunes / Memphis blues: notes float up
    layers.append(notes(tm_after(tm, "TUNES", 58.0)))
    layers[-1] = (lambda lay, t1: (lambda f: None if f.t > t1 else lay(f)))(layers[-1], tm_after(tm, "SING", 62.0) + 1.5)
    # drinkin Jack: a glass on the sill for each of those lines
    for s in words(tm, "DRINKIN"):
        layers.append(icon("🥃", 5, 13.5, 22.3, at=s, until=tm_after(tm, "MYSELF", s) + 1.2, enter="drop"))
    # finale: a present pops into the stocking
    gift = tm_after(tm, "TEXAS", 131.0)
    layers.append(icon("🎁", 5, 8.5, 3.5, at=gift, enter="pop", motion="pulse"))
    layers.append(sparkles(5, seed=23, box=(2, 0, 15, 12), color=(255, 230, 150)))
    layers[-1] = (lambda lay, t0: (lambda f: None if f.t < t0 else lay(f)))(layers[-1], gift)
    layers += [window(curtain_w=2.5), fade_end(tm)]
    return [Scene(0.0, layers, "stocking")]
