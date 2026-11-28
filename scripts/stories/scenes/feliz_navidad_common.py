"""Feliz Navidad matrix scenes, shared plan for the garage, the two windows (one stage) and the bushes.

The MegaTree carries the SuperStar story (FELIZ / NAVIDAD / MERRY spelled letter by letter in red, white and
green, a present at the start); these scenes spell the same words on the other matrices with a fiesta around
them. The song is two verses sung over and over - "Feliz Navidad ... prospero ano y felicidad" and "I want to
wish you a Merry Christmas ... from the bottom of my heart" - so every repeat gets its own props (guitar and
maracas, a pinata, dancers and chili peppers; presents, poinsettias, trees and bells) to keep it from looping.
Words, beats, bars and horn hits come from the sequence's own timing tracks. The garage keeps the sequence's own
trumpet pictures and horn chases (Story.keep): the Merry Christmas verses are theirs there.
"""
import html
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
import matrix_storybook as mb  # noqa: E402
from matrix_scenes import Cues  # noqa: E402
from morph_backdrop import backdrop, pattern_sweeps  # noqa: E402
from rockin_common import GOLD, GREEN, PINK, RED, WHITE, Z_BACK, Z_FRONT, Z_PIC, Z_WORD  # noqa: E402,F401

WORDS_TRACK, BEATS_TRACK, BARS_TRACK, HORNS_TRACK = "Lyrics 1", "Beats", "Bars", "Horns"
ORANGE = (255, 120, 0)
FLAG = (RED, WHITE, GREEN)
FIESTA = (RED, GREEN, GOLD, PINK, ORANGE)


def cues(xsq):
    root = ET.parse(xsq).getroot()
    words, beats, bars, horns = [], [], [], []
    for e in root.find("ElementEffects"):
        lays = e.findall("EffectLayer")
        name = e.get("name")
        if name == WORDS_TRACK and len(lays) > 1:
            words = [(html.unescape(f.get("label")), int(f.get("startTime")) / 1000, int(f.get("endTime")) / 1000)
                     for f in lays[1] if f.get("label")]
        elif lays and name in (BEATS_TRACK, BARS_TRACK, HORNS_TRACK):
            ts = [int(f.get("startTime")) / 1000 for f in lays[0]]
            {BEATS_TRACK: beats, BARS_TRACK: bars, HORNS_TRACK: horns}[name].extend(ts)
    c = Cues(words, beats, float(root.findtext("head/sequenceDuration")))
    if bars:
        c.bars = sorted(bars)
    c.horns = sorted(horns)
    return c


def words_in(c, word, t0, t1):
    return [s for w, s, _ in c.words if w == word and t0 <= s < t1]


def thin(ts, gap=0.3):
    """Hits at least `gap` apart (a hop takes 0.25 s)."""
    out = []
    for t in ts:
        if not out or t - out[-1] >= gap:
            out.append(t)
    return out


def horns_in(c, t0, t1):
    return thin([h for h in c.horns if t0 <= h < t1])


def plan(c):
    """intro, then the Feliz Navidad verse and the Merry Christmas verse in turn; each repeat has a variant number."""
    t = [("intro", 0.0)]
    nf = nm = 0
    for t0 in (11.0, 24.5, 63.7, 75.8, 115.0, 128.2, 166.5):
        start = c.w("ah", t0) - 0.1 if t0 == 75.8 else c.w("fay", t0) - 0.1
        t.append((f"feliz{nf}", start))
        nf += 1
    for t0 in (37.0, 50.3, 89.0, 102.0, 140.5, 153.5):
        t.append((f"merry{nm}", c.w("want", t0) - 0.25))
        nm += 1
    t.sort(key=lambda x: x[1])
    t[-1] = ("finale", t[-1][1])
    return [(n, t0, t[k + 1][1] if k + 1 < len(t) else c.duration) for k, (n, t0) in enumerate(t)]


def run(s, scenes):
    for name, t0, t1 in plan(s.cues):
        backdrop(s, t0, t1)
        base = name.rstrip("0123456789")
        v = int(name[len(base):] or 0)
        fn = scenes.get(base)
        if fn:
            fn(s, t0, t1) if base in ("intro", "finale") else fn(s, t0, t1, v)


def verse(c, t0, t1):
    """The Feliz Navidad verse: (fay times, nav times, pro, feel, last dad)."""
    fays, navs = words_in(c, "fay", t0, t1), words_in(c, "nav", t0, t1)
    pro = c.w("pro", t0)
    return fays, navs, pro, c.w("feel", pro), words_in(c, "dad", pro, t1)[-1]


def lines(c, t0, t1):
    """The Merry Christmas verse: (line starts, merry times, christmas times, bottom, heart)."""
    starts = [w - 0.15 for w in words_in(c, "want", t0, t1)]
    return starts, words_in(c, "merry", t0, t1), words_in(c, "christmas", t0, t1), c.w("bottom", t0), \
        c.w("heart", t0)


# ---------------------------------------------------------------- pictures

GLYPHS = dict(mb.FONT, Z=["###", "..#", ".#.", "#..", "###"])  # the 3x5 font has no Z


def tri(s, text, scale, colors=FLAG, shift=0):
    """A word in the pixel font, letters coloured in turn (red, white, green); draws the Z the font lacks."""
    w = sum(len(GLYPHS.get(ch, GLYPHS[" "])[0]) + 1 for ch in text) * scale - scale
    im = Image.new("RGBA", (w + 2, 5 * scale + 2), (0, 0, 0, 0))
    px = im.load()
    x, k = 0, shift
    for ch in text:
        g = GLYPHS.get(ch, GLYPHS[" "])
        col = tuple(colors[k % len(colors)]) + (255,)
        for gy, row in enumerate(g):
            for gx, on in enumerate(row):
                if on == "#":
                    for sy in range(scale):
                        for sx in range(scale):
                            px[x + gx * scale + sx, gy * scale + sy] = col
        x += (len(g[0]) + 1) * scale
        if ch != " ":
            k += 1
    cname = "".join(f"{c[0]:02x}{c[1]:02x}" for c in colors)
    return s.image(f"t_{text.replace(' ', '_').lower()}_{scale}_{shift % len(colors)}_{cname}", im)


def poinsettia(s, px):
    """The Christmas flower: red pointed petals around a gold centre, a few green leaves behind."""
    def draw(d, im):
        c, r = px / 2, px / 2 - 0.5

        def petal(a, length, width, col):
            ax, ay = math.cos(a), math.sin(a)
            bx, by = -ay, ax
            d.polygon([(c + bx * width, c + by * width), (c + ax * length, c + ay * length),
                       (c - bx * width, c - by * width), (c - ax * length * 0.15, c - ay * length * 0.15)], fill=col)
        for k in range(5):
            petal(math.pi / 2 + k * 2 * math.pi / 5 + 0.6, r, px * 0.13, (0, 120, 40, 255))
        for k in range(6):
            petal(-math.pi / 2 + k * math.pi / 3, r * 0.95, px * 0.15, (225, 0, 20, 255))
        for k in range(6):
            petal(-math.pi / 2 + math.pi / 6 + k * math.pi / 3, r * 0.6, px * 0.12, (255, 60, 60, 255))
        d.ellipse([c - px * 0.1, c - px * 0.1, c + px * 0.1, c + px * 0.1], fill=(255, 210, 0, 255))
    return s.drawn(f"poinsettia_{px}", px, px, draw)


def sombrero(s, w):
    """A wide-brimmed sombrero with a red-white-green band."""
    h = round(w * 0.55)

    def draw(d, im):
        d.ellipse([0, h * 0.55, w - 1, h - 1], fill=(230, 180, 60, 255))  # brim
        d.ellipse([w * 0.06, h * 0.6, w * 0.94, h * 0.92], fill=(200, 150, 40, 255))
        d.polygon([(w * 0.3, h * 0.72), (w * 0.38, h * 0.08), (w * 0.62, h * 0.08), (w * 0.7, h * 0.72)],
                  fill=(240, 195, 70, 255))  # crown
        d.ellipse([w * 0.37, 0, w * 0.63, h * 0.18], fill=(240, 195, 70, 255))
        band = max(1, round(h * 0.08))
        for k, col in enumerate(FLAG):
            x0 = w * (0.32 + 0.12 * k)
            d.rectangle([x0, h * 0.56, x0 + w * 0.12, h * 0.56 + band], fill=col + (255,))
    return s.drawn(f"sombrero_{w}", w, h, draw)


def variant_props(s, v, px):
    """The props for repeat v of the Feliz Navidad verse: (left, right)."""
    k = v % 3
    if k == 0:
        return s.emoji("🎸", px), s.emoji("🪇", px)
    if k == 1:
        return s.emoji("🪅", px), s.emoji("🎉", px)
    return s.emoji("💃", px), s.emoji("🕺", px)


def merry_props(s, v, px):
    k = v % 3
    if k == 0:
        return s.emoji("🎁", px), s.emoji("🎁", px, flip=True)
    if k == 1:
        return poinsettia(s, px), poinsettia(s, px)
    return s.emoji("🎄", px), s.emoji("🔔", px)


def swing(s, key, t0, t1, x, y, beats, amp=4, z=Z_PIC):
    """Swing side to side, one swing per beat (the pinata on its rope)."""
    pts, side = [(t0, x, y)], 1
    for b in beats:
        if t0 < b < t1:
            pts.append((b, x + side * amp, y))
            side = -side
    pts.append((t1, pts[-1][1], y))
    s.glide(key, pts, z=z)


def burst_img(s, px, color=GOLD, inner=WHITE):
    """A firework burst: rays of dots from a bright centre (the emoji has a dark square behind it)."""
    def draw(d, im):
        c = (px - 1) / 2
        for k in range(12):
            a = k * math.pi / 6
            for f, col, r in ((0.95, color, 1.0), (0.7, color, 0.8), (0.45, inner, 0.7)):
                x, y = c + math.cos(a) * c * f, c + math.sin(a) * c * f
                d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(col) + (255,))
        d.ellipse([c - 1.5, c - 1.5, c + 1.5, c + 1.5], fill=tuple(inner) + (255,))
    return s.drawn(f"burst_{px}_{color[0]:02x}{color[1]:02x}{color[2]:02x}", px, px, draw)


def fireworks(s, t, spots, colors=FIESTA, px=26, r=30, every=0.18):
    """A burst of fireworks: a picture and a ring at each spot, one after another."""
    for k, (x, y) in enumerate(spots):
        a = t + every * k
        s.show(burst_img(s, px, colors[k % len(colors)]), a, a + 1.2, x, y, enter="pop", exit="fade", enter_s=0.2,
               exit_s=0.5, z=Z_FRONT)
        s.ring(a, x, y, colors[k % len(colors)], r=r, dur=0.8, width=2)


# ================================================================ 140x60 matrix (the garage)

def g_intro(s, t0, t1):
    c = s.cues
    horns = horns_in(c, t0, t1)
    s.show(s.emoji("🎁", 34), 0.2, 11.5, 70, 32, enter="pop", hits=horns, amp=3)
    s.show(s.emoji("🪇", 28), 0.4, t1, 20, 34, enter="left", enter_s=0.8, hits=horns[0::2], amp=3)
    s.show(s.emoji("🎺", 28, flip=True), 1.2, t1, 120, 34, enter="right", enter_s=0.8, hits=horns[1::2], amp=3)
    # the present bursts open into confetti just before the singing starts
    s.ring(11.5, 70, 32, GOLD, r=60, dur=0.8, width=3)
    s.show(s.emoji("🎊", 30), 11.5, t1, 70, 32, enter="pop", enter_s=0.2)
    s.twinkle(0.2, t1, FIESTA, count=8, steps=30, fade=1.0)


def g_feliz(s, t0, t1, v):
    c = s.cues
    fays, navs, pro, feel, dad = verse(c, t0, t1)
    left, right = variant_props(s, v, 30)
    beats = c.beats_in(t0, t1)
    hits = thin(beats + horns_in(c, t0, t1))
    if v % 3 == 1:  # the pinata swings until felicidad, then bursts
        swing(s, left, t0, feel, 20, 30, beats)
        s.ring(feel, 20, 30, PINK, r=40, dur=0.9, width=3)
        s.show(s.emoji("🎊", 30), feel, t1, 20, 30, enter="pop", enter_s=0.2)
    else:
        s.show(left, t0, t1, 20, 34, enter="left", enter_s=0.5, hits=hits[0::2], amp=3)
    s.show(right, t0 + 0.2, t1, 120, 34, enter="right", enter_s=0.5, hits=hits[1::2], amp=3)
    if v % 3 == 2:  # the dancers get sombreros, chili peppers in the top corners
        hat = sombrero(s, 22)
        s.show(hat, t0 + 0.6, t1, 20, 16, enter="top", hits=hits[0::2], amp=3, z=Z_FRONT)
        s.show(hat, t0 + 0.8, t1, 120, 16, enter="top", hits=hits[1::2], amp=3, z=Z_FRONT)
        for x in (8, 132):
            s.show(s.emoji("🌶️", 12), t0 + 0.5, t1, x, 8, enter="top", hits=beats[::2], amp=2, z=Z_FRONT)
    # Feliz on "fay", Navidad on "nav", three times, the colours turning each line
    ends = fays[1:] + [pro]
    for i, (f, e) in enumerate(zip(fays, ends)):
        nav = next((n for n in navs if f <= n < e), f + 0.6)
        s.show(tri(s, "FELIZ", 3, shift=i), f, e - 0.05, 70, 17, enter="pop", enter_s=0.2, z=Z_WORD)
        s.show(tri(s, "NAVIDAD", 2, shift=i + 1), nav, e - 0.05, 70, 40, enter="pop", enter_s=0.2, z=Z_WORD)
        s.ring(f, 70, 17, FLAG[i % 3], r=50, dur=0.7, width=2)
    s.show(s.word("PROSPERO", GOLD, 2), pro, t1, 70, 17, enter="top", enter_s=0.3, z=Z_WORD)
    s.show(tri(s, "FELICIDAD", 2, shift=v), feel, t1, 70, 40, enter="pop", enter_s=0.2, z=Z_WORD)
    corners = [(20, 14), (120, 14), (20, 48), (120, 48)]
    fireworks(s, feel, corners if v % 2 else corners[1::-1] + corners[:1:-1])
    s.twinkle(feel, t1, FIESTA, count=20, steps=20, fade=0.5)


def g_merry(s, t0, t1, v):
    c = s.cues
    starts, merrys, xmases, bottom, heart = lines(c, t0, t1)
    left, right = merry_props(s, v, 30)
    hits = thin(c.beats_in(t0, t1) + horns_in(c, t0, t1))
    s.show(left, t0, bottom, 20, 32, enter="pop", exit="left", hits=hits[0::2], amp=3)
    s.show(right, t0 + 0.2, bottom, 120, 32, enter="pop", exit="right", hits=hits[1::2], amp=3)
    pattern_sweeps(s, t0, bottom, (RED, GREEN, GOLD))
    ends = starts[1:] + [bottom]
    for i, (a, e) in enumerate(zip(starts, ends)):
        m = next((w for w in merrys if a <= w < e), a + 1.0)
        x = next((w for w in xmases if a <= w < e), m + 0.6)
        s.show(s.word("MERRY", RED, 3), m, e - 0.05, 70, 16, enter="pop", enter_s=0.2, z=Z_WORD)
        s.show(s.word("CHRISTMAS", GREEN if i % 2 == 0 else WHITE, 2), x, e - 0.05, 70, 40, enter="pop",
               enter_s=0.2, z=Z_WORD)
        s.ring(m, 70, 16, (RED, GOLD, GREEN)[(i + v) % 3], r=50, dur=0.7, width=2)
    # from the bottom of my heart: one big heart beating in the middle
    heartk = s.emoji("❤️", 40)
    s.show(heartk, bottom, t1, 70, 30, enter="pop", enter_s=0.4, exit="fade", exit_s=0.4,
           hits=[b for b in c.beats_in(heart, t1)], amp=3)
    s.ring(heart, 70, 30, RED, r=70, dur=1.0, width=3)
    s.ring(heart + 0.3, 70, 30, PINK, r=70, dur=1.0, width=2)
    for k, x in enumerate((24, 116)):
        s.show(s.emoji("💖", 18), heart + 0.2 * k, t1, x, 30, enter="pop", exit="fade", exit_s=0.4, z=Z_FRONT)
    s.twinkle(heart, t1, (RED, PINK, WHITE), count=20, steps=20, fade=0.4)


def g_finale(s, t0, t1):
    c = s.cues
    g_feliz(s, t0, min(t1, c.w("dad", c.w("see", t0)) + 1.5), 6)
    end = t1 - 0.1
    a = c.w("dad", c.w("see", t0)) + 1.5
    s.show(tri(s, "FELIZ", 3), a, end, 70, 17, enter="pop", exit="fade", exit_s=1.0, z=Z_WORD)
    s.show(tri(s, "NAVIDAD", 2, shift=1), a + 0.3, end, 70, 40, enter="pop", exit="fade", exit_s=1.0, z=Z_WORD)
    for k, h in enumerate(horns_in(c, a, end - 0.5)):
        fireworks(s, h, [((20, 120, 45, 95)[k % 4], (14, 46, 46, 14)[k % 4])], px=24, r=34)


def g_horns(s, t0, t1, v):
    """The Merry Christmas verses are the trumpets' part: the sequence's own trumpet pictures stay on the garage
    (the story plays on the windows and bushes)."""
    s.keep(t0, t1, ("Pictures",))
    s.twinkle(t0, t1, (GOLD, WHITE), count=10, steps=20, fade=0.5)


def g_feliz_horns(s, t0, t1, v):
    g_feliz(s, t0, t1, v)
    s.keep(t0, t1, ("Pictures",))  # the trumpet stabs between the lines
    s.keep(t0, t1, ("SingleStrand",), z=12)  # the horn riffs' chases, behind the pictures


def g_finale_horns(s, t0, t1):
    g_finale(s, t0, t1)
    s.keep(t0, t1, ("Pictures",), z=Z_WORD - 1)
    s.keep(t0, t1, ("SingleStrand",), z=12)


GARAGE = dict(intro=g_intro, feliz=g_feliz_horns, merry=g_horns, finale=g_finale_horns)


# ================================================================ the two windows as one stage

def wins(s):
    return tuple(s.center(m)[0] for m in s.places)  # the two windows, in --model order


def w_intro(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    horns = horns_in(c, t0, t1)
    s.show(s.emoji("🪇", 30), 0.3, t1, L, 26, enter="pop", hits=horns[0::2], amp=3)
    s.show(s.emoji("🎺", 30, flip=True), 1.0, t1, C, 26, enter="pop", hits=horns[1::2], amp=3)
    s.ring(11.5, L, 26, GOLD, r=30, dur=0.8, width=2)
    s.ring(11.5, C, 26, GOLD, r=30, dur=0.8, width=2)
    s.twinkle(0.2, t1, FIESTA, count=6, steps=30, fade=1.0)


def w_feliz(s, t0, t1, v):
    c = s.cues
    L, C = wins(s)
    fays, navs, pro, feel, dad = verse(c, t0, t1)
    left, right = variant_props(s, v, 22)
    beats = c.beats_in(t0, t1)
    hits = thin(beats + horns_in(c, t0, t1))
    if v % 3 == 1:
        swing(s, left, t0, feel, L, 35, beats, amp=3)
        s.ring(feel, L, 35, PINK, r=26, dur=0.8, width=2)
        s.show(s.emoji("🎊", 22), feel, t1, L, 35, enter="pop", enter_s=0.2)
    else:
        s.show(left, t0, pro, L, 35, enter="bottom", enter_s=0.4, hits=hits[0::2], amp=2)
    s.show(right, t0 + 0.2, pro, C, 36, enter="bottom", enter_s=0.4, hits=hits[1::2], amp=2)
    ends = fays[1:] + [pro]
    for i, (f, e) in enumerate(zip(fays, ends)):
        nav = next((n for n in navs if f <= n < e), f + 0.6)
        s.show(tri(s, "FELIZ", 2, shift=i), f, e - 0.05, L, 12, enter="pop", enter_s=0.2, z=Z_WORD)
        s.show(tri(s, "NAVI", 2, shift=i + 1), nav, e - 0.05, C, 8, enter="pop", enter_s=0.2, z=Z_WORD)
        s.show(tri(s, "DAD", 2, shift=i + 2), nav + 0.15, e - 0.05, C, 21, enter="pop", enter_s=0.2, z=Z_WORD)
    # prospero ano y felicidad: fireworks over both windows
    s.show(burst_img(s, 30, GOLD, RED), pro, t1, L if v % 2 else C, 22, enter="pop", hits=beats[::2], amp=2)
    fireworks(s, feel, [(L, 12), (C, 12), (L, 34), (C, 34)], px=20, r=24)
    s.twinkle(feel, t1, FIESTA, count=16, steps=20, fade=0.5)


def w_merry(s, t0, t1, v):
    c = s.cues
    L, C = wins(s)
    starts, merrys, xmases, bottom, heart = lines(c, t0, t1)
    left, right = merry_props(s, v, 28)
    hits = thin(c.beats_in(t0, t1) + horns_in(c, t0, t1))
    pattern_sweeps(s, t0, bottom, (RED, GREEN, GOLD))
    ends = starts[1:] + [bottom]
    for i, (a, e) in enumerate(zip(starts, ends)):
        m = next((w for w in merrys if a <= w < e), a + 1.0)
        x = next((w for w in xmases if a <= w < e), m + 0.6)
        s.show(s.word("MERRY", RED, 1), m, e - 0.05, L, 7, enter="pop", enter_s=0.2, z=Z_WORD)
        s.show(left, m, e - 0.05, L, 30, enter="pop", hits=[h for h in hits if m < h < e][0::2], amp=2)
        s.show(s.word("XMAS", GREEN if i % 2 == 0 else WHITE, 2), x, e - 0.05, C, 9, enter="pop", enter_s=0.2,
               z=Z_WORD)
        s.show(right, x, e - 0.05, C, 31, enter="pop", hits=[h for h in hits if x < h < e][1::2], amp=2)
    heartk = s.emoji("❤️", 30)
    beats = c.beats_in(heart, t1)
    s.show(heartk, bottom, t1, L, 24, enter="pop", exit="fade", exit_s=0.4, hits=beats[0::2], amp=2)
    s.show(heartk, bottom + 0.3, t1, C, 24, enter="pop", exit="fade", exit_s=0.4, hits=beats[1::2], amp=2)
    s.ring(heart, L, 24, RED, r=30, dur=1.0, width=2)
    s.ring(heart, C, 24, RED, r=30, dur=1.0, width=2)
    s.twinkle(heart, t1, (RED, PINK, WHITE), count=14, steps=20, fade=0.4)


def w_finale(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    a = c.w("dad", c.w("see", t0)) + 1.5
    w_feliz(s, t0, min(t1, a), 6)
    end = t1 - 0.1
    s.show(tri(s, "FELIZ", 2), a, end, L, 12, enter="pop", exit="fade", exit_s=1.0, z=Z_WORD)
    s.show(tri(s, "NAVI", 2, shift=1), a + 0.3, end, C, 8, enter="pop", exit="fade", exit_s=1.0, z=Z_WORD)
    s.show(tri(s, "DAD", 2, shift=2), a + 0.45, end, C, 21, enter="pop", exit="fade", exit_s=1.0, z=Z_WORD)
    for k, h in enumerate(horns_in(c, a, end - 0.5)):
        fireworks(s, h, [((L, C)[k % 2], 34)], px=20, r=26)


WINDOWS = dict(intro=w_intro, feliz=w_feliz, merry=w_merry, finale=w_finale)


# ================================================================ 200x42 matrix: 8 bushes, 25 px each

def bx(i):
    return 12.5 + 25 * i


BY = 22


def spell(s, text, t, end, first, colors=FLAG, shift=0, stagger=0.06):
    """One big letter per bush, from bush `first`."""
    for k, ch in enumerate(text):
        s.show(tri(s, ch, 5, colors, shift + k), t + stagger * k, end, bx(first + k), BY, enter="pop",
               enter_s=0.2, z=Z_WORD)


def b_intro(s, t0, t1):
    c = s.cues
    horns = horns_in(c, t0, t1)
    mar = s.emoji("🪇", 22)
    for i in range(8):
        a = horns[i] if i < len(horns) else 0.3 + 0.2 * i
        s.show(mar, a, t1, bx(i), BY, enter="pop", hits=[h for h in horns if h > a][i % 2::2], amp=2)
    s.ring(11.5, 100, BY, GOLD, r=100, dur=0.8, width=3)


def b_feliz(s, t0, t1, v):
    c = s.cues
    fays, navs, pro, feel, dad = verse(c, t0, t1)
    left, right = variant_props(s, v, 22)
    beats = c.beats_in(t0, t1)
    ends = fays[1:] + [pro]
    for i, (f, e) in enumerate(zip(fays, ends)):
        nav = next((n for n in navs if f <= n < e), f + 0.6)
        lo = i % 2 == 0  # Feliz on the left five bushes, then on the right five
        spell(s, "FELIZ", f, nav - 0.05, 0 if lo else 3, shift=i)
        for k in ((5, 6, 7) if lo else (0, 1, 2)):
            s.show((left, right)[k % 2], f + 0.05 * k, nav - 0.05, bx(k), BY, enter="pop", enter_s=0.2)
        spell(s, "NAVIDAD", nav, e - 0.05, 0 if lo else 1, shift=i + 1, stagger=0.05)
        s.show((left, right)[i % 2], nav + 0.4, e - 0.05, bx(7 if lo else 0), BY, enter="pop", enter_s=0.2)
    # prospero: the fiesta on every bush, then fireworks along the row on felicidad
    hits = thin(beats + horns_in(c, pro, t1))
    for i in range(8):
        s.show((left, right)[i % 2], pro + 0.05 * i, feel, bx(i), BY, enter="pop", enter_s=0.2,
               hits=hits[i % 2::2], amp=2)
    order = range(8) if v % 2 == 0 else range(7, -1, -1)
    fireworks(s, feel, [(bx(i), BY) for i in order], px=22, r=20, every=0.1)
    s.twinkle(feel, t1, FIESTA, count=16, steps=20, fade=0.5)


def b_merry(s, t0, t1, v):
    c = s.cues
    starts, merrys, xmases, bottom, heart = lines(c, t0, t1)
    left, right = merry_props(s, v, 22)
    hits = thin(c.beats_in(t0, t1) + horns_in(c, t0, t1))
    pattern_sweeps(s, t0, bottom, (RED, GREEN, GOLD))
    ends = starts[1:] + [bottom]
    for i, (a, e) in enumerate(zip(starts, ends)):
        m = next((w for w in merrys if a <= w < e), a + 1.0)
        x = next((w for w in xmases if a <= w < e), m + 0.6)
        first = 0 if i % 2 == 0 else 3
        spell(s, "MERRY", m, x - 0.05, first, colors=(RED, WHITE), shift=i)
        for k in range(8):  # on Christmas the props fill the row
            s.show((left, right)[k % 2], x + 0.05 * k, e - 0.05, bx(k), BY, enter="pop", enter_s=0.2,
                   hits=[h for h in hits if x < h < e][k % 2::2], amp=2)
    heartk = s.emoji("❤️", 22)
    beats = c.beats_in(heart, t1)
    for i in range(8):
        s.show(heartk, bottom + 0.06 * i, t1, bx(i), BY, enter="pop", exit="fade", exit_s=0.4,
               hits=beats[i % 2::2], amp=2)
    s.ring(heart, 100, BY, RED, r=100, dur=1.0, width=3)
    s.twinkle(heart, t1, (RED, PINK, WHITE), count=14, steps=20, fade=0.4)


def b_finale(s, t0, t1):
    c = s.cues
    a = c.w("dad", c.w("see", t0)) + 1.5
    b_feliz(s, t0, min(t1, a), 6)
    end = t1 - 0.1
    spell(s, "FELIZ", a, a + 1.6, 0)
    spell(s, "NAVIDAD", a + 1.6, end, 0, shift=1, stagger=0.05)
    s.show(burst_img(s, 22, GREEN), a + 1.6, end, bx(7), BY, enter="pop", exit="fade", exit_s=1.0)
    for k, h in enumerate(horns_in(c, a, end - 0.5)):
        s.ring(h, bx((k * 3) % 8), BY, FIESTA[k % 5], r=24, dur=0.7, width=2)


BUSHES = dict(intro=b_intro, feliz=b_feliz, merry=b_merry, finale=b_finale)
