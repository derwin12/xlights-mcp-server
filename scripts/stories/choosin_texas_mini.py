"""Storybook for Ella Langley 'Choosin Texas' on the 25x24 mini matrices (Matrix-mini-left/right) in ShowFolder3D.

    python matrix_storybook.py stories/choosin_texas_mini.py \
        "E:/2023/ShowFolder3D/Ella Langley - Choosin Texas.xsq" OUT.mp4 \
        --size 25x24 --k 1 --ss 4 --scale 20 --flat --fps 40 --jobs 10

Christmas version: snow in most scenes, Santa-red hats on the line dancers, a Santa hat on the smiling cowboy,
a Christmas tree in the pickup, lit-up cacti, and MERRY XMAS Y'ALL over the final fireworks.

The story: she brought her cowboy home, he fell for a Texas girl. A drawn Texas flag on every "TEXAS", two-steppers
on "two steppin", a crystal ball, the cowboy riding off, a lonely glass of Jack. Lyrics labels are capitals.
Staged like hippopotamus_for_christmas_mini.py: black backgrounds, one big picture, few words.
"""

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matrix_storybook as mb  # noqa: E402
from hippopotamus_for_christmas import BLACK, P, beats_after, keyframes_fn, santa_hat, tm_after  # noqa: E402
from matrix_storybook import (Scene, confetti, dim, ease, fireworks, glow, ground, icon, rising, road,  # noqa: E402
                              snow, sparkles, stars, text, tree_lights)
from PIL import ImageDraw  # noqa: E402

W, H = 25, 24
BOX = (0, 0, W, H)
WHITE = (255, 255, 255)
RED = (230, 30, 40)
BLUE = (30, 70, 220)
GOLD = (255, 200, 60)
DIRT = (120, 75, 35)


# ---------------------------------------------------------------- drawn props (story pixels, 25x24)

def texas_flag(x0=2, y0=5, w=21, h=14, at=None, wave_hits=None) -> mb.Layer:
    """The Lone Star flag: blue band with a white star on the left, white over red on the right.
    wave_hits: the flag ripples (columns shift up/down) for a moment after each hit."""

    def draw(f):
        t0 = f.start if at is None else at
        if f.t < t0:
            return
        k = mb.kick(wave_hits, f.t, 0.35) if wave_hits else 0.0
        d = ImageDraw.Draw(f.img)
        band = w / 3
        cols = 24
        for i in range(cols):
            xa, xb = x0 + w * i / cols, x0 + w * (i + 1) / cols
            dy = math.sin(i / cols * 2 * math.pi + f.t * 8) * 0.8 * k
            if xa < x0 + band:
                d.rectangle([P(xa), P(y0 + dy), P(xb), P(y0 + h + dy)], fill=BLUE + (255,))
            else:
                d.rectangle([P(xa), P(y0 + dy), P(xb), P(y0 + h / 2 + dy)], fill=WHITE + (255,))
                d.rectangle([P(xa), P(y0 + h / 2 + dy), P(xb), P(y0 + h + dy)], fill=RED + (255,))
        # five-point star centred in the blue band
        cx, cy, r = x0 + band / 2, y0 + h / 2, band * 0.42
        pts = []
        for j in range(10):
            a = -math.pi / 2 + j * math.pi / 5
            rr = r if j % 2 == 0 else r * 0.42
            pts.append((P(cx + rr * math.cos(a)), P(cy + rr * math.sin(a))))
        d.polygon(pts, fill=WHITE + (255,))
    return draw


def rain(n=14, seed=3, box=(0, 8, 25, 24), speed=14.0, at=None, color=(90, 150, 255)) -> mb.Layer:
    """Short falling streaks."""
    rnd = random.Random(seed)
    drops = [(rnd.uniform(box[0], box[2]), rnd.uniform(0, 1), rnd.uniform(0.8, 1.2)) for _ in range(n)]

    def draw(f):
        t0 = f.start if at is None else at
        if f.t < t0:
            return
        d = ImageDraw.Draw(f.img)
        hgt = box[3] - box[1]
        for x, ph, sp in drops:
            y = box[1] + ((ph * hgt + (f.t - t0) * speed * sp) % hgt)
            d.line([P(x), P(y), P(x - 0.3), P(y + 1.5)], fill=color + (255,), width=mb.LW())
    return draw


def sunrise(t0, t1, cx=12.5, y_from=26, y_to=14, r=6) -> mb.Layer:
    """A sun climbing from below the horizon between t0 and t1, sky warming behind it."""

    def draw(f):
        p = ease((f.t - t0) / (t1 - t0)) if t1 > t0 else 1.0
        y = y_from + (y_to - y_from) * max(0.0, min(1.0, p))
        glow(cx, y, r * 2.4, (255, 120, 30), 0.35 * max(0.2, p))(f)
        d = ImageDraw.Draw(f.img)
        d.ellipse([P(cx - r), P(y - r), P(cx + r), P(y + r)], fill=(255, 190, 40, 255))
    return draw


def dance_floor(y=20) -> mb.Layer:
    """Wooden boards."""

    def draw(f):
        d = ImageDraw.Draw(f.img)
        d.rectangle([0, P(y), f.img.width, f.img.height], fill=(110, 60, 25, 255))
        for i in range(0, W + 1, 5):
            d.line([P(i), P(y), P(i), P(H)], fill=(70, 35, 12, 255), width=mb.LW())
    return draw


def until_(layer, t_end):
    """Hide a layer from t_end on."""
    return lambda f: None if f.t >= t_end else layer(f)


def SN(seed, n=10):
    """Light snowfall for the Christmas version."""
    return snow(n, seed=seed, speed=2.0)


def garland(y=2.5, n=7, seed=9) -> mb.Layer:
    """A sagging string of twinkling coloured bulbs across the top."""
    cols = [(255, 40, 40), (40, 220, 60), (255, 210, 40), (60, 140, 255), (255, 255, 255)]
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 6) for _ in range(n)]

    def draw(f):
        d = ImageDraw.Draw(f.img)
        pts = [(i * W / 24, y + 1.4 * math.sin(math.pi * ((i * W / 24) % (W / 2)) / (W / 2))) for i in range(25)]
        d.line([(P(a), P(b)) for a, b in pts], fill=(30, 90, 40, 255), width=mb.LW())
        for i in range(n):
            x = (i + 0.5) * W / n
            yy = y + 1.4 * math.sin(math.pi * (x % (W / 2)) / (W / 2)) + 0.8
            b = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(f.t * 5 + ph[i])) ** 2
            mb.dot(d, x, yy, tuple(round(v * b) for v in cols[i % len(cols)]) + (255,), 0.6)
    return draw


def circle_x(t0, period, cx=12.5, rx=6.0, phase=0.0):
    return lambda f: cx + rx * math.sin((f.t - t0) * 2 * math.pi / period + phase)


# ---------------------------------------------------------------- reused chorus scenes

def texas_scene(tm, start, k, word="TEXAS", end_hold=2.5):
    """She's from Texas, I can tell: the flag waves in, TEXAS when it's sung, ripples on TELL."""
    w = lambda wd: tm_after(tm, wd, start)  # noqa: E731
    tx = w(word)
    return Scene(start - 0.1, [BLACK, SN(10 + k, 8),
                               texas_flag(2, 1, 21, 14, at=start, wave_hits=[tx, w("TELL")]),
                               text("TEXAS", 17, GOLD, at=tx),
                               sparkles(4, seed=11 + k, box=(0, 15, 25, 24))], f"texas {k}", cut=True)


def line_dancers(hits, xs=(4.5, 12.5, 20.5), base=20.0,
                 shirts=((220, 40, 40), (40, 110, 255), (255, 255, 255))) -> mb.Layer:
    """A row of line dancers in hats and boots, all in step: a grapevine right for 4 counts and back left for 4,
    with a heel kick on counts 4 and 8. Each figure is about 5 px wide and 14 tall, feet on `base`."""
    DX = [0, 1, 2, 2, 2, 1, 0, 0]  # shift per count
    KICK = {3, 7}
    HAT, SKIN, JEANS, BOOT = (150, 95, 40), (255, 200, 150), (40, 70, 160), (110, 60, 20)

    def draw(f):
        n = sum(1 for h in hits if h <= f.t)
        s = mb.since(hits, f.t)
        prev, cur = DX[(n - 1) % 8] if n > 1 else 0, DX[(n - 1) % 8] if n else 0
        before = DX[(n - 2) % 8] if n > 1 else 0
        frac = 1.0 if s is None else ease(min(1.0, s / 0.18))
        dx = before + (cur - before) * frac
        kicking = n > 0 and (n - 1) % 8 in KICK and s is not None and s < 0.35
        hop = math.sin(min(1.0, s / 0.18) * math.pi) * 0.6 if s is not None and s < 0.18 else 0.0
        d = ImageDraw.Draw(f.img)
        lw = mb.LW()
        for x0, shirt in zip(xs, shirts):
            x = x0 + dx - 1
            y = base - hop
            # boots + legs (one leg kicks forward/out on the kick counts)
            d.line([P(x - 0.8), P(y - 4.5), P(x - 1.0), P(y - 0.8)], fill=JEANS + (255,), width=lw * 2)
            d.rectangle([P(x - 1.6), P(y - 1), P(x - 0.2), P(y)], fill=BOOT + (255,))
            if kicking:
                d.line([P(x + 0.8), P(y - 4.5), P(x + 2.6), P(y - 1.8)], fill=JEANS + (255,), width=lw * 2)
                d.rectangle([P(x + 2.2), P(y - 2.2), P(x + 3.4), P(y - 1.2)], fill=BOOT + (255,))
            else:
                d.line([P(x + 0.8), P(y - 4.5), P(x + 1.0), P(y - 0.8)], fill=JEANS + (255,), width=lw * 2)
                d.rectangle([P(x + 0.2), P(y - 1), P(x + 1.6), P(y)], fill=BOOT + (255,))
            # shirt, arms bent with thumbs in belt loops
            d.rectangle([P(x - 1.5), P(y - 9), P(x + 1.5), P(y - 4.5)], fill=shirt + (255,))
            for sgn in (-1, 1):
                d.line([P(x + 1.5 * sgn), P(y - 8.5), P(x + 2.6 * sgn), P(y - 6.5), P(x + 1.6 * sgn), P(y - 5)],
                       fill=shirt + (255,), width=lw)
            # head and hat
            d.rectangle([P(x - 1), P(y - 11.5), P(x + 1), P(y - 9.3)], fill=SKIN + (255,))
            d.rectangle([P(x - 1.3), P(y - 14), P(x + 1.3), P(y - 12.2)], fill=(220, 30, 40, 255))
            d.rectangle([P(x - 2.5), P(y - 12.2), P(x + 2.5), P(y - 11.4)], fill=(245, 245, 245, 255))
    return draw


def dance_scene(tm, start, k):
    """He's two steppin round the room: a row of line dancers on the boards, in step with the beat."""
    w = lambda wd: tm_after(tm, wd, start)  # noqa: E731
    beats = tm.beats_in(start, start + 8)
    return Scene(start - 0.1, [BLACK, SN(70 + k, 6), garland(2.0, seed=71 + k), dance_floor(20),
                               line_dancers(beats),
                               ], f"dance {k}")


def smile_scene(tm, start, k):
    w = lambda wd: tm_after(tm, wd, start)  # noqa: E731
    return Scene(start - 0.1, [BLACK, SN(20 + k),
                               icon("🤠", 18, 12.5, 12, enter="grow", motion="pulse",
                                    hits=[w("SMILE"), w("FACE")], amp=1.3),
                               santa_hat(12.5, 6.0, 10.0),
                               icon("❤️", 6, 21, 4, at=w("FACE"), enter="pop", motion="pulse")], f"smile {k}")


def nothin_scene(tm, start, k):
    w = lambda wd: tm_after(tm, wd, start)  # noqa: E731
    return Scene(start - 0.1, [BLACK, SN(30 + k, 14),
                               icon("😢", 16, 12.5, 12, enter="fade", enter_s=0.4, motion="pulse",
                                    hits=[w("DO")])], f"nothin {k}", cut=True)


def crystal_scene(tm, start, k):
    w = lambda wd: tm_after(tm, wd, start)  # noqa: E731
    return Scene(start - 0.1, [BLACK, SN(40 + k, 8),
                               glow(12.5, 12, 11, (170, 90, 255), 0.35),
                               icon("🔮", 18, 12.5, 12, enter="grow", motion="pulse",
                                    hits=[w("CRYSTAL"), w("BALL"), w("SEE")], amp=1.5)], f"crystal {k}")


def cowboy_scene(tm, start, k):
    """A cowboy always finds a way to leave: rides across the sunset and out on LEAVE."""
    w = lambda wd: tm_after(tm, wd, start)  # noqa: E731
    out = w("LEAVE")
    beats = tm.beats_in(start, out + 1)
    x = keyframes_fn([(start, -6), (start + 0.8, 7), (out - 0.3, 14), (out + 0.6, 33)])
    return Scene(start - 0.1, [BLACK, stars(6, seed=50 + k, ymax=8),
                               sunrise(start - 1, start, cx=20, y_from=8, y_to=5, r=3),
                               ground(18, DIRT, hill=0.3),
                               SN(52 + k, 8),
                               icon("🌵", 9, 3, 13.5, enter="fade"), tree_lights((-1, 6, 7, 19), 5, seed=53 + k),
                               icon("🏇", 12, x, 13, enter=None, flip=True, motion="bounce", hits=beats, amp=0.4)],
                 f"cowboy {k}")


def jack_scene(tm, start, k):
    """Drinkin Jack all by myself."""
    w = lambda wd: tm_after(tm, wd, start)  # noqa: E731
    return Scene(start - 0.1, [BLACK, SN(56 + k, 8), glow(12.5, 14, 9, (200, 120, 40), 0.25),
                               icon("🥃", 15, 12.5, 14, enter="drop", enter_s=0.3, motion="pulse",
                                    hits=[w("JACK"), w("MYSELF")]),
                               icon("💧", 4, 6, 5, at=w("MYSELF"), enter="pop", motion="float", amp=-1.2)],
                 f"jack {k}", cut=True)


def chorus(tm, start, k, texas_word="SHE'S"):
    w = lambda wd: tm_after(tm, wd, start)  # noqa: E731
    S = [texas_scene(tm, w(texas_word), k),
         dance_scene(tm, w("BY"), k),
         smile_scene(tm, w("JUDGING") - 0.2, k),
         nothin_scene(tm, w("THERE'S"), k),
         crystal_scene(tm, w("IT"), k),
         cowboy_scene(tm, w("COWBOY") - 0.1, k),
         jack_scene(tm, w("DRINKIN"), k)]
    return S


# ---------------------------------------------------------------- the story

def build(tm):
    S = []
    w = lambda word, t: tm_after(tm, word, t)  # noqa: E731

    # ---- verse 1: just when I thought I got him to fall in love with Tennessee
    S.append(Scene(0.0, [BLACK, stars(8, seed=1, ymax=10), SN(1),
                         icon("⛰️", 16, 12.5, 15, enter="fade", enter_s=0.8),
                         icon("🤠", 9, 12.5, 18, at=w("HIM", 2.0), enter="rise", motion="bob"),
                         icon("❤️", 6, 20, 5, at=w("LOVE", 3.0), enter="pop", motion="pulse",
                              hits=[w("LOVE", 3.0), w("TENNESSEE", 4.0)], amp=2)], "tennessee"))
    # I should've known better than to take him back to Abilene
    S.append(Scene(7.9, [BLACK, stars(8, seed=2, ymax=10), SN(2), road(y=19, speed=10),
                         icon("🌵", 8, keyframes_fn([(7.9, 30), (13.5, -8)]), 13.5, enter=None),
                         icon("🎄", 8, 8.5, 8.5, enter="left", enter_s=0.6, motion="bounce",
                              hits=tm.beats_in(8, 14)[::2], amp=0.3),
                         icon("🛻", 13, 12.5, 15, enter="left", enter_s=0.6, flip=True, motion="bounce",
                              hits=tm.beats_in(8, 14)[::2], amp=0.3)], "abilene"))
    # put him right back into her arms
    S.append(Scene(15.3, [BLACK, SN(3),
                          icon("💃", 13, 18, 12, enter="right"),
                          icon("🤠", 10, keyframes_fn([(15.4, 3), (17.85, 10)]), 13, enter="left"),
                          icon("💞", 7, 14, 4, at=w("ARMS", 17.0), enter="pop", motion="pulse")], "arms"))
    # I wasn't a match for that kind of spark
    spark = w("SPARK", 21.0)
    S.append(Scene(18.8, [BLACK,
                          icon("💔", 15, 12.5, 12, at=w("MATCH", 19.0), enter="pop", until=spark, exit_s=0.1,
                               motion="shake", hits=[w("MATCH", 19.0)]),
                          icon("🔥", 16, 12.5, 12, at=spark, enter="pop", motion="pulse"),
                          confetti(18, seed=4, at=spark)], "spark", cut=True))

    # ---- chorus 1
    S += chorus(tm, 22.0, 1)
    # he's choosin Texas, I can tell
    S.append(texas_scene(tm, w("HE'S", 47.0), 2))

    # ---- verse 2: smoky mountain rain
    S.append(Scene(51.2, [BLACK, ground(20, (30, 70, 30), hill=0.3),
                          icon("⛰️", 18, 12.5, 13, enter="fade", enter_s=0.8),
                          icon("🌧️", 10, 12.5, 4, at=w("SMOKY", 53.0), enter="drop"),
                          rain(12, seed=5, box=(5, 6, 20, 20), at=w("RAIN", 55.0))], "smoky rain"))
    # them old Hank tunes, the Memphis blues we used to sing
    S.append(Scene(58.4, [BLACK, SN(6),
                          icon("🎸", 15, 9, 12, enter="grow", motion="swing", amp=0.6),
                          rising("🎵", n=4, seed=7, size=5, box=(14, 24), speed=4, at=w("TUNES", 59.0)),
                          text("BLUES", 19, (90, 150, 255), at=w("BLUES", 60.0))], "hank tunes"))
    # he always loved Amarillo by morning
    S.append(Scene(65.8, [BLACK, stars(10, seed=8, ymax=12),
                          sunrise(w("AMARILLO", 66.0), w("MORNING", 68.0) + 0.4, y_from=27, y_to=15, r=6),
                          ground(19, DIRT, hill=0.3),
                          icon("🌵", 8, 4, 14.5, enter="fade"), icon("🌵", 6, 21, 16, enter="fade"),
                          tree_lights((0, 8, 8, 19), 5, seed=81), tree_lights((18, 11, 24, 19), 3, seed=82),
                          SN(8, 6)], "amarillo"))
    # I should've taken that as a warnin
    S.append(Scene(69.4, [BLACK, glow(12.5, 12, 10, (255, 180, 0), lambda f: 0.15 + 0.3 * mb.kick([72.26], f.t, 0.4)),
                          icon("⚠️", 17, 12.5, 12, enter="pop", motion="pulse",
                               hits=[w("TAKEN", 69.5), w("WARNIN", 71.0)], amp=1.5)], "warning", cut=True))

    # ---- chorus 2
    S += chorus(tm, 72.5, 3)
    # 'cause she's from Texas, I can tell
    S.append(texas_scene(tm, w("CAUSE", 97.0), 4))

    # ---- chorus 3
    S += chorus(tm, 101.3, 5)
    S.append(texas_scene(tm, w("HE'S", 126.0), 6))

    # ---- finale: he's choosin Texas (sung once more), fireworks over the flag, fade out
    fin = w("HE'S", 129.0) - 1.5
    end = tm.duration
    fade = lambda f: ease((f.t - (end - 1.5)) / 1.5)  # noqa: E731
    hits = beats_after(tm.beats, fin, 12)
    tx = w("TEXAS", 131.0)
    S.append(Scene(fin, [BLACK, SN(60), fireworks(hits, seed=60),
                         until_(texas_flag(2, 6, 21, 13, wave_hits=hits), tx + 0.9),
                         text("TEXAS", 0, GOLD, at=tx, until=tx + 0.9),
                         text("MERRY", 2, RED, at=tx + 0.9),
                         text("XMAS", 9, (60, 220, 90), at=tx + 1.1),
                         text("Y'ALL", 16, GOLD, at=tx + 1.3),
                         dim(fade)], "finale"))
    return S
