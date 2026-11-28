"""Little Saint Nick matrix scenes, shared plan for the garage, the two windows (one stage) and the bushes.

The MegaTree carries the SuperStar story (the bell, MERRY CHRISTMAS, a crowd of Santas, NORTH, the carolling
family, Santa in his gym shorts, the hot-rod sleigh with its exhaust and stick shift, Santa at the wheel, the
reindeer standing then leaping, the sack, the wheel spinning, MERRY CHRISTMAS SAINT NICK); these scenes follow the
same lines on the other matrices. A fast surf-rock song: pops and slides, the sleigh racing across the windows and
along the bushes, the reindeer galloping on "run run reindeer".
Santa, the family, the sleigh, the reindeer and the sack are the sequence's own SuperStar MegaTree pictures,
loaded from the .xsq at build time and aspect corrected (see ss()).
Words: the sequence's three lyric tracks merged (lead, the "ooh"s and "Merry Christmas Saint Nick", "run run
reindeer"); beats and bars: its Beats track; the Hits track gives the intro and reindeer accents.
"""
import base64
import html
import io
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
from morph_backdrop import backdrop, pattern_sweeps  # noqa: E402
from matrix_scenes import Cues  # noqa: E402
from rockin_common import GOLD, GREEN, ICE, RED, WHITE, Z_BACK, Z_FRONT, Z_PIC, Z_WORD  # noqa: E402,F401

CANDY = (255, 20, 40)
CHROME = (190, 200, 220)
XMAS = (RED, GREEN, GOLD, WHITE)
SURF = (RED, WHITE, ICE, GOLD)
LYRIC_TRACKS = ("Lyric 1", "Lyric 2", "Lyric 3")
_SS = {"xsq": None, "imgs": None, "hits": []}


def cues(xsq):
    _SS["xsq"] = xsq
    root = ET.parse(xsq).getroot()
    dur = float(root.findtext("head/sequenceDuration"))
    words, beats, ones = [], [], []
    for e in root.find("ElementEffects"):
        if e.get("type") != "timing":
            continue
        layers = e.findall("EffectLayer")
        name = e.get("name")
        if name in LYRIC_TRACKS and len(layers) > 1:
            words += [(html.unescape(f.get("label")), int(f.get("startTime")) / 1000, int(f.get("endTime")) / 1000)
                      for f in layers[1] if f.get("label")]
        elif name == "Beats":
            for f in layers[0]:
                lab, t = f.get("label") or "", int(f.get("startTime")) / 1000
                if lab and t < dur:
                    beats.append(t)
                    if lab == "1":
                        ones.append(t)
        elif name == "Hits":
            _SS["hits"] = [int(f.get("startTime")) / 1000 for f in layers[0]][2:]  # the first two are empty marks
    words.sort(key=lambda w: w[1])
    c = Cues(words, beats, dur)
    c.bars = ones
    return c


def hits(t0, t1):
    return [h for h in _SS["hits"] if t0 <= h < t1]


def plan(c):
    w = c.w
    t = [
        ("intro", 0.0),
        ("comes", w("christmas", 8.0) - 0.1),
        ("north", w("well", 14) - 0.1),
        ("tale", w("theres", 18) - 0.1),
        ("cat", w("and", 22) - 0.1),
        ("workout", w("and", 25.8) - 0.1),
        ("chorus", w("its", 29.5) - 0.1),
        ("bobsled", w("just", 36.5) - 0.1),
        ("candy", w("shes", 44.5) - 0.1),
        ("peel", w("and", 48) - 0.1),
        ("chorus2", w("its", 51.5) - 0.1),
        ("run", w("run", 59) - 0.1),
        ("hemiss", w("he", 72.5) - 0.1),
        ("hauling", w("and", 74.5) - 0.1),
        ("goggles", w("hes", 81.5) - 0.1),
        ("surprise", w("and", 85.2) - 0.1),
        ("chorus3", w("its", 89) - 0.1),
        ("merry", w("ahh", 96) - 0.1),
        ("outro", w("christmas", 100.8) - 0.1),
        ("outro2", w("christmas", 108.3) - 0.1),
        ("outro3", w("christmas", 116) - 0.1),
        ("finale", w("christmas", 123) - 0.1),
    ]
    return [(n, t0, t[k + 1][1] if k + 1 < len(t) else c.duration) for k, (n, t0) in enumerate(t)]


MORPH_PEAK = 16  # this tree runs up to 180 Morphs at once: copy its Morphs only where at most 16 overlap


def run(s, scenes):
    for name, t0, t1 in plan(s.cues):
        backdrop(s, t0, t1, peak=MORPH_PEAK)
        fn = scenes.get(name)
        if fn:
            fn(s, t0, t1)


# ---------------------------------------------------------------- the SuperStar pictures

SS_X = 3.0  # the tree's pixels are about three times as tall as they are wide
SS = {  # name -> picture number in the sequence's SuperStar media
    "santa": 165,    # Santa, front on
    "santa2": 149,   # Santa waving
    "family": 332,   # the family reading the Christmas story
    "gym": 157,      # Santa in his gym shorts
    "ride": 411,     # Santa at the wheel of the sleigh
    "sled": 187,     # the hot-rod sleigh: exhaust, stick shift, runners
    "deer": 212,     # a reindeer standing
    "sack": 283,
    "bell": 102,
}
LEAP = (233, 234, 235, 236, 237, 238, 240, 241, 242)  # the reindeer's gallop, frame by frame


def _ss_image(n):
    if _SS["imgs"] is None:
        root = ET.parse(_SS["xsq"]).getroot()
        _SS["imgs"] = {}
        for m in root.find("SequenceMedia"):
            p, d = m.get("path") or "", m.findtext("Data")
            if d and "SUP_" in p and p.rsplit("_", 1)[1][:-4].isdigit():
                _SS["imgs"][int(p.rsplit("_", 1)[1][:-4])] = d
    d = _SS["imgs"][n]
    if isinstance(d, str):
        d = _SS["imgs"][n] = Image.open(io.BytesIO(base64.b64decode(d))).convert("RGBA")
    return d


def ss(s, name, h, flip=False):
    """SuperStar picture `name` (or a picture number), h LEDs tall, aspect corrected. Everything faces right."""
    n = SS.get(name, name)
    key = f"ss_{n}_{h}{'f' if flip else ''}"
    if s._key(key) in s.images:
        return s._key(key)
    im = _ss_image(n)
    bb = im.getbbox()
    im = im.crop(bb) if bb else im
    w = max(1, round(im.width * SS_X * h / im.height))
    im = im.resize((round(im.width * SS_X), im.height), Image.LANCZOS).resize((w, h), Image.LANCZOS)
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return s.image(key, im)


def gallop(s, h, t0, t1, x0, x1, y, *, flip=False, frame=0.1, phase=0, z=Z_PIC):
    """A leaping reindeer galloping from x0 to x1 (x0 == x1: on the spot), one SuperStar frame per `frame` s."""
    keys = [ss(s, n, h, flip) for n in LEAP]
    n = max(1, round((t1 - t0) / frame))
    for k in range(n):
        a, b = t0 + (t1 - t0) * k / n, t0 + (t1 - t0) * (k + 1) / n
        xa, xb = x0 + (x1 - x0) * k / n, x0 + (x1 - x0) * (k + 1) / n
        bob = -1 if (k + phase) % 4 < 2 else 0
        s.pic(keys[(k + phase) % len(keys)], a, b, xa, y + bob, to=(xb, y + bob) if xa != xb else None, z=z)


def zoom(s, key, t0, t1, x0, x1, y, *, smoke=True, z=Z_FRONT):
    """A sleigh racing across (glide) with smoke puffs following its tail."""
    s.glide(key, [(t0, x0, y), (t1, x1, y)], z=z)
    if smoke:
        w = s.size(key)[0]
        step = (x1 - x0) / max(0.1, t1 - t0)
        t = t0
        while t + 0.5 < t1:
            x = x0 + step * (t - t0) - (w / 2 + 3) * (1 if x1 > x0 else -1)
            s.pic(s.emoji("💨", 9, flip=x1 > x0), t, t + 0.5, x, y + s.size(key)[1] / 2 - 4, fade_out=0.3,
                  z=Z_BACK)
            t += 0.12


def arrow(s, w, h, color=ICE):
    def draw(d, im):
        d.polygon([(w / 2, 0), (0, h * 0.45), (w * 0.32, h * 0.45), (w * 0.32, h - 1), (w * 0.68, h - 1),
                   (w * 0.68, h * 0.45), (w - 1, h * 0.45)], fill=tuple(color) + (255,))
    return s.drawn(f"arrow_{w}_{h}", w, h, draw)


def stick(s, h):
    """The four-speed stick shift: a chrome lever with a red knob and the H gate."""
    w = round(h * 0.7)

    def draw(d, im):
        d.rectangle([w * 0.1, h * 0.82, w * 0.9, h - 1], fill=(70, 70, 80, 255))
        d.line([(w / 2, h * 0.82), (w * 0.6, h * 0.3)], fill=(200, 210, 230, 255), width=max(2, w // 7))
        r = w * 0.22
        d.ellipse([w * 0.6 - r, h * 0.3 - 2 * r, w * 0.6 + r, h * 0.3], fill=(230, 0, 30, 255))
    return s.drawn(f"stick_{h}", w, h, draw)


def ski(s, w):
    h = max(4, w // 5)

    def draw(d, im):
        d.line([(0, h - 2), (w - 4, h - 2)], fill=(255, 210, 0, 255), width=2)
        d.arc([w - 8, 0, w - 1, h * 2 - 3], 270, 90, fill=(255, 210, 0, 255), width=2)
    return s.drawn(f"ski_{w}", w, h, draw)


def flag(s, w):
    """A chequered racing flag."""
    h = round(w * 0.7)

    def draw(d, im):
        sq = max(2, w // 6)
        for i in range(0, w, sq):
            for j in range(0, h, sq):
                if (i // sq + j // sq) % 2 == 0:
                    d.rectangle([i, j, i + sq - 1, j + sq - 1], fill=(255, 255, 255, 255))
                else:
                    d.rectangle([i, j, i + sq - 1, j + sq - 1], fill=(40, 40, 40, 255))
    return s.drawn(f"flag_{w}", w, h, draw)


def words_at(s, words, y, scale, t1, colors=SURF, *, x=None, z=Z_WORD):
    """Each (word, time) pops in on its time and stays to t1, laid out on one centred line."""
    keys = [s.word(w, colors[k % len(colors)], scale) for k, (w, _t) in enumerate(words)]
    widths = [s.size(k)[0] for k in keys]
    total = sum(widths) + 2 * scale * (len(keys) - 1)
    cx = s.W / 2 if x is None else x
    left = cx - total / 2
    for key, wd, (_w, t) in zip(keys, widths, words):
        s.show(key, t, t1, left + wd / 2, y, enter="pop", enter_s=0.2, z=z)
        left += wd + 2 * scale


# ================================================================ 140x60 matrix (the garage)

def g_intro(s, t0, t1):
    c = s.cues
    s.show(ss(s, "bell", 44), 0.3, t1 - 0.2, 70, 26, enter="top", enter_s=0.5, exit="fade", exit_s=0.4,
           hits=hits(0.8, 4.2), amp=2)
    for k, h in enumerate(hits(0.3, 4.2)):
        s.ring(h, 70, 40, (GOLD, RED, GREEN)[k % 3], r=30 + 4 * k, dur=0.5, width=2)
    merry, xmas = c.w("merry", 6), c.w("christmas", 7)
    s.show(s.word("MERRY", RED, 2), merry, t1, 26, 30, enter="left", enter_s=0.3, z=Z_WORD)
    s.show(s.word("XMAS", GREEN, 2), xmas, t1, 116, 30, enter="right", enter_s=0.3, z=Z_WORD)
    s.twinkle(t0, t1, (GOLD, WHITE), count=10)


def g_comes(s, t0, t1):
    c = s.cues
    s.show(ss(s, "santa", 50), c.w("comes", t0), t1, 70, 34, enter="pop", hits=c.beats_in(t0 + 1, t1)[::2])
    for k, (w, x, y, col) in enumerate((("this", 24, 20, WHITE), ("time", 24, 36, GOLD), ("each", 116, 20, WHITE),
                                         ("year", 116, 36, GOLD))):
        s.show(s.word(w.upper(), col, 2), c.w(w, t0), t1, x, y, enter="pop", z=Z_WORD)
    s.show(s.emoji("🎄", 14), c.w("year", t0) + 0.3, t1, 116, 52, enter="pop")
    s.show(s.emoji("📅", 14), c.w("year", t0) + 0.3, t1, 24, 52, enter="pop")
    pattern_sweeps(s, t0, t1, XMAS)


def g_north(s, t0, t1):
    c = s.cues
    north, cold = c.w("north", t0), c.w("cold", t0)
    s.show(arrow(s, 24, 34), t0 + 0.2, t1, 24, 32, enter="bottom", enter_s=0.4)
    s.show(s.word("NORTH", ICE, 3), north, t1, 82, 18, enter="pop", z=Z_WORD)
    s.show(s.emoji("🥶", 24), cold, t1, 82, 44, enter="pop")
    s.ring(cold, 82, 44, ICE, r=40, dur=0.8)
    s.snow(t0, t1, count=14, speed=22)


def g_tale(s, t0, t1):
    c = s.cues
    s.show(ss(s, "family", 52), t0 + 0.1, t1, 70, 32, enter="bottom", enter_s=0.4)
    s.show(s.word("TALE", GOLD, 2), c.w("tale", t0), t1, 22, 18, enter="pop", z=Z_WORD)
    s.show(s.word("TOLD", GOLD, 2), c.w("told", t0), t1, 118, 18, enter="pop", z=Z_WORD)
    s.show(s.emoji("📖", 20), c.w("christmas", t0), t1, 22, 42, enter="pop")
    s.show(s.emoji("🎅", 20), c.w("told", t0), t1, 118, 42, enter="pop")
    s.twinkle(t0, t1, (GOLD, WHITE), count=8)


def g_cat(s, t0, t1):
    c = s.cues
    cat, red = c.w("cat", t0), c.w("red", t0)
    s.show(s.word("FAMOUS", GOLD, 2), c.w("famous", t0), t1, 70, 7, enter="pop", z=Z_WORD)
    s.show(ss(s, "santa", 48), cat, t1, 70, 36, enter="pop")
    s.show(s.emoji("😎", 12), cat + 0.4, t1, 70, 21, enter="top", z=Z_FRONT)  # a cool cat
    s.show(s.word("RED", RED, 3), red, t1, 118, 36, enter="pop", z=Z_WORD)
    s.ring(red, 70, 36, RED, r=60, dur=0.9, width=3)
    for k, b in enumerate(c.beats_in(cat, t1)):  # the paparazzi
        s.ring(b, (20, 120, 34, 106)[k % 4], (14, 44, 46, 14)[k % 4], WHITE, r=8, dur=0.25, width=2)


def g_workout(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    s.show(ss(s, "gym", 50), t0 + 0.1, t1, 70, 34, enter="pop", hits=beats, amp=4)
    s.show(s.emoji("🏋️", 24), c.w("working", t0), t1, 24, 36, enter="pop", hits=beats[1::2], amp=4)
    s.show(s.word("WORKING", GOLD, 1), c.w("working", t0), t1, 116, 22, enter="pop", z=Z_WORD)
    s.show(s.word("OUT", GOLD, 2), c.w("out", t0), t1, 116, 34, enter="pop", z=Z_WORD)
    s.show(ss(s, "sled", 18), c.w("sled", t0), t1, 116, 50, enter="right", enter_s=0.3)


def chorus(s, t0, t1, *, sleigh=False):
    c = s.cues
    nicks = [t for w, t, _e in c.words if w == "nick" and t0 <= t < t1]
    s.show(s.word("LITTLE", WHITE, 2), c.w("little", t0), t1, 70, 7, enter="pop", z=Z_WORD)
    s.show(s.word("SAINT NICK", RED, 2), c.w("saint", t0), t1, 70, 52, enter="pop", z=Z_WORD)
    keys = [ss(s, "santa", 34), ss(s, "santa2", 34)]
    beats = c.beats_in(t0 + 0.2, t1)
    if beats:
        s.flash(keys, beats, 22, 30, end=t1)
        s.flash(keys[::-1], beats, 118, 30, end=t1)
    for k, n in enumerate(nicks):
        s.ring(n, 22 if k % 2 == 0 else 118, 30, (RED, GOLD)[k % 2], r=30, dur=0.6)
    if sleigh:
        bars = c.bars_in(t0, t1)
        for k, b in enumerate(bars[::2]):
            r = k % 2 == 0
            zoom(s, ss(s, "ride", 24, flip=not r), b, b + 1.6, -30 if r else 170, 170 if r else -30, 30)
    else:
        s.show(ss(s, "bell", 26), t0 + 0.3, t1, 70, 30, enter="pop", hits=beats[::2], amp=2)
    pattern_sweeps(s, t0, t1, (RED, WHITE))


def g_chorus(s, t0, t1):
    chorus(s, t0, t1)


def g_chorus2(s, t0, t1):
    chorus(s, t0, t1, sleigh=True)


def g_bobsled(s, t0, t1):
    c = s.cues
    sled, stk, four = c.w("bobsled", t0), c.w("toboggan", t0), c.w("four", t0)
    s.show(ss(s, "sled", 34), sled, t1, 62, 36, enter="left", enter_s=0.6,
           hits=c.beats_in(sled + 1, t1)[::2], amp=2)
    s.show(s.word("BOBSLED", GOLD, 2), sled, stk - 0.1, 70, 7, enter="pop", exit="fade", exit_s=0.2, z=Z_WORD)
    s.show(s.word("TOBOGGAN", GOLD, 2), stk, four - 0.1, 70, 7, enter="pop", exit="fade", exit_s=0.2, z=Z_WORD)
    s.show(s.word("FOUR SPEED", WHITE, 2), four, t1, 70, 7, enter="pop", z=Z_WORD)
    s.show(stick(s, 30), c.w("stick", t0), t1, 122, 38, enter="bottom", enter_s=0.3)
    s.ring(c.w("stick", t0), 122, 30, RED, r=20, dur=0.5)


def g_candy(s, t0, t1):
    c = s.cues
    candy, red, ski_t = c.w("candy", t0), c.w("red", t0), c.w("ski", t0)
    s.show(ss(s, "sled", 34), t0, t1, 62, 32, enter=None)
    s.show(s.emoji("🍎", 18), candy, t1, 122, 16, enter="pop", hits=c.beats_in(candy, t1)[::2])
    s.show(s.word("CANDY APPLE", CANDY, 1), candy, t1, 62, 6, enter="pop", z=Z_WORD)
    s.wash(red, red + 0.4, (120, 0, 10), z=1, fade_out=0.4)
    s.ring(red, 62, 32, CANDY, r=70, dur=0.7)
    s.show(ski(s, 40), ski_t, t1, 62, 54, enter="left", enter_s=0.3)
    s.show(s.word("SKI", WHITE, 2), ski_t, t1, 122, 38, enter="pop", z=Z_WORD)


def g_peel(s, t0, t1):
    c = s.cues
    gas, peel = c.w("gas", t0), c.w("peel", t0)
    ride = ss(s, "ride", 36)
    s.show(ride, t0, gas, 40, 32, enter="left", enter_s=0.4, hits=c.beats_in(t0 + 0.5, gas - 0.2), amp=1)
    s.show(s.word("GAS", RED, 3), gas, peel, 104, 14, enter="pop", exit="fade", exit_s=0.2, z=Z_WORD)
    zoom(s, ride, gas, peel, 40, 180, 32)
    s.show(s.word("PEEL", GOLD, 3), peel, t1, 70, 30, enter="pop", z=Z_WORD)
    s.show(flag(s, 18), peel, t1, 20, 30, enter="pop", hits=c.beats_in(peel, t1), amp=2)
    s.show(flag(s, 18), peel, t1, 120, 30, enter="pop", hits=c.beats_in(peel, t1), amp=2)
    for k, b in enumerate(c.beats_in(gas, peel)):
        s.ring(b, 40 + 34 * k, 40, (RED, GOLD)[k % 2], r=12, dur=0.4)


def g_run(s, t0, t1):
    c = s.cues
    runs = [t for w, t, _e in c.words if w == "run" and t0 <= t < t1][::2]  # each "run run reindeer"
    whoa = c.w("whoa", t0)
    for k, r in enumerate(runs):
        end = runs[k + 1] if k + 1 < len(runs) else t1
        if r < whoa < end:
            end = whoa
        s.show(s.word("RUN RUN", RED if k % 2 else GREEN, 2), r, end - 0.05, 70, 7, enter="pop", z=Z_WORD)
        gallop(s, 36, r, end, -20 if k % 2 == 0 else 20, 160 if k % 2 == 0 else 120, 36)
        gallop(s, 30, r + 0.2, end, -50 if k % 2 == 0 else -20, 120 if k % 2 == 0 else 160, 40, phase=4,
               z=Z_PIC - 1)
    s.show(ss(s, "deer", 46), whoa, runs[2] if len(runs) > 2 else t1, 70, 34, enter="pop")
    s.show(s.word("WHOA", GOLD, 2), whoa, runs[2] if len(runs) > 2 else t1, 70, 7, enter="pop", z=Z_WORD)
    for k, h in enumerate(hits(t0, t1)):
        s.ring(h, (30, 110)[k % 2], 36, (GOLD, ICE)[k % 2], r=26, dur=0.4)
    s.snow(t0, t1, count=10, speed=24)


def g_hemiss(s, t0, t1):
    c = s.cues
    words_at(s, [("HE", c.w("he", t0)), ("DON'T", c.w("dont", t0)), ("MISS", c.w("miss", t0))], 20, 2, t1,
             (RED, GREEN, GOLD))
    words_at(s, [("NO", c.w("no", t0)), ("ONE", c.w("one", t0))], 40, 2, t1, (WHITE, RED))
    for h in hits(t0, t1 + 0.2):
        s.ring(h, 70, 30, GOLD, r=50, dur=0.4)


def g_hauling(s, t0, t1):
    c = s.cues
    dozen, rudy, speed = c.w("dozen", t0), c.w("rudy", t0), c.w("frightening", t0)
    s.show(s.word("FRIGHTENING", ICE, 1), speed, dozen - 0.1, 70, 6, enter="pop", exit="fade", exit_s=0.2,
           z=Z_WORD)
    s.show(s.word("SPEED", RED, 2), c.w("speed", t0), dozen - 0.1, 70, 16, enter="pop", exit="fade", exit_s=0.2,
           z=Z_WORD)
    zoom(s, ss(s, "ride", 30), t0, dozen, -30, 170, 36)
    # half a dozen deer galloping on the spot in two rows, Rudy out in front with his nose aglow
    for k in range(6):
        x, y = 20 + 22 * (k % 3) + (8 if k >= 3 else 0), 24 if k < 3 else 44
        gallop(s, 22, dozen + 0.15 * k, t1, x, x, y, phase=k * 2)
    gallop(s, 26, rudy, t1, 118, 118, 34, phase=1, z=Z_FRONT)
    s.show(s.word("RUDY", RED, 2), rudy, t1, 118, 7, enter="pop", z=Z_WORD)
    s.ring(rudy, 128, 28, RED, r=10, dur=0.6)
    s.snow(t0, t1, count=16, speed=30)


def g_goggles(s, t0, t1):
    c = s.cues
    gog, flies = c.w("goggles", t0), c.w("flies", t0)
    s.show(ss(s, "santa", 52), t0 + 0.1, t1, 70, 33, enter="pop")
    s.show(s.emoji("🥽", 20), gog, t1, 70, 22, enter="top", enter_s=0.3, z=Z_FRONT)
    s.show(s.word("GOGGLES", ICE, 1), gog, t1, 22, 12, enter="pop", z=Z_WORD)
    s.show(s.word("FLIES", WHITE, 1), flies, t1, 118, 12, enter="pop", z=Z_WORD)
    s.snow(t0, flies, count=10, speed=20)
    s.snow(flies, t1, count=30, speed=40)
    s.twinkle(flies, t1, (WHITE, ICE), count=30, steps=10)


def g_surprise(s, t0, t1):
    c = s.cues
    sur = c.w("surprise", t0)
    s.show(ss(s, "sack", 44), t0 + 0.1, t1, 70, 36, enter="top", enter_s=0.4,
           hits=c.beats_in(t0 + 0.5, sur), amp=2)
    s.show(s.word("SURPRISE", GOLD, 2), sur, t1, 70, 7, enter="pop", z=Z_WORD)
    for k, b in enumerate(c.beats_in(sur - 0.1, t1)[:4]):
        x = (30, 110, 46, 94)[k]
        s.show(s.emoji("🎁", 16), b, t1, x, 40 - 10 * (k // 2), enter="pop")
        s.ring(b, x, 40 - 10 * (k // 2), GOLD, r=14, dur=0.4)
    s.show(s.word("CRUISING", WHITE, 1), c.w("cruising", t0), sur - 0.1, 70, 7, enter="pop", exit="fade",
           exit_s=0.2, z=Z_WORD)


def g_chorus3(s, t0, t1):
    chorus(s, t0, t1, sleigh=True)


def g_merry(s, t0, t1):
    c = s.cues
    merry = c.w("merry", t0)
    for k, t in enumerate((t0 + 0.1, c.w("ooh", t0))):
        s.ring(t, 70, 30, (ICE, WHITE)[k], r=70, dur=1.6, width=4)
    s.show(ss(s, "santa2", 40), t0 + 0.2, merry, 70, 32, enter="fade", exit="fade", enter_s=0.6, exit_s=0.3)
    words_at(s, [("MERRY", merry), ("XMAS", c.w("christmas", merry))], 18, 2, t1, (RED, GREEN))
    words_at(s, [("SAINT", c.w("saint", merry)), ("NICK", c.w("nick", merry))], 40, 2, t1, (WHITE, GOLD))
    s.twinkle(merry, t1, XMAS, count=20)


def outro(s, t0, t1, k):
    c = s.cues
    merry = c.w("merry", t0 + 1) if any(w == "merry" and t0 < t < t1 for w, t, _e in c.words) else t1
    who = ("santa", "santa2", "gym")[k % 3]
    s.show(ss(s, who, 46), c.w("comes", t0), merry, 30, 34, enter="left", exit="left", exit_s=0.3,
           hits=c.beats_in(t0 + 1, merry)[::2])
    words_at(s, [("CHRISTMAS", t0 + 0.1), ("COMES", c.w("comes", t0))], 14, 1, merry, (RED, GREEN), x=98)
    words_at(s, [("EACH", c.w("each", t0)), ("YEAR", c.w("year", t0) if k < 2 else c.w("each", t0) + 0.35)],
             28, 1, merry, (WHITE, GOLD), x=98)
    s.show(s.emoji("🎁", 14), c.w("each", t0), merry, 98, 48, enter="pop")
    if merry < t1:
        zoom(s, ss(s, "ride", 30, flip=k % 2 == 1), merry, t1, -30 if k % 2 == 0 else 170,
             170 if k % 2 == 0 else -30, 36)
        words_at(s, [("MERRY", merry), ("XMAS", c.w("christmas", merry))], 8, 2, t1, (RED, GREEN))
    pattern_sweeps(s, t0, t1, XMAS)


def g_outro(s, t0, t1):
    outro(s, t0, t1, 0)


def g_outro2(s, t0, t1):
    outro(s, t0, t1, 1)


def g_outro3(s, t0, t1):
    outro(s, t0, t1, 2)


def g_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.1
    ride = ss(s, "ride", 34)
    s.show(ride, t0, c.w("comes", t0), 40, 34, enter="left", enter_s=0.4)
    s.glide(ride, [(c.w("comes", t0), 40, 34), (c.w("year", t0), 160, -10)], z=Z_FRONT)  # up and away
    s.show(s.word("MERRY", RED, 3), c.w("year", t0), end, 70, 18, enter="pop", exit="fade", exit_s=1.5, z=Z_WORD)
    s.show(s.word("XMAS", GREEN, 3), c.w("year", t0) + 0.3, end, 70, 42, enter="pop", exit="fade", exit_s=1.5,
           z=Z_WORD)
    s.twinkle(t0, t1, XMAS, count=25, fade=1.5)
    s.ring(c.w("year", t0), 70, 30, GOLD, r=80, dur=1.4, width=3)


GARAGE = dict(intro=g_intro, comes=g_comes, north=g_north, tale=g_tale, cat=g_cat, workout=g_workout,
              chorus=g_chorus, bobsled=g_bobsled, candy=g_candy, peel=g_peel, chorus2=g_chorus2, run=g_run,
              hemiss=g_hemiss, hauling=g_hauling, goggles=g_goggles, surprise=g_surprise, chorus3=g_chorus3,
              merry=g_merry, outro=g_outro, outro2=g_outro2, outro3=g_outro3, finale=g_finale)


# ================================================================ the two windows as one stage

def wins(s):
    return tuple(s.center(m)[0] for m in s.places)  # the two windows, in --model order


WY = 26


def w_intro(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    s.show(ss(s, "bell", 32), 0.3, t1 - 0.2, L, 21, enter="top", enter_s=0.5, hits=hits(0.8, 4.2), amp=2)
    s.show(ss(s, "bell", 32), 0.5, t1 - 0.2, C, 21, enter="top", enter_s=0.5, hits=hits(0.8, 4.2)[1:], amp=2)
    for k, h in enumerate(hits(0.3, 4.2)):
        s.ring(h, L if k % 2 == 0 else C, WY, (GOLD, RED, GREEN)[k % 3], r=24, dur=0.5, width=2)
    s.show(s.word("MERRY", RED, 1), c.w("merry", 6), t1, L, 44, enter="pop", z=Z_WORD)
    s.show(s.word("XMAS", GREEN, 1), c.w("christmas", 7), t1, C, 44, enter="pop", z=Z_WORD)
    s.twinkle(t0, t1, (GOLD, WHITE), count=8)


def w_comes(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    s.show(ss(s, "santa", 40), c.w("comes", t0), t1, L, WY, enter="pop", hits=c.beats_in(t0 + 1, t1)[::2])
    s.show(s.emoji("📅", 24), c.w("year", t0), t1, C, WY + 4, enter="pop")
    s.show(s.word("EACH", WHITE, 1), c.w("each", t0), t1, C, 6, enter="pop", z=Z_WORD)
    s.show(s.word("YEAR", GOLD, 1), c.w("year", t0), t1, C, 13, enter="pop", z=Z_WORD)
    pattern_sweeps(s, t0, t1, XMAS)


def w_north(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    s.show(arrow(s, 20, 30), t0 + 0.2, t1, L, WY, enter="bottom", enter_s=0.4)
    s.show(s.word("NORTH", ICE, 1), c.w("north", t0), t1, C, 8, enter="pop", z=Z_WORD)
    s.show(s.emoji("🥶", 24), c.w("cold", t0), t1, C, 30, enter="pop")
    s.snow(t0, t1, count=12, speed=22)


def w_tale(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    s.show(ss(s, "family", 42), t0 + 0.1, t1, L, WY, enter="bottom", enter_s=0.4)
    s.show(s.emoji("📖", 24), c.w("christmas", t0), t1, C, WY + 4, enter="pop")
    s.show(s.word("TALE", GOLD, 1), c.w("tale", t0), t1, C, 6, enter="pop", z=Z_WORD)


def w_cat(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    cat, red = c.w("cat", t0), c.w("red", t0)
    s.show(s.word("FAMOUS", GOLD, 1), c.w("famous", t0), t1, L, 6, enter="pop", z=Z_WORD)
    s.show(s.emoji("📸", 22), c.w("famous", t0), t1, L, 28, enter="pop", hits=c.beats_in(cat, t1), amp=2)
    s.show(ss(s, "santa", 40), cat, t1, C, WY, enter="right", enter_s=0.4)
    s.show(s.emoji("😎", 10), cat + 0.5, t1, C, 15, enter="top", z=Z_FRONT)
    for b in c.beats_in(cat, t1):
        s.ring(b, L + 6, 24, WHITE, r=10, dur=0.25, width=2)
    s.ring(red, C, WY, RED, r=30, dur=0.8)


def w_workout(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    s.show(ss(s, "gym", 40), t0 + 0.1, t1, L, WY, enter="pop", hits=beats, amp=4)
    s.show(s.emoji("🏋️", 26), c.w("working", t0), t1, C, WY, enter="pop", hits=beats[1::2], amp=4)
    s.show(s.word("WORK OUT", GOLD, 1), c.w("working", t0), t1, C, 6, enter="pop", z=Z_WORD)


def w_chorus(s, t0, t1, *, sleigh=False):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0 + 0.2, t1)
    keys = [ss(s, "santa", 32), ss(s, "santa2", 32)]
    if beats:
        s.flash(keys, beats, L, 24, end=t1)
        s.flash(keys[::-1], beats, C, 24, end=t1)
    s.show(s.word("LITTLE", WHITE, 1), c.w("little", t0), t1, L, 44, enter="pop", z=Z_WORD)
    s.show(s.word("ST NICK", RED, 1), c.w("saint", t0), t1, C, 44, enter="pop", z=Z_WORD)
    if sleigh:  # the sleigh races from window to window, behind the wall between them
        for k, b in enumerate(c.bars_in(t0, t1)[::2]):
            r = k % 2 == 0
            zoom(s, ss(s, "ride", 20, flip=not r), b, b + 1.4, -24 if r else s.W + 24, s.W + 24 if r else -24, 8)
    pattern_sweeps(s, t0, t1, (RED, WHITE))


def w_chorus2(s, t0, t1):
    w_chorus(s, t0, t1, sleigh=True)


def w_bobsled(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    sled = c.w("bobsled", t0)
    s.show(ss(s, "sled", 26), sled, t1, L, WY, enter="left", enter_s=0.6, hits=c.beats_in(sled + 1, t1)[::2])
    s.show(s.word("BOBSLED", GOLD, 1), sled, t1, L, 6, enter="pop", z=Z_WORD)
    s.show(s.word("FOUR", WHITE, 1), c.w("four", t0), t1, C, 6, enter="pop", z=Z_WORD)
    s.show(stick(s, 30), c.w("stick", t0), t1, C, 28, enter="bottom", enter_s=0.3)
    s.ring(c.w("stick", t0), C, 20, RED, r=20, dur=0.5)


def w_candy(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    candy, red = c.w("candy", t0), c.w("red", t0)
    s.show(ss(s, "sled", 26), t0, t1, L, WY, enter=None)
    s.show(s.emoji("🍎", 26), candy, t1, C, WY, enter="pop", hits=c.beats_in(candy, t1)[::2])
    s.ring(red, C, WY, CANDY, r=30, dur=0.7)
    s.show(ski(s, 34), c.w("ski", t0), t1, L, 42, enter="left", enter_s=0.3)


def w_peel(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    gas, peel = c.w("gas", t0), c.w("peel", t0)
    ride = ss(s, "ride", 30)
    s.show(ride, t0, gas, L, WY, enter="left", enter_s=0.4)
    zoom(s, ride, gas, peel, L, s.W + 30, WY)  # behind the wall and out through the right window
    s.show(s.word("PEEL", GOLD, 2), peel, t1, C, 14, enter="pop", z=Z_WORD)
    s.show(flag(s, 16), peel, t1, L, WY, enter="pop", hits=c.beats_in(peel, t1), amp=2)
    s.show(flag(s, 16), peel, t1, C, 36, enter="pop", hits=c.beats_in(peel, t1), amp=2)


def w_run(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    runs = [t for w, t, _e in c.words if w == "run" and t0 <= t < t1][::2]
    whoa = c.w("whoa", t0)
    for k, r in enumerate(runs):
        end = runs[k + 1] if k + 1 < len(runs) else t1
        if r < whoa < end:
            end = whoa
        a, b = (-20, s.W + 20) if k % 2 == 0 else (-20, s.W + 20)
        gallop(s, 30, r, end, a, b, WY)
        s.show(s.word("RUN", (GREEN, RED)[k % 2], 2), r, end - 0.05, (L, C)[k % 2], 6, enter="pop", z=Z_WORD)
    nxt = runs[2] if len(runs) > 2 else t1
    s.show(ss(s, "deer", 40), whoa, nxt, L, WY, enter="pop")
    s.show(s.word("WHOA", GOLD, 2), whoa, nxt, C, WY, enter="pop", z=Z_WORD)
    for k, h in enumerate(hits(t0, t1)):
        s.ring(h, (L, C)[k % 2], WY, (GOLD, ICE)[k % 2], r=22, dur=0.4)
    s.snow(t0, t1, count=8, speed=24)


def w_hemiss(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    for w, y, col in (("he", 12, RED), ("dont", 22, GREEN), ("miss", 32, GOLD)):
        s.show(s.word(w.upper().replace("DONT", "DON'T"), col, 1), c.w(w, t0), t1, L, y, enter="pop", z=Z_WORD)
    s.show(s.word("NO", WHITE, 2), c.w("no", t0), t1, C, 16, enter="pop", z=Z_WORD)
    s.show(s.word("ONE", RED, 2), c.w("one", t0), t1, C, 32, enter="pop", z=Z_WORD)


def w_hauling(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    dozen, rudy = c.w("dozen", t0), c.w("rudy", t0)
    zoom(s, ss(s, "ride", 24), t0, dozen, -30, s.W + 30, WY)
    for k in range(6):  # three deer in each window
        x = (L, C)[k // 3] - 12 + 12 * (k % 3)
        gallop(s, 18, dozen + 0.15 * k, t1, x, x, 16 + 14 * (k % 2), phase=2 * k)
    gallop(s, 20, rudy, t1, C, C, 40, phase=1, z=Z_FRONT)
    s.ring(rudy, C + 8, 34, RED, r=8, dur=0.6)
    s.snow(t0, t1, count=14, speed=30)


def w_goggles(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    gog, flies = c.w("goggles", t0), c.w("flies", t0)
    s.show(ss(s, "santa", 42), t0 + 0.1, t1, L, WY, enter="pop")
    s.show(s.emoji("🥽", 16), gog, t1, L, 16, enter="top", enter_s=0.3, z=Z_FRONT)
    s.show(s.emoji("🥽", 28), gog, t1, C, WY, enter="pop")
    s.snow(t0, flies, count=10, speed=20)
    s.snow(flies, t1, count=30, speed=40)


def w_surprise(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    sur = c.w("surprise", t0)
    s.show(ss(s, "sack", 38), t0 + 0.1, t1, L, WY, enter="top", enter_s=0.4)
    s.show(s.emoji("🎁", 26), sur, t1, C, WY, enter="pop", hits=c.beats_in(sur + 0.3, t1))
    s.ring(sur, C, WY, GOLD, r=26, dur=0.6)


def w_chorus3(s, t0, t1):
    w_chorus(s, t0, t1, sleigh=True)


def w_merry(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    merry = c.w("merry", t0)
    for k, t in enumerate((t0 + 0.1, c.w("ooh", t0))):
        s.ring(t, (L, C)[k], WY, (ICE, WHITE)[k], r=36, dur=1.6, width=3)
    s.show(s.word("MERRY", RED, 1), merry, t1, L, 18, enter="pop", z=Z_WORD)
    s.show(s.word("XMAS", GREEN, 1), c.w("christmas", merry), t1, L, 30, enter="pop", z=Z_WORD)
    s.show(s.word("SAINT", WHITE, 1), c.w("saint", merry), t1, C, 18, enter="pop", z=Z_WORD)
    s.show(s.word("NICK", GOLD, 1), c.w("nick", merry), t1, C, 30, enter="pop", z=Z_WORD)
    s.twinkle(merry, t1, XMAS, count=15)


def w_outro(s, t0, t1, k):
    c = s.cues
    L, C = wins(s)
    merry = c.w("merry", t0 + 1) if any(w == "merry" and t0 < t < t1 for w, t, _e in c.words) else t1
    who = ("santa", "santa2", "gym")[k % 3]
    s.show(ss(s, who, 40), c.w("comes", t0), merry, L, WY, enter="left", exit="left", exit_s=0.3,
           hits=c.beats_in(t0 + 1, merry)[::2])
    s.show(s.emoji("🎄", 30), c.w("each", t0), merry, C, WY, enter="pop", exit="shrink", exit_s=0.3)
    if merry < t1:
        zoom(s, ss(s, "ride", 24, flip=k % 2 == 1), merry, t1, -30 if k % 2 == 0 else s.W + 30,
             s.W + 30 if k % 2 == 0 else -30, 34)
        s.show(s.word("MERRY", RED, 1), merry, t1, L, 10, enter="pop", z=Z_WORD)
        s.show(s.word("XMAS", GREEN, 1), c.w("christmas", merry), t1, C, 10, enter="pop", z=Z_WORD)
    pattern_sweeps(s, t0, t1, XMAS)


def w_finale(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    end = t1 - 0.1
    ride = ss(s, "ride", 28)
    s.show(ride, t0, c.w("comes", t0), L, 30, enter="left", enter_s=0.4)
    s.glide(ride, [(c.w("comes", t0), L, 30), (c.w("year", t0), C + 30, -14)], z=Z_FRONT)
    s.show(s.word("MERRY", RED, 1), c.w("year", t0), end, L, WY, enter="pop", exit="fade", exit_s=1.5, z=Z_WORD)
    s.show(s.word("XMAS", GREEN, 1), c.w("year", t0) + 0.3, end, C, WY, enter="pop", exit="fade", exit_s=1.5,
           z=Z_WORD)
    s.twinkle(t0, t1, XMAS, count=20, fade=1.5)


WINDOWS = dict(intro=w_intro, comes=w_comes, north=w_north, tale=w_tale, cat=w_cat, workout=w_workout,
               chorus=w_chorus, bobsled=w_bobsled, candy=w_candy, peel=w_peel, chorus2=w_chorus2, run=w_run,
               hemiss=w_hemiss, hauling=w_hauling, goggles=w_goggles, surprise=w_surprise, chorus3=w_chorus3,
               merry=w_merry, outro=lambda s, a, b: w_outro(s, a, b, 0), outro2=lambda s, a, b: w_outro(s, a, b, 1),
               outro3=lambda s, a, b: w_outro(s, a, b, 2), finale=w_finale)


# ================================================================ 200x42 matrix: 8 bushes, 25 px each

def bx(i):
    return 12.5 + 25 * i


BY = 22


def row(s, keys, t0, t1, *, hits=None, enter="pop", stagger=0.06, amp=3, y=BY, only=range(8)):
    for i in only:
        s.show(keys[i % len(keys)], t0 + stagger * i, t1, bx(i), y, enter=enter,
               hits=(hits or [])[i % 2::2], amp=amp)


def spell(s, word, t0, t1, colors, *, first=0, step=0.08, scale=4):
    for i, ch in enumerate(word):
        if ch != " ":
            s.show(s.word(ch, colors[i % len(colors)], scale), t0 + step * i, t1, bx(first + i), BY, enter="pop",
                   z=Z_WORD)


def b_intro(s, t0, t1):
    c = s.cues
    hs = hits(0.3, 4.2)
    for k, h in enumerate(hs[:8]):
        s.show(ss(s, "bell", 34), h, c.w("merry", 6) - 0.05, bx(k), BY, enter="top", enter_s=0.2)
    spell(s, "MERRY", c.w("merry", 6), c.w("christmas", 7), (RED,), first=1)
    spell(s, "XMAS", c.w("christmas", 7), t1, (GREEN,), first=2)
    s.twinkle(t0, t1, (GOLD, WHITE), count=8)


def b_comes(s, t0, t1):
    c = s.cues
    row(s, [ss(s, "santa", 34), ss(s, "santa2", 34)], c.w("comes", t0), t1, hits=c.beats_in(t0 + 1, t1))
    pattern_sweeps(s, t0, t1, XMAS)


def b_north(s, t0, t1):
    c = s.cues
    row(s, [arrow(s, 16, 26)], t0 + 0.2, c.w("north", t0), enter="bottom")
    spell(s, "NORTH", c.w("north", t0), c.w("cold", t0), (ICE,), first=1)
    row(s, [s.emoji("🥶", 22)], c.w("cold", t0), t1)
    s.snow(t0, t1, count=14, speed=22)


def b_tale(s, t0, t1):
    row(s, [ss(s, "family", 36), s.emoji("📖", 20)], t0 + 0.1, t1, enter="bottom")


def b_cat(s, t0, t1):
    c = s.cues
    cat = c.w("cat", t0)
    spell(s, "FAMOUS", c.w("famous", t0), cat, (GOLD,), first=1, scale=3)
    row(s, [ss(s, "santa", 34)], cat, t1, hits=c.beats_in(cat, t1))
    s.ring(c.w("red", t0), 100, BY, RED, r=100, dur=0.8)


def b_workout(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    row(s, [ss(s, "gym", 34), s.emoji("🏋️", 20)], t0 + 0.1, t1, hits=beats, amp=4)


def b_chorus(s, t0, t1, *, sleigh=False):
    c = s.cues
    beats = c.beats_in(t0 + 0.2, t1)
    keys = [ss(s, "santa", 30), ss(s, "santa2", 30)]
    nicks = [t for w, t, _e in c.words if w == "nick" and t0 <= t < t1]
    if beats:
        for i in range(8):
            s.flash(keys if i % 2 else keys[::-1], beats, bx(i), BY, end=t1)
    for k, n in enumerate(nicks):
        s.ring(n, bx((2 * k) % 8), BY, (RED, GOLD)[k % 2], r=40, dur=0.6)
    if sleigh:  # the sleigh races along the bushes in front of the Santas
        for k, b in enumerate(c.bars_in(t0, t1)[::2]):
            r = k % 2 == 0
            zoom(s, ss(s, "ride", 22, flip=not r), b, b + 1.6, -30 if r else 230, 230 if r else -30, 28)
    pattern_sweeps(s, t0, t1, (RED, WHITE))


def b_bobsled(s, t0, t1):
    c = s.cues
    sled, four, stk = c.w("bobsled", t0), c.w("four", t0), c.w("stick", t0)
    sl = ss(s, "sled", 24)
    s.glide(sl, [(sled, -30, BY), (sled + 1.2, 150, BY)], z=Z_PIC)
    s.show(sl, sled + 1.2, t1, 150, BY, enter=None, hits=c.beats_in(sled + 1.5, t1)[::2])
    spell(s, "FOUR", four, t1, (WHITE, GOLD), first=0)
    for i, k in enumerate((4, 7)):
        s.show(stick(s, 28), stk + 0.08 * i, t1, bx(k), BY, enter="bottom", enter_s=0.3)
        s.ring(stk + 0.08 * i, bx(k), BY - 8, RED, r=12, dur=0.4)


def b_candy(s, t0, t1):
    c = s.cues
    candy = c.w("candy", t0)
    row(s, [s.emoji("🍎", 22), ss(s, "sled", 18)], candy, t1, hits=c.beats_in(candy, t1))
    s.wash(c.w("red", t0), c.w("red", t0) + 0.4, (120, 0, 10), z=1, fade_out=0.4)


def b_peel(s, t0, t1):
    c = s.cues
    gas, peel = c.w("gas", t0), c.w("peel", t0)
    ride = ss(s, "ride", 30)
    s.show(ride, t0, gas, 30, BY, enter="left", enter_s=0.4)
    zoom(s, ride, gas, peel, 30, 240, BY)
    row(s, [flag(s, 16)], peel, t1, hits=c.beats_in(peel, t1), amp=2)


def b_run(s, t0, t1):
    c = s.cues
    runs = [t for w, t, _e in c.words if w == "run" and t0 <= t < t1][::2]
    whoa = c.w("whoa", t0)
    for k, r in enumerate(runs):
        end = runs[k + 1] if k + 1 < len(runs) else t1
        if r < whoa < end:
            end = whoa
        for j in range(3):  # a herd galloping the length of the bushes
            gallop(s, 26, r + 0.25 * j, end, -20 - 40 * j, 230 - 40 * j, BY, phase=3 * j)
    nxt = runs[2] if len(runs) > 2 else t1
    row(s, [ss(s, "deer", 34)], whoa, nxt)
    for k, h in enumerate(hits(t0, t1)):
        s.ring(h, bx((k * 3) % 8), BY, (GOLD, ICE)[k % 2], r=20, dur=0.4)
    s.snow(t0, t1, count=8, speed=24)


def b_hemiss(s, t0, t1):
    c = s.cues
    for k, (w, i) in enumerate((("he", 0), ("dont", 1), ("miss", 2), ("no", 5), ("one", 6))):
        t = c.w(w, t0)
        txt = w.upper().replace("DONT", "DON'T")
        s.show(s.word(txt, (RED, GREEN, GOLD, WHITE, RED)[k], 2 if len(txt) <= 3 else 1), t, t1, bx(i), BY,
               enter="pop", z=Z_WORD)
        s.ring(t, bx(i), BY, GOLD, r=14, dur=0.3)


def b_hauling(s, t0, t1):
    c = s.cues
    dozen, rudy = c.w("dozen", t0), c.w("rudy", t0)
    zoom(s, ss(s, "ride", 26), t0, dozen, -30, 230, BY)
    for i in range(6):
        gallop(s, 24, dozen + 0.15 * i, t1, bx(i), bx(i), BY, phase=2 * i)
    gallop(s, 26, rudy, t1, bx(7) - 2, bx(7) - 2, BY, phase=1, z=Z_FRONT)
    s.ring(rudy, bx(7) + 8, BY - 6, RED, r=10, dur=0.6)
    s.snow(t0, t1, count=14, speed=30)


def b_goggles(s, t0, t1):
    c = s.cues
    gog, flies = c.w("goggles", t0), c.w("flies", t0)
    row(s, [ss(s, "santa", 34)], t0 + 0.1, t1)
    for i in range(8):
        s.show(s.emoji("🥽", 12), gog + 0.05 * i, t1, bx(i), 13, enter="top", enter_s=0.3, z=Z_FRONT)
    s.snow(flies, t1, count=30, speed=40)


def b_surprise(s, t0, t1):
    c = s.cues
    sur = c.w("surprise", t0)
    row(s, [ss(s, "sack", 32)], t0 + 0.1, sur, enter="top")
    row(s, [s.emoji("🎁", 22)], sur, t1, hits=c.beats_in(sur + 0.3, t1))


def b_merry(s, t0, t1):
    c = s.cues
    merry = c.w("merry", t0)
    s.ring(t0 + 0.1, 100, BY, ICE, r=110, dur=1.6, width=3)
    s.ring(c.w("ooh", t0), 100, BY, WHITE, r=110, dur=1.6, width=3)
    spell(s, "MERRY", merry, c.w("saint", merry), (RED,), first=1)
    spell(s, "ST NICK", c.w("saint", merry), t1, (WHITE, GOLD), first=0)


def b_outro(s, t0, t1, k):
    c = s.cues
    merry = c.w("merry", t0 + 1) if any(w == "merry" and t0 < t < t1 for w, t, _e in c.words) else t1
    who = ("santa", "santa2", "gym")[k % 3]
    row(s, [ss(s, who, 32), s.emoji("🎄", 26)], c.w("comes", t0), merry, hits=c.beats_in(t0 + 1, merry))
    if merry < t1:
        zoom(s, ss(s, "ride", 26, flip=k % 2 == 1), merry, t1, -30 if k % 2 == 0 else 230,
             230 if k % 2 == 0 else -30, BY)
    pattern_sweeps(s, t0, t1, XMAS)


def b_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.1
    zoom(s, ss(s, "ride", 28), t0, c.w("year", t0), -30, 230, BY)
    spell(s, "MERRY", c.w("year", t0), end, (RED,), first=0)
    s.twinkle(t0, t1, XMAS, count=15, fade=1.5)
    for i in range(5, 8):
        s.show(s.emoji("🎄", 28), c.w("year", t0) + 0.1 * i, end, bx(i), BY, enter="pop", exit="fade", exit_s=1.5)


BUSHES = dict(intro=b_intro, comes=b_comes, north=b_north, tale=b_tale, cat=b_cat, workout=b_workout,
              chorus=b_chorus, bobsled=b_bobsled, candy=b_candy, peel=b_peel,
              chorus2=lambda s, a, b: b_chorus(s, a, b, sleigh=True), run=b_run, hemiss=b_hemiss,
              hauling=b_hauling, goggles=b_goggles, surprise=b_surprise,
              chorus3=lambda s, a, b: b_chorus(s, a, b, sleigh=True), merry=b_merry,
              outro=lambda s, a, b: b_outro(s, a, b, 0), outro2=lambda s, a, b: b_outro(s, a, b, 1),
              outro3=lambda s, a, b: b_outro(s, a, b, 2), finale=b_finale)
