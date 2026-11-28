"""Frosty the Snowman matrix scenes, shared plan for the garage, the two windows (one stage) and the bushes.

The MegaTree carries the SuperStar story (Frosty built, the hat, kids, running through town, the traffic cop, the
sleigh away); these scenes follow the same lyric beats on the other matrices.
Words: faster-whisper (stories/lyrics/frosty.json); beats: librosa (frosty_beats.json).
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
from morph_backdrop import backdrop, pattern_sweeps  # noqa: E402,F401
from matrix_scenes import Cues  # noqa: E402
from rockin_common import (BLUE, GOLD, GREEN, ICE, PINK, RED, WHITE, XMAS, Z_BACK, Z_FRONT, Z_PIC,  # noqa: E402,F401
                           Z_WORD, bar_sweeps, sleigh_team)

LYRICS = HERE.parent / "lyrics"
COAL, CARROT, BROWN, HAT = (20, 20, 30), (255, 120, 0), (130, 70, 20), (35, 35, 45)


def cues(xsq):
    dur = float(ET.parse(xsq).getroot().findtext("head/sequenceDuration"))
    return Cues.from_files(LYRICS / "frosty.json", LYRICS / "frosty_beats.json", dur)


def plan(c):
    w = c.w
    t = [
        ("intro", 0.0),
        ("frosty", w("frosty") - 0.1),
        ("fairy", w("frosty", 17) - 0.1),
        ("magic", w("there", 26.5) - 0.1),
        ("alive", w("frosty", 38) - 0.1),
        ("sun", w("the", 52) - 0.1),
        ("village", w("down", 66) - 0.1),
        ("town", w("she", 86) - 0.1),
        ("stop", w("stop", 100) - 0.1),
        ("thump", w("thumpity") - 0.1),
        ("frosty2", w("frosty", 116.5) - 0.1),
        ("goodbye", w("frosty", 128) - 0.1),
        ("finale", w("back", 139) - 0.9),
    ]
    return [(n, t0, t[k + 1][1] if k + 1 < len(t) else c.duration) for k, (n, t0) in enumerate(t)]


def run(s, scenes):
    for name, t0, t1 in plan(s.cues):
        backdrop(s, t0, t1)
        fn = scenes.get(name)
        if fn:
            fn(s, t0, t1)


# ---------------------------------------------------------------- drawn props

def snowman(s, h, *, pipe=True, nose=True, eyes=True, hat=False, broom=False):
    """A drawn snowman h pixels tall (without hat). Arms always drawn so every variant crops to the same width;
    the hat variant is taller, so place it with hat_dy()."""
    hh = round(h * 0.28) if hat else 0
    W = round(h * 0.9)
    H = h + hh

    def draw(d, im):
        cx = W / 2
        rb, rm, rh = h * 0.24, h * 0.18, h * 0.14
        yb = H - rb - 1
        ym = yb - rb - rm + h * 0.06
        yh = ym - rm - rh + h * 0.05
        snow = (245, 250, 255, 255)
        for r, y in ((rb, yb), (rm, ym), (rh, yh)):
            d.ellipse([cx - r, y - r, cx + r, y + r], fill=snow)
        # stick arms (fix the width)
        d.line([(cx - rm * 0.8, ym - 1), (1, ym - rm * 1.1)], fill=BROWN + (255,), width=max(1, h // 30))
        d.line([(cx + rm * 0.8, ym - 1), (W - 2, ym - rm * 1.1)], fill=BROWN + (255,), width=max(1, h // 30))
        if broom:
            d.line([(W - 4, ym - rm * 1.6), (W - 8, yb + rb * 0.6)], fill=BROWN + (255,), width=max(1, h // 25))
            d.polygon([(W - 11, yb + rb * 0.3), (W - 4, yb + rb * 0.3), (W - 3, H - 1), (W - 13, H - 1)],
                      fill=(220, 180, 60, 255))
        for k in range(3):  # coal buttons
            y = ym - rm * 0.5 + k * rm * 0.5
            d.ellipse([cx - 1, y - 1, cx + 1, y + 1], fill=COAL + (255,))
        if eyes:
            e = max(1, round(h / 40))
            for dx in (-rh * 0.4, rh * 0.4):
                d.ellipse([cx + dx - e, yh - rh * 0.3 - e, cx + dx + e, yh - rh * 0.3 + e], fill=COAL + (255,))
        if nose:
            d.polygon([(cx, yh - 1), (cx, yh + 2), (cx + rh * 0.9, yh + 1)], fill=CARROT + (255,))
        if pipe:
            d.line([(cx - 1, yh + rh * 0.5), (cx - rh * 0.9, yh + rh * 0.7)], fill=BROWN + (255,),
                   width=max(1, h // 30))
            d.rectangle([cx - rh * 1.1, yh + rh * 0.2, cx - rh * 0.7, yh + rh * 0.8], fill=BROWN + (255,))
        if hat:
            top = yh - rh
            d.rectangle([cx - rh * 1.2, top - 2, cx + rh * 1.2, top], fill=HAT + (255,))  # brim
            d.rectangle([cx - rh * 0.75, top - hh, cx + rh * 0.75, top - 2], fill=HAT + (255,))
            d.rectangle([cx - rh * 0.75, top - hh * 0.4, cx + rh * 0.75, top - hh * 0.25], fill=RED + (255,))

    name = f"snowman_{h}_{int(pipe)}{int(nose)}{int(eyes)}{int(hat)}{int(broom)}"
    return s.drawn(name, W, H, draw)


def hat_dy(s, plain, hatted):
    """Shift for the hatted snowman so its body lines up with the plain one at the same (x, y)."""
    return -(s.size(hatted)[1] - s.size(plain)[1]) / 2


def top_hat(s, w):
    h = round(w * 0.8)

    def draw(d, im):
        d.rectangle([0, h - 3, w - 1, h - 1], fill=HAT + (255,))
        d.rectangle([w * 0.2, 0, w * 0.8, h - 3], fill=HAT + (255,))
        d.rectangle([w * 0.2, h * 0.55, w * 0.8, h * 0.72], fill=RED + (255,))
        d.line([(w * 0.25, 1), (w * 0.25, h * 0.5)], fill=(90, 90, 110, 255))  # silk sheen
    return s.drawn(f"tophat_{w}", w, h, draw)


def flipped(s, key):
    name = key.rsplit("/", 1)[1][:-4] + "_flip"
    return s.image(name, s.images[key].transpose(0))


def pipe_img(s, w):
    h = round(w * 0.6)

    def draw(d, im):
        d.line([(0, h * 0.3), (w * 0.6, h * 0.45)], fill=BROWN + (255,), width=max(2, w // 10))
        d.rectangle([w * 0.6, h * 0.1, w - 1, h - 1], fill=BROWN + (255,))
        d.rectangle([w * 0.62, h * 0.1, w - 2, h * 0.25], fill=(60, 30, 10, 255))
    return s.drawn(f"pipe_{w}", w, h, draw)


def hills(s, w, h):
    def draw(d, im):
        d.ellipse([-w * 0.2, h * 0.25, w * 0.55, h * 2.0], fill=(235, 245, 255, 255))
        d.ellipse([w * 0.35, h * 0.05, w * 1.2, h * 2.2], fill=(200, 225, 255, 255))
    return s.drawn(f"hills_{w}_{h}", w, h, draw)


def stop_sign(s, px):
    def draw(d, im):
        import math
        r = px / 2 - 0.5
        pts = [(px / 2 + r * math.cos(math.radians(22.5 + 45 * k)), px / 2 + r * math.sin(math.radians(22.5 + 45 * k)))
               for k in range(8)]
        d.polygon(pts, fill=(220, 0, 0, 255))
    key = s.drawn(f"stopsign_{px}", px, px, draw)
    return key


def sun_img(s, px):
    def draw(d, im):
        import math
        c = px / 2
        for k in range(12):
            a = math.radians(30 * k)
            d.line([(c + px * 0.28 * math.cos(a), c + px * 0.28 * math.sin(a)),
                    (c + px * 0.48 * math.cos(a), c + px * 0.48 * math.sin(a))], fill=(255, 150, 0, 255),
                   width=max(1, px // 14))
        d.ellipse([c - px * 0.3, c - px * 0.3, c + px * 0.3, c + px * 0.3], fill=(255, 220, 0, 255))
    return s.drawn(f"sun_{px}", px, px, draw)


def puddle(s, w):
    h = max(3, w // 5)

    def draw(d, im):
        d.ellipse([0, 0, w - 1, h - 1], fill=(120, 190, 255, 255))
        d.ellipse([w * 0.3, h * 0.2, w * 0.5, h * 0.5], fill=(255, 255, 255, 255))
    return s.drawn(f"puddle_{w}", w, h, draw)


# ================================================================ 140x60 matrix (the garage)

GY = 34  # snowman centre row on the garage


def g_intro(s, t0, t1):
    c = s.cues
    s.snow(0.0, t1, count=8, fade=1.5)
    beats = c.beats_in(1.0, t1)
    # three snowballs roll in and stack (bottom, middle, head) on beats
    for k, (r, y) in enumerate(((13, 46), (10, 30), (8, 17))):
        ball = s.drawn(f"ball_{r}", 2 * r, 2 * r, lambda d, im, r=r: d.ellipse([0, 0, 2 * r - 1, 2 * r - 1],
                                                                                fill=(245, 250, 255, 255)))
        b = beats[2 + 2 * k] if len(beats) > 2 + 2 * k else t0
        s.glide(ball, [(b, -20 if k % 2 == 0 else 160, y), (b + 0.6, 70, y), (t1, 70, y)])
        s.ring(b + 0.6, 70, y, ICE, r=18, dur=0.5)
    s.twinkle(0.5, t1, (WHITE, ICE), count=10, fade=1.0)


def g_frosty(s, t0, t1):
    c = s.cues
    pipe, nose, eyes = c.w("pipe", t0), c.w("nose", t0), c.w("eyes", t0)
    plain = snowman(s, 52, pipe=False, nose=False, eyes=False)
    s.flash([plain, snowman(s, 52, nose=False, eyes=False), snowman(s, 52, eyes=False), snowman(s, 52)],
            [t0, pipe, nose, eyes], 70, GY, end=t1)
    s.show(s.word("FROSTY", WHITE, 2), t0 + 0.2, pipe, 70, 6, enter="pop", z=Z_WORD)
    s.show(s.word("PIPE", BROWN, 2), pipe, nose, 24, 30, enter="left", z=Z_WORD)
    s.show(s.word("NOSE", CARROT, 2), nose, eyes, 116, 30, enter="right", z=Z_WORD)
    s.show(s.word("COAL", WHITE, 2), eyes, t1, 70, 6, enter="pop", z=Z_WORD)
    for t in (pipe, nose, eyes):
        s.ring(t, 70, 18, GOLD, r=20, dur=0.5)
    s.snow(t0, t1, count=5)
    bar_sweeps(s, t0, t1, (ICE, WHITE), every=2)


def g_fairy(s, t0, t1):
    c = s.cues
    snow, life = c.w("snow", t0), c.w("life", t0)
    beats = c.beats_in(t0, t1)
    s.show(snowman(s, 52), t0, t1, 70, GY, enter=None)
    s.show(s.emoji("🧒", 26), t0 + 0.3, t1, 22, 44, enter="left", hits=beats[0::2], amp=2)
    s.show(s.emoji("👧", 26), t0 + 0.6, t1, 118, 44, enter="right", hits=beats[1::2], amp=2)
    s.show(s.word("SNOW", ICE, 2), snow, life, 70, 6, enter="pop", z=Z_WORD)
    s.show(s.word("LIFE", GOLD, 2), life, t1, 70, 6, enter="pop", z=Z_WORD)
    s.ring(life, 70, GY, GOLD, r=45, dur=0.9)
    s.twinkle(life, t1, (GOLD, WHITE), count=20, steps=15, fade=0.3)
    s.snow(t0, t1, count=6)


def g_magic(s, t0, t1):
    c = s.cues
    magic, found, placed, head, dance = (c.w(k, t0) for k in ("magic", "found", "placed", "head", "dance"))
    plain, hatted = snowman(s, 52), snowman(s, 52, hat=True)
    hat = top_hat(s, 20)
    s.show(plain, t0, head, 70, GY, enter=None)
    # the silk hat: found on the left, carried over, dropped on his head
    s.show(hat, magic, found, 24, 20, enter="pop", hits=c.beats_in(magic, found), amp=2, z=Z_FRONT)
    s.twinkle(magic, head, (GOLD, PINK, WHITE), count=25, steps=12, fade=0.3)
    s.show(s.word("MAGIC", GOLD, 2), magic, found, 70, 6, enter="pop", z=Z_WORD)
    s.glide(hat, [(found, 24, 20), (placed, 70, -6), (head, 70, 2)], z=Z_FRONT)
    dy = hat_dy(s, plain, hatted)
    hits = c.beats_in(dance, t1)
    s.hold(hatted, head, t1, 70, GY + dy, hits=hits, amp=3)
    s.ring(head, 70, 10, GOLD, r=40, dur=0.8)
    s.show(s.word("DANCE", PINK, 2), dance, t1, 70, 6, enter="pop", z=Z_WORD)
    for i, b in enumerate(hits):
        s.ring(b, 24 if i % 2 == 0 else 116, 34, XMAS[i % 4], r=16, dur=0.4)


def g_alive(s, t0, t1):
    c = s.cues
    alive, laugh, play = c.w("alive", t0), c.w("laugh", t0), c.w("play", t0)
    beats = c.beats_in(t0, t1)
    plain, hatted = snowman(s, 52), snowman(s, 52, hat=True)
    dy = hat_dy(s, plain, hatted)
    s.hold(hatted, t0, t1, 70, GY + dy, hits=beats, amp=3)
    s.show(s.word("ALIVE", GREEN, 2), alive, laugh, 70, 6, enter="pop", z=Z_WORD)
    s.ring(alive, 70, GY, GREEN, r=50)
    s.show(s.emoji("😄", 22), laugh, t1, 22, 40, enter="left", hits=beats[0::2], amp=3)
    s.show(s.word("LAUGH", GOLD, 2), laugh, play, 24, 10, enter="pop", z=Z_WORD)
    s.show(s.emoji("🧒", 24), play, t1, 118, 42, enter="right", hits=beats[1::2], amp=3)
    s.show(s.word("PLAY", PINK, 2), play, t1, 116, 10, enter="pop", z=Z_WORD)
    s.twinkle(alive, t1, XMAS, count=15, fade=0.5)
    bar_sweeps(s, t0, t1)


def g_sun(s, t0, t1):
    c = s.cues
    hot, run, melt = c.w("hot", t0), c.w("run", t0), c.w("melt", t0)
    plain, hatted = snowman(s, 52), snowman(s, 52, hat=True)
    dy = hat_dy(s, plain, hatted)
    sun = sun_img(s, 30)
    s.glide(sun, [(t0, 18, 70), (hot, 18, 16), (t1, 18, 16)], z=Z_BACK)
    s.show(s.word("HOT", (255, 150, 0), 3), hot, run, 70, 6, enter="pop", z=Z_WORD)
    s.ring(hot, 18, 16, (255, 150, 0), r=30)
    s.hold(hatted, t0, run, 80, GY + dy)
    s.glide(hatted, [(run, 80, GY + dy), (melt - 0.3, 110, GY + dy)])
    s.show(s.word("RUN", GREEN, 2), run, melt, 50, 50, enter="pop", z=Z_WORD)
    # melt: shrink into a puddle
    s.pic(hatted, melt - 0.3, melt + 1.2, 110, GY + dy, to=(110, 48), scale=(100, 25))
    s.show(puddle(s, 40), melt + 0.6, t1, 110, 56, enter="fade", enter_s=0.6)
    s.show(s.emoji("💧", 12), melt, t1, 96, 24, enter="top", hits=c.beats_in(melt, t1), amp=2, z=Z_FRONT)
    s.show(s.word("MELT", ICE, 2), melt, t1, 70, 6, enter="pop", z=Z_WORD)


def g_village(s, t0, t1):
    c = s.cues
    broom, catch = c.w("broomstick", t0), c.w("catch", t0)
    houses = [("🏠", 26, 14), ("🏡", 28, 48), ("🏠", 26, 92), ("🏡", 28, 126)]
    for k, (e, px, x) in enumerate(houses):
        s.show(s.emoji(e, px, flip=k % 2 == 1), t0 + 0.25 * k, t1, x, 46, enter="bottom", z=Z_BACK)
    s.show(s.word("VILLAGE", GOLD, 2), c.w("village", t0), broom, 70, 6, enter="pop", z=Z_WORD)
    runner = snowman(s, 36, broom=True)
    runner_f = flipped(s, runner)
    # running here and there across the square
    pts = [(broom, -20, 40), (broom + 3.5, 160, 40)]
    pts += [(broom + 3.6, 160, 40), (catch - 0.3, -20, 40)]
    s.glide(runner, pts[:2])
    s.glide(runner_f, pts[2:])
    s.show(s.word("CATCH ME", RED, 2), catch, t1 - 0.4, 70, 6, enter="pop", z=Z_WORD)
    # the kids chase him back and forth through the instrumental
    kid, kid2 = s.emoji("🧒", 22), s.emoji("👧", 22)
    sweep_t = [catch + 2.2 * k for k in range(int((t1 - catch) / 2.2))]
    for k, a in enumerate(sweep_t):
        rt = k % 2 == 0
        x0, x1 = (-20, 160) if rt else (160, -20)
        s.glide(runner if rt else runner_f, [(a, x0, 30), (a + 2.1, x1, 30)], z=Z_FRONT)
        s.glide(kid, [(a + 0.3, x0, 46), (min(a + 2.4, t1), x1, 46)], z=Z_FRONT)
        s.glide(kid2, [(a + 0.6, x0, 46), (min(a + 2.7, t1), x1, 46)], z=Z_FRONT)
    s.snow(t0, t1, count=4)


def g_town(s, t0, t1):
    c = s.cues
    traffic, paused = c.w("traffic", t0), c.w("paused", t0)
    beats = c.beats_in(t0, t1)
    s.show(s.emoji("🚦", 36), t0, t1, 120, 30, enter="right", z=Z_BACK)
    runner = snowman(s, 36, hat=True)
    s.glide(runner, [(t0, -20, 38), (traffic, 40, 38), (t1, 40, 38)])
    s.show(s.word("TOWN", GOLD, 2), c.w("town", t0), traffic, 70, 6, enter="pop", z=Z_WORD)
    s.show(s.emoji("👮", 32), traffic, t1, 84, 38, enter="bottom", hits=beats[::2], amp=2)
    s.show(s.word("TRAFFIC COP", BLUE, 2), traffic, paused, 70, 6, enter="pop", z=Z_WORD)
    s.show(s.word("WAIT", WHITE, 2), paused, t1, 70, 6, enter="pop", z=Z_WORD)
    s.twinkle(t0, t1, (RED, GOLD, GREEN), count=6)


def g_stop(s, t0, t1):
    c = s.cues
    s.show(stop_sign(s, 50), t0, t1 - 0.5, 70, 30, enter="pop", exit="shrink", hits=c.beats_in(t0 + 0.5, t1)[:4])
    s.show(s.word("STOP", WHITE, 3), t0 + 0.1, t1 - 0.5, 70, 30, enter="pop", exit="shrink", z=Z_WORD)
    s.ring(t0, 70, 30, RED, r=70, dur=0.9)
    s.ring(t0 + 0.4, 70, 30, WHITE, r=70, dur=0.9)
    s.show(s.emoji("👮", 28), t0, t1, 18, 40, enter="left")
    s.show(snowman(s, 36, hat=True), t0, t1, 122, 38, enter="right")


def g_thump(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    s.show(hills(s, 140, 22), t0, t1, 70, 49, enter="bottom", z=Z_BACK)
    hopper = snowman(s, 32, hat=True)
    n = max(1, len(beats) - 1)
    for k, b in enumerate(beats[:-1]):
        x0, x1 = -10 + 160 * k / n, -10 + 160 * (k + 1) / n
        mid = (b + beats[k + 1]) / 2
        s.pic(hopper, b, mid, x0, 34, to=((x0 + x1) / 2, 18))
        s.pic(hopper, mid, beats[k + 1], (x0 + x1) / 2, 18, to=(x1, 34))
    thumps = [t for w_, t, _ in c.words if t0 <= t < t1 and w_.startswith("thump")]
    for k, t in enumerate(thumps):
        s.pic(s.word("THUMP", (WHITE, ICE, GOLD)[k % 3], 2), t, t + 0.35, 70, 8, z=Z_WORD)
    s.show(s.word("LOOK AT HIM GO", GOLD, 1), c.w("look", t0), c.w("thump", c.w("look", t0)), 70, 8,
           enter="pop", z=Z_WORD)
    s.show(s.word("HILLS OF SNOW", ICE, 1), c.w("over", t0), t1, 70, 8, enter="pop", z=Z_WORD)
    s.snow(t0, t1, count=8)


def g_frosty2(s, t0, t1):
    c = s.cues
    jolly, pipe, eyes = c.w("jolly", t0), c.w("pipe", t0), c.w("eyes", t0)
    beats = c.beats_in(t0, t1)
    plain, hatted = snowman(s, 52), snowman(s, 52, hat=True)
    s.hold(hatted, t0, t1, 70, GY + hat_dy(s, plain, hatted), hits=beats[::2], amp=2)
    s.show(s.word("JOLLY", GOLD, 2), jolly, pipe, 24, 14, enter="left", z=Z_WORD)
    s.show(s.word("HAPPY", PINK, 2), c.w("happy", t0), pipe, 116, 14, enter="right", z=Z_WORD)
    s.show(s.emoji("❄️", 18), pipe, t1, 22, 36, enter="pop", hits=beats[0::2], amp=2)
    s.show(s.emoji("❄️", 18), eyes, t1, 118, 36, enter="pop", hits=beats[1::2], amp=2)
    s.ring(jolly, 70, GY, GOLD, r=50)
    bar_sweeps(s, t0, t1, (RED, GREEN))
    s.snow(t0, t1, count=5)


def g_goodbye(s, t0, t1):
    c = s.cues
    hurry, wave, cry = c.w("hurry", t0), c.w("wave", t0), c.w("cry", t0)
    hatted = snowman(s, 44, hat=True)
    s.hold(hatted, t0, hurry, 70, 32)
    s.glide(hatted, [(hurry, 70, 32), (wave, 100, 32), (t1 - 0.6, 100, 32), (t1, 170, 32)])
    s.show(s.word("HURRY", GOLD, 2), hurry, wave, 40, 8, enter="pop", z=Z_WORD)
    s.show(s.emoji("👋", 20), wave, t1 - 0.6, 124, 18, enter="pop", hits=c.beats_in(wave, t1), amp=3, z=Z_FRONT)
    s.show(s.word("GOODBYE", WHITE, 2), wave, cry, 40, 8, enter="pop", z=Z_WORD)
    s.show(s.emoji("😢", 22), cry - 0.2, t1, 30, 36, enter="left")
    s.show(s.word("DONT CRY", ICE, 2), cry, t1, 40, 8, enter="pop", z=Z_WORD)
    s.snow(t0, t1, count=6)


def g_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.2
    back = c.w("back", t0)
    s.show(s.word("BACK ON", WHITE, 2), back, back + 2.0, 70, 22, enter="pop", z=Z_WORD)
    s.show(s.word("CHRISTMAS DAY", GOLD, 2), c.w("christmas", t0), c.w("christmas", t0) + 3.0, 70, 36,
           enter="pop", z=Z_WORD)
    a = c.w("christmas", t0) + 3.0
    s.show(snowman(s, 52, hat=True), a, end, 70, 30, enter="fade", exit="fade", exit_s=2.0, enter_s=1.0,
           hits=c.beats_in(a + 1, end - 2.5)[::2], amp=2)
    s.show(s.emoji("🎄", 24), a, end, 18, 46, enter="bottom", exit="fade", exit_s=2.0)
    s.show(s.emoji("🎄", 24), a, end, 122, 46, enter="bottom", exit="fade", exit_s=2.0)
    s.twinkle(t0, t1, XMAS, count=18, fade=2.0)
    s.snow(t0, t1, count=8, fade=2.0)


GARAGE = dict(intro=g_intro, frosty=g_frosty, fairy=g_fairy, magic=g_magic, alive=g_alive, sun=g_sun,
              village=g_village, town=g_town, stop=g_stop, thump=g_thump, frosty2=g_frosty2, goodbye=g_goodbye,
              finale=g_finale)


# ================================================================ the two windows as one stage

def wins(s):
    return tuple(s.center(m)[0] for m in s.places)  # the two windows, in --model order


WY = 26


def w_intro(s, t0, t1):
    s.snow(0.0, t1, count=6, fade=1.5)
    s.twinkle(0.5, t1, (WHITE, ICE), count=8, fade=1.0)
    L, C = wins(s)
    s.show(s.emoji("❄️", 26), 1.5, t1, L, WY, enter="fade", enter_s=1.5)
    s.show(s.emoji("❄️", 26), 2.5, t1, C, WY, enter="fade", enter_s=1.5)


def w_frosty(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    pipe, nose, eyes = c.w("pipe", t0), c.w("nose", t0), c.w("eyes", t0)
    s.show(s.emoji("⛄", 32), t0, pipe, L, WY, enter="pop")
    s.show(s.emoji("🎅", 30), t0 + 0.4, pipe, C, WY, enter="pop")
    # the parts of his face, one window then the other
    s.show(s.emoji("🥕", 28), nose, t1, C, WY, enter="right")
    s.show(pipe_img(s, 24), pipe, nose, C, WY, enter="right")
    s.show(snowman(s, 40, eyes=False, nose=False), pipe, eyes, L, WY + 2, enter=None)
    s.show(snowman(s, 40), eyes, t1, L, WY + 2, enter=None)
    for t, x in ((pipe, C), (nose, C), (eyes, L)):
        s.ring(t, x, WY, GOLD, r=24, dur=0.5)


def w_fairy(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    life = c.w("life", t0)
    s.show(s.emoji("🧒", 30), t0, t1, L, 30, enter="left", hits=beats[0::2], amp=3)
    s.show(s.emoji("👧", 30), t0 + 0.3, t1, C, 30, enter="right", hits=beats[1::2], amp=3)
    # a snowball tossed back and forth over the wall
    ball = s.drawn("ball_4", 8, 8, lambda d, im: d.ellipse([0, 0, 7, 7], fill=(245, 250, 255, 255)))
    bars = c.bars_in(t0, life)
    for k, b in enumerate(bars):
        a, z = (L, C) if k % 2 == 0 else (C, L)
        s.glide(ball, [(b, a, 22), (b + 0.6, (a + z) / 2, 2), (b + 1.2, z, 22)], z=Z_FRONT)
    s.show(s.emoji("✨", 18), life, t1, L, 8, enter="pop", z=Z_FRONT)
    s.show(s.emoji("✨", 18), life + 0.2, t1, C, 8, enter="pop", z=Z_FRONT)
    s.twinkle(life, t1, (GOLD, WHITE), count=20, steps=15, fade=0.3)


def w_magic(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    magic, found, head, dance = (c.w(k, t0) for k in ("magic", "found", "head", "dance"))
    hat = top_hat(s, 26)
    plain = snowman(s, 40)
    hatted = snowman(s, 40, hat=True)
    # the hat sits in the left window, sparkles, then floats over the wall onto Frosty in the right one
    s.show(hat, magic, found, L, 30, enter="pop", hits=c.beats_in(magic, found), amp=2, z=Z_FRONT)
    s.twinkle(magic, head, (GOLD, PINK, WHITE), count=25, steps=12, fade=0.3)
    s.glide(hat, [(found, L, 30), (head - 0.4, C, 2), (head, C, 6)], z=Z_FRONT)
    s.show(plain, t0, head, C, WY + 2, enter="right")
    s.hold(hatted, head, t1, C, WY + 2 + hat_dy(s, plain, hatted), hits=c.beats_in(dance, t1), amp=3)
    s.ring(head, C, 10, GOLD, r=30)
    s.show(s.emoji("🎶", 24), dance, t1, L, WY, enter="pop", hits=c.beats_in(dance, t1), amp=3)


def w_alive(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    laugh, play = c.w("laugh", t0), c.w("play", t0)
    plain, hatted = snowman(s, 40), snowman(s, 40, hat=True)
    dy = hat_dy(s, plain, hatted)
    # Frosty hops from window to window on the bars
    bars = c.bars_in(t0, laugh)
    pos = [L, C]
    t = t0
    for k, b in enumerate(bars + [laugh]):
        x = pos[k % 2]
        s.hold(hatted, t, b, x, WY + 2 + dy, hits=c.beats_in(t, b), amp=3)
        t = b
    s.show(s.emoji("😂", 30), laugh, play, L, WY, enter="pop")
    s.show(s.emoji("⛄", 32), laugh, t1, C, WY, enter="pop", hits=beats[1::2], amp=3)
    s.show(s.emoji("🧒", 30), play, t1, L, WY, enter="pop", hits=beats[0::2], amp=3)
    s.ring(laugh, L, WY, GOLD, r=26)
    s.ring(play, L, WY, PINK, r=26)


def w_sun(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    hot, melt = c.w("hot", t0), c.w("melt", t0)
    s.show(sun_img(s, 34), t0, t1, L, 22, enter="bottom", enter_s=1.0, hits=c.beats_in(hot, t1)[::2], amp=2)
    s.ring(hot, L, 22, (255, 150, 0), r=26)
    plain, hatted = snowman(s, 40), snowman(s, 40, hat=True)
    dy = hat_dy(s, plain, hatted)
    s.hold(hatted, t0, melt, C, WY + 2 + dy)
    s.pic(hatted, melt, melt + 1.2, C, WY + 2 + dy, to=(C, 40), scale=(100, 25))
    s.show(puddle(s, 30), melt + 0.6, t1, C, 44, enter="fade", enter_s=0.6)
    s.show(s.emoji("💦", 16), hot, t1, C - 12, 10, enter="pop", hits=c.beats_in(hot, t1), amp=2, z=Z_FRONT)


def w_village(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    broom = c.w("broomstick", t0)
    s.show(s.emoji("🏠", 30), t0, t1, L, 32, enter="bottom", z=Z_BACK)
    s.show(s.emoji("🏡", 30), t0 + 0.4, t1, C, 32, enter="bottom", z=Z_BACK)
    runner = snowman(s, 28, broom=True)
    runner_f = flipped(s, runner)
    span = s.W
    k, a = 0, broom
    while a + 2.4 < t1:  # across both windows and behind the wall, back and forth
        rt = k % 2 == 0
        x0, x1 = (-16, span + 16) if rt else (span + 16, -16)
        s.glide(runner if rt else runner_f, [(a, x0, 32), (a + 2.4, x1, 32)], z=Z_FRONT)
        if k % 2:
            s.glide(s.emoji("🧒", 20), [(a + 0.4, x0, 38), (min(a + 2.8, t1), x1, 38)], z=Z_FRONT)
        k, a = k + 1, a + 2.6
    s.snow(t0, t1, count=4)


def w_town(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    traffic = c.w("traffic", t0)
    beats = c.beats_in(t0, t1)
    s.show(s.emoji("🚦", 34), t0, t1, C, WY, enter="top")
    runner = snowman(s, 34, hat=True)
    s.show(runner, t0, t1, L, WY + 4, enter="left", hits=beats[::2], amp=2)
    s.show(s.emoji("👮", 30), traffic, t1, C, WY + 4, enter="right", z=Z_FRONT)
    s.ring(traffic, C, WY, BLUE, r=26)


def w_stop(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    for x in (L, C):
        s.show(stop_sign(s, 36), t0, t1 - 0.4, x, WY, enter="pop", exit="shrink")
        s.show(s.word("STOP", WHITE, 2), t0 + 0.1, t1 - 0.4, x, WY, enter="pop", exit="shrink", z=Z_WORD)
        s.ring(t0, x, WY, RED, r=30, dur=0.8)
        s.ring(t0 + 0.4, x, WY, WHITE, r=30, dur=0.8)


def w_thump(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    s.show(hills(s, s.W, 14), t0, t1, s.W / 2, 41, enter="bottom", z=Z_BACK)
    hopper = snowman(s, 24, hat=True)
    n = max(1, len(beats) - 1)
    for k, b in enumerate(beats[:-1]):
        x0, x1 = -10 + (s.W + 20) * k / n, -10 + (s.W + 20) * (k + 1) / n
        mid = (b + beats[k + 1]) / 2
        s.pic(hopper, b, mid, x0, 30, to=((x0 + x1) / 2, 14))
        s.pic(hopper, mid, beats[k + 1], (x0 + x1) / 2, 14, to=(x1, 30))
    s.snow(t0, t1, count=6)


def w_frosty2(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    pipe, nose, eyes = c.w("pipe", t0), c.w("nose", t0), c.w("eyes", t0)
    beats = c.beats_in(t0, t1)
    s.show(snowman(s, 40, hat=True), t0, t1, L, WY, enter="pop", hits=beats[0::2], amp=2)
    s.flash([pipe_img(s, 24), s.emoji("🥕", 26), s.emoji("⚫", 16)], [pipe, nose, eyes], C, WY, end=t1)
    s.show(s.emoji("😊", 30), t0, pipe, C, WY, enter="pop")
    for t in (pipe, nose, eyes):
        s.ring(t, C, WY, GOLD, r=24, dur=0.5)


def w_goodbye(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    wave, cry = c.w("wave", t0), c.w("cry", t0)
    hatted = snowman(s, 36, hat=True)
    s.glide(hatted, [(t0, C, WY + 4), (wave, C, WY + 4), (t1, s.W + 30, WY + 4)])
    s.show(s.emoji("👋", 24), wave, t1, L, WY, enter="pop", hits=c.beats_in(wave, t1), amp=3)
    s.show(s.emoji("😢", 28), cry, t1, L, WY, enter="pop", z=Z_FRONT)
    s.snow(t0, t1, count=5)


def w_finale(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    end = t1 - 0.2
    s.show(s.emoji("🎄", 34), t0, end, L, WY, enter="pop", exit="fade", exit_s=2.0,
           hits=c.beats_in(t0 + 0.4, end - 2.5)[0::2], amp=2)
    s.show(snowman(s, 40, hat=True), t0 + 0.4, end, C, WY, enter="pop", exit="fade", exit_s=2.0,
           hits=c.beats_in(t0 + 0.4, end - 2.5)[1::2], amp=2)
    s.twinkle(t0, t1, XMAS, count=15, fade=2.0)
    s.snow(t0, t1, count=6, fade=2.0)


WINDOWS = dict(intro=w_intro, frosty=w_frosty, fairy=w_fairy, magic=w_magic, alive=w_alive, sun=w_sun,
               village=w_village, town=w_town, stop=w_stop, thump=w_thump, frosty2=w_frosty2, goodbye=w_goodbye,
               finale=w_finale)


# ================================================================ 200x42 matrix: 8 bushes, 25 px each

def bx(i):
    return 12.5 + 25 * i


BY = 22


def b_intro(s, t0, t1):
    c = s.cues
    flake = s.emoji("❄️", 20)
    for i in range(8):
        s.show(flake, c.beats_in(1.0, t1)[i] if len(c.beats_in(1.0, t1)) > i else t0, t1, bx(i), BY,
               enter="top", enter_s=0.4)
    s.snow(0.0, t1, count=4, fade=1.5)


def b_frosty(s, t0, t1):
    c = s.cues
    pipe, nose, eyes = c.w("pipe", t0), c.w("nose", t0), c.w("eyes", t0)
    stages = [snowman(s, 36, pipe=False, nose=False, eyes=False), snowman(s, 36, nose=False, eyes=False),
              snowman(s, 36, eyes=False), snowman(s, 36)]
    for i in range(8):
        s.flash(stages, [t0 + 0.08 * i, pipe, nose, eyes], bx(i), BY + 2, end=t1)


def b_fairy(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    life = c.w("life", t0)
    kids = [s.emoji("🧒", 24), s.emoji("👧", 24)]
    for i in range(8):
        s.show(kids[i % 2], t0, life, bx(i), BY, enter="bottom", hits=beats[i % 2::2], amp=3)
        s.show(s.emoji("✨", 20), life + 0.05 * i, t1, bx(i), BY, enter="pop")
    s.twinkle(life, t1, (GOLD, WHITE), count=12, fade=0.3)


def b_magic(s, t0, t1):
    c = s.cues
    magic, head = c.w("magic", t0), c.w("head", t0)
    hat = top_hat(s, 20)
    hatted = snowman(s, 38, hat=True)
    beats = c.beats_in(head, t1)
    for i in range(8):
        s.show(hat, magic + 0.15 * i, head, bx(i), BY, enter="top", hits=c.beats_in(magic, head)[i % 2::2], amp=2)
        s.hold(hatted, head, t1, bx(i), BY + 1, hits=beats[i % 2::2], amp=3)
    for i in range(8):
        s.ring(head + 0.05 * i, bx(i), 6, GOLD, r=12, dur=0.5)


def b_alive(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    keys = [snowman(s, 38, hat=True), s.emoji("🧒", 24), s.emoji("😄", 22), s.emoji("👧", 24)]
    for i in range(8):
        s.show(keys[i % 4], t0 + 0.05 * i, t1, bx(i), BY + (1 if i % 4 == 0 else 0), enter="bottom",
               hits=beats[i % 2::2], amp=3)


def b_sun(s, t0, t1):
    c = s.cues
    hot, melt = c.w("hot", t0), c.w("melt", t0)
    sun = sun_img(s, 24)
    hatted = snowman(s, 38, hat=True)
    for i in range(8):
        s.show(sun if i % 2 == 0 else hatted, t0 + 0.05 * i, melt, bx(i), BY, enter="pop",
               hits=c.beats_in(hot, melt)[i % 2::2], amp=2)
        if i % 2:
            s.pic(hatted, melt, melt + 1.0, bx(i), BY, to=(bx(i), 34), scale=(100, 25))
            s.show(puddle(s, 22), melt + 0.5, t1, bx(i), 38, enter="fade", enter_s=0.5)
        else:
            s.show(sun, melt, t1, bx(i), BY, enter=None)


def b_village(s, t0, t1):
    c = s.cues
    broom = c.w("broomstick", t0)
    for i in range(8):
        s.show(s.emoji("🏠" if i % 2 == 0 else "🏡", 22), t0 + 0.1 * i, t1, bx(i), BY + 2, enter="bottom", z=Z_BACK)
    runner = snowman(s, 30, broom=True)
    runner_f = flipped(s, runner)
    k, a = 0, broom
    while a + 3.0 < t1:
        rt = k % 2 == 0
        x0, x1 = (-16, 216) if rt else (216, -16)
        s.glide(runner if rt else runner_f, [(a, x0, 24), (a + 3.0, x1, 24)], z=Z_FRONT)
        k, a = k + 1, a + 3.2


def b_town(s, t0, t1):
    c = s.cues
    traffic = c.w("traffic", t0)
    cars = [s.emoji("🚗", 18), s.emoji("🚕", 18), s.emoji("🚙", 18, flip=True)]
    for k, a in enumerate(c.bars_in(t0, t1)):
        rt = k % 2 == 0
        s.glide(cars[k % 3] if rt else s.emoji("🚙", 18, flip=True), [(a, -12 if rt else 212, 32),
                                                                      (a + 2.2, 212 if rt else -12, 32)])
    for i in range(8):
        s.show(s.emoji("🚦", 20) if i % 2 == 0 else s.emoji("👮", 20), traffic + 0.08 * i, t1, bx(i), 14,
               enter="top")


def b_stop(s, t0, t1):
    sign = stop_sign(s, 22)
    for i in range(8):
        s.show(sign, t0 + 0.04 * i, t1 - 0.3, bx(i), BY, enter="pop", exit="shrink")
        s.show(s.word("STOP", WHITE, 1), t0 + 0.04 * i + 0.1, t1 - 0.3, bx(i), BY, enter="pop", exit="shrink",
               z=Z_WORD)
        s.ring(t0 + 0.04 * i, bx(i), BY, RED, r=14, dur=0.5)


def b_thump(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    hopper = snowman(s, 30, hat=True)
    # one bush per beat, there and back
    path = list(range(8)) + list(range(6, 0, -1))
    for k, b in enumerate(beats[:-1]):
        i, j = path[k % len(path)], path[(k + 1) % len(path)]
        mid = (b + beats[k + 1]) / 2
        s.pic(hopper, b, mid, bx(i), 26, to=((bx(i) + bx(j)) / 2, 12))
        s.pic(hopper, mid, beats[k + 1], (bx(i) + bx(j)) / 2, 12, to=(bx(j), 26))
        s.ring(beats[k + 1], bx(j), 38, ICE, r=10, dur=0.35)
    s.snow(t0, t1, count=4)


def b_frosty2(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    keys = [snowman(s, 38, hat=True), s.emoji("❄️", 20)]
    for i in range(8):
        s.show(keys[i % 2], t0 + 0.06 * i, t1, bx(i), BY, enter="top", hits=beats[i % 2::2], amp=3)


def b_goodbye(s, t0, t1):
    c = s.cues
    wave = c.w("wave", t0)
    hatted = snowman(s, 34, hat=True)
    s.glide(hatted, [(t0, -14, 24), (t1, 214, 24)], z=Z_FRONT)
    for i in range(8):
        s.show(s.emoji("👋", 18), wave + 0.1 * i, t1, bx(i), 12, enter="pop", hits=c.beats_in(wave, t1)[i % 2::2],
               amp=3, z=Z_BACK)


def b_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.2
    keys = [s.emoji("🎄", 24), snowman(s, 38, hat=True)]
    beats = c.beats_in(t0 + 0.3, end - 2.5)
    for i in range(8):
        s.show(keys[i % 2], t0 + 0.05 * i, end, bx(i), BY, enter="pop", exit="fade", exit_s=2.0,
               hits=beats[i % 2::2], amp=2)
    s.twinkle(t0, t1, XMAS, count=10, fade=2.0)


BUSHES = dict(intro=b_intro, frosty=b_frosty, fairy=b_fairy, magic=b_magic, alive=b_alive, sun=b_sun,
              village=b_village, town=b_town, stop=b_stop, thump=b_thump, frosty2=b_frosty2, goodbye=b_goodbye,
              finale=b_finale)
