"""'I Want a Hippopotamus for Christmas' as SuperStar-style scenes on a 40x48 window matrix.

    cd scripts
    python matrix_scenes.py stories/scenes/hippopotamus_window.py SHOW/SONG.xsq \
        --model WINDOW --size 40x48 --out SHOW/SONG-MatrixScenes.xsq

The sequence has no Lyrics track: word times come from faster-whisper (stories/lyrics/hippopotamus_for_christmas.json)
and beats from librosa (..._beats.json). Pictures slide, pop and hop like SuperStar image actions; Morph bars sweep on
bars, Shockwave rings burst on the key words, Twinkle and Snowflakes sit behind.
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from matrix_scenes import Cues  # noqa: E402

PREFIX = "hippo_window"
LYRICS = Path(__file__).resolve().parents[1] / "lyrics"

RED, GREEN, WHITE, GOLD = (255, 30, 30), (30, 230, 60), (255, 255, 255), (255, 200, 30)
BLUE, PURPLE, PINK, ICE = (40, 90, 255), (190, 80, 255), (255, 80, 190), (140, 210, 255)
XMAS = (RED, GREEN, WHITE, GOLD)

HIPPO, KID, NO = "🦛", "🧒", "🚫"
Z_BG, Z_SWEEP, Z_RING, Z_BACK, Z_PIC, Z_FRONT, Z_WORD = 0, 10, 12, 18, 20, 25, 30


def cues(xsq):
    dur = float(ET.parse(xsq).getroot().findtext("head/sequenceDuration"))
    return Cues.from_files(LYRICS / "hippopotamus_for_christmas.json",
                           LYRICS / "hippopotamus_for_christmas_beats.json", dur)


# ---------------------------------------------------------------- drawn props

def stairs_img(s):
    def draw(d, im):
        for i in range(5):
            x0, y0 = i * 7, i * 5
            d.rectangle([x0, y0 + 3, 39, y0 + 4], fill=(200, 140, 80, 255))  # tread edge
            d.rectangle([x0, y0 + 5, 39, y0 + 7], fill=(120, 70, 40, 255))
    return s.drawn("stairs", 40, 33, draw)


def cape_img(s):
    def draw(d, im):
        d.polygon([(0, 3), (5, 0), (17, 6), (19, 14), (12, 12), (4, 15), (0, 9)], fill=(220, 20, 30, 255))
        d.line([(5, 0), (17, 6), (19, 14)], fill=(255, 100, 90, 255))
    return s.drawn("cape", 20, 16, draw)


def garage_img(s):
    def draw(d, im):
        d.polygon([(0, 8), (19, 0), (39, 8)], fill=(150, 40, 40, 255))  # roof
        d.rectangle([2, 8, 37, 25], fill=(170, 150, 120, 255))
        for x0 in (4, 21):
            d.rectangle([x0, 12, x0 + 14, 25], fill=(235, 235, 235, 255))
            for y in (15, 18, 21):
                d.line([(x0, y), (x0 + 14, y)], fill=(150, 150, 150, 255))
    return s.drawn("garage", 40, 26, draw)


def pond_img(s):
    def draw(d, im):
        d.ellipse([0, 0, 39, 9], fill=(120, 190, 255, 255))
        d.ellipse([4, 2, 35, 7], fill=(170, 220, 255, 255))
    return s.drawn("pond", 40, 10, draw)


# ---------------------------------------------------------------- scene builders

def bar_sweeps(s, t0, t1, colors=XMAS, every=1):
    """A bar across the whole matrix on each bar line, alternating sides and colours."""
    for i, b in enumerate(s.cues.bars_in(t0, t1)[::every]):
        s.sweep(b, min(b + 0.7, t1), colors[i % len(colors)], "left" if i % 2 == 0 else "right", z=Z_SWEEP)


def want_scene(s, t0, t1):
    """I want a hippopotamus for Christmas: words, then the hippo slides in on 'hippo' with a ring."""
    c = s.cues
    hip = c.w("hippo", t0)
    xmas = c.w("christmas", hip)
    s.show(s.word("I WANT"), t0, hip, 20, 6, enter="pop", z=Z_WORD)
    s.show(s.word("HIPPO", PURPLE, 2), hip, xmas + 0.3, 20, 7, enter="pop", z=Z_WORD)
    s.show(s.emoji(HIPPO, 30), hip, t1, 20, 31, enter="right", enter_s=0.45, exit="left",
           hits=c.beats_in(hip + 0.5, t1)[::2], amp=3)
    s.ring(hip + 0.4, 20, 31, PURPLE, r=26)
    s.show(s.emoji("🎄", 12), xmas, t1, 6, 40, enter="bottom", z=Z_BACK)
    s.show(s.emoji("🎄", 12), xmas + 0.15, t1, 34, 40, enter="bottom", z=Z_BACK)
    s.twinkle(t0, t1, (WHITE, GOLD), count=6)


def only_scene(s, t0, t1):
    """Only a hippopotamus will do: a big hippo hops on the beats; a ring and a sweep on 'do'."""
    c = s.cues
    do = c.w("do", t0)
    s.show(s.word("ONLY", GOLD, 2), c.w("only", t0 - 0.5), do, 20, 6, enter="pop", z=Z_WORD)
    s.show(s.emoji(HIPPO, 32), t0, t1, 20, 29, enter="pop", hits=c.beats_in(t0, t1)[::2], amp=3)
    s.ring(do, 20, 29, GOLD, r=28)
    s.sweep(do, do + 0.6, WHITE, "top", z=Z_SWEEP)
    s.twinkle(t0, t1, (WHITE, PURPLE), count=6)


def no_items(s, items):
    """[(emoji, t0, t1, hit)]: each drops in, then a red 'no' sign pops over it on the hit."""
    for em, t0, t1, hit in items:
        s.show(s.emoji(em, 26), t0, t1, 20, 26, enter="top", enter_s=0.25)
        s.show(s.emoji(NO, 32), hit, t1, 20, 26, enter="pop", enter_s=0.2, z=Z_FRONT)
        s.ring(hit, 20, 26, RED, r=24, dur=0.5)


def play_scene(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    s.show(s.emoji(KID, 16), t0, t1, 9, 36, enter="left", hits=beats[0::2], amp=3)
    s.show(s.emoji(HIPPO, 22), t0, t1, 28, 34, enter="right", hits=beats[1::2], amp=3)
    for i, b in enumerate(beats[1::2]):
        if b + 1.2 <= t1:
            s.glide(s.emoji("❤️", 7), [(b, 12 + 8 * (i % 3), 30), (b + 1.2, 10 + 9 * (i % 3), 4)], z=Z_FRONT)
    play = c.w("play", t0)
    s.show(s.word("PLAY", GREEN, 2), play, t1, 20, 7, enter="pop", z=Z_WORD)
    s.snow(t0, t1, count=3)


def gift_scene(s, t0, t1):
    """The present shakes until 'hippo', then it's a hippo in a burst of colour."""
    c = s.cues
    hip = c.w("hippo", t0)
    s.show(s.word("I WANT"), t0, hip, 20, 6, enter="pop", z=Z_WORD)
    s.show(s.emoji("🎁", 28), t0, hip, 20, 28, enter="top", exit="shrink", exit_s=0.15,
           hits=c.beats_in(t0 + 0.4, hip), amp=2)
    s.show(s.emoji(HIPPO, 30), hip, t1, 20, 29, enter="pop", hits=c.beats_in(hip + 0.4, t1)[::2], amp=3,
           exit="right")
    s.ring(hip, 20, 28, GOLD, r=30)
    s.ring(hip + 0.2, 20, 28, RED, r=30)
    s.twinkle(hip, hip + 2.5, (RED, GREEN, GOLD, BLUE, PINK), count=30, steps=20, fade=0.3)
    s.show(s.word("XMAS", RED, 2), c.w("christmas", hip), t1, 20, 7, enter="pop", z=Z_WORD)


def santa_scene(s, t0, t1):
    c = s.cues
    s.show(s.emoji("🎅", 30), t0, t1, 20, 25, enter="left", hits=c.beats_in(t0 + 0.5, t1)[::2], amp=2)
    s.show(s.emoji("👍", 12), c.w("mind", t0) - 0.2, t1, 33, 40, enter="pop", z=Z_FRONT)
    s.snow(t0, t1, count=4)


def chimney_scene(s, t0, t1):
    c = s.cues
    s.show(s.emoji("🏠", 34), t0, t1, 20, 28, enter="fade", enter_s=0.6)
    hit = c.w("chimney", t0)
    s.show(s.emoji(NO, 14), hit, t1, 28, 13, enter="pop", z=Z_FRONT)
    s.ring(hit, 28, 13, RED, r=14, dur=0.5)
    s.snow(t0, t1, count=5)


def door_scene(s, t0, t1):
    c = s.cues
    s.show(s.emoji("🚪", 26), t0, t1, 28, 29, enter="fade", enter_s=0.4)
    walk = c.w("bring", t0)
    door = c.w("door", t0)
    h = s.emoji(HIPPO, 18, flip=True)
    s.glide(h, [(walk, -10, 36), (door, 16, 36), (t1, 16, 36)])
    s.ring(door, 28, 29, GOLD, r=20)


def easy_scene(s, t0, t1):
    c = s.cues
    s.show(s.word("EASY", GREEN, 2), c.w("easy", t0), t1, 20, 9, enter="pop", z=Z_WORD)
    s.show(s.emoji("👍", 22), t0 + 0.3, t1, 20, 32, enter="bottom", hits=c.beats_in(t0 + 0.8, t1), amp=2)
    bar_sweeps(s, t0, t1)


def morning_scene(s, t0, t1):
    c = s.cues
    xm = c.w("christmas", t0)
    s.glide(s.emoji("☀️", 20), [(t0, 20, 58), (xm, 20, 15), (t1, 20, 15)], z=Z_BACK)
    s.show(s.emoji("🎄", 20), xm, t1, 9, 36, enter="bottom")
    s.show(s.emoji("🎁", 10), xm + 0.3, t1, 31, 42, enter="pop")
    s.show(s.emoji("🎁", 8), xm + 0.5, t1, 22, 43, enter="pop")
    s.twinkle(t0, t1, (GOLD, WHITE), count=8)


def stairs_scene(s, t0, t1):
    c = s.cues
    s.show(stairs_img(s), t0, t1, 20, 31.5, enter="fade", enter_s=0.5, z=Z_BACK)
    kid = s.emoji(KID, 12)
    beats = c.beats_in(t0 + 0.6, t1 - 0.3)[:5]
    pts = [(t0, 4, 12)]
    for i, b in enumerate(beats):  # one step down per beat
        x0, y0 = 4 + 7 * i, 12 + 5 * i
        pts += [(b, x0, y0), (b + 0.2, x0 + 7, y0 + 5)]
    pts.append((t1, pts[-1][1], pts[-1][2]))
    s.glide(kid, pts)


def joy_scene(s, t0, t1):
    c = s.cues
    joy, sur = c.w("joy", t0), c.w("surprise", t0)
    s.show(s.emoji("😃", 30), t0, sur, 20, 28, enter="pop")
    s.show(s.emoji("😲", 30), sur, t1, 20, 28, enter="pop", enter_s=0.2)
    s.show(s.word("JOY", GOLD, 2), joy, sur, 20, 6, enter="pop", z=Z_WORD)
    s.show(s.word("WOW", PINK, 2), sur, t1, 20, 6, enter="pop", z=Z_WORD)
    s.ring(joy, 20, 28, GOLD, r=28)
    s.ring(sur, 20, 28, PINK, r=28)


def eyes_scene(s, t0, t1):
    c = s.cues
    op = c.w("open", t0)
    s.show(s.emoji("😴", 30), t0, op, 20, 26, enter="fade", enter_s=0.3)
    s.show(s.emoji("😳", 30), op, t1, 20, 26, enter="pop", enter_s=0.2, hits=[c.w("eyes", op)], amp=3)
    s.ring(op, 20, 26, WHITE, r=26)


def hero_scene(s, t0, t1):
    c = s.cues
    hero = c.w("hero", t0)
    s.show(cape_img(s), t0 + 0.25, t1, 30, 30, enter="pop", z=Z_BACK)
    s.show(s.emoji(HIPPO, 30), t0, t1, 18, 30, enter="pop", hits=c.beats_in(t0 + 0.6, t1)[::2], amp=2)
    s.show(s.word("HERO", GOLD, 2), hero, t1, 20, 6, enter="pop", z=Z_WORD)
    s.ring(hero, 18, 30, GOLD, r=30)
    for i, b in enumerate(c.beats_in(t0, t1)):
        s.sweep(b, b + 0.5, (RED, GOLD, GREEN, BLUE, PURPLE)[i % 5], "left" if i % 2 else "right", z=Z_SWEEP)
    s.twinkle(hero, t1, (RED, GOLD, GREEN, BLUE, PINK), count=20, steps=20)


def no_animals(s, t0, t1, croc_hit, rhino_t, rhino_hit):
    s.show(s.emoji("🐊", 32), t0, rhino_t, 20, 27, enter="right", enter_s=0.4)
    s.show(s.emoji(NO, 34), croc_hit, rhino_t, 20, 27, enter="pop", z=Z_FRONT)
    s.ring(croc_hit, 20, 27, RED, r=26)
    s.show(s.emoji("🦏", 30, flip=True), rhino_t, t1, 20, 27, enter="left", enter_s=0.3)
    s.show(s.emoji(NO, 34), rhino_hit, t1, 20, 27, enter="pop", z=Z_FRONT)
    s.ring(rhino_hit, 20, 27, RED, r=26)


def parade_scene(s, t0, t1):
    """Three hippos march right to left across, hopping on alternate beats."""
    c = s.cues
    h = s.emoji(HIPPO, 16)
    span = t1 - t0
    for k in range(3):
        a = t0 + k * span / 4
        s.glide(h, [(a, 50, 34), (a + span * 0.6, -10, 34)], z=Z_PIC)
    s.show(s.word("LIKE"), c.w("like", t0), t1, 20, 8, enter="pop", z=Z_WORD)
    s.show(s.emoji("❤️", 9), c.w("like", t0) + 0.1, t1, 20, 17, enter="pop", hits=c.beats_in(t0, t1), amp=1)
    s.snow(t0, t1, count=4)


def love_scene(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    s.show(s.emoji(KID, 16), t0, t1, 10, 34, enter="left", hits=beats[0::2], amp=3)
    s.show(s.emoji(HIPPO, 22), t0, t1, 28, 33, enter="right", hits=beats[1::2], amp=3)
    me = c.w("me", t0)
    s.show(s.emoji("❤️", 14), me, t1, 20, 12, enter="pop", hits=c.beats_in(me + 0.3, t1), amp=2, z=Z_FRONT)
    s.ring(me, 20, 12, PINK, r=24)


def skate_scene(s, t0, t1):
    """Instrumental: the hippo skates back and forth on a pond under the moon."""
    s.show(pond_img(s), t0, t1, 20, 41, enter="fade", enter_s=0.8, z=Z_BACK)
    s.show(s.emoji("🌙", 9), t0, t1, 33, 7, enter="fade", enter_s=0.8, z=Z_BACK)
    left, right = s.emoji(HIPPO, 16), s.emoji(HIPPO, 16, flip=True)
    lap = 2.2
    t, k = t0, 0
    while t < t1 - 0.05:
        e = min(t + lap, t1)
        if k % 2 == 0:
            s.pic(right, t, e, 8, 34, to=(32, 34))
        else:
            s.pic(left, t, e, 32, 34, to=(8, 34))
        t, k = e, k + 1
    s.snow(t0, t1, count=5)
    s.twinkle(t0, t1, (WHITE,), count=4)


def gifts_scene(s, t0, t1):
    """Instrumental: presents drop in on each bar and stack up, with sweeps and rings."""
    bars = s.cues.bars_in(t0, t1)
    spots = [(9, 41, "🎁", 14), (30, 41, "🎁", 16), (20, 39, "🎁", 18), (12, 27, "⭐", 10), (28, 27, "🔔", 10),
             (20, 14, "🎀", 14)]
    for (x, y, em, px), b in zip(spots, bars):
        s.show(s.emoji(em, px), b, t1, x, y, enter="top", enter_s=0.3, hits=s.cues.beats_in(b + 0.5, t1)[::4], amp=1)
        s.ring(b + 0.3, x, y, GOLD, r=12, dur=0.5)
    bar_sweeps(s, t0, t1, (RED, GREEN))


def tree_scene(s, t0, t1):
    """Instrumental: a big tree with twinkling lights; the star tops it; then quick hippo/tree swaps."""
    c = s.cues
    bars = c.bars_in(t0, t1)
    end_tree = bars[-2] if len(bars) >= 3 else t1
    s.show(s.emoji("🎄", 36), t0, end_tree, 20, 27, enter="fade", enter_s=1.0)
    s.show(s.emoji("⭐", 10), bars[1] if len(bars) > 1 else t0, end_tree, 20, 7, enter="top", z=Z_FRONT)
    s.twinkle(t0, end_tree, (RED, GOLD, BLUE, GREEN, WHITE), count=10, steps=25)
    bar_sweeps(s, t0, end_tree, (GOLD, WHITE))
    swaps = c.beats_in(end_tree, t1)
    if swaps:
        s.flash([s.emoji(HIPPO, 30), s.emoji("🎄", 30), s.emoji("🎁", 26)], swaps, 20, 27, end=t1)
        for i, b in enumerate(swaps):
            s.ring(b, 20, 27, XMAS[i % 4], r=26, dur=0.5)


def garage_scene(s, t0, t1):
    c = s.cues
    s.show(garage_img(s), t0, t1, 20, 33, enter="fade", enter_s=0.6, z=Z_BACK)
    him = c.w("him", t0)
    feed, wash, mas = c.w("feed", t0), c.w("wash", t0), c.w("massage", t0)
    h = s.emoji(HIPPO, 14)
    s.glide(h, [(him, 50, 40), (him + 1.0, 28, 40), (t1, 28, 40)], z=Z_PIC)
    s.show(s.emoji("🍉", 10), feed, wash, 14, 12, enter="pop", hits=[feed + 0.3], z=Z_FRONT)
    s.show(s.emoji("🧽", 10), wash, mas, 26, 12, enter="pop", hits=c.beats_in(wash + 0.2, mas), amp=2, z=Z_FRONT)
    s.show(s.emoji("💆", 18), mas, t1, 13, 12, enter="pop", z=Z_FRONT)
    s.ring(mas, 13, 12, PINK, r=14)
    s.show(s.word("ROOM", ICE, 2), c.w("room", t0), feed, 20, 4, enter="pop", z=Z_WORD)


def ending_scene(s, t0, t1):
    c = s.cues
    s.show(s.emoji(HIPPO, 30), t0, t1 - 0.5, 20, 30, enter="pop", hits=c.beats_in(t0 + 0.5, t1 - 1)[::2], amp=2)
    s.show(s.word("MERRY", RED), t0 + 0.5, t1 - 0.5, 20, 5, enter="left", z=Z_WORD)
    s.show(s.word("XMAS", GREEN), t0 + 1.0, t1 - 0.5, 20, 12, enter="right", z=Z_WORD)
    s.twinkle(t0, t1, (RED, GREEN, GOLD, WHITE), count=20, fade=1.5)
    s.ring(t0, 20, 30, GOLD, r=30)


# ---------------------------------------------------------------- story

def build(s):
    c = s.cues
    w = c.w

    # ---- intro: tree fades in under twinkle, sweeps on the bars, a present drops
    s.twinkle(0.2, 7.7, (WHITE, GOLD), count=8, fade=1.0)
    s.show(s.emoji("🎄", 28), 0.4, 7.7, 20, 25, enter="fade", enter_s=1.5)
    s.show(s.emoji("🎁", 12), 4.8, 7.7, 30, 40, enter="top", hits=c.beats_in(5.2, 7.7)[::2], amp=1, z=Z_FRONT)
    bar_sweeps(s, 0.4, 7.6, (RED, GREEN))

    # ---- verse 1
    want_scene(s, w("I", 7.5), w("only", 11.0) - 0.1)
    s.show(s.emoji(KID, 16), w("only", 11.0) - 0.1, 13.4, 10, 36, enter="bottom")
    s.show(s.emoji("💭", 22), 11.9, 13.4, 26, 15, enter="pop")
    s.show(s.emoji(HIPPO, 12), 12.2, 13.4, 26, 14, enter="pop", z=Z_FRONT)
    only_scene(s, 13.4, w("don't", 16.0) - 0.1)
    no_items(s, [("🪆", 17.3, 19.55, w("doll", 17.0)), ("🧸", 19.55, 20.35, w("dink", 19.5)),
                 ("🚂", 20.35, 21.05, w("toy", 20.3))])
    play_scene(s, 21.05, w("I", 25.0) - 0.05)
    gift_scene(s, w("I", 25.0) - 0.05, 30.1)
    santa_scene(s, 30.1, w("he", 33.5) - 0.1)
    chimney_scene(s, w("he", 33.5) - 0.1, w("just", 37.8) - 0.05)
    door_scene(s, w("just", 37.8) - 0.05, w("that", 40.0) - 0.05)
    easy_scene(s, w("that", 40.0) - 0.05, w("I", 42.0) - 0.05)

    # ---- bridge
    morning_scene(s, w("I", 42.0) - 0.05, w("creeping", 46.5) - 0.05)
    stairs_scene(s, w("creeping", 46.5) - 0.05, w("oh", 50.0) - 0.05)
    joy_scene(s, w("oh", 50.0) - 0.05, w("when", 52.5) - 0.05)
    eyes_scene(s, w("when", 52.5) - 0.05, w("hippo", 55.3) - 0.05)
    hero_scene(s, w("hippo", 55.3) - 0.05, w("I", 59.5) - 0.1)

    # ---- chorus
    want_scene(s, w("I", 59.5) - 0.1, w("only", 63.5) - 0.1)
    only_scene(s, w("only", 63.5) - 0.1, w("no", 67.8) - 0.1)
    no_animals(s, w("no", 67.8) - 0.1, 72.2, w("crocodiles", 68.0), w("no", 70.0) - 0.05,
               w("rhinoceroses", 70.0) + 0.3)
    parade_scene(s, 72.2, w("and", 75.8) - 0.05)
    love_scene(s, w("and", 75.8) - 0.05, 80.4)

    # ---- instrumental
    skate_scene(s, 80.4, 89.0)
    gifts_scene(s, 89.0, 97.5)
    tree_scene(s, 97.5, w("there's", 105.0) - 0.1)

    # ---- verse 2
    garage_scene(s, w("there's", 105.0) - 0.1, w("I", 113.5) - 0.05)
    morning_scene(s, w("I", 113.5) - 0.05, w("creeping", 118.0) - 0.05)
    stairs_scene(s, w("creeping", 118.0) - 0.05, w("oh", 121.5) - 0.05)
    joy_scene(s, w("oh", 121.5) - 0.05, w("when", 124.0) - 0.05)
    eyes_scene(s, w("when", 124.0) - 0.05, w("hippo", 126.8) - 0.05)
    hero_scene(s, w("hippo", 126.8) - 0.05, w("I", 130.5) - 0.1)

    # ---- last chorus
    want_scene(s, w("I", 130.5) - 0.1, w("only", 134.0) - 0.1)
    only_scene(s, w("only", 134.0) - 0.1, w("no", 139.0) - 0.1)
    no_animals(s, w("no", 139.0) - 0.1, w("I", 143.0) - 0.05, w("crocodiles", 139.5), w("or", 141.0) - 0.05,
               w("rhinoceroses", 141.0) + 0.3)
    parade_scene(s, w("I", 143.0) - 0.05, w("and", 147.3) - 0.05)
    love_scene(s, w("and", 147.3) - 0.05, 151.3)
    ending_scene(s, 151.3, c.duration)
