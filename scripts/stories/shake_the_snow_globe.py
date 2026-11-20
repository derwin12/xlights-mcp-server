"""Storybook for 'Shake The Snow Globe' (Gwen Stefani) on a 30x40 matrix. Used by scripts/matrix_storybook.py.

The story follows the lyrics: a snowless yard, tangled tinsel, the tree on the car, Mrs Claus getting her applause,
the snow globe shaken on every SHAKE, cinnamon rolls and spiked cocoa, the mall Santa, and a merry finale.
"""

from matrix_storybook import (Scene, cinnamon_roll, confetti, dim, ease, fireworks, glow, ground, icon, keyframes,
                              mistletoe, pour, rising, road, siren, sky, snow, snow_globe, sparkles, spotlight,
                              stars, steam, sung_words, text, tinsel, tree_lights)

NIGHT = sky((0, 0, 14), (6, 8, 34))
WARM = sky((18, 6, 2), (40, 14, 4))


def globe_scene(tm, start, n_first, cut=False, inside=None):
    """Snow globe shaken on SHAKE, SHAKE, SHAKE (the n_first-th SHAKE and the two after it)."""
    hits = [tm.w(f"SHAKE#{n_first + i}") for i in range(3)]
    inside = inside or [("🏠", 9, -2.5, 4.5), ("🎄", 7, 5, 4)]
    return Scene(start, [NIGHT, stars(10, seed=n_first, ymax=40),
                         snow_globe(inside, hits, enter=None),
                         sung_words({"SHAKE": "SHAKE!"}, 34, (120, 220, 255))], f"globe {n_first}", cut=cut)


def ho_scene(tm, start, ho_nums):
    hits = [tm.w(f"HO#{n}") for n in ho_nums]
    return Scene(start, [WARM, sparkles(10, seed=ho_nums[0]),
                         icon("🎅", 22, 15, 17, motion="bounce", hits=hits, amp=1.3),
                         sung_words({"HO": "HO"}, 30, (255, 60, 50), scale=2)], "ho ho ho")


def cinnamon_scene(tm, start, n):
    return Scene(start, [WARM, glow(15, 21, 16, (120, 60, 10), 0.6), cinnamon_roll(15, 22, 10),
                         steam(15, 11, n=3, height=9)], f"cinnamon {n}")


def mistletoe_scene(tm, start, n):
    return Scene(start, [sky((10, 0, 8), (40, 4, 18)), mistletoe(15, 0, 9),
                         rising("❤️", n=6, seed=20 + n, size=4, speed=7),
                         icon("💋", 10, 15, 29, at=tm.w(f"MISTLETOE#{n}"), motion="pulse")], f"mistletoe {n}")


def cocoa_scene(tm, start, n):
    spike = tm.w(f"SPIKE#{n}")
    tip = lambda f: -55 * ease((f.t - spike) / 0.4)  # noqa: E731
    return Scene(start, [WARM, glow(13, 28, 14, (120, 60, 10), 0.5),
                         icon("☕", 16, 12, 29, enter="rise"),
                         steam(11, 21, n=2, height=7),
                         icon("🥃", 11, 22, 10, at=spike, enter="right", rot=tip),
                         pour(18, 13, 13, 22, at=spike + 0.4)], f"cocoa {n}")


def alone_scene(tm, start, n):
    return Scene(start, [NIGHT, stars(16, seed=40 + n), icon("🌙", 7, 24, 6, enter="fade", enter_s=1.0),
                         ground(33, snowy=True), snow(30, seed=n, speed=3),
                         icon("⛄", 15, 10, 26, enter="fade", enter_s=1.2, motion="bob", amp=0.4),
                         icon("💭", 9, 21, 15, at=tm.w(f"ALONE#{n}"), enter="pop"),
                         icon("❤️", 3.5, 22, 14.5, at=tm.w(f"ALONE#{n}") + 0.3, motion="pulse")], f"alone {n}")


def forget_scene(tm, start, n, em="💌"):
    return Scene(start, [sky((10, 0, 10), (36, 6, 28)), rising("❤️", n=5, seed=30 + n, size=3.5, speed=6),
                         icon(em, 18, 15, 19, motion="bob", enter="grow")], f"forget {n}")


def home_scene(tm, start, n):
    home = tm.w(f"HOME#{n}")
    return Scene(start, [NIGHT, stars(14, seed=50 + n, ymax=18), ground(31, snowy=True),
                         snow(26, seed=60 + n, speed=2.5),
                         glow(15, 22, 13, (255, 170, 60), lambda f: 0.25 + 0.3 * ease((f.t - home) / 0.6)),
                         icon("🏠", 19, 15, 22, enter="rise"),
                         steam(18.5, 11, n=1, height=6, color=(140, 140, 150)),
                         icon("❤️", 7, 15, 7, at=home, motion="pulse")], f"home {n}")


def merry_scene(tm, start, layers, name):
    words = {"MERRY": "MERRY", "VERY": "VERY", "CHRISTMAS": "CHRIST/MAS"}
    colors = {"MERRY": (255, 50, 50), "VERY": (60, 230, 80), "CHRISTMAS": (255, 210, 40)}
    return Scene(start, layers + [sung_words(words, 28, colors=colors, hold=0.9)], name)


def build(tm):
    w = tm.w
    beats = tm.beats
    S = []

    # ---- intro: a quiet night, a snowless yard, the title
    S.append(Scene(0.0, [NIGHT, stars(22, seed=1, ymax=30),
                         icon("🌙", 8, 23, 7, enter="fade", enter_s=2.0),
                         ground(33), icon("🏠", 16, 13, 25, at=3.0, enter="rise", enter_s=1.2),
                         text("SHAKE THE SNOW GLOBE", 1, (120, 220, 255), at=6.0, scroll=9.0)], "night"))
    S.append(Scene(13.3, [NIGHT, stars(10, seed=2, ymax=40),
                          snow_globe([("🏠", 9, -2.5, 4.5), ("🎄", 7, 5, 4)], tm.beats_in(15.4, 19.8))],
                   "globe intro"))

    # ---- verse 1
    S.append(Scene(w("LAWN"), [sky((40, 80, 160), (110, 160, 220)), icon("☀️", 7, 24, 6, enter="fade"),
                               ground(31), icon("🏠", 14, 10, 24, enter=None),
                               icon("🌲", 9, 23, 26, enter="rise")], "lawn"))
    S.append(Scene(w("DECEMBER'S"), [NIGHT, icon("🎄", 26, 15, 21, enter=None, motion="wobble", amp=0.6),
                                      tinsel((5, 9, 25, 33))], "tinsel"))
    car_x = lambda f: keyframes([(w("TIE"), -12), (w("TIE") + 1.2, 15), (w("GOT#2") - 0.3, 15),  # noqa: E731
                                 (w("GOT#2"), 42)], f.t)
    S.append(Scene(w("TIE"), [sky((0, 0, 20), (20, 20, 50)), stars(10, seed=3, ymax=20), road(33),
                              icon("🌲", 11, lambda f: car_x(f) + 0.5, 21, enter=None, rot=88, motion="bob",
                                   amp=0.4),
                              icon("🚗", 16, car_x, 28, enter=None, flip=True, motion="bob", amp=0.4)], "car"))
    S.append(Scene(w("GOT#2"), [sky((40, 80, 160), (110, 160, 220)), ground(32),
                                icon("☁️", 13, 15, 6, motion="shake", hits=[w("NO#1"), w("SNOW#1")]),
                                icon("👼", 13, 15, 23, at=w("ANGEL"), enter="fade", alpha=0.75, motion="bob")],
                   "no snow"))
    S.append(Scene(w("THIS"), [sky((10, 4, 30), (30, 10, 50)), icon("🤔", 15, 10, 30, enter="rise"),
                               icon("💭", 17, 18, 13, at=w("SEASON'S") + 0.2, enter="pop"),
                               icon("🤶", 9, 18, 12.5, at=w("THINKING"), enter="pop")], "thinking"))
    S.append(Scene(w("MRS"), [sky((30, 0, 10), (60, 0, 20)), sparkles(14, seed=4),
                              icon("🤶", 24, 15, 20, enter="grow", motion="bob")], "mrs claus"))
    S.append(Scene(w("WHY"), [sky((30, 20, 0), (50, 30, 0)), icon("🎅", 16, 10, 27, enter="left"),
                              icon("🏆", 12, 21, 11, at=w("CREDIT"), enter="drop", motion="bob"),
                              sparkles(8, seed=5, box=(14, 3, 28, 20))], "credit"))
    S.append(Scene(w("CAN"), [spotlight(15), icon("🤶", 20, 15, 25, enter="fade", motion="bob", amp=0.5)],
                   "spotlight"))
    claps = tm.beats_in(w("ROUND") - 0.1, w("SOOO"))
    S.append(Scene(w("ROUND"), [spotlight(15, strength=0.25), confetti(36, seed=6),
                                icon("🤶", 18, 15, 25, enter=None, motion="bounce", hits=claps, amp=0.5),
                                icon("👏", 11, 6, 12, motion="pulse", hits=claps, amp=2),
                                icon("👏", 11, 24, 12, motion="pulse", hits=claps, amp=2, flip=True)], "applause"))

    # ---- chorus 1
    S.append(Scene(w("SOOO"), [NIGHT, stars(10, seed=7, ymax=40),
                               snow_globe([("🏠", 9, -2.5, 4.5), ("🎄", 7, 5, 4)], [], enter="pop")], "globe in"))
    S.append(globe_scene(tm, w("SHAKE#1") - 0.05, 1, cut=True))
    S.append(cinnamon_scene(tm, w("CINNAMON#1") - 0.2, 1))
    S.append(ho_scene(tm, w("HO#1") - 0.1, [1, 2, 3]))
    S.append(mistletoe_scene(tm, w("I'LL#1") - 0.1, 1))
    S.append(globe_scene(tm, w("SHAKE#4") - 0.05, 4, cut=True))
    S.append(cocoa_scene(tm, w("SPIKE#1") - 0.25, 1))
    S.append(Scene(w("OOOH#1"), [NIGHT, stars(16, seed=8, ymax=40),
                                 snow_globe([("🏠", 9, -2.5, 4.5), ("🎄", 7, 5, 4)], [w("HO#4")], enter=None),
                                 sparkles(10, seed=9)], "ooh"))
    S.append(alone_scene(tm, w("CAUSE#1") - 0.1, 1))
    S.append(forget_scene(tm, w("NO#2") - 0.1, 1))
    S.append(ho_scene(tm, w("HO#5") - 0.1, [5, 6]))
    S.append(home_scene(tm, w("THERE'S#1") - 0.1, 1))
    S.append(forget_scene(tm, w("NO#4") - 0.1, 2, em="🎁"))

    # ---- instrumental break: the globe on every beat, then it settles
    brk = w("ME#3") + 0.4
    S.append(Scene(brk, [NIGHT, stars(16, seed=10, ymax=40),
                         snow_globe([("🎅", 9, -3, 4), ("🦌", 8, 4.5, 4.5)],
                                    [b for i, b in enumerate(tm.beats_in(brk, w("ON#2") - 1.5)) if i % 2 == 0],
                                    enter="pop")], "break"))

    # ---- verse 2: the mall Santa
    S.append(Scene(w("ON#2") - 0.1, [sky((40, 10, 40), (80, 20, 60)), sparkles(10, seed=11),
                                     icon("🎅", 20, 15, 18, enter="grow", motion="bob"),
                                     icon("🛍️", 9, 5, 32, at=w("MALL"), enter="left"),
                                     icon("🛍️", 9, 25, 32, at=w("MALL") + 0.15, enter="right")], "mall"))
    S.append(Scene(w("TALK"), [sky((10, 20, 30), (20, 40, 50)), icon("🛋️", 18, 15, 31, enter="rise"),
                               icon("🎅", 12, 9, 22, enter=None),
                               icon("💬", 12, 21, 10, at=w("THERAPIST"), enter="pop", motion="bob")],
                   "therapist"))
    S.append(Scene(w("RING"), [WARM, glow(15, 18, 14, (200, 150, 20), 0.45),
                               icon("🔔", 20, 15, 18, enter="drop", motion="swing", amp=1.2, pivot_top=True)],
                   "bell", cut=True))
    S.append(Scene(w("SECURITY"), [siren(4.0), dim(0.35), icon("🚨", 18, 15, 20, enter="pop", motion="pulse",
                                                                 hits=[w("SECURITY"), w("CALLS")])],
                   "security", cut=True))
    S.append(Scene(w("TELLING"), [sky((25, 0, 0), (50, 5, 5)), icon("📜", 20, 15, 22, enter="drop"),
                                  icon("😈", 9, 23, 9, at=w("NAUGHTY"), enter="pop", motion="shake",
                                       hits=[w("NAUGHTY"), w("LIST")])], "naughty list"))
    S.append(Scene(w("NO#5"), [sky((20, 30, 60), (60, 80, 120)), glow(15, 18, 15, (255, 240, 180), 0.4),
                               icon("😇", 20, 15, 19, enter="grow", motion="bob"),
                               sung_words({"NO": "NO", "NOT": "NOT!"}, 33, (255, 255, 255))], "not naughty"))

    # ---- chorus 2
    S.append(globe_scene(tm, w("SHAKE#7") - 0.05, 7, cut=True))
    S.append(cinnamon_scene(tm, w("CINNAMON#2") - 0.2, 2))
    S.append(ho_scene(tm, w("HO#7") - 0.1, [7, 8, 9]))
    S.append(mistletoe_scene(tm, w("I'LL#2") - 0.6, 2))
    S.append(globe_scene(tm, w("SHAKE#10") - 0.05, 10, cut=True))
    S.append(cocoa_scene(tm, w("SPIKE#2") - 0.25, 2))
    S.append(Scene(w("OOOH#2"), [NIGHT, stars(16, seed=12, ymax=40),
                                 snow_globe([("🏠", 9, -2.5, 4.5), ("🎄", 7, 5, 4)], [w("HO#10")], enter=None),
                                 sparkles(10, seed=13)], "ooh 2"))
    S.append(alone_scene(tm, w("CAUSE#2") - 0.1, 2))
    S.append(forget_scene(tm, w("NO#6") - 0.1, 3))
    S.append(ho_scene(tm, w("HO#11") - 0.1, [11, 12]))
    S.append(home_scene(tm, w("THERE'S#2") - 0.1, 2))
    S.append(forget_scene(tm, w("NO#8") - 0.1, 4, em="🎁"))

    # ---- merry merry very very very merry Christmas, four times
    m = [w("MERRY#1"), w("MERRY#4"), w("MERRY#7"), w("MERRY#10")]
    merry_hits = lambda a, b: [s for lab, s, _e in tm.words if lab in ("MERRY", "VERY", "CHRISTMAS")  # noqa: E731
                               and a <= s < b]
    S.append(merry_scene(tm, m[0] - 0.1, [NIGHT, stars(12, seed=14, ymax=10),
                                          icon("🎄", 25, 15, 14, enter="grow"),
                                          tree_lights((3, 3, 27, 26), 18, hits=merry_hits(m[0], m[1])),
                                          icon("⭐", 6, 15, 2.5, motion="pulse", hits=merry_hits(m[0], m[1]))],
                         "merry tree"))
    gifts = merry_hits(m[1], m[2])
    S.append(merry_scene(tm, m[1] - 0.1, [WARM,
                                          icon("🎁", 10, 8, 20, at=gifts[0], enter="drop"),
                                          icon("🎁", 10, 22, 20, at=gifts[1], enter="drop"),
                                          icon("🎁", 9, 15, 11, at=gifts[2], enter="drop"),
                                          icon("🎁", 8, 6, 9, at=gifts[3], enter="drop", flip=True),
                                          icon("🎁", 8, 24, 9, at=gifts[4], enter="drop", flip=True),
                                          icon("🎀", 8, 15, 3, at=gifts[5], enter="pop", motion="pulse",
                                               hits=gifts),
                                          sparkles(10, seed=15, box=(0, 0, 30, 25))], "merry gifts"))
    sleigh_x = lambda f: keyframes([(m[2], 38), (m[3] - 0.5, -14)], f.t, smooth=False)  # noqa: E731
    S.append(merry_scene(tm, m[2] - 0.1, [NIGHT, stars(24, seed=16, ymax=40),
                                          icon("🌕", 18, 15, 12, enter="fade", enter_s=1.0),
                                          icon("🦌", 8, lambda f: sleigh_x(f) - 4,
                                               lambda f: 14 + (sleigh_x(f) - 15) * 0.25, enter=None, flip=True,
                                               motion="bob", amp=0.8),
                                          icon("🛷", 9, lambda f: sleigh_x(f) + 5,
                                               lambda f: 16 + (sleigh_x(f) - 15) * 0.25, enter=None, flip=True,
                                               motion="bob", amp=0.8)], "merry sleigh"))
    S.append(merry_scene(tm, m[3] - 0.1, [NIGHT, fireworks(merry_hits(m[3], m[3] + 6), seed=17),
                                          icon("🎄", 16, 15, 16, enter="grow"),
                                          tree_lights((7, 8, 23, 24), 12, seed=18,
                                                      hits=merry_hits(m[3], m[3] + 6))], "merry fireworks"))

    # ---- outro: shake it one last time, let it snow, fade out
    out = w("CHRISTMAS#8") + 1.6
    end = tm.duration
    fade = lambda f: ease((f.t - (end - 3.0)) / 3.0)  # noqa: E731
    S.append(Scene(out, [NIGHT, stars(14, seed=19, ymax=40),
                         snow_globe([("🏠", 9, -2.5, 4.5), ("🎄", 7, 5, 4)],
                                    [b for i, b in enumerate(tm.beats_in(out, out + 9)) if i % 4 == 0], enter="pop"),
                         text("MERRY CHRISTMAS", 33, (255, 60, 50), at=out + 6, scroll=8.0),
                         dim(fade)], "outro"))
    return S
