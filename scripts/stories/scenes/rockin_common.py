"""Shared cues for the Rockin' Around the Christmas Tree matrix-scene stories."""
import html
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from morph_backdrop import backdrop, pattern_sweeps  # noqa: E402,F401
from matrix_scenes import Cues  # noqa: E402

LYRICS_TRACK = "Rockin Around the Christmas Tree"
BEATS_TRACK = "Beat Count"


def cues(xsq):
    """Words from the lyric track's word layer, beats from the counted 1-2-3-4 track."""
    root = ET.parse(xsq).getroot()
    words, beats = [], []
    for e in root.find("ElementEffects"):
        lays = e.findall("EffectLayer")
        if e.get("name") == LYRICS_TRACK and len(lays) > 1:
            words = [(html.unescape(f.get("label")), int(f.get("startTime")) / 1000, int(f.get("endTime")) / 1000)
                     for f in lays[1] if f.get("label")]
        elif e.get("name") == BEATS_TRACK and lays and len(lays[0]):
            beats = [int(f.get("startTime")) / 1000 for f in lays[0]]
    return Cues(words, beats, float(root.findtext("head/sequenceDuration")))


# ---------------------------------------------------------------- look

RED, GREEN, GOLD, WHITE = (230, 0, 0), (0, 200, 40), (255, 190, 0), (255, 255, 255)
PINK, BLUE, ICE, PURPLE = (255, 80, 160), (40, 120, 255), (150, 220, 255), (170, 60, 255)
XMAS = (RED, GREEN, GOLD, WHITE)
Z_BACK, Z_PIC, Z_FRONT, Z_WORD = 18, 20, 25, 30


def plan(c):
    """Scene boundaries (seconds) shared by every prop so the four matrices tell the story together."""
    w, B = c.w, c.beats
    t = [
        ("intro", 0.0),
        ("party", w("rocking") - 0.05),
        ("mistletoe", w("mistletoe") - 0.1),
        ("ring", w("rocking", 20) - 0.05),
        ("pie", w("later") - 0.05),
        ("carol", w("and", 30.3) - 0.05),
        ("feel", w("you", 34) - 0.1),
        ("jolly", w("voices") - 0.1),
        ("deck", w("deck") - 0.05),
        ("happy", w("rocking", 47.5) - 0.05),
        ("dance", w("everyone") - 0.05),
        ("sax", B[141]),
        ("sleigh", B[158]),
        ("presents", B[175]),
        ("party2", B[192]),
        ("feel", w("you", 88) - 0.1),
        ("jolly", w("voices", 95) - 0.1),
        ("deck", w("deck", 98.5) - 0.05),
        ("happy", w("rocking", 102) - 0.05),
        ("dance", w("everyone", 108) - 0.05),
        ("finale", B[274]),
    ]
    out = []
    for k, (name, t0) in enumerate(t):
        t1 = t[k + 1][1] if k + 1 < len(t) else c.duration
        out.append((name, t0, t1))
    return out


def run(s, scenes):
    """Call scenes[name](s, t0, t1) for each planned scene this prop has."""
    for name, t0, t1 in plan(s.cues):
        backdrop(s, t0, t1)
        fn = scenes.get(name)
        if fn:
            fn(s, t0, t1)


def holly_img(s, w=22, h=16):
    def draw(d, im):
        d.polygon([(0, h * 0.55), (w * 0.2, h * 0.2), (w * 0.45, h * 0.45), (w * 0.25, h * 0.75)],
                  fill=(0, 170, 40, 255))
        d.polygon([(w - 1, h * 0.55), (w * 0.8, h * 0.2), (w * 0.55, h * 0.45), (w * 0.75, h * 0.75)],
                  fill=(0, 140, 30, 255))
        r = max(2, w // 8)
        for cx, cy in ((w * 0.5 - r, h * 0.6), (w * 0.5 + r, h * 0.6), (w * 0.5, h * 0.6 + r * 1.4)):
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(235, 0, 0, 255))
    return s.drawn(f"holly_{w}", w, h, draw)


def mistletoe_img(s, w=20, h=22):
    def draw(d, im):
        cx = w // 2
        d.line([(cx, 0), (cx, h * 0.35)], fill=(200, 0, 0, 255), width=1)
        d.polygon([(cx, 3), (cx - 6, 0), (cx - 6, 6)], fill=(230, 0, 0, 255))   # bow
        d.polygon([(cx, 3), (cx + 6, 0), (cx + 6, 6)], fill=(230, 0, 0, 255))
        for dx, dy in ((-6, 9), (6, 9), (-4, 15), (4, 15), (0, 19)):
            d.ellipse([cx + dx - 4, dy - 2, cx + dx + 4, dy + 2], fill=(60, 170, 60, 255))
        for dx, dy in ((-1, 12), (2, 14), (0, 10)):
            d.point((cx + dx, dy), fill=(255, 255, 255, 255))
    return s.drawn("mistletoe", w, h, draw)


def bar_sweeps(s, t0, t1, colors=(RED, GREEN), every=1):
    """SuperStar-style Morph pattern groups on every other beat (none while the tree's are echoed)."""
    pattern_sweeps(s, t0, t1, colors, every)


# ================================================================ 140x60 matrix (the garage)

def g_intro(s, t0, t1):
    c = s.cues
    s.show(s.emoji("🎄", 50), 0.3, t1, 70, 34, enter="fade", enter_s=2.0, hits=c.beats_in(4.0, t1), amp=1)
    s.show(s.emoji("⭐", 12), c.beats[8], t1, 70, 7, enter="top", z=Z_FRONT)
    s.ring(c.beats[8] + 0.35, 70, 8, GOLD, r=20)
    s.twinkle(0.2, t1, (WHITE, GOLD), count=8, fade=1.0)
    bar_sweeps(s, 3.6, t1)


def g_party(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    party = c.w("party", t0)
    s.show(s.emoji("🎄", 44), t0, t1, 70, 36, enter=None, hits=beats, amp=2)
    s.show(s.emoji("💃", 32), t0, t1, 22, 40, enter="left", hits=beats[0::2], amp=3)
    s.show(s.emoji("🕺", 32), t0, t1, 118, 40, enter="right", hits=beats[1::2], amp=3)
    s.show(s.word("ROCKIN", RED, 2), t0, party, 70, 7, enter="pop", z=Z_WORD)
    s.show(s.word("PARTY HOP", GREEN, 2), party, t1, 70, 7, enter="pop", z=Z_WORD)
    s.ring(c.w("hop", t0), 70, 36, GOLD, r=40)
    s.snow(t0, t1, count=4)


def g_mistletoe(s, t0, t1):
    c = s.cues
    every, stop = c.w("every", t0), c.w("stop", t0)
    s.show(mistletoe_img(s, 26, 26), t0, t1, 70, 14, enter="top", hits=[stop], amp=2, z=Z_BACK)
    s.show(s.word("MISTLETOE", GREEN, 2), c.w("mistletoe", t0), every, 70, 50, enter="pop", z=Z_WORD)
    she, he = s.emoji("💃", 26), s.emoji("🕺", 26)
    s.glide(she, [(every, -14, 42), (stop, 58, 42), (t1, 58, 42)])
    s.glide(he, [(every, 154, 42), (stop, 82, 42), (t1, 82, 42)])
    s.show(s.emoji("💋", 14), stop, t1, 70, 34, enter="pop", z=Z_FRONT)
    s.ring(stop, 70, 34, PINK, r=40)
    s.twinkle(stop, t1, (PINK, RED, WHITE), count=20, steps=20, fade=0.3)


def g_ring(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    s.show(s.emoji("🎄", 44), t0, t1, 70, 36, enter="pop", hits=beats[::2], amp=2)
    s.show(s.emoji("🔔", 26), t0, t1, 22, 22, enter="left", hits=beats[0::2], amp=3)
    s.show(s.emoji("🔔", 26, flip=True), t0, t1, 118, 22, enter="right", hits=beats[1::2], amp=3)
    for i, b in enumerate(beats):
        s.ring(b, 22 if i % 2 == 0 else 118, 22, GOLD, r=18, dur=0.4)
    ring = c.w("ring", t0)
    s.show(s.word("RING", GOLD, 2), ring, t1, 70, 7, enter="pop", z=Z_WORD)
    s.ring(ring, 70, 30, WHITE, r=60, dur=0.9)
    s.twinkle(ring, t1, (GOLD, WHITE), count=20, steps=15, fade=0.3)


def g_pie(s, t0, t1):
    c = s.cues
    pumpkin, pie = c.w("pumpkin", t0), c.w("pie", t0)
    s.show(s.word("LATER", WHITE, 2), t0, pumpkin, 70, 30, enter="pop", z=Z_WORD)
    s.show(s.emoji("🎃", 34), pumpkin, t1, 36, 33, enter="pop")
    s.show(s.emoji("🥧", 38), pie, t1, 102, 34, enter="pop", hits=c.beats_in(pie + 0.3, t1), amp=2)
    s.show(s.word("PIE", GOLD, 3), pie, t1, 102, 8, enter="pop", z=Z_WORD)
    s.ring(pie, 102, 34, GOLD, r=34)


def g_carol(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    s.show(s.emoji("🎅", 32), t0, t1, 28, 38, enter="left", hits=beats[0::2], amp=2)
    s.show(s.emoji("🤶", 32), t0, t1, 112, 38, enter="right", hits=beats[1::2], amp=2)
    s.show(s.emoji("🎶", 20), t0 + 0.3, t1, 70, 34, enter="pop", hits=beats, amp=3)
    s.show(s.word("CAROLING", GREEN, 2), c.w("carol", t0), t1, 70, 7, enter="pop", z=Z_WORD)
    s.snow(t0, t1, count=5)


def g_feel(s, t0, t1):
    c = s.cues
    feel, hear = c.w("feeling", t0), c.w("hear", t0)
    s.show(s.emoji("❤️", 44), t0, t1, 70, 31, enter="pop", hits=c.beats_in(t0 + 0.4, t1), amp=2)
    for b in c.bars_in(t0, t1):
        s.ring(b, 70, 31, PINK, r=50, dur=0.8)
    s.show(s.word("FEEL", PINK, 2), feel, t1, 21, 30, enter="left", z=Z_WORD)
    s.show(s.word("HEAR", ICE, 2), hear, t1, 119, 30, enter="right", z=Z_WORD)
    s.twinkle(t0, t1, (PINK, RED), count=8)


def g_jolly(s, t0, t1):
    c = s.cues
    jolly = c.w("jolly", t0)
    beats = c.beats_in(t0, t1)
    s.show(s.emoji("🎅", 40), t0, t1, 70, 36, enter="bottom", hits=beats, amp=2)
    s.show(s.emoji("🎶", 18), t0 + 0.2, t1, 22, 26, enter="pop", hits=beats[0::2], amp=3)
    s.show(s.emoji("🎵", 18), t0 + 0.4, t1, 118, 26, enter="pop", hits=beats[1::2], amp=3)
    s.show(s.word("SINGING", WHITE, 2), c.w("singing", t0), jolly, 70, 7, enter="pop", z=Z_WORD)
    s.show(s.word("JOLLY", GOLD, 2), jolly, t1, 70, 7, enter="pop", z=Z_WORD)
    s.ring(jolly, 70, 36, GOLD, r=50)


def g_deck(s, t0, t1):
    c = s.cues
    spots = [(14 + 28 * k, 9) for k in range(5)] + [(14 + 28 * k, 52) for k in range(5)]
    times = c.beats_in(t0, t1)
    times = [t0 + (t1 - t0) * 0.7 * k / len(spots) for k in range(len(spots))]
    for k, ((x, y), t) in enumerate(zip(spots, times)):
        s.show(holly_img(s, 24, 18), t, t1, x, y, enter="pop", enter_s=0.2)
    s.show(s.word("DECK THE", RED, 2), c.w("deck", t0), t1, 70, 24, enter="pop", z=Z_WORD)
    s.show(s.word("HALLS", GREEN, 2), c.w("halls", t0), t1, 70, 37, enter="pop", z=Z_WORD)
    s.ring(c.w("holly", t0), 70, 30, RED, r=60)


def g_happy(s, t0, t1):
    c = s.cues
    happy, hol = c.w("happy", t0), c.w("holiday", t0)
    beats = c.beats_in(t0, t1)
    s.show(s.emoji("🎄", 44), t0, t1, 22, 36, enter="left", hits=beats, amp=2)
    s.show(s.word("ROCKIN", GREEN, 3), t0, happy, 86, 30, enter="pop", z=Z_WORD)
    s.show(s.word("HAPPY", RED, 3), happy, t1, 88, 15, enter="pop", z=Z_WORD)
    s.show(s.word("HOLIDAY", GREEN, 3), hol, t1, 88, 43, enter="pop", z=Z_WORD)
    s.ring(hol, 88, 30, GOLD, r=60)
    bar_sweeps(s, t0, t1, (GOLD, WHITE))
    s.twinkle(hol, t1, XMAS, count=20, steps=20, fade=0.3)


def g_dance(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    s.show(s.emoji("💃", 32), t0, t1, 22, 40, enter="left", hits=beats[0::2], amp=3)
    s.show(s.emoji("👯", 32), t0, t1, 70, 40, enter="bottom", hits=beats, amp=2)
    s.show(s.emoji("🕺", 32), t0, t1, 118, 40, enter="right", hits=beats[1::2], amp=3)
    s.show(s.word("DANCE", PINK, 2), c.w("dancing", t0), t1, 70, 7, enter="pop", z=Z_WORD)
    s.twinkle(t0, t1, (PINK, GOLD, BLUE), count=10)


def g_sax(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    s.show(s.emoji("🎷", 46), t0, t1, 70, 31, enter="pop", hits=beats, amp=2)
    s.show(s.emoji("🎶", 18), t0 + 0.5, t1, 20, 24, enter="pop", hits=beats[0::2], amp=4)
    s.show(s.emoji("🎵", 18), t0 + 0.9, t1, 120, 24, enter="pop", hits=beats[1::2], amp=4)
    bar_sweeps(s, t0, t1, (GOLD, PURPLE, BLUE))


def sleigh_team(s, t0, t1, x0, x1, y, px):
    """Two reindeer pulling Santa's sleigh, travelling from x0 to x1 (lead reindeer's centre)."""
    deer, sled, santa = s.emoji("🦌", px), s.emoji("🛷", px), s.emoji("🎅", int(px * 0.8))
    gap = px + 2
    for k, (key, dy) in enumerate(((deer, 0), (deer, 0), (sled, 2), (santa, -px * 0.45))):
        off = gap * (k if k < 3 else 2)
        s.glide(key, [(t0, x0 + off, y + dy), (t1, x1 + off, y + dy)], z=Z_FRONT if key == santa else Z_PIC)


def g_sleigh(s, t0, t1):
    sleigh_team(s, t0, t1, 150, -110, 36, 24)
    s.snow(t0, t1, count=6)
    s.twinkle(t0, t1, (WHITE,), count=6)


def g_presents(s, t0, t1):
    c = s.cues
    bars = c.bars_in(t0, t1)
    spots = [(30, 46, 22), (70, 46, 22), (110, 46, 22), (50, 26, 20), (90, 26, 20), (70, 9, 16)]
    for (x, y, px), b in zip(spots, bars):
        s.show(s.emoji("🎁", px), b, t1, x, y, enter="top", enter_s=0.3, hits=c.beats_in(b + 0.5, t1)[::4], amp=1)
        s.ring(b + 0.3, x, y, GOLD, r=14, dur=0.5)
    bar_sweeps(s, t0, t1, (RED, GREEN))


def g_party2(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    half = beats[len(beats) // 2] if beats else t0
    s.show(s.emoji("🕺", 44), t0, half, 70, 34, enter="pop", hits=beats, amp=3)
    s.show(s.emoji("🎄", 24), t0, half, 20, 44, enter="left", hits=beats[1::2], amp=2)
    s.show(s.emoji("🎄", 24), t0, half, 120, 44, enter="right", hits=beats[0::2], amp=2)
    swaps = c.beats_in(half, t1)
    if swaps:
        a, b, g = s.emoji("💃", 44), s.emoji("🎄", 44), s.emoji("🕺", 44)
        s.flash([a, b, g], swaps, 70, 32, end=t1)
        for i, t in enumerate(swaps):
            s.ring(t, 70, 32, XMAS[i % 4], r=55, dur=0.5)
    s.twinkle(t0, t1, (RED, GREEN, GOLD, BLUE, PINK), count=25, steps=20)


def g_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.2
    s.show(s.word("MERRY", RED, 3), t0, end, 70, 14, enter="left", exit="fade", exit_s=1.5, z=Z_WORD)
    s.show(s.word("CHRISTMAS", GREEN, 2), t0 + 0.4, end, 70, 38, enter="right", exit="fade", exit_s=1.5, z=Z_WORD)
    s.show(s.emoji("🎄", 22), t0, end, 12, 47, enter="bottom", exit="fade", exit_s=1.5,
           hits=c.beats_in(t0 + 0.4, end - 1.6), amp=2)
    s.show(s.emoji("🎄", 22), t0, end, 128, 47, enter="bottom", exit="fade", exit_s=1.5,
           hits=c.beats_in(t0 + 0.6, end - 1.6), amp=2)
    s.twinkle(t0, t1, XMAS, count=20, fade=1.5)
    for b in c.bars_in(t0, end - 1.5):
        s.ring(b, 70, 26, GOLD, r=60, dur=0.8)


GARAGE = dict(intro=g_intro, party=g_party, mistletoe=g_mistletoe, ring=g_ring, pie=g_pie, carol=g_carol,
              feel=g_feel, jolly=g_jolly, deck=g_deck, happy=g_happy, dance=g_dance, sax=g_sax, sleigh=g_sleigh,
              presents=g_presents, party2=g_party2, finale=g_finale)


# ================================================================ the two windows as one stage

def wins(s):
    return tuple(s.center(m)[0] for m in s.places)  # the two windows, in --model order


def w_intro(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    s.show(s.emoji("🎁", 24), c.beats[8], t1, L, 28, enter="top", hits=c.beats_in(c.beats[9], t1)[::2], amp=1)
    s.show(s.emoji("🎁", 24, flip=True), c.beats[10], t1, C, 28, enter="top",
           hits=c.beats_in(c.beats[11], t1)[1::2], amp=1)
    s.twinkle(0.2, t1, (WHITE, GOLD), count=8, fade=1.0)


def w_party(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    party = c.w("party", t0)
    s.show(s.emoji("💃", 30), t0, t1, L, 30, enter="left", hits=beats[0::2], amp=3)
    s.show(s.emoji("🕺", 30), t0, t1, C, 30, enter="right", hits=beats[1::2], amp=3)
    for x in (L, C):
        s.show(s.emoji("🎉", 14), party, t1, x, 8, enter="pop", z=Z_FRONT)
        s.ring(party, x, 24, GOLD, r=26)


def w_mistletoe(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    stop = c.w("stop", t0)
    s.show(mistletoe_img(s), t0, t1, L, 11, enter="top", z=Z_BACK)
    s.show(s.emoji("💃", 24), t0 + 0.3, t1, L, 34, enter="left")
    s.show(s.emoji("🕺", 24), t0 + 0.6, t1, C, 34, enter="right")
    heart = s.emoji("❤️", 12)
    s.glide(heart, [(stop - 0.9, C, 14), (stop, L, 18)], z=Z_FRONT)
    s.show(s.emoji("💋", 12), stop, t1, L, 18, enter="pop", z=Z_FRONT)
    s.show(heart, stop + 0.2, t1, C, 14, enter="pop", hits=c.beats_in(stop + 0.5, t1), amp=2, z=Z_FRONT)
    s.ring(stop, L, 24, PINK, r=26)


def w_ring(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    s.show(s.emoji("🔔", 30), t0, t1, L, 24, enter="top", hits=beats[0::2], amp=3)
    s.show(s.emoji("🔔", 30, flip=True), t0, t1, C, 24, enter="top", hits=beats[1::2], amp=3)
    for i, b in enumerate(beats):
        s.ring(b, L if i % 2 == 0 else C, 24, GOLD, r=24, dur=0.4)
    s.twinkle(c.w("ring", t0), t1, (GOLD, WHITE), count=20, steps=15, fade=0.3)


def w_pie(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    s.show(s.emoji("🎃", 30), c.w("pumpkin", t0), t1, L, 26, enter="pop")
    s.show(s.emoji("🥧", 32), c.w("pie", t0), t1, C, 26, enter="pop")
    s.ring(c.w("pie", t0), C, 26, GOLD, r=26)


def w_carol(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    s.show(s.emoji("🎶", 26), t0, t1, L, 24, enter="pop", hits=beats[0::2], amp=3)
    s.show(s.emoji("🎤", 26), t0 + 0.3, t1, C, 26, enter="pop", hits=beats[1::2], amp=2)
    s.snow(t0, t1, count=4)


def w_feel(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    hear = c.w("hear", t0)
    s.show(s.emoji("❤️", 30), t0, t1, L, 24, enter="pop", hits=c.beats_in(t0 + 0.4, t1), amp=2)
    s.show(s.emoji("🥰", 30), t0 + 0.3, hear, C, 24, enter="pop")
    s.show(s.emoji("👂", 28), hear, t1, C, 24, enter="pop")
    s.ring(hear, C, 24, ICE, r=26)


def w_jolly(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    jolly = c.w("jolly", t0)
    beats = c.beats_in(t0, t1)
    s.show(s.emoji("😄", 30), t0, t1, L, 24, enter="pop", hits=beats[0::2], amp=2)
    s.show(s.emoji("🎅", 30), t0, t1, C, 26, enter="pop", hits=beats[1::2], amp=2)
    s.ring(jolly, L, 24, GOLD, r=26)
    s.ring(jolly, C, 26, GOLD, r=26)


def w_deck(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    hol = c.w("holly", t0)
    s.show(holly_img(s, 34, 24), c.w("deck", t0), t1, L, 24, enter="pop", hits=[hol], amp=3)
    s.show(holly_img(s, 34, 24), c.w("halls", t0), t1, C, 24, enter="pop", hits=[hol], amp=3)
    s.ring(hol, L, 24, RED, r=26)
    s.ring(hol, C, 24, RED, r=26)


def w_happy(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    happy, hol = c.w("happy", t0), c.w("holiday", t0)
    s.show(s.emoji("🎄", 34), t0, t1, L, 27, enter="bottom", hits=beats[0::2], amp=2)
    s.show(s.emoji("🎁", 28), t0, t1, C, 28, enter="bottom", hits=beats[1::2], amp=2)
    s.ring(happy, L, 24, RED, r=26)
    s.ring(hol, C, 24, GREEN, r=26)
    s.twinkle(hol, t1, XMAS, count=20, steps=20, fade=0.3)


def w_dance(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    old = c.w("old", t0)
    s.show(s.emoji("💃", 30), t0, old, L, 26, enter="left", hits=beats[0::2], amp=3)
    s.show(s.emoji("🕺", 30), t0, old, C, 26, enter="right", hits=beats[1::2], amp=3)
    swaps = c.beats_in(old, t1)
    if swaps:
        a, b = s.emoji("💃", 30), s.emoji("🕺", 30)
        s.flash([b, a], swaps, L, 26, end=t1)
        s.flash([a, b], swaps, C, 26, end=t1)


def w_sax(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    s.show(s.emoji("🎷", 32), t0, t1, L, 24, enter="pop", hits=beats, amp=2)
    s.show(s.emoji("🎶", 26), t0 + 0.3, t1, C, 24, enter="pop", hits=beats[1::2], amp=3)
    bar_sweeps(s, t0, t1, (GOLD, PURPLE, BLUE))


def w_sleigh(s, t0, t1):
    L, C = wins(s)
    # crosses the right window, goes behind the wall, comes out in the left one
    sleigh_team(s, t0, t1, C + 40, L - 130, 26, 18)
    s.snow(t0, t1, count=5)


def w_presents(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    bars = c.bars_in(t0, t1)
    spots = [(L - 9, 39, 18), (C + 9, 39, 18), (L + 9, 39, 18), (C - 9, 39, 18), (L, 22, 16), (C, 22, 16)]
    for (x, y, px), b in zip(spots, bars):
        s.show(s.emoji("🎁", px), b, t1, x, y, enter="top", enter_s=0.3)
        s.ring(b + 0.3, x, y, GOLD, r=12, dur=0.5)
    bar_sweeps(s, t0, t1, (RED, GREEN))


def w_party2(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    if beats:
        a, b, g = s.emoji("💃", 30), s.emoji("🎄", 30), s.emoji("🕺", 30)
        s.flash([a, b, g], beats, L, 26, end=t1)
        s.flash([g, a, b], beats, C, 26, end=t1)
    s.twinkle(t0, t1, (RED, GREEN, GOLD, BLUE, PINK), count=20, steps=20)


def w_finale(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    end = t1 - 0.2
    s.show(s.emoji("🎄", 34), t0, end, L, 26, enter="pop", exit="fade", exit_s=1.5,
           hits=c.beats_in(t0 + 0.4, end - 1.6)[0::2], amp=2)
    s.show(s.emoji("🎅", 30), t0, end, C, 26, enter="pop", exit="fade", exit_s=1.5,
           hits=c.beats_in(t0 + 0.4, end - 1.6)[1::2], amp=2)
    s.twinkle(t0, t1, XMAS, count=15, fade=1.5)


WINDOWS = dict(intro=w_intro, party=w_party, mistletoe=w_mistletoe, ring=w_ring, pie=w_pie, carol=w_carol,
               feel=w_feel, jolly=w_jolly, deck=w_deck, happy=w_happy, dance=w_dance, sax=w_sax, sleigh=w_sleigh,
               presents=w_presents, party2=w_party2, finale=w_finale)


# ================================================================ 200x42 matrix: 8 bushes, 25 px each

def bx(i):
    return 12.5 + 25 * i


BY = 22


def each(s, key, t0, t1, *, flip_odd=False, hits_of=None, amp=2, enter="pop", **kw):
    for i in range(8):
        k = key(i) if callable(key) else key
        if flip_odd and i % 2 and not callable(key):
            k = key
        s.show(k, t0, t1, bx(i), BY, enter=enter, hits=hits_of(i) if hits_of else (), amp=amp, **kw)


def b_intro(s, t0, t1):
    c = s.cues
    tree = s.emoji("🎄", 24)
    for i in range(8):
        b = c.beats[8 + i]
        s.show(tree, b, t1, bx(i), BY, enter="pop", enter_s=0.2)
    s.twinkle(0.2, t1, (WHITE,), count=4, fade=1.0)


def b_party(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    she, he = s.emoji("💃", 24), s.emoji("🕺", 24)
    for i in range(8):
        s.show(she if i % 2 == 0 else he, t0, t1, bx(i), BY, enter="bottom", hits=beats[i % 2::2], amp=3)


def b_mistletoe(s, t0, t1):
    c = s.cues
    bars = c.bars_in(t0, t1) or [t0]
    times = [t0] + [b for b in bars if b > t0 + 0.3]
    mist, heart = mistletoe_img(s), s.emoji("❤️", 18)
    for i in range(8):
        keys = [mist, heart] if i % 2 == 0 else [heart, mist]
        s.flash(keys, times, bx(i), BY, end=t1)


def b_ring(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    bell, bellf = s.emoji("🔔", 22), s.emoji("🔔", 22, flip=True)
    ring = c.w("ring", t0)
    for i in range(8):
        s.show(bell if i % 2 == 0 else bellf, t0, t1, bx(i), BY, enter="top", hits=beats[i % 2::2], amp=3)
        s.ring(ring + 0.05 * i, bx(i), BY, GOLD, r=13, dur=0.5)


def b_pie(s, t0, t1):
    c = s.cues
    pie = s.emoji("🥧", 22)
    beats = c.beats_in(t0, t1)
    for i, b in enumerate(beats[:8]):
        s.show(pie, b, t1, bx(i), BY + 4, enter="top", enter_s=0.2)


def b_carol(s, t0, t1):
    notes = [s.emoji("🎵", 18), s.emoji("🎶", 20), s.emoji("🎵", 18)]
    span = t1 - t0
    for k, key in enumerate(notes):
        a = t0 + k * span / 6
        s.glide(key, [(a, 212, 18 + 6 * (k % 2)), (a + span * 0.6, -12, 18 + 6 * (k % 2))])
    s.snow(t0, t1, count=4)


def b_feel(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0 + 0.3, t1)
    heart = s.emoji("❤️", 20)
    for i in range(8):
        s.show(heart, t0 + 0.05 * i, t1, bx(i), BY, enter="pop", hits=beats[i % 2::2], amp=3)


def b_jolly(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    santa, snowman = s.emoji("🎅", 22), s.emoji("⛄", 24)
    for i in range(8):
        s.show(santa if i % 2 == 0 else snowman, t0, t1, bx(i), BY, enter="bottom", hits=beats[i % 2::2], amp=3)
    s.ring(c.w("jolly", t0), 100, BY, GOLD, r=40)


def b_deck(s, t0, t1):
    holly = holly_img(s, 24, 18)
    for i in range(8):
        s.show(holly, t0 + (t1 - t0) * 0.75 * i / 8, t1, bx(i), BY, enter="pop", enter_s=0.2)


def b_happy(s, t0, t1):
    c = s.cues
    happy, hol = c.w("happy", t0), c.w("holiday", t0)
    tree = s.emoji("🎄", 24)
    beats = c.beats_in(t0, happy)
    for i in range(8):
        s.show(tree, t0, happy, bx(i), BY, enter="bottom", hits=beats[i % 2::2], amp=2)
    for i, ch in enumerate("HAPPY"):  # one letter per bush, bushes 2-6
        s.show(s.word(ch, RED if i % 2 == 0 else GREEN, 5), happy, hol, bx(i + 1), BY, enter="pop",
               enter_s=0.15, z=Z_WORD)
    for i, ch in enumerate("HOLIDAY"):
        s.show(s.word(ch, GREEN if i % 2 == 0 else RED, 5), hol + 0.08 * i, t1, bx(i), BY, enter="pop",
               enter_s=0.15, z=Z_WORD)
    s.show(s.emoji("🎉", 20), hol + 0.6, t1, bx(7), BY, enter="pop")


def b_dance(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    pair, she, he = s.emoji("👯", 22), s.emoji("💃", 24), s.emoji("🕺", 24)
    for i in range(8):
        key = (she, pair, he, pair)[i % 4]
        s.show(key, t0, t1, bx(i), BY, enter="bottom", hits=beats[i % 2::2], amp=3)


def b_sax(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    notes = [s.emoji("🎵", 20), s.emoji("🎶", 22)]
    for i in range(8):
        s.show(notes[i % 2], t0 + 0.06 * i, t1, bx(i), BY, enter="pop", hits=beats[i % 2::2], amp=4)


def b_sleigh(s, t0, t1):
    sleigh_team(s, t0, t1, 215, -110, 24, 22)
    s.snow(t0, t1, count=4)


def b_presents(s, t0, t1):
    c = s.cues
    gift = s.emoji("🎁", 22)
    beats = c.beats_in(t0, t1)
    order = [0, 7, 1, 6, 2, 5, 3, 4]
    for k, b in enumerate(beats[:16:2]):
        i = order[k]
        s.show(gift, b, t1, bx(i), BY + 2, enter="top", enter_s=0.2)
        s.ring(b + 0.2, bx(i), BY + 2, GOLD, r=12, dur=0.4)


def b_party2(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    keys = [s.emoji("💃", 24), s.emoji("🎄", 24), s.emoji("🕺", 24)]
    for i in range(8):
        if beats:
            s.flash(keys[i % 3:] + keys[:i % 3], beats, bx(i), BY, end=t1)


def b_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.2
    tree = s.emoji("🎄", 24)
    beats = c.beats_in(t0 + 0.3, end - 1.6)
    for i in range(8):
        s.show(tree, t0 + 0.05 * i, end, bx(i), BY, enter="pop", exit="fade", exit_s=1.5,
               hits=beats[i % 2::2], amp=2)
    s.twinkle(t0, t1, XMAS, count=10, fade=1.5)


BUSHES = dict(intro=b_intro, party=b_party, mistletoe=b_mistletoe, ring=b_ring, pie=b_pie, carol=b_carol,
              feel=b_feel, jolly=b_jolly, deck=b_deck, happy=b_happy, dance=b_dance, sax=b_sax, sleigh=b_sleigh,
              presents=b_presents, party2=b_party2, finale=b_finale)
