"""Rudolph the Red-Nosed Reindeer matrix scenes, shared plan for the garage, the two windows (one stage) and the bushes.

The MegaTree carries the SuperStar story (the reindeer, Rudolph's nose, the fog, Santa and the sleigh); these scenes
follow the same lyric beats on the other matrices. A drawn reindeer carries Rudolph's nose, so the nose can glow
(Shockwave rings at its exact pixel) and travel between props on its own.
Words: faster-whisper (stories/lyrics/rudolph.json); beats: librosa (rudolph_beats.json).
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
import matrix_storybook as mb  # noqa: E402
from morph_backdrop import backdrop, pattern_sweeps  # noqa: E402,F401
from matrix_scenes import Cues  # noqa: E402
from rockin_common import (BLUE, GOLD, GREEN, ICE, PINK, RED, WHITE, XMAS, Z_BACK, Z_FRONT, Z_PIC,  # noqa: E402,F401
                           Z_WORD, bar_sweeps)

mb.FONT.setdefault("Z", ["###", "..#", ".#.", "#..", "###"])  # BLITZEN (the 3x5 font has no Z)

LYRICS = HERE.parent / "lyrics"
FUR, BELLY, ANTLER = (150, 85, 35), (200, 150, 100), (215, 190, 140)
NOSE_ON, NOSE_OFF = (255, 0, 0), (40, 20, 15)
FOG = (90, 90, 105)
NAMES = ["dasher", "dancer", "prancer", "vixen", "comet", "cupid", "donner", "blitzen"]


def cues(xsq):
    dur = float(ET.parse(xsq).getroot().findtext("head/sequenceDuration"))
    return Cues.from_files(LYRICS / "rudolph.json", LYRICS / "rudolph_beats.json", dur)


def plan(c):
    w = c.w
    t = [
        ("intro", 0.0),
        ("names", w("dasher") - 0.3),
        ("recall", w("but") - 0.1),
        ("rudolph", w("rudolph") - 0.1),
        ("glows", w("and", 29.9) - 0.1),
        ("laugh", w("all", 36.5) - 0.1),
        ("games", w("they", 43) - 0.1),
        ("foggy", w("then", 49) - 0.1),
        ("guide", w("rudolph", 56.5) - 0.1),
        ("loved", w("then", 63.5) - 0.1),
        ("history", w("rudolph", 70.5) - 0.1),
        ("flight", w("history") + 1.0),
        ("deliver", c.beat_after(98.0)),
        ("party", c.beat_after(114.5)),
        ("rudolph", w("rude", 130) - 0.1),
        ("glows", w("and", 137) - 0.1),
        ("laugh", w("all", 145) - 0.1),
        ("games", w("they", 152) - 0.1),
        ("foggy", w("then", 159) - 0.1),
        ("guide", w("rudolph", 164.5) - 0.1),
        ("loved", w("then", 172.5) - 0.1),
        ("history", w("rudolph", 179.5) - 0.1),
        ("finale", w("history", 184) + 0.9),
    ]
    return [(n, t0, t[k + 1][1] if k + 1 < len(t) else c.duration) for k, (n, t0) in enumerate(t)]


def run(s, scenes):
    for name, t0, t1 in plan(s.cues):
        backdrop(s, t0, t1)
        fn = scenes.get(name)
        if fn:
            fn(s, t0, t1)


# ---------------------------------------------------------------- drawn props

def reindeer(s, h, *, nose="on", flip=False):
    """A drawn reindeer h pixels tall, facing right (left with flip). nose: "on" (Rudolph), "off" (Rudolph unlit),
    None (an ordinary reindeer, a small black nose)."""
    W = round(h * 1.3)

    def draw(d, im):
        lw = max(1, h // 14)
        # legs
        for x in (0.25, 0.36, 0.58, 0.68):
            d.line([(W * x, h * 0.62), (W * x + (1 if x > 0.5 else -1), h - 1)], fill=FUR + (255,), width=lw)
        d.ellipse([W * 0.14, h * 0.38, W * 0.76, h * 0.72], fill=FUR + (255,))         # body
        d.ellipse([W * 0.3, h * 0.55, W * 0.66, h * 0.72], fill=BELLY + (255,))        # belly
        d.polygon([(W * 0.62, h * 0.45), (W * 0.74, h * 0.28), (W * 0.84, h * 0.32), (W * 0.76, h * 0.55)],
                  fill=FUR + (255,))                                                   # neck
        d.ellipse([W * 0.72, h * 0.2, W * 0.9, h * 0.4], fill=FUR + (255,))           # head
        d.polygon([(W * 0.84, h * 0.26), (W * 0.97, h * 0.3), (W * 0.97, h * 0.38), (W * 0.84, h * 0.4)],
                  fill=FUR + (255,))                                                   # snout
        d.ellipse([W * 0.1, h * 0.38, W * 0.18, h * 0.46], fill=(255, 255, 255, 255))  # tail
        for dx in (0, 0.06):                                                           # antlers
            bx = W * (0.77 + dx)
            d.line([(bx, h * 0.22), (bx - W * 0.06, 0)], fill=ANTLER + (255,), width=lw)
            d.line([(bx - W * 0.03, h * 0.11), (bx + W * 0.03, h * 0.03)], fill=ANTLER + (255,), width=lw)
        e = max(1, h // 20)
        d.ellipse([W * 0.82 - e, h * 0.27 - e, W * 0.82 + e, h * 0.27 + e], fill=(0, 0, 0, 255))
        r = max(1.5, h * 0.06) if nose else max(1, h * 0.03)
        col = {"on": NOSE_ON, "off": NOSE_OFF}.get(nose, (20, 10, 5))
        cx, cy = W * 0.97, h * 0.33
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (255,))

    key = s.drawn(f"deer_{h}_{nose}", W, h, draw)
    return flipped(s, key) if flip else key


def flipped(s, key):
    name = key.rsplit("/", 1)[1][:-4] + "_flip"
    return s.image(name, s.images[key].transpose(0))


def nose_xy(s, key, x, y):
    """Where the red nose of a reindeer picture centred at (x, y) is."""
    im = s.images[key]
    px = im.load()
    pts = [(i, j) for j in range(im.height) for i in range(im.width)
           if px[i, j][3] and px[i, j][0] > 200 and px[i, j][1] < 60]
    if not pts:
        return x, y
    cx = sum(p[0] for p in pts) / len(pts) + 0.5
    cy = sum(p[1] for p in pts) / len(pts) + 0.5
    return x - im.width / 2 + cx, y - im.height / 2 + cy


def nose_dot(s, px):
    def draw(d, im):
        d.ellipse([0, 0, px - 1, px - 1], fill=NOSE_ON + (255,))
        if px >= 5:
            d.point((px // 3, px // 3), fill=(255, 200, 200, 255))
    return s.drawn(f"nose_{px}", px, px, draw)


def glow(s, key, t, x, y, r=12, dur=0.5, color=RED):
    """A ring bursting from the reindeer's nose."""
    nx, ny = nose_xy(s, key, x, y)
    s.ring(t, nx, ny, color, r=r, dur=dur)


def name_word(s, n, color, scale):
    return s.word(n.upper(), color, scale)


def fog(s, t0, t1, fade_in=1.5, fade_out=1.5):
    s.wash(t0, t1, FOG, fade_in=fade_in, fade_out=fade_out)
    s.twinkle(t0, t1, ((150, 150, 165),), count=20, steps=60, fade=fade_in)


def team(s, t0, t1, x0, x1, y, h, *, glow_every=None):
    """Rudolph leading two reindeer and Santa's sleigh from x0 to x1 (Rudolph's centre)."""
    right = x1 > x0
    rud = reindeer(s, h, flip=not right)
    deer = reindeer(s, h, nose=None, flip=not right)
    sled = s.emoji("🛷", h, flip=right)
    santa = s.emoji("🎅", int(h * 0.75), flip=right)
    gap = round(h * 1.3) + 1
    back = -1 if right else 1
    parts = [(rud, 0, 0, Z_PIC), (deer, 1, 0, Z_PIC), (deer, 2, 0, Z_PIC), (sled, 3, 2, Z_PIC),
             (santa, 3, -h * 0.45, Z_FRONT)]
    for key, k, dy, z in parts:
        off = back * gap * k
        s.glide(key, [(t0, x0 + off, y + dy), (t1, x1 + off, y + dy)], z=z)
    if glow_every:
        n = int((t1 - t0) / glow_every)
        for k in range(n):
            u = (k + 0.5) / max(1, n)
            glow(s, rud, t0 + (t1 - t0) * u, x0 + (x1 - x0) * u, y, r=8, dur=0.4)


def team_len(h):
    return (round(h * 1.3) + 1) * 4


# ================================================================ 140x60 matrix (the garage)

GY = 34


def g_intro(s, t0, t1):
    s.twinkle(0.2, t1, (WHITE, ICE), count=10, fade=1.5)
    dot = nose_dot(s, 8)
    s.show(dot, 1.5, t1, 70, 30, enter="fade", enter_s=1.5)
    for t in (3.0, 4.0, 5.0, t1 - 0.4):
        s.ring(t, 70, 30, RED, r=24, dur=0.6)


def g_names(s, t0, t1):
    c = s.cues
    spots = [(20, 26), (53, 26), (86, 26), (119, 26), (20, 49), (53, 49), (86, 49), (119, 49)]
    deer = reindeer(s, 20, nose=None)
    for k, (n, (x, y)) in enumerate(zip(NAMES, spots)):
        t = c.w(n, t0)
        nxt = c.w(NAMES[k + 1], t0) if k + 1 < len(NAMES) else t1
        s.show(deer, t, t1, x, y, enter="pop", enter_s=0.2)
        s.show(name_word(s, n, XMAS[k % 4] if k % 4 != 3 else ICE, 2), t, nxt, 70, 6, enter="pop", enter_s=0.15,
               z=Z_WORD)
        s.ring(t, x, y, GOLD, r=14, dur=0.4)
    s.show(s.emoji("⚡", 14), c.w("blitzen", t0), t1, 132, 40, enter="pop", z=Z_FRONT)


def g_recall(s, t0, t1):
    c = s.cues
    recall, most, famous = c.w("recall", t0), c.w("most", t0), c.w("famous", t0)
    spots = [(20, 26), (53, 26), (86, 26), (119, 26), (20, 49), (53, 49), (86, 49), (119, 49)]
    deer = reindeer(s, 20, nose=None)
    for k, (x, y) in enumerate(spots):
        s.show(deer, t0, most - 0.3, x, y, enter=None, exit="bottom" if y > 30 else "top", exit_s=0.5)
    s.show(s.emoji("❓", 18), recall, most, 70, 38, enter="pop", z=Z_FRONT)
    s.show(s.word("MOST FAMOUS", GOLD, 2), most, t1, 70, 6, enter="pop", z=Z_WORD)
    rud = reindeer(s, 40, nose="off")
    s.show(rud, famous, t1, 70, 38, enter="fade", enter_s=1.2)
    s.twinkle(famous, t1, (GOLD, WHITE), count=20, steps=15, fade=0.5)
    s.ring(famous, 70, 38, GOLD, r=60, dur=1.0)


def rud_light(s, t0, t1, x, y, h, light, *, hits=(), amp=2, flip=False, enter=None, z=Z_PIC):
    """Rudolph with his nose off until `light`, then on."""
    off, on = reindeer(s, h, nose="off", flip=flip), reindeer(s, h, flip=flip)
    if light > t0:
        s.show(off, t0, light, x, y, enter=enter, hits=[b for b in hits if b < light], amp=amp, z=z)
    s.hold(on, max(t0, light), t1, x, y, hits=[b for b in hits if b >= light], amp=amp, z=z)
    glow(s, on, max(t0, light), x, y, r=h, dur=0.6)


def g_rudolph(s, t0, t1):
    c = s.cues
    red, shiny = c.w("red", t0), c.w("shiny", t0)
    rud = reindeer(s, 40)
    rud_light(s, t0, t1, 70, GY, 40, red)
    s.show(s.word("RUDOLPH", RED, 2), t0 + 0.1, shiny, 70, 6, enter="pop", z=Z_WORD)
    s.show(s.word("SHINY", WHITE, 2), shiny, t1, 70, 6, enter="pop", z=Z_WORD)
    for t in (shiny, shiny + 0.6):
        glow(s, rud, t, 70, GY, r=40, dur=0.7)
    s.twinkle(shiny, t1, (RED, WHITE), count=15, steps=15, fade=0.3)


def g_glows(s, t0, t1):
    c = s.cues
    saw, glows = c.w("saw", t0), c.w("glows", t0)
    rud = reindeer(s, 40)
    s.hold(rud, t0, t1, 84, GY)
    s.show(s.emoji("😮", 24), saw, t1, 22, 32, enter="left")
    for b in c.bars_in(t0, glows):
        glow(s, rud, b, 84, GY, r=18, dur=0.5)
    s.show(s.word("GLOWS", RED, 3), glows, t1, 70, 8, enter="pop", z=Z_WORD)
    nx, ny = nose_xy(s, rud, 84, GY)
    s.ring(glows, nx, ny, RED, r=90, width=5, dur=1.0)
    s.ring(glows + 0.3, nx, ny, (255, 120, 120), r=90, width=3, dur=1.0)
    s.wash(glows, t1, (60, 0, 0), fade_in=0.3, fade_out=0.6)


def g_laugh(s, t0, t1):
    c = s.cues
    laugh, names = c.w("laugh", t0), c.w("names", t0)
    beats = c.beats_in(t0, t1)
    deer = reindeer(s, 24, nose=None)
    for k, x in enumerate((18, 44, 70)):
        s.show(deer, t0 + 0.2 * k, t1, x, 44, enter="left", hits=beats[k % 2::2], amp=2)
    s.show(s.emoji("😂", 16), laugh, t1, 44, 20, enter="pop", hits=beats[::2], amp=3, z=Z_FRONT)
    s.show(s.word("HA HA", GOLD, 2), laugh, names, 44, 6, enter="pop", z=Z_WORD)
    s.show(s.word("NAMES", PINK, 2), names, t1, 44, 6, enter="pop", z=Z_WORD)
    sad = reindeer(s, 32, flip=True)
    s.show(sad, t0, t1, 116, 38, enter="right")
    s.show(s.emoji("😢", 14), names, t1, 116, 12, enter="pop", z=Z_FRONT)


def g_games(s, t0, t1):
    c = s.cues
    poor, join, games = c.w("poor", t0), c.w("join", t0), c.w("games", t0)
    deer, deer_f = reindeer(s, 24, nose=None), reindeer(s, 24, nose=None, flip=True)
    s.show(deer, t0, t1, 16, 44, enter="left")
    s.show(deer_f, t0, t1, 76, 44, enter=None)
    ball = s.emoji("⚽", 9)
    for k, b in enumerate(c.bars_in(t0, t1)):
        a, z = (30, 62) if k % 2 == 0 else (62, 30)
        s.glide(ball, [(b, a, 40), (b + 0.45, (a + z) / 2, 20), (b + 0.9, z, 40)], z=Z_FRONT)
    rud = reindeer(s, 30, flip=True)
    s.show(rud, t0, t1, 118, 40, enter="right")
    s.show(s.emoji("😢", 14), poor, t1, 118, 14, enter="pop", z=Z_FRONT)
    s.show(s.emoji("🚫", 22), join, t1, 118, 40, enter="pop", z=Z_FRONT)
    s.show(s.word("GAMES", GREEN, 2), games, t1, 46, 6, enter="pop", z=Z_WORD)


def g_foggy(s, t0, t1):
    c = s.cues
    foggy, eve, santa = c.w("foggy", t0), c.w("eve", t0), c.w("santa", t0)
    fog(s, foggy - 0.3, t1, fade_out=0)
    s.show(s.word("FOGGY", (180, 180, 200), 2), foggy, eve, 70, 6, enter="pop", z=Z_WORD)
    s.show(s.word("XMAS EVE", ICE, 2), eve, santa, 70, 6, enter="pop", z=Z_WORD)
    s.show(s.emoji("🌙", 16), t0, t1, 124, 10, enter="fade", enter_s=1.0, z=Z_BACK)
    s.show(s.emoji("🎅", 34), santa, t1, 30, 38, enter="left", hits=c.beats_in(santa, t1)[::2], amp=2)
    s.show(s.word("SANTA", RED, 2), santa, t1, 70, 6, enter="pop", z=Z_WORD)
    rud = reindeer(s, 30, flip=True)
    s.show(rud, t0, t1, 108, 40, enter="right")
    for b in c.bars_in(t0, t1):
        glow(s, rud, b, 108, 40, r=16, dur=0.6)


def g_guide(s, t0, t1):
    c = s.cues
    bright, guide, sleigh, tonight = (c.w(k, t0) for k in ("bright", "guide", "sleigh", "tonight"))
    fog(s, t0, tonight + 0.6, fade_in=0.05, fade_out=0.6)
    s.show(s.emoji("🎅", 34), t0, t1, 30, 38, enter=None, hits=c.beats_in(guide, t1)[::2], amp=2)
    rud = reindeer(s, 34, flip=True)
    s.show(rud, t0, t1, 104, 38, enter=None)
    s.show(s.word("BRIGHT", RED, 2), bright, guide, 70, 6, enter="pop", z=Z_WORD)
    for t in (bright, guide, sleigh, tonight):
        glow(s, rud, t, 104, 38, r=50, dur=0.8)
    s.show(s.word("GUIDE MY", GOLD, 2), guide, sleigh, 70, 6, enter="pop", z=Z_WORD)
    s.show(s.word("SLEIGH", GREEN, 2), sleigh, tonight, 70, 6, enter="pop", z=Z_WORD)
    s.show(s.emoji("🛷", 22), sleigh, t1, 66, 48, enter="bottom")
    s.show(s.word("TONIGHT", WHITE, 2), tonight, t1, 70, 6, enter="pop", z=Z_WORD)


def g_loved(s, t0, t1):
    c = s.cues
    loved, glee = c.w("loved", t0), c.w("glee", t0)
    beats = c.beats_in(t0, t1)
    rud = reindeer(s, 36)
    s.hold(rud, t0, t1, 70, GY, hits=beats[::2], amp=3)
    for k, (x, fl) in enumerate(((20, False), (120, True))):
        s.show(reindeer(s, 24, nose=None, flip=fl), t0, t1, x, 44, enter="left" if k == 0 else "right",
               hits=beats[k::2], amp=3)
    heart = s.emoji("❤️", 12)
    for k, x in enumerate((20, 50, 90, 120)):
        s.show(heart, loved + 0.15 * k, t1, x, 18, enter="pop", hits=beats[k % 2::2], amp=2, z=Z_FRONT)
    s.show(s.word("LOVED HIM", PINK, 2), loved, glee, 70, 6, enter="pop", z=Z_WORD)
    s.show(s.word("GLEE", GOLD, 2), glee, t1, 70, 6, enter="pop", z=Z_WORD)
    s.ring(glee, 70, GY, PINK, r=60)
    s.twinkle(loved, t1, (PINK, RED, WHITE), count=15, fade=0.3)


def g_history(s, t0, t1):
    c = s.cues
    hist = c.w("history", t0)
    rud = reindeer(s, 40)
    s.hold(rud, t0, t1, 70, 36, hits=c.beats_in(t0, hist)[::2], amp=2)
    s.show(s.word("RUDOLPH", RED, 2), t0 + 0.1, hist, 70, 6, enter="pop", z=Z_WORD)
    s.show(s.word("HISTORY", GOLD, 2), hist, t1, 70, 6, enter="pop", z=Z_WORD)
    for k, x in enumerate((16, 124)):
        s.show(s.emoji("⭐", 14), hist + 0.2 * k, t1, x, 24, enter="pop", z=Z_FRONT)
    glow(s, rud, hist, 70, 36, r=70, dur=0.9)
    s.ring(hist, 70, 30, GOLD, r=80, dur=1.0)
    s.twinkle(hist, t1, (GOLD, WHITE), count=25, steps=15, fade=0.3)
    bar_sweeps(s, t0, t1)


def g_flight(s, t0, t1):
    s.show(s.emoji("🌕", 18), t0, t1, 124, 11, enter="fade", enter_s=1.5, z=Z_BACK)
    s.twinkle(t0, t1, (WHITE, ICE, GOLD), count=15, fade=1.0)
    s.snow(t0, t1, count=5)
    h, L = 14, team_len(14)
    passes = [(True, 36), (False, 22), (True, 46), (False, 30)]
    span = (t1 - t0) / len(passes)
    for k, (right, y) in enumerate(passes):
        a = t0 + span * k
        x0, x1 = (-10, 140 + L) if right else (150, -L)
        team(s, a, a + span - 0.2, x0, x1, y, h, glow_every=0.9)


def g_deliver(s, t0, t1):
    c = s.cues
    bars = c.bars_in(t0, t1)
    houses = [14, 50, 90, 126]
    for k, x in enumerate(houses):
        s.show(s.emoji("🏠" if k % 2 == 0 else "🏡", 24), t0 + 0.2 * k, t1, x, 47, enter="bottom", z=Z_BACK)
    s.snow(t0, t1, count=4)
    h, L = 12, team_len(12)
    passes = 3
    span = (t1 - t0) / passes
    gift = s.emoji("🎁", 10)
    for k in range(passes):
        a, b = t0 + span * k, t0 + span * (k + 1) - 0.2
        right = k % 2 == 0
        x0, x1 = (-10, 140 + L) if right else (150, -L)
        team(s, a, b, x0, x1, 12, h)
        sled_off = -3 * (round(h * 1.3) + 1) if right else 3 * (round(h * 1.3) + 1)
        for x in houses:
            u = (x - sled_off - x0) / (x1 - x0)    # when the sleigh is over this house
            td = a + (b - a) * u
            if a < td < b - 0.5:
                s.glide(gift, [(td, x, 16), (td + 0.5, x, 36)], z=Z_BACK - 1)  # down the chimney
                s.ring(td + 0.5, x, 40, GOLD, r=14, dur=0.4)


def g_party(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    bars = c.bars_in(t0, t1)
    rud = reindeer(s, 36)
    s.hold(rud, t0, t1, 70, 36, hits=beats[::2], amp=3)
    for b in bars:
        glow(s, rud, b, 70, 36, r=30, dur=0.5)
    words = [name_word(s, n, XMAS[k % 4], 2) for k, n in enumerate(NAMES)]
    if bars:
        s.flash(words, bars, 70, 6, z=Z_WORD, end=t1)
    for k, (x, fl) in enumerate(((20, False), (120, True))):
        s.show(reindeer(s, 24, nose=None, flip=fl), t0, t1, x, 44, enter="left" if k == 0 else "right",
               hits=beats[k::2], amp=3)
    bar_sweeps(s, t0, t1, (RED, GREEN, GOLD))
    s.twinkle(t0, t1, XMAS, count=15)


def g_finale(s, t0, t1):
    end = t1 - 0.2
    rud = reindeer(s, 40)
    s.show(rud, t0, end, 70, 34, enter=None, exit="fade", exit_s=2.5)
    nx, ny = nose_xy(s, rud, 70, 34)
    s.show(nose_dot(s, 6), end - 2.5, end, nx, ny, enter=None, exit="fade", exit_s=1.0, z=Z_FRONT)
    for t in (t0, t0 + 1.0, end - 1.2):
        s.ring(t, nx, ny, RED, r=40, dur=0.8)
    s.twinkle(t0, t1, XMAS, count=15, fade=2.0)


GARAGE = dict(intro=g_intro, names=g_names, recall=g_recall, rudolph=g_rudolph, glows=g_glows, laugh=g_laugh,
              games=g_games, foggy=g_foggy, guide=g_guide, loved=g_loved, history=g_history, flight=g_flight,
              deliver=g_deliver, party=g_party, finale=g_finale)


# ================================================================ the two windows as one stage

def wins(s):
    return tuple(s.center(m)[0] for m in s.places)  # the two windows, in --model order


WY = 28


def w_intro(s, t0, t1):
    L, C = wins(s)
    s.twinkle(0.2, t1, (WHITE, ICE), count=8, fade=1.5)
    dot = nose_dot(s, 6)
    s.show(dot, 1.5, 3.5, L, 24, enter="fade", enter_s=1.0)
    s.glide(dot, [(3.5, L, 24), (5.0, C, 24), (t1, C, 24)], z=Z_FRONT)
    s.ring(3.4, L, 24, RED, r=16, dur=0.5)
    s.ring(5.0, C, 24, RED, r=16, dur=0.5)


def w_names(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    deer = reindeer(s, 22, nose=None)
    deer_f = reindeer(s, 22, nose=None, flip=True)
    for k, n in enumerate(NAMES):
        t = c.w(n, t0)
        nxt = c.w(NAMES[k + 1], t0) if k + 1 < len(NAMES) else t1
        x = (L, C)[k % 2]
        s.show(deer if k % 2 == 0 else deer_f, t, nxt if k < 6 else t1, x, 32, enter="pop", enter_s=0.15)
        s.show(name_word(s, n, XMAS[k % 4] if k % 4 != 3 else ICE, 1), t, nxt if k < 6 else t1, x, 8,
               enter="pop", enter_s=0.15, z=Z_WORD)
        s.ring(t, x, 32, GOLD, r=18, dur=0.4)
    s.show(s.emoji("⚡", 14), c.w("blitzen", t0), t1, C + 13, 18, enter="pop", z=Z_FRONT)


def w_recall(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    recall, famous = c.w("recall", t0), c.w("famous", t0)
    s.show(s.emoji("❓", 26), recall, t1, L, WY, enter="pop", hits=c.beats_in(recall, t1)[::4], amp=2)
    s.show(reindeer(s, 30, nose="off", flip=True), famous, t1, C, WY + 2, enter="fade", enter_s=1.2)
    s.twinkle(famous, t1, (GOLD, WHITE), count=20, steps=15, fade=0.5)


def w_rudolph(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    red, shiny = c.w("red", t0), c.w("shiny", t0)
    rud = reindeer(s, 30)
    rud_light(s, t0, t1, L, WY + 2, 30, red)
    # the glow leaves his nose, crosses behind the wall and lights up the other window
    nx, ny = nose_xy(s, rud, L, WY + 2)
    dot = nose_dot(s, 6)
    s.glide(dot, [(shiny - 0.8, nx, ny), (shiny, C, 18)], z=Z_FRONT)
    s.show(dot, shiny, t1, C, 18, enter=None, z=Z_FRONT)
    s.ring(shiny, C, 18, RED, r=30, dur=0.7)
    s.show(s.emoji("✨", 18), shiny + 0.2, t1, C, 36, enter="pop")
    s.twinkle(shiny, t1, (RED, WHITE), count=15, steps=15, fade=0.3)


def w_glows(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    saw, glows = c.w("saw", t0), c.w("glows", t0)
    rud = reindeer(s, 30, flip=True)
    s.hold(rud, t0, t1, C, WY + 2)
    s.show(s.emoji("😮", 28), saw, t1, L, WY, enter="left")
    for b in c.bars_in(t0, glows):
        glow(s, rud, b, C, WY + 2, r=14, dur=0.5)
    glow(s, rud, glows, C, WY + 2, r=40, dur=0.9)
    s.ring(glows + 0.2, L, WY, RED, r=30, dur=0.8)
    s.wash(glows, t1, (60, 0, 0), fade_in=0.3, fade_out=0.6)


def w_laugh(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    laugh, names = c.w("laugh", t0), c.w("names", t0)
    beats = c.beats_in(t0, t1)
    s.show(reindeer(s, 22, nose=None), t0, t1, L, 36, enter="left", hits=beats[::2], amp=2)
    s.show(s.emoji("😂", 16), laugh, t1, L, 12, enter="pop", hits=beats[1::2], amp=3, z=Z_FRONT)
    s.show(s.word("HA HA", GOLD, 1), laugh, t1, L, 3, enter="pop", z=Z_WORD)
    s.show(reindeer(s, 30, flip=True), t0, t1, C, WY + 4, enter="right")
    s.show(s.emoji("😢", 14), names, t1, C, 8, enter="pop", z=Z_FRONT)


def w_games(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    join = c.w("join", t0)
    s.show(reindeer(s, 18, nose=None), t0, t1, L - 9, 38, enter="left")
    s.show(reindeer(s, 18, nose=None, flip=True), t0, t1, L + 9, 38, enter=None)
    ball = s.emoji("⚽", 8)
    bars = c.bars_in(t0, join)
    for k, b in enumerate(bars):
        a, z = (L - 4, L + 4) if k % 2 == 0 else (L + 4, L - 4)
        s.glide(ball, [(b, a, 30), (b + 0.4, (a + z) / 2, 16), (b + 0.8, z, 30)], z=Z_FRONT)
    # the ball flies over the wall to Rudolph... and is taken away
    s.glide(ball, [(join - 0.8, L, 30), (join - 0.2, C, 10), (join, C, 14)], z=Z_FRONT)
    s.show(reindeer(s, 30, flip=True), t0, t1, C, WY + 4, enter="right")
    s.show(s.emoji("🚫", 30), join, t1, C, WY, enter="pop", z=Z_FRONT)


def w_foggy(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    foggy, santa = c.w("foggy", t0), c.w("santa", t0)
    fog(s, foggy - 0.3, t1, fade_out=0)
    s.show(s.emoji("🎅", 32), santa, t1, L, WY, enter="left")
    rud = reindeer(s, 30, flip=True)
    s.show(rud, t0, t1, C, WY + 4, enter="right")
    for b in c.bars_in(t0, t1):
        glow(s, rud, b, C, WY + 4, r=14, dur=0.6)


def w_guide(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    bright, sleigh, tonight = c.w("bright", t0), c.w("sleigh", t0), c.w("tonight", t0)
    fog(s, t0, tonight + 0.6, fade_in=0.05, fade_out=0.6)
    s.show(s.emoji("🎅", 32), t0, sleigh, L, WY, enter=None)
    s.show(s.emoji("🛷", 34), sleigh, t1, L, WY + 6, enter="bottom")
    s.show(s.emoji("🎅", 22), sleigh, t1, L + 4, WY - 6, enter=None, z=Z_FRONT)
    rud = reindeer(s, 30, flip=True)
    s.show(rud, t0, t1, C, WY + 4, enter=None)
    for t in (bright, sleigh, tonight):
        glow(s, rud, t, C, WY + 4, r=40, dur=0.8)


def w_loved(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    loved = c.w("loved", t0)
    beats = c.beats_in(t0, t1)
    s.show(reindeer(s, 22, nose=None), t0, t1, L, 34, enter="left", hits=beats[::2], amp=3)
    s.show(reindeer(s, 30, flip=True), t0, t1, C, WY + 4, enter="right", hits=beats[1::2], amp=3)
    for x in (L, C):
        s.show(s.emoji("❤️", 14), loved, t1, x, 9, enter="pop", hits=beats[::2], amp=2, z=Z_FRONT)
    s.twinkle(loved, t1, (PINK, RED, WHITE), count=15, fade=0.3)


def w_history(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    hist = c.w("history", t0)
    rud = reindeer(s, 30)
    s.show(rud, t0, t1, L, WY + 2, enter="left", hits=c.beats_in(t0, hist)[::2], amp=2)
    s.show(s.emoji("⭐", 26), hist, t1, C, WY, enter="pop")
    s.show(s.word("HISTORY", GOLD, 1), hist, t1, C, 6, enter="pop", z=Z_WORD)
    s.ring(hist, C, WY, GOLD, r=30)
    glow(s, rud, hist, L, WY + 2, r=30)
    s.twinkle(hist, t1, (GOLD, WHITE), count=20, steps=15, fade=0.3)


def w_flight(s, t0, t1):
    L, C = wins(s)
    s.show(s.emoji("🌕", 14), t0, t1, C + 10, 8, enter="fade", enter_s=1.5, z=Z_BACK)
    s.twinkle(t0, t1, (WHITE, ICE, GOLD), count=12, fade=1.0)
    s.snow(t0, t1, count=4)
    h, Ln = 12, team_len(12)
    passes = [(False, 28), (True, 20), (False, 34), (True, 26)]
    span = (t1 - t0) / len(passes)
    for k, (right, y) in enumerate(passes):
        a = t0 + span * k
        x0, x1 = (-10, s.W + Ln) if right else (s.W + 10, -Ln)
        team(s, a, a + span - 0.2, x0, x1, y, h, glow_every=0.9)


def w_deliver(s, t0, t1):
    L, C = wins(s)
    for k, x in enumerate((L, C)):
        s.show(s.emoji("🏠" if k == 0 else "🏡", 26), t0 + 0.3 * k, t1, x, 36, enter="bottom", z=Z_BACK)
    s.snow(t0, t1, count=4)
    h, Ln = 10, team_len(10)
    gap = round(h * 1.3) + 1
    passes = 3
    span = (t1 - t0) / passes
    gift = s.emoji("🎁", 10)
    for k in range(passes):
        a, b = t0 + span * k, t0 + span * (k + 1) - 0.2
        right = k % 2 == 0
        x0, x1 = (-10, s.W + Ln) if right else (s.W + 10, -Ln)
        team(s, a, b, x0, x1, 8, h)
        sled_off = -3 * gap if right else 3 * gap
        for x in (L, C):
            td = a + (b - a) * (x - sled_off - x0) / (x1 - x0)
            if a < td < b - 0.5:
                s.glide(gift, [(td, x, 12), (td + 0.5, x, 26)], z=Z_BACK - 1)  # down the chimney
                s.ring(td + 0.5, x, 26, GOLD, r=14, dur=0.4)


def w_party(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    rud = reindeer(s, 30, flip=True)
    s.hold(rud, t0, t1, C, WY + 2, hits=beats[::2], amp=3)
    for b in c.bars_in(t0, t1):
        glow(s, rud, b, C, WY + 2, r=20, dur=0.5)
    bars = c.bars_in(t0, t1)
    if bars:
        s.flash([name_word(s, n, XMAS[k % 4], 1) for k, n in enumerate(NAMES)], bars, L, 6, z=Z_WORD, end=t1)
        s.flash([reindeer(s, 22, nose=None), reindeer(s, 22, nose=None, flip=True)], bars, L, 32, end=t1)
    s.twinkle(t0, t1, XMAS, count=12)


def w_finale(s, t0, t1):
    L, C = wins(s)
    end = t1 - 0.2
    rud = reindeer(s, 30)
    s.show(rud, t0, end, L, WY + 2, enter=None, exit="fade", exit_s=2.5)
    s.show(s.emoji("🎄", 34), t0, end, C, WY, enter="pop", exit="fade", exit_s=2.5)
    glow(s, rud, t0 + 0.5, L, WY + 2, r=30, dur=0.8)
    s.twinkle(t0, t1, XMAS, count=12, fade=2.0)


WINDOWS = dict(intro=w_intro, names=w_names, recall=w_recall, rudolph=w_rudolph, glows=w_glows, laugh=w_laugh,
               games=w_games, foggy=w_foggy, guide=w_guide, loved=w_loved, history=w_history, flight=w_flight,
               deliver=w_deliver, party=w_party, finale=w_finale)


# ================================================================ 200x42 matrix: 8 bushes, 25 px each

def bx(i):
    return 12.5 + 25 * i


BY = 24


def b_intro(s, t0, t1):
    dot = nose_dot(s, 6)
    for i in range(8):
        t = 1.0 + 0.6 * i
        s.show(dot, t, t1, bx(i), 20, enter="pop", enter_s=0.2)
        s.ring(t, bx(i), 20, RED, r=10, dur=0.4)


def b_names(s, t0, t1):
    c = s.cues
    deer = reindeer(s, 22, nose=None)
    for i, n in enumerate(NAMES):
        t = c.w(n, t0)
        s.show(deer, t, t1, bx(i), BY, enter="pop", enter_s=0.2)
        s.ring(t, bx(i), BY, GOLD, r=13, dur=0.4)
    s.show(s.emoji("⚡", 12), c.w("blitzen", t0), t1, bx(7) + 6, 7, enter="pop", z=Z_FRONT)


def b_recall(s, t0, t1):
    c = s.cues
    recall, most, famous = c.w("recall", t0), c.w("most", t0), c.w("famous", t0)
    deer = reindeer(s, 22, nose=None)
    q = s.emoji("❓", 18)
    for i in range(8):
        s.show(deer, t0, recall + 0.06 * i, bx(i), BY, enter=None)
        s.show(q, recall + 0.06 * i, famous, bx(i), BY, enter="pop", enter_s=0.2,
               hits=c.beats_in(most, famous)[i % 2::2], amp=2)
    rud = reindeer(s, 24, nose="off")
    for i in range(8):
        s.show(rud, famous + 0.1 * i, t1, bx(i), BY, enter="fade", enter_s=0.8)
    s.twinkle(famous, t1, (GOLD, WHITE), count=12, fade=0.5)


def b_rudolph(s, t0, t1):
    c = s.cues
    red, shiny = c.w("red", t0), c.w("shiny", t0)
    rud = reindeer(s, 24)
    for i in range(8):
        rud_light(s, t0, t1, bx(i), BY, 24, red + 0.08 * i)
    for i in range(8):
        glow(s, rud, shiny + 0.05 * i, bx(i), BY, r=12, dur=0.5)


def b_glows(s, t0, t1):
    c = s.cues
    glows = c.w("glows", t0)
    rud = reindeer(s, 24)
    beats = c.beats_in(t0, t1)
    for i in range(8):
        s.hold(rud, t0, t1, bx(i), BY, hits=beats[i % 2::4], amp=2)
    for k, b in enumerate(c.bars_in(t0, glows)):
        for i in range(k % 2, 8, 2):
            glow(s, rud, b, bx(i), BY, r=8, dur=0.4)
    for i in range(8):
        glow(s, rud, glows + 0.04 * i, bx(i), BY, r=20, dur=0.7)
    s.wash(glows, t1, (60, 0, 0), fade_in=0.3, fade_out=0.6)


def b_laugh(s, t0, t1):
    c = s.cues
    laugh = c.w("laugh", t0)
    beats = c.beats_in(t0, t1)
    deer = reindeer(s, 22, nose=None)
    lol = s.emoji("😂", 20)
    for i in range(7):
        s.show(deer, t0 + 0.05 * i, laugh, bx(i), BY, enter="bottom")
        s.show(lol, laugh + 0.05 * i, t1, bx(i), BY - 2, enter="pop", hits=beats[i % 2::2], amp=3)
    s.show(reindeer(s, 24, flip=True), t0, t1, bx(7), BY, enter="right")


def b_games(s, t0, t1):
    c = s.cues
    poor, join = c.w("poor", t0), c.w("join", t0)
    deer, deer_f = reindeer(s, 22, nose=None), reindeer(s, 22, nose=None, flip=True)
    for i in range(6):
        s.show(deer if i % 2 == 0 else deer_f, t0 + 0.05 * i, t1, bx(i), BY + 2, enter="bottom")
    ball = s.emoji("⚽", 8)
    for k, b in enumerate(c.bars_in(t0, t1)):
        i = k % 5
        a, z = (bx(i), bx(i + 1)) if k % 2 == 0 else (bx(5 - i), bx(4 - i))
        s.glide(ball, [(b, a, 14), (b + 0.4, (a + z) / 2, 4), (b + 0.8, z, 14)], z=Z_FRONT)
    rud = reindeer(s, 24, flip=True)
    s.show(rud, t0, t1, bx(7), BY, enter="right")
    s.show(s.emoji("😢", 18), poor, join, bx(6), BY, enter="pop")
    s.show(s.emoji("🚫", 22), join, t1, bx(6), BY, enter="pop", z=Z_FRONT)


def b_foggy(s, t0, t1):
    c = s.cues
    foggy, santa = c.w("foggy", t0), c.w("santa", t0)
    fog(s, foggy - 0.3, t1, fade_out=0)
    s.show(s.emoji("🎅", 24), santa, t1, bx(0), BY - 2, enter="left")
    rud = reindeer(s, 24, flip=True)
    s.show(rud, t0, t1, bx(7), BY, enter="right")
    for b in c.bars_in(t0, t1):
        glow(s, rud, b, bx(7), BY, r=14, dur=0.6)


def b_guide(s, t0, t1):
    c = s.cues
    guide, sleigh, tonight = c.w("guide", t0), c.w("sleigh", t0), c.w("tonight", t0)
    fog(s, t0, tonight + 0.6, fade_in=0.05, fade_out=0.6)
    s.show(s.emoji("🎅", 24), t0, t1, bx(0), BY - 2, enter=None)
    s.show(s.emoji("🛷", 22), sleigh, t1, bx(1), BY + 2, enter="bottom")
    rud = reindeer(s, 24, flip=True)
    s.show(rud, t0, guide, bx(7), BY, enter=None)
    # Rudolph trots over from the far bush to lead the sleigh
    s.glide(rud, [(guide, bx(7), BY), (tonight, bx(3), BY), (t1, bx(3), BY)])
    nx, ny = nose_xy(s, rud, bx(7), BY)
    for k, b in enumerate(c.beats_in(guide, tonight)[::2]):
        u = (b - guide) / max(0.1, tonight - guide)
        s.ring(b, nx + (bx(3) - bx(7)) * u, ny, RED, r=10, dur=0.4)
    glow(s, rud, tonight, bx(3), BY, r=30, dur=0.8)


def b_loved(s, t0, t1):
    c = s.cues
    loved = c.w("loved", t0)
    beats = c.beats_in(t0, t1)
    keys = [reindeer(s, 22, nose=None), s.emoji("❤️", 18), reindeer(s, 24), s.emoji("❤️", 18)]
    for i in range(8):
        s.show(keys[i % 4], (t0 if i % 2 == 0 else loved) + 0.05 * i, t1, bx(i), BY, enter="pop",
               hits=beats[i % 2::2], amp=3)
    s.twinkle(loved, t1, (PINK, RED, WHITE), count=10, fade=0.3)


def b_history(s, t0, t1):
    c = s.cues
    hist = c.w("history", t0)
    rud = reindeer(s, 24)
    beats = c.beats_in(t0, hist)
    for i in range(8):
        s.show(rud, t0 + 0.05 * i, hist, bx(i), BY, enter="bottom", hits=beats[i % 2::2], amp=2)
    for i, ch in enumerate("HISTORY"):
        s.show(s.word(ch, GOLD if i % 2 == 0 else RED, 5), hist + 0.08 * i, t1, bx(i), 21, enter="pop",
               enter_s=0.15, z=Z_WORD)
    s.show(s.emoji("⭐", 22), hist + 0.6, t1, bx(7), 21, enter="pop")


def b_flight(s, t0, t1):
    s.twinkle(t0, t1, (WHITE, ICE, GOLD), count=10, fade=1.0)
    s.snow(t0, t1, count=4)
    h, L = 14, team_len(14)
    passes = [(True, 24), (False, 16), (True, 30), (False, 22)]
    span = (t1 - t0) / len(passes)
    for k, (right, y) in enumerate(passes):
        a = t0 + span * k
        x0, x1 = (-10, 200 + L) if right else (210, -L)
        team(s, a, a + span - 0.2, x0, x1, y, h, glow_every=0.9)


def b_deliver(s, t0, t1):
    house = [s.emoji("🏠", 18), s.emoji("🏡", 18)]
    for i in range(8):
        s.show(house[i % 2], t0 + 0.08 * i, t1, bx(i), 32, enter="bottom", z=Z_BACK)
    h, Ln = 9, team_len(9)
    gap = round(h * 1.3) + 1
    passes = 3
    span = (t1 - t0) / passes
    gift = s.emoji("🎁", 8)
    for k in range(passes):
        a, b = t0 + span * k, t0 + span * (k + 1) - 0.2
        right = k % 2 == 0
        x0, x1 = (-10, 200 + Ln) if right else (210, -Ln)
        team(s, a, b, x0, x1, 7, h)
        sled_off = -3 * gap if right else 3 * gap
        for i in range(8):
            td = a + (b - a) * (bx(i) - sled_off - x0) / (x1 - x0)
            if a < td < b - 0.4:
                s.glide(gift, [(td, bx(i), 10), (td + 0.4, bx(i), 26)], z=Z_BACK - 1)  # down the chimney
                s.ring(td + 0.4, bx(i), 28, GOLD, r=10, dur=0.4)


def b_party(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    keys = [reindeer(s, 24), reindeer(s, 22, nose=None), s.emoji("🎄", 22)]
    for i in range(8):
        if beats:
            s.flash(keys[i % 3:] + keys[:i % 3], beats[::2], bx(i), BY, end=t1)
    s.twinkle(t0, t1, XMAS, count=12)


def b_finale(s, t0, t1):
    end = t1 - 0.2
    rud = reindeer(s, 24)
    for i in range(8):
        s.show(rud, t0 + 0.05 * i, end, bx(i), BY, enter="pop", exit="fade", exit_s=2.5)
        glow(s, rud, t0 + 0.5 + 0.05 * i, bx(i), BY, r=14, dur=0.6)
    s.twinkle(t0, t1, XMAS, count=10, fade=2.0)


BUSHES = dict(intro=b_intro, names=b_names, recall=b_recall, rudolph=b_rudolph, glows=b_glows, laugh=b_laugh,
              games=b_games, foggy=b_foggy, guide=b_guide, loved=b_loved, history=b_history, flight=b_flight,
              deliver=b_deliver, party=b_party, finale=b_finale)
