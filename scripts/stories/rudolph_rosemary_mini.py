"""Storybook for 'Rudolph the Red-Nosed Reindeer' (Rosemary Clooney) on the 25x24 mini matrices, ShowFolder3D.

    python matrix_storybook.py stories/rudolph_rosemary_mini.py \
        "E:/2023/ShowFolder3D/Rudolph - Rosemary Clooney.xsq" OUT.mp4 \
        --size 25x24 --k 1 --ss 4 --scale 20 --flat --fps 40 --jobs 10

Words come from the sequence's "Lyric Main" track (capitals). The reindeer names pop up one deer at a time, Rudolph's
drawn red nose glows on "red"/"shiny"/"glows"/"bright", the others laugh, a foggy Christmas Eve, Santa asks, the sleigh
flies, hearts and fireworks. The 74-104 s instrumental is a sleigh ride across the moon.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from minis_common import (BLACK, BOX, SHOW, big, fog, flyer, flying_rudolph, red_nose, w,  # noqa: E402
                          words_from_track)
from matrix_storybook import (Scene, confetti, fireworks, glow, ground, icon, rising, snow,  # noqa: E402
                              sparkles, stars, text)

XSQ = SHOW / "Rudolph - Rosemary Clooney.xsq"
DEER = "🦌"  # faces left; nose at (-0.30, -0.15) x size from its centre


def nose(cx, cy, size, flip=False):
    return cx + (0.30 if flip else -0.30) * size, cy - 0.15 * size


def rudolph(cx, cy, size, hits=None, at=None, flip=False, glow_r=4.0, enter="pop", motion="bob", **kw):
    nx, ny = nose(cx, cy, size, flip)
    return [icon(DEER, size, cx, cy, at=at, enter=enter, motion=motion, flip=flip, **kw),
            red_nose(nx, ny, hits=hits, at=at, r=max(0.7, size / 16), glow_r=glow_r)]


def foggy_eve(tm, t):
    santa = w(tm, "santa", t)
    return [Scene(t, [BLACK, icon("🌕", 9, 17, 6, enter="fade", enter_s=1.5), stars(6, seed=31, ymax=10),
                      ground(20, snowy=True), icon("🎄", 9, 6, 15, enter="fade"), fog(0.9, seed=5)], "fog"),
            Scene(santa - 0.2, [BLACK, snow(10, seed=32, speed=2), fog(0.6, seed=6),
                                icon("🎅", 16, 12.5, 12.5, enter="right", enter_s=0.6, motion="wobble")], "santa")]


def guide_sleigh(tm, t):
    bright, sleigh = w(tm, "bright", t), w(tm, "sleigh", t)
    return [Scene(t - 0.2, [BLACK, stars(8, seed=33, ymax=24),
                            *rudolph(13.5, 13, 17, hits=[w(tm, "nose", t), bright], enter="left", glow_r=5)],
                  "with your nose"),
            Scene(w(tm, "won't", t) - 0.2, [BLACK, stars(10, seed=34, ymax=14), icon("🌕", 8, 19, 5, enter=None),
                                            *rudolph(6, 12, 9, hits=[sleigh], motion="bounce", glow_r=3),
                                            icon("🛷", 11, 17, 15, at=sleigh, enter="right", motion="bob")],
                  "guide my sleigh")]


def loved_glee(tm, t):
    loved, glee = w(tm, "loved", t), w(tm, "glee", t)
    return [Scene(t - 0.2, [BLACK, rising("❤️", n=5, seed=35, size=3, box=(1, 24), speed=4, at=loved - 0.3),
                            *rudolph(12.5, 13, 14, hits=[loved]),
                            icon("❤️", 6, 19, 5, at=loved, enter="pop", motion="pulse", amp=2)], "loved him"),
            Scene(w(tm, "as", t + 2) - 0.2, [BLACK, confetti(30, seed=36, at=glee - 0.1),
                                             icon(DEER, 8, 5, 16, enter="left", motion="bounce"),
                                             icon(DEER, 8, 20, 16, enter="right", motion="bounce", flip=True),
                                             icon("🎉", 10, 12.5, 7, at=glee, enter="pop", motion="pulse")],
                  "glee")]


def history(tm, t):
    red, hist = w(tm, "red", t), w(tm, "history", t)
    return [Scene(t - 0.2, [BLACK, stars(10, seed=37), sparkles(6, seed=38, box=BOX),
                            *rudolph(12.5, 14, 17, hits=[red, w(tm, "reindeer", t)], glow_r=6),
                            text("RED", 1, (255, 60, 50), at=red, until=red + 1.6)], "red nosed reindeer"),
            Scene(w(tm, "you'll", t) - 0.2, [BLACK, fireworks(tm.beats_in(hist - 1.5, hist + 8)[::2], seed=39),
                                             icon("⭐", 13, 12.5, 12, enter="grow", motion="pulse", amp=1.5),
                                             sparkles(8, seed=40, box=BOX)], "history")]


def build(tm):
    words_from_track(tm, XSQ, "Lyric Main", 1)
    S = []

    # ---- the eight reindeer, one per name, in two rows of four
    names = ["dasher", "dancer", "prancer", "vixen", "comet", "cupid", "donner", "blitzen"]
    layers = [BLACK, snow(10, seed=1, speed=2)]
    for k, nm in enumerate(names):
        x, y = 3.5 + (k % 4) * 6, 7 + (k // 4) * 10
        layers.append(icon(DEER, 7, x, y, at=w(tm, nm), enter="pop", motion="bounce",
                           hits=tm.beats_in(w(tm, nm), 11)[k % 2::2], amp=0.4))
    S.append(Scene(0.0, layers, "names"))

    S.append(big(w(tm, "but") - 0.2, "🤔", 16, motion="wobble", bg=[stars(6, seed=2)], name="recall"))
    famous = w(tm, "famous")
    S.append(Scene(w(tm, "the", 13) - 0.2, [BLACK, sparkles(8, seed=3, box=BOX),
                                            icon("⭐", 15, 12.5, 12.5, at=famous, enter="grow", motion="pulse")],
                   "most famous"))

    # ---- Rudolph and his nose
    red = w(tm, "red")
    S.append(Scene(w(tm, "rudolph") - 0.2, [BLACK, stars(8, seed=4), ground(21, snowy=True),
                                            icon(DEER, 16, 12.5, 12.5, enter="rise", motion="bob"),
                                            red_nose(*nose(12.5, 12.5, 16), at=red, hits=[red], r=1.0),
                                            text("RED", 1, (255, 60, 50), at=red, until=red + 1.6)], "rudolph"))
    shiny, nose_t = w(tm, "shiny"), w(tm, "nose")
    # close-up: just the head, very big, nose glowing
    S.append(Scene(w(tm, "had") - 0.2, [BLACK, *rudolph(13.5, 13, 22, hits=[shiny, nose_t], enter="fade",
                                                         motion=None, glow_r=7)], "shiny nose", cut=True))
    glows = w(tm, "glows")
    S.append(Scene(w(tm, "and", 24) - 0.2, [BLACK, stars(10, seed=5),
                                            glow(12.5, 12, 12, (255, 40, 30),
                                                 lambda f: 0.15 + 0.45 * min(1, max(0, (f.t - glows + 3) / 3))),
                                            *rudolph(12.5, 13, 15, hits=[glows], glow_r=5, motion="bob"),
                                            text("GLOWS", 1, (255, 70, 60), at=glows)], "glows"))

    # ---- the others laugh, no reindeer games
    laugh = w(tm, "laugh")
    S.append(Scene(w(tm, "all", 31) - 0.2, [BLACK, ground(21, snowy=True),
                                            icon(DEER, 9, 5, 15, enter="left", flip=True),
                                            icon(DEER, 9, 20, 15, enter="right"),
                                            icon("😂", 7, 5, 5, at=laugh, enter="pop", motion="shake"),
                                            icon("😂", 7, 20, 5, at=laugh + 0.3, enter="pop", motion="shake")],
                   "laugh"))
    games = w(tm, "games")
    S.append(Scene(w(tm, "they", 38) - 0.2, [BLACK, snow(8, seed=7, speed=1.5),
                                             *rudolph(12.5, 13, 14, enter="fade", motion=None, glow_r=2.5),
                                             icon("😢", 6, 19, 5, at=w(tm, "poor"), enter="pop"),
                                             icon("🚫", 22, 12.5, 12.5, at=games, enter="pop", alpha=0.85)],
                   "no games"))

    # ---- foggy Christmas Eve, Santa, guide my sleigh, loved him, history
    S += foggy_eve(tm, w(tm, "then") - 0.2)
    S += guide_sleigh(tm, w(tm, "rudolph", 52))
    S += loved_glee(tm, w(tm, "then", 60))
    S += history(tm, w(tm, "rudolph", 67))

    # ---- instrumental 74-103.7: the sleigh ride across the moon, then over the snowy town
    t0 = 75.0
    S.append(Scene(t0, [BLACK, stars(14, seed=41), icon("🌕", 8, 19.5, 5, enter="fade", enter_s=2.0),
                        snow(6, seed=44, speed=1.5),
                        flying_rudolph(9, 13, t0 + 1, t0 + 7, -6, 34, arc=-4),
                        flyer("🛷", 10, 15, t0 + 2.2, t0 + 8.2, x0=-15, x1=25, arc=-4, flip=True),
                        flying_rudolph(9, 13, t0 + 8, t0 + 14, 31, -9, arc=-4),
                        flyer("🛷", 10, 15, t0 + 9.2, t0 + 15.2, x0=40, x1=0, arc=-4)], "moon ride"))
    t1 = 90.0
    S.append(Scene(t1, [BLACK, stars(10, seed=42, ymax=10), snow(12, seed=43, speed=2), ground(20, snowy=True),
                        icon("🏠", 9, 6, 15, enter="rise"), icon("🏠", 8, 19, 16, enter="rise"),
                        icon("🎁", 5, 12.5, 19, at=t1 + 6, enter="drop"),
                        flyer("🎅", 7, 5, t1 + 1, t1 + 6, x0=-5, x1=30, arc=-1)], "town"))

    # ---- second time round
    S += foggy_eve(tm, w(tm, "then", 103) - 0.2)
    S += guide_sleigh(tm, w(tm, "rudolph", 110))
    S += loved_glee(tm, w(tm, "then", 117))
    S += history(tm, w(tm, "rudolph", 124))
    return S
