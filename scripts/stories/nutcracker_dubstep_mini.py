"""Storybook for 'Nutcracker Dubstep' (Trapcity) on the 25x24 mini matrices, ShowFolder3D.

    python matrix_storybook.py stories/nutcracker_dubstep_mini.py \
        "E:/2023/ShowFolder3D/Nutcracker Dubstep - Trapcity.xsq" OUT.mp4 \
        --size 25x24 --k 1 --ss 4 --scale 20 --flat --fps 40 --jobs 10

Instrumental. The sequence has no Beats track: beats are its "Arch" marks (about one per bar) split in four.
Sections from the loudness: intro to 10.75, build/hit to 34.75 (dip 18.75-21), quiet to 41.5, drop to 72.5, quiet to
79.25, drop to 98.75, end. The Nutcracker ballet in pictures: the tree grows, the toy soldier fights the Mouse King,
the mice run off, the Land of Snow, the Land of Sweets with the Sugar Plum Fairy.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from minis_common import (BLACK, BOX, GOLD, RED, SHOW, beats_from_marks, flash, flyer, rays, snap,  # noqa: E402
                          track)
import matrix_storybook as mb  # noqa: E402
from matrix_storybook import (Scene, confetti, glow, ground, icon, snow, sparkles, stars, tree_lights)  # noqa: E402
from minis_common import P  # noqa: E402
from PIL import ImageDraw  # noqa: E402

XSQ = SHOW / "Nutcracker Dubstep - Trapcity.xsq"
SOLDIER, MOUSE = "nutcracker", "🐭"
WARM = (RED, GOLD, (255, 140, 40))
SWEET = ((255, 90, 200), (255, 200, 230), (140, 220, 255), GOLD)


def nutcracker(cx, cy, h, hits=None, at=None, enter_s=0.4, motion="bounce", amp=1.0, x=None):
    """A drawn toy nutcracker, h story pixels tall, centred at (cx, cy); hops on hits (motion bounce) or
    jaw-snaps (motion pulse). x may be a callable to move it."""

    def draw(f):
        t0 = f.start if at is None else at
        if f.t < t0:
            return
        e = min(1.0, (f.t - t0) / enter_s)
        xx = mb.val(x, f) if x is not None else cx
        dy = 0.0
        jaw = 0.0
        if hits:
            sn = mb.since(hits, f.t)
            if sn is not None and sn < 0.35:
                if motion == "bounce":
                    dy = -math.sin(sn / 0.35 * math.pi) * 2.5 * amp
                else:
                    jaw = math.sin(sn / 0.35 * math.pi) * 1.2 * amp
        top = cy - h / 2 + dy + (1 - mb.back_out(e)) * 30
        wd = h * 0.42
        d = ImageDraw.Draw(f.img)

        def box(y0, y1, c, w0=wd):
            d.rectangle([P(xx - w0 / 2), P(top + h * y0), P(xx + w0 / 2), P(top + h * y1)], fill=c + (255,))
        box(0.00, 0.26, (25, 25, 35), wd * 0.9)            # busby hat
        box(0.20, 0.25, GOLD, wd * 0.9)                    # hat band
        box(0.00, 0.05, RED, wd * 0.3)                     # plume
        box(0.26, 0.44, (240, 190, 150), wd * 0.8)         # face
        d.rectangle([P(xx - wd * 0.25), P(top + h * 0.31), P(xx - wd * 0.12), P(top + h * 0.34)], fill=(0, 0, 0, 255))
        d.rectangle([P(xx + wd * 0.12), P(top + h * 0.31), P(xx + wd * 0.25), P(top + h * 0.34)], fill=(0, 0, 0, 255))
        box(0.38, 0.50 + jaw / h, (245, 245, 245), wd * 0.8)  # white beard / jaw
        d.rectangle([P(xx - wd * 0.2), P(top + h * 0.41), P(xx + wd * 0.2), P(top + h * 0.41 + 0.5 + jaw)],
                    fill=(60, 0, 0, 255))                  # mouth
        box(0.50, 0.74, (215, 25, 35))                     # red jacket
        d.line([P(xx - wd / 2), P(top + h * 0.50), P(xx + wd / 2), P(top + h * 0.74)], fill=(250, 250, 250, 255),
               width=mb.LW())
        d.line([P(xx + wd / 2), P(top + h * 0.50), P(xx - wd / 2), P(top + h * 0.74)], fill=(250, 250, 250, 255),
               width=mb.LW())
        box(0.70, 0.74, GOLD)                              # belt
        box(0.74, 0.88, (40, 70, 200), wd * 0.8)           # trousers
        d.rectangle([P(xx - 0.4), P(top + h * 0.78), P(xx + 0.4), P(top + h * 0.88)], fill=(0, 0, 0, 255))
        box(0.88, 1.00, (20, 20, 20), wd * 0.85)           # boots
    return draw


def every(tm, t0, t1, n=4):
    """Scene starts on every n-th mark between t0 and t1."""
    return [t0] + [m for m in tm.marks[::n] if t0 + 3 < m < t1 - 2]


def build(tm):
    tm.marks = [s for _l, s, _e in track(XSQ, "Arch")]
    beats_from_marks(tm, tm.marks, 4)
    hit1, dip, back = snap(tm, 10.75), snap(tm, 18.75), snap(tm, 21.0)
    q1, drop1, q2, drop2, end = snap(tm, 34.75), snap(tm, 41.5), snap(tm, 72.5), snap(tm, 79.25), snap(tm, 98.75)
    S = []
    # ---- intro: the tree with a toy soldier waiting under it
    S.append(Scene(0.0, [BLACK, stars(10, seed=1, ymax=12), ground(21, snowy=True),
                         icon("🎄", 14, 9, 12.5, at=0.3, enter="fade", enter_s=2.5, motion=None),
                         tree_lights((2, 5, 16, 19), 6, seed=2),
                         nutcracker(19.5, 15.5, 11, at=4.0)], "intro"))
    # ---- the hit: the tree grows on the beats
    S.append(Scene(hit1, [BLACK, sparkles(8, seed=3, box=BOX, rate=3),
                          icon("🎄", lambda f: min(24, 10 + (f.t - hit1) * 2.0), 12.5,
                               lambda f: 12.5 + max(0, 24 - min(24, 10 + (f.t - hit1) * 2.0)) / 2 - 0.5,
                               enter=None, motion="pulse", hits=tm.beats_in(hit1, dip)),
                          flash([hit1], color=GOLD, strength=0.6)], "tree grows", cut=True))
    S.append(Scene(dip, [BLACK, stars(10, seed=4),
                         icon(MOUSE, 11, 12.5, 14, enter="fade", enter_s=1.0, motion="bob"),
                         icon("👑", 6, 12.5, 7.5, at=dip + 1.0, enter="drop")], "mouse king"))
    # ---- battle: soldier and mouse king, crossed swords on the bars
    beats = tm.beats_in(back, q1)
    S.append(Scene(back, [BLACK, rays(12.5, 6, n=8, colors=WARM, hits=beats, strength=0.25),
                          nutcracker(6, 14.5, 15, hits=beats[0::2]),
                          icon(MOUSE, 11, 19, 16, enter="right", motion="bounce", hits=beats[1::2]),
                          icon("👑", 5, 19, 9.5, enter="right", motion="bounce", hits=beats[1::2]),
                          icon("⚔️", 8, 12.5, 6, enter="pop", motion="pulse", hits=beats[::4], amp=2)],
                   "battle", cut=True))
    # ---- quiet: the soldier stands guard in the dark
    S.append(Scene(q1, [BLACK, stars(12, seed=5), snow(8, seed=6, speed=1),
                        glow(12.5, 13, 9, GOLD, lambda f: 0.15 + 0.35 * min(1, (f.t - q1) / (drop1 - q1))),
                        nutcracker(12.5, 12.5, 20, hits=tm.beats_in(q1, drop1)[::4], motion="pulse")], "guard"))
    # ---- drop 1: the fight in pictures, changing every 4 marks
    pics = [(SOLDIER, "pulse"), ("⚔️", "shake"), (MOUSE, "chase"), (SOLDIER, "win")]
    starts = every(tm, drop1, q2)
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else q2
        em, kind = pics[i % len(pics)]
        bt = tm.beats_in(s, e)
        L = [BLACK, rays(12.5, 12.5, n=8, colors=WARM, hits=bt, strength=0.3)]
        if kind == "chase":
            L += [flyer(MOUSE, 9, 16, s, s + (e - s) / 2, x0=-6, x1=32, flip=True, motion="bounce", hits=bt),
                  nutcracker(0, 14, 13, hits=bt, at=s + 0.6, enter_s=0.01,
                             x=(lambda s, e: lambda f: -6 + 38 * min(1, (f.t - s - 0.6) / ((e - s) / 2)))(s, e)),
                  flyer(MOUSE, 9, 16, s + (e - s) / 2, e, x0=-6, x1=32, flip=True, motion="bounce", hits=bt)]
        elif kind == "win":
            L += [confetti(24, seed=7 + i), nutcracker(12.5, 12.5, 20, hits=bt)]
        else:
            L += [nutcracker(12.5, 12.5, 21, hits=bt, motion="pulse", amp=1.5) if em == SOLDIER
                  else icon(em, 16, 12.5, 12.5, enter="pop", motion=kind, hits=bt, amp=1.2)]
        if i == 0:
            L.append(flash([s], strength=0.8))
        S.append(Scene(s, L, f"drop1 {kind}", cut=True))
    # ---- quiet: the Land of Snow
    S.append(Scene(q2, [BLACK, stars(8, seed=8, ymax=10), snow(20, seed=9, speed=2.5, wind=1.5),
                        ground(21, snowy=True), icon("🌲", 10, 5, 15, enter="fade", motion=None),
                        icon("🌲", 10, 20, 15, enter="fade", motion=None),
                        icon("❄️", 10, 12.5, 9, enter="fade", motion="bob")], "land of snow"))
    # ---- drop 2: the Land of Sweets
    sweets = [("🧚", None), ("🍭", "🍬"), ("🧁", "🍭"), ("🧚", None)]
    starts = every(tm, drop2, end)
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else end
        a, b = sweets[i % len(sweets)]
        bt = tm.beats_in(s, e)
        L = [BLACK, rays(12.5, 12.5, n=8, colors=SWEET, hits=bt, strength=0.3), sparkles(10, seed=10 + i, box=BOX)]
        if b:
            L += [icon(a, 12, 7, 13, enter="left", motion="bounce", hits=bt[0::2]),
                  icon(b, 11, 18, 13, enter="right", motion="bounce", hits=bt[1::2])]
        else:
            L += [icon(a, 17, 12.5, 12.5, enter="grow", motion="pulse", hits=bt)]
        if i == 0:
            L.append(flash([s], color=(255, 150, 220), strength=0.8))
        S.append(Scene(s, L, f"sweets {i}", cut=True))
    # ---- end: the soldier back under the tree
    S.append(Scene(end, [BLACK, stars(10, seed=20, ymax=12), ground(21, snowy=True),
                         icon("🎄", 14, 9, 12.5, enter="fade", motion=None), tree_lights((2, 5, 16, 19), 6, seed=21),
                         nutcracker(19.5, 15.5, 11)], "end"))
    return S
