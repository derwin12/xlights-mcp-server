"""Ambient story for the '2025 Static Witchs Brew' static sequence on the 25x24 mini matrices, ShowFolder3D.

    python matrix_storybook.py stories/static_witchs_brew_mini.py \
        "E:/2023/ShowFolder3D/2025 Static Witchs Brew.xsq" OUT.mp4 \
        --size 25x24 --k 1 --ss 4 --scale 20 --flat --fps 40 --jobs 10

No audio: a slow 90 s loop in three parts on the sequence's marks (0, 30.1, 60.2) with a steady 1 s pulse.
Green and purple: a bubbling cauldron under the moon, a witch flying past the moon with bats, potions glowing.
It ends on the cauldron again so the loop joins up.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from minis_common import BLACK, BOX, GREEN, PURPLE, cauldron, flyer, steady_beats  # noqa: E402
from matrix_storybook import Scene, glow, icon, sparkles, stars  # noqa: E402

BREW = (70, 255, 90)


def pot_scene(t, seed, beats):
    return Scene(t, [BLACK, stars(10, seed=seed, ymax=10), icon("🌕", 6, 20.5, 4, enter="fade", motion=None),
                     sparkles(6, seed=seed + 1, box=(2, 2, 23, 12), color=(200, 140, 255)),
                     cauldron(12.5, 14, 16, BREW, hits=beats[::3], seed=seed)], "cauldron")


def build(tm):
    steady_beats(tm, 1.0)
    b = tm.beats
    S = [pot_scene(0.0, 1, b)]
    # ---- 30.1: the witch flies past the moon, twice, with bats
    t = 30.1
    S.append(Scene(t, [BLACK, stars(14, seed=3), glow(12.5, 10, 9, (255, 240, 180), 0.25),
                       icon("🌕", 14, 12.5, 10, enter="fade", enter_s=2.0, motion=None),
                       flyer("🧙", 9, 10, t + 2, t + 10, x0=32, x1=-8, arc=-2, motion="bob"),
                       flyer("🧹", 9, 14, t + 2, t + 10, x0=32, x1=-8, arc=-2),
                       flyer("🦇", 5, 5, t + 11, t + 15, x0=-4, x1=30, arc=3, motion="bounce", hits=b),
                       flyer("🦇", 4, 18, t + 12, t + 16, x0=-4, x1=30, arc=-3, motion="bounce", hits=b[1:]),
                       flyer("🧙", 9, 12, t + 17, t + 26, x0=-8, x1=32, arc=-4, flip=True, motion="bob"),
                       flyer("🧹", 9, 16, t + 17, t + 26, x0=-8, x1=32, arc=-4, flip=True)], "witch and moon"))
    # ---- 60.2: potions glowing, then back to the cauldron for the loop
    t = 60.2
    S.append(Scene(t, [BLACK, stars(8, seed=4, ymax=8),
                       glow(6, 14, 6, PURPLE, 0.45), glow(19, 14, 6, GREEN, 0.45),
                       icon("🧪", 11, 6, 14, enter="rise", motion="pulse", hits=b[0::2]),
                       icon("⚗️", 11, 19, 14, enter="rise", enter_s=0.8, motion="pulse", hits=b[1::2]),
                       sparkles(10, seed=5, box=BOX, color=(170, 255, 170))], "potions"))
    S.append(pot_scene(78.0, 6, b))
    return S
