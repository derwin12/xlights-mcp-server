"""Jingle Bell Rock matrix scenes, shared plan for the garage, the two windows (one stage) and the bushes.

The MegaTree carries the SuperStar story (toy soldier, swinging bells, ROCK, FUN, dancers, a clock, the running
horse and the sleigh); these scenes follow the same lyric beats on the other matrices. The song is two passes of
the same verse, so each scene is written once and placed twice; optional words fall back when a pass lacks them.
Words: faster-whisper (stories/lyrics/jingle_bell_rock.json); beats: librosa (jingle_bell_rock_beats.json).
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
from morph_backdrop import backdrop, pattern_sweeps  # noqa: E402,F401
from matrix_scenes import Cues, norm  # noqa: E402
from rockin_common import (BLUE, GOLD, GREEN, ICE, PINK, PURPLE, RED, WHITE, XMAS, Z_BACK, Z_FRONT,  # noqa: E402,F401
                           Z_PIC, Z_WORD, bar_sweeps, sleigh_team)

LYRICS = HERE.parent / "lyrics"
CLOCKS = ["🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚"]


def cues(xsq):
    dur = float(ET.parse(xsq).getroot().findtext("head/sequenceDuration"))
    return Cues.from_files(LYRICS / "jingle_bell_rock.json", LYRICS / "jingle_bell_rock_beats.json", dur)


def plan(c):
    w = c.w
    t = [
        ("intro", 0.0),
        ("bells", w("jingle") - 0.1),
        ("snow", w("snowing") - 0.1),
        ("rock", w("jingle", 23.4) - 0.1),
        ("chime", w("jingle", 28.1) - 0.1),
        ("square", w("dancin") - 0.1),
        ("frosty", w("in", 36.4) - 0.1),
        ("night", w("right", 42) - 0.4),
        ("swell", w("jingle", 47.5) - 0.1),
        ("sleigh", w("to", 52) - 0.1),
        ("giddy", w("giddy") - 0.1),
        ("clock", w("jingle", 60) - 0.1),
        ("mingle", w("mix") - 0.1),
        ("rock", w("that", 67.5) - 0.1),
        ("bells", w("jingle", 71.9) - 0.1),
        ("chime", w("jingle", 75.7) - 0.1),
        ("square", w("dancin", 80) - 0.1),
        ("frosty", w("in", 83.8) - 0.1),
        ("night", w("got") - 0.1),
        ("swell", w("jingle", 96) - 0.1),
        ("sleigh", w("to", 100.6) - 0.1),
        ("giddy", w("giddy", 104) - 0.1),
        ("clock", w("jingle", 108) - 0.1),
        ("mingle", w("mix", 112.5) - 0.1),
        ("finale", w("that", 117) - 0.1),
    ]
    return [(n, t0, t[k + 1][1] if k + 1 < len(t) else c.duration) for k, (n, t0) in enumerate(t)]


def run(s, scenes):
    for name, t0, t1 in plan(s.cues):
        backdrop(s, t0, t1)
        fn = scenes.get(name)
        if fn:
            fn(s, t0, t1)


def opt(c, word, t0, t1, default=None):
    """First sung word starting with `word` inside [t0, t1), else default."""
    key = norm(word)
    return next((s for w_, s, _ in c.words if t0 <= s < t1 and w_.startswith(key)), default)


def words_in(c, word, t0, t1):
    key = norm(word)
    return [s for w_, s, _ in c.words if t0 <= s < t1 and w_.startswith(key)]


def swing_bell(s, key_l, key_r, t0, t1, x, y, beats, z=Z_PIC):
    """A bell swinging: alternate mirrored pictures on each beat, nudged left/right."""
    ts = [t0] + [b for b in beats if t0 < b < t1]
    for i, (a, b) in enumerate(zip(ts, ts[1:] + [t1])):
        dx = -2 if i % 2 == 0 else 2
        s.pic(key_l if i % 2 == 0 else key_r, a, b, x + dx, y, z=z)


def basket(s, w):
    h = round(w * 0.75)

    def draw(d, im):
        d.ellipse([w * 0.1, 0, w * 0.9, h * 0.7], outline=(160, 100, 40, 255), width=max(1, w // 12))  # handle
        d.polygon([(0, h * 0.4), (w - 1, h * 0.4), (w * 0.85, h - 1), (w * 0.15, h - 1)], fill=(170, 110, 50, 255))
        for k in range(1, 4):
            y = h * 0.4 + k * h * 0.15
            d.line([(w * 0.08, y), (w * 0.92, y)], fill=(120, 70, 30, 255))
        for k, col in enumerate((RED, GREEN, GOLD)):  # bells peeking out
            cx = w * (0.3 + 0.2 * k)
            d.ellipse([cx - w * 0.1, h * 0.25, cx + w * 0.1, h * 0.45], fill=col + (255,))
    return s.drawn(f"basket_{w}", w, h, draw)


# ================================================================ 140x60 matrix (the garage)

def g_intro(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    guard = s.emoji("💂", 30)
    s.glide(guard, [(0.2, -16, 38), (t1 - 0.5, 70, 38), (t1, 70, 38)])
    for i, b in enumerate(beats[2::2]):
        s.ring(b, 70 if i % 2 else 30, 20, (RED, GREEN)[i % 2], r=14, dur=0.4)
    s.show(s.word("JINGLE", RED, 2), beats[4] if len(beats) > 4 else t0, t1, 70, 8, enter="pop", z=Z_WORD)
    s.twinkle(0.3, t1, (RED, GREEN, GOLD), count=10, fade=1.0)


def g_bells(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    rock, swing = opt(c, "rock", t0, t1), opt(c, "swing", t0, t1)
    ring = opt(c, "rain", t0, t1) or opt(c, "chime", t0, t1)
    bl, br = s.emoji("🔔", 30), s.emoji("🔔", 30, flip=True)
    swing_bell(s, bl, br, t0, t1, 30, 32, beats)
    swing_bell(s, br, bl, t0, t1, 110, 32, beats)
    jingles = words_in(c, "jingle", t0, t1)
    for i, t in enumerate(jingles):
        s.ring(t, 30 if i % 2 == 0 else 110, 32, (GOLD, WHITE)[i % 2], r=22, dur=0.45)
    s.show(s.word("JINGLE", GREEN, 2), t0, rock or t1, 70, 10, enter="pop", z=Z_WORD)
    if rock:
        s.show(s.word("ROCK", RED, 3), rock, swing or t1, 70, 28, enter="pop", z=Z_WORD)
        s.ring(rock, 70, 28, GOLD, r=60, dur=0.8)
    if swing:
        s.show(s.word("SWING", GOLD, 2), swing, ring or t1, 70, 28, enter="left", z=Z_WORD)
    if ring:
        s.show(s.word("RING", GOLD, 2), ring, t1, 70, 28, enter="pop", z=Z_WORD)
        s.ring(ring, 70, 28, WHITE, r=60)
    bar_sweeps(s, t0, t1, (RED, GREEN))


def g_snow(s, t0, t1):
    c = s.cues
    fun, hop = c.w("fun", t0), c.w("hop", t0)
    beats = c.beats_in(t0, t1)
    s.snow(t0, t1, count=12, speed=20)
    s.show(s.emoji("🌬", 30), t0, fun, 24, 28, enter="left")
    s.show(s.word("SNOWING", ICE, 2), t0, c.w("blowing", t0), 84, 14, enter="pop", z=Z_WORD)
    s.show(s.word("BLOWING", WHITE, 2), c.w("blowing", t0), fun, 84, 14, enter="right", z=Z_WORD)
    for k in range(4):  # gusts across
        a = t0 + 0.6 * k
        s.sweep(a, a + 1.0, (ICE, WHITE)[k % 2], "left", band=(30 + 6 * k, 32 + 6 * k))
    s.show(basket(s, 36), fun, t1, 40, 38, enter="bottom", hits=c.beats_in(fun, hop), amp=2)
    s.show(s.word("FUN", GOLD, 3), fun, hop, 100, 22, enter="pop", z=Z_WORD)
    s.show(s.emoji("💃", 26), hop, t1, 90, 40, enter="bottom", hits=c.beats_in(hop, t1), amp=5)
    s.show(s.emoji("🕺", 26), hop, t1, 118, 40, enter="bottom", hits=c.beats_in(hop + 0.25, t1), amp=5)
    s.show(s.word("HOP", PINK, 2), hop, t1, 104, 8, enter="pop", z=Z_WORD)
    s.ring(hop, 104, 40, PINK, r=30)


def g_rock(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    rock = opt(c, "rock", t0, t1, t0 + 1)
    s.show(s.emoji("🎸", 40), t0, t1, 30, 32, enter="left", hits=beats, amp=3)
    s.show(s.emoji("🔔", 26), t0 + 0.3, t1, 112, 32, enter="right", hits=beats[1::2], amp=3)
    s.show(s.word("JINGLE BELL", GREEN, 2), t0, rock, 94, 8, enter="pop", z=Z_WORD)
    s.show(s.word("ROCK", RED, 3), rock, t1, 80, 30, enter="pop", hits=c.beats_in(rock, t1), amp=2, z=Z_WORD)
    s.ring(rock, 80, 30, GOLD, r=60, dur=0.8)
    bar_sweeps(s, t0, t1, (GOLD, RED))


def g_chime(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    time = opt(c, "time", t0, t1) or opt(c, "chime", t0, t1, t0 + 1)
    s.flash([s.emoji(e, 34) for e in CLOCKS], [t0] + beats, 30, 30, end=t1)
    for i, b in enumerate(beats):
        s.ring(b, 110, 30, (GOLD, WHITE)[i % 2], r=26, dur=0.4)
    s.show(s.emoji("🔔", 30), t0, t1, 110, 30, enter="pop", hits=beats, amp=2)
    s.show(s.word("CHIME", GOLD, 2), t0 + 0.2, time, 70, 10, enter="pop", z=Z_WORD)
    s.show(s.word("TIME", WHITE, 2), time, t1, 70, 10, enter="pop", z=Z_WORD)


def g_square(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    square = opt(c, "square", t0, t1, t1 - 1)
    s.show(s.emoji("💃", 30), t0, t1, 24, 38, enter="left", hits=beats[0::2], amp=4)
    s.show(s.emoji("🕺", 30), t0, t1, 116, 38, enter="right", hits=beats[1::2], amp=4)
    s.show(s.emoji("🎄", 32), t0 + 0.3, t1, 70, 34, enter="bottom", hits=beats, amp=2)
    s.show(s.word("DANCIN", PINK, 2), t0, square, 70, 7, enter="pop", z=Z_WORD)
    s.show(s.word("SQUARE", GOLD, 2), square, t1, 70, 7, enter="pop", z=Z_WORD)
    s.twinkle(t0, t1, (PINK, GOLD, BLUE), count=12)


def g_frosty(s, t0, t1):
    c = s.cues
    frosty = opt(c, "frosty", t0, t1, t0 + 0.5)
    bright = opt(c, "bright", t0, t1)
    s.show(s.emoji("❄️", 40), frosty, t1, 70, 32, enter="pop", hits=c.beats_in(frosty, t1)[::2], amp=2)
    s.show(s.word("FROSTY", ICE, 2), frosty, bright or t1, 70, 7, enter="pop", z=Z_WORD)
    s.snow(t0, t1, count=8)
    for b in c.bars_in(t0, t1):
        s.ring(b, 70, 32, ICE, r=50, dur=0.8)
    if bright:
        s.show(s.emoji("✨", 22), bright, t1, 24, 30, enter="pop", z=Z_FRONT)
        s.show(s.emoji("✨", 22), bright + 0.2, t1, 116, 30, enter="pop", z=Z_FRONT)
        s.show(s.word("BRIGHT", GOLD, 2), bright, t1, 70, 7, enter="pop", z=Z_WORD)
        s.twinkle(bright, t1, (GOLD, WHITE), count=25, steps=12, fade=0.3)


def g_night(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    rock = opt(c, "rock", t0, t1, t0 + 1.5)
    s.show(s.emoji("🌙", 26), t0, t1, 18, 14, enter="top", z=Z_BACK)
    s.twinkle(t0, t1, (WHITE, GOLD), count=15)
    s.show(s.word("RIGHT TIME", WHITE, 2), t0, rock, 80, 14, enter="pop", z=Z_WORD)
    s.show(s.emoji("🎸", 34), rock, t1, 40, 36, enter="pop", hits=c.beats_in(rock, t1), amp=3)
    s.show(s.word("ROCK", RED, 3), rock, t1, 96, 24, enter="pop", z=Z_WORD)
    s.show(s.word("ALL NIGHT", PURPLE, 2), opt(c, "night", t0, t1, rock + 0.8), t1, 96, 44, enter="pop", z=Z_WORD)
    for i, b in enumerate(c.beats_in(rock, t1)):
        s.ring(b, 40, 36, XMAS[i % 4], r=22, dur=0.4)
    bar_sweeps(s, t0, t1, (PURPLE, BLUE))


def g_swell(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    swell = opt(c, "swell", t0, t1, t0 + 2)
    s.show(s.emoji("🔔", 30), t0, t1, 28, 32, enter="left", hits=beats[0::2], amp=3)
    s.show(s.emoji("🎉", 32), swell, t1, 112, 32, enter="pop", hits=c.beats_in(swell, t1), amp=2)
    s.show(s.word("SWELL", PINK, 3), swell, t1, 70, 30, enter="pop", z=Z_WORD)
    s.ring(swell, 112, 32, GOLD, r=40)
    s.twinkle(swell, t1, (PINK, GOLD, BLUE, GREEN), count=25, steps=12, fade=0.3)


def g_sleigh(s, t0, t1):
    c = s.cues
    horse, sled = s.emoji("🐎", 30, flip=True), s.emoji("🛷", 26, flip=True)
    s.glide(horse, [(t0, -20, 34), (t1, 140, 34)])
    s.glide(sled, [(t0, -52, 38), (t1, 108, 38)])
    s.show(s.word("ONE HORSE", GOLD, 2), opt(c, "one", t0, t1, t0 + 1), t1, 70, 8, enter="pop", z=Z_WORD)
    s.snow(t0, t1, count=8, speed=20)


def g_giddy(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    feet = opt(c, "feet", t0, t1, t1 - 1)
    horse = s.emoji("🐎", 36, flip=True)
    s.hold(horse, t0, t1, 70, 34, hits=beats, amp=6)
    for i, b in enumerate(beats):
        s.ring(b + 0.2, 70, 54, (GOLD, WHITE)[i % 2], r=18, dur=0.35)
    s.show(s.word("GIDDY UP", RED, 2), t0, feet, 70, 7, enter="pop", z=Z_WORD)
    s.show(s.word("PICK UP YOUR FEET", GREEN, 1), feet - 0.6, t1, 70, 7, enter="pop", z=Z_WORD)
    s.show(s.emoji("🔔", 18), t0, t1, 20, 30, enter="left", hits=beats[0::2], amp=4)
    s.show(s.emoji("🔔", 18, flip=True), t0, t1, 120, 30, enter="right", hits=beats[1::2], amp=4)


def g_clock(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    s.flash([s.emoji(e, 44) for e in CLOCKS], [t0] + beats, 100, 32, end=t1)
    s.show(s.word("AROUND", GOLD, 2), t0, t1, 40, 22, enter="left", z=Z_WORD)
    s.show(s.word("CLOCK", WHITE, 2), opt(c, "clock", t0, t1, t0 + 1.5), t1, 40, 40, enter="left", z=Z_WORD)
    for i, b in enumerate(beats):
        s.ring(b, 100, 32, (RED, GREEN)[i % 2], r=36, dur=0.45)


def g_mingle(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    she, he, pair = s.emoji("💃", 26), s.emoji("🕺", 26), s.emoji("👯", 28)
    s.glide(she, [(t0, 20, 40), (t0 + (t1 - t0) / 2, 60, 40), (t1, 20, 40)])
    s.glide(he, [(t0, 120, 40), (t0 + (t1 - t0) / 2, 80, 40), (t1, 120, 40)])
    s.show(pair, t0 + (t1 - t0) / 2 - 0.3, t1, 70, 18, enter="pop", hits=beats, amp=2, z=Z_FRONT)
    s.show(s.word("MIX", PINK, 2), t0, t1, 24, 10, enter="pop", z=Z_WORD)
    s.show(s.word("MINGLE", GOLD, 2), opt(c, "ming", t0, t1) or opt(c, "mang", t0, t1) or t0 + 1, t1, 112, 10, enter="pop", z=Z_WORD)
    s.twinkle(t0, t1, (PINK, GOLD, GREEN), count=15, steps=15)


def g_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.2
    rock = words_in(c, "rock", t0, t1)
    last = rock[-1] if rock else t0 + 5
    beats = c.beats_in(t0, last)
    s.show(s.emoji("🎸", 34), t0, end, 22, 36, enter="left", exit="fade", exit_s=1.5, hits=beats, amp=3)
    s.show(s.emoji("🔔", 30), t0, end, 118, 34, enter="right", exit="fade", exit_s=1.5, hits=beats[1::2], amp=3)
    s.show(s.word("JINGLE BELL", GREEN, 2), t0, last, 70, 16, enter="pop", z=Z_WORD)
    s.show(s.word("ROCK", RED, 3), last, end, 70, 30, enter="pop", exit="fade", exit_s=1.5, z=Z_WORD)
    s.ring(last, 70, 30, GOLD, r=70, dur=1.0)
    s.twinkle(t0, t1, XMAS, count=20, fade=1.5)
    for b in c.bars_in(last, end - 1.5):
        s.ring(b, 70, 30, XMAS[int(b) % 4], r=60, dur=0.8)


GARAGE = dict(intro=g_intro, bells=g_bells, snow=g_snow, rock=g_rock, chime=g_chime, square=g_square,
              frosty=g_frosty, night=g_night, swell=g_swell, sleigh=g_sleigh, giddy=g_giddy, clock=g_clock,
              mingle=g_mingle, finale=g_finale)


# ================================================================ the two windows as one stage

def wins(s):
    return tuple(s.center(m)[0] for m in s.places)  # the two windows, in --model order


WY = 26


def w_intro(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    guard = s.emoji("💂", 28)
    # the toy soldier marches across both windows, behind the wall
    s.glide(guard, [(0.3, -16, 30), (t1, s.W + 16, 30)])
    s.twinkle(0.3, t1, (RED, GREEN, GOLD), count=8, fade=1.0)


def w_bells(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    bl, br = s.emoji("🔔", 30), s.emoji("🔔", 30, flip=True)
    swing_bell(s, bl, br, t0, t1, L, WY, beats)
    swing_bell(s, br, bl, t0, t1, C, WY, beats)
    for i, t in enumerate(words_in(c, "jingle", t0, t1)):
        s.ring(t, L if i % 2 == 0 else C, WY, (GOLD, WHITE)[i % 2], r=24, dur=0.45)
    ring = opt(c, "rain", t0, t1) or opt(c, "chime", t0, t1)
    if ring:
        s.twinkle(ring, t1, (GOLD, WHITE), count=20, steps=12, fade=0.3)


def w_snow(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    fun, hop = c.w("fun", t0), c.w("hop", t0)
    s.snow(t0, t1, count=10, speed=20)
    s.show(s.emoji("🌬", 28), t0, fun, L, WY, enter="left")
    # a gust carries a snowflake from the left window into the right one
    s.glide(s.emoji("❄️", 16), [(t0 + 0.5, L + 10, WY), (fun - 0.3, C, WY - 10)], z=Z_FRONT)
    s.show(basket(s, 30), fun, hop, C, WY + 4, enter="bottom")
    s.show(s.emoji("💃", 28), hop, t1, L, WY + 4, enter="bottom", hits=c.beats_in(hop, t1), amp=5)
    s.show(s.emoji("🕺", 28), hop, t1, C, WY + 4, enter="bottom", hits=c.beats_in(hop + 0.25, t1), amp=5)


def w_rock(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    rock = opt(c, "rock", t0, t1, t0 + 1)
    s.show(s.emoji("🎸", 32), t0, t1, L, WY, enter="left", hits=beats, amp=3)
    s.show(s.word("ROCK", RED, 2), rock, t1, C, WY, enter="pop", hits=c.beats_in(rock, t1), amp=2, z=Z_WORD)
    s.ring(rock, C, WY, GOLD, r=28)


def w_chime(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    s.flash([s.emoji(e, 32) for e in CLOCKS], [t0] + beats, L, WY, end=t1)
    s.show(s.emoji("🔔", 30), t0, t1, C, WY, enter="pop", hits=beats, amp=2)
    for i, b in enumerate(beats):
        s.ring(b, C, WY, (GOLD, WHITE)[i % 2], r=24, dur=0.4)


def w_square(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    # the dancers swap windows, crossing behind the wall
    she, he = s.emoji("💃", 30), s.emoji("🕺", 30)
    mid = t0 + (t1 - t0) / 2
    s.glide(she, [(t0, L, WY), (mid - 0.6, L, WY), (mid + 0.6, C, WY), (t1, C, WY)])
    s.glide(he, [(t0, C, WY), (mid - 0.6, C, WY), (mid + 0.6, L, WY), (t1, L, WY)])
    s.twinkle(t0, t1, (PINK, GOLD, BLUE), count=10)
    for i, b in enumerate(beats):
        s.ring(b, L if i % 2 == 0 else C, WY, (PINK, GOLD)[i % 2], r=22, dur=0.4)


def w_frosty(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    bright = opt(c, "bright", t0, t1)
    s.show(s.emoji("❄️", 32), t0, t1, L, WY, enter="pop", hits=c.beats_in(t0, t1)[0::2], amp=2)
    s.show(s.emoji("⛄", 32), t0 + 0.3, bright or t1, C, WY, enter="pop")
    if bright:
        s.show(s.emoji("🌟", 32), bright, t1, C, WY, enter="pop", hits=c.beats_in(bright, t1), amp=2)
        s.twinkle(bright, t1, (GOLD, WHITE), count=20, steps=12, fade=0.3)
    s.snow(t0, t1, count=6)


def w_night(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    rock = opt(c, "rock", t0, t1, t0 + 1.5)
    s.show(s.emoji("🌙", 28), t0, t1, L, 18, enter="top")
    s.show(s.emoji("🎸", 32), rock, t1, C, WY, enter="pop", hits=c.beats_in(rock, t1), amp=3)
    s.twinkle(t0, t1, (WHITE, GOLD), count=12)
    bar_sweeps(s, t0, t1, (PURPLE, BLUE))


def w_swell(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    swell = opt(c, "swell", t0, t1, t0 + 2)
    s.show(s.emoji("🔔", 30), t0, t1, L, WY, enter="pop", hits=c.beats_in(t0, t1)[0::2], amp=3)
    s.show(s.emoji("🎉", 30), swell, t1, C, WY, enter="pop", hits=c.beats_in(swell, t1), amp=2)
    s.ring(swell, C, WY, GOLD, r=28)


def w_sleigh(s, t0, t1):
    # horse and sleigh cross the left window, go behind the wall and come out in the right one
    horse, sled = s.emoji("🐎", 24, flip=True), s.emoji("🛷", 22, flip=True)
    s.glide(horse, [(t0, -16, 28), (t1, s.W + 16, 28)])
    s.glide(sled, [(t0 + 0.5, -16, 32), (t1 + 0.5, s.W + 16, 32)])
    s.snow(t0, t1, count=6, speed=20)


def w_giddy(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    horse = s.emoji("🐎", 30, flip=True)
    # the horse hops from window to window, one beat each
    ts = [t0] + beats
    for i, (a, b) in enumerate(zip(ts, ts[1:] + [t1])):
        s.pic(horse, a, b, L if i % 2 == 0 else C, WY, z=Z_PIC)
        s.ring(a, L if i % 2 == 0 else C, 44, GOLD, r=16, dur=0.35)


def w_clock(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    faces = [s.emoji(e, 34) for e in CLOCKS]
    s.flash(faces, [t0] + beats, L, WY, end=t1)
    s.flash(faces[6:] + faces[:6], [t0] + beats, C, WY, end=t1)


def w_mingle(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    s.show(s.emoji("👯", 32), t0, t1, L, WY, enter="left", hits=beats[0::2], amp=3)
    s.show(s.emoji("🎶", 28), t0 + 0.3, t1, C, WY, enter="right", hits=beats[1::2], amp=3)
    s.twinkle(t0, t1, (PINK, GOLD, GREEN), count=12)


def w_finale(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    end = t1 - 0.2
    rock = words_in(c, "rock", t0, t1)
    last = rock[-1] if rock else t0 + 5
    s.show(s.emoji("🔔", 32), t0, end, L, WY, enter="pop", exit="fade", exit_s=1.5,
           hits=c.beats_in(t0, last)[0::2], amp=3)
    s.show(s.emoji("🎸", 32), t0 + 0.3, end, C, WY, enter="pop", exit="fade", exit_s=1.5,
           hits=c.beats_in(t0, last)[1::2], amp=3)
    s.ring(last, L, WY, GOLD, r=30)
    s.ring(last, C, WY, GOLD, r=30)
    s.twinkle(t0, t1, XMAS, count=15, fade=1.5)


WINDOWS = dict(intro=w_intro, bells=w_bells, snow=w_snow, rock=w_rock, chime=w_chime, square=w_square,
               frosty=w_frosty, night=w_night, swell=w_swell, sleigh=w_sleigh, giddy=w_giddy, clock=w_clock,
               mingle=w_mingle, finale=w_finale)


# ================================================================ 200x42 matrix: 8 bushes, 25 px each

def bx(i):
    return 12.5 + 25 * i


BY = 22


def b_intro(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    guard = s.emoji("💂", 24)
    for i in range(8):
        b = beats[i] if i < len(beats) else t0
        s.show(guard, b, t1, bx(i), BY, enter="bottom", enter_s=0.3, hits=beats[i % 2::2], amp=2)


def b_bells(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    bl, br = s.emoji("🔔", 22), s.emoji("🔔", 22, flip=True)
    for i in range(8):
        a, b = (bl, br) if i % 2 == 0 else (br, bl)
        swing_bell(s, a, b, t0, t1, bx(i), BY, beats)
    for k, t in enumerate(words_in(c, "jingle", t0, t1)):
        i = (k * 3) % 8
        s.ring(t, bx(i), BY, GOLD, r=13, dur=0.4)


def b_snow(s, t0, t1):
    c = s.cues
    fun, hop = c.w("fun", t0), c.w("hop", t0)
    s.snow(t0, t1, count=6, speed=20)
    flake = s.emoji("❄️", 16)
    for k in range(3):  # blowing across all the bushes
        a = t0 + 0.7 * k
        s.glide(flake, [(a, -10, 12 + 9 * k), (a + 2.0, 210, 16 + 9 * k)])
    for i, ch in enumerate("FUN"):
        s.show(s.word(ch, (GOLD, RED, GREEN)[i], 5), fun + 0.1 * i, hop, bx(i + 3), BY, enter="pop", z=Z_WORD)
    she, he = s.emoji("💃", 24), s.emoji("🕺", 24)
    beats = c.beats_in(hop, t1)
    for i in range(8):
        s.show(she if i % 2 == 0 else he, hop + 0.05 * i, t1, bx(i), BY, enter="bottom", hits=beats[i % 2::2],
               amp=5)


def b_rock(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    rock = opt(c, "rock", t0, t1, t0 + 1)
    gtr = s.emoji("🎸", 22)
    for i in range(8):
        s.show(gtr, t0 + 0.05 * i, rock, bx(i), BY, enter="pop", hits=beats[i % 2::2], amp=3)
    for i, ch in enumerate("ROCK"):
        s.show(s.word(ch, RED if i % 2 == 0 else GREEN, 5), rock + 0.08 * i, t1, bx(i + 2), BY, enter="pop",
               z=Z_WORD)
    s.show(gtr, rock, t1, bx(0), BY, enter="pop", hits=c.beats_in(rock, t1), amp=3)
    s.show(gtr, rock, t1, bx(7), BY, enter="pop", hits=c.beats_in(rock, t1), amp=3)


def b_chime(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    faces = [s.emoji(e, 22) for e in CLOCKS]
    for i in range(8):
        s.flash(faces[i:] + faces[:i], [t0] + beats, bx(i), BY, end=t1)


def b_square(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    keys = [s.emoji("💃", 24), s.emoji("🕺", 24), s.emoji("🎄", 22)]
    for i in range(8):
        s.show(keys[i % 3], t0 + 0.04 * i, t1, bx(i), BY, enter="bottom", hits=beats[i % 2::2], amp=4)


def b_frosty(s, t0, t1):
    c = s.cues
    bright = opt(c, "bright", t0, t1)
    flake = s.emoji("❄️", 20)
    for i in range(8):
        s.show(flake, t0 + 0.12 * i, bright or t1, bx(i), BY, enter="top")
        if bright:
            s.show(s.emoji("🌟", 20), bright + 0.05 * i, t1, bx(i), BY, enter="pop")
    s.snow(t0, t1, count=4)


def b_night(s, t0, t1):
    c = s.cues
    rock = opt(c, "rock", t0, t1, t0 + 1.5)
    s.show(s.emoji("🌙", 22), t0, t1, bx(0), BY, enter="top")
    s.twinkle(t0, t1, (WHITE, GOLD), count=8)
    gtr = s.emoji("🎸", 22)
    beats = c.beats_in(rock, t1)
    for i in range(1, 8):
        s.show(gtr, rock + 0.05 * i, t1, bx(i), BY, enter="pop", hits=beats[i % 2::2], amp=3)


def b_swell(s, t0, t1):
    c = s.cues
    swell = opt(c, "swell", t0, t1, t0 + 2)
    beats = c.beats_in(t0, t1)
    bell, party = s.emoji("🔔", 22), s.emoji("🎉", 22)
    for i in range(8):
        s.show(bell, t0 + 0.04 * i, swell, bx(i), BY, enter="pop", hits=beats[i % 2::2], amp=3)
        s.show(party, swell + 0.06 * i, t1, bx(i), BY, enter="pop")
    s.twinkle(swell, t1, (PINK, GOLD, BLUE, GREEN), count=12, fade=0.3)


def b_sleigh(s, t0, t1):
    horse, sled = s.emoji("🐎", 24, flip=True), s.emoji("🛷", 22, flip=True)
    s.glide(horse, [(t0, -14, 22), (t1, 214, 22)])
    s.glide(sled, [(t0, -40, 26), (t1, 188, 26)])
    s.snow(t0, t1, count=5, speed=20)


def b_giddy(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    horse = s.emoji("🐎", 26, flip=True)
    # one bush per beat, left to right
    ts = [t0] + beats
    for k, (a, b) in enumerate(zip(ts, ts[1:] + [t1])):
        i = k % 8
        s.pic(horse, a, b, bx(i), BY)
        s.ring(a, bx(i), 38, GOLD, r=10, dur=0.3)


def b_clock(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    faces = [s.emoji(e, 22) for e in CLOCKS]
    # the hour ticks around the bushes: one lit clock moves each beat
    ts = [t0] + beats
    for k, (a, b) in enumerate(zip(ts, ts[1:] + [t1])):
        s.pic(faces[k % 12], a, b, bx(k % 8), BY)
        s.ring(a, bx(k % 8), BY, (RED, GREEN)[k % 2], r=13, dur=0.4)


def b_mingle(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    keys = [s.emoji("💃", 24), s.emoji("👯", 22), s.emoji("🕺", 24), s.emoji("🎶", 20)]
    for i in range(8):
        s.flash(keys[i % 4:] + keys[:i % 4], [t0 + 0.03 * i] + beats, bx(i), BY, end=t1)


def b_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.2
    rock = words_in(c, "rock", t0, t1)
    last = rock[-1] if rock else t0 + 5
    bell = s.emoji("🔔", 22)
    beats = c.beats_in(t0, last)
    for i in range(8):
        s.show(bell, t0 + 0.05 * i, last, bx(i), BY, enter="pop", hits=beats[i % 2::2], amp=3)
    for i, ch in enumerate("ROCK"):
        s.show(s.word(ch, RED if i % 2 == 0 else GREEN, 5), last + 0.08 * i, end, bx(i + 2), BY, enter="pop",
               exit="fade", exit_s=1.5, z=Z_WORD)
    s.show(s.emoji("🎸", 22), last, end, bx(0), BY, enter="pop", exit="fade", exit_s=1.5)
    s.show(s.emoji("🎸", 22), last, end, bx(7), BY, enter="pop", exit="fade", exit_s=1.5)
    s.twinkle(t0, t1, XMAS, count=10, fade=1.5)


BUSHES = dict(intro=b_intro, bells=b_bells, snow=b_snow, rock=b_rock, chime=b_chime, square=b_square,
              frosty=b_frosty, night=b_night, swell=b_swell, sleigh=b_sleigh, giddy=b_giddy, clock=b_clock,
              mingle=b_mingle, finale=b_finale)
