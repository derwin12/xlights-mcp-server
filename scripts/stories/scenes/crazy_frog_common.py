"""Crazy Frog Jingle Bells matrix scenes, shared plan for the garage, the two windows (one stage) and the bushes.

The MegaTree carries the SuperStar story (swinging bells, dancing elves, reindeer, HEY, the sleigh, a motorbike,
colour stripes); these scenes follow the same sections. Few words are sung, so most cues are bars and beats.
Words: faster-whisper, hand-fixed sleigh lines (stories/lyrics/crazy_frog_fixed.json); beats: librosa.
The frog is an original cartoon (goggles, Santa hat, scooter), not the trademarked character.
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
from morph_backdrop import backdrop, pattern_sweeps  # noqa: E402,F401
from matrix_scenes import Cues  # noqa: E402
from rockin_common import (BLUE, GOLD, GREEN, ICE, PINK, PURPLE, RED, WHITE, XMAS, Z_BACK, Z_FRONT,  # noqa: E402,F401
                           Z_PIC, Z_WORD, bar_sweeps, sleigh_team)

LYRICS = HERE.parent / "lyrics"
FROG, FROG_DK, ORANGE = (60, 210, 40), (20, 130, 20), (255, 130, 0)
RAINBOW = (RED, ORANGE, GOLD, GREEN, BLUE, PURPLE)


def cues(xsq):
    dur = float(ET.parse(xsq).getroot().findtext("head/sequenceDuration"))
    return Cues.from_files(LYRICS / "crazy_frog_fixed.json", LYRICS / "crazy_frog_beats.json", dur)


def plan(c):
    w = c.w
    t = [
        ("intro", 0.0),
        ("dance", c.beat_after(9.4)),
        ("hey", c.beat_after(26.9)),
        ("jingle", w("in", 29.5) - 0.1),
        ("ride", c.beat_after(39.4)),
        ("jingle2", w("jingle", 54) - 0.1),
        ("hey2", w("think", 62) - 0.1),
        ("moto", c.beat_after(68.9)),
        ("christmas", w("it's", 75) - 0.1),
        ("party", c.beat_after(79.5)),
        ("jingleman", w("i'm", 95) - 0.1),
        ("sleigh", w("oh", 106) - 0.1),
        ("finale", w("christmas", 110.5) - 0.1),
    ]
    return [(n, t0, t[k + 1][1] if k + 1 < len(t) else c.duration) for k, (n, t0) in enumerate(t)]


def run(s, scenes):
    for name, t0, t1 in plan(s.cues):
        backdrop(s, t0, t1)
        fn = scenes.get(name)
        if fn:
            fn(s, t0, t1)


def beats_to(c, t0, t1):
    """Beats in [t0, t1); past the end of the detected beats, keep the last tempo going."""
    b = c.beats_in(t0, t1)
    if c.beats and t1 > c.beats[-1]:
        step = c.beats[-1] - c.beats[-2]
        t = c.beats[-1] + step
        while t < t1:
            if t >= t0:
                b.append(t)
            t += step
    return b


# ---------------------------------------------------------------- drawn props

def frog(s, h, *, scooter=True, arms_up=False):
    """An original cartoon frog h px tall: Santa hat, goggles, big grin; on a scooter or standing."""
    W = round(h * (1.1 if scooter else 0.75))

    def draw(d, im):
        cx = W * (0.45 if scooter else 0.5)
        hr = h * 0.2                     # head radius
        hy = h * 0.32
        # Santa hat
        d.polygon([(cx - hr * 0.9, hy - hr * 0.6), (cx + hr * 0.9, hy - hr * 0.6), (cx + hr * 1.3, 1)],
                  fill=(220, 0, 0, 255))
        d.ellipse([cx + hr * 1.1, 0, cx + hr * 1.5, hr * 0.4], fill=(255, 255, 255, 255))
        # head
        d.ellipse([cx - hr, hy - hr * 0.8, cx + hr, hy + hr * 0.9], fill=FROG + (255,))
        d.rectangle([cx - hr * 1.0, hy - hr * 0.65, cx + hr * 1.0, hy - hr * 0.45], fill=(255, 255, 255, 255))
        # goggles
        g = hr * 0.42
        for dx in (-hr * 0.48, hr * 0.48):
            d.ellipse([cx + dx - g, hy - hr * 0.35 - g, cx + dx + g, hy - hr * 0.35 + g], fill=(90, 90, 110, 255))
            d.ellipse([cx + dx - g * 0.6, hy - hr * 0.35 - g * 0.6, cx + dx + g * 0.6, hy - hr * 0.35 + g * 0.6],
                      fill=(150, 230, 255, 255))
        # grin
        d.chord([cx - hr * 0.7, hy - hr * 0.1, cx + hr * 0.7, hy + hr * 0.7], 0, 180, fill=(255, 255, 255, 255))
        # body
        by0, by1 = hy + hr * 0.8, h * (0.72 if scooter else 0.82)
        d.ellipse([cx - hr * 0.7, by0, cx + hr * 0.7, by1], fill=FROG + (255,))
        # arms
        aw = max(1, h // 18)
        if arms_up:
            d.line([(cx - hr * 0.6, by0 + 2), (cx - hr * 1.5, hy - hr * 0.2)], fill=FROG_DK + (255,), width=aw)
            d.line([(cx + hr * 0.6, by0 + 2), (cx + hr * 1.5, hy - hr * 0.2)], fill=FROG_DK + (255,), width=aw)
        elif scooter:
            d.line([(cx + hr * 0.5, by0 + 2), (W * 0.82, by0 - 1)], fill=FROG_DK + (255,), width=aw)
        else:
            d.line([(cx - hr * 0.6, by0 + 2), (cx - hr * 1.3, by1)], fill=FROG_DK + (255,), width=aw)
            d.line([(cx + hr * 0.6, by0 + 2), (cx + hr * 1.3, by1)], fill=FROG_DK + (255,), width=aw)
        if scooter:
            deck = h * 0.84
            r = h * 0.08
            d.rectangle([W * 0.12, deck - 1, W * 0.86, deck + 1], fill=(200, 200, 210, 255))
            d.line([(W * 0.86, deck), (W * 0.82, by0 - 3)], fill=(200, 200, 210, 255), width=max(1, h // 25))
            d.line([(W * 0.76, by0 - 3), (W * 0.9, by0 - 3)], fill=(200, 200, 210, 255), width=max(1, h // 25))
            for wx in (W * 0.16, W * 0.84):
                d.ellipse([wx - r, h - 1 - 2 * r, wx + r, h - 1], fill=(30, 30, 30, 255), outline=(255, 200, 0, 255))
        else:
            d.ellipse([cx - hr * 1.0, by1 - 2, cx - hr * 0.1, h - 1], fill=FROG_DK + (255,))
            d.ellipse([cx + hr * 0.1, by1 - 2, cx + hr * 1.0, h - 1], fill=FROG_DK + (255,))

    name = f"frog_{h}_{int(scooter)}{int(arms_up)}"
    return s.drawn(name, W, h, draw)


def flipped(s, key):
    name = key.rsplit("/", 1)[1][:-4] + "_flip"
    return s.image(name, s.images[key].transpose(0))


def bell(s, px, tilt=0):
    """A gold bell; tilt -1/0/1 swings it."""
    def draw(d, im):
        w = px
        d.polygon([(w * 0.3, w * 0.2), (w * 0.7, w * 0.2), (w * 0.95, w * 0.85), (w * 0.05, w * 0.85)],
                  fill=(255, 190, 0, 255))
        d.ellipse([w * 0.3, w * 0.05, w * 0.7, w * 0.4], fill=(255, 190, 0, 255))
        d.rectangle([w * 0.05, w * 0.8, w * 0.95, w * 0.88], fill=(200, 120, 0, 255))
        d.ellipse([w * 0.42, w * 0.84, w * 0.58, w * 0.99], fill=(200, 120, 0, 255))
        d.rectangle([w * 0.25, w * 0.35, w * 0.35, w * 0.6], fill=(255, 240, 150, 255))
    key = s.drawn(f"bell_{px}", px, px, draw)
    if not tilt:
        return key
    name = f"bell_{px}_{'l' if tilt < 0 else 'r'}"
    return s.image(name, s.images[key].rotate(-20 * tilt, resample=0, expand=True))


def swing(s, px, times, x, y, end, z=Z_PIC):
    """A bell swinging left/right on each time."""
    keys = [bell(s, px, -1), bell(s, px, 1)]
    times = [t for t in times if t < end - 0.05]
    if times:
        s.flash(keys, times, x, y, z=z, end=end)


def stripes(s, w, h, colors, name):
    def draw(d, im):
        n = len(colors)
        for k, col in enumerate(colors):
            d.rectangle([k * w / n, 0, (k + 1) * w / n - 1, h - 1], fill=col + (255,))
    return s.drawn(name, w, h, draw)


# ================================================================ 140x60 matrix (the garage)

GY = 32


def g_intro(s, t0, t1):
    c = s.cues
    beats = beats_to(c, t0, t1)
    xmas = c.w("christmas")
    for k, x in enumerate((24, 70, 116)):
        swing(s, 26 if k != 1 else 30, beats[k % 2::2] if len(beats) > 2 else [t0], x, 17, t1)
    s.show(s.word("ITS", WHITE, 2), c.w("it's") - 0.05, t1, 70, 38, enter="pop", z=Z_WORD)
    s.show(s.word("CHRISTMAS", RED, 2), xmas, t1, 70, 50, enter="pop", z=Z_WORD)
    s.ring(xmas, 70, 17, GOLD, r=70, dur=0.9)
    s.twinkle(0.3, t1, (GOLD, WHITE), count=10, fade=1.0)


def g_dance(s, t0, t1):
    c = s.cues
    beats = beats_to(c, t0, t1)
    a, b = frog(s, 52, scooter=False), frog(s, 52, scooter=False, arms_up=True)
    s.flash([a, b], beats, 70, GY, end=t1)
    for i, x in enumerate((20, 120)):
        s.flash([s.emoji("🐸", 26), s.emoji("🔔", 24, flip=i == 1)], beats[i:], x, 34, end=t1)
    for i, bb in enumerate(c.bars_in(t0, t1)):
        s.ring(bb, 70, GY, RAINBOW[i % 6], r=60, dur=0.6)
    bar_sweeps(s, t0, t1, (GREEN, GOLD))


def g_hey(s, t0, t1):
    c = s.cues
    beats = beats_to(c, t0, t1)
    s.show(s.emoji("🦌", 40), t0, t1, 30, 32, enter="left", hits=beats, amp=3)
    s.show(s.emoji("🦌", 40, flip=True), t0, t1, 110, 32, enter="right", hits=beats, amp=3)
    s.show(s.word("HEY", WHITE, 4), t0 + 0.3, t1, 70, 30, enter="pop", z=Z_WORD)
    s.ring(t0 + 0.3, 70, 30, GOLD, r=60)


def g_jingle(s, t0, t1):
    c = s.cues
    beats = beats_to(c, t0, t1)
    jingle, ride = c.w("jingle", t0), c.w("ride", t0)
    sleigh2 = c.w("in", ride)
    sleigh_team(s, t0, jingle + 0.2, 150, -110, 40, 22)
    s.show(s.word("JINGLE", GOLD, 2), jingle, ride - 1.5, 70, 8, enter="pop", z=Z_WORD)
    s.show(s.word("BELLS", RED, 2), c.w("bells", jingle), ride - 1.5, 70, 22, enter="pop", z=Z_WORD)
    for k, x in enumerate((20, 120)):
        swing(s, 24, beats[k::2], x, 34, ride - 1.5)
    s.show(s.word("ALL THE WAY", GREEN, 2), c.w("all", jingle), ride - 1.5, 70, 44, enter="pop", z=Z_WORD)
    s.show(s.word("RIDE", PINK, 3), ride - 1.4, sleigh2, 70, 30, enter="pop", z=Z_WORD)
    sleigh_team(s, sleigh2, t1, -110, 150, 36, 22)
    s.snow(t0, t1, count=6)


def g_ride(s, t0, t1):
    c = s.cues
    rider = frog(s, 44)
    back = flipped(s, rider)
    bars = c.bars_in(t0, t1)
    for k, b in enumerate(bars):
        rt = k % 2 == 0
        s.glide(rider if rt else back, [(b, -30 if rt else 170, 36), (b + 1.8, 170 if rt else -30, 36)])
        s.ring(b + 0.9, 70, 40, RAINBOW[k % 6], r=40, dur=0.5)
    s.show(s.word("VROOM", ORANGE, 2), t0, t1, 70, 7, enter="pop", hits=beats_to(c, t0, t1)[::2], amp=1, z=Z_WORD)
    bar_sweeps(s, t0, t1, RAINBOW)


def g_jingle2(s, t0, t1):
    c = s.cues
    beats = beats_to(c, t0, t1)
    hey = c.w("hey", t0)
    s.flash([bell(s, 40, -1), bell(s, 40, 1)], [t0] + beats_to(c, t0 + 0.1, hey - 0.05), 70, 30, end=hey)
    s.show(s.word("JINGLE", GOLD, 2), t0, c.w("oh", t0), 22, 10, enter="left", z=Z_WORD)
    s.show(s.word("BELLS", RED, 2), c.w("bells", t0), c.w("oh", t0), 118, 10, enter="right", z=Z_WORD)
    s.show(s.word("OH OH OH", GREEN, 2), c.w("oh", t0), hey, 70, 52, enter="pop", z=Z_WORD)
    s.show(s.word("HEY", WHITE, 4), hey, t1, 70, 30, enter="pop", z=Z_WORD)
    s.ring(hey, 70, 30, GOLD, r=60)


def g_hey2(s, t0, t1):
    c = s.cues
    beats = beats_to(c, t0, t1)
    a, b = frog(s, 52, scooter=False), frog(s, 52, scooter=False, arms_up=True)
    s.flash([a, b], beats, 70, GY, end=t1)
    heys = [t for w_, t, _ in c.words if t0 <= t < t1 and w_.startswith("hey")]
    for t in heys:
        s.show(s.word("HEY", WHITE, 3), t, t + 0.9, 24, 30, enter="pop", z=Z_WORD)
        s.show(s.word("HEY", WHITE, 3), t, t + 0.9, 116, 30, enter="pop", z=Z_WORD)
        s.ring(t, 70, GY, GOLD, r=70)
    s.twinkle(t0, t1, (GREEN, GOLD), count=15)


def g_moto(s, t0, t1):
    c = s.cues
    beats = beats_to(c, t0, t1)
    cols = [stripes(s, 140, 60, [col] * 1, f"solid_{i}") for i, col in enumerate((BLUE, PURPLE, RED, ORANGE, GOLD))]
    band = [stripes(s, 140, 60, (col, (0, 0, 0)) * 4, f"bars_{i}") for i, col in enumerate((BLUE, PURPLE, RED, ORANGE, GOLD))]
    s.flash(band, beats, 70, 30, z=Z_BACK, end=t1)
    rider = frog(s, 44)
    s.glide(rider, [(t0, -30, 36), (t1, 170, 36)], z=Z_FRONT)
    _ = cols


def g_christmas(s, t0, t1):
    c = s.cues
    xmas = c.w("christmas", t0)
    s.show(s.word("ITS", WHITE, 2), t0, t1, 70, 18, enter="pop", z=Z_WORD)
    s.show(s.word("CHRISTMAS", RED, 2), xmas, t1, 70, 34, enter="pop", z=Z_WORD)
    s.ring(xmas, 70, 30, GOLD, r=70, dur=0.9)
    s.ring(xmas + 0.4, 70, 30, GREEN, r=70, dur=0.9)
    s.show(s.emoji("🎄", 26), xmas + 0.6, t1, 12, 46, enter="bottom")
    s.show(s.emoji("🎄", 26), xmas + 0.6, t1, 128, 46, enter="bottom")
    s.twinkle(t0, t1, XMAS, count=20, steps=15)


def g_party(s, t0, t1):
    c = s.cues
    beats = beats_to(c, t0, t1)
    keys = [frog(s, 52, scooter=False), s.emoji("🐸", 44), frog(s, 52, scooter=False, arms_up=True),
            s.emoji("🎅", 44)]
    s.flash(keys, beats, 70, GY, end=t1)
    for i, x in enumerate((20, 120)):
        swing(s, 24, beats[i::2], x, 34, t1)
    for i, b in enumerate(beats[::2]):
        s.ring(b, 70, GY, RAINBOW[i % 6], r=55, dur=0.5)
    bar_sweeps(s, t0, t1, RAINBOW)


def g_jingleman(s, t0, t1):
    c = s.cues
    beats = beats_to(c, t0, t1)
    s.show(frog(s, 52, scooter=False, arms_up=True), t0, t1, 70, GY, enter="bottom", hits=beats, amp=3)
    jingles = [t for w_, t, _ in c.words if t0 <= t < t1 and w_.startswith("jingle")]
    for k, t in enumerate(jingles):
        x = (24, 116)[k % 2]
        s.pic(s.word("JINGLE", (GOLD, RED, GREEN)[k % 3], 2), t, t + 0.8, x, 10, z=Z_WORD)
        s.ring(t, x, 34, GOLD, r=20, dur=0.5)
    for i, x in enumerate((22, 118)):
        swing(s, 24, beats[i::2], x, 38, t1)


def g_sleigh(s, t0, t1):
    c = s.cues
    sleigh = c.w("sleigh", t0)
    s.show(s.word("RIDE", PINK, 2), c.w("ride", t0), sleigh, 70, 8, enter="pop", z=Z_WORD)
    s.show(s.word("SLEIGH", RED, 2), sleigh, t1, 70, 8, enter="pop", z=Z_WORD)
    sleigh_team(s, t0, t1, 150, -110, 38, 22)
    s.snow(t0, t1, count=8)


def g_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.2
    beats = beats_to(c, t0 + 0.3, end - 1.5)
    s.show(s.word("MERRY", RED, 3), t0, end, 70, 12, enter="left", exit="fade", exit_s=1.2, z=Z_WORD)
    s.show(s.word("CHRISTMAS", GREEN, 2), t0 + 0.3, end, 70, 32, enter="right", exit="fade", exit_s=1.2, z=Z_WORD)
    s.show(frog(s, 40, scooter=False, arms_up=True), t0, end, 14, 38, enter="bottom", exit="fade", exit_s=1.2,
           hits=beats[0::2], amp=3)
    s.show(bell(s, 26), t0, end, 126, 40, enter="bottom", exit="fade", exit_s=1.2, hits=beats[1::2], amp=3)
    s.ring(t0, 70, 26, GOLD, r=70, dur=0.9)
    s.twinkle(t0, t1, XMAS, count=20, fade=1.2)


GARAGE = dict(intro=g_intro, dance=g_dance, hey=g_hey, jingle=g_jingle, ride=g_ride, jingle2=g_jingle2,
              hey2=g_hey2, moto=g_moto, christmas=g_christmas, party=g_party, jingleman=g_jingleman,
              sleigh=g_sleigh, finale=g_finale)


# ================================================================ the two windows as one stage

def wins(s):
    return tuple(s.center(m)[0] for m in s.places)  # the two windows, in --model order


WY = 26


def w_intro(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = beats_to(c, t0, t1)
    swing(s, 30, beats[0::2], L, WY, t1)
    swing(s, 30, beats[1::2], C, WY, t1)
    s.ring(c.w("christmas"), L, WY, GOLD, r=28)
    s.ring(c.w("christmas"), C, WY, GOLD, r=28)
    s.twinkle(0.3, t1, (GOLD, WHITE), count=8, fade=1.0)


def w_dance(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = beats_to(c, t0, t1)
    a, b = frog(s, 40, scooter=False), frog(s, 40, scooter=False, arms_up=True)
    s.flash([a, b], beats, L, WY + 2, end=t1)
    s.flash([b, a], beats, C, WY + 2, end=t1)
    for i, bb in enumerate(c.bars_in(t0, t1)):
        s.ring(bb, (L, C)[i % 2], WY, RAINBOW[i % 6], r=28, dur=0.5)


def w_hey(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = beats_to(c, t0, t1)
    s.show(s.emoji("🦌", 32), t0, t1, L, 30, enter="left", hits=beats, amp=3)
    s.show(s.word("HEY", WHITE, 3), t0 + 0.3, t1, C, WY, enter="pop", z=Z_WORD)
    s.ring(t0 + 0.3, C, WY, GOLD, r=30)


def w_jingle(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = beats_to(c, t0, t1)
    jingle, ride = c.w("jingle", t0), c.w("ride", t0)
    sleigh_team(s, t0, jingle + 0.4, s.W + 40, -100, 30, 16)
    swing(s, 28, beats[0::2], L, WY, ride - 1.5)
    swing(s, 28, beats[1::2], C, WY, ride - 1.5)
    s.show(s.word("RIDE", PINK, 2), ride - 1.4, t1, L, WY, enter="pop", z=Z_WORD)
    sleigh_team(s, c.w("in", ride), t1, -100, s.W + 40, 30, 16)
    s.snow(t0, t1, count=5)


def w_ride(s, t0, t1):
    c = s.cues
    rider = frog(s, 32)
    back = flipped(s, rider)
    for k, b in enumerate(c.bars_in(t0, t1)):  # zooms through one window, behind the wall, out the other
        rt = k % 2 == 0
        s.glide(rider if rt else back, [(b, -20 if rt else s.W + 20, 30), (b + 1.8, s.W + 20 if rt else -20, 30)])
    bar_sweeps(s, t0, t1, RAINBOW)


def w_jingle2(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = beats_to(c, t0, t1)
    hey = c.w("hey", t0)
    swing(s, 30, beats[0::2], L, WY, hey)
    swing(s, 30, beats[1::2], C, WY, hey)
    for x in (L, C):
        s.show(s.word("HEY", WHITE, 3), hey, t1, x, WY, enter="pop", z=Z_WORD)
        s.ring(hey, x, WY, GOLD, r=28)


def w_hey2(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = beats_to(c, t0, t1)
    a, b = frog(s, 40, scooter=False), frog(s, 40, scooter=False, arms_up=True)
    s.flash([a, b], beats, L, WY + 2, end=t1)
    s.flash([s.emoji("🐸", 30), s.emoji("🔔", 28)], beats, C, WY, end=t1)
    for t in [t for w_, t, _ in c.words if t0 <= t < t1 and w_.startswith("hey")]:
        s.ring(t, L, WY, GOLD, r=28)
        s.ring(t, C, WY, GOLD, r=28)


def w_moto(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = beats_to(c, t0, t1)
    band = [stripes(s, 40, 48, (col, (0, 0, 0)) * 3, f"wbars_{i}") for i, col in
            enumerate((BLUE, PURPLE, RED, ORANGE, GOLD))]
    s.flash(band, beats, L, 24, z=Z_BACK, end=t1)
    s.flash(band[2:] + band[:2], beats, C, 24, z=Z_BACK, end=t1)
    s.glide(frog(s, 32), [(t0, -20, 30), (t1, s.W + 20, 30)], z=Z_FRONT)


def w_christmas(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    xmas = c.w("christmas", t0)
    s.show(s.emoji("🎄", 34), xmas, t1, L, WY, enter="bottom")
    s.show(s.emoji("🎅", 32), xmas + 0.2, t1, C, WY, enter="bottom")
    s.ring(xmas, L, WY, GOLD, r=28)
    s.ring(xmas, C, WY, GREEN, r=28)
    s.twinkle(t0, t1, XMAS, count=15)


def w_party(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = beats_to(c, t0, t1)
    keys = [frog(s, 40, scooter=False), s.emoji("🐸", 32), frog(s, 40, scooter=False, arms_up=True),
            s.emoji("🎅", 32)]
    s.flash(keys, beats, L, WY + 2, end=t1)
    s.flash(keys[2:] + keys[:2], beats, C, WY + 2, end=t1)
    # a bell tossed back and forth over the wall each bar
    toss = bell(s, 12)
    for k, b in enumerate(c.bars_in(t0, t1)):
        a, z = (L, C) if k % 2 == 0 else (C, L)
        s.glide(toss, [(b, a, 8), (b + 0.5, (a + z) / 2, -4), (b + 1.0, z, 8)], z=Z_FRONT)


def w_jingleman(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = beats_to(c, t0, t1)
    s.show(frog(s, 40, scooter=False, arms_up=True), t0, t1, L, WY + 2, enter="left", hits=beats, amp=3)
    swing(s, 30, beats[1::2], C, WY, t1)
    for t in [t for w_, t, _ in c.words if t0 <= t < t1 and w_.startswith("jingle")]:
        s.ring(t, C, WY, GOLD, r=28, dur=0.5)


def w_sleigh(s, t0, t1):
    sleigh_team(s, t0, t1, s.W + 40, -110, 30, 16)
    s.snow(t0, t1, count=6)


def w_finale(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    end = t1 - 0.2
    beats = beats_to(c, t0 + 0.3, end - 1.5)
    s.show(frog(s, 40, scooter=False, arms_up=True), t0, end, L, WY + 2, enter="pop", exit="fade", exit_s=1.2,
           hits=beats[0::2], amp=3)
    s.show(s.emoji("🎄", 34), t0 + 0.2, end, C, WY, enter="pop", exit="fade", exit_s=1.2, hits=beats[1::2], amp=2)
    s.twinkle(t0, t1, XMAS, count=15, fade=1.2)


WINDOWS = dict(intro=w_intro, dance=w_dance, hey=w_hey, jingle=w_jingle, ride=w_ride, jingle2=w_jingle2,
               hey2=w_hey2, moto=w_moto, christmas=w_christmas, party=w_party, jingleman=w_jingleman,
               sleigh=w_sleigh, finale=w_finale)


# ================================================================ 200x42 matrix: 8 bushes, 25 px each

def bx(i):
    return 12.5 + 25 * i


BY = 22


def b_intro(s, t0, t1):
    c = s.cues
    beats = beats_to(c, 1.0, t1)
    for i in range(8):
        b = beats[i] if i < len(beats) else t0
        swing(s, 22, [b] + [x for x in beats[i + 1:] if x > b][i % 2::2], bx(i), BY, t1)


def b_dance(s, t0, t1):
    c = s.cues
    beats = beats_to(c, t0, t1)
    a, b = frog(s, 38, scooter=False), frog(s, 38, scooter=False, arms_up=True)
    for i in range(8):
        s.flash([a, b] if i % 2 == 0 else [b, a], beats, bx(i), BY, end=t1)


def b_hey(s, t0, t1):
    c = s.cues
    beats = beats_to(c, t0, t1)
    deer = s.emoji("🦌", 24)
    for i in range(8):
        s.show(deer if i % 2 == 0 else s.word("HEY", WHITE, 1), t0 + 0.04 * i, t1, bx(i), BY,
               enter="bottom", hits=beats[i % 2::2], amp=3, z=Z_PIC if i % 2 == 0 else Z_WORD)


def b_jingle(s, t0, t1):
    c = s.cues
    beats = beats_to(c, t0, t1)
    ride = c.w("ride", t0)
    for i in range(8):
        swing(s, 22, beats[i % 2:][:: 2], bx(i), BY, ride - 1.5)
    sleigh_team(s, ride - 1.5, t1, 215, -110, 24, 20)
    s.snow(t0, t1, count=4)


def b_ride(s, t0, t1):
    c = s.cues
    rider = frog(s, 34)
    back = flipped(s, rider)
    for k, b in enumerate(c.bars_in(t0, t1)):
        rt = k % 2 == 0
        s.glide(rider if rt else back, [(b, -24 if rt else 224, 23), (b + 1.8, 224 if rt else -24, 23)])


def b_jingle2(s, t0, t1):
    c = s.cues
    beats = beats_to(c, t0, t1)
    hey = c.w("hey", t0)
    for i in range(8):
        swing(s, 22, beats[i % 2::2], bx(i), BY, hey)
        s.show(s.word("HEY", WHITE, 1), hey + 0.03 * i, t1, bx(i), BY, enter="pop", z=Z_WORD)
        s.ring(hey + 0.03 * i, bx(i), BY, GOLD, r=12, dur=0.4)


def b_hey2(s, t0, t1):
    c = s.cues
    beats = beats_to(c, t0, t1)
    keys = [frog(s, 38, scooter=False), s.emoji("🐸", 22), frog(s, 38, scooter=False, arms_up=True)]
    for i in range(8):
        s.flash(keys[i % 3:] + keys[:i % 3], beats, bx(i), BY, end=t1)


def b_moto(s, t0, t1):
    c = s.cues
    beats = beats_to(c, t0, t1)
    blocks = [stripes(s, 25, 42, [col], f"bblock_{k}") for k, col in enumerate(RAINBOW)]
    for i in range(8):
        s.flash(blocks[i % 6:] + blocks[:i % 6], beats, bx(i), 21, z=Z_BACK, end=t1)
    s.glide(frog(s, 34), [(t0, -24, 23), (t1, 224, 23)], z=Z_FRONT)


def b_christmas(s, t0, t1):
    c = s.cues
    xmas = c.w("christmas", t0)
    keys = [s.emoji("🎄", 24), s.emoji("🎅", 22)]
    for i in range(8):
        s.show(keys[i % 2], xmas + 0.05 * i, t1, bx(i), BY, enter="pop")
        s.ring(xmas + 0.05 * i, bx(i), BY, GOLD, r=12, dur=0.4)


def b_party(s, t0, t1):
    c = s.cues
    beats = beats_to(c, t0, t1)
    keys = [frog(s, 38, scooter=False), s.emoji("🐸", 22), frog(s, 38, scooter=False, arms_up=True),
            s.emoji("🔔", 22)]
    for i in range(8):
        s.flash(keys[i % 4:] + keys[:i % 4], beats, bx(i), BY, end=t1)


def b_jingleman(s, t0, t1):
    c = s.cues
    beats = beats_to(c, t0, t1)
    jingles = [t for w_, t, _ in c.words if t0 <= t < t1 and w_.startswith("jingle")]
    for i in range(8):
        swing(s, 22, beats[i % 2::2], bx(i), BY, t1)
    for k, t in enumerate(jingles):
        i = (k * 3) % 8
        s.ring(t, bx(i), BY, GOLD, r=14, dur=0.5)


def b_sleigh(s, t0, t1):
    sleigh_team(s, t0, t1, 215, -110, 24, 20)
    s.snow(t0, t1, count=4)


def b_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.2
    beats = beats_to(c, t0 + 0.3, end - 1.5)
    keys = [frog(s, 38, scooter=False, arms_up=True), s.emoji("🎄", 24)]
    for i in range(8):
        s.show(keys[i % 2], t0 + 0.05 * i, end, bx(i), BY, enter="pop", exit="fade", exit_s=1.2,
               hits=beats[i % 2::2], amp=2)
    s.twinkle(t0, t1, XMAS, count=10, fade=1.2)


BUSHES = dict(intro=b_intro, dance=b_dance, hey=b_hey, jingle=b_jingle, ride=b_ride, jingle2=b_jingle2,
              hey2=b_hey2, moto=b_moto, christmas=b_christmas, party=b_party, jingleman=b_jingleman,
              sleigh=b_sleigh, finale=b_finale)
