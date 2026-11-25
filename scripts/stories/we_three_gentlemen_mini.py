"""Storybook for 'We Three Gentlemen' (Lindsey Stirling) on the 25x24 mini matrices, ShowFolder3D.

    python matrix_storybook.py stories/we_three_gentlemen_mini.py \
        "E:/2023/ShowFolder3D/We Three Gentlemen - Lindsey Stirling.xsq" OUT.mp4 \
        --size 25x24 --k 1 --ss 4 --scale 20 --flat --fps 40 --jobs 10

Instrumental violin medley of 'We Three Kings' and 'God Rest Ye Merry Gentlemen'. Scene changes on the sequence's
"New Timing" section marks (0.6, 29.2, 38.6, 48, 54.2, 57.5, 59.9, 74, 76.3, 97.5, 99.8, 111.7, 128.1, 138.9) and the
loudness (quiet outro from ~152.5). The star rises, the violin plays, three kings arrive one per bar, camels follow
the star, three gifts, then carol bells for the merry gentlemen, the stable under the star, fireworks.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from minis_common import BLACK, BOX, GOLD, SHOW, flash, flyer, rays, snap, track  # noqa: E402
from matrix_storybook import (Scene, confetti, fireworks, glow, ground, icon, rising, snow, sparkles, stars)  # noqa: E402

XSQ = SHOW / "We Three Gentlemen - Lindsey Stirling.xsq"
SAND = (150, 105, 50)
WARM = (GOLD, (255, 140, 40), (255, 240, 180))


def star_sky(y=4, size=7, strength=0.45):
    return [stars(12, seed=y, ymax=14), glow(12.5, y, 7, GOLD, strength),
            icon("⭐", size, 12.5, y, enter="fade", motion="pulse")]


def hats(hb):
    """'God rest ye merry gentlemen': three carol bells swinging in turn, with music notes rising."""
    out = [rising("🎶", n=4, seed=31, size=4, box=(2, 23), speed=5)]
    for k, x in enumerate((4.5, 12.5, 20.5)):
        out.append(icon("🔔", 8, x, 13, enter="drop", enter_s=0.3 + 0.2 * k, motion="bounce", hits=hb[k % 3::3]))
    return out


def build(tm):
    M = [s for _l, s, _e in track(XSQ, "New Timing")]
    bars = tm.bars or tm.beats[::3]
    S = []
    # ---- intro (quiet violin): the star rises over the desert, then the violin
    S.append(Scene(0.0, [BLACK, stars(14, seed=1, ymax=16), ground(20, SAND, hill=0.8),
                         glow(12.5, lambda f: 18 - min(14, f.t * 1.0), 8, GOLD, 0.4),
                         icon("⭐", 8, 12.5, lambda f: 18 - min(14, f.t * 1.0), at=0.6, enter="fade", enter_s=3,
                              motion="pulse", hits=bars)], "star rises"))
    S.append(Scene(snap(tm, 14.5), [BLACK, sparkles(8, seed=2, box=BOX),
                                    icon("🎻", 16, 12.5, 12.5, enter="fade", enter_s=1.5, motion="swing", amp=0.5)],
                   "violin"))
    # ---- 29.2: three kings, one per bar
    kb = [b for b in bars if b >= M[2] - 0.05][:3]
    S.append(Scene(M[2], [BLACK, *star_sky(4, 6), ground(21, SAND, hill=0.6)] +
                   [icon("👑", 8, x, 14, at=b, enter="drop", motion="bounce", hits=tm.beats_in(b, M[3])[::3])
                    for x, b in zip((4.5, 12.5, 20.5), kb)], "three kings", cut=True))
    # ---- 38.6: camels follow the star
    S.append(Scene(M[3], [BLACK, *star_sky(4, 6, 0.35), ground(20, SAND, hill=0.6),
                          flyer("🐪", 10, 15, M[3], M[4], x0=30, x1=-8, motion="bounce", hits=tm.beats_in(M[3], M[4])[::3]),
                          flyer("🐪", 9, 15.5, M[3] + 2.5, M[4] + 2.5, x0=30, x1=-8, motion="bounce",
                                hits=tm.beats_in(M[3], M[4])[1::3])], "camels"))
    # ---- 48: the three gifts
    gb = [b for b in bars if b >= M[4] - 0.05][:3]
    S.append(Scene(M[4], [BLACK, sparkles(8, seed=3, box=BOX)] +
                   [icon(e, 8, x, 12.5, at=b, enter="pop", motion="pulse", hits=tm.beats_in(b, M[5])[::3])
                    for e, x, b in zip(("🪙", "🏺", "🎁"), (4.5, 12.5, 20.5), gb)], "gifts", cut=True))
    # ---- 54.2: the star brightens toward the big entrance
    S.append(Scene(M[5], [BLACK, stars(16, seed=4),
                          glow(12.5, 12, 12, GOLD, lambda f: 0.2 + 0.5 * min(1, (f.t - M[5]) / (M[7] - M[5]))),
                          icon("⭐", lambda f: 8 + 8 * min(1, (f.t - M[5]) / (M[7] - M[5])), 12.5, 12, enter=None,
                               motion="pulse", hits=tm.beats_in(M[5], M[7]))], "star swells"))
    # ---- 59.9: God rest ye merry gentlemen - three carol bells
    hb = tm.beats_in(M[7], M[8])
    S.append(Scene(M[7], [BLACK, rays(12.5, 3, n=8, colors=WARM, hits=hb, strength=0.25)] +
                   hats(hb) + [flash([M[7]], color=GOLD, strength=0.6)],
                   "gentlemen", cut=True))
    # ---- 74/76.3: the violin solo
    vb = tm.beats_in(M[9], M[10])
    S.append(Scene(M[8], [BLACK, rays(12.5, 12.5, n=10, colors=WARM, hits=vb, strength=0.3),
                          icon("🎻", 17, 12.5, 12.5, enter="grow", motion="swing", amp=0.6)], "violin solo"))
    S.append(Scene(snap(tm, 87.0), [BLACK, *star_sky(4, 6), ground(21, SAND, hill=0.6),
                                    flyer("👑", 7, 13, snap(tm, 87.0), M[10], x0=30, x1=-6, motion="bounce", hits=vb),
                                    flyer("🐪", 10, 16, snap(tm, 87.0) + 1, M[10] + 1, x0=34, x1=-4, motion="bounce",
                                          hits=vb)], "kings travel"))
    # ---- 99.8: the stable under the star
    S.append(Scene(M[10], [BLACK, *star_sky(4, 7, 0.5), ground(21, SAND, hill=0.6),
                           icon("🛖", 13, 12.5, 15, enter="fade", enter_s=1.5, motion=None),
                           sparkles(5, seed=5, box=(4, 8, 21, 18))], "stable"))
    # ---- 111.7: the kings arrive, rising to the 117 lift
    ab = tm.beats_in(M[12], M[13])
    S.append(Scene(M[12], [BLACK, *star_sky(3, 5, 0.4), ground(21, SAND, hill=0.6),
                           icon("🛖", 10, 12.5, 15.5, enter=None, motion=None)] +
                   [icon("👑", 5, x, 19, enter="pop", enter_s=0.4, motion="bounce", hits=ab[k::3])
                    for k, x in enumerate((3, 22))] + [icon("🐪", 7, 21, 16, at=snap(tm, 117.25), enter="right")],
                   "arrival"))
    # ---- 128.1: the gentlemen again, with confetti
    hb = tm.beats_in(M[13], M[14])
    S.append(Scene(M[13], [BLACK, confetti(20, seed=6), rays(12.5, 3, n=8, colors=WARM, hits=hb, strength=0.25)] +
                   hats(hb), "gentlemen 2", cut=True))
    # ---- 138.9: finale fireworks around the star
    fb = tm.beats_in(M[14], 152.5)
    S.append(Scene(M[14], [BLACK, fireworks(fb[::3], seed=7), stars(10, seed=8),
                           icon("⭐", 14, 12.5, 12.5, enter="grow", motion="pulse", hits=fb), flash([M[14]], GOLD)],
                   "finale", cut=True))
    # ---- 152.5: quiet outro - the stable in the snow under the star, fading
    out = snap(tm, 152.5)
    S.append(Scene(out, [BLACK, *star_sky(4, 7, 0.5), snow(10, seed=9, speed=1), ground(21, SAND, hill=0.6),
                         icon("🛖", 13, 12.5, 15, enter="fade", motion=None)], "outro"))
    return S
