"""'I Want a Hippopotamus for Christmas' across both 40x48 window matrices as one stage.

    cd scripts
    python matrix_scenes.py stories/scenes/hippopotamus_windows.py SHOW/SONG.xsq \
        --model LEFT_WINDOW,RIGHT_WINDOW --out SHOW/SONG-MatrixScenes.xsq

Stage coordinates come from the layout: the left window is columns 0-39, then 24 LEDs of wall, then the
right window at 64-103 (48 rows). The windows play off each other: the kid on one and the hippo on the other,
the ball tossed between them, the hippo walking behind the wall from one window into the next, one staircase and
one two-car garage spanning both, the two windows as a pair of eyes.
"""

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from hippopotamus_window import (BLUE, GOLD, GREEN, HIPPO, ICE, KID, NO, PINK, PURPLE, RED, WHITE, XMAS,  # noqa: E402
                                 Z_BACK, Z_FRONT, Z_PIC, Z_WORD, cape_img, cues)

PREFIX = "hippo_windows"
cues = cues  # same word/beat times as the one-window story

L, C = 20, 84  # x of the two window centres on the stage
CY = 24
OFF_L, OFF_R = -24, 128  # past the stage edges


# ---------------------------------------------------------------- stage-wide props

def stairs_img(s, n=6, w=18, h=6):
    def draw(d, im):
        for i in range(n):
            x0, y0 = i * w, i * h
            d.rectangle([x0, y0, im.width - 1, y0 + 1], fill=(200, 140, 80, 255))
            d.rectangle([x0, y0 + 2, im.width - 1, y0 + h - 1], fill=(120, 70, 40, 255))
    return s.drawn("stairs_wide", 104, n * h, draw)


def pond_img(s):
    def draw(d, im):
        d.ellipse([0, 0, 103, 9], fill=(120, 190, 255, 255))
        d.ellipse([8, 2, 95, 7], fill=(170, 220, 255, 255))
    return s.drawn("pond_wide", 104, 10, draw)


def garage_img(s):
    """A two-car garage as wide as the stage: one door in each window."""
    def draw(d, im):
        d.polygon([(0, 10), (52, 0), (103, 10)], fill=(150, 40, 40, 255))
        d.rectangle([2, 10, 101, 29], fill=(170, 150, 120, 255))
        for cx in (L, C):
            d.rectangle([cx - 14, 13, cx + 14, 29], fill=(235, 235, 235, 255))
            for y in (17, 21, 25):
                d.line([(cx - 14, y), (cx + 14, y)], fill=(150, 150, 150, 255))
    return s.drawn("garage_wide", 104, 30, draw)


def closed_eye_img(s):
    def draw(d, im):
        d.arc([0, -8, 29, 12], 20, 160, fill=(255, 220, 180, 255), width=2)
        for x in (5, 11, 18, 24):
            d.line([(x, 10), (x - 1 if x < 15 else x + 1, 13)], fill=(255, 220, 180, 255))
    return s.drawn("eye_closed", 30, 14, draw)


def cape_right(s):
    key = cape_img(s)
    return s.image("cape_r", s.images[key].transpose(Image.FLIP_LEFT_RIGHT))


# ---------------------------------------------------------------- scenes

def bar_sweeps(s, t0, t1, colors=XMAS):
    """A bar across both windows on each bar line - it crosses one window, then the other."""
    for i, b in enumerate(s.cues.bars_in(t0, t1)):
        s.sweep(b, min(b + 1.4, t1), colors[i % len(colors)], "left" if i % 2 == 0 else "right")


def want_scene(s, t0, t1):
    """'I want' on the left; the hippo trots in on 'hippo', then crosses behind the wall into the right window on
    'Christmas', where trees pop up to meet it."""
    c = s.cues
    hip = c.w("hippo", t0)
    xmas = c.w("christmas", hip)
    s.show(s.word("I WANT"), t0, hip, L, 8, enter="pop", z=Z_WORD)
    s.show(s.word("HIPPO", PURPLE, 2), hip, t1, L, 8, enter="pop", z=Z_WORD)
    h = s.emoji(HIPPO, 26, flip=True)
    s.glide(h, [(hip, OFF_L, 32), (hip + 0.45, L, 32), (xmas, L, 32), (xmas + 0.9, C, 32), (t1, C, 32)])
    s.ring(hip + 0.4, L, 32, PURPLE, r=26)
    s.ring(xmas + 0.9, C, 32, GOLD, r=26)
    s.show(s.emoji("🎄", 14), xmas + 0.5, t1, C - 13, 38, enter="bottom", z=Z_BACK)
    s.show(s.emoji("🎄", 14), xmas + 0.65, t1, C + 13, 38, enter="bottom", z=Z_BACK)
    s.twinkle(t0, t1, (WHITE, GOLD), count=6)


def wish_scene(s, t0, t1):
    """The kid in the left window dreams; the dream bubble with the hippo fills the right one."""
    s.show(s.emoji(KID, 22), t0, t1, L, 32, enter="bottom")
    s.show(s.emoji("💭", 34), t0 + 0.4, t1, C, 22, enter="pop")
    s.show(s.emoji(HIPPO, 18), t0 + 0.8, t1, C, 20, enter="pop", z=Z_FRONT)


def only_scene(s, t0, t1):
    c = s.cues
    do = c.w("do", t0)
    s.show(s.word("ONLY", GOLD, 2), c.w("only", t0 - 0.5), t1, L, 14, enter="pop", z=Z_WORD)
    s.show(s.emoji("☝️", 18), t0 + 0.3, t1, L, 34, enter="bottom", hits=c.beats_in(t0 + 0.6, t1)[1::2], amp=2)
    s.show(s.emoji(HIPPO, 32), t0, t1, C, 29, enter="pop", hits=c.beats_in(t0, t1)[::2], amp=3)
    s.ring(do, C, 29, GOLD, r=28)
    s.ring(do, L, 34, GOLD, r=20)
    s.sweep(do, do + 0.6, WHITE, "top")
    s.twinkle(t0, t1, (WHITE, PURPLE), count=6)


def no_items(s, items):
    """[(emoji, x, t0, t1, hit)]: windows take turns - each item drops into its window and is crossed out."""
    for em, x, t0, t1, hit in items:
        s.show(s.emoji(em, 26), t0, t1, x, 26, enter="top", enter_s=0.25)
        s.show(s.emoji(NO, 32), hit, t1, x, 26, enter="pop", enter_s=0.2, z=Z_FRONT)
        s.ring(hit, x, 26, RED, r=24, dur=0.5)


def play_scene(s, t0, t1):
    """Kid left, hippo right, a ball tossed between them over the wall on the beats."""
    c = s.cues
    beats = c.beats_in(t0 + 0.4, t1)
    s.show(s.emoji(KID, 18), t0, t1, L, 34, enter="left", hits=beats[0::2], amp=3)
    s.show(s.emoji(HIPPO, 24), t0, t1, C, 33, enter="right", hits=beats[1::2], amp=3)
    ball = s.emoji("⚽", 7)
    a, b = (L + 8, 26), (C - 10, 26)
    for i, (x, y) in enumerate(zip(beats, beats[1:])):
        frm, to = (a, b) if i % 2 == 0 else (b, a)
        mid = (x + y) / 2
        s.glide(ball, [(x, *frm), (mid, (frm[0] + to[0]) / 2, 4), (y, *to)], z=Z_FRONT)
    s.show(s.word("PLAY", GREEN, 2), c.w("play", t0), t1, C, 7, enter="pop", z=Z_WORD)
    s.snow(t0, t1, count=3)


def gift_scene(s, t0, t1):
    """The present in the right window shakes until 'hippo' and becomes the hippo; the left window spells it out."""
    c = s.cues
    hip = c.w("hippo", t0)
    xm = c.w("christmas", hip)
    s.show(s.word("I WANT"), t0, hip, L, 20, enter="pop", z=Z_WORD)
    s.show(s.word("HIPPO", PURPLE, 2), hip, xm, L, 20, enter="pop", z=Z_WORD)
    s.show(s.word("XMAS", RED, 2), xm, t1, L, 8, enter="pop", z=Z_WORD)
    s.show(s.emoji("🎄", 22), xm + 0.1, t1, L, 33, enter="bottom")
    s.show(s.emoji("🎁", 28), t0, hip, C, 28, enter="top", exit="shrink", exit_s=0.15,
           hits=c.beats_in(t0 + 0.4, hip), amp=2)
    s.show(s.emoji(HIPPO, 30), hip, t1, C, 29, enter="pop", hits=c.beats_in(hip + 0.4, t1)[::2], amp=3)
    s.ring(hip, C, 28, GOLD, r=30)
    s.ring(hip + 0.2, C, 28, RED, r=30)
    s.twinkle(hip, hip + 2.5, (RED, GREEN, GOLD, BLUE, PINK), count=30, steps=20, fade=0.3)


def santa_scene(s, t0, t1):
    c = s.cues
    mind = c.w("mind", t0)
    s.show(s.emoji("🎅", 30), t0, t1, L, 25, enter="left", hits=c.beats_in(t0 + 0.5, t1)[::2], amp=2)
    s.show(s.emoji("👍", 26), mind - 0.2, t1, C, 26, enter="right", hits=c.beats_in(mind + 0.3, t1), amp=2)
    s.ring(mind, C, 26, GREEN, r=24)
    s.snow(t0, t1, count=4)


def chimney_scene(s, t0, t1):
    c = s.cues
    s.show(s.emoji(HIPPO, 24, flip=True), t0, t1, L, 34, enter="left", hits=c.beats_in(t0 + 0.5, t1)[::2], amp=2)
    s.show(s.emoji("🏠", 34), t0, t1, C, 28, enter="fade", enter_s=0.6)
    hit = c.w("chimney", t0)
    s.show(s.emoji(NO, 14), hit, t1, C + 8, 13, enter="pop", z=Z_FRONT)
    s.ring(hit, C + 8, 13, RED, r=14, dur=0.5)
    s.snow(t0, t1, count=5)


def door_scene(s, t0, t1):
    """The hippo walks out of the left window, behind the wall, and up to the front door in the right one."""
    c = s.cues
    s.show(s.emoji("🚪", 26), t0, t1, C + 6, 29, enter="fade", enter_s=0.4)
    door = c.w("door", t0)
    h = s.emoji(HIPPO, 18, flip=True)
    s.glide(h, [(t0, L, 36), (c.w("bring", t0), L, 36), (door, C - 10, 36), (t1, C - 10, 36)])
    s.ring(door, C + 6, 29, GOLD, r=20)


def easy_scene(s, t0, t1):
    c = s.cues
    s.show(s.word("EASY", GREEN, 2), c.w("easy", t0), t1, L, 24, enter="pop", z=Z_WORD)
    s.show(s.emoji("👍", 26), t0 + 0.3, t1, C, 26, enter="bottom", hits=c.beats_in(t0 + 0.8, t1), amp=2)
    bar_sweeps(s, t0, t1)


def morning_scene(s, t0, t1):
    """The sun comes up in the left window; the tree and presents wait in the right one."""
    c = s.cues
    xm = c.w("christmas", t0)
    s.glide(s.emoji("☀️", 26), [(t0, L, 62), (xm, L, 22), (t1, L, 22)], z=Z_BACK)
    s.show(s.emoji("🎄", 30), xm, t1, C, 24, enter="bottom")
    s.show(s.emoji("🎁", 12), xm + 0.3, t1, C - 11, 41, enter="pop", z=Z_FRONT)
    s.show(s.emoji("🎁", 10), xm + 0.5, t1, C + 12, 42, enter="pop", z=Z_FRONT)
    s.twinkle(t0, t1, (GOLD, WHITE), count=8)


def stairs_scene(s, t0, t1):
    """One staircase from the top of the left window down to the bottom of the right one; the kid creeps down a
    step per beat, out of sight for the steps behind the wall."""
    c = s.cues
    n, w, h = 6, 18, 6
    top = 48 - n * h
    s.show(stairs_img(s, n, w, h), t0, t1, 52, top + n * h / 2, enter="fade", enter_s=0.5, z=Z_BACK)
    kid = s.emoji(KID, 12)
    beats = c.beats_in(t0 + 0.4, t1 - 0.2)[: n - 1]
    pos = [(w * i + 9, top + h * i - 6) for i in range(n)]
    pts = [(t0, *pos[0])]
    for i, b in enumerate(beats):
        pts += [(b, *pos[i]), (b + 0.2, *pos[i + 1])]
    pts.append((t1, *pts[-1][1:]))
    s.glide(kid, pts)


def joy_scene(s, t0, t1):
    c = s.cues
    joy, sur = c.w("joy", t0), c.w("surprise", t0)
    s.show(s.emoji("😃", 30), t0, t1, L, 28, enter="pop")
    s.show(s.emoji("😲", 30), sur, t1, C, 28, enter="pop", enter_s=0.2)
    s.show(s.word("JOY", GOLD, 2), joy, t1, L, 6, enter="pop", z=Z_WORD)
    s.show(s.word("WOW", PINK, 2), sur, t1, C, 6, enter="pop", z=Z_WORD)
    s.ring(joy, L, 28, GOLD, r=28)
    s.ring(sur, C, 28, PINK, r=28)


def eyes_scene(s, t0, t1):
    """The two windows are a pair of eyes: closed, then they open on 'open' and blink on 'eyes'."""
    c = s.cues
    op, ey = c.w("open", t0), c.w("eyes", t0)
    shut = closed_eye_img(s)
    eye = s.emoji("👁️", 34)
    for x in (L, C):
        s.show(shut, t0, op, x, 26, enter="fade", enter_s=0.3)
        s.pic(eye, op, ey, x, 26, scale=(20, 100))
        s.pic(shut, ey, ey + 0.15, x, 26)
        s.pic(eye, ey + 0.15, t1, x, 26)
        s.ring(op, x, 26, WHITE, r=26)


def hero_scene(s, t0, t1):
    """The hero hippo flies in across both windows, cape streaming, and lands in the right one."""
    c = s.cues
    hero = c.w("hero", t0)
    h = s.emoji(HIPPO, 28, flip=True)
    cape = cape_right(s)
    land = t0 + 1.4
    s.glide(h, [(t0, OFF_L, 18), (land, C + 2, 30), (t1, C + 2, 30)])
    s.glide(cape, [(t0, OFF_L - 12, 16), (land, C - 10, 28), (t1, C - 10, 28)], z=Z_BACK)
    s.show(s.word("HERO", GOLD, 2), hero, t1, L, 24, enter="pop", z=Z_WORD)
    s.ring(land, C, 30, GOLD, r=30)
    for i, b in enumerate(c.beats_in(t0, t1)):
        s.sweep(b, b + 1.0, (RED, GOLD, GREEN, BLUE, PURPLE)[i % 5], "left" if i % 2 else "right")
    s.twinkle(hero, t1, (RED, GOLD, GREEN, BLUE, PINK), count=20, steps=20)


def no_animals(s, t0, t1, croc_hit, rhino_t, rhino_hit):
    """The crocodile in the left window, then the rhino in the right one - both stay crossed out."""
    s.show(s.emoji("🐊", 32), t0, t1, L, 27, enter="left", enter_s=0.4)
    s.show(s.emoji(NO, 34), croc_hit, t1, L, 27, enter="pop", z=Z_FRONT)
    s.ring(croc_hit, L, 27, RED, r=26)
    s.show(s.emoji("🦏", 30), rhino_t, t1, C, 27, enter="right", enter_s=0.3)
    s.show(s.emoji(NO, 34), rhino_hit, t1, C, 27, enter="pop", z=Z_FRONT)
    s.ring(rhino_hit, C, 27, RED, r=26)


def parade_scene(s, t0, t1):
    """Hippos march right to left across both windows."""
    c = s.cues
    h = s.emoji(HIPPO, 16)
    span = t1 - t0
    for k in range(4):
        a = t0 + k * span / 5
        s.glide(h, [(a, OFF_R, 36), (a + span * 0.75, OFF_L, 36)], z=Z_PIC)
    s.show(s.word("LIKE", WHITE, 2), c.w("like", t0), t1, L, 12, enter="pop", z=Z_WORD)
    s.show(s.emoji("❤️", 16), c.w("like", t0) + 0.1, t1, C, 14, enter="pop", hits=c.beats_in(t0, t1), amp=1)
    s.snow(t0, t1, count=4)


def love_scene(s, t0, t1):
    """Kid left, hippo right; on 'me' a heart flies from the hippo over the wall to the kid."""
    c = s.cues
    beats = c.beats_in(t0, t1)
    s.show(s.emoji(KID, 20), t0, t1, L, 32, enter="left", hits=beats[0::2], amp=3)
    s.show(s.emoji(HIPPO, 26), t0, t1, C, 32, enter="right", hits=beats[1::2], amp=3)
    me = c.w("me", t0)
    heart = s.emoji("❤️", 12)
    s.glide(heart, [(me - 0.9, C, 14), (me, L, 12)], z=Z_FRONT)
    s.show(heart, me, t1, L, 12, enter=None, hits=c.beats_in(me + 0.3, t1), amp=2, z=Z_FRONT)
    s.show(heart, me + 0.2, t1, C, 12, enter="pop", hits=c.beats_in(me + 0.5, t1), amp=2, z=Z_FRONT)
    s.ring(me, L, 12, PINK, r=22)


def skate_scene(s, t0, t1):
    """Instrumental: one long pond under both windows; the hippo skates all the way across and back."""
    s.show(pond_img(s), t0, t1, 52, 42, enter="fade", enter_s=0.8, z=Z_BACK)
    s.show(s.emoji("🌙", 10), t0, t1, C + 10, 8, enter="fade", enter_s=0.8, z=Z_BACK)
    left, right = s.emoji(HIPPO, 16), s.emoji(HIPPO, 16, flip=True)
    lap, t, k = 3.4, t0, 0
    while t < t1 - 0.05:
        e = min(t + lap, t1)
        u = (e - t) / lap
        if k % 2 == 0:
            s.pic(right, t, e, 8, 35, to=(8 + 88 * u, 35))
        else:
            s.pic(left, t, e, 96, 35, to=(96 - 88 * u, 35))
        t, k = e, k + 1
    s.snow(t0, t1, count=5)
    s.twinkle(t0, t1, (WHITE,), count=4)


def gifts_scene(s, t0, t1):
    """Instrumental: presents drop in on each bar, taking turns between the windows."""
    bars = s.cues.bars_in(t0, t1)
    spots = [(L - 10, 40, "🎁", 16), (C + 10, 40, "🎁", 16), (L + 9, 39, "🎁", 18), (C - 9, 39, "🎁", 18),
             (L, 24, "🔔", 14), (C, 24, "🎀", 14)]
    for (x, y, em, px), b in zip(spots, bars):
        s.show(s.emoji(em, px), b, t1, x, y, enter="top", enter_s=0.3, hits=s.cues.beats_in(b + 0.5, t1)[::4], amp=1)
        s.ring(b + 0.3, x, y, GOLD, r=12, dur=0.5)
    bar_sweeps(s, t0, t1, (RED, GREEN))


def tree_scene(s, t0, t1):
    """Instrumental: the tree in the left window, the hippo waiting by its present in the right; then the windows
    swap pictures back and forth on the beats."""
    c = s.cues
    bars = c.bars_in(t0, t1)
    end_tree = bars[-2] if len(bars) >= 3 else t1
    s.show(s.emoji("🎄", 36), t0, end_tree, L, 27, enter="fade", enter_s=1.0)
    s.show(s.emoji("⭐", 10), bars[1] if len(bars) > 1 else t0, end_tree, L, 7, enter="top", z=Z_FRONT)
    s.show(s.emoji(HIPPO, 24), t0 + 1.0, end_tree, C - 4, 32, enter="right",
           hits=c.beats_in(t0 + 1.5, end_tree)[::2], amp=2)
    s.show(s.emoji("🎁", 14), t0 + 1.5, end_tree, C + 12, 38, enter="pop", z=Z_FRONT)
    s.twinkle(t0, end_tree, (RED, GOLD, BLUE, GREEN, WHITE), count=10, steps=25)
    bar_sweeps(s, t0, end_tree, (GOLD, WHITE))
    swaps = c.beats_in(end_tree, t1)
    if swaps:
        a, b, g = s.emoji(HIPPO, 30), s.emoji("🎄", 30), s.emoji("🎁", 26)
        s.flash([a, b, g], swaps, L, 27, end=t1)
        s.flash([b, g, a], swaps, C, 27, end=t1)
        for i, t in enumerate(swaps):
            s.ring(t, L if i % 2 == 0 else C, 27, XMAS[i % 4], r=26, dur=0.5)


def garage_scene(s, t0, t1):
    """The two-car garage spans both windows, a door in each; the hippo moves into the right-hand bay."""
    c = s.cues
    s.show(garage_img(s), t0, t1, 52, 33, enter="fade", enter_s=0.6, z=Z_BACK)
    him = c.w("him", t0)
    feed, wash, mas = c.w("feed", t0), c.w("wash", t0), c.w("massage", t0)
    s.glide(s.emoji(HIPPO, 16), [(him, OFF_R, 40), (him + 1.0, C, 40), (t1, C, 40)], z=Z_PIC)
    s.show(s.word("ROOM", ICE, 2), c.w("room", t0), feed, L, 9, enter="pop", z=Z_WORD)
    s.show(s.emoji("🍉", 12), feed, wash, C, 10, enter="pop", hits=[feed + 0.3], z=Z_FRONT)
    s.show(s.emoji("🧽", 12), wash, mas, C, 10, enter="pop", hits=c.beats_in(wash + 0.2, mas), amp=2, z=Z_FRONT)
    s.show(s.emoji("💆", 16), mas, t1, L, 10, enter="pop", z=Z_FRONT)
    s.ring(mas, L, 10, PINK, r=14)


def ending_scene(s, t0, t1):
    c = s.cues
    s.show(s.word("MERRY", RED), t0 + 0.5, t1 - 0.5, L, 8, enter="left", z=Z_WORD)
    s.show(s.emoji("🎄", 26), t0, t1 - 0.5, L, 31, enter="pop")
    s.show(s.word("XMAS", GREEN, 2), t0 + 1.0, t1 - 0.5, C, 8, enter="right", z=Z_WORD)
    s.show(s.emoji(HIPPO, 28), t0, t1 - 0.5, C, 31, enter="pop", hits=c.beats_in(t0 + 0.5, t1 - 1)[::2], amp=2)
    s.twinkle(t0, t1, (RED, GREEN, GOLD, WHITE), count=20, fade=1.5)
    s.ring(t0, L, 31, GOLD, r=30)
    s.ring(t0, C, 31, GOLD, r=30)


# ---------------------------------------------------------------- story

def build(s):
    c = s.cues
    w = c.w

    # ---- intro: the tree on the left, a present drops into the right window, bars cross both
    s.twinkle(0.2, 7.7, (WHITE, GOLD), count=8, fade=1.0)
    s.show(s.emoji("🎄", 30), 0.4, 7.7, L, 26, enter="fade", enter_s=1.5)
    s.show(s.emoji("🎁", 22), 4.8, 7.7, C, 32, enter="top", hits=c.beats_in(5.2, 7.7)[::2], amp=1)
    bar_sweeps(s, 0.4, 7.6, (RED, GREEN))

    # ---- verse 1
    want_scene(s, w("I", 7.5), w("only", 11.0) - 0.1)
    wish_scene(s, w("only", 11.0) - 0.1, 13.4)
    only_scene(s, 13.4, w("don't", 16.0) - 0.1)
    no_items(s, [("🪆", L, 17.3, 21.05, w("doll", 17.0)), ("🧸", C, 19.55, 21.05, w("dink", 19.5))])
    s.show(s.emoji("🚂", 22), 20.35, 21.05, 52, 44, enter="right", enter_s=0.3, exit="left", exit_s=0.3,
           z=Z_FRONT)  # the train runs along the bottom of both windows
    s.ring(w("toy", 20.3), C, 40, RED, r=16, dur=0.4)
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
