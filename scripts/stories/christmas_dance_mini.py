"""Storybook for 'Christmas Dance' (Ashes Last) on the 25x24 mini matrices, ShowFolder3D.

    python matrix_storybook.py stories/christmas_dance_mini.py \
        "E:/2023/ShowFolder3D/Ashes Last - Christmas Dance.xsq" OUT.mp4 \
        --size 25x24 --k 1 --ss 4 --scale 20 --flat --fps 40 --jobs 10

Instrumental dance track (only "Let's get started!" is spoken, at 28.6 s). Sections from the sequence's
"New Timing" marks and the loudness: intro to 38.4, build 38.4-40.2, drop to 109.6, break to 123.2, build to 144,
drop to 191.4, outro. A Christmas dance party: a disco ball, Santa, elves, a snowman and reindeer dancing on the beats
in pairs that change every 8 bars.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from minis_common import BLACK, BOX, GOLD, bars, flash, rays  # noqa: E402
from matrix_storybook import (Scene, confetti, fireworks, ground, icon, snow, sparkles, stars, text,  # noqa: E402
                              tree_lights)

PAIRS = [("🎅", "💃"), ("🧝", "🕺"), ("⛄", "🦌"), ("💃", "🕺"), ("🎅", "🧝"), ("🦌", "⛄"), ("🕺", "🎅"), ("🧝", "💃")]


def dance(tm, t0, t1, k):
    a, b = PAIRS[k % len(PAIRS)]
    beats = tm.beats_in(t0, t1 + 1)
    return Scene(t0, [BLACK, rays(12.5, 2, n=8, hits=beats, strength=0.3), confetti(12, seed=40 + k),
                      icon(a, 12, 6.5, 15, enter="left", enter_s=0.3, motion="bounce", hits=beats[0::2], amp=0.8),
                      icon(b, 12, 18.5, 15, enter="right", enter_s=0.3, motion="bounce", hits=beats[1::2], amp=0.8,
                           flip=True),
                      icon("🪩", 6, 12.5, 3, enter="drop", motion="pulse", hits=beats)], f"dance {a}{b}", cut=True)


def solo(tm, t0, t1, emoji, k):
    beats = tm.beats_in(t0, t1 + 1)
    return Scene(t0, [BLACK, rays(12.5, 12.5, n=10, hits=beats, strength=0.35), sparkles(8, seed=60 + k, box=BOX),
                      icon(emoji, 17, 12.5, 13, enter="pop", motion="bounce", hits=beats, amp=0.7)], f"solo {emoji}",
                 cut=True)


def party(tm, t0, t1, k0):
    """Scenes every 8 bars between t0 and t1: pairs, with a solo every third."""
    bs = [b for b in bars(tm) if t0 - 0.05 <= b < t1 - 2]
    starts = [t0] + [b for b in bs[::8] if b > t0 + 4]
    out = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else t1
        k = k0 + i
        out.append(solo(tm, s, e, ("🪩", "🎅", "🦌")[k % 3], k) if i % 3 == 2 else dance(tm, s, e, k))
    return out


def build(tm):
    tm.bars = tm.beats[0::4]
    S = []
    # ---- intro: snowy night, the tree lights up on the beat; then a present that shakes
    S.append(Scene(0.0, [BLACK, stars(12, seed=1, ymax=14), snow(12, seed=2, speed=1.5), ground(21, snowy=True),
                         icon("🎄", 15, 12.5, 12.5, at=0.3, enter="fade", enter_s=3.0, motion=None),
                         tree_lights((5, 5, 20, 20), 7, seed=3, hits=tm.beats_in(0, 15))], "intro tree"))
    t = 14.6
    S.append(Scene(t, [BLACK, stars(8, seed=4, ymax=10), ground(20, snowy=True),
                       icon("🎁", 13, 12.5, 13, enter="drop", motion="shake", hits=tm.beats_in(t, 28.6)[::2])],
                   "present"))
    # ---- "Let's get started!" (spoken at 28.6-30.0)
    S.append(Scene(28.5, [BLACK, sparkles(6, seed=5, box=BOX),
                          icon("🎅", 16, 12.5, 14, enter="pop", motion="bounce", hits=tm.beats_in(28.5, 38.4)),
                          text("GO!", 1, GOLD, at=30.0, until=33.0)], "lets get started", cut=True))
    # ---- build 38.4 -> drop at 40.2
    S.append(Scene(38.4, [BLACK, icon("🪩", 9, 12.5, lambda f: -6 + 14 * min(1, (f.t - 38.4) / 1.8), enter=None),
                          sparkles(10, seed=6, box=BOX, rate=6)], "build"))
    drop1 = party(tm, 40.2, 109.6, 0)
    drop1[0].layers.append(flash([40.2], strength=0.7))
    S += drop1
    # ---- break 109.6-123.2: calm snowy night, a snowman by the tree
    S.append(Scene(109.6, [BLACK, stars(14, seed=7, ymax=14), snow(14, seed=8, speed=1.2), ground(20, snowy=True),
                           icon("🌲", 13, 7, 13, enter="fade", enter_s=1.5, motion=None),
                           icon("⛄", 11, 18, 15, at=111.5, enter="fade", enter_s=1.5, motion="bob")], "break"))
    # ---- build again 123.2-144: the present shakes harder, the disco ball comes down
    S.append(Scene(123.2, [BLACK, stars(8, seed=9, ymax=10), ground(20, snowy=True),
                           icon("🎁", 12, 12.5, 14, enter="drop", motion="shake", hits=tm.beats_in(123.2, 134)[::2])],
                   "build present"))
    S.append(Scene(134.0, [BLACK, sparkles(10, seed=10, box=BOX, rate=4),
                           icon("🪩", 11, 12.5, lambda f: -6 + 18 * min(1, (f.t - 134) / 8), enter=None,
                                motion="pulse", hits=tm.beats_in(134, 144))], "ball descends"))
    drop2 = party(tm, 144.0, 191.4, 3)
    drop2[0].layers.append(flash([144.0], strength=0.7))
    drop2[0].layers.append(fireworks(tm.beats_in(144, 150)[::2], seed=11))
    S += drop2
    # ---- outro
    S.append(Scene(191.4, [BLACK, stars(12, seed=12, ymax=14), snow(10, seed=13, speed=1.5), ground(21, snowy=True),
                           fireworks(tm.beats_in(191.4, 197)[::2], seed=14),
                           icon("🎄", 15, 12.5, 12.5, enter="fade", motion=None),
                           tree_lights((5, 5, 20, 20), 7, seed=15, hits=tm.beats_in(191.4, 198))], "outro"))
    return S
