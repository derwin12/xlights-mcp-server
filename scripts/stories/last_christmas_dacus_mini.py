"""Storybook for 'Last Christmas' (Lucy Dacus) on the 25x24 mini matrices, ShowFolder3D.

    python matrix_storybook.py stories/last_christmas_dacus_mini.py \
        "E:/2023/ShowFolder3D/Last Christmas - Lucy Dacus.xsq" OUT.mp4 \
        --size 25x24 --k 1 --ss 4 --scale 20 --flat --fps 40 --jobs 10

No Lyrics track in the sequence: word times from faster-whisper (stories/lyrics/last_christmas_lucy_dacus.json).
The chorus: LAST / XMAS, a heart given on "heart", flying away on "away", a tear on "tears", a gift on "special".
Verses: shy monkey, eyes, calendar, a gift sent, a love note, the fool, a kiss, ice, fire, a broken heart, a real love.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from minis_common import BLACK, BOX, ICE, RED, WHITE, big, flyer, w, words_from_json  # noqa: E402
from matrix_storybook import (Scene, glow, ground, icon, rising, snow, sparkles, stars, text,  # noqa: E402
                              tree_lights)


def moment(tm, t_from, start_word, emoji, hit_word, size=16, pre=None, bg=(), **kw):
    """Scene starting on start_word (after t_from) with the picture popping on hit_word."""
    t = w(tm, start_word, t_from)
    hit = w(tm, hit_word, t)
    layers = [BLACK, *bg]
    if pre:
        layers.append(icon(pre, size, 12.5, 12.5, enter="fade", until=hit, exit_s=0.15, motion="bob"))
        layers.append(icon(emoji, size, 12.5, 12.5, at=hit, enter="pop", **{"motion": "bob", **kw}))
    else:
        # the picture comes in with the phrase and jumps on the key word
        kw = {"motion": "pulse", "hits": [hit], "amp": 1.5, **kw}
        layers.append(icon(emoji, size, 12.5, 12.5, enter="pop", **kw))
    return Scene(t - 0.15, layers, emoji)


def chorus(tm, t):
    xmas, heart = w(tm, "christmas", t), w(tm, "heart", t)
    but, away = w(tm, "but", t), w(tm, "away", t)
    this, tears = w(tm, "this", t), w(tm, "tears", t)
    give, special = w(tm, "i'll", t), w(tm, "special", t)
    return [
        Scene(t - 0.15, [BLACK, snow(10, seed=31, speed=2),
                         text("LAST", 2, WHITE, until=xmas), text("XMAS", 2, RED, at=xmas),
                         icon("🎁", 11, 12.5, 15, at=xmas, enter="pop", until=heart, exit_s=0.1),
                         glow(12.5, 15, 8, (255, 60, 60), lambda f: 0.4 if f.t >= heart else 0),
                         icon("❤️", 12, 12.5, 15, at=heart, enter="pop", motion="pulse")], "last christmas"),
        Scene(but - 0.15, [BLACK, stars(10, seed=32),
                           icon("❤️", 12, 12.5, 12.5, enter=None, until=away, exit_s=0.05, motion="pulse"),
                           flyer("❤️", 10, 12.5, away, away + 1.2, x0=12.5, x1=34, arc=-8)], "gave it away"),
        Scene(this - 0.15, [BLACK, rising("💧", n=4, seed=33, size=3, box=(2, 23), speed=-4, at=tears),
                            icon("😢", 16, 12.5, 12.5, enter="fade", motion="pulse", hits=[tears])], "tears"),
        Scene(give - 0.15, [BLACK, sparkles(8, seed=34, box=BOX),
                            icon("🎁", 13, 12.5, 12.5, enter="pop", until=special, exit_s=0.1),
                            icon("💝", 15, 12.5, 12.5, at=special, enter="grow", motion="pulse",
                                 hits=tm.beats_in(special, special + 4))], "someone special"),
    ]


def build(tm):
    words_from_json(tm, "last_christmas_lucy_dacus")
    S = []
    # ---- intro (music only): a quiet snowy night with the tree, then a present waiting under it
    S.append(Scene(0.0, [BLACK, stars(12, seed=1, ymax=16), snow(12, seed=2, speed=1.5), ground(21, snowy=True),
                         icon("🎄", 15, 12.5, 12.5, at=0.5, enter="fade", enter_s=3.0, motion=None),
                         tree_lights((5, 5, 20, 20), 7, seed=3)], "intro tree"))
    S.append(Scene(16.0, [BLACK, stars(8, seed=4, ymax=12), snow(10, seed=5, speed=1.5), ground(20, snowy=True),
                          icon("🎁", 13, 12.5, 13, enter="drop", motion="pulse",
                               hits=tm.beats_in(16, 31)[::4])], "intro gift"))

    # ---- verse 1
    S.append(moment(tm, 31, "once", "🙈", "shy", bg=[snow(6, seed=6, speed=1.5)]))
    S.append(moment(tm, 35, "but", "👀", "eye"))
    S.append(moment(tm, 37.5, "tell", "🤔", "recognize", motion="wobble"))
    S.append(moment(tm, 40, "well", "📅", "year"))
    sent = w(tm, "sent", 43)
    S.append(Scene(w(tm, "merry", 43) - 0.15, [BLACK, snow(8, seed=7, speed=2),
                                               icon("🎁", 14, 12.5, 12.5, at=w(tm, "wrapped", 43), enter="pop",
                                                    until=sent + 0.05, exit_s=0.05),
                                               flyer("🎁", 10, 12.5, sent, sent + 0.8, x0=12.5, x1=34, arc=-6)],
                   "wrapped and sent"))
    love = w(tm, "love", 46)
    S.append(Scene(w(tm, "with", 46) - 0.15, [BLACK, sparkles(6, seed=8, box=BOX),
                                              icon("💌", 14, 12.5, 14, enter="pop", motion="pulse", hits=[w(tm, "note", 46)]),
                                              text("LOVE", 1, RED, at=love)], "note"))
    S.append(moment(tm, 49, "now", "🤡", "fool", motion="wobble"))
    S.append(Scene(w(tm, "but", 51.8) - 0.15, [BLACK,
                                               icon("💋", 15, 12.5, 12.5, enter="pop",
                                                    until=w(tm, "fool", 53.5), exit_s=0.1, motion="pulse"),
                                               icon("🤡", 16, 12.5, 12.5, at=w(tm, "fool", 53.5), enter="pop",
                                                    motion="wobble")], "kiss / fool again"))

    S += chorus(tm, w(tm, "last", 55))
    S += chorus(tm, w(tm, "last", 67))

    # ---- verse 2
    S.append(Scene(w(tm, "a", 79) - 0.15, [BLACK, sparkles(4, seed=9, box=BOX),
                                           icon("🥱", 16, 12.5, 12.5, enter="pop", motion="pulse", hits=[w(tm, "tired", 79)])],
                   "tired eyes"))
    S.append(moment(tm, 82, "i'm", "🧊", "ice", bg=[snow(10, seed=10, speed=1.5)]))
    S.append(Scene(w(tm, "my", 85) - 0.15, [BLACK, stars(6, seed=11),
                                            icon("🤝", 15, 12.5, 12.5, enter="fade", until=w(tm, "cry", 88),
                                                 exit_s=0.15),
                                            icon("😭", 16, 12.5, 12.5, at=w(tm, "cry", 88), enter="pop"),
                                            rising("💧", n=4, seed=12, size=3, box=(2, 23), speed=-4,
                                                   at=w(tm, "cry", 88))], "shoulder to cry on"))
    S.append(moment(tm, 91, "my", "🔥", "fire", motion="pulse", bg=[glow(12.5, 14, 10, (255, 120, 20), 0.35)]))
    apart = w(tm, "apart", 94)
    S.append(Scene(w(tm, "a", 94) - 0.15, [BLACK,
                                           icon("🕵️", 15, 12.5, 12.5, enter="pop",
                                                until=apart - 0.1, exit_s=0.1),
                                           icon("💔", 16, 12.5, 12.5, at=apart, enter="pop", motion="shake",
                                                hits=[apart])], "tore me apart"))
    S.append(moment(tm, 97, "now", "💞", "love", motion="pulse",
                    bg=[rising("❤️", n=4, seed=13, size=3, box=(1, 24), speed=4)]))
    fool = w(tm, "fool", 100)
    S.append(Scene(w(tm, "and", 99.5) - 0.15, [BLACK, icon("🤡", 15, 12.5, 12.5, enter="pop", motion="pulse", hits=[fool]),
                                               icon("🚫", 20, 12.5, 12.5, at=fool + 0.5, enter="pop", alpha=0.85)],
                   "never fool me"))

    S += chorus(tm, w(tm, "last", 103))
    S += chorus(tm, w(tm, "last", 115))

    # ---- outro (music only, 126-162): heart on the tree, snow, then the gift and a slow fade of lights
    end = w(tm, "special", 125)
    S.append(Scene(end + 2.0, [BLACK, stars(10, seed=14, ymax=14), snow(12, seed=15, speed=1.5),
                               ground(21, snowy=True), icon("🎄", 15, 12.5, 12.5, enter="fade", motion=None),
                               tree_lights((5, 5, 20, 20), 7, seed=16, hits=tm.beats_in(end, tm.duration)[::2]),
                               icon("❤️", 5, 12.5, 3.5, at=end + 4, enter="pop", motion="pulse")], "outro tree"))
    S.append(Scene(145.0, [BLACK, stars(10, seed=17), snow(10, seed=18, speed=1.2),
                           rising("❤️", n=5, seed=19, size=3, box=(1, 24), speed=3),
                           icon("💝", 13, 12.5, 12.5, enter="fade", motion="pulse",
                                hits=tm.beats_in(145, 158)[::4])], "outro heart"))
    return S
