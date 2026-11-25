"""Choosin Texas - left upper window (Window Frame-Upper-1 Matrix, 13x27): a candle in the window.

It flickers all song, flares on TEXAS, blows out on each LEAVE (smoke curls up), stays dark through
"drinkin Jack all by myself", and relights on the next "Texas" line.
    python matrix_storybook.py stories/choosin_window_candle.py SEQ.xsq OUT.mp4 --size 13x27 --k 1 --ss 4 --scale 20 --flat --fps 40 --jobs 10
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matrix_storybook as mb  # noqa: E402
from choosin_windows_common import P, fade_end, outside_snow, window, words  # noqa: E402
from matrix_storybook import Scene, ease, glow, kick  # noqa: E402
from PIL import ImageDraw  # noqa: E402

BLACK = mb.fill((0, 0, 0))


def candle(cx, base, height, outs, flares, light_at) -> mb.Layer:
    """outs: [(blow_out, relight)] times. Flame shrinks out over 0.4 s and regrows over 0.3 s."""

    def level(t):
        if t < light_at:
            return 0.0
        lv = min(1.0, (t - light_at) / 0.6)
        for a, b in outs:
            if a <= t < b:
                return max(0.0, 1 - (t - a) / 0.4)
            if b <= t < b + 0.3:
                lv = min(lv, (t - b) / 0.3)
        return lv

    def smoke(t):
        return any(a + 0.3 <= t < a + 2.6 for a, _b in outs)

    def draw(f):
        d = ImageDraw.Draw(f.img)
        top = base - height
        lv = level(f.t)
        fl = 1 + 0.6 * kick(flares, f.t, 0.35)
        if lv > 0:
            glow(cx, top - 2, 6.5 * fl, (255, 150, 40), 0.35 * lv)(f)
        # candle body, wax drip, holly at the base
        d.rectangle([P(cx - 1.2), P(top), P(cx + 1.2), P(base)], fill=(235, 225, 195, 255))
        d.rectangle([P(cx + 0.4), P(top), P(cx + 1.2), P(top + 1.5)], fill=(255, 250, 230, 255))
        for dx, c in ((-1.8, (30, 150, 50)), (1.8, (30, 150, 50)), (0, (230, 30, 40))):
            mb.dot(d, cx + dx, base - 0.6, c + (255,), 0.8)
        d.line([P(cx), P(top), P(cx), P(top - 0.8)], fill=(60, 40, 30, 255), width=mb.LW())  # wick
        if lv > 0:
            fx = cx + math.sin(f.t * 9) * 0.25 + math.sin(f.t * 23) * 0.15
            h = (2.2 + 0.4 * math.sin(f.t * 13)) * lv * fl
            w = 0.9 * lv * (0.8 + 0.2 * fl)
            d.ellipse([P(fx - w), P(top - 0.8 - h * 2), P(fx + w), P(top - 0.4)], fill=(255, 130, 20, 255))
            d.ellipse([P(fx - w * 0.5), P(top - 0.8 - h * 1.2), P(fx + w * 0.5), P(top - 0.6)],
                      fill=(255, 235, 140, 255))
        if smoke(f.t):
            mb.steam(cx, top - 1.5, n=1, height=7, color=(120, 120, 130))(f)
    return draw


def build(tm):
    leaves = words(tm, "LEAVE")
    # relight on the next "Texas" line after each LEAVE
    relights = [min(s for s in words(tm, "HE'S") + words(tm, "CAUSE") if s > a) for a in leaves]
    flares = words(tm, "TEXAS")
    return [Scene(0.0, [BLACK, outside_snow(6, seed=11), candle(6.5, 25, 8, list(zip(leaves, relights)), flares,
                                                                 light_at=words(tm, "JUST")[0]),
                        window(curtain_w=2.2), fade_end(tm)], "candle")]
