"""Storybook for 'I Want a Hippopotamus for Christmas' on a 48x27 grid (the Garage matrices; 16:9).

Render (96x54 pixel art blown up 5x to 480x270; black backgrounds, flat colours, words only in the title and finale):
    python scripts/matrix_storybook.py scripts/stories/hippopotamus_for_christmas.py \
        "E:/2023/ShowFolder3D/I Want a Hippopotamus for Christmas SS.xsq" OUT.mp4 \
        --size 48x27 --k 2 --ss 4 --scale 5 --flat --fps 40 --jobs 10

The story follows the lyrics: a child wishing for a hippo, no dolls or toys, playing ball with a hippo, the gift that
pops open, Santa thinking it over, no dirty chimney (through the front door), creeping down the stairs on Christmas
morning, the surprise, the hippo hero in a cape, no crocodiles or rhinos, a hippo parade, skating, Mom's warning, the
teacher's chalkboard (vegetarian!), the two-car garage, feeding / washing / massage, and a fireworks finale.
"""

import math
import random

import matrix_storybook as mb
from matrix_storybook import (Scene, confetti, dim, ease, fireworks, glow, ground, icon, keyframes, rising, since,
                              sky, snow, sparkles, spotlight, stars, steam, text, tree_lights)
from PIL import Image, ImageDraw

# Black backgrounds like a real matrix storybook: the pictures are the only lit pixels (plus sparse stars / snow).
BLACK = sky((0, 0, 0), (0, 0, 0))
NIGHT = ROOM = DAY = DAWN = WARM = BLACK
GREEN = (60, 230, 90)
RED = (255, 60, 50)
GOLD = (255, 205, 40)
WHITE = (255, 255, 255)

HIPPO = "🦛"
KID = "🧒"
NO = "🚫"


# ---------------------------------------------------------------- drawn props (in story pixels, 48x27)

def P(v):
    """Story pixels -> canvas pixels (read at draw time: SS is set from the command line)."""
    return v * mb.SS


def stairs(x0=1, y0=7, steps=7, w=3.4, h=2.3, color=(120, 70, 40), edge=(200, 140, 80)) -> mb.Layer:
    """A staircase going down to the right; returns the layer. Step i top-left = (x0 + i*w, y0 + i*h)."""

    def draw(f):
        d = ImageDraw.Draw(f.img)
        for i in range(steps):
            x, y = x0 + i * w, y0 + i * h
            d.rectangle([P(x), P(y), P(x + w), P(f.H)], fill=color + (255,))
            d.rectangle([P(x), P(y), P(x + w), P(y + 0.5)], fill=edge + (255,))
        # banister
        d.line([P(x0 + 0.5), P(y0 - 4), P(x0 + steps * w), P(y0 + steps * h - 4)], fill=(230, 190, 120, 255),
               width=mb.LW())
        for i in range(steps):
            x, y = x0 + i * w + 1.5, y0 + i * h
            d.line([P(x), P(y), P(x), P(y - 4 + 0.2)], fill=(230, 190, 120, 255), width=max(1, mb.LW() // 2))
    return draw


def stair_kid(hits, x0=1, y0=7, steps=7, w=3.4, h=2.3, size=6.5):
    """The child creeping down one step on each hit (tip-toe hop between steps)."""

    def pos(f):
        n = sum(1 for t in hits if t <= f.t)
        n = min(n, steps - 1)
        s = since(hits, f.t)
        hop = 0.0
        frac = 1.0
        if s is not None and s < 0.3 and n > 0:
            frac = ease(s / 0.3)
            hop = math.sin(frac * math.pi) * 1.2
        i = (n - 1) + frac if n > 0 else 0
        x = x0 + i * w + w / 2
        y = y0 + i * h - size / 2 - hop
        return x, y

    return icon(KID, size, lambda f: pos(f)[0], lambda f: pos(f)[1], enter=None)


def cape(cx, cy, length=14, color=(220, 20, 30)) -> mb.Layer:
    """A superhero cape streaming to the right from (cx, cy), rippling."""

    def draw(f):
        d = ImageDraw.Draw(f.img)
        top, bot = [], []
        for k in range(13):
            u = k / 12
            wave = math.sin(u * 5 - f.t * 9) * 1.0 * u
            x = cx + u * length
            half = 1.2 + u * 4.0
            top.append((P(x), P(cy - half + wave - u * 2)))
            bot.append((P(x), P(cy + half + wave - u * 2)))
        d.polygon(top + bot[::-1], fill=color + (255,))
        d.line(top, fill=(255, 90, 80, 255), width=mb.LW())
    return draw


def toss(a, b, hits, emoji="⚽", size=4, peak=9) -> mb.Layer:
    """A ball bounced back and forth between points a and b, arriving on each hit."""

    def draw(f):
        prev = [h for h in hits if h <= f.t]
        nxt = [h for h in hits if h > f.t]
        if not prev or not nxt:
            return
        t0, t1 = prev[-1], nxt[0]
        u = (f.t - t0) / (t1 - t0)
        frm, to = (a, b) if len(prev) % 2 else (b, a)
        x = frm[0] + (to[0] - frm[0]) * u
        y = frm[1] + (to[1] - frm[1]) * u - math.sin(u * math.pi) * peak
        mb.paste_center(f.img, mb.icon_image(emoji, round(P(size))).rotate(-u * 360, resample=Image.BICUBIC),
                        P(x), P(y))
    return draw


def falling(emojis, n=8, seed=1, size=4, speed=7.0, box=(2, 46)) -> mb.Layer:
    """Pictures falling from the top, spinning a little."""
    rnd = random.Random(seed)
    items = [(rnd.choice(emojis), rnd.uniform(*box), rnd.uniform(0, 1), rnd.uniform(-1, 1)) for _ in range(n)]

    def draw(f):
        for em, x, ph, spin in items:
            k = ((f.t - f.start) * speed / (f.H + 8) + ph) % 1
            y = -4 + k * (f.H + 8)
            im = mb.icon_image(em, round(P(size)))
            mb.paste_center(f.img, im.rotate(spin * k * 200, resample=Image.BICUBIC, expand=True), P(x), P(y))
    return draw


def garage(x0=6, x1=42, y0=6, y1=23) -> mb.Layer:
    """A two-car garage: walls, roof, two open bays."""

    def draw(f):
        d = ImageDraw.Draw(f.img)
        mid = (x0 + x1) / 2
        d.polygon([(P(x0 - 2), P(y0)), (P(mid), P(y0 - 5)), (P(x1 + 2), P(y0))], fill=(150, 30, 30, 255))
        d.rectangle([P(x0), P(y0), P(x1), P(y1)], fill=(205, 180, 140, 255))
        bw = (x1 - x0 - 6) / 2
        for i in range(2):
            bx = x0 + 2 + i * (bw + 2)
            d.rectangle([P(bx), P(y0 + 4), P(bx + bw), P(y1)], fill=(30, 26, 30, 255))
            # rolled-up door
            d.rectangle([P(bx), P(y0 + 4), P(bx + bw), P(y0 + 5.5)], fill=(235, 235, 235, 255))
        # wreath over the middle
        d.ellipse([P(mid - 1.5), P(y0 + 0.5), P(mid + 1.5), P(y0 + 3.5)], outline=(30, 160, 50, 255),
                  width=mb.LW() * 2)
    return draw


def board(x0=19, y0=2, x1=47, y1=18) -> mb.Layer:
    """A chalkboard in a wooden frame."""

    def draw(f):
        d = ImageDraw.Draw(f.img)
        d.rectangle([P(x0), P(y0), P(x1), P(y1)], fill=(140, 90, 40, 255))
        d.rectangle([P(x0 + 0.8), P(y0 + 0.8), P(x1 - 0.8), P(y1 - 0.8)], fill=(20, 70, 45, 255))
    return draw


def chalk_equals(x, y, at) -> mb.Layer:
    def draw(f):
        if f.t < at:
            return
        d = ImageDraw.Draw(f.img)
        k = ease((f.t - at) / 0.3)
        for dy in (-1, 1):
            d.line([P(x - 1.6), P(y + dy * 0.8), P(x - 1.6 + 3.2 * k), P(y + dy * 0.8)], fill=(235, 235, 225, 255),
                   width=mb.LW())
    return draw


def pond(cy=21, rx=26, ry=5) -> mb.Layer:
    def draw(f):
        d = ImageDraw.Draw(f.img)
        cx = f.W / 2
        d.ellipse([P(cx - rx), P(cy - ry), P(cx + rx), P(cy + ry)], fill=(150, 200, 235, 255))
        d.ellipse([P(cx - rx + 2), P(cy - ry + 1), P(cx + rx - 2), P(cy + ry - 1)], fill=(180, 225, 250, 255))
    return draw


def bow_tie(x, y, size=3.0, color=(230, 30, 60)) -> mb.Layer:
    """A ribbon bow drawn at (x, y) (callables of the frame allowed)."""

    def draw(f):
        d = ImageDraw.Draw(f.img)
        cx, cy = mb.val(x, f), mb.val(y, f)
        s = size
        d.polygon([(P(cx), P(cy)), (P(cx - s), P(cy - s * 0.6)), (P(cx - s), P(cy + s * 0.6))], fill=color + (255,))
        d.polygon([(P(cx), P(cy)), (P(cx + s), P(cy - s * 0.6)), (P(cx + s), P(cy + s * 0.6))], fill=color + (255,))
        d.ellipse([P(cx - s * 0.3), P(cy - s * 0.3), P(cx + s * 0.3), P(cy + s * 0.3)], fill=(255, 90, 110, 255))
    return draw


def santa_hat(x, y, size=6.0, flip=False) -> mb.Layer:
    def draw(f):
        d = ImageDraw.Draw(f.img)
        cx, cy = mb.val(x, f), mb.val(y, f)
        s = size
        tip = (cx + s * (-0.55 if flip else 0.55), cy - s * 0.75 + math.sin(f.t * 4) * 0.3)
        d.polygon([(P(cx - s / 2), P(cy)), (P(cx + s / 2), P(cy)), (P(tip[0]), P(tip[1]))], fill=(220, 20, 30, 255))
        d.rounded_rectangle([P(cx - s / 2 - 0.4), P(cy - 0.5), P(cx + s / 2 + 0.4), P(cy + 1.1)], radius=P(0.6),
                            fill=(245, 245, 245, 255))
        d.ellipse([P(tip[0] - 0.8), P(tip[1] - 0.8), P(tip[0] + 0.8), P(tip[1] + 0.8)], fill=(245, 245, 245, 255))
    return draw


def hatted_hippo(size, x, y, *, at=None, enter="grow", hits=None, bob=False, amp=0.6, flip=False) -> mb.Layer:
    """The hippo wearing a Santa hat on its head; the hat follows the hippo's bob / bounce.

    Noto's hippo faces left; its head (between the ears) is ~0.23*size left of centre and its top 0.35*size above.
    """

    def dy(f, t0):
        lt = f.t - t0
        v = 0.0
        if bob:
            v += math.sin(lt * 2 * math.pi * 0.8) * 0.7 * amp
        if hits:
            s = since(hits, f.t)
            if s is not None and s < 0.35:
                v -= math.sin(s / 0.35 * math.pi) * 3 * amp
        return v

    def draw(f):
        t0 = f.start if at is None else at
        if f.t < t0:
            return
        off = dy(f, t0)
        icon(HIPPO, size, x, y + off, at=t0, enter=enter, flip=flip)(f)
        hk = (f.t - t0 - 0.35) / 0.25
        if hk > 0:
            hx = x + (0.23 if flip else -0.23) * size
            hy = y - 0.24 * size + off - (1 - ease(hk)) * 3
            santa_hat(hx, hy, 0.36 * size * (0.6 + 0.4 * ease(hk)), flip=flip)(f)
    return draw


# ---------------------------------------------------------------- reusable scenes

def stairs_scene(tm, start, end_):
    """Christmas morning: creeping down the stairs, one step every other beat; the tree glows at the bottom."""
    beats = tm.beats_in(start + 1.0, end_ - 0.5)
    hits = beats[1::2][:6]
    return Scene(start, [DAWN, stars(8, seed=21, ymax=10),
                         glow(39, 15, 12, (255, 200, 80), 0.35),
                         icon("🎄", 16, 39, 15, enter="fade", enter_s=1.0),
                         tree_lights((33, 9, 45, 21), 12, seed=22),
                         stairs(), stair_kid(hits)], "stairs")


def surprise_scene(tm, start):
    w = lambda word: tm_after(tm, word, start)  # noqa: E731
    return Scene(start, [ROOM, sparkles(14, seed=23, box=(0, 0, 48, 27)),
                         icon("😴", 16, 24, 13.5, enter="grow", until=w("open")),
                         icon("😲", 16, 24, 13.5, at=w("open"), enter="pop", motion="pulse",
                              hits=[w("open"), w("eyes"), w("see")]),
                         icon("✨", 6, 9, 6, at=w("joy"), enter="pop", motion="pulse"),
                         icon("✨", 6, 39, 21, at=w("surprise"), enter="pop", motion="pulse")], "surprise")


def hero_scene(tm, start):
    w = lambda word: tm_after(tm, word, start)  # noqa: E731
    return Scene(start, [NIGHT, spotlight(24, strength=0.28), stars(18, seed=24),
                         cape(29, 13, length=15),
                         icon(HIPPO, 20, 23, 15, enter="grow", motion="bob", amp=0.8),
                         confetti(60, seed=25, at=w("there") - 0.2)], "hero")


def gift_scene(tm, start):
    w = lambda word: tm_after(tm, word, start)  # noqa: E731
    pop = w("hippopotamus")
    return Scene(start, [ROOM, sparkles(12, seed=26, box=(0, 0, 48, 27)),
                         icon("🎁", 17, 24, 14, enter="drop", until=pop, exit_s=0.1, motion="shake",
                              hits=tm.beats_in(start, pop)),
                         glow(24, 14, 14, (255, 220, 120), lambda f: 0.6 * max(0.0, 1 - (f.t - pop) / 1.0)
                              if f.t >= pop else 0),
                         icon(HIPPO, 19, 24, 14.5, at=pop, enter="pop", motion="bob"),
                         confetti(50, seed=27, at=pop)], "gift")


def only_scene(tm, start, seed):
    w = lambda word: tm_after(tm, word, start)  # noqa: E731
    beats = tm.beats_in(start, start + 5)
    return Scene(start, [BLACK, sparkles(20, seed=seed, box=(0, 0, 48, 27)),
                         rising("❤️", n=7, seed=seed, size=3, box=(2, 46), speed=6),
                         hatted_hippo(18, 24, 15, hits=beats[::2], amp=0.5)],
                 "only")


def no_scene(tm, start, emoji, word, flip=False, name="no"):
    at = tm_after(tm, word, start)
    return Scene(start, [BLACK, ground(24, (30, 110, 40)),
                         icon(emoji, 22, 24, 14, enter="left" if flip else "right", enter_s=0.5, flip=flip,
                              motion="bob"),
                         icon(NO, 20, 24, 14, at=at, enter="pop", alpha=0.9)], name, cut=True)


def parade_scene(tm, start, end_):
    beats = tm.beats_in(start, end_ + 1)
    layers = [DAY, ground(24, snowy=True), snow(30, seed=28, speed=2)]
    for k, sz in enumerate((11, 8, 10, 7, 9)):
        x = (lambda kk: lambda f: 54 - ((f.t - start) * 6.0 + kk * 13) % 66)(k)  # march right to left, wrapping
        layers.append(icon(HIPPO, sz, x, 21 - sz / 2 + 0.6, enter=None, motion="bounce", hits=beats[k % 2::2],
                           amp=0.6))
    return Scene(start, layers, "parade")


def love_scene(tm, start, seed):
    beats = tm.beats_in(start, start + 6)
    return Scene(start, [BLACK, rising("❤️", n=9, seed=seed, size=3.5, box=(2, 46),
                                                                 speed=7),
                         icon(KID, 12, 15, 15, enter="left", motion="bounce", hits=beats[0::2]),
                         icon(HIPPO, 16, 32, 15, enter="right", motion="bounce", hits=beats[1::2]),
                         icon("❤️", 5, 23.5, 7, at=tm_after(tm, "me", start), enter="pop", motion="pulse", amp=2)],
                 "love")


def tm_after(tm, word, t):
    """Start of the first sung `word` at or after time t."""
    for label, s, _e in tm.words:
        if label == word and s >= t - 0.05:
            return s
    raise KeyError(f"{word} after {t}")


# ---------------------------------------------------------------- the story

def build(tm):
    S = []
    w = lambda word, t: tm_after(tm, word, t)  # noqa: E731
    beats = tm.beats

    # ---- intro: snowy night, the title, a hippo peeks out
    S.append(Scene(0.0, [NIGHT, stars(30, seed=1), snow(50, seed=2, speed=2.5),
                         ground(24, snowy=True),
                         icon("🏠", 14, 12, 15.5, enter="fade", enter_s=1.5),
                         icon("🎄", 11, 37, 16.5, at=1.0, enter="fade", enter_s=1.5),
                         icon(HIPPO, 9, 26, 18, at=4.8, enter="rise", enter_s=0.8, motion="bob"),
                         text("I WANT A", 2, WHITE, at=3.0),
                         text("HIPPO!", 8, (200, 120, 255), at=4.8)], "intro"))

    # ---- verse 1: the wish
    S.append(Scene(8.35, [ROOM, sparkles(10, seed=3, box=(0, 0, 48, 27)),
                          icon(KID, 13, 11, 16, enter="rise"),
                          icon("💭", 22, 31, 11, at=9.05, enter="pop"),
                          icon(HIPPO, 10, 31, 11, at=9.60, enter="pop", motion="bob"),
                          icon("🎄", 5, 38, 6, at=11.22, enter="pop")], "wish"))
    S.append(only_scene(tm, 13.1, 4))

    # no dolls, no dinky tinker toys
    S.append(Scene(17.4, [BLACK,
                          icon("🪆", 10, 9, 13, at=18.6, enter="drop"),
                          icon(NO, 11, 9, 13, at=18.9, enter="pop", alpha=0.9),
                          icon("🧸", 10, 24, 13, at=19.68, enter="drop"),
                          icon(NO, 11, 24, 13, at=20.0, enter="pop", alpha=0.9),
                          icon("🚂", 10, 39, 13, at=20.18, enter="drop"),
                          icon(NO, 11, 39, 13, at=20.73, enter="pop", alpha=0.9)], "no toys"))
    # play with and enjoy: ball between the child and the hippo
    play = tm.beats_in(21.4, 25.6)
    S.append(Scene(21.45, [DAY, ground(24, snowy=True), snow(24, seed=5, speed=2),
                           icon(KID, 11, 9, 16.5, enter="left", motion="bounce", hits=play[0::2]),
                           icon(HIPPO, 14, 38, 15.5, enter="right", flip=False, motion="bounce", hits=play[1::2]),
                           toss((13, 13), (32, 12), play)], "play"))
    S.append(gift_scene(tm, 25.5))

    # Santa thinks it over
    S.append(Scene(30.05, [NIGHT, stars(20, seed=6), snow(30, seed=7, speed=2),
                           icon("🎅", 16, 14, 15, enter="left", motion="wobble"),
                           icon("💭", 18, 34, 9, at=30.68, enter="pop"),
                           icon(HIPPO, 9, 34, 9, at=31.4, enter="pop", motion="bob"),
                           icon("👍", 8, 36, 21, at=31.93, enter="pop", motion="pulse")], "santa"))
    # no dirty chimney flue...
    S.append(Scene(34.3, [NIGHT, stars(20, seed=8), snow(30, seed=9, speed=2), ground(24, snowy=True),
                          icon("🏠", 22, 24, 13.5, enter=None),
                          steam(29.5, 4, n=2, height=4, color=(70, 70, 80)),
                          icon("💨", 7, 31, 3, at=36.7, enter="pop"),
                          icon(NO, 12, 29.5, 5, at=35.0, enter="pop", alpha=0.9)], "chimney"))
    # ...just bring him through the front door
    walk = lambda f: keyframes([(38.75, -10), (40.12, 21), (42.0, 22)], f.t)  # noqa: E731
    S.append(Scene(38.45, [DAY, ground(24, (90, 60, 30)),
                           glow(30, 13, 11, (255, 230, 150), 0.35),
                           icon("🚪", 16, 30, 14, enter="fade"),
                           icon(HIPPO, 13, walk, 16, enter=None, flip=True, motion="bob", amp=0.7),
                           icon("👍", 7, 42, 6, at=40.9, enter="pop", motion="pulse"),
                           sparkles(8, seed=10, box=(22, 4, 40, 22))], "front door"))

    # ---- bridge: Christmas morning
    S.append(stairs_scene(tm, 42.5, 50.9))
    S.append(surprise_scene(tm, 50.85))
    S.append(hero_scene(tm, w("hippo", 55.0) - 0.05))

    # ---- chorus 2
    S.append(Scene(59.65, [NIGHT, stars(18, seed=11), snow(40, seed=12, speed=2.5), ground(24, snowy=True),
                           icon(KID, 12, 13, 15.5, enter="left"),
                           hatted_hippo(16, 32, 15, enter="right", bob=True),
                           rising("❤️", n=5, seed=13, size=3, box=(18, 30), speed=5, at=60.5)], "together"))
    S.append(only_scene(tm, 63.95, 14))
    S.append(no_scene(tm, 68.3, "🐊", "crocodiles", name="no crocodiles"))
    S.append(no_scene(tm, 70.2, "🦏", "roses", flip=True, name="no rhinos"))
    S.append(parade_scene(tm, 72.35, 76.6))
    S.append(love_scene(tm, 76.55, 15))

    # ---- instrumental: the hippo goes skating
    skate_x = lambda f: 24 + 15 * math.sin((f.t - 80.4) * 2 * math.pi / 4.2)  # noqa: E731
    skate_flip = lambda f: math.cos((f.t - 80.4) * 2 * math.pi / 4.2) > 0  # noqa: E731
    S.append(Scene(80.4, [NIGHT, stars(30, seed=16), icon("🌙", 6, 41, 5, enter="fade"),
                          snow(40, seed=17, speed=2), pond(),
                          skater(skate_x, skate_flip),
                          sparkles(10, seed=18, box=(0, 0, 48, 12))], "skating"))

    # ---- verse 2: Mom and the teacher
    S.append(Scene(89.3, [ROOM, icon("👩", 13, 9, 15, enter="left"),
                          icon("💬", 20, 28, 9, at=89.92, enter="pop"),
                          icon(HIPPO, 9, 28, 8.5, at=90.45, enter="pop", motion="pulse",
                               hits=[91.6, 91.8, 91.97], amp=2.5),
                          icon("😱", 9, 42, 20, at=91.6, enter="pop", motion="shake",
                               hits=[91.6, 91.97])], "mom"))
    S.append(Scene(93.35, [BLACK, board(),
                           icon("👩\u200d🏫", 14, 9, 15, enter="left"),
                           icon(HIPPO, 8, 26, 10, at=94.6, enter="pop"),
                           chalk_equals(32.5, 10, 95.08),
                           icon("🥕", 5, 38, 7.5, at=95.62, enter="pop"),
                           icon("🥬", 6, 41.5, 12, at=95.9, enter="pop")], "teacher"))
    # instrumental: veggies rain down, the hippo munches
    munch = tm.beats_in(97.3, 106)
    S.append(Scene(97.2, [BLACK, ground(24, (40, 120, 40)),
                          falling(["🥕", "🥬", "🍉", "🍎", "🥦"], n=12, seed=19, size=4.5, speed=9),
                          icon(HIPPO, 16, 24, 15, enter="grow", motion="pulse", hits=munch, amp=0.8),
                          sparkles(8, seed=20, box=(0, 0, 48, 20))], "munch"))

    # ---- the two-car garage
    S.append(Scene(105.9, [DAY, ground(24, (110, 110, 110)), garage(),
                           icon("🚗", 9, keyframes_fn([(108.47, 16.5), (109.3, -12)]), 18.5, enter=None),
                           icon("🚗", 9, keyframes_fn([(108.67, 31.5), (109.5, 60)]), 18.5, enter=None,
                                flip=True),
                           icon(HIPPO, 14, 24, 16.5, at=109.03, enter="drop", motion="bob"),
                           sparkles(10, seed=21, box=(4, 0, 44, 23))], "garage"))
    S.append(Scene(110.15, [WARM, glow(24, 15, 15, (255, 170, 80), 0.3),
                            icon(HIPPO, 18, 26, 15, enter=None, motion="bob", amp=0.5),
                            icon("🍉", 7, 11, 18, at=110.33, enter="pop", until=111.4),
                            rising("🫧", n=8, seed=22, size=3.5, box=(14, 40), speed=10, at=111.42),
                            icon("🧽", 6, 30, 11, at=111.42, enter="pop", until=112.5, motion="shake",
                                 hits=tm.beats_in(111.4, 112.6)),
                            icon("💆", 8, 36, 8, at=112.53, enter="pop", motion="bob"),
                            rising("❤️", n=5, seed=23, size=3, box=(18, 36), speed=6, at=113.35)], "care"))

    # ---- bridge 2
    S.append(stairs_scene(tm, 114.05, 122.4))
    S.append(surprise_scene(tm, 122.4))
    S.append(hero_scene(tm, w("hippo", 127.0) - 0.05))

    # ---- final chorus
    S.append(gift_scene(tm, 131.2))
    S.append(only_scene(tm, 135.5, 30))
    S.append(no_scene(tm, 139.85, "🐊", "crocodiles", name="no crocodiles 2"))
    S.append(no_scene(tm, 141.75, "🦏", "roses", flip=True, name="no rhinos 2"))
    S.append(parade_scene(tm, 143.95, 148.1))
    S.append(love_scene(tm, 148.1, 31))

    # ---- finale
    fin = 150.9
    end = tm.duration
    fade = lambda f: ease((f.t - (end - 2.5)) / 2.5)  # noqa: E731
    S.append(Scene(fin, [NIGHT, fireworks(beats_after(beats, fin, 10), seed=32),
                         icon("🎄", 15, 38, 15, enter="grow"),
                         hatted_hippo(14, 14, 16, hits=beats_after(beats, fin, 10)),
                         text("MERRY", 2, RED, at=fin + 0.5),
                         text("CHRISTMAS!", 21, GREEN, at=fin + 1.0),
                         dim(fade)], "finale"))
    return S


def beats_after(beats, t, n):
    return [b for b in beats if b >= t][:n]


def keyframes_fn(points):
    return lambda f: keyframes(points, f.t)


def skater(x, flip):
    """The hippo skating: faces the way it glides, leaning into it."""
    right = icon(HIPPO, 12, x, 15.5, enter=None, flip=True, rot=lambda f: -6 * math.sin(f.t * 3))
    left = icon(HIPPO, 12, x, 15.5, enter=None, flip=False, rot=lambda f: 6 * math.sin(f.t * 3))

    def draw(f):
        (right if flip(f) else left)(f)
    return draw
