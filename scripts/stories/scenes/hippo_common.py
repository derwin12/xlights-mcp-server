"""'I Want a Hippopotamus for Christmas': 140x60 garage matrix and 200x42 bushes scenes to go with the approved
two-window story.

The timeline below is the same as hippopotamus_windows.build() (same scene boundaries and lyric cues), so the
garage, the windows and the bushes change scene together. The windows story itself is unchanged; it is written
with hippopotamus_windows.py, and these with hippo_garage.py / hippo_bushes.py.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
from morph_backdrop import backdrop, pattern_sweeps  # noqa: E402,F401
from hippopotamus_window import (BLUE, GOLD, GREEN, HIPPO, ICE, KID, NO, PINK, PURPLE, RED, WHITE, XMAS,  # noqa: E402,F401
                                 Z_BACK, Z_FRONT, Z_PIC, Z_WORD, cape_img, cues)

cues = cues


def timeline(c):
    """[(scene, t0, t1, kwargs)] - mirrors hippopotamus_windows.build()."""
    w = c.w
    T = [("intro", 0.0, w("I", 7.5), {}),
         ("want", w("I", 7.5), w("only", 11.0) - 0.1, {}),
         ("wish", w("only", 11.0) - 0.1, 13.4, {}),
         ("only", 13.4, w("don't", 16.0) - 0.1, {}),
         ("toys", w("don't", 16.0) - 0.1, 21.05, dict(doll=(17.3, w("doll", 17.0)), teddy=(19.55, w("dink", 19.5)),
                                                       train=(20.35, w("toy", 20.3)))),
         ("play", 21.05, w("I", 25.0) - 0.05, {}),
         ("gift", w("I", 25.0) - 0.05, 30.1, {}),
         ("santa", 30.1, w("he", 33.5) - 0.1, {}),
         ("chimney", w("he", 33.5) - 0.1, w("just", 37.8) - 0.05, {}),
         ("door", w("just", 37.8) - 0.05, w("that", 40.0) - 0.05, {}),
         ("easy", w("that", 40.0) - 0.05, w("I", 42.0) - 0.05, {}),
         ("morning", w("I", 42.0) - 0.05, w("creeping", 46.5) - 0.05, {}),
         ("stairs", w("creeping", 46.5) - 0.05, w("oh", 50.0) - 0.05, {}),
         ("joy", w("oh", 50.0) - 0.05, w("when", 52.5) - 0.05, {}),
         ("eyes", w("when", 52.5) - 0.05, w("hippo", 55.3) - 0.05, {}),
         ("hero", w("hippo", 55.3) - 0.05, w("I", 59.5) - 0.1, {}),
         ("want", w("I", 59.5) - 0.1, w("only", 63.5) - 0.1, {}),
         ("only", w("only", 63.5) - 0.1, w("no", 67.8) - 0.1, {}),
         ("animals", w("no", 67.8) - 0.1, 72.2, dict(croc=w("crocodiles", 68.0), rhino_t=w("no", 70.0) - 0.05,
                                                     rhino=w("rhinoceroses", 70.0) + 0.3)),
         ("parade", 72.2, w("and", 75.8) - 0.05, {}),
         ("love", w("and", 75.8) - 0.05, 80.4, {}),
         ("skate", 80.4, 89.0, {}),
         ("gifts", 89.0, 97.5, {}),
         ("tree", 97.5, w("there's", 105.0) - 0.1, {}),
         ("garage", w("there's", 105.0) - 0.1, w("I", 113.5) - 0.05, {}),
         ("morning", w("I", 113.5) - 0.05, w("creeping", 118.0) - 0.05, {}),
         ("stairs", w("creeping", 118.0) - 0.05, w("oh", 121.5) - 0.05, {}),
         ("joy", w("oh", 121.5) - 0.05, w("when", 124.0) - 0.05, {}),
         ("eyes", w("when", 124.0) - 0.05, w("hippo", 126.8) - 0.05, {}),
         ("hero", w("hippo", 126.8) - 0.05, w("I", 130.5) - 0.1, {}),
         ("want", w("I", 130.5) - 0.1, w("only", 134.0) - 0.1, {}),
         ("only", w("only", 134.0) - 0.1, w("no", 139.0) - 0.1, {}),
         ("animals", w("no", 139.0) - 0.1, w("I", 143.0) - 0.05, dict(croc=w("crocodiles", 139.5),
                                                                      rhino_t=w("or", 141.0) - 0.05,
                                                                      rhino=w("rhinoceroses", 141.0) + 0.3)),
         ("parade", w("I", 143.0) - 0.05, w("and", 147.3) - 0.05, {}),
         ("love", w("and", 147.3) - 0.05, 151.3, {}),
         ("ending", 151.3, c.duration, {})]
    return T


def run(s, scenes):
    for name, t0, t1, kw in timeline(s.cues):
        backdrop(s, t0, t1)
        fn = scenes.get(name)
        if fn:
            fn(s, t0, t1, **kw)


def bar_sweeps(s, t0, t1, colors=XMAS, every=1):
    """SuperStar-style Morph pattern groups on every other beat (none while the tree's are echoed)."""
    pattern_sweeps(s, t0, t1, colors, every)


# ---------------------------------------------------------------- drawn props (sized for these matrices)

def cape_r(s, scale=1):
    key = cape_img(s)
    im = s.images[key].transpose(0)
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), 0)
    return s.image(f"cape_r_{scale}", im)


def stairs_wide(s, n, w, h, name):
    def draw(d, im):
        for i in range(n):
            x0, y0 = i * w, i * h
            d.rectangle([x0, y0, im.width - 1, y0 + 1], fill=(200, 140, 80, 255))
            d.rectangle([x0, y0 + 2, im.width - 1, y0 + h - 1], fill=(120, 70, 40, 255))
    return s.drawn(name, n * w, n * h, draw)


def pond(s, w, h):
    def draw(d, im):
        d.ellipse([0, 0, w - 1, h - 1], fill=(120, 190, 255, 255))
        d.ellipse([w * 0.08, h * 0.25, w * 0.92, h * 0.75], fill=(170, 220, 255, 255))
    return s.drawn(f"pond_{w}", w, h, draw)


def garage_big(s, w=96, h=44):
    def draw(d, im):
        d.polygon([(0, h * 0.28), (w / 2, 0), (w - 1, h * 0.28)], fill=(150, 40, 40, 255))
        d.rectangle([3, h * 0.28, w - 4, h - 1], fill=(170, 150, 120, 255))
        bw = (w - 18) / 2
        for x0 in (7, 11 + bw):
            d.rectangle([x0, h * 0.42, x0 + bw, h - 1], fill=(235, 235, 235, 255))
            for k in range(1, 5):
                y = h * 0.42 + k * (h * 0.58) / 5
                d.line([(x0, y), (x0 + bw, y)], fill=(150, 150, 150, 255))
    return s.drawn(f"garage_{w}", w, h, draw)


def closed_eye(s, w):
    def draw(d, im):
        d.arc([0, -w * 0.3, w - 1, w * 0.5], 20, 160, fill=(255, 220, 180, 255), width=max(2, w // 12))
        for k in range(5):
            x = w * (0.2 + 0.15 * k)
            d.line([(x, w * 0.45), (x - 1, w * 0.58)], fill=(255, 220, 180, 255))
    return s.drawn(f"closed_eye_{w}", w, round(w * 0.6), draw)


# ================================================================ 140x60 matrix (the garage)

GL, GC, GR = 26, 70, 114  # left / centre / right spots


def g_intro(s, t0, t1):
    c = s.cues
    s.twinkle(0.2, t1, (WHITE, GOLD), count=10, fade=1.0)
    s.show(s.emoji("🎄", 50), 0.4, t1, GC, 32, enter="fade", enter_s=1.5)
    s.show(s.emoji("🎁", 22), 4.6, t1, GL, 46, enter="top", hits=c.beats_in(5.0, t1)[::2], amp=1)
    s.show(s.emoji("🎁", 22), 5.2, t1, GR, 46, enter="top", hits=c.beats_in(5.6, t1)[1::2], amp=1)
    bar_sweeps(s, 0.4, t1, (RED, GREEN))


def g_want(s, t0, t1):
    c = s.cues
    hip = c.w("hippo", t0)
    xm = c.w("christmas", hip)
    s.show(s.word("I WANT A", WHITE, 2), t0, hip, GC, 8, enter="pop", z=Z_WORD)
    s.show(s.word("HIPPO", PURPLE, 3), hip, xm, GC, 9, enter="pop", z=Z_WORD)
    s.show(s.word("FOR XMAS", RED, 2), xm, t1, GC, 8, enter="pop", z=Z_WORD)
    h = s.emoji(HIPPO, 34, flip=True)
    s.glide(h, [(hip, -20, 40), (hip + 0.6, GC, 40), (t1, GC, 40)])
    s.ring(hip + 0.6, GC, 40, PURPLE, r=40)
    s.show(s.emoji("🎄", 30), xm + 0.1, t1, GL - 8, 42, enter="bottom", z=Z_BACK)
    s.show(s.emoji("🎄", 30), xm + 0.25, t1, GR + 8, 42, enter="bottom", z=Z_BACK)
    s.ring(xm, GC, 40, GOLD, r=60)
    s.twinkle(t0, t1, (WHITE, GOLD), count=8)


def g_wish(s, t0, t1):
    s.show(s.emoji(KID, 30), t0, t1, GL, 40, enter="left")
    s.show(s.emoji("💭", 50), t0 + 0.3, t1, 92, 26, enter="pop")
    s.show(s.emoji(HIPPO, 28), t0 + 0.7, t1, 92, 24, enter="pop", z=Z_FRONT)


def g_only(s, t0, t1):
    c = s.cues
    do = next((t for w_, t, _ in c.words if t0 <= t < t1 and w_ == "do"), t0 + 1.0)
    s.show(s.word("ONLY", GOLD, 3), c.w("only", t0 - 0.5), t1, GL, 12, enter="left", z=Z_WORD)
    s.show(s.emoji("☝️", 26), t0 + 0.3, t1, GL, 40, enter="bottom", hits=c.beats_in(t0 + 0.6, t1)[1::2], amp=2)
    s.show(s.emoji(HIPPO, 46), t0, t1, 92, 32, enter="pop", hits=c.beats_in(t0, t1)[::2], amp=3)
    s.ring(do, 92, 32, GOLD, r=50)
    s.sweep(do, do + 0.6, WHITE, "top")
    s.twinkle(t0, t1, (WHITE, PURPLE), count=8)


def g_toys(s, t0, t1, doll, teddy, train):
    s.show(s.word("NO", RED, 3), t0, t1, GC, 10, enter="pop", z=Z_WORD)
    for (em, x, (a, hit)) in (("🪆", GL, doll), ("🧸", GR, teddy)):
        s.show(s.emoji(em, 34), a, t1, x, 30, enter="top", enter_s=0.25)
        s.show(s.emoji(NO, 40), hit, t1, x, 30, enter="pop", enter_s=0.2, z=Z_FRONT)
        s.ring(hit, x, 30, RED, r=30, dur=0.5)
    a, hit = train
    s.show(s.emoji("🚂", 24), a, t1, GC, 46, enter="right", enter_s=0.3, z=Z_FRONT)
    s.show(s.emoji(NO, 28), hit, t1, GC, 46, enter="pop", enter_s=0.15, z=Z_FRONT + 1)


def g_play(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0 + 0.4, t1)
    s.show(s.emoji(KID, 28), t0, t1, GL, 42, enter="left", hits=beats[0::2], amp=3)
    s.show(s.emoji(HIPPO, 34), t0, t1, GR, 40, enter="right", hits=beats[1::2], amp=3)
    ball = s.emoji("⚽", 9)
    a, b = (GL + 14, 32), (GR - 18, 32)
    for i, (x, y) in enumerate(zip(beats, beats[1:])):
        frm, to = (a, b) if i % 2 == 0 else (b, a)
        s.glide(ball, [(x, *frm), ((x + y) / 2, (frm[0] + to[0]) / 2, 6), (y, *to)], z=Z_FRONT)
    s.show(s.word("PLAY", GREEN, 2), c.w("play", t0), t1, GC, 52, enter="pop", z=Z_WORD)
    s.snow(t0, t1, count=4)


def g_gift(s, t0, t1):
    c = s.cues
    hip = c.w("hippo", t0)
    xm = c.w("christmas", hip)
    s.show(s.emoji("🎁", 40), t0, hip, GC, 34, enter="top", exit="shrink", exit_s=0.15,
           hits=c.beats_in(t0 + 0.4, hip), amp=2)
    s.show(s.emoji(HIPPO, 44), hip, t1, GC, 34, enter="pop", hits=c.beats_in(hip + 0.4, t1)[::2], amp=3)
    s.show(s.word("HIPPO", PURPLE, 2), hip, t1, GL, 12, enter="pop", z=Z_WORD)
    s.show(s.word("XMAS", RED, 2), xm, t1, GR, 12, enter="pop", z=Z_WORD)
    s.show(s.emoji("🎄", 28), xm + 0.1, t1, GL, 42, enter="bottom")
    s.show(s.emoji("🎄", 28), xm + 0.2, t1, GR, 42, enter="bottom")
    s.ring(hip, GC, 34, GOLD, r=50)
    s.ring(hip + 0.2, GC, 34, RED, r=50)
    s.twinkle(hip, hip + 2.5, (RED, GREEN, GOLD, BLUE, PINK), count=35, steps=20, fade=0.3)


def g_santa(s, t0, t1):
    c = s.cues
    mind = c.w("mind", t0)
    s.show(s.emoji("🎅", 40), t0, t1, GL + 6, 32, enter="left", hits=c.beats_in(t0 + 0.5, t1)[::2], amp=2)
    s.show(s.emoji(HIPPO, 30), t0 + 0.4, t1, GC + 10, 40, enter="bottom")
    s.show(s.emoji("👍", 30), mind - 0.2, t1, GR + 4, 30, enter="right", hits=c.beats_in(mind + 0.3, t1), amp=2)
    s.ring(mind, GR + 4, 30, GREEN, r=30)
    s.snow(t0, t1, count=5)


def g_chimney(s, t0, t1):
    c = s.cues
    hit = c.w("chimney", t0)
    s.show(s.emoji("🏠", 50), t0, t1, 96, 32, enter="fade", enter_s=0.6, z=Z_BACK)
    s.show(s.emoji(HIPPO, 30, flip=True), t0, t1, 28, 42, enter="left", hits=c.beats_in(t0 + 0.5, t1)[::2], amp=2)
    s.show(s.emoji(NO, 20), hit, t1, 108, 12, enter="pop", z=Z_FRONT)
    s.ring(hit, 108, 12, RED, r=20, dur=0.5)
    s.snow(t0, t1, count=6)


def g_door(s, t0, t1):
    c = s.cues
    door = c.w("door", t0)
    s.show(s.emoji("🚪", 40), t0, t1, 116, 32, enter="fade", enter_s=0.4)
    h = s.emoji(HIPPO, 30, flip=True)
    s.glide(h, [(t0, 22, 42), (c.w("bring", t0), 22, 42), (door, 88, 42), (t1, 88, 42)])
    s.ring(door, 116, 32, GOLD, r=30)


def g_easy(s, t0, t1):
    c = s.cues
    s.show(s.word("EASY", GREEN, 3), c.w("easy", t0), t1, 46, 30, enter="pop", z=Z_WORD)
    s.show(s.emoji("👍", 34), t0 + 0.3, t1, 108, 30, enter="bottom", hits=c.beats_in(t0 + 0.8, t1), amp=2)
    bar_sweeps(s, t0, t1)


def g_morning(s, t0, t1):
    c = s.cues
    xm = c.w("christmas", t0)
    s.glide(s.emoji("☀️", 30), [(t0, 22, 80), (xm, 22, 18), (t1, 22, 18)], z=Z_BACK)
    s.show(s.emoji("🎄", 44), xm, t1, 86, 32, enter="bottom")
    for k, (x, px) in enumerate(((66, 16), (106, 18), (120, 14))):
        s.show(s.emoji("🎁", px), xm + 0.3 + 0.15 * k, t1, x, 52, enter="pop", z=Z_FRONT)
    s.twinkle(t0, t1, (GOLD, WHITE), count=10)


def g_stairs(s, t0, t1):
    c = s.cues
    n, w, h = 6, 20, 8
    st = stairs_wide(s, n, w, h, "stairs_garage")
    top = 60 - n * h
    s.show(st, t0, t1, n * w / 2 + 10, top + n * h / 2, enter="fade", enter_s=0.5, z=Z_BACK)
    kid = s.emoji(KID, 14)
    beats = c.beats_in(t0 + 0.4, t1 - 0.2)[: n - 1]
    pos = [(10 + w * i + 10, top + h * i - 7) for i in range(n)]
    pts = [(t0, *pos[0])]
    for i, b in enumerate(beats):
        pts += [(b, *pos[i]), (b + 0.2, *pos[i + 1])]
    pts.append((t1, *pts[-1][1:]))
    s.glide(kid, pts)
    s.show(s.emoji("🎄", 30), t0 + 0.3, t1, 125, 40, enter="fade", enter_s=0.5, z=Z_BACK)
    s.show(s.word("SHHH", ICE, 1), t0 + 0.3, t1, 26, 6, enter="pop", z=Z_WORD)


def g_joy(s, t0, t1):
    c = s.cues
    joy, sur = c.w("joy", t0), c.w("surprise", t0)
    s.show(s.emoji("😃", 38), t0, t1, GL + 4, 34, enter="pop")
    s.show(s.emoji("😲", 38), sur, t1, GR - 4, 34, enter="pop", enter_s=0.2)
    s.show(s.word("JOY", GOLD, 2), joy, t1, GC, 18, enter="pop", z=Z_WORD)
    s.show(s.word("WOW", PINK, 2), sur, t1, GC, 42, enter="pop", z=Z_WORD)
    s.ring(joy, GL + 4, 34, GOLD, r=36)
    s.ring(sur, GR - 4, 34, PINK, r=36)


def g_eyes(s, t0, t1):
    """The garage is a face: two eyes closed, opening on 'open', blinking on 'eyes'."""
    c = s.cues
    op, ey = c.w("open", t0), c.w("eyes", t0)
    shut, eye = closed_eye(s, 40), s.emoji("👁️", 40)
    for x in (40, 100):
        s.show(shut, t0, op, x, 28, enter="fade", enter_s=0.3)
        s.pic(eye, op, ey, x, 28, scale=(20, 100))
        s.pic(shut, ey, ey + 0.15, x, 28)
        s.pic(eye, ey + 0.15, t1, x, 28)
        s.ring(op, x, 28, WHITE, r=34)


def g_hero(s, t0, t1):
    c = s.cues
    hero = c.w("hero", t0)
    h = s.emoji(HIPPO, 40, flip=True)
    cape = cape_r(s, 2)
    land = t0 + 1.4
    s.glide(h, [(t0, -30, 16), (land, 92, 34), (t1, 92, 34)])
    s.glide(cape, [(t0, -52, 12), (land, 70, 30), (t1, 70, 30)], z=Z_BACK)
    s.show(s.word("HERO", GOLD, 3), hero, t1, 30, 14, enter="pop", z=Z_WORD)
    s.ring(land, 92, 34, GOLD, r=50)
    for i, b in enumerate(c.beats_in(t0, t1)):
        s.sweep(b, b + 1.0, (RED, GOLD, GREEN, BLUE, PURPLE)[i % 5], "left" if i % 2 else "right")
    s.twinkle(hero, t1, (RED, GOLD, GREEN, BLUE, PINK), count=25, steps=20)


def g_animals(s, t0, t1, croc, rhino_t, rhino):
    s.show(s.emoji("🐊", 40), t0, t1, GL + 8, 34, enter="left", enter_s=0.4)
    s.show(s.emoji(NO, 46), croc, t1, GL + 8, 34, enter="pop", z=Z_FRONT)
    s.ring(croc, GL + 8, 34, RED, r=36)
    s.show(s.emoji("🦏", 40), rhino_t, t1, GR - 8, 34, enter="right", enter_s=0.3)
    s.show(s.emoji(NO, 46), rhino, t1, GR - 8, 34, enter="pop", z=Z_FRONT)
    s.ring(rhino, GR - 8, 34, RED, r=36)


def g_parade(s, t0, t1):
    c = s.cues
    h = s.emoji(HIPPO, 22)
    span = t1 - t0
    for k in range(5):
        a = t0 + k * span / 6
        s.glide(h, [(a, 156, 44), (a + span * 0.7, -16, 44)])
    like = c.w("like", t0)
    s.show(s.word("LIKE", WHITE, 2), like, t1, 50, 12, enter="pop", z=Z_WORD)
    s.show(s.emoji("❤️", 20), like + 0.1, t1, 90, 12, enter="pop", hits=c.beats_in(t0, t1), amp=1)
    s.snow(t0, t1, count=5)


def g_love(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    me = c.w("me", t0)
    s.show(s.emoji(KID, 28), t0, t1, GL, 40, enter="left", hits=beats[0::2], amp=3)
    s.show(s.emoji(HIPPO, 36), t0, t1, GR, 38, enter="right", hits=beats[1::2], amp=3)
    heart = s.emoji("❤️", 16)
    s.glide(heart, [(me - 0.9, GR, 14), (me - 0.45, GC, 4), (me, GL, 14)], z=Z_FRONT)
    s.show(s.emoji("❤️", 26), me, t1, GC, 28, enter="pop", hits=c.beats_in(me + 0.3, t1), amp=2, z=Z_FRONT)
    s.ring(me, GC, 28, PINK, r=50)


def g_skate(s, t0, t1):
    s.show(pond(s, 136, 18), t0, t1, 70, 50, enter="fade", enter_s=0.8, z=Z_BACK)
    s.show(s.emoji("🌙", 14), t0, t1, 120, 10, enter="fade", enter_s=0.8, z=Z_BACK)
    left, right = s.emoji(HIPPO, 22), s.emoji(HIPPO, 22, flip=True)
    lap, t, k = 3.4, t0, 0
    while t < t1 - 0.05:
        e = min(t + lap, t1)
        u = (e - t) / lap
        if k % 2 == 0:
            s.pic(right, t, e, 14, 40, to=(14 + 112 * u, 40))
        else:
            s.pic(left, t, e, 126, 40, to=(126 - 112 * u, 40))
        t, k = e, k + 1
    s.snow(t0, t1, count=6)
    s.twinkle(t0, t1, (WHITE,), count=6)


def g_gifts(s, t0, t1):
    c = s.cues
    bars = c.bars_in(t0, t1)
    spots = [(30, 48, 22), (70, 48, 22), (110, 48, 22), (50, 28, 20), (90, 28, 20), (70, 10, 16)]
    for (x, y, px), b in zip(spots, bars):
        s.show(s.emoji("🎁", px), b, t1, x, y, enter="top", enter_s=0.3, hits=c.beats_in(b + 0.5, t1)[::4], amp=1)
        s.ring(b + 0.3, x, y, GOLD, r=16, dur=0.5)
    bar_sweeps(s, t0, t1, (RED, GREEN))


def g_tree(s, t0, t1):
    c = s.cues
    bars = c.bars_in(t0, t1)
    end_tree = bars[-2] if len(bars) >= 3 else t1
    s.show(s.emoji("🎄", 52), t0, end_tree, 46, 32, enter="fade", enter_s=1.0)
    s.show(s.emoji("⭐", 14), bars[1] if len(bars) > 1 else t0, end_tree, 46, 6, enter="top", z=Z_FRONT)
    s.show(s.emoji(HIPPO, 34), t0 + 1.0, end_tree, 104, 40, enter="right",
           hits=c.beats_in(t0 + 1.5, end_tree)[::2], amp=2)
    s.show(s.emoji("🎁", 18), t0 + 1.5, end_tree, 126, 48, enter="pop", z=Z_FRONT)
    s.twinkle(t0, end_tree, (RED, GOLD, BLUE, GREEN, WHITE), count=12, steps=25)
    bar_sweeps(s, t0, end_tree, (GOLD, WHITE))
    swaps = c.beats_in(end_tree, t1)
    if swaps:
        a, b, g = s.emoji(HIPPO, 44), s.emoji("🎄", 44), s.emoji("🎁", 38)
        s.flash([a, b, g], swaps, GC, 32, end=t1)
        for i, t in enumerate(swaps):
            s.ring(t, GC, 32, XMAS[i % 4], r=50, dur=0.5)


def g_garage(s, t0, t1):
    """There's lots of room for him in the two-car garage: feed him, wash him, massage him."""
    c = s.cues
    him = c.w("him", t0)
    feed, wash, mas = c.w("feed", t0), c.w("wash", t0), c.w("massage", t0)
    s.show(garage_big(s), t0, t1, 70, 38, enter="fade", enter_s=0.6, z=Z_BACK)
    s.glide(s.emoji(HIPPO, 22), [(him, 160, 48), (him + 1.0, 92, 48), (t1, 92, 48)], z=Z_PIC)
    s.show(s.word("ROOM", ICE, 2), c.w("room", t0), feed, 22, 8, enter="pop", z=Z_WORD)
    s.show(s.emoji("🍉", 16), feed, wash, 122, 10, enter="pop", hits=[feed + 0.3], z=Z_FRONT)
    s.show(s.word("FEED", GREEN, 2), feed, wash, 26, 8, enter="pop", z=Z_WORD)
    s.show(s.emoji("🧽", 16), wash, mas, 122, 10, enter="pop", hits=c.beats_in(wash + 0.2, mas), amp=2, z=Z_FRONT)
    s.show(s.word("WASH", ICE, 2), wash, mas, 26, 8, enter="pop", z=Z_WORD)
    s.show(s.emoji("💆", 18), mas, t1, 122, 10, enter="pop", z=Z_FRONT)
    s.show(s.word("MASSAGE", PINK, 2), mas, t1, 34, 8, enter="pop", z=Z_WORD)
    s.ring(mas, 92, 48, PINK, r=24)


def g_ending(s, t0, t1):
    c = s.cues
    end = t1 - 0.5
    s.show(s.word("MERRY", RED, 3), t0 + 0.5, end, GC, 10, enter="left", exit="fade", exit_s=1.5, z=Z_WORD)
    s.show(s.word("CHRISTMAS", GREEN, 2), t0 + 1.0, end, GC, 50, enter="right", exit="fade", exit_s=1.5, z=Z_WORD)
    s.show(s.emoji("🎄", 34), t0, end, 22, 32, enter="pop", exit="fade", exit_s=1.5)
    s.show(s.emoji(HIPPO, 30), t0, end, GC, 31, enter="pop", exit="fade", exit_s=1.5,
           hits=c.beats_in(t0 + 0.5, end - 1.6)[::2], amp=2)
    s.show(s.emoji("🎄", 34), t0, end, 118, 32, enter="pop", exit="fade", exit_s=1.5)
    s.twinkle(t0, t1, XMAS, count=25, fade=1.5)
    s.ring(t0, GC, 31, GOLD, r=60)


GARAGE = dict(intro=g_intro, want=g_want, wish=g_wish, only=g_only, toys=g_toys, play=g_play, gift=g_gift,
              santa=g_santa, chimney=g_chimney, door=g_door, easy=g_easy, morning=g_morning, stairs=g_stairs,
              joy=g_joy, eyes=g_eyes, hero=g_hero, animals=g_animals, parade=g_parade, love=g_love, skate=g_skate,
              gifts=g_gifts, tree=g_tree, garage=g_garage, ending=g_ending)


# ================================================================ 200x42 matrix: 8 bushes, 25 px each

def bx(i):
    return 12.5 + 25 * i


BY = 22


def b_intro(s, t0, t1):
    c = s.cues
    beats = c.beats_in(1.0, t1)
    tree = s.emoji("🎄", 24)
    for i in range(8):
        s.show(tree, beats[i] if i < len(beats) else t0, t1, bx(i), BY, enter="pop", enter_s=0.2)
    s.twinkle(0.2, t1, (WHITE, GOLD), count=4, fade=1.0)


def b_want(s, t0, t1):
    c = s.cues
    hip = c.w("hippo", t0)
    xm = c.w("christmas", hip)
    tree, h = s.emoji("🎄", 24), s.emoji(HIPPO, 22, flip=True)
    for i in range(8):
        s.show(tree, t0, hip + 0.06 * i, bx(i), BY, enter=None)
        s.show(h, hip + 0.06 * i, t1, bx(i), BY + 2, enter="pop", hits=c.beats_in(xm, t1)[i % 2::2], amp=3)
        s.ring(xm + 0.04 * i, bx(i), BY, GOLD, r=13, dur=0.5)


def b_wish(s, t0, t1):
    kid, bub, h = s.emoji(KID, 22), s.emoji("💭", 22), s.emoji(HIPPO, 12)
    for i in range(8):
        if i % 2 == 0:
            s.show(kid, t0 + 0.05 * i, t1, bx(i), BY, enter="bottom")
        else:
            s.show(bub, t0 + 0.3 + 0.05 * i, t1, bx(i), BY - 2, enter="pop")
            s.show(h, t0 + 0.6 + 0.05 * i, t1, bx(i), BY - 3, enter="pop", z=Z_FRONT)


def b_only(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    h = s.emoji(HIPPO, 24)
    for i in range(8):
        s.show(h, t0 + 0.05 * i, t1, bx(i), BY + 1, enter="pop", hits=beats[i % 2::2], amp=3)
    s.show(s.emoji("☝️", 22), t0, t1, bx(0), BY, enter="bottom", z=Z_FRONT)


def b_toys(s, t0, t1, doll, teddy, train):
    for (em, rng, (a, hit)) in (("🪆", range(0, 4), doll), ("🧸", range(4, 8), teddy)):
        for i in rng:
            s.show(s.emoji(em, 22), a + 0.05 * (i % 4), t1, bx(i), BY, enter="top", enter_s=0.25)
            s.show(s.emoji(NO, 24), hit + 0.04 * (i % 4), t1, bx(i), BY, enter="pop", enter_s=0.2, z=Z_FRONT)
    a, hit = train
    s.glide(s.emoji("🚂", 16), [(a - 0.6, 214, 36), (t1, 100, 36)], z=Z_FRONT + 1)


def b_play(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0 + 0.4, t1)
    kid, h = s.emoji(KID, 22), s.emoji(HIPPO, 24)
    for i in range(8):
        s.show(kid if i % 2 == 0 else h, t0, t1, bx(i), BY + 4, enter="bottom", hits=beats[i % 2::2], amp=2)
    ball = s.emoji("⚽", 7)
    for k, (x, y) in enumerate(zip(beats, beats[1:])):  # the ball hops along the row, one bush a beat
        i, j = k % 8, (k + 1) % 8
        if j == 0:
            continue
        s.glide(ball, [(x, bx(i), 8), ((x + y) / 2, (bx(i) + bx(j)) / 2, 2), (y, bx(j), 8)], z=Z_FRONT)


def b_gift(s, t0, t1):
    c = s.cues
    hip = c.w("hippo", t0)
    gift, h = s.emoji("🎁", 22), s.emoji(HIPPO, 24)
    for i in range(8):
        s.show(gift, t0 + 0.05 * i, hip, bx(i), BY, enter="top", exit="shrink", exit_s=0.15,
               hits=c.beats_in(t0 + 0.4, hip)[i % 2::2], amp=2)
        s.show(h, hip + 0.05 * i, t1, bx(i), BY + 1, enter="pop", hits=c.beats_in(hip + 0.4, t1)[i % 2::2], amp=3)
        s.ring(hip + 0.05 * i, bx(i), BY, GOLD, r=14, dur=0.5)
    s.twinkle(hip, hip + 2.5, (RED, GREEN, GOLD, BLUE, PINK), count=20, steps=20, fade=0.3)


def b_santa(s, t0, t1):
    c = s.cues
    mind = c.w("mind", t0)
    santa, ok = s.emoji("🎅", 24), s.emoji("👍", 22)
    for i in range(8):
        s.show(santa, t0 + 0.05 * i, mind, bx(i), BY, enter="top")
        s.show(ok, mind + 0.05 * i, t1, bx(i), BY, enter="pop", hits=c.beats_in(mind + 0.3, t1)[i % 2::2], amp=2)


def b_chimney(s, t0, t1):
    c = s.cues
    hit = c.w("chimney", t0)
    house = s.emoji("🏠", 24)
    for i in range(8):
        s.show(house, t0 + 0.06 * i, t1, bx(i), BY, enter="bottom", z=Z_BACK)
        s.show(s.emoji(NO, 12), hit + 0.04 * i, t1, bx(i) + 5, 10, enter="pop", z=Z_FRONT)
    s.snow(t0, t1, count=4)


def b_door(s, t0, t1):
    c = s.cues
    door = c.w("door", t0)
    s.show(s.emoji("🚪", 26), t0, t1, bx(7), BY, enter="fade", enter_s=0.4)
    h = s.emoji(HIPPO, 22, flip=True)
    s.glide(h, [(t0, bx(0), BY + 2), (c.w("bring", t0), bx(0), BY + 2), (door, bx(6), BY + 2), (t1, bx(6), BY + 2)])
    s.ring(door, bx(7), BY, GOLD, r=14)


def b_easy(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    ok = s.emoji("👍", 22)
    for i in range(8):
        s.show(ok, t0 + 0.05 * i, t1, bx(i), BY, enter="bottom", hits=beats[i % 2::2], amp=3)


def b_morning(s, t0, t1):
    c = s.cues
    xm = c.w("christmas", t0)
    s.glide(s.emoji("☀️", 22), [(t0, bx(0), 60), (xm, bx(0), BY), (t1, bx(0), BY)], z=Z_BACK)
    tree, gift = s.emoji("🎄", 24), s.emoji("🎁", 12)
    for i in range(1, 8):
        s.show(tree, xm + 0.06 * i, t1, bx(i), BY - 2, enter="bottom")
        s.show(gift, xm + 0.3 + 0.06 * i, t1, bx(i) + 6, 36, enter="pop", z=Z_FRONT)


def b_stairs(s, t0, t1):
    """The kid tiptoes from bush to bush, one a beat."""
    c = s.cues
    kid = s.emoji(KID, 18)
    beats = c.beats_in(t0 + 0.2, t1)
    pts = [(t0, bx(0), BY)]
    for k, b in enumerate(beats[:7]):
        pts += [(b, bx(k), BY), (b + 0.2, bx(k + 1), BY)]
    pts.append((t1, *pts[-1][1:]))
    s.glide(kid, pts)
    s.twinkle(t0, t1, (WHITE,), count=4)


def b_joy(s, t0, t1):
    c = s.cues
    joy, sur = c.w("joy", t0), c.w("surprise", t0)
    a, b = s.emoji("😃", 22), s.emoji("😲", 22)
    for i in range(8):
        s.show(a, joy + 0.04 * i if i % 2 == 0 else t0, t1 if i % 2 == 0 else sur, bx(i), BY, enter="pop")
        if i % 2:
            s.show(b, sur, t1, bx(i), BY, enter="pop", enter_s=0.2)
        s.ring(sur if i % 2 else joy, bx(i), BY, PINK if i % 2 else GOLD, r=14, dur=0.5)


def b_eyes(s, t0, t1):
    c = s.cues
    op, ey = c.w("open", t0), c.w("eyes", t0)
    shut, eye = closed_eye(s, 20), s.emoji("👁️", 20)
    for i in range(8):
        x = bx(i)
        s.show(shut, t0, op, x, BY, enter="fade", enter_s=0.3)
        s.pic(eye, op, ey, x, BY, scale=(20, 100))
        s.pic(shut, ey, ey + 0.15, x, BY)
        s.pic(eye, ey + 0.15, t1, x, BY)


def b_hero(s, t0, t1):
    c = s.cues
    h = s.emoji(HIPPO, 24, flip=True)
    cape = cape_r(s, 1)
    land = t0 + 1.6
    s.glide(h, [(t0, -20, 10), (land, bx(6), BY + 2), (t1, bx(6), BY + 2)])
    s.glide(cape, [(t0, -34, 8), (land, bx(6) - 14, BY), (t1, bx(6) - 14, BY)], z=Z_BACK)
    for i, ch in enumerate("HERO"):
        s.show(s.word(ch, GOLD, 4), land + 0.1 * i, t1, bx(i), BY, enter="pop", enter_s=0.15, z=Z_WORD)
    s.ring(land, bx(6), BY, GOLD, r=20)
    s.twinkle(land, t1, (RED, GOLD, GREEN, BLUE, PINK), count=15, steps=20)


def b_animals(s, t0, t1, croc, rhino_t, rhino):
    for i in range(4):
        s.show(s.emoji("🐊", 22), t0 + 0.05 * i, t1, bx(i), BY, enter="left", enter_s=0.3)
        s.show(s.emoji(NO, 24), croc + 0.04 * i, t1, bx(i), BY, enter="pop", z=Z_FRONT)
    for i in range(4, 8):
        s.show(s.emoji("🦏", 22), rhino_t + 0.05 * (i - 4), t1, bx(i), BY, enter="right", enter_s=0.3)
        s.show(s.emoji(NO, 24), rhino + 0.04 * (i - 4), t1, bx(i), BY, enter="pop", z=Z_FRONT)


def b_parade(s, t0, t1):
    c = s.cues
    h = s.emoji(HIPPO, 20)
    span = t1 - t0
    for k in range(6):
        a = t0 + k * span / 7
        s.glide(h, [(a, 214, BY + 4), (a + span * 0.7, -14, BY + 4)])
    like = c.w("like", t0)
    heart = s.emoji("❤️", 10)
    for i in range(8):
        s.show(heart, like + 0.05 * i, t1, bx(i), 6, enter="pop", hits=c.beats_in(like, t1)[i % 2::2], amp=1,
               z=Z_FRONT)


def b_love(s, t0, t1):
    c = s.cues
    me = c.w("me", t0)
    beats = c.beats_in(t0, t1)
    s.show(s.emoji(KID, 22), t0, t1, bx(0), BY, enter="left", hits=beats[0::2], amp=3)
    s.show(s.emoji(HIPPO, 24), t0, t1, bx(7), BY + 1, enter="right", hits=beats[1::2], amp=3)
    heart = s.emoji("❤️", 14)
    s.glide(heart, [(me - 1.0, bx(7), 10), (me, bx(0), 10)], z=Z_FRONT)
    for i in range(1, 7):
        s.show(s.emoji("❤️", 20), me + 0.05 * i, t1, bx(i), BY, enter="pop", hits=c.beats_in(me + 0.3, t1)[i % 2::2],
               amp=2)


def b_skate(s, t0, t1):
    s.show(pond(s, 196, 10), t0, t1, 100, 37, enter="fade", enter_s=0.8, z=Z_BACK)
    left, right = s.emoji(HIPPO, 20), s.emoji(HIPPO, 20, flip=True)
    lap, t, k = 4.0, t0, 0
    while t < t1 - 0.05:
        e = min(t + lap, t1)
        u = (e - t) / lap
        if k % 2 == 0:
            s.pic(right, t, e, 12, 26, to=(12 + 176 * u, 26))
        else:
            s.pic(left, t, e, 188, 26, to=(188 - 176 * u, 26))
        t, k = e, k + 1
    s.snow(t0, t1, count=4)


def b_gifts(s, t0, t1):
    c = s.cues
    gift = s.emoji("🎁", 22)
    order = [0, 7, 1, 6, 2, 5, 3, 4]
    for k, b in enumerate(c.beats_in(t0, t1)[:16:2]):
        i = order[k]
        s.show(gift, b, t1, bx(i), BY + 2, enter="top", enter_s=0.2)
        s.ring(b + 0.2, bx(i), BY + 2, GOLD, r=12, dur=0.4)


def b_tree(s, t0, t1):
    c = s.cues
    bars = c.bars_in(t0, t1)
    end_tree = bars[-2] if len(bars) >= 3 else t1
    tree = s.emoji("🎄", 24)
    for i in range(8):
        s.show(tree, t0 + 0.1 * i, end_tree, bx(i), BY, enter="fade", enter_s=0.6)
    s.twinkle(t0, end_tree, (RED, GOLD, BLUE, GREEN, WHITE), count=10, steps=25)
    swaps = c.beats_in(end_tree, t1)
    if swaps:
        keys = [s.emoji(HIPPO, 24), s.emoji("🎄", 24), s.emoji("🎁", 22)]
        for i in range(8):
            s.flash(keys[i % 3:] + keys[:i % 3], swaps, bx(i), BY, end=t1)


def b_garage(s, t0, t1):
    c = s.cues
    feed, wash, mas = c.w("feed", t0), c.w("wash", t0), c.w("massage", t0)
    g = garage_big(s, 24, 20)
    for i in range(8):
        s.show(g, t0 + 0.05 * i, feed, bx(i), BY, enter="fade", enter_s=0.5)
    for k, (em, a, b) in enumerate((("🍉", feed, wash), ("🧽", wash, mas), ("💆", mas, t1))):
        for i in range(8):
            s.show(s.emoji(em, 20), a + 0.04 * i, b, bx(i), BY, enter="pop", hits=c.beats_in(a + 0.3, b)[i % 2::2],
                   amp=2)


def b_ending(s, t0, t1):
    c = s.cues
    end = t1 - 0.5
    keys = [s.emoji("🎄", 24), s.emoji(HIPPO, 24)]
    beats = c.beats_in(t0 + 0.3, end - 1.6)
    for i in range(8):
        s.show(keys[i % 2], t0 + 0.05 * i, end, bx(i), BY, enter="pop", exit="fade", exit_s=1.5,
               hits=beats[i % 2::2], amp=2)
    s.twinkle(t0, t1, XMAS, count=10, fade=1.5)


BUSHES = dict(intro=b_intro, want=b_want, wish=b_wish, only=b_only, toys=b_toys, play=b_play, gift=b_gift,
              santa=b_santa, chimney=b_chimney, door=b_door, easy=b_easy, morning=b_morning, stairs=b_stairs,
              joy=b_joy, eyes=b_eyes, hero=b_hero, animals=b_animals, parade=b_parade, love=b_love, skate=b_skate,
              gifts=b_gifts, tree=b_tree, garage=b_garage, ending=b_ending)
