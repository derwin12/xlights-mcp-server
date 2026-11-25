"""Shared parts for the Choosin Texas window matrices in ShowFolder3D (three upper windows looking into the house):
curtains, a sill, snow outside, and the song's key times. Story pixels = LEDs (draw with P())."""

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matrix_storybook as mb  # noqa: E402
from hippopotamus_for_christmas import P, tm_after  # noqa: E402
from PIL import ImageDraw  # noqa: E402

CURTAIN = (150, 15, 30)
CURTAIN_LIGHT = (200, 40, 50)
TIEBACK = (255, 190, 40)
SILL = (110, 60, 25)

# sections of this song (seconds)
V1, C1, V2, C2, C3 = 0.0, 22.05, 51.27, 72.57, 101.34


def words(tm, word):
    """All start times of a sung word."""
    return [s for label, s, _e in tm.words if label == word]


def outside_snow(n=8, seed=1, speed=1.6) -> mb.Layer:
    """Sparse dim snow falling behind the glass."""
    rnd = random.Random(seed)
    flakes = [(rnd.uniform(0, 1), rnd.uniform(0, 1), rnd.uniform(0.7, 1.3)) for _ in range(n)]

    def draw(f):
        d = ImageDraw.Draw(f.img)
        for fx, fy, sp in flakes:
            y = ((fy * (f.H + 2) + f.t * speed * sp) % (f.H + 2)) - 1
            x = fx * f.W + math.sin(f.t * 1.3 + fy * 6) * 0.6
            c = round(150 * sp / 1.3)
            mb.dot(d, x, y, (c, c, min(255, c + 20), 255), 0.5)
    return draw


def window(curtain_w=2.0, sill_h=2.0, valance=1.5) -> mb.Layer:
    """Curtains tied back at the sides, a valance on top and a wooden sill at the bottom."""

    def draw(f):
        d = ImageDraw.Draw(f.img)
        W, H = f.W, f.H
        tie = H * 0.55
        for side in (0, 1):
            pts = []
            # curtain hangs straight, pinched in at the tieback, flares below
            for y in range(0, int(H - sill_h) + 1):
                pinch = 1.0 - 0.45 * math.exp(-((y - tie) / 3.0) ** 2)
                pts.append((curtain_w * pinch, y))
            edge = [(x if side == 0 else W - x, y) for x, y in pts]
            base = [(0 if side == 0 else W, H - sill_h), (0 if side == 0 else W, 0)]
            d.polygon([(P(x), P(y)) for x, y in edge + base], fill=CURTAIN + (255,))
            x_fold = curtain_w * 0.45 if side == 0 else W - curtain_w * 0.45
            d.line([P(x_fold), P(0), P(x_fold), P(H - sill_h)], fill=CURTAIN_LIGHT + (255,), width=max(1, mb.LW() // 2))
            tx = curtain_w * 0.55 if side == 0 else W - curtain_w * 0.55
            d.rectangle([P(tx - 0.6), P(tie - 0.4), P(tx + 0.6), P(tie + 0.4)], fill=TIEBACK + (255,))
        d.rectangle([0, 0, P(W), P(valance)], fill=CURTAIN + (255,))
        for i in range(int(W) + 1):
            if i % 3 == 1:
                mb.dot(d, i, valance, CURTAIN + (255,), 0.7)
        d.rectangle([0, P(H - sill_h), P(W), P(H)], fill=SILL + (255,))
        d.line([0, P(H - sill_h), P(W), P(H - sill_h)], fill=(170, 100, 45, 255), width=mb.LW())
    return draw


def fade_end(tm, secs=1.5) -> mb.Layer:
    return mb.dim(lambda f: mb.ease((f.t - (tm.duration - secs)) / secs))


__all__ = ["P", "tm_after", "words", "outside_snow", "window", "fade_end", "V1", "C1", "V2", "C2", "C3"]
