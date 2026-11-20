"""Storybook for Owl City 'Fireflies' on Matrix 2 (40x30) in F:/ShowFolderAI.

One LED per story pixel, blown up 20x so the xLights Video effect samples one colour per LED:
    python matrix_storybook.py stories/fireflies.py "<Fireflies.xsq from the vendor .xsqz>" OUT.mp4 \
        --size 40x30 --k 1 --ss 4 --scale 20 --flat --fps 40 --jobs 10

Timing comes from the vendor sequence: its Lyrics word layer (labels in capitals) and its counted "Timing" track as
beats. Fireflies are drawn as blinking yellow-green dots, which read better on LEDs than any emoji.
"""

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matrix_storybook as mb  # noqa: E402
from hippopotamus_for_christmas import BLACK, P, beats_after, falling, keyframes_fn, tm_after  # noqa: E402
from matrix_storybook import (Scene, dim, ease, fireworks, glow, ground, icon, rising, sparkles,  # noqa: E402
                              stars, text)
from PIL import ImageDraw  # noqa: E402

W, H = 40, 30
BOX = (0, 0, W, H)
FLY = (200, 255, 60)
YELLOW = (255, 220, 60)
WHITE = (255, 255, 255)
CYAN = (90, 220, 255)


# ---------------------------------------------------------------- drawn props (story pixels, 40x30)

def fireflies(n=12, seed=1, box=BOX, at=None, color=FLY, speed=1.0, rise=0.0, grow=0.0) -> mb.Layer:
    """Blinking dots wandering in box. rise: px/s drift upward (wrapping). grow: seconds to fade them in one by one."""
    rnd = random.Random(seed)
    flies = [(rnd.uniform(box[0], box[2]), rnd.uniform(box[1], box[3]), rnd.uniform(0, 6.28),
              rnd.uniform(0.5, 1.4), rnd.uniform(0, 1), rnd.uniform(0, 1)) for _ in range(n)]

    def draw(f):
        t0 = f.start if at is None else at
        if f.t < t0:
            return
        lt = f.t - t0
        d = ImageDraw.Draw(f.img)
        bw, bh = box[2] - box[0], box[3] - box[1]
        for x, y, ph, sp, blink, order in flies:
            if grow and lt < order * grow:
                continue
            xx = box[0] + (x - box[0] + math.sin(lt * sp * speed + ph) * 2.0) % bw
            yy = box[1] + (y - box[1] + math.cos(lt * sp * 0.8 * speed + ph * 1.3) * 1.5 - lt * rise) % bh
            b = 0.4 + 0.6 * max(0.0, math.sin((lt * 0.7 * sp + blink) * 2 * math.pi)) ** 2
            c = tuple(round(v * b) for v in color) + (255,)
            mb.dot(d, xx, yy, c, 0.5)
    return draw


def jar(cx=20, top=8, w=14, h=18, at=None) -> mb.Layer:
    """A glass jar with a gold lid (drawn, so it stays crisp on LEDs)."""

    def draw(f):
        if at is not None and f.t < at:
            return
        d = ImageDraw.Draw(f.img)
        x0, x1, y0, y1 = cx - w / 2, cx + w / 2, top, top + h
        glass = (110, 170, 210, 255)
        d.rectangle([P(x0 - 0.5), P(y0 - 3), P(x1 + 0.5), P(y0 - 1)], fill=(220, 170, 40, 255))  # lid
        d.line([P(x0), P(y0), P(x0), P(y1)], fill=glass, width=mb.LW())
        d.line([P(x1), P(y0), P(x1), P(y1)], fill=glass, width=mb.LW())
        d.line([P(x0), P(y1), P(x1), P(y1)], fill=glass, width=mb.LW())
        d.line([P(x0 + 2), P(y0 + 2), P(x0 + 2), P(y0 + 6)], fill=(200, 230, 255, 255), width=mb.LW())  # shine
    return draw


def thread(x, y0, y1, color=(160, 160, 170)) -> mb.Layer:
    def draw(f):
        ImageDraw.Draw(f.img).line([P(x), P(y0), P(x), P(y1)], fill=color + (255,), width=mb.LW())
    return draw


def door_crack(x0=12, x1=28, y0=4, y1=27, open_at=None) -> mb.Layer:
    """A dark door that opens a crack, letting a strip of warm light out."""

    def draw(f):
        d = ImageDraw.Draw(f.img)
        d.rectangle([P(x0 - 1), P(y0 - 1), P(x1 + 1), P(y1)], fill=(90, 55, 25, 255))  # frame
        k = 0.0 if open_at is None or f.t < open_at else ease((f.t - open_at) / 0.8)
        gap = 2.5 * k
        if gap > 0:
            d.rectangle([P(x1 - gap), P(y0), P(x1), P(y1)], fill=(255, 210, 110, 255))
        d.rectangle([P(x0), P(y0), P(x1 - gap), P(y1)], fill=(150, 90, 40, 255))  # door
        d.rectangle([P(x1 - gap - 3), P(y0 + 11), P(x1 - gap - 2), P(y0 + 12)], fill=(240, 200, 60, 255))  # knob
    return draw


def fence(y=21, color=(150, 100, 50)) -> mb.Layer:
    def draw(f):
        d = ImageDraw.Draw(f.img)
        for x in (17, 20, 23):
            d.rectangle([P(x), P(y - 6), P(x + 1), P(y)], fill=color + (255,))
        d.rectangle([P(16), P(y - 4.5), P(25), P(y - 3.5)], fill=color + (255,))
    return draw


def jumping_sheep(hits, size=10, y=19, x0=-6, x1=46) -> mb.Layer:
    """One sheep per hit hops across the fence (left to right)."""

    def draw(f):
        for h in hits:
            s = f.t - h
            if not 0 <= s < 1.6:
                continue
            k = s / 1.6
            x = x0 + (x1 - x0) * k
            jump = math.sin(min(1.0, max(0.0, (x - 10) / 20)) * math.pi) * 8
            icon("🐑", size, x, y - jump, enter=None, flip=True)(f)
    return draw


def walk_icon(emoji, size, y, t0, t1, x0, x1, flip=False, hits=None) -> mb.Layer:
    return icon(emoji, size, keyframes_fn([(t0, x0), (t1, x1)]), y, enter=None, flip=flip, motion="bounce",
                hits=hits, amp=0.6)


# ---------------------------------------------------------------- chorus (five times)

EARTHS = ["🌍", "🌎", "🌏", "🌍", "🌎"]


def chorus(tm, start, k, seems=True):
    """I'd like to make myself believe / that planet Earth turns slowly / it's hard to say that I'd rather stay awake
    when I'm asleep / 'cause everything is never as it seems."""
    w = lambda word: tm_after(tm, word, start)  # noqa: E731
    S = []
    # believe: a wish on a shooting star
    S.append(Scene(start - 0.1, [BLACK, stars(10, seed=40 + k, ymax=30),
                                 icon("⭐", 10, keyframes_fn([(start, 34), (w("BELIEVE") + 1.5, 8)]),
                                      keyframes_fn([(start, 6), (w("BELIEVE") + 1.5, 16)]), enter="fade"),
                                 sparkles(6, seed=41 + k, box=BOX)], f"believe {k}"))
    # planet Earth turns slowly
    t = w("PLANET") - 0.2
    S.append(Scene(t, [BLACK, stars(12, seed=42 + k, ymax=30),
                       glow(20, 15, 15, (60, 140, 255), 0.25),
                       icon(EARTHS[k], 22, 20, 15, enter="grow", enter_s=0.8,
                            rot=(lambda t0: lambda f: -(f.t - t0) * 12)(t)),
                       fireflies(8, seed=43 + k, box=(0, 0, W, H), at=w("EARTH")),
                       text("SLOWLY", 24, CYAN, at=w("SLOWLY"), until=w("SLOWLY") + 2.0)], f"earth {k}"))
    # awake when I'm asleep
    t = w("IT'S") - 0.1
    S.append(Scene(t, [BLACK, stars(6, seed=44 + k, ymax=10), icon("🌙", 7, 34, 5, enter="fade"),
                       icon("🛌", 22, 20, 19, enter="rise"),
                       icon("👀", 9, 13, 8, at=w("AWAKE"), until=w("ASLEEP"), enter="pop", motion="shake",
                            hits=[w("AWAKE")]),
                       icon("💤", 8, 13, 8, at=w("ASLEEP"), enter="pop", motion="bob")], f"awake {k}"))
    if not seems:
        return S
    # everything is never as it seems
    t = w("EVERYTHING") - 0.2
    S.append(Scene(t, [BLACK, sparkles(10, seed=45 + k, box=BOX, color=(200, 160, 255)),
                       glow(20, 15, 13, (170, 90, 255), 0.3),
                       icon("🔮", 20, 20, 15, enter="grow", motion="pulse",
                            hits=[w("EVERYTHING"), w("NEVER"), w("SEEMS")], amp=1.5)], f"seems {k}"))
    return S


def asleep_scene(start, seed):
    """(when I fall asleep): the moon and Zs, a few fireflies."""
    return Scene(start, [BLACK, stars(10, seed=seed, ymax=30), icon("🌙", 16, 20, 13, enter="fade", motion="bob"),
                         rising("💤", n=3, seed=seed, size=6, box=(8, 32), speed=4),
                         fireflies(6, seed=seed + 1)], "fall asleep")


# ---------------------------------------------------------------- the story

def build(tm):
    S = []
    w = lambda word, t: tm_after(tm, word, t)  # noqa: E731
    beats = tm.beats

    # ---- intro (music only): a dark field, fireflies come out one by one
    S.append(Scene(0.0, [BLACK, stars(14, seed=1, ymax=16), icon("🌙", 8, 33, 6, at=1.0, enter="fade", enter_s=2.0),
                         ground(26, (10, 60, 20), hill=1.0),
                         fireflies(18, seed=2, box=(0, 8, W, 26), grow=16.0)], "intro"))

    # ---- verse 1
    S.append(Scene(w("YOU", 21) - 0.1, [BLACK, sparkles(6, seed=3, box=BOX),
                                       icon("😲", 22, 20, 15, enter="grow", motion="pulse",
                                            hits=[w("BELIEVE", 21), w("EYES", 21)], amp=1.5)], "believe eyes"))
    ff = w("FIREFLIES", 24)
    S.append(Scene(w("IF", 24) - 0.1, [BLACK, fireflies(40, seed=4, grow=1.0),
                                      text("FIREFLIES", 12, FLY, at=ff, until=ff + 1.7)], "ten million"))
    lit = w("LIT", 26)
    S.append(Scene(lit - 0.1, [BLACK, glow(20, 14, 16, (255, 230, 90), lambda f: 0.15 + 0.25 * ease(f.t - lit)),
                               icon("🌍", 20, 20, 14, enter="grow", until=w("ASLEEP", 27)),
                               fireflies(24, seed=5, box=(4, 0, 36, 28)),
                               icon("😴", 20, 20, 15, at=w("ASLEEP", 27), enter="pop", motion="bob")],
                   "lit up the world"))
    S.append(Scene(w("CAUSE", 30) - 0.1, [BLACK, stars(10, seed=6, ymax=30),
                                         fireflies(30, seed=7, rise=1.5),
                                         icon("🌙", 10, 32, 7, enter="fade")], "open air"))
    S.append(Scene(w("LEAVE", 34) - 0.1, [BLACK, falling(["💧"], n=7, seed=8, size=4, speed=10, box=(2, 38)),
                                         fireflies(10, seed=9)], "teardrops"))
    S.append(Scene(w("YOU'D", 36) - 0.1, [BLACK, ground(26, (10, 60, 20), hill=1.0),
                                         fireflies(20, seed=10, box=(0, 0, W, 16)),
                                         icon("🧍", 18, 20, 17, enter="rise"),
                                         icon("😳", 7, 30, 6, at=w("STARE", 39), enter="pop", motion="pulse")],
                   "stand and stare"))

    # ---- chorus 1
    S += chorus(tm, w("I'D", 42), 0)

    # ---- verse 2
    hugs = w("HUGS", 64)
    S.append(Scene(w("CAUSE", 63) - 0.1, [BLACK, sparkles(6, seed=11, box=BOX),
                                         icon("🤗", 20, 20, 15, at=hugs - 0.3, enter="grow", motion="pulse",
                                              hits=[hugs])], "hugs"))
    lb = w("LIGHTNING", 67)
    S.append(Scene(w("FROM", 66.5) - 0.1, [BLACK, icon("⚡", 14, 20, 14, at=lb, enter="pop", until=lb + 1.2),
                                          fireflies(45, seed=12, at=lb + 0.6, grow=0.8)], "lightning bugs"))
    dance = beats_after(beats, w("AS", 69), 12)
    S.append(Scene(w("AS", 69) - 0.1, [BLACK, glow(20, 16, 14, (255, 80, 200), 0.2),
                                      fireflies(16, seed=13, speed=3.0),
                                      icon("💃", 20, 20, 15, enter="grow", motion="bounce", hits=dance),
                                      text("DANCE!", 1, (255, 90, 230), at=w("DANCE", 70))], "dance"))
    fox = w("FOXTROT", 74)
    S.append(Scene(w("A", 74.5) - 0.1, [BLACK, icon("🧑", 14, 20, 22, enter="rise"),
                                       walk_icon("🦊", 10, 7, fox - 0.3, fox + 2.6, -6, 46, flip=True,
                                                 hits=tm.beats_in(fox, fox + 3))], "foxtrot"))
    sock = w("SOCK", 77)
    S.append(Scene(w("A", 77.5) - 0.1, [BLACK, icon("🛏️", 24, 20, 12, enter=None),
                                       icon("🧦", 8, 12, 25, at=sock, enter="pop", motion="bounce",
                                            hits=tm.beats_in(sock, sock + 2.5), amp=1.2),
                                       icon("🧦", 8, 28, 25, at=w("HOP", 77), enter="pop", motion="bounce",
                                            hits=tm.beats_in(sock + 0.25, sock + 2.5), amp=1.2, flip=True)],
                   "sock hop"))
    disco = w("DISCO", 79.5)
    S.append(Scene(w("THE", 79.5) - 0.1, [BLACK,
                                         sparkles(16, seed=14, box=BOX, color=(255, 120, 240), rate=3),
                                         sparkles(16, seed=15, box=BOX, color=(90, 220, 255), rate=3),
                                         thread(20, 0, 7),
                                         icon("🪩", 16, 20, 14, at=disco - 0.2, enter="drop", motion="swing",
                                              amp=0.5)], "disco ball"))

    # ---- chorus 2
    S += chorus(tm, w("I'D", 85), 1)
    S.append(asleep_scene(w("SEEMS", 103) + 1.5, 50))

    # ---- bridge
    S.append(Scene(w("LEAVE", 109) - 0.1, [BLACK, door_crack(open_at=w("CRACK", 109) - 0.3),
                                          fireflies(10, seed=16, box=(26, 4, 40, 27), at=w("CRACK", 109))],
                   "door open a crack"))
    S.append(Scene(w("CAUSE", 114) - 0.1, [BLACK, stars(10, seed=17, ymax=30), icon("🌙", 8, 34, 5, enter="fade"),
                                          icon("🦉", 22, 20, 16, enter="rise", motion="pulse",
                                               hits=[w("INSOMNIAC", 115)], amp=1.5)], "insomniac"))
    sheep_t = w("WHY", 120)
    S.append(Scene(sheep_t - 0.1, [BLACK, stars(8, seed=18, ymax=12), ground(24, (10, 60, 20), hill=0.6),
                                   fence(), jumping_sheep(beats_after(beats, sheep_t, 20)[::2][:8])],
                   "counting sheep"))
    S.append(Scene(w("WHEN", 125) - 0.1, [BLACK, stars(8, seed=19, ymax=30),
                                         icon("🥱", 22, 20, 15, enter="grow", motion="bob")], "too tired"))

    # ---- verse 3
    ff = w("FIREFLIES", 131)
    S.append(Scene(w("TO", 130.5) - 0.1, [BLACK, fireflies(60, seed=20, grow=1.2),
                                         text("FIREFLIES", 12, FLY, at=ff, until=ff + 1.6)], "ten million 2"))
    S.append(Scene(w("I'M", 133) - 0.1, [BLACK, fireflies(14, seed=21),
                                        icon("👋", 18, 20, 15, enter="pop", motion="swing", amp=1.5)], "goodbyes"))
    S.append(Scene(w("I", 136) - 0.1, [BLACK, fireflies(24, seed=22, rise=4.0, at=w("FAREWELL", 137)),
                                      icon("🥲", 20, 20, 16, enter="grow")], "misty eyes"))
    S.append(Scene(w("BUT", 141) - 0.1, [BLACK, ground(26, (10, 60, 20), hill=1.0),
                                        icon("🌳", 22, 20, 15, enter="rise"),
                                        fireflies(5, seed=23, box=(10, 4, 30, 20))], "several are"))
    S.append(Scene(w("IF", 144) - 0.1, [BLACK, sparkles(12, seed=24, box=BOX, color=(255, 170, 255)),
                                       icon("🌈", 18, 20, 9, at=w("BIZARRE", 144), enter="pop"),
                                       icon("🦄", 18, 20, 18, enter="grow", motion="bob")], "bizarre"))
    jar_t = w("CAUSE", 146)
    S.append(Scene(jar_t - 0.1, [BLACK, fireflies(8, seed=25, box=(14, 9, 26, 25), at=w("SAVED", 146), speed=0.6),
                                 jar(at=jar_t)], "jar"))

    # ---- choruses 3-5
    S += chorus(tm, w("I'D", 152), 2)
    S.append(asleep_scene(w("SEEMS", 170) + 1.5, 52))
    S += chorus(tm, w("I'D", 173), 3)
    S.append(asleep_scene(w("SEEMS", 191) + 1.5, 54))
    S += chorus(tm, w("I'D", 195), 4, seems=False)  # the last one ends on "because my dreams are bursting at the seams"

    burst = w("BURSTING", 211)
    S.append(Scene(w("BECAUSE", 210) - 0.1, [BLACK, icon("💭", 26, 20, 15, enter="grow", until=burst + 0.2,
                                                        motion="pulse", hits=tm.beats_in(210, burst + 0.2)),
                                            fireworks(beats_after(beats, burst, 8), seed=26),
                                            fireflies(50, seed=27, at=burst, grow=1.0)], "bursting"))

    # ---- outro: the jar is opened and the fireflies go home
    out = w("SEAMS", 213) + 1.5
    end = tm.duration
    fade = lambda f: ease((f.t - (end - 3.0)) / 3.0)  # noqa: E731
    S.append(Scene(out, [BLACK, stars(12, seed=28, ymax=30), icon("🌙", 8, 33, 5, enter="fade"),
                         jar(),
                         fireflies(10, seed=29, box=(14, 9, 26, 25), speed=0.6),
                         fireflies(30, seed=30, box=(0, 0, W, 24), rise=3.0, at=out + 2.0, grow=6.0),
                         dim(fade)], "outro"))
    return S
