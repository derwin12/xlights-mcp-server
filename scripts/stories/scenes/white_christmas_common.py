"""White Christmas matrix scenes, shared plan for the garage, the two windows (one stage) and the bushes.

The MegaTree carries the SuperStar story (sleeping Zzz, the house in the snow, treetops, the sleigh bells, the
Christmas card, strings of lights, a star at the end); these scenes follow the same lyric lines on the other
matrices. A slow, gentle song: fades rather than pops, soft white/ice/gold, steady snow.
Words: faster-whisper (stories/lyrics/white_christmas.json, several lines misheard - only clean words are cued);
beats: librosa (white_christmas_beats.json came out double-time, so every other beat is used).
"""
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
from morph_backdrop import backdrop, pattern_sweeps  # noqa: E402,F401
from matrix_scenes import Cues  # noqa: E402
from rockin_common import (GOLD, GREEN, ICE, RED, WHITE, Z_BACK, Z_FRONT, Z_PIC,  # noqa: E402,F401
                           Z_WORD, bar_sweeps, sleigh_team)

LYRICS = HERE.parent / "lyrics"
SOFT = (WHITE, ICE, GOLD)
WARM = (255, 200, 90)


def cues(xsq):
    dur = float(ET.parse(xsq).getroot().findtext("head/sequenceDuration"))
    beats = json.loads((LYRICS / "white_christmas_beats.json").read_text())[::2]  # librosa doubled the tempo
    words = [(w["w"], w["s"], w["e"]) for p in json.loads((LYRICS / "white_christmas.json").read_text())
             for w in p["words"]]
    return Cues(words, beats, dur)


def plan(c):
    w = c.w
    t = [
        ("intro", 0.0),
        ("dream", w("dreaming") - 1.5),
        ("treetops", w("where", 20) - 0.1),
        ("bells", w("sleep", 32) - 0.1),
        ("dream2", w("for", 37) - 0.1),
        ("cards", w("with", 44) - 0.1),
        ("merry", w("be", 56.5) - 0.1),
        ("allwhite", w("turn", 60) - 0.1),
        ("dream", w("dreaming", 70) - 1.2),
        ("treetops", w("where", 84) - 0.1),
        ("bells", w("play", 94) - 0.1),
        ("dream2", w("yay", 99.5) - 0.1),
        ("cards", w("with", 106) - 0.1),
        ("merry", w("may", 113) - 0.1),
        ("allwhite", w("ooh", 122.5) - 0.1),
        ("lights", 133.0),
        ("jingle", w("jingle", 145) - 0.1),
        ("finale", 150.5),
    ]
    return [(n, t0, t[k + 1][1] if k + 1 < len(t) else c.duration) for k, (n, t0) in enumerate(t)]


def wf(c, t0, *words):
    """First of several possible cue words (whisper misheard some repeats); falls back to t0 + 3 s."""
    for w in words:
        try:
            return c.w(w, t0)
        except KeyError:
            pass
    return t0 + 3.0


def run(s, scenes):
    for name, t0, t1 in plan(s.cues):
        backdrop(s, t0, t1)
        fn = scenes.get(name)
        if fn:
            fn(s, t0, t1)


# ---------------------------------------------------------------- drawn props

def house(s, w, lit=True):
    """A little house with a snowy roof; windows glow when lit."""
    h = round(w * 0.85)

    def draw(d, im):
        roof = h * 0.42
        d.rectangle([w * 0.1, roof, w * 0.9, h - 1], fill=(150, 40, 30, 255))
        d.polygon([(0, roof + 1), (w / 2, 0), (w - 1, roof + 1)], fill=(90, 50, 40, 255))
        d.polygon([(w * 0.12, roof * 0.75), (w / 2, 0), (w * 0.88, roof * 0.75), (w / 2, roof * 0.35)],
                  fill=(245, 250, 255, 255))  # snow on the roof
        glow = (255, 210, 80, 255) if lit else (40, 40, 60, 255)
        ww = max(2, round(w * 0.16))
        for x in (w * 0.2, w * 0.64):
            d.rectangle([x, roof + h * 0.12, x + ww, roof + h * 0.12 + ww], fill=glow)
        d.rectangle([w * 0.44, h - h * 0.3, w * 0.56, h - 1], fill=(70, 30, 10, 255))
        d.rectangle([w * 0.72, h * 0.05, w * 0.8, roof * 0.6], fill=(120, 60, 40, 255))  # chimney
    return s.drawn(f"house_{w}_{int(lit)}", w, h, draw)


def pine(s, h, snowy=True):
    w = round(h * 0.7)

    def draw(d, im):
        trunk = max(2, w // 8)
        d.rectangle([w / 2 - trunk / 2, h * 0.85, w / 2 + trunk / 2, h - 1], fill=(100, 55, 20, 255))
        for k in range(3):
            top, bot = h * (0.0 + 0.25 * k), h * (0.45 + 0.2 * k)
            half = w * (0.25 + 0.12 * k)
            d.polygon([(w / 2, top), (w / 2 - half, bot), (w / 2 + half, bot)], fill=(0, 120, 40, 255))
            if snowy:
                d.line([(w / 2 - half, bot), (w / 2 + half, bot)], fill=(240, 250, 255, 255), width=1)
                d.polygon([(w / 2, top), (w / 2 - half * 0.3, top + (bot - top) * 0.3),
                           (w / 2 + half * 0.3, top + (bot - top) * 0.3)], fill=(240, 250, 255, 255))
    return s.drawn(f"pine_{h}_{int(snowy)}", w, h, draw)


def ground(s, w, h):
    def draw(d, im):
        d.ellipse([-w * 0.3, h * 0.2, w * 0.6, h * 3], fill=(235, 245, 255, 255))
        d.ellipse([w * 0.4, 0, w * 1.3, h * 3], fill=(215, 232, 255, 255))
    return s.drawn(f"ground_{w}_{h}", w, h, draw)


def card(s, w):
    """A Christmas card: green with a red ribbon and a little gold tree."""
    h = round(w * 0.72)

    def draw(d, im):
        d.rectangle([0, 0, w - 1, h - 1], fill=(250, 250, 250, 255))
        d.rectangle([1, 1, w - 2, h - 2], fill=(0, 130, 50, 255))
        d.rectangle([w * 0.12, 0, w * 0.2, h - 1], fill=(220, 0, 0, 255))
        cx = w * 0.6
        d.polygon([(cx, h * 0.15), (cx - w * 0.17, h * 0.75), (cx + w * 0.17, h * 0.75)], fill=(255, 200, 0, 255))
        d.rectangle([cx - 1, h * 0.75, cx + 1, h * 0.85], fill=(150, 80, 20, 255))
    return s.drawn(f"card_{w}", w, h, draw)


def candle(s, h, flame=0):
    w = max(5, round(h * 0.35))

    def draw(d, im):
        fh = h * 0.3
        d.rectangle([w * 0.2, fh, w * 0.8, h - 1], fill=(220, 20, 30, 255))
        d.rectangle([w * 0.2, fh, w * 0.35, h - 1], fill=(255, 90, 90, 255))
        lean = (-1, 0, 1)[flame % 3]
        d.ellipse([w / 2 - w * 0.3 + lean, 0, w / 2 + w * 0.3 + lean, fh], fill=(255, 190, 0, 255))
        d.ellipse([w / 2 - w * 0.12 + lean, fh * 0.35, w / 2 + w * 0.12 + lean, fh * 0.9],
                  fill=(255, 255, 200, 255))
    return s.drawn(f"candle_{h}_{flame}", w, h, draw)


def moon(s, px):
    def draw(d, im):
        d.ellipse([0, 0, px - 1, px - 1], fill=(255, 240, 170, 255))
        d.ellipse([px * 0.35, -px * 0.1, px * 1.2, px * 0.8], fill=(0, 0, 0, 0))
    return s.drawn(f"moon_{px}", px, px, draw)


def light_string(s, w, phase=0):
    """A sagging string of coloured bulbs (the tree's strings of lights)."""
    h = max(5, w // 8)
    cols = [(255, 0, 0), (0, 200, 40), (40, 120, 255), (255, 190, 0), (170, 60, 255)]

    def draw(d, im):
        pts = [(x, 1 + (h - 3) * math.sin(math.pi * x / (w - 1))) for x in range(w)]
        d.line(pts, fill=(30, 90, 30, 255), width=1)
        for k, x in enumerate(range(2, w - 1, 5)):
            y = 1 + (h - 3) * math.sin(math.pi * x / (w - 1))
            c = cols[(k + phase) % len(cols)]
            d.ellipse([x - 1, y, x + 1, y + 2], fill=c + (255,))
    return s.drawn(f"lights_{w}_{phase}", w, h, draw)


def zzz(s, scale):
    return [s.word("Z", c, scale) for c in (WHITE, ICE, GOLD)]


def float_z(s, t0, t1, x, y, scale, rise=14, every=1.6):
    """Z's drifting up and fading from a sleeper at (x, y)."""
    keys = zzz(s, scale)
    k, t = 0, t0
    while t + 2.0 < t1:
        s.pic(keys[k % 3], t, t + 2.0, x + 3 * (k % 2), y, to=(x + 6 + 3 * (k % 2), y - rise), fade_in=0.3,
              fade_out=0.6, z=Z_WORD)
        k, t = k + 1, t + every


# ================================================================ 140x60 matrix (the garage)

def g_intro(s, t0, t1):
    s.show(moon(s, 16), 0.3, t1, 122, 11, enter="fade", enter_s=2.0, z=Z_BACK)
    s.twinkle(0.3, t1, (WHITE, ICE), count=10, steps=60, fade=2.0)
    s.show(house(s, 44, lit=False), 0.5, t1, 70, 41, enter="fade", enter_s=2.5)
    float_z(s, 2.0, t1, 82, 24, 2)
    s.show(ground(s, 140, 10), 0.5, t1, 70, 56, enter="fade", enter_s=2.5, z=Z_BACK)


def g_dream(s, t0, t1):
    c = s.cues
    white, know = c.w("white", t0), c.w("know", t0)
    s.show(house(s, 44, lit=False), t0, white, 70, 41, enter=None)
    s.show(house(s, 44), white, t1, 70, 41, enter="fade", enter_s=1.5)
    s.show(ground(s, 140, 10), t0, t1, 70, 56, enter=None, z=Z_BACK)
    s.show(pine(s, 30), t0 + 1.0, t1, 22, 40, enter="fade", enter_s=2.0)
    s.show(pine(s, 26), t0 + 2.0, t1, 118, 42, enter="fade", enter_s=2.0)
    s.show(s.word("DREAMING", ICE, 2), c.w("dreaming", t0), white - 0.1, 70, 7, enter="fade", exit="fade",
           enter_s=0.8, exit_s=0.5, z=Z_WORD)
    s.show(s.word("WHITE CHRISTMAS", WHITE, 2), white, know, 70, 7, enter="fade", exit="fade", enter_s=0.8,
           exit_s=0.8, z=Z_WORD)
    s.ring(white, 70, 41, WHITE, r=60, dur=1.4, width=2)
    s.snow(t0, t1, count=10, speed=6, fade=1.0)


def g_treetops(s, t0, t1):
    c = s.cues
    children = wf(c, t0, "children", "to")
    s.show(ground(s, 140, 10), t0, t1, 70, 56, enter=None, z=Z_BACK)
    for k, (x, h) in enumerate(((16, 40), (42, 48), (98, 48), (124, 40))):
        s.show(pine(s, h), t0 + 0.6 * k, t1, x, 58 - h / 2, enter="fade", enter_s=1.5, z=Z_BACK)
    s.twinkle(t0 + 1.0, t1, (WHITE, GOLD), count=30, steps=30, fade=1.0, z=Z_FRONT + 1)
    s.show(s.word("TREETOPS GLISTEN", GOLD, 1), t0 + 0.5, children, 70, 6, enter="fade", exit="fade", z=Z_WORD)
    s.show(s.emoji("👧", 22), children, t1, 62, 44, enter="fade", enter_s=1.0)
    s.show(s.emoji("🧒", 22), children + 0.4, t1, 80, 44, enter="fade", enter_s=1.0)
    s.show(s.word("LISTEN", ICE, 2), children, t1, 70, 7, enter="fade", exit="fade", z=Z_WORD)
    s.snow(t0, t1, count=8, speed=6)


def g_bells(s, t0, t1):
    c = s.cues
    bells = c.w("bell", t0)
    s.show(ground(s, 140, 10), t0, t1, 70, 56, enter=None, z=Z_BACK)
    sleigh_team(s, t0, t1 + 1.5, 150, -100, 34, 22)
    for k, b in enumerate(c.beats_in(bells, t1)):
        s.pic(s.emoji("🔔", 14, flip=k % 2 == 1), b, b + 0.6, 28 + 84 * (k % 2), 10, fade_out=0.3, z=Z_FRONT)
        s.ring(b, 28 + 84 * (k % 2), 10, GOLD, r=14, dur=0.6, width=2)
    s.show(s.word("SLEIGH BELLS", GOLD, 1), bells, t1, 70, 6, enter="fade", exit="fade", z=Z_WORD)
    s.snow(t0, t1, count=10, speed=8)


def g_dream2(s, t0, t1):
    c = s.cues
    flake = s.emoji("❄️", 40)
    s.show(flake, t0, t1, 70, 30, enter="fade", exit="fade", enter_s=1.2, exit_s=1.0)
    for i, b in enumerate(c.bars_in(t0, t1)):
        s.ring(b, 70, 30, (WHITE, ICE)[i % 2], r=60, dur=1.2, width=2)
    s.show(s.word("WHITE", WHITE, 2), t0 + 0.5, t1, 24, 30, enter="fade", exit="fade", z=Z_WORD)
    s.show(s.word("XMAS", ICE, 2), t0 + 1.5, t1, 116, 30, enter="fade", exit="fade", z=Z_WORD)
    s.snow(t0, t1, count=10, speed=5)


def g_cards(s, t0, t1):
    c = s.cues
    write = c.w("write", t0)
    s.show(card(s, 44), t0 + 0.6, t1, 46, 30, enter="fade", enter_s=1.0)
    s.show(s.word("DEAR", GOLD, 1), write, t1, 98, 20, enter="fade", z=Z_WORD)
    s.show(s.word("FRIENDS", WHITE, 1), write + 0.8, t1, 102, 28, enter="fade", z=Z_WORD)
    # the cards fly off, one per bar, to the right
    for k, b in enumerate(c.bars_in(write + 1.0, t1)):
        s.glide(s.emoji("✉️", 14), [(b, 46, 30), (b + 2.0, 160, 10 + 12 * (k % 3))], z=Z_FRONT)
    s.snow(t0, t1, count=6, speed=5)


def g_merry(s, t0, t1):
    c = s.cues
    merry, bright = c.w("merry", t0), c.w("bright", t0)
    s.show(s.word("MERRY", RED, 3), merry, t1, 46, 18, enter="fade", exit="fade", enter_s=0.5, z=Z_WORD)
    s.show(s.word("BRIGHT", GOLD, 3), bright, t1, 94, 42, enter="fade", exit="fade", enter_s=0.5, z=Z_WORD)
    s.ring(bright, 94, 42, GOLD, r=60, dur=1.2, width=2)
    s.twinkle(merry, t1, (GOLD, WHITE, RED), count=30, steps=25, fade=0.8)


def candles(s, t0, t1, xs, y, h):
    """A row of candles whose flames flicker on the beats."""
    keys = [candle(s, h, f) for f in range(3)]
    beats = s.cues.beats_in(t0 + 0.6, t1)
    for k, x in enumerate(xs):
        s.pic(keys[k % 3], t0, t0 + 0.6, x, y, fade_in=0.6)
        if beats:
            s.flash(keys[k % 3:] + keys[:k % 3], beats, x, y, end=t1)


def g_allwhite(s, t0, t1):
    c = s.cues
    xmas = c.w("christmas", t0)
    s.wash(t0, xmas, (12, 12, 22), z=0, fade_in=1.0)
    candles(s, t0, t1, (20, 44, 96, 120), 40, 30)
    s.show(s.word("ALL WHITE", WHITE, 2), xmas, t1, 70, 10, enter="fade", exit="fade", enter_s=1.0, z=Z_WORD)
    s.show(s.emoji("❄️", 26), xmas, t1, 70, 38, enter="fade", exit="fade", enter_s=1.5,
           hits=c.beats_in(xmas, t1)[::2], amp=1)
    s.snow(t0, t1, count=12, speed=7, fade=1.0)


def g_lights(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    for row, y in enumerate((10, 28, 46)):
        keys = [light_string(s, 132, p) for p in range(5)]
        s.pic(keys[0], t0 + 0.5 * row, t0 + 0.5 * row + 0.8, 70, y, fade_in=0.8)
        b = [t for t in beats if t > t0 + 0.5 * row + 0.8]
        if b:
            s.flash(keys[row:] + keys[:row], b, 70, y, end=t1)
    s.snow(t0, t1, count=6, speed=5)


def g_jingle(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    s.show(s.emoji("🔔", 30), t0, t1, 36, 32, enter="fade", hits=beats[0::2], amp=3)
    s.show(s.emoji("🔔", 30, flip=True), t0 + 0.3, t1, 104, 32, enter="fade", hits=beats[1::2], amp=3)
    for i, b in enumerate(beats):
        s.ring(b, 36 if i % 2 == 0 else 104, 32, GOLD, r=22, dur=0.5, width=2)
    s.show(s.word("JINGLE", GOLD, 2), t0, t1, 70, 8, enter="fade", z=Z_WORD)
    s.twinkle(t0, t1, (GOLD, WHITE), count=15)


def g_finale(s, t0, t1):
    end = t1 - 0.2
    s.show(pine(s, 50), t0, end, 70, 33, enter="fade", exit="fade", enter_s=1.5, exit_s=2.5)
    s.show(s.emoji("⭐", 12), t0 + 1.5, end, 70, 6, enter="top", exit="fade", exit_s=2.5, z=Z_FRONT)
    s.ring(t0 + 1.85, 70, 6, GOLD, r=40, dur=1.2, width=2)
    s.show(s.word("MERRY", RED, 2), t0 + 1.0, end, 28, 26, enter="fade", exit="fade", exit_s=2.5, z=Z_WORD)
    s.show(s.word("CHRISTMAS", GREEN, 1), t0 + 1.6, end, 116, 26, enter="fade", exit="fade", exit_s=2.5, z=Z_WORD)
    s.twinkle(t0, t1, (WHITE, GOLD, RED, GREEN), count=15, fade=2.5)
    s.snow(t0, t1, count=8, speed=5, fade=2.5)


GARAGE = dict(intro=g_intro, dream=g_dream, treetops=g_treetops, bells=g_bells, dream2=g_dream2, cards=g_cards,
              merry=g_merry, allwhite=g_allwhite, lights=g_lights, jingle=g_jingle, finale=g_finale)


# ================================================================ the two windows as one stage

def wins(s):
    return tuple(s.center(m)[0] for m in s.places)  # the two windows, in --model order


WY = 26


def w_intro(s, t0, t1):
    L, C = wins(s)
    s.show(moon(s, 14), 0.5, t1, C + 8, 9, enter="fade", enter_s=2.5, z=Z_BACK)
    s.twinkle(0.3, t1, (WHITE, ICE), count=8, steps=60, fade=2.0)
    s.show(s.emoji("😴", 26), 1.0, t1, L, 30, enter="fade", enter_s=2.0)
    float_z(s, 2.5, t1, L + 10, 18, 2, rise=16, every=1.8)


def w_dream(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    white = c.w("white", t0)
    # one snowy scene across both windows: the house on the left, a pine on the right, ground under both
    s.show(ground(s, s.W, 9), t0, t1, s.W / 2, 44, enter="fade", enter_s=1.5, z=Z_BACK)
    s.show(house(s, 32, lit=False), t0, white, L, 30, enter="fade", enter_s=1.5)
    s.show(house(s, 32), white, t1, L, 30, enter="fade", enter_s=1.2)
    s.show(pine(s, 34), t0 + 1.0, t1, C, 28, enter="fade", enter_s=2.0)
    s.ring(white, L, 30, WHITE, r=30, dur=1.4, width=2)
    s.snow(t0, t1, count=8, speed=6, fade=1.0)


def w_treetops(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    children = wf(c, t0, "children", "to")
    s.show(ground(s, s.W, 9), t0, t1, s.W / 2, 44, enter=None, z=Z_BACK)
    s.show(pine(s, 40), t0, children, L, 26, enter="fade", enter_s=1.2, exit="fade", exit_s=0.8)
    s.show(pine(s, 40), t0 + 0.5, children, C, 26, enter="fade", enter_s=1.2, exit="fade", exit_s=0.8)
    s.twinkle(t0 + 0.5, children, (WHITE, GOLD), count=30, steps=30, fade=0.8, z=Z_FRONT + 1)
    # the children listen at their windows, one in each
    s.show(s.emoji("👧", 28), children, t1, L, 28, enter="fade", enter_s=1.0)
    s.show(s.emoji("🧒", 28), children + 0.5, t1, C, 28, enter="fade", enter_s=1.0)
    s.show(s.emoji("👂", 12), children + 1.5, t1, L + 13, 14, enter="fade", z=Z_FRONT)
    s.show(s.emoji("👂", 12), children + 2.0, t1, C - 13, 14, enter="fade", z=Z_FRONT)
    s.snow(t0, t1, count=6, speed=6)


def w_bells(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    s.show(ground(s, s.W, 9), t0, t1, s.W / 2, 44, enter=None, z=Z_BACK)
    # the sleigh comes in on the right, goes behind the wall and out through the left window
    sleigh_team(s, t0, t1 + 1.0, s.W + 20, -110, 30, 16)
    for k, b in enumerate(c.beats_in(c.w("bell", t0), t1)):
        x = C if k % 2 == 0 else L
        s.pic(s.emoji("🔔", 12, flip=k % 2 == 1), b, b + 0.6, x, 8, fade_out=0.3, z=Z_FRONT)
    s.snow(t0, t1, count=8, speed=8)


def w_dream2(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    flake = s.emoji("❄️", 30)
    s.show(flake, t0, t1, L, WY, enter="fade", exit="fade", enter_s=1.2)
    s.show(flake, t0 + 0.8, t1, C, WY, enter="fade", exit="fade", enter_s=1.2)
    for i, b in enumerate(c.bars_in(t0, t1)):
        s.ring(b, L if i % 2 == 0 else C, WY, (WHITE, ICE)[i % 2], r=28, dur=1.2, width=2)
    s.snow(t0, t1, count=8, speed=5)


def w_cards(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    write = c.w("write", t0)
    s.show(card(s, 32), t0 + 0.6, t1, L, WY, enter="fade", enter_s=1.0)
    s.show(s.emoji("✍️", 22), c.w("card", t0), write + 1.0, L + 8, WY + 10, enter="fade", z=Z_FRONT)
    s.show(s.emoji("📮", 30), write, t1, C, 30, enter="fade", enter_s=1.0)
    # the letters float over the wall into the postbox
    for b in c.bars_in(write + 0.5, t1 - 1.8):
        s.glide(s.emoji("✉️", 12), [(b, L, WY), (b + 0.9, (L + C) / 2, 6), (b + 1.8, C, 22)], z=Z_FRONT)


def w_merry(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    merry, bright = c.w("merry", t0), c.w("bright", t0)
    s.show(s.word("MERRY", RED, 1), merry, t1, L, WY, enter="fade", exit="fade", z=Z_WORD)
    s.show(s.word("BRIGHT", GOLD, 1), bright, t1, C, WY, enter="fade", exit="fade", z=Z_WORD)
    s.ring(merry, L, WY, RED, r=28, dur=1.2, width=2)
    s.ring(bright, C, WY, GOLD, r=28, dur=1.2, width=2)
    s.twinkle(merry, t1, (GOLD, WHITE, RED), count=25, steps=25, fade=0.8)


def w_allwhite(s, t0, t1):
    L, C = wins(s)
    candles(s, t0, t1, (L, C), 30, 30)
    s.snow(t0, t1, count=10, speed=7, fade=1.0)
    s.twinkle(t0, t1, (WARM,), count=8, steps=40, fade=1.0)


def w_lights(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    for row, y in enumerate((10, 24, 38)):
        keys = [light_string(s, s.W - 4, p) for p in range(5)]  # one string across both windows
        s.pic(keys[0], t0 + 0.5 * row, t0 + 0.5 * row + 0.8, s.W / 2, y, fade_in=0.8)
        b = [t for t in beats if t > t0 + 0.5 * row + 0.8]
        if b:
            s.flash(keys[row:] + keys[:row], b, s.W / 2, y, end=t1)


def w_jingle(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    s.show(s.emoji("🔔", 30), t0, t1, L, WY, enter="fade", hits=beats[0::2], amp=3)
    s.show(s.emoji("🔔", 30, flip=True), t0 + 0.3, t1, C, WY, enter="fade", hits=beats[1::2], amp=3)
    for i, b in enumerate(beats):
        s.ring(b, L if i % 2 == 0 else C, WY, GOLD, r=24, dur=0.5, width=2)


def w_finale(s, t0, t1):
    L, C = wins(s)
    end = t1 - 0.2
    s.show(house(s, 32), t0, end, L, 30, enter="fade", exit="fade", enter_s=1.5, exit_s=2.5)
    s.show(pine(s, 36), t0 + 0.6, end, C, 28, enter="fade", exit="fade", enter_s=1.5, exit_s=2.5)
    s.show(s.emoji("⭐", 10), t0 + 2.0, end, C, 7, enter="top", exit="fade", exit_s=2.5, z=Z_FRONT)
    s.show(ground(s, s.W, 9), t0, end, s.W / 2, 44, enter="fade", exit="fade", exit_s=2.5, z=Z_BACK)
    s.snow(t0, t1, count=8, speed=5, fade=2.5)


WINDOWS = dict(intro=w_intro, dream=w_dream, treetops=w_treetops, bells=w_bells, dream2=w_dream2, cards=w_cards,
               merry=w_merry, allwhite=w_allwhite, lights=w_lights, jingle=w_jingle, finale=w_finale)


# ================================================================ 200x42 matrix: 8 bushes, 25 px each

def bx(i):
    return 12.5 + 25 * i


BY = 22


def b_intro(s, t0, t1):
    s.twinkle(0.3, t1, (WHITE, ICE), count=6, steps=60, fade=2.0)
    for i in range(8):
        float_z(s, 1.0 + 0.4 * i, t1, bx(i) - 3, 30, 1, rise=20, every=2.4)


def b_dream(s, t0, t1):
    c = s.cues
    white = c.w("white", t0)
    keys = [house(s, 22), pine(s, 30)]
    for i in range(8):
        s.show(keys[i % 2], white - 1.0 + 0.25 * i, t1, bx(i), BY + 2, enter="fade", enter_s=1.2)
    s.show(s.emoji("❄️", 18), t0, white - 0.5, 100, BY, enter="fade", exit="fade", enter_s=1.0)
    s.snow(t0, t1, count=6, speed=6)


def b_treetops(s, t0, t1):
    c = s.cues
    children = wf(c, t0, "children", "to")
    tree = pine(s, 34)
    for i in range(8):
        s.show(tree, t0 + 0.15 * i, children, bx(i), BY + 2, enter="fade", enter_s=1.0, exit="fade", exit_s=0.6)
    s.twinkle(t0, children, (WHITE, GOLD), count=20, steps=30, fade=0.8, z=Z_FRONT + 1)
    kids = [s.emoji("👧", 22), s.emoji("🧒", 22)]
    for i in range(8):
        s.show(kids[i % 2], children + 0.12 * i, t1, bx(i), BY, enter="fade", enter_s=0.8)


def b_bells(s, t0, t1):
    c = s.cues
    sleigh_team(s, t0, t1 + 1.0, 215, -100, 24, 20)
    bell = s.emoji("🔔", 14)
    for k, b in enumerate(c.beats_in(c.w("bell", t0), t1)):
        i = (7 - k) % 8
        s.pic(bell, b, b + 0.6, bx(i), 8, fade_out=0.3, z=Z_FRONT)
    s.snow(t0, t1, count=5, speed=8)


def b_dream2(s, t0, t1):
    flake = s.emoji("❄️", 20)
    for i in range(8):
        s.show(flake, t0 + 0.2 * i, t1, bx(i), BY, enter="fade", exit="fade", enter_s=1.0)
    s.snow(t0, t1, count=6, speed=5)


def b_cards(s, t0, t1):
    c = s.cues
    write = c.w("write", t0)
    crd = card(s, 22)
    env = s.emoji("✉️", 16)
    for i in range(8):
        s.show(crd, t0 + 0.6 + 0.15 * i, write + 0.5, bx(i), BY, enter="fade", exit="fade")
        s.show(env, write + 0.5 + 0.15 * i, t1, bx(i), BY, enter="fade", exit="top", exit_s=0.8)


def b_merry(s, t0, t1):
    c = s.cues
    merry, bright = c.w("merry", t0), c.w("bright", t0)
    for i, ch in enumerate("MERRY"):
        s.show(s.word(ch, RED, 4), merry + 0.1 * i, bright, bx(i), BY, enter="fade", exit="fade", z=Z_WORD)
    for i, ch in enumerate("BRIGHT"):
        s.show(s.word(ch, GOLD, 4), bright + 0.1 * i, t1, bx(i + 1), BY, enter="fade", exit="fade", z=Z_WORD)
    s.twinkle(merry, t1, (GOLD, WHITE), count=15, steps=25, fade=0.8)


def b_allwhite(s, t0, t1):
    keys = [candle(s, 30, f) for f in range(3)]
    beats = s.cues.beats_in(t0 + 0.6, t1)
    for i in range(8):
        s.pic(keys[i % 3], t0 + 0.15 * i, t0 + 0.15 * i + 0.6, bx(i), BY, fade_in=0.6)
        b = [t for t in beats if t > t0 + 0.15 * i + 0.6]
        if b:
            s.flash(keys[i % 3:] + keys[:i % 3], b, bx(i), BY, end=t1)
    s.snow(t0, t1, count=8, speed=7, fade=1.0)


def b_lights(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    for row, y in enumerate((10, 26)):
        keys = [light_string(s, 196, p) for p in range(5)]
        s.pic(keys[0], t0 + 0.5 * row, t0 + 0.5 * row + 0.8, 100, y, fade_in=0.8)
        b = [t for t in beats if t > t0 + 0.5 * row + 0.8]
        if b:
            s.flash(keys[row:] + keys[:row], b, 100, y, end=t1)


def b_jingle(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    bell, bellf = s.emoji("🔔", 20), s.emoji("🔔", 20, flip=True)
    for i in range(8):
        s.show(bell if i % 2 == 0 else bellf, t0 + 0.05 * i, t1, bx(i), BY, enter="fade", hits=beats[i % 2::2],
               amp=3)


def b_finale(s, t0, t1):
    end = t1 - 0.2
    keys = [pine(s, 34), house(s, 22)]
    for i in range(8):
        s.show(keys[i % 2], t0 + 0.2 * i, end, bx(i), BY + 2, enter="fade", exit="fade", enter_s=1.2,
               exit_s=2.5)
    s.twinkle(t0, t1, (WHITE, GOLD), count=10, fade=2.5)
    s.snow(t0, t1, count=6, speed=5, fade=2.5)


BUSHES = dict(intro=b_intro, dream=b_dream, treetops=b_treetops, bells=b_bells, dream2=b_dream2, cards=b_cards,
              merry=b_merry, allwhite=b_allwhite, lights=b_lights, jingle=b_jingle, finale=b_finale)
