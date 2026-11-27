"""Grandma Got Run Over By A Reindeer matrix scenes, shared plan for the garage, the two windows (one stage) and
the bushes.

The MegaTree carries the SuperStar story (the reindeer, eggnog, the police line, Grandpa with football and beer,
the family in black, the blue-haired wig); these scenes follow the same lyric beats on the other matrices and keep
it cartoonish: Grandma is bumped clean off the matrix and pops back up, fine, at the end.
Words: faster-whisper (stories/lyrics/grandma.json); beats: librosa (grandma_beats.json).
"""
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
from morph_backdrop import backdrop, pattern_sweeps  # noqa: E402,F401
from matrix_scenes import Cues  # noqa: E402
from rockin_common import (BLUE, GOLD, GREEN, ICE, PINK, PURPLE, RED, WHITE, XMAS, Z_BACK, Z_FRONT,  # noqa: E402,F401
                           Z_PIC, Z_WORD, bar_sweeps, sleigh_team)

LYRICS = HERE.parent / "lyrics"
BROWN, YELLOW, SILVER, BLACK = (120, 70, 25), (255, 210, 0), (200, 210, 225), (10, 10, 10)


def cues(xsq):
    dur = float(ET.parse(xsq).getroot().findtext("head/sequenceDuration"))
    return Cues.from_files(LYRICS / "grandma.json", LYRICS / "grandma_beats.json", dur)


def plan(c):
    w = c.w
    t = [
        ("intro", 0.0),
        ("chorus", w("grandma") - 0.1),
        ("santa", w("you", 12) - 0.1),
        ("eggnog", w("drinking") - 0.9),
        ("meds", w("forgot") - 1.1),
        ("found", w("found", 40) - 0.6),
        ("hoof", w("hoof") - 1.2),
        ("chorus", w("grandma", 56) - 0.1),
        ("santa", w("you", 65) - 0.1),
        ("proud", w("now", 74) - 0.1),
        ("black", w("without") - 3.3),
        ("gifts", w("should") - 0.1),
        ("chorus", w("grandma", 109) - 0.1),
        ("santa", w("you", 118) - 0.1),
        ("goose", w("goose") - 1.1),
        ("candles", w("blue") - 1.0),
        ("warn", w("warned") - 0.7),
        ("chorus", w("grandma", 162) - 0.1),
        ("santa", w("you", 170.5) - 0.1),
        ("chorus", w("grandma", 180) - 0.1),
        ("santa", w("you", 188) - 0.1),
        ("finale", w("believe", 195) + 0.8),
    ]
    return [(n, t0, t[k + 1][1] if k + 1 < len(t) else c.duration) for k, (n, t0) in enumerate(t)]


def believe(c, t0, t1):
    """'we believe' - one verse is cut off by "Sing it, Grandpa!", so fall back to "me and Grandma"."""
    b = c.w("believe", t0)
    return b if b < t1 - 0.5 else c.w("me", c.w("santa", t0))


def run(s, scenes):
    count = {}
    for name, t0, t1 in plan(s.cues):
        backdrop(s, t0, t1)
        fn = scenes.get(name)
        if fn:
            k = count[name] = count.get(name, -1) + 1
            fn(s, t0, t1, k) if name in ("chorus", "santa") else fn(s, t0, t1)


# ---------------------------------------------------------------- drawn props

def flipped(s, key):
    name = key.rsplit("/", 1)[1][:-4] + "_flip"
    return s.image(name, s.images[key].transpose(0))


def tape(s, w, h=9):
    """Yellow police-line tape with black chevrons (the words go on top as their own picture)."""
    def draw(d, im):
        d.rectangle([0, 0, w - 1, h - 1], fill=YELLOW + (255,))
        d.line([(0, 0), (w - 1, 0)], fill=BLACK + (255,))
        d.line([(0, h - 1), (w - 1, h - 1)], fill=BLACK + (255,))
    return s.drawn(f"tape_{w}_{h}", w, h, draw)


def hoofprint(s, px):
    def draw(d, im):
        d.ellipse([0, 0, px * 0.45, px - 1], fill=BROWN + (255,))
        d.ellipse([px * 0.55, 0, px - 1, px - 1], fill=BROWN + (255,))
    return s.drawn(f"hoof_{px}", px, px, draw)


def candle(s, h, color):
    w = max(4, h // 3)

    def draw(d, im):
        d.ellipse([w * 0.2, 0, w * 0.8, h * 0.28], fill=(255, 170, 0, 255))
        d.ellipse([w * 0.35, h * 0.08, w * 0.65, h * 0.24], fill=(255, 255, 160, 255))
        d.rectangle([0, h * 0.3, w - 1, h - 1], fill=tuple(color) + (255,))
    return s.drawn(f"candle_{h}_{color[0]}_{color[2]}", w, h, draw)


def wig(s, w):
    h = round(w * 0.55)

    def draw(d, im):
        r = w / 6
        for k in range(5):
            cx = r + k * (w - 2 * r) / 4
            cy = h * 0.55 - math.sin(math.pi * k / 4) * h * 0.25
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(60, 120, 255, 255))
        for k in range(4):
            cx = r * 1.6 + k * (w - 3.2 * r) / 3
            d.ellipse([cx - r * 0.5, h * 0.25, cx + r * 0.5, h * 0.25 + r], fill=(170, 200, 255, 255))
    return s.drawn(f"wig_{w}", w, h, draw)


def table(s, w):
    h = max(6, w // 5)

    def draw(d, im):
        d.rectangle([0, 0, w - 1, 2], fill=(230, 230, 240, 255))           # cloth
        d.rectangle([0, 3, w - 1, 4], fill=BROWN + (255,))
        d.rectangle([2, 5, 4, h - 1], fill=BROWN + (255,))
        d.rectangle([w - 5, 5, w - 3, h - 1], fill=BROWN + (255,))
    return s.drawn(f"table_{w}", w, h, draw)


def launch(s, key, t, x, y, *, up=-40, dur=0.9, z=Z_FRONT):
    """Bumped clean off the matrix: a quick hop sideways and up out of the top, shrinking."""
    s.pic(key, t, t + dur, x, y, to=(x + 20, y + up), scale=(100, 40), z=z)


# ================================================================ 140x60 matrix (the garage)

def g_intro(s, t0, t1):
    c = s.cues
    s.snow(0.0, t1, count=6, fade=1.0)
    s.show(s.emoji("🏠", 34), 0.3, t1, 20, 40, enter="fade", enter_s=1.0)
    s.show(s.emoji("🌙", 16), 0.8, t1, 124, 10, enter="fade", enter_s=1.0)
    beats = c.beats_in(0.5, t1)
    for i, b in enumerate(beats):
        s.ring(b, 124, 10, GOLD, r=10, dur=0.4)


def g_chorus(s, t0, t1, k):
    c = s.cues
    run_, deer_t, walk, eve = c.w("run", t0), c.w("reindeer", t0), c.w("walking", t0), c.w("eve", t0)
    gma = s.emoji("👵", 30)
    deer = s.emoji("🦌", 32)
    beats = c.beats_in(t0, deer_t)
    s.show(s.word("GRANDMA", PINK, 2), t0, run_, 70, 6, enter="pop", z=Z_WORD)
    s.hold(gma, t0, deer_t, 78, 38, hits=beats, amp=2)
    # the reindeer charges in from the right and bumps her clean off the top
    s.pic(deer, run_, deer_t, 160, 38, to=(96, 38))
    s.pic(deer, deer_t, deer_t + 1.0, 96, 38, to=(-20, 38))
    launch(s, gma, deer_t, 78, 38)
    s.show(s.word("REINDEER", (210, 140, 60), 2), deer_t, walk, 70, 6, enter="pop", z=Z_WORD)
    s.ring(deer_t, 82, 32, WHITE, r=40, dur=0.7)
    s.show(s.emoji("💫", 18), deer_t + 0.4, walk, 78, 40, enter="pop", z=Z_FRONT)
    # then the walk home on Christmas Eve
    s.show(s.emoji("🏠", 34), walk, t1, 22, 40, enter="left")
    s.show(s.emoji("🌙", 18), walk + 0.3, t1, 122, 12, enter="top")
    s.show(s.word("CHRISTMAS EVE", GOLD, 2) if k % 2 == 0 else s.word("CHRISTMAS EVE", ICE, 2),
           eve - 0.3, t1, 76, 36, enter="pop", z=Z_WORD)
    s.snow(walk, t1, count=6)
    bar_sweeps(s, t0, deer_t, (RED, GREEN))


def g_santa(s, t0, t1, k):
    c = s.cues
    no, santa, bel = c.w("no", t0), c.w("santa", t0), believe(c, t0, t1)
    s.show(s.word("NO SUCH", WHITE, 2), no, santa, 36, 14, enter="left", z=Z_WORD)
    s.show(s.word("THING", WHITE, 2), no + 0.4, santa, 36, 30, enter="left", z=Z_WORD)
    s.show(s.emoji("❓", 26), no, santa, 104, 30, enter="pop", hits=c.beats_in(no, santa), amp=2)
    s.show(s.emoji("🎅", 36), santa, t1, 104, 32, enter="pop", hits=c.beats_in(santa + 0.3, t1)[::2], amp=2)
    s.ring(santa, 104, 32, RED, r=40)
    s.show(s.emoji("👴", 30), santa + 0.6, t1, 34, 34, enter="left", hits=c.beats_in(santa + 1, t1)[1::2], amp=2)
    s.show(s.word("BELIEVE", GOLD, 2), bel, t1, 70, 6, enter="pop", z=Z_WORD)
    s.ring(bel, 70, 30, GOLD, r=70, dur=0.9)
    s.twinkle(bel, t1, (GOLD, WHITE), count=20, steps=15, fade=0.3)
    if k == 3:  # "Sing it, Grandpa!"
        sing = c.w("sing", t0)
        s.show(s.emoji("🎤", 18), sing, t1, 52, 30, enter="pop", z=Z_FRONT)


def g_eggnog(s, t0, t1):
    c = s.cues
    egg, begged, go = c.w("eggnog", t0), c.w("begged", t0), c.w("go", c.w("begged", t0))
    gma = s.emoji("👵", 32)
    s.show(gma, t0, begged, 30, 36, enter="left", hits=c.beats_in(t0, begged), amp=2)
    mug = s.emoji("🥛", 14)
    for i, b in enumerate(c.beats_in(t0 + 0.3, egg + 0.5)[:6]):  # glasses lining up
        s.show(mug, b, begged, 62 + 12 * i, 46, enter="top", enter_s=0.2)
    s.show(s.word("EGGNOG", (255, 240, 190), 2), egg, begged, 92, 10, enter="pop", z=Z_WORD)
    s.ring(egg, 92, 30, (255, 240, 190), r=40)
    s.show(s.emoji("🥴", 32), begged, t1, 30, 36, enter=None, hits=c.beats_in(begged, t1), amp=3)
    s.show(s.emoji("🙏", 24), begged + 0.2, t1, 104, 34, enter="pop", hits=c.beats_in(begged, t1)[::2], amp=2)
    s.show(s.word("DONT GO", RED, 2), go - 0.2, t1, 70, 6, enter="pop", z=Z_WORD)


def g_meds(s, t0, t1):
    c = s.cues
    med, stag, snow = c.w("medication", t0), c.w("staggered", t0), c.w("snow", t0)
    s.show(s.emoji("💊", 26), t0 + 0.3, t1, 22, 30, enter="pop", hits=c.beats_in(t0, stag), amp=2)
    s.show(s.word("FORGOT", WHITE, 2), c.w("forgot", t0), med, 80, 6, enter="pop", z=Z_WORD)
    s.show(s.word("MEDICATION", PINK, 2), med, stag, 80, 6, enter="pop", z=Z_WORD)
    s.ring(med, 22, 30, PINK, r=26)
    s.show(s.emoji("🚪", 34), t0, t1, 122, 38, enter="right", z=Z_BACK)
    # staggering to the door: a zig-zag, one step per beat
    gma = s.emoji("🥴", 26)
    beats = c.beats_in(stag, snow + 0.4)
    pts = [(stag, 48, 38)]
    for i, b in enumerate(beats[1:]):
        x = 48 + 74 * (i + 1) / max(1, len(beats) - 1)
        pts.append((b, x, 38 + (5 if i % 2 == 0 else -5)))
    pts.append((t1, 122, 38))
    s.show(gma, med, stag, 48, 38, enter="pop")
    s.glide(gma, pts, z=Z_FRONT)
    s.show(s.word("SNOW", ICE, 2), snow, t1, 80, 6, enter="pop", z=Z_WORD)
    s.snow(stag, t1, count=10)


def g_found(s, t0, t1):
    c = s.cues
    morning, scene, attack = c.w("morning", t0), c.w("scene", t0), c.w("attack", t0)
    s.show(s.emoji("🌅", 30), t0, scene, 70, 32, enter="bottom", enter_s=1.0)
    s.show(s.word("CHRISTMAS MORNING", GOLD, 1), morning - 0.3, scene, 70, 8, enter="pop", z=Z_WORD)
    band = tape(s, 140, 11)
    s.show(band, scene, t1, 70, 30, enter="left", enter_s=0.5, z=Z_FRONT)
    s.show(s.word("POLICE LINE", BLACK, 1), scene + 0.5, t1, 70, 30, enter="fade", enter_s=0.2, z=Z_WORD)
    s.show(s.emoji("🚓", 26), scene, t1, 24, 48, enter="left", z=Z_PIC)
    s.show(s.emoji("🔍", 22), attack, t1, 112, 48, enter="pop", hits=c.beats_in(attack, t1), amp=3)
    beats = c.beats_in(scene, t1)
    for i, b in enumerate(beats):
        s.ring(b, 24, 40, RED if i % 2 == 0 else BLUE, r=18, dur=0.4)


def g_hoof(s, t0, t1):
    c = s.cues
    hoof, claw = c.w("hoof", t0), c.w("claws", t0)
    s.show(s.emoji("👵", 34), t0, t1, 22, 34, enter="left")
    print_ = hoofprint(s, 8)
    for i, b in enumerate(c.beats_in(hoof, t1)[:12]):  # a trail of hoof prints marching across
        s.show(print_, b, t1, 44 + 8 * i, 44 if i % 2 == 0 else 52, enter="pop", enter_s=0.15)
    s.show(s.word("HOOF PRINTS", (210, 140, 60), 2), hoof, claw, 86, 12, enter="pop", z=Z_WORD)
    s.show(s.emoji("🐾", 20), claw, t1, 70, 22, enter="pop", z=Z_FRONT)
    s.show(s.word("CLAUS MARKS", RED, 2), claw, t1, 86, 12, enter="pop", z=Z_WORD)
    s.ring(claw, 70, 22, RED, r=40)


def g_proud(s, t0, t1):
    c = s.cues
    proud, foot, beer, cards = c.w("proud", t0), c.w("football", t0), c.w("beer", t0), c.w("cards", t0)
    beats = c.beats_in(t0, t1)
    s.show(s.emoji("👴", 34), t0, t1, 26, 34, enter="left", hits=beats[::2], amp=2)
    s.show(s.word("PROUD", GOLD, 2), proud, foot, 86, 8, enter="pop", z=Z_WORD)
    s.show(s.emoji("📺", 32), foot - 0.6, t1, 100, 34, enter="right", z=Z_BACK)
    s.show(s.emoji("🏈", 14), foot, beer, 100, 32, enter="pop", hits=c.beats_in(foot, beer), amp=3, z=Z_FRONT)
    s.show(s.word("FOOTBALL", (210, 140, 60), 2), foot, beer, 70, 8, enter="pop", z=Z_WORD)
    s.show(s.emoji("🍺", 18), beer, t1, 54, 42, enter="top", hits=c.beats_in(beer, t1)[1::2], amp=2, z=Z_FRONT)
    s.show(s.word("BEER", GOLD, 2), beer, cards, 70, 8, enter="pop", z=Z_WORD)
    s.show(s.emoji("🃏", 16), cards, t1, 100, 32, enter="pop", hits=c.beats_in(cards, t1), amp=2, z=Z_FRONT)
    s.show(s.word("CARDS", RED, 2), cards, t1, 70, 8, enter="pop", z=Z_WORD)


def g_black(s, t0, t1):
    c = s.cues
    without, black, wonder = c.w("without", t0), c.w("black", t0), c.w("wonder", t0)
    s.show(s.word("NOT CHRISTMAS", WHITE, 1), t0, black - 0.4, 70, 18, enter="pop", z=Z_WORD)
    s.show(s.word("WITHOUT GRANDMA", PINK, 1), without, black - 0.4, 70, 30, enter="pop", z=Z_WORD)
    s.show(s.emoji("🖤", 18), without + 0.4, black - 0.4, 70, 46, enter="pop")
    man = s.emoji("🕴️", 30)
    for i, x in enumerate((30, 70, 110)):
        s.show(man, black - 0.3 + 0.2 * i, t1, x, 36, enter="bottom", hits=c.beats_in(black, wonder)[i % 2::2])
    s.show(s.word("DRESSED IN BLACK", SILVER, 1), black, wonder, 70, 8, enter="pop", z=Z_WORD)
    s.show(s.emoji("🤔", 18), wonder, t1, 70, 12, enter="pop", z=Z_FRONT)
    for x in (30, 110):
        s.show(s.emoji("❓", 14), wonder + 0.3, t1, x, 12, enter="pop", z=Z_FRONT)


def g_gifts(s, t0, t1):
    c = s.cues
    opn, send = c.w("open", t0), c.w("send", t0)
    send2 = c.w("send", send + 0.3)
    gift = s.emoji("🎁", 36)
    s.show(gift, t0, send2, 70, 34, enter="top", hits=c.beats_in(t0 + 0.4, send2), amp=2)
    s.show(s.word("OPEN", GREEN, 2), opn, send2, 24, 30, enter="left", z=Z_WORD)
    s.show(s.word("SEND", RED, 2), send, send2, 116, 24, enter="right", z=Z_WORD)
    s.show(s.word("BACK", RED, 2), send + 0.3, send2, 116, 38, enter="right", z=Z_WORD)
    s.pic(gift, send2, t1, 70, 34, to=(170, 34))
    s.show(s.word("SEND THEM BACK", GOLD, 2), send2, t1, 70, 8, enter="pop", z=Z_WORD)
    s.ring(send2, 70, 34, GOLD, r=60)


def g_goose(s, t0, t1):
    c = s.cues
    goose, pud = c.w("goose", t0), c.w("pudding", t0)
    s.show(table(s, 120), t0, t1, 70, 52, enter="bottom", z=Z_BACK)
    s.show(s.emoji("🍗", 26), goose, t1, 44, 36, enter="top", hits=c.beats_in(goose, t1)[::2], amp=2)
    s.show(s.word("GOOSE", WHITE, 2), goose, pud, 70, 8, enter="pop", z=Z_WORD)
    s.show(s.emoji("🍮", 26), pud, t1, 96, 36, enter="top", hits=c.beats_in(pud, t1)[1::2], amp=2)
    s.show(s.word("FIG PUDDING", (190, 120, 60), 2), pud, t1, 70, 8, enter="pop", z=Z_WORD)
    s.ring(pud, 96, 36, GOLD, r=30)


def g_candles(s, t0, t1):
    c = s.cues
    blue, cand, hair = c.w("blue", t0), c.w("candles", t0), c.w("hair", t0)
    for i, b in enumerate(c.beats_in(blue, hair - 0.4)[:8]):
        col = (60, 120, 255) if i % 2 == 0 else SILVER
        s.show(candle(s, 24, col), b, hair - 0.3, 14 + 16 * i, 40, enter="bottom", enter_s=0.2)
    s.show(s.word("BLUE", (60, 120, 255), 2), blue, cand, 46, 8, enter="pop", z=Z_WORD)
    s.show(s.word("SILVER", SILVER, 2), blue + 0.5, cand, 98, 8, enter="pop", z=Z_WORD)
    # ... which match the hair in her wig
    gma = s.emoji("👵", 40)
    s.show(gma, hair - 0.3, t1, 70, 34, enter="pop")
    s.show(wig(s, 34), hair, t1, 70, 15, enter="top", z=Z_FRONT, hits=c.beats_in(hair + 0.4, t1), amp=2)
    s.show(s.word("WIG", (60, 120, 255), 3), hair, t1, 118, 30, enter="pop", z=Z_WORD)
    s.ring(hair + 0.35, 70, 20, (60, 120, 255), r=40)
    s.twinkle(t0, t1, ((60, 120, 255), SILVER), count=10)


def g_warn(s, t0, t1):
    c = s.cues
    watch, lic, sleigh, elves = c.w("watch", t0), c.w("license", t0), c.w("sleigh", t0), c.w("elves", t0)
    warn = s.emoji("⚠️", 34)
    s.show(warn, t0, lic, 70, 32, enter="pop", hits=c.beats_in(t0 + 0.3, lic), amp=2)
    s.show(s.word("WATCH OUT", RED, 2), watch, lic, 70, 6, enter="pop", z=Z_WORD)
    for b in c.bars_in(watch, lic):
        s.ring(b, 70, 32, YELLOW, r=50, dur=0.6)
    s.show(s.word("NO LICENSE", WHITE, 2), lic, sleigh - 0.3, 70, 30, enter="pop", z=Z_WORD)
    sleigh_team(s, sleigh - 0.8, elves + 0.9, 150, -110, 32, 24)
    s.show(s.emoji("🧝", 26), elves, t1, 70, 34, enter="bottom", hits=c.beats_in(elves, t1), amp=3)
    s.show(s.word("ELVES", GREEN, 2), elves, t1, 70, 6, enter="pop", z=Z_WORD)
    s.snow(t0, t1, count=5)


def g_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.2
    merry = c.w("merry", t0)
    beats = c.beats_in(t0, end - 2.0)
    # all's well: Grandma pops back up, the reindeer makes up with her
    s.show(s.emoji("👵", 32), t0, end, 52, 36, enter="pop", exit="fade", exit_s=2.0, hits=beats[0::2], amp=3)
    s.show(s.emoji("🦌", 32, flip=True), t0 + 0.5, end, 92, 36, enter="right", exit="fade", exit_s=2.0,
           hits=beats[1::2], amp=3)
    s.show(s.emoji("❤️", 14), t0 + 1.5, end, 72, 20, enter="pop", exit="fade", exit_s=2.0, z=Z_FRONT)
    s.show(s.word("MERRY", RED, 2), merry, end, 30, 8, enter="left", exit="fade", exit_s=2.0, z=Z_WORD)
    s.show(s.word("CHRISTMAS", GREEN, 2), merry + 0.4, end, 98, 8, enter="right", exit="fade", exit_s=2.0, z=Z_WORD)
    s.twinkle(t0, t1, XMAS, count=18, fade=2.0)
    s.snow(t0, t1, count=6, fade=2.0)


GARAGE = dict(intro=g_intro, chorus=g_chorus, santa=g_santa, eggnog=g_eggnog, meds=g_meds, found=g_found,
              hoof=g_hoof, proud=g_proud, black=g_black, gifts=g_gifts, goose=g_goose, candles=g_candles,
              warn=g_warn, finale=g_finale)


# ================================================================ the two windows as one stage

def wins(s):
    return tuple(s.center(m)[0] for m in s.places)  # the two windows, in --model order


WY = 26


def w_intro(s, t0, t1):
    L, C = wins(s)
    s.snow(0.0, t1, count=5, fade=1.0)
    s.show(s.emoji("🔔", 26), 0.4, t1, L, WY, enter="fade", enter_s=1.0, hits=s.cues.beats_in(1, t1)[0::2])
    s.show(s.emoji("🔔", 26, flip=True), 0.8, t1, C, WY, enter="fade", enter_s=1.0,
           hits=s.cues.beats_in(1, t1)[1::2])


def w_chorus(s, t0, t1, k):
    c = s.cues
    L, C = wins(s)
    run_, deer_t, walk = c.w("run", t0), c.w("reindeer", t0), c.w("walking", t0)
    gma, deer = s.emoji("👵", 28), s.emoji("🦌", 30)
    s.hold(gma, t0, deer_t, L, 30, hits=c.beats_in(t0, deer_t), amp=2)
    # the reindeer comes in from the right window, behind the wall, into the left one
    s.pic(deer, run_, deer_t, s.W + 18, 30, to=(L + 14, 30))
    s.pic(deer, deer_t, deer_t + 0.8, L + 14, 30, to=(-18, 30))
    launch(s, gma, deer_t, L, 30, up=-36)
    s.ring(deer_t, L, 26, WHITE, r=28)
    s.show(s.emoji("💫", 18), deer_t + 0.4, walk, L, 30, enter="pop", z=Z_FRONT)
    s.show(s.emoji("😱", 26), run_, walk, C, WY, enter="pop")
    s.show(s.emoji("🏠", 30), walk, t1, L, 30, enter="bottom")
    s.show(s.emoji("🌙", 24), walk + 0.3, t1, C, 20, enter="top")
    s.snow(walk, t1, count=5)


def w_santa(s, t0, t1, k):
    c = s.cues
    L, C = wins(s)
    no, santa, bel = c.w("no", t0), c.w("santa", t0), believe(c, t0, t1)
    s.show(s.emoji("👴", 30), t0, t1, L, WY, enter="left", hits=c.beats_in(t0, t1)[0::2], amp=2)
    s.show(s.emoji("❓", 26), no, santa, C, WY, enter="pop")
    s.show(s.emoji("🎅", 32), santa, t1, C, WY, enter="pop", hits=c.beats_in(santa + 0.3, t1)[1::2], amp=2)
    heart = s.emoji("❤️", 12)
    s.glide(heart, [(bel - 0.6, L, 8), (bel + 0.4, C, 8), (t1, C, 8)], z=Z_FRONT)
    s.ring(bel, C, WY, GOLD, r=30)
    s.twinkle(bel, t1, (GOLD, WHITE), count=20, steps=15, fade=0.3)


def w_eggnog(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    egg, begged = c.w("eggnog", t0), c.w("begged", t0)
    s.show(s.emoji("👵", 30), t0, egg, L, WY, enter="left")
    s.show(s.emoji("🥴", 30), egg, t1, L, WY, enter=None, hits=c.beats_in(egg, t1), amp=3)
    mug = s.emoji("🥛", 14)
    for i, b in enumerate(c.bars_in(t0, begged)):  # glasses slid over the wall from the right window
        s.glide(mug, [(b, C + 6, 38), (b + 1.0, L + 10, 38)], z=Z_FRONT)
    s.show(s.emoji("🙏", 28), begged, t1, C, WY, enter="right", hits=c.beats_in(begged, t1)[::2], amp=2)


def w_meds(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    med, stag = c.w("medication", t0), c.w("staggered", t0)
    s.show(s.emoji("💊", 26), t0, t1, L, 22, enter="pop", hits=c.beats_in(med, t1)[::2], amp=2)
    s.ring(med, L, 22, PINK, r=26)
    gma = s.emoji("🥴", 22)
    s.show(s.emoji("🚪", 32), t0 + 0.4, t1, C + 8, 28, enter="right", z=Z_BACK)
    beats = c.beats_in(stag, t1)
    pts = [(stag, L - 6, 34)]
    for i, b in enumerate(beats[1:]):
        x = L - 6 + (C + 8 - L + 6) * (i + 1) / max(1, len(beats) - 1)
        pts.append((b, x, 34 + (4 if i % 2 == 0 else -3)))
    s.glide(gma, pts, z=Z_FRONT)
    s.snow(stag, t1, count=8)


def w_found(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    scene = c.w("scene", t0)
    s.show(s.emoji("🌅", 30), t0, scene, L, WY, enter="bottom", enter_s=1.0)
    s.show(s.emoji("☕", 24), t0 + 0.5, scene, C, WY, enter="pop")
    # one long police tape stretched across both windows
    s.show(tape(s, s.W, 9), scene, t1, s.W / 2, 22, enter="left", enter_s=0.6, z=Z_FRONT)
    s.show(s.word("POLICE", BLACK, 1), scene + 0.6, t1, L, 22, enter="fade", enter_s=0.2, z=Z_WORD)
    s.show(s.word("LINE", BLACK, 1), scene + 0.6, t1, C, 22, enter="fade", enter_s=0.2, z=Z_WORD)
    s.show(s.emoji("🚨", 18), scene, t1, L, 40, enter="bottom", hits=c.beats_in(scene, t1), amp=2)
    s.show(s.emoji("🚓", 22), scene + 0.3, t1, C, 40, enter="right")
    for i, b in enumerate(c.beats_in(scene, t1)):
        s.ring(b, L, 40, RED if i % 2 == 0 else BLUE, r=18, dur=0.4)


def w_hoof(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    hoof, claw = c.w("hoof", t0), c.w("claws", t0)
    pr = hoofprint(s, 6)
    beats = c.beats_in(hoof, t1)
    n = len(beats)
    for i, b in enumerate(beats):  # a trail from the left window, over the wall, into the right
        x = 4 + (s.W - 8) * i / max(1, n - 1)
        s.show(pr, b, t1, x, 36 if i % 2 == 0 else 42, enter="pop", enter_s=0.15)
    s.show(s.emoji("👵", 24), t0, t1, L, 16, enter="top")
    s.show(s.emoji("🐾", 22), claw, t1, C, 16, enter="pop")
    s.ring(claw, C, 16, RED, r=24)


def w_proud(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    foot, beer, cards = c.w("football", t0), c.w("beer", t0), c.w("cards", t0)
    s.show(s.emoji("👴", 30), t0, t1, C, WY, enter="right", hits=c.beats_in(t0, t1)[::2], amp=2)
    s.show(s.emoji("📺", 30), foot - 0.6, t1, L, WY, enter="left")
    ball = s.emoji("🏈", 12)
    for i, b in enumerate(c.bars_in(foot, beer)):  # passes thrown over the wall
        a, z = (L, C) if i % 2 == 0 else (C, L)
        s.glide(ball, [(b, a, 20), (b + 0.5, (a + z) / 2, 3), (b + 1.0, z, 20)], z=Z_FRONT)
    s.show(s.emoji("🍺", 16), beer, t1, C + 12, 36, enter="top", z=Z_FRONT)
    s.show(s.emoji("🃏", 16), cards, t1, L, 40, enter="pop", z=Z_FRONT)


def w_black(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    black, wonder = c.w("black", t0), c.w("wonder", t0)
    s.show(s.emoji("🖤", 26), t0, black - 0.3, L, WY, enter="pop")
    s.show(s.emoji("😢", 26), t0 + 0.4, black - 0.3, C, WY, enter="pop")
    man = s.emoji("🕴️", 30)
    s.show(man, black - 0.3, t1, L, WY, enter="bottom")
    s.show(man, black, t1, C, WY, enter="bottom")
    s.show(s.emoji("🤔", 16), wonder, t1, L + 12, 8, enter="pop", z=Z_FRONT)
    s.show(s.emoji("🤔", 16), wonder + 0.2, t1, C + 12, 8, enter="pop", z=Z_FRONT)


def w_gifts(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    send = c.w("send", t0)
    send2 = c.w("send", send + 0.3)
    gift = s.emoji("🎁", 28)
    s.show(gift, t0, send, L, WY, enter="top", hits=c.beats_in(t0 + 0.4, send), amp=2)
    s.show(s.emoji("🤔", 28), t0 + 0.4, send2, C, WY, enter="pop")
    # sent back: across the wall and out the far side of the right window
    s.pic(gift, send, send2 + 0.8, L, WY, to=(s.W + 20, WY))
    s.ring(send2, C, WY, GOLD, r=26)
    s.show(s.emoji("📦", 24), send2 + 0.5, t1, L, WY, enter="pop")


def w_goose(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    goose, pud = c.w("goose", t0), c.w("pudding", t0)
    s.show(table(s, s.W), t0, t1, s.W / 2, 44, enter="bottom", z=Z_BACK)
    s.show(s.emoji("🍗", 26), goose, t1, L, 28, enter="top", hits=c.beats_in(goose, t1)[::2], amp=2)
    s.show(s.emoji("🍮", 26), pud, t1, C, 28, enter="top", hits=c.beats_in(pud, t1)[1::2], amp=2)


def w_candles(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    blue, hair = c.w("blue", t0), c.w("hair", t0)
    s.show(candle(s, 30, (60, 120, 255)), blue, hair - 0.3, L, 28, enter="bottom")
    s.show(candle(s, 30, SILVER), blue + 0.5, hair - 0.3, C, 28, enter="bottom")
    s.show(s.emoji("👵", 30), hair - 0.3, t1, L, 30, enter="pop")
    s.show(wig(s, 26), hair, t1, L, 15, enter="top", z=Z_FRONT)
    s.show(s.emoji("😲", 28), hair + 0.3, t1, C, WY, enter="pop")
    s.ring(hair + 0.35, L, 18, (60, 120, 255), r=26)


def w_warn(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    lic, sleigh, elves = c.w("license", t0), c.w("sleigh", t0), c.w("elves", t0)
    warn = s.emoji("⚠️", 30)
    beats = c.beats_in(t0, lic)
    s.flash([warn, s.emoji("👀", 28)], [t0] + beats[1::2], L, WY, end=lic)
    s.flash([s.emoji("👀", 28), warn], [t0] + beats[1::2], C, WY, end=lic)
    sleigh_team(s, sleigh - 0.8, elves + 0.8, s.W + 20, -110, 26, 18)
    s.show(s.emoji("🧝", 26), elves, t1, L, WY, enter="pop", hits=c.beats_in(elves, t1)[0::2], amp=3)
    s.show(s.emoji("🧝", 26, flip=True), elves + 0.2, t1, C, WY, enter="pop", hits=c.beats_in(elves, t1)[1::2],
           amp=3)


def w_finale(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    end = t1 - 0.2
    beats = c.beats_in(t0, end - 2.0)
    s.show(s.emoji("👵", 30), t0, end, L, WY, enter="pop", exit="fade", exit_s=2.0, hits=beats[0::2], amp=3)
    s.show(s.emoji("🦌", 30, flip=True), t0 + 0.4, end, C, WY, enter="pop", exit="fade", exit_s=2.0,
           hits=beats[1::2], amp=3)
    heart = s.emoji("❤️", 12)
    s.glide(heart, [(t0 + 1.2, C, 6), (t0 + 2.4, L, 6), (end, L, 6)], z=Z_FRONT)
    s.twinkle(t0, t1, XMAS, count=15, fade=2.0)


WINDOWS = dict(intro=w_intro, chorus=w_chorus, santa=w_santa, eggnog=w_eggnog, meds=w_meds, found=w_found,
               hoof=w_hoof, proud=w_proud, black=w_black, gifts=w_gifts, goose=w_goose, candles=w_candles,
               warn=w_warn, finale=w_finale)


# ================================================================ 200x42 matrix: 8 bushes, 25 px each

def bx(i):
    return 12.5 + 25 * i


BY = 22


def b_intro(s, t0, t1):
    c = s.cues
    bell = s.emoji("🔔", 20)
    beats = c.beats_in(0.3, t1)
    for i in range(8):
        b = beats[i] if i < len(beats) else t0
        s.show(bell, b * 0.5, t1, bx(i), BY, enter="top", enter_s=0.3, hits=beats[i % 2::2], amp=2)


def b_chorus(s, t0, t1, k):
    c = s.cues
    run_, deer_t, walk = c.w("run", t0), c.w("reindeer", t0), c.w("walking", t0)
    gma, deer = s.emoji("👵", 24), s.emoji("🦌", 24)
    g = 3 + (k % 3)  # which bush Grandma is standing in
    s.hold(gma, t0, deer_t, bx(g), BY, hits=c.beats_in(t0, deer_t), amp=2)
    s.pic(deer, run_, deer_t, 214, BY, to=(bx(g) + 14, BY))
    s.pic(deer, deer_t, deer_t + 1.2, bx(g) + 14, BY, to=(-14, BY))
    launch(s, gma, deer_t, bx(g), BY, up=-34)
    s.ring(deer_t, bx(g), BY, WHITE, r=16, dur=0.5)
    keys = [s.emoji("🏠", 22), s.emoji("🌙", 18)]
    for i in range(8):
        s.show(keys[i % 2], walk + 0.08 * i, t1, bx(i), BY, enter="bottom", hits=c.beats_in(walk, t1)[i % 2::2],
               amp=2)
    s.snow(walk, t1, count=3)


def b_santa(s, t0, t1, k):
    c = s.cues
    no, santa, bel = c.w("no", t0), c.w("santa", t0), believe(c, t0, t1)
    q, sc = s.emoji("❓", 20), s.emoji("🎅", 24)
    for i in range(8):
        s.show(q, no + 0.05 * i, santa, bx(i), BY, enter="pop")
        s.show(sc, santa + 0.05 * i, bel, bx(i), BY, enter="pop", hits=c.beats_in(santa, bel)[i % 2::2], amp=2)
    for i, ch in enumerate("BELIEVE"):
        s.show(s.word(ch, GOLD if i % 2 == 0 else RED, 5), bel + 0.08 * i, t1, bx(i), BY, enter="pop",
               enter_s=0.15, z=Z_WORD)
    s.show(s.emoji("❤️", 20), bel + 0.6, t1, bx(7), BY, enter="pop")


def b_eggnog(s, t0, t1):
    c = s.cues
    egg, begged = c.w("eggnog", t0), c.w("begged", t0)
    mug = s.emoji("🥛", 20)
    for i, b in enumerate(c.beats_in(t0, egg + 1.0)[:8]):
        s.show(mug, b, begged, bx(i), BY, enter="top", enter_s=0.2)
    keys = [s.emoji("🥴", 22), s.emoji("🙏", 20)]
    for i in range(8):
        s.show(keys[i % 2], begged + 0.05 * i, t1, bx(i), BY, enter="pop", hits=c.beats_in(begged, t1)[i % 2::2],
               amp=3)


def b_meds(s, t0, t1):
    c = s.cues
    stag = c.w("staggered", t0)
    pill = s.emoji("💊", 20)
    for i in range(8):
        s.show(pill, t0 + 0.1 * i, stag, bx(i), BY, enter="pop", hits=c.beats_in(t0, stag)[i % 2::2], amp=2)
    gma = s.emoji("🥴", 22)
    beats = c.beats_in(stag, t1)
    pts = [(stag, -12, BY)] + [(b, -12 + 224 * (i + 1) / max(1, len(beats)), BY + (4 if i % 2 else -4))
                               for i, b in enumerate(beats)]
    s.glide(gma, pts, z=Z_FRONT)
    s.snow(stag, t1, count=5)


def b_found(s, t0, t1):
    c = s.cues
    scene = c.w("scene", t0)
    sun = s.emoji("🌅", 22)
    for i in range(8):
        s.show(sun, t0 + 0.1 * i, scene, bx(i), BY, enter="bottom", enter_s=0.6)
    s.show(tape(s, 200, 9), scene, t1, 100, BY, enter="left", enter_s=0.8, z=Z_FRONT)
    for i in range(8):
        s.show(s.word("POLICE" if i % 2 == 0 else "LINE", BLACK, 1), scene + 0.8, t1, bx(i), BY, enter="fade",
               enter_s=0.2, z=Z_WORD)
    siren = s.emoji("🚨", 14)
    for i, b in enumerate(c.beats_in(scene, t1)):
        s.ring(b, bx(i % 8), BY, RED if i % 2 == 0 else BLUE, r=12, dur=0.4)
    s.show(siren, scene, t1, bx(0), 8, enter="top")
    s.show(siren, scene, t1, bx(7), 8, enter="top")


def b_hoof(s, t0, t1):
    c = s.cues
    hoof, claw = c.w("hoof", t0), c.w("claws", t0)
    pr = hoofprint(s, 8)
    for i, b in enumerate(c.beats_in(hoof, claw)[:16]):
        s.show(pr, b, t1, 8 + 12.5 * i, BY + (5 if i % 2 == 0 else -5), enter="pop", enter_s=0.15)
    paw = s.emoji("🐾", 18)
    for i in range(8):
        s.show(paw, claw + 0.06 * i, t1, bx(i), BY, enter="pop", z=Z_FRONT)


def b_proud(s, t0, t1):
    c = s.cues
    foot, beer, cards = c.w("football", t0), c.w("beer", t0), c.w("cards", t0)
    gpa = s.emoji("👴", 24)
    for i in range(8):
        s.show(gpa, t0 + 0.05 * i, foot, bx(i), BY, enter="bottom", hits=c.beats_in(t0, foot)[i % 2::2], amp=2)
    ball = s.emoji("🏈", 14)
    beats = c.beats_in(foot, beer)
    for k, b in enumerate(beats[:-1]):  # passed bush to bush on the beats
        i, j = k % 8, (k + 1) % 8
        if j == 0:
            continue
        mid = (b + beats[k + 1]) / 2
        s.pic(ball, b, mid, bx(i), 28, to=((bx(i) + bx(j)) / 2, 8))
        s.pic(ball, mid, beats[k + 1], (bx(i) + bx(j)) / 2, 8, to=(bx(j), 28))
    keys = [s.emoji("🍺", 20), s.emoji("🃏", 20)]
    for i in range(8):
        s.show(keys[0], beer + 0.05 * i, cards, bx(i), BY, enter="top", enter_s=0.2)
        s.show(keys[1], cards + 0.05 * i, t1, bx(i), BY, enter="pop", hits=c.beats_in(cards, t1)[i % 2::2], amp=2)


def b_black(s, t0, t1):
    c = s.cues
    black, wonder = c.w("black", t0), c.w("wonder", t0)
    heart, man, think = s.emoji("🖤", 18), s.emoji("🕴️", 24), s.emoji("🤔", 20)
    for i in range(8):
        s.show(heart, t0 + 0.08 * i, black - 0.3, bx(i), BY, enter="pop")
        s.show(man, black - 0.3 + 0.06 * i, wonder, bx(i), BY, enter="bottom")
        s.show(think, wonder + 0.06 * i, t1, bx(i), BY, enter="pop")


def b_gifts(s, t0, t1):
    c = s.cues
    send = c.w("send", t0)
    send2 = c.w("send", send + 0.3)
    gift = s.emoji("🎁", 20)
    for i in range(8):
        s.show(gift, t0 + 0.1 * i, send2, bx(i), BY, enter="top", hits=c.beats_in(t0, send2)[i % 2::2], amp=2)
        s.pic(gift, send2 + 0.05 * (7 - i), t1, bx(i), BY, to=(bx(i) + 220, BY))  # all sent back off the right


def b_goose(s, t0, t1):
    c = s.cues
    goose, pud = c.w("goose", t0), c.w("pudding", t0)
    s.show(table(s, 200), t0, t1, 100, 38, enter="bottom", z=Z_BACK)
    keys = [s.emoji("🍗", 18), s.emoji("🍮", 18)]
    for i in range(8):
        s.show(keys[i % 2], (goose if i % 2 == 0 else pud) + 0.05 * i, t1, bx(i), 24, enter="top",
               hits=c.beats_in(pud, t1)[i % 2::2], amp=2)


def b_candles(s, t0, t1):
    c = s.cues
    blue, hair = c.w("blue", t0), c.w("hair", t0)
    beats = c.beats_in(blue, hair)
    for i in range(8):
        col = (60, 120, 255) if i % 2 == 0 else SILVER
        b = beats[i] if i < len(beats) else blue + 0.2 * i
        s.show(candle(s, 30, col), b, t1, bx(i), BY + 4, enter="bottom", enter_s=0.2)
    s.show(s.emoji("👵", 22), hair, t1, bx(3) + 12.5, BY + 6, enter="pop", z=Z_FRONT)
    s.show(wig(s, 18), hair + 0.2, t1, bx(3) + 12.5, BY - 7, enter="top", z=Z_FRONT)
    s.twinkle(t0, t1, ((60, 120, 255), SILVER), count=8)


def b_warn(s, t0, t1):
    c = s.cues
    lic, sleigh, elves = c.w("license", t0), c.w("sleigh", t0), c.w("elves", t0)
    warn = s.emoji("⚠️", 22)
    beats = c.beats_in(t0, lic)
    for i in range(8):
        s.show(warn, t0 + 0.06 * i, lic, bx(i), BY, enter="pop", hits=beats[i % 2::2], amp=2)
    sleigh_team(s, sleigh - 0.8, elves + 0.8, 215, -110, BY, 22)
    elf = s.emoji("🧝", 22)
    for i in range(8):
        s.show(elf, elves + 0.06 * i, t1, bx(i), BY, enter="bottom", hits=c.beats_in(elves, t1)[i % 2::2], amp=3)


def b_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.2
    keys = [s.emoji("👵", 22), s.emoji("🦌", 22, flip=True), s.emoji("🎄", 22), s.emoji("❤️", 18)]
    beats = c.beats_in(t0 + 0.3, end - 2.0)
    for i in range(8):
        s.show(keys[i % 4], t0 + 0.06 * i, end, bx(i), BY, enter="pop", exit="fade", exit_s=2.0,
               hits=beats[i % 2::2], amp=2)
    s.twinkle(t0, t1, XMAS, count=10, fade=2.0)


BUSHES = dict(intro=b_intro, chorus=b_chorus, santa=b_santa, eggnog=b_eggnog, meds=b_meds, found=b_found,
              hoof=b_hoof, proud=b_proud, black=b_black, gifts=b_gifts, goose=b_goose, candles=b_candles,
              warn=b_warn, finale=b_finale)
