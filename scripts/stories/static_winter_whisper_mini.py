"""Ambient story for the 'Static 2024 Winter Whisper' static sequence on the 25x24 mini matrices, ShowFolder3D.

    python matrix_storybook.py stories/static_winter_whisper_mini.py \
        "E:/2023/ShowFolder3D/Static 2024 Winter Whisper.xsq" OUT.mp4 \
        --size 25x24 --k 1 --ss 4 --scale 20 --flat --fps 40 --jobs 10

No audio: a slow 90 s loop in three parts on the sequence's marks (0, 30.0, 60.1). Icy whites and blues: a big
snowflake turning in the snow, the northern lights over the pines, a snowman under the moon; it ends on the
snowflake again so the loop joins up.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from minis_common import BLACK, ICE, aurora, spin, steady_beats  # noqa: E402
from matrix_storybook import Scene, glow, ground, icon, snow, sparkles, stars  # noqa: E402


def flake_scene(t, seed):
    return Scene(t, [BLACK, glow(12.5, 12.5, 11, ICE, 0.25), snow(16, seed=seed, speed=1.5, wind=0.4),
                     icon("❄️", 17, 12.5, 12.5, enter="fade", enter_s=2.0, rot=spin(12, t), motion=None),
                     sparkles(6, seed=seed + 1, box=(1, 1, 24, 23), rate=1.0)], "snowflake")


def build(tm):
    steady_beats(tm, 1.0)
    S = [flake_scene(0.0, 1)]
    S.append(Scene(30.0, [BLACK, stars(14, seed=3, ymax=10), aurora(y=4, strength=0.6), ground(21, snowy=True),
                          icon("🌲", 10, 5, 15, enter="fade", enter_s=2, motion=None),
                          icon("🌲", 12, 12.5, 14, enter="fade", enter_s=2, motion=None),
                          icon("🌲", 10, 20, 15, enter="fade", enter_s=2, motion=None),
                          snow(8, seed=4, speed=1)], "aurora"))
    S.append(Scene(60.1, [BLACK, stars(10, seed=5, ymax=12), icon("🌙", 7, 19.5, 5, enter="fade", motion=None),
                          snow(14, seed=6, speed=1.2), ground(20, snowy=True),
                          icon("⛄", 14, 10, 13, enter="fade", enter_s=2.0, motion="bob", amp=0.5)], "snowman"))
    S.append(flake_scene(80.0, 7))
    return S
