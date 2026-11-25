"""Storybook for 'Jingle, Jingle, Jingle' (Rudolph the Red-Nosed Reindeer special) on the 25x24 mini matrices.

    python matrix_storybook.py stories/jingle_jingle_jingle_mini.py \
        "E:/2023/ShowFolder3D/Rudolph the Red Nosed Reindeer - Jingle Jingle Jingle.xsq" OUT.mp4 \
        --size 25x24 --k 1 --ss 4 --scale 20 --flat --fps 40 --jobs 10

The sequence has no Lyrics track: word times come from faster-whisper (stories/lyrics/jingle_jingle_jingle.json;
"Kris Kringle" was heard as "Chris Crangle"). A bell pops on each "jingle", Santa gets his crown on "king", the
reindeer fly and race, HO HO on "ho", a tree on "Christmas Eve", a present on "pass you by", the sleigh dashes away.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from minis_common import (BLACK, BOX, GOLD, RED, WHITE, big, flyer, flying_rudolph, w, ws,  # noqa: E402
                          words_from_json)
from matrix_storybook import (Scene, confetti, fireworks, ground, icon, snow, sparkles, stars, text,  # noqa: E402
                              tree_lights)

BELL = "🔔"


def jingles(tm, t):
    """Three bells, one on each 'jingle', then the sleigh with its bells ringing."""
    j = ws(tm, "jingle", t - 0.1, t + 2.5)[:3]
    ring = w(tm, "ring", t)
    return [Scene(t - 0.2, [BLACK, snow(10, seed=11, speed=2)] +
                  [icon(BELL, 9, x, 11, at=s, enter="drop", enter_s=0.3, motion="swing")
                   for x, s in zip((4.5, 12.5, 20.5), j)], "jingle x3", cut=True),
            Scene(w(tm, "you", t) - 0.15, [BLACK, stars(8, seed=12, ymax=12), ground(20, snowy=True),
                                           icon("🛷", 16, 12.5, 13, enter="right", enter_s=0.5, motion="bob"),
                                           icon(BELL, 6, 19, 5, at=ring - 0.3, enter="pop", motion="shake",
                                                hits=[ring, ring + 0.25, ring + 0.5])], "sleigh bells ring")]


def kringle(tm, t):
    king = w(tm, "king", t)
    return Scene(t - 0.2, [BLACK, sparkles(6, seed=13, box=BOX),
                           icon("🎅", 16, 12.5, 15, enter="pop", motion="wobble"),
                           icon("👑", 9, 12.5, 5, at=king, enter="drop", enter_s=0.35)], "kris kringle")


def ho_ho(tm, t, seed=14):
    h = ws(tm, "ho", t - 0.1, t + 1.5)
    return Scene(t - 0.15, [BLACK, confetti(24, seed=seed, at=h[0]),
                            icon("🎅", 14, 12.5, 15, enter="pop", motion="pulse", hits=h, amp=1.5),
                            text("HO", 1, RED, at=h[0], until=h[-1]), text("HO HO!", 1, RED, at=h[-1])], "ho ho", cut=True)


def believe(tm, t, seed=15):
    xmas = w(tm, "christmas", t)
    by = w(tm, "by", t)
    dash, magic, sky = w(tm, "dash", t), w(tm, "magic", t), w(tm, "sky", t)
    return [Scene(t - 0.2, [BLACK, stars(8, seed=seed), ground(21, snowy=True),
                            icon("🎄", 16, 12.5, 12.5, enter="fade", enter_s=0.6, motion="pulse", hits=[xmas]),
                            tree_lights((5, 4, 20, 19), 7, seed=seed, hits=[xmas])], "christmas eve"),
            Scene(w(tm, "won't", t) - 0.5, [BLACK, stars(6, seed=seed + 1, ymax=10), snow(8, seed=seed, speed=2),
                                              ground(20, snowy=True), icon("🏠", 14, 12.5, 13, enter="rise"),
                                              icon("🎁", 6, 19, 18, at=by, enter="drop")], "pass you by"),
            Scene(dash - 0.3, [BLACK, stars(12, seed=seed + 2), icon("🌕", 8, 19.5, 5, enter="fade"),
                               sparkles(8, seed=seed + 3, box=(0, 8, 25, 22)),
                               flying_rudolph(8, 13, dash, magic + 1.2, -6, 32, arc=-3),
                               flyer("🛷", 9, 15, dash + 0.5, magic + 1.7, x0=-14, x1=24, arc=-3, flip=True),
                               flying_rudolph(8, 13, magic + 1.2, sky + 1.0, 31, -8, arc=-4),
                               flyer("🛷", 9, 15, magic + 1.7, sky + 1.5, x0=40, x1=1, arc=-4)], "dash away")]


def reindeer(tm, t):
    r = w(tm, "reindeer", t)
    frosty, plain, fastest = w(tm, "through", t), w(tm, "they", t + 3), w(tm, "fastest", t)
    return [Scene(t - 0.2, [BLACK, snow(10, seed=16, speed=2)] +
                  [icon(BELL, 8, x, 6, at=s, enter="drop", motion="swing")
                   for x, s in zip((5, 20), ws(tm, "jingle", t - 0.1, t + 2))] +
                  [icon("🦌", 13, 12.5, 15, at=r, enter="pop", motion="bounce")], "jingle reindeer"),
            Scene(frosty - 0.2, [BLACK, stars(10, seed=17), snow(16, seed=18, speed=3, wind=3),
                                 flying_rudolph(12, 12, frosty, plain, -8, 33, arc=-5)], "frosty air"),
            Scene(plain - 0.2, [BLACK, ground(20, snowy=True),
                                icon("🦌", 15, 12.5, 12, enter="fade", motion=None, until=fastest - 0.1),
                                flyer("🦌", 13, 13, fastest - 0.1, fastest + 0.9, x0=30, x1=-8),
                                flyer("🦌", 13, 13, fastest + 0.9, fastest + 1.9, x0=30, x1=-8)], "fastest deer")]


def build(tm):
    words_from_json(tm, "jingle_jingle_jingle")
    S = [Scene(0.0, [BLACK, stars(10, seed=1, ymax=14), snow(10, seed=2, speed=1.5), ground(20, snowy=True),
                     icon(BELL, 11, 12.5, 10, at=0.8, enter="fade", enter_s=1.5, motion="swing")], "intro")]
    S += jingles(tm, w(tm, "jingle"))
    S.append(kringle(tm, w(tm, "i", 9.9)))
    S += reindeer(tm, w(tm, "jingle", 14))
    S.append(ho_ho(tm, w(tm, "ho")))
    S += believe(tm, w(tm, "you", 24.5))
    S += jingles(tm, w(tm, "jingle", 34))
    S.append(kringle(tm, w(tm, "i", 39.5)))
    S.append(ho_ho(tm, w(tm, "ho", 43), seed=19))
    S += believe(tm, w(tm, "you", 44.5), seed=20)
    S += jingles(tm, w(tm, "jingle", 54))
    S.append(kringle(tm, w(tm, "i", 59.5)))
    S.append(kringle(tm, w(tm, "i", 64.5)))
    last = w(tm, "ho", 70)
    S.append(ho_ho(tm, last, seed=21))
    S.append(Scene(last + 2.0, [BLACK, fireworks(tm.beats_in(last + 2, tm.duration), seed=22),
                                icon("🎅", 13, 12.5, 14, enter="pop", motion="bob"),
                                sparkles(8, seed=23, box=BOX)], "finale"))
    return S
