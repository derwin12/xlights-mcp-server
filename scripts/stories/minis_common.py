"""Shared helpers for the ShowFolder3D mini-matrix storybooks (Matrix-mini-left/right, 25x24).

Many of these older sequences have no "Lyrics"/"Beats"/"Bars" tracks under those names, so the stories load word
timing from another timing track (e.g. "Lyric Main") or from a faster-whisper word list (stories/lyrics/*.json),
and make bars from every 4th beat. Word labels are normalised to lower case without punctuation.
"""

import json
import math
import random
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matrix_storybook as mb  # noqa: E402
from matrix_storybook import Scene, icon, kick, sky  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

SHOW = Path("E:/2023/ShowFolder3D")
LYRICS = Path(__file__).resolve().parent / "lyrics"
W, H = 25, 24
BOX = (0, 0, W, H)
BLACK = sky((0, 0, 0), (0, 0, 0))
WHITE = (255, 255, 255)
RED = (255, 50, 40)
GREEN = (60, 230, 90)
GOLD = (255, 205, 40)
ICE = (140, 210, 255)
PURPLE = (190, 90, 255)
PINK = (255, 90, 200)


def P(v):
    return v * mb.SS


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9']", "", s.lower())


def track(xsq, name, layer=0):
    """(label, start, end) of a timing track's layer."""
    root = ET.parse(xsq).getroot()
    for el in root.iter("Element"):
        if el.get("type") == "timing" and el.get("name") == name:
            layers = el.findall("EffectLayer")
            if layer < len(layers):
                return [(e.get("label") or "", int(e.get("startTime")) / 1000, int(e.get("endTime")) / 1000)
                        for e in layers[layer]]
    # the timing rows also appear inside ElementEffects
    for el in root.find("ElementEffects"):
        if el.get("name") == name:
            layers = el.findall("EffectLayer")
            if layer < len(layers):
                return [(e.get("label") or "", int(e.get("startTime")) / 1000, int(e.get("endTime")) / 1000)
                        for e in layers[layer]]
    return []


def words_from_track(tm, xsq, name, layer=1):
    tm.words = [(norm(lab), s, e) for lab, s, e in track(xsq, name, layer) if lab]


def words_from_json(tm, stem):
    tm.words = [(norm(a), s, e) for a, s, e in json.load(open(LYRICS / f"{stem}.json"))]


def beats_from_marks(tm, marks, per=4):
    """Beats by splitting each gap between marks (e.g. bar marks) into `per` parts."""
    out = []
    for a, b in zip(marks, marks[1:]):
        out += [a + (b - a) * k / per for k in range(per)]
    out.append(marks[-1])
    tm.beats = out


def steady_beats(tm, period=1.0):
    tm.beats = [k * period for k in range(int(tm.duration / period) + 1)]


def bars(tm, every=4, phase=0):
    return tm.bars or tm.beats[phase::every]


def w(tm, word, t=0.0):
    """Start of the first sung `word` at or after time t."""
    word = norm(word)
    for label, s, _e in tm.words:
        if label == word and s >= t - 0.05:
            return s
    raise KeyError(f"{word} after {t}")


def ws(tm, word, t0, t1):
    word = norm(word)
    return [s for label, s, _e in tm.words if label == word and t0 <= s < t1]


def big(start, emoji, size=17, x=12.5, y=12.5, bg=(), extra=(), name="", cut=False, **kw):
    """One big picture on black, with background layers under it and extra layers over it."""
    kw.setdefault("motion", "bob")
    return Scene(start, [BLACK, *bg, icon(emoji, size, x, y, **kw), *extra], name or emoji, cut=cut)


# ---------------------------------------------------------------- drawn props (story pixels, 25x24)

def red_nose(x, y, hits=None, at=None, r=1.0, glow_r=4.0, strength=0.8):
    """Rudolph's nose: a red dot with a pulsing glow (bigger on hits)."""

    def draw(f):
        if at is not None and f.t < at:
            return
        k = kick(hits, f.t, 0.35) if hits else 0.0
        xx, yy = mb.val(x, f), mb.val(y, f)
        rr = glow_r * (1 + 0.5 * k)
        lay = Image.new("RGBA", f.img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for i in range(6, 0, -1):
            q = i / 6
            a = round(255 * strength * (1 - q) ** 1.5 * (0.7 + 0.3 * k))
            d.ellipse([P(xx - rr * q), P(yy - rr * q), P(xx + rr * q), P(yy + rr * q)], fill=(255, 30, 20, a))
        f.img.alpha_composite(lay)
        d = ImageDraw.Draw(f.img)
        d.ellipse([P(xx - r), P(yy - r), P(xx + r), P(yy + r)], fill=(255, 40, 30, 255))
    return draw


def fog(alpha=0.5, seed=4, speed=1.5):
    """Grey drifting bands."""
    rnd = random.Random(seed)
    bands = [(rnd.uniform(0, H), rnd.uniform(2, 4), rnd.uniform(0.6, 1.4), rnd.uniform(0, 6)) for _ in range(5)]

    def draw(f):
        a = mb.val(alpha, f)
        lay = Image.new("RGBA", f.img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for y, hgt, sp, ph in bands:
            for i in range(-1, 3):
                x0 = (f.t * speed * sp + ph * 5) % 20 - 20 + i * 20
                d.ellipse([P(x0), P(y - hgt / 2), P(x0 + 16), P(y + hgt / 2)], fill=(150, 150, 165, round(110 * a)))
        f.img.alpha_composite(lay)
    return draw


def aurora(colors=((40, 255, 140), (60, 160, 255), (180, 80, 255)), y=5.0, amp=2.0, strength=0.55):
    """Northern lights: soft wavy bands across the sky."""

    def draw(f):
        lay = Image.new("RGBA", f.img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for k, c in enumerate(colors):
            for xi in range(W * 2):
                x = xi / 2
                yy = y + k * 2.2 + math.sin(x * 0.45 + f.t * (0.6 + 0.2 * k) + k) * amp
                b = 0.5 + 0.5 * math.sin(x * 0.3 - f.t * 0.9 + k * 2)
                a = round(255 * strength * b)
                d.rectangle([P(x), P(yy - 1.2), P(x + 0.5), P(yy + 1.2)], fill=c + (a,))
        f.img.alpha_composite(lay)
    return draw


def cauldron(cx=12.5, top=14.0, wd=15.0, brew=(60, 255, 80), hits=None, seed=8):
    """A black iron pot on legs with a glowing brew and bubbles that rise and pop (more on hits)."""
    rnd = random.Random(seed)
    bub = [(rnd.uniform(-wd / 2 + 2, wd / 2 - 2), rnd.uniform(0, 1), rnd.uniform(0.7, 1.3)) for _ in range(7)]

    def draw(f):
        d = ImageDraw.Draw(f.img)
        k = kick(hits, f.t, 0.4) if hits else 0.0
        # glow over the brew
        lay = Image.new("RGBA", f.img.size, (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        for i in range(5, 0, -1):
            q = i / 5
            dl.ellipse([P(cx - wd * 0.7 * q), P(top - 6 * q), P(cx + wd * 0.7 * q), P(top + 2 * q)],
                       fill=brew + (round(90 * (1 - q) * (0.6 + 0.4 * k)),))
        f.img.alpha_composite(lay)
        # legs, pot body, rim
        d.rectangle([P(cx - wd / 2 + 1), P(top + 7), P(cx - wd / 2 + 2.5), P(H)], fill=(55, 55, 65, 255))
        d.rectangle([P(cx + wd / 2 - 2.5), P(top + 7), P(cx + wd / 2 - 1), P(H)], fill=(55, 55, 65, 255))
        d.ellipse([P(cx - wd / 2), P(top - 1), P(cx + wd / 2), P(top + 9)], fill=(45, 45, 55, 255))
        d.rectangle([P(cx - wd / 2 - 0.5), P(top - 1), P(cx + wd / 2 + 0.5), P(top + 0.6)], fill=(90, 90, 105, 255))
        d.rectangle([P(cx - wd / 2 + 1), P(top - 1.6), P(cx + wd / 2 - 1), P(top - 0.6)], fill=brew + (255,))
        # bubbles
        for x, ph, sp in bub:
            q = (f.t * 0.5 * sp * (1 + k) + ph) % 1
            yy = top - 1 - q * 9
            r = 0.6 + 0.5 * q
            c = tuple(round(v * (1 - q * 0.6)) for v in brew) + (255,)
            d.ellipse([P(cx + x - r), P(yy - r), P(cx + x + r), P(yy + r)], outline=c, width=mb.LW())
    return draw


def rays(cx=12.5, cy=12.5, n=10, colors=(PINK, ICE, GOLD, GREEN, PURPLE), spin=0.6, hits=None, strength=0.45):
    """Disco/spotlight beams spinning out from a point."""

    def draw(f):
        k = kick(hits, f.t, 0.3) if hits else 0.5
        lay = Image.new("RGBA", f.img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for i in range(n):
            a = f.t * spin + i * 2 * math.pi / n
            c = colors[i % len(colors)]
            x1, y1 = cx + math.cos(a) * 30, cy + math.sin(a) * 30
            x2, y2 = cx + math.cos(a + 0.12) * 30, cy + math.sin(a + 0.12) * 30
            d.polygon([(P(cx), P(cy)), (P(x1), P(y1)), (P(x2), P(y2))],
                      fill=c + (round(255 * strength * (0.4 + 0.6 * k)),))
        f.img.alpha_composite(lay)
    return draw


def flash(hits, color=(255, 255, 255), tau=0.15, strength=0.5):
    """Whole-matrix flash on hits (drops)."""

    def draw(f):
        k = kick(hits, f.t, tau)
        if k > 0.02:
            f.img.alpha_composite(Image.new("RGBA", f.img.size, color + (round(255 * strength * k),)))
    return draw


def flyer(emoji, size, y, t0, t1, x0=-8.0, x1=33.0, flip=False, arc=0.0, **kw):
    """A picture flying across between t0 and t1 (x0 -> x1), optionally on an arc (negative = up)."""

    def xf(f):
        q = min(1.0, max(0.0, (f.t - t0) / (t1 - t0)))
        return x0 + (x1 - x0) * q

    def yf(f):
        q = min(1.0, max(0.0, (f.t - t0) / (t1 - t0)))
        return y + arc * math.sin(q * math.pi)
    kw.setdefault("enter", None)
    return icon(emoji, size, xf, yf, at=t0, until=t1, flip=flip, **kw)


def flying_rudolph(size, y, t0, t1, x0, x1, arc=0.0):
    """The deer flying across (facing the way it goes) with its red nose glowing."""
    flip = x1 > x0

    def q(f):
        return min(1.0, max(0.0, (f.t - t0) / (t1 - t0)))

    def nx(f):
        return x0 + (x1 - x0) * q(f) + (0.30 if flip else -0.30) * size

    def ny(f):
        return y + arc * math.sin(q(f) * math.pi) - 0.15 * size
    deer = flyer("🦌", size, y, t0, t1, x0=x0, x1=x1, flip=flip, arc=arc)
    nose = red_nose(nx, ny, r=max(0.6, size / 16), glow_r=2.5)

    def draw(f):
        if t0 <= f.t < t1:
            deer(f)
            nose(f)
    return draw


def snap(tm, t):
    """Nearest beat to t (or t if there are no beats)."""
    return min(tm.beats, key=lambda b: abs(b - t)) if tm.beats else t


def spin(rate=40.0, t0=0.0):
    """Rotation (degrees) for icon(rot=...): turns steadily."""
    return lambda f: ((f.t - t0) * rate) % 360
