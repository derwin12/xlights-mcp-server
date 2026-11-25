"""Storybook for 'Let It Go - Trap Mix' on the 25x24 mini matrices, ShowFolder3D.

    python matrix_storybook.py stories/let_it_go_trap_mini.py \
        "E:/2023/ShowFolder3D/Frozen - Let it go - Trap Mix.xsq" OUT.mp4 \
        --size 25x24 --k 1 --ss 4 --scale 20 --flat --fps 40 --jobs 10

Instrumental trap remix: the only sung words are "let it go" at ~146.5 s (faster-whisper), shown as LET IT / GO!.
Sections from the loudness: quiet build from 30.5, drops at 58.0, 100.0 and 142.0, breaks from 86.3 and 113.8.
An ice-and-snow world (no film characters): a spinning snowflake, an ice palace under the northern lights, a snowman,
a crown, ice blocks; each drop is a white flash with snowflakes bursting out on the beats.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from minis_common import BLACK, BOX, ICE, WHITE, aurora, flash, rays, snap, spin  # noqa: E402
from matrix_storybook import Scene, glow, ground, icon, snow, sparkles, stars, text  # noqa: E402

FLAKE = "❄️"
ICY = ((140, 210, 255), (255, 255, 255), (90, 160, 255))


def burst(tm, t0, t1, seed):
    """Snowflakes shooting out from the centre on every other beat."""
    hits = tm.beats_in(t0, t1)[::2]
    layers = []
    for k, h in enumerate(hits):
        a = (k * 2.4 + seed) % (2 * math.pi)
        layers.append(icon(FLAKE, 5, (lambda a, h: lambda f: 12.5 + math.cos(a) * (7 + (f.t - h) * 12))(a, h),
                           (lambda a, h: lambda f: 12.5 + math.sin(a) * (7 + (f.t - h) * 12))(a, h),
                           at=h, until=h + 1.0, enter=None, exit_s=0.3))
    return layers


def drop(tm, t0, t1, hero, seed):
    beats = tm.beats_in(t0, t1)
    return Scene(t0, [BLACK, rays(12.5, 12.5, n=8, colors=ICY, hits=beats, strength=0.35, spin=0.8),
                      *burst(tm, t0, t1, seed),
                      icon(hero, 15, 12.5, 12.5, enter="grow", motion="pulse", hits=beats, amp=0.8),
                      flash([t0], strength=0.8)], f"drop {hero}", cut=True)


def build(tm):
    d1, d2, d3 = snap(tm, 58.0), snap(tm, 100.0), snap(tm, 142.0)
    b1, b2, b3 = snap(tm, 30.5), snap(tm, 86.3), snap(tm, 113.8)
    S = []
    # ---- opening (beat in from ~2 s): a snowflake spins up, then the ice palace under the northern lights
    S.append(Scene(0.0, [BLACK, snow(12, seed=1, speed=2),
                         icon(FLAKE, 17, 12.5, 12.5, at=1.0, enter="grow", enter_s=1.5, rot=spin(30),
                              motion="pulse", hits=tm.beats_in(1, 15)[::2])], "flake"))
    t = snap(tm, 15.0)
    S.append(Scene(t, [BLACK, stars(10, seed=2, ymax=10), aurora(ICY, y=3, strength=0.5), ground(20, snowy=True),
                       icon("🏰", 15, 12.5, 13, enter="rise", enter_s=1.0, motion=None),
                       sparkles(6, seed=3, box=(3, 5, 22, 19))], "palace"))
    # ---- quiet build: a snowman in the snow, then a crown glowing brighter toward the drop
    S.append(Scene(b1, [BLACK, stars(8, seed=4, ymax=12), snow(14, seed=5, speed=1.5), ground(20, snowy=True),
                        icon("⛄", 15, 12.5, 12.5, enter="fade", enter_s=1.5, motion="bob")], "snowman"))
    t = snap(tm, 44.0)
    S.append(Scene(t, [BLACK, glow(12.5, 12.5, 11, ICE, lambda f: 0.1 + 0.5 * min(1, (f.t - t) / (d1 - t))),
                       sparkles(10, seed=6, box=BOX, rate=3),
                       icon("👑", 14, 12.5, 12.5, enter="fade", enter_s=1.5, motion="pulse",
                            hits=tm.beats_in(t, d1)[::2])], "crown"))
    # ---- drop 1
    S.append(drop(tm, d1, snap(tm, 71.0), "⛄", 1))
    t = snap(tm, 71.0)
    beats = tm.beats_in(t, b2)
    S.append(Scene(t, [BLACK, snow(16, seed=7, speed=4, wind=2),
                       icon("🧊", 10, 7, 9, enter="drop", motion="bounce", hits=beats[0::2]),
                       icon("🧊", 10, 18, 16, enter="drop", enter_s=0.6, motion="bounce", hits=beats[1::2]),
                       icon(FLAKE, 7, 18, 6, enter="pop", rot=spin(90)),
                       icon(FLAKE, 7, 7, 19, enter="pop", rot=spin(-90))], "ice blocks", cut=True))
    # ---- break: northern lights over the pines
    S.append(Scene(b2, [BLACK, stars(14, seed=8, ymax=12), aurora(y=4, strength=0.6), ground(21, snowy=True),
                        icon("🌲", 10, 5, 15, enter="fade", motion=None), icon("🌲", 12, 12.5, 14, enter="fade",
                                                                              motion=None),
                        icon("🌲", 10, 20, 15, enter="fade", motion=None), snow(8, seed=9, speed=1)], "aurora"))
    # ---- drop 2
    S.append(drop(tm, d2, b3, "🏰", 2))
    # ---- quiet again: the moon over the snowman, then a snowflake growing toward the last drop
    S.append(Scene(b3, [BLACK, stars(10, seed=10, ymax=12), icon("🌙", 7, 19, 5, enter="fade", motion=None),
                        snow(12, seed=11, speed=1.5), ground(20, snowy=True),
                        icon("⛄", 13, 10, 13.5, enter="fade", enter_s=1.5, motion="bob")], "moon"))
    t = snap(tm, 128.0)
    S.append(Scene(t, [BLACK, sparkles(10, seed=12, box=BOX, rate=3),
                       icon(FLAKE, lambda f: 6 + 12 * min(1, (f.t - t) / (d3 - t)), 12.5, 12.5, enter=None,
                            rot=spin(60))], "flake grows"))
    # ---- drop 3 and the words: LET IT ... GO!
    let, go = 146.5, 147.9
    s3 = drop(tm, d3, snap(tm, 156.0), FLAKE, 3)
    s3.layers += [text("LET IT", 1, WHITE, at=let, until=go), text("GO!", 1, ICE, at=go, until=go + 2.5),
                  flash([go], color=ICE, strength=0.6)]
    S.append(s3)
    t = snap(tm, 156.0)
    S.append(Scene(t, [BLACK, rays(12.5, 12.5, n=8, colors=ICY, hits=tm.beats_in(t, 170), strength=0.3),
                       *burst(tm, t, 168.5, 4), stars(8, seed=13),
                       icon("👑", 14, 12.5, 12.5, enter="pop", motion="pulse", hits=tm.beats_in(t, 170))],
                   "crown finale", cut=True))
    S.append(Scene(169.5, [BLACK, snow(10, seed=14, speed=1),
                           icon(FLAKE, 12, 12.5, 12.5, enter="fade", rot=spin(15),
                                alpha=lambda f: max(0, 1 - (f.t - 169.5) / 2.5))], "end"))
    return S
