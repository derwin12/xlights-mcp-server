"""Storybook for 'I Want a Hippopotamus for Christmas' on the 25x24 mini matrices (Matrix-mini-left/right).

One LED per story pixel, blown up 20x so the xLights Video effect samples one colour per LED:
    python scripts/matrix_storybook.py scripts/stories/hippopotamus_for_christmas_mini.py \
        "E:/2023/ShowFolder3D/I Want a Hippopotamus for Christmas SS.xsq" OUT.mp4 \
        --size 25x24 --k 1 --ss 4 --scale 20 --flat --fps 40 --jobs 10

Same story as hippopotamus_for_christmas.py (the 48x27 Garage layout), re-staged for a small square matrix: one big
picture per scene (two at most), black backgrounds, and only words that fit the 3x5 font in 25 pixels.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hippopotamus_for_christmas import (BLACK, HIPPO, KID, NO, beats_after, board, cape, chalk_equals,  # noqa: E402
                                        falling, garage, hatted_hippo, keyframes_fn, pond, stair_kid, stairs,
                                        tm_after, toss)
from matrix_storybook import (Scene, confetti, dim, ease, fireworks, glow, ground, icon, keyframes,  # noqa: E402
                              rising, snow, sparkles, spotlight, stars, steam, text, tree_lights)

RED = (255, 60, 50)
GREEN = (60, 230, 90)
WHITE = (255, 255, 255)
PURPLE = (200, 120, 255)
BOX = (0, 0, 25, 24)


def stairs_scene(tm, start, end_):
    beats = tm.beats_in(start + 1.0, end_ - 0.5)
    hits = beats[1::2][:5]
    geo = dict(x0=0, y0=6, steps=6, w=3.0, h=2.6)
    return Scene(start, [BLACK, stars(6, seed=21, ymax=6),
                         glow(20.5, 16, 7, (255, 200, 80), 0.3),
                         icon("🎄", 9, 20.5, 16, enter="fade", enter_s=1.0),
                         tree_lights((17, 12, 24, 20), 5, seed=22),
                         stairs(**geo), stair_kid(hits, size=6, **geo)], "stairs")


def surprise_scene(tm, start):
    w = lambda word: tm_after(tm, word, start)  # noqa: E731
    return Scene(start, [BLACK, sparkles(6, seed=23, box=BOX),
                         icon("😴", 18, 12.5, 12, enter="grow", until=w("open")),
                         icon("😲", 18, 12.5, 12, at=w("open"), enter="pop", motion="pulse",
                              hits=[w("open"), w("eyes"), w("see")])], "surprise")


def hero_scene(tm, start):
    w = lambda word: tm_after(tm, word, start)  # noqa: E731
    return Scene(start, [BLACK, spotlight(11, strength=0.22), stars(8, seed=24, ymax=24),
                         cape(15, 11, length=10),
                         icon(HIPPO, 16, 10.5, 13, enter="grow", motion="bob", amp=0.6),
                         confetti(30, seed=25, at=w("there") - 0.2)], "hero")


def gift_scene(tm, start):
    pop = tm_after(tm, "hippopotamus", start)
    return Scene(start, [BLACK, sparkles(6, seed=26, box=BOX),
                         icon("🎁", 15, 12.5, 12.5, enter="drop", until=pop, exit_s=0.1, motion="shake",
                              hits=tm.beats_in(start, pop)),
                         glow(12.5, 12.5, 10, (255, 220, 120),
                              lambda f: 0.6 * max(0.0, 1 - (f.t - pop) / 1.0) if f.t >= pop else 0),
                         icon(HIPPO, 17, 12.5, 13, at=pop, enter="pop", motion="bob"),
                         confetti(30, seed=27, at=pop)], "gift")


def only_scene(tm, start, seed):
    beats = tm.beats_in(start, start + 5)
    return Scene(start, [BLACK, sparkles(8, seed=seed, box=BOX),
                         rising("❤️", n=4, seed=seed, size=3, box=(1, 24), speed=4),
                         hatted_hippo(17, 12.5, 14, hits=beats[::2], amp=0.4)], "only")


def no_scene(tm, start, emoji, word, flip=False, name="no"):
    at = tm_after(tm, word, start)
    return Scene(start, [BLACK, ground(22, (30, 110, 40)),
                         icon(emoji, 18, 12.5, 12.5, enter="left" if flip else "right", enter_s=0.5, flip=flip,
                              motion="bob"),
                         icon(NO, 19, 12.5, 12.5, at=at, enter="pop", alpha=0.9)], name, cut=True)


def parade_scene(tm, start, end_):
    beats = tm.beats_in(start, end_ + 1)
    layers = [BLACK, stars(8, seed=27, ymax=12), ground(22.5, snowy=True, hill=0.6)]
    for k, sz in enumerate((12, 10, 11)):
        x = (lambda kk: lambda f: 33 - ((f.t - start) * 5.0 + kk * 15) % 45)(k)  # march right to left, wrapping
        layers.append(icon(HIPPO, sz, x, 21.6 - sz * 0.35, enter=None, motion="bounce", hits=beats[k % 2::2],
                           amp=0.5))
    return Scene(start, layers, "parade")


def love_scene(tm, start, seed):
    beats = tm.beats_in(start, start + 6)
    return Scene(start, [BLACK, rising("❤️", n=5, seed=seed, size=3, box=(1, 24), speed=5),
                         icon(KID, 9, 5.5, 15, enter="left", motion="bounce", hits=beats[0::2]),
                         icon(HIPPO, 12, 17.5, 15, enter="right", motion="bounce", hits=beats[1::2]),
                         icon("❤️", 5, 12, 6, at=tm_after(tm, "me", start), enter="pop", motion="pulse", amp=2)],
                 "love")


def skater(x, flip):
    right = icon(HIPPO, 11, x, 15, enter=None, flip=True, rot=lambda f: -6 * math.sin(f.t * 3))
    left = icon(HIPPO, 11, x, 15, enter=None, flip=False, rot=lambda f: 6 * math.sin(f.t * 3))

    def draw(f):
        (right if flip(f) else left)(f)
    return draw


def build(tm):
    S = []
    w = lambda word, t: tm_after(tm, word, t)  # noqa: E731
    beats = tm.beats

    # ---- intro (music only): a quiet snowy night, a present under the tree
    S.append(Scene(0.0, [BLACK, stars(12, seed=1, ymax=20), snow(14, seed=2, speed=2.0),
                         ground(21, snowy=True),
                         icon("🎄", 12, 12.5, 14.5, at=0.5, enter="fade", enter_s=2.0),
                         icon("🎁", 6, 19.5, 18.5, at=4.8, enter="drop", motion="pulse",
                              hits=tm.beats_in(4.8, 8.3)[::2])], "intro"))

    # ---- verse 1: the words with the singing - "I WANT" on "I", "HIPPO!" on "hippopotamus"
    i_at, hippo_at = w("I", 8.0), w("hippopotamus", 8.0)
    S.append(Scene(i_at - 0.1, [BLACK, stars(10, seed=1, ymax=20), snow(12, seed=2, speed=2.0),
                                ground(21, snowy=True),
                                text("I WANT", 2, WHITE, at=i_at, until=hippo_at),
                                text("HIPPO!", 2, PURPLE, at=hippo_at),
                                icon(HIPPO, 13, 12.5, 15.5, at=hippo_at, enter="rise", enter_s=0.6, motion="bob")],
                   "title"))
    S.append(Scene(w("Christmas", 10.0) - 0.1, [BLACK, sparkles(5, seed=3, box=BOX),
                                                icon(KID, 10, 6, 17, enter="rise"),
                                                icon("💭", 15, 16, 8, enter="pop"),
                                                icon(HIPPO, 8, 16, 8, at=w("Christmas", 10.0) + 0.2, enter="pop",
                                                     motion="bob")], "wish"))
    S.append(only_scene(tm, 13.1, 4))
    # no dolls, no dinky tinker toys: one at a time, crossed out
    for em, t0, t1, hit in (("🪆", 17.4, 19.68, 18.9), ("🧸", 19.68, 20.18, 19.9), ("🚂", 20.18, 21.45, 20.73)):
        S.append(Scene(t0, [BLACK, icon(em, 15, 12.5, 12.5, enter="drop", enter_s=0.25),
                            icon(NO, 18, 12.5, 12.5, at=hit, enter="pop", alpha=0.9)], f"no {em}", cut=True))
    play = tm.beats_in(21.4, 25.6)
    S.append(Scene(21.45, [BLACK, stars(6, seed=5, ymax=8), ground(21, snowy=True),
                           icon(KID, 9, 4.5, 16.5, enter="left", motion="bounce", hits=play[0::2]),
                           icon(HIPPO, 11, 19, 16, enter="right", motion="bounce", hits=play[1::2]),
                           toss((7.5, 13), (15, 12), play, size=4, peak=7)], "play"))
    S.append(gift_scene(tm, 25.5))

    S.append(Scene(30.05, [BLACK, stars(10, seed=6), snow(10, seed=7, speed=2),
                           icon("🎅", 16, 12.5, 12.5, enter="left", motion="wobble"),
                           icon("👍", 9, 19.5, 18, at=31.93, enter="pop", motion="pulse")], "santa"))
    S.append(Scene(34.3, [BLACK, stars(10, seed=8, ymax=10), snow(10, seed=9, speed=2), ground(21, snowy=True),
                          icon("🏠", 18, 12.5, 13, enter=None),
                          steam(17, 5, n=1, height=4, color=(70, 70, 80)),
                          icon(NO, 10, 17, 5, at=35.0, enter="pop", alpha=0.9)], "chimney"))
    walk = lambda f: keyframes([(38.75, -8), (40.12, 8), (42.0, 8.5)], f.t)  # noqa: E731
    S.append(Scene(38.45, [BLACK, ground(21, (90, 60, 30)),
                           glow(17, 11, 8, (255, 230, 150), 0.3),
                           icon("🚪", 14, 17.5, 12, enter="fade"),
                           icon(HIPPO, 11, walk, 15.5, enter=None, flip=True, motion="bob", amp=0.6)],
                   "front door"))

    # ---- bridge: Christmas morning
    S.append(stairs_scene(tm, 42.5, 50.9))
    S.append(surprise_scene(tm, 50.85))
    S.append(hero_scene(tm, w("hippo", 55.0) - 0.05))

    # ---- chorus 2
    S.append(Scene(59.65, [BLACK, stars(8, seed=11, ymax=12), snow(14, seed=12, speed=2), ground(21, snowy=True),
                           icon(KID, 9, 5.5, 16, enter="left"),
                           hatted_hippo(13, 16.5, 15, enter="right", bob=True)], "together"))
    S.append(only_scene(tm, 63.95, 14))
    S.append(no_scene(tm, 68.3, "🐊", "crocodiles", name="no crocodiles"))
    S.append(no_scene(tm, 70.2, "🦏", "roses", flip=True, name="no rhinos"))
    S.append(parade_scene(tm, 72.35, 76.6))
    S.append(love_scene(tm, 76.55, 15))

    # ---- instrumental: skating
    skate_x = lambda f: 12.5 + 7 * math.sin((f.t - 80.4) * 2 * math.pi / 4.2)  # noqa: E731
    skate_flip = lambda f: math.cos((f.t - 80.4) * 2 * math.pi / 4.2) > 0  # noqa: E731
    S.append(Scene(80.4, [BLACK, stars(12, seed=16, ymax=12), icon("🌙", 5, 21, 3.5, enter="fade"),
                          pond(cy=19.5, rx=13, ry=3.5), skater(skate_x, skate_flip)], "skating"))

    # ---- verse 2
    S.append(Scene(89.3, [BLACK, icon("👩", 11, 6.5, 15, enter="left"),
                          icon("💬", 13, 17, 7, at=89.92, enter="pop"),
                          icon(HIPPO, 7, 17, 6.5, at=90.45, enter="pop", motion="pulse", hits=[91.6, 91.8, 91.97],
                               amp=2.5),
                          icon("😱", 8, 19, 19, at=91.6, enter="pop", motion="shake", hits=[91.6, 91.97])], "mom"))
    S.append(Scene(93.35, [BLACK, board(x0=0.5, y0=1, x1=24.5, y1=13),
                           icon(HIPPO, 7, 6, 7, at=94.6, enter="pop"),
                           chalk_equals(12.5, 7, 95.08),
                           icon("🥕", 6, 18.5, 7, at=95.62, enter="pop"),
                           icon("👩\u200d🏫", 10, 12.5, 19, enter="rise")], "teacher"))
    munch = tm.beats_in(97.3, 106)
    S.append(Scene(97.2, [BLACK, ground(22, (40, 120, 40)),
                          falling(["🥕", "🥬", "🍉", "🍎", "🥦"], n=6, seed=19, size=4, speed=8, box=(1, 24)),
                          icon(HIPPO, 15, 12.5, 15, enter="grow", motion="pulse", hits=munch, amp=0.8)], "munch"))

    # ---- the two-car garage
    S.append(Scene(105.9, [BLACK, garage(x0=2, x1=23, y0=8, y1=21),
                           icon("🚗", 6, keyframes_fn([(108.47, 7.75), (109.3, -8)]), 18, enter=None),
                           icon("🚗", 6, keyframes_fn([(108.67, 17.25), (109.5, 33)]), 18, enter=None, flip=True),
                           icon(HIPPO, 11, 12.5, 16, at=109.03, enter="drop", motion="bob")], "garage"))
    S.append(Scene(110.15, [BLACK, glow(13, 14, 10, (255, 170, 80), 0.25),
                            icon(HIPPO, 15, 13.5, 14.5, enter=None, motion="bob", amp=0.4),
                            icon("🍉", 6, 3.5, 17, at=110.33, enter="pop", until=111.4),
                            rising("🫧", n=5, seed=22, size=3, box=(6, 22), speed=9, at=111.42),
                            icon("🧽", 5, 16, 9, at=111.42, enter="pop", until=112.5, motion="shake",
                                 hits=tm.beats_in(111.4, 112.6)),
                            icon("💆", 6, 19, 5, at=112.53, enter="pop", motion="bob"),
                            rising("❤️", n=3, seed=23, size=3, box=(8, 20), speed=5, at=113.35)], "care"))

    # ---- bridge 2
    S.append(stairs_scene(tm, 114.05, 122.4))
    S.append(surprise_scene(tm, 122.4))
    S.append(hero_scene(tm, w("hippo", 127.0) - 0.05))

    # ---- final chorus
    S.append(gift_scene(tm, 131.2))
    S.append(only_scene(tm, 135.5, 30))
    S.append(no_scene(tm, 139.85, "🐊", "crocodiles", name="no crocodiles 2"))
    S.append(no_scene(tm, 141.75, "🦏", "roses", flip=True, name="no rhinos 2"))
    S.append(parade_scene(tm, 143.95, 148.1))
    S.append(love_scene(tm, 148.1, 31))

    # ---- finale
    fin = 150.9
    end = tm.duration
    fade = lambda f: ease((f.t - (end - 2.5)) / 2.5)  # noqa: E731
    hits = beats_after(beats, fin, 10)
    S.append(Scene(fin, [BLACK, fireworks(hits, seed=32),
                         icon("🎄", 10, 19.5, 12.5, enter="grow"),
                         hatted_hippo(10, 7, 13, hits=hits, amp=0.4),
                         text("MERRY", 1, RED, at=fin + 0.3),
                         text("XMAS!", 18, GREEN, at=fin + 0.8),
                         dim(fade)], "finale"))
    return S
