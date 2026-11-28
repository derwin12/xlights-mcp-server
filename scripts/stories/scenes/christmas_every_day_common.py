"""Christmas Every Day matrix scenes, shared plan for the garage, the two windows (one stage) and the bushes.

The MegaTree carries the SuperStar story (CHRISTMAS / EVERYDAY spelled out, the guy in his PJs, the TV, a DEC 25
calendar, the palm tree on holiday, Santa, IN A ROW, a toy soldier, a bunny, presents under a tree); these scenes
follow the same lyric lines on the other matrices. Upbeat pop: pops and hops in Christmas colours. Santa, the guy,
the soldier and the bunny are the sequence's own SuperStar tree pictures (see ss()).
Words: the sequence's "Main Vocals" timing track (word layer); beats and bars: its Beats and Bars tracks.
"""
import html
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
from morph_backdrop import backdrop, pattern_sweeps  # noqa: E402
from matrix_scenes import Cues  # noqa: E402
from rockin_common import (BLUE, GOLD, GREEN, ICE, PINK, PURPLE, RED, WHITE, Z_BACK, Z_FRONT,  # noqa: E402,F401
                           Z_PIC, Z_WORD, mistletoe_img)
from white_christmas_common import light_string, pine  # noqa: E402

WORDS_TRACK, BEATS_TRACK, BARS_TRACK = "Main Vocals", "Beats", "Bars"
XMAS = (RED, GREEN, GOLD, WHITE)

SS_X = 3.0
SS = {  # the sequence's SuperStar tree pictures (media path) -> what they show
    "santa": "ChristmasEveryDay/SUPImages/ChristmasEveryDay_332.png",    # Santa waving
    "guy": "ChristmasEveryDay/SUPImages/ChristmasEveryDay_83.png",       # the guy in his PJs
    "guy_arms": "ChristmasEveryDay/SUPImages/ChristmasEveryDay_84.png",  # arms out
    "soldier": "ChristmasEveryDay/SUPImages/ChristmasEveryDay_397.png",  # toy soldier
    "soldier2": "ChristmasEveryDay/SUPImages/ChristmasEveryDay_151.png",
    "bunny": "ChristmasEveryDay/SUPImages/ChristmasEveryDay_164.png",    # bunny with an egg
    "beach": "ChristmasEveryDay/SUPImages/ChristmasEveryDay_143.png",    # on holiday at the beach
}
_SS = {"xsq": None, "imgs": None}


def cues(xsq):
    _SS["xsq"] = xsq
    root = ET.parse(xsq).getroot()
    words, beats, bars = [], [], []
    for e in root.find("ElementEffects"):
        lays = e.findall("EffectLayer")
        if e.get("name") == WORDS_TRACK and len(lays) > 1:
            words = [(html.unescape(f.get("label")), int(f.get("startTime")) / 1000, int(f.get("endTime")) / 1000)
                     for f in lays[1] if f.get("label")]
        elif e.get("name") == BEATS_TRACK and lays:
            beats = [int(f.get("startTime")) / 1000 for f in lays[0]]
        elif e.get("name") == BARS_TRACK and lays:
            bars = [int(f.get("startTime")) / 1000 for f in lays[0]]
    c = Cues(words, beats, float(root.findtext("head/sequenceDuration")))
    if bars:
        c.bars = bars
    return c


def ss(s, name, h, flip=False):
    """A SuperStar picture h LEDs tall, aspect corrected for the tree's tall pixels."""
    from PIL import Image, ImageOps
    key = f"ced_{name}_{h}{'f' if flip else ''}"
    if s._key(key) in s.images:
        return s._key(key)
    if _SS["imgs"] is None:
        import base64
        import io
        root = ET.parse(_SS["xsq"]).getroot()
        _SS["imgs"] = {m.get("path"): Image.open(io.BytesIO(base64.b64decode(m.findtext("Data")))).convert("RGBA")
                       for m in root.find("SequenceMedia") if m.findtext("Data") and m.get("path") in SS.values()}
    im = _SS["imgs"][SS[name]]
    bb = im.getbbox()
    im = im.crop(bb) if bb else im
    w = max(1, round(im.width * SS_X * h / im.height))
    im = im.resize((round(im.width * SS_X), im.height), Image.LANCZOS).resize((w, h), Image.LANCZOS)
    if flip:
        im = ImageOps.mirror(im)
    return s.image(key, im)


def plan(c):
    w = c.w
    t = [("intro", 0.0)]

    def chorus(t_i, finale=False):
        """Each cue is looked up after the previous one, so the choruses' different spacing doesn't matter."""
        a = w("wish", t_i) - 0.9  # "I wish..."
        t.append(("wish", a))
        a = w("we", a)
        t.append(("snow", a))
        a = w("there", a)
        t.append(("presents", a))
        a = w("oh", a)
        t.append(("santa", a))
        t.append(("finale" if finale else "everyday", w("wish", w("way", a)) - 0.9))

    chorus(6)
    t += [("school", w("school", 44)), ("wonder", w("staring", 50)), ("slippers", w("the", 55.5)),
          ("tv", w("a", 58)), ("kid", w("i", 60.7)), ("lights", w("i", 64.7)), ("welcome", w("welcome", 69))]
    chorus(76)
    t += [("kiss", w("kissing", 101)), ("row", w("fifty", 104)), ("glee", w("now", 107)), ("peace", w("no", 112)),
          ("world", w("what", 117)), ("lights", w("i", 121.4)), ("welcome", w("welcome", 126))]
    chorus(133)
    t.append(("parade", w("christmas", 159.5)))
    chorus(174.5, finale=True)
    return [(n, t0, t[k + 1][1] if k + 1 < len(t) else c.duration) for k, (n, t0) in enumerate(t)]


MORPH_PEAK = 24  # the tree's Morph bursts here stack up to ~190 at once: copying those would need hundreds of layers


def run(s, scenes):
    for name, t0, t1 in plan(s.cues):
        backdrop(s, t0, t1, peak=MORPH_PEAK)
        fn = scenes.get(name)
        if fn:
            fn(s, t0, t1)


def sweeps(s, t0, t1, colors=(RED, GREEN)):
    pattern_sweeps(s, t0, t1, colors)


# ---------------------------------------------------------------- drawn props

DIGITS = {  # 3x5 digits (the pixel word font has none)
    "0": ("111", "101", "101", "101", "111"), "1": ("010", "110", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"), "3": ("111", "001", "011", "001", "111"),
    "4": ("101", "101", "111", "001", "001"), "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"), "7": ("111", "001", "010", "010", "010"),
    "8": ("111", "101", "111", "101", "111"), "9": ("111", "101", "111", "001", "111"),
}


def _digits(d, text, x, y, k, fill):
    for n, ch in enumerate(text):
        for r, rowbits in enumerate(DIGITS[ch]):
            for cc, bit in enumerate(rowbits):
                if bit == "1":
                    d.rectangle([x + (n * 4 + cc) * k, y + r * k, x + (n * 4 + cc) * k + k - 1, y + r * k + k - 1],
                                fill=fill)


def calendar(s, w, num="25", top=(220, 0, 0)):
    """A tear-off calendar page: red header with rings, the day number in big red digits."""
    h = round(w * 1.1)

    def draw(d, im):
        d.rectangle([0, 0, w - 1, h - 1], fill=(245, 245, 245, 255))
        hh = max(4, round(h * 0.24))
        d.rectangle([0, 0, w - 1, hh], fill=top + (255,))
        for x in (w * 0.25, w * 0.75):
            d.rectangle([x - 1, 0, x, 1], fill=(60, 60, 60, 255))
        k = max(1, min((w - 4) // (4 * len(num) - 1), (h - hh - 4) // 5))
        tw, th = (4 * len(num) - 1) * k, 5 * k
        _digits(d, num, (w - tw) // 2, hh + (h - hh - th) // 2 + 1, k, (200, 0, 0, 255))
    return s.drawn(f"cal_{w}_{num}_{top[0]}", w, h, draw)


def tv(s, w, screen=(40, 120, 255)):
    h = round(w * 0.8)

    def draw(d, im):
        d.line([(w * 0.3, 0), (w / 2, h * 0.2)], fill=(180, 180, 180, 255))
        d.line([(w * 0.7, 0), (w / 2, h * 0.2)], fill=(180, 180, 180, 255))
        d.rectangle([0, h * 0.2, w - 1, h * 0.9], fill=(110, 70, 40, 255))
        d.rectangle([2, h * 0.2 + 2, w * 0.78, h * 0.9 - 2], fill=screen + (255,))
        for y in (h * 0.4, h * 0.6):
            d.ellipse([w * 0.84, y, w * 0.84 + 2, y + 2], fill=(220, 200, 120, 255))
        d.rectangle([w * 0.15, h * 0.9, w * 0.25, h - 1], fill=(80, 50, 30, 255))
        d.rectangle([w * 0.75, h * 0.9, w * 0.85, h - 1], fill=(80, 50, 30, 255))
    return s.drawn(f"tv_{w}_{screen[0]}_{screen[2]}", w, h, draw)


def drop_presents(s, t0, t1, x, base_y, px, n=4, every=2, z=Z_PIC):
    """Presents dropping in on every `every`-th beat, stacking up from base_y (the bottom of the pile)."""
    keys = [s.emoji("🎁", px), s.emoji("🎁", px, flip=True)]
    for k, b in enumerate(s.cues.beats_in(t0 + 0.3, t1 - 0.5)[::every][:n]):
        y = base_y - px / 2 - k * (px - 2)
        xx = x + (-3, 3, -1, 2)[k % 4]
        s.pic(keys[k % 2], b, b + 0.25, xx, -px, to=(xx, y), z=z)
        s.pic(keys[k % 2], b + 0.25, t1, xx, y, z=z)


# ================================================================ 140x60 matrix (the garage)

GY = 32


def g_intro(s, t0, t1):
    c = s.cues
    s.twinkle(0.2, t1, (RED, GREEN, GOLD), count=8, steps=40, fade=1.0)
    s.show(s.emoji("🎄", 40), 0.3, t1, 70, 34, enter="fade", enter_s=1.5, exit="shrink", exit_s=0.3)
    beats = c.beats_in(1.5, t1 - 0.3)
    for k, ch in enumerate("XMAS"):
        if k < len(beats):
            x = (22, 40, 100, 118)[k]
            s.show(s.word(ch, XMAS[k], 3), beats[k * 2 % len(beats)], t1, x, 30, enter="pop", z=Z_WORD)


def g_wish(s, t0, t1):
    c = s.cues
    xm = c.w("christmas", t0)
    xm2 = c.w("christmas", xm + 0.5)
    every = c.w("every", t0)
    s.show(s.emoji("🌠", 26), t0, xm, 70, 30, enter="fade", exit="shrink", enter_s=0.4)
    s.show(s.word("I WISH", GOLD, 2), c.w("wish", t0), xm, 70, 8, enter="pop", z=Z_WORD)
    s.show(s.word("CHRISTMAS", RED, 2), xm, t1, 70, 12, enter="pop", z=Z_WORD)
    s.ring(xm, 70, 34, GOLD, r=60, dur=1.0, width=2)
    beats = c.beats_in(xm, t1)
    s.show(s.emoji("🎄", 34), xm, t1, 28, 40, enter="pop", hits=beats[0::2], amp=2)
    s.show(s.emoji("🎁", 26), xm2, t1, 112, 44, enter="pop", hits=beats[1::2], amp=3)
    s.show(s.word("EVERY DAY", GREEN, 2), every, t1, 70, 46, enter="bottom", z=Z_WORD)
    sweeps(s, t0, t1)


def g_snow(s, t0, t1):
    c = s.cues
    let, hol = c.w("let", t0), c.w("holiday", t0)
    s.snow(t0, t1, count=14, speed=8, fade=0.5)
    beats = c.beats_in(t0, t1)
    s.show(s.emoji("⛄", 40), t0, t1, 70, 36, enter="bottom", hits=beats[1::2], amp=2)
    s.show(s.word("LET IT SNOW", WHITE, 2), let, hol, 70, 7, enter="pop", exit="top", z=Z_WORD)
    s.show(s.word("HOLIDAY", GOLD, 2), hol, t1, 70, 7, enter="pop", z=Z_WORD)
    s.show(s.emoji("❄️", 18), let, t1, 18, 30, enter="pop", hits=beats[0::2], amp=2)
    s.show(s.emoji("❄️", 18), let + 0.3, t1, 122, 30, enter="pop", hits=beats[1::2], amp=2)
    s.ring(hol, 70, 30, ICE, r=60, dur=1.0, width=2)


def g_presents(s, t0, t1):
    c = s.cues
    tree_ = c.w("tree", t0)
    s.show(s.word("PRESENTS", RED, 2), c.w("presents", t0), tree_, 70, 7, enter="pop", exit="fade", z=Z_WORD)
    s.show(s.word("MORNING", GOLD, 1), c.w("morning", t0), tree_, 70, 18, enter="pop", exit="fade", z=Z_WORD)
    drop_presents(s, t0, t1, 30, 58, 16, n=3)
    drop_presents(s, t0 + 0.4, t1, 110, 58, 16, n=3)
    s.show(s.emoji("🎄", 44), c.w("under", t0), t1, 70, 36, enter="pop", hits=c.beats_in(tree_, t1)[::2])
    s.ring(tree_, 70, 30, GREEN, r=60, dur=1.0, width=2)
    s.twinkle(tree_, t1, (GOLD, RED, WHITE), count=20, fade=0.4, z=Z_FRONT + 1)


def g_santa(s, t0, t1):
    c = s.cues
    claus, way = c.w("claus", t0), c.w("way", t0)
    s.show(ss(s, "santa", 54), t0, t1, 70, 31, enter="right", enter_s=0.8, hits=c.beats_in(claus, t1)[::2])
    s.show(s.word("SANTA", RED, 2), c.w("santa", t0), t1, 24, 14, enter="pop", z=Z_WORD)
    s.show(s.word("CLAUS", RED, 2), claus, t1, 116, 14, enter="pop", z=Z_WORD)
    s.show(s.word("MY WAY", GOLD, 1), way, t1, 116, 46, enter="pop", z=Z_WORD)
    s.show(s.emoji("🎁", 18), way, t1, 24, 44, enter="pop")
    s.ring(claus, 70, 30, RED, r=60, dur=1.0, width=2)


def g_everyday(s, t0, t1):
    c = s.cues
    xm, day = c.w("christmas", t0), c.w("day", t0)
    s.show(s.word("I WISH IT WAS", WHITE, 1), t0, xm, 70, 8, enter="pop", z=Z_WORD)
    s.show(s.word("CHRISTMAS", RED, 2), xm, t1, 70, 8, enter="pop", z=Z_WORD)
    s.show(s.word("EVERY DAY", GREEN, 2), c.w("every", t0), t1, 70, 52, enter="pop", z=Z_WORD)
    s.show(calendar(s, 26), xm, t1, 70, 31, enter="pop", hits=c.beats_in(day, t1)[::2], amp=2)
    s.ring(day, 70, 31, GOLD, r=60, dur=1.0, width=2)
    # the instrumental: quick SuperStar-style swaps either side of the calendar
    beats = c.beats_in(day + 0.5, t1)
    if beats:
        keys = [s.emoji(e, 24) for e in ("🎄", "🎁", "⛄", "🔔", "⭐")]
        s.flash(keys, beats, 24, 31, end=t1)
        s.flash(keys[2:] + keys[:2], beats, 116, 31, end=t1)
    sweeps(s, t0, t1, (GOLD, RED))


def g_school(s, t0, t1):
    c = s.cues
    out, pj = c.w("out", t0), c.w("pj", t0)
    s.show(s.emoji("🏫", 34), t0, out + 0.6, 40, 34, enter="pop", exit="bottom", exit_s=0.5)
    s.show(s.word("SCHOOL IS OUT", GOLD, 1), t0 + 0.1, pj, 70, 7, enter="pop", exit="fade", z=Z_WORD)
    s.glide(s.emoji("🎒", 18), [(out, 40, 30), (out + 1.2, 150, -10)], z=Z_FRONT)
    beats = c.beats_in(pj, t1)
    s.show(ss(s, "guy", 52), pj - 0.4, t1, 96, 32, enter="right", enter_s=0.4, hits=beats[::2])
    s.show(s.word("PJ", PINK, 3), pj, t1, 40, 30, enter="pop", z=Z_WORD)
    s.show(s.emoji("😴", 16), c.w("stay", t0), t1, 40, 50, enter="pop")


def g_wonder(s, t0, t1):
    c = s.cues
    wl = c.w("wonderland", t0)
    s.snow(t0, t1, count=12, speed=6)
    for k, (x, h) in enumerate(((14, 36), (40, 44), (100, 44), (126, 36))):
        s.show(pine(s, h), t0 + 0.2 * k, t1, x, 58 - h / 2, enter="fade", enter_s=0.6, z=Z_BACK)
    s.show(s.emoji("⛄", 30), wl, t1, 70, 42, enter="pop")
    s.show(s.word("WINTER", ICE, 2), c.w("winter", t0), t1, 70, 7, enter="pop", z=Z_WORD)
    s.show(s.word("WONDERLAND", WHITE, 1), wl, t1, 70, 19, enter="pop", z=Z_WORD)


def g_slippers(s, t0, t1):
    c = s.cues
    beats = c.beats_in(c.w("slippers", t0), t1)
    deer = s.emoji("🦌", 22)
    s.show(deer, c.w("reindeer", t0), t1, 52, 46, enter="pop", hits=beats[0::2], amp=4)
    s.show(s.emoji("🦌", 22, flip=True), c.w("reindeer", t0) + 0.2, t1, 88, 46, enter="pop", hits=beats[1::2],
           amp=4)
    s.show(s.word("SLIPPERS", RED, 2), c.w("slippers", t0), t1, 70, 10, enter="pop", z=Z_WORD)


def g_tv(s, t0, t1):
    c = s.cues
    keys = [tv(s, 50, col) for col in ((40, 120, 255), (230, 0, 0), (0, 200, 40), (255, 190, 0))]
    beats = c.beats_in(t0 + 0.4, t1)
    s.pic(keys[0], t0, t0 + 0.4, 70, 34, scale=(10, 100))
    if beats:
        s.flash(keys, beats, 70, 34, end=t1)
    s.show(s.word("VACATION", GOLD, 1), c.w("vacation", t0), t1, 70, 6, enter="pop", z=Z_WORD)


def g_kid(s, t0, t1):
    c = s.cues
    kid = c.w("kid", t0)
    beats = c.beats_in(kid, t1)
    s.show(s.emoji("🧒", 36), t0 + 0.2, t1, 70, 36, enter="bottom", hits=beats, amp=3)
    s.show(s.word("KID", GOLD, 3), kid, t1, 26, 30, enter="pop", z=Z_WORD)
    s.show(s.word("AGAIN", GREEN, 2), c.w("again", t0), t1, 114, 30, enter="pop", z=Z_WORD)
    s.show(s.emoji("🎈", 16), kid, t1, 100, 12, enter="bottom")


def g_lights(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    lights = c.w("lights", t0)
    for row, y in enumerate((14, 34, 52)):
        keys = [light_string(s, 132, p) for p in range(5)]
        start = t0 + 0.3 * row
        s.pic(keys[0], start, start + 0.4, 70, y, fade_in=0.3)
        b = [t for t in beats if t > start + 0.4]
        if b:
            s.flash(keys[row:] + keys[:row], b, 70, y, end=t1)
    s.show(s.word("LIGHTS", GOLD, 2), lights, t1, 70, 24, enter="pop", z=Z_WORD)
    s.ring(lights, 70, 24, GOLD, r=60, dur=1.0, width=2)


def g_welcome(s, t0, t1):
    c = s.cues
    best, year = c.w("best", t0), c.w("year", t0)
    s.show(s.word("WELCOME", WHITE, 2), t0, best, 70, 30, enter="pop", exit="fade", z=Z_WORD)
    s.show(s.word("BEST TIME", GOLD, 2), best, t1, 70, 20, enter="pop", z=Z_WORD)
    s.show(s.word("OF THE YEAR", RED, 2), year, t1, 70, 40, enter="pop", z=Z_WORD)
    for k, b in enumerate(c.beats_in(year, t1)):
        x, y = (24, 116, 44, 96)[k % 4], (12, 14, 52, 50)[k % 4]
        s.ring(b, x, y, XMAS[k % 4], r=18, dur=0.5, width=2)
        s.pic(s.emoji("🎆", 18), b, b + 0.5, x, y, fade_out=0.3, z=Z_FRONT)


def g_kiss(s, t0, t1):
    c = s.cues
    ml = c.w("mistletoe", t0)
    s.show(mistletoe_img(s, 24, 26), t0, t1, 70, 13, enter="top")
    s.show(s.emoji("🙂", 24), t0 + 0.2, t1, 52, 42, enter="left")
    s.show(s.emoji("🙂", 24, flip=True), t0 + 0.2, t1, 88, 42, enter="right")
    s.pic(s.emoji("💋", 14), ml, t1, 70, 36, scale=(20, 100), z=Z_FRONT)
    s.ring(ml, 70, 36, PINK, r=40, dur=0.8, width=2)
    s.show(s.word("KISS", PINK, 2), c.w("kissing", t0), t1, 22, 20, enter="pop", z=Z_WORD)


def g_row(s, t0, t1):
    """Fifty-two weeks in a row: the calendar's pages flip faster and faster, week 1 to 52."""
    c = s.cues
    n = 14
    nums = [str(round(1 + (52 - 1) * (k / (n - 1)) ** 1.4)) for k in range(n)]
    span = max(0.8, c.w("row", t0) + 0.2 - t0)
    times = [t0 + span * (k / n) ** 0.7 for k in range(n)]
    keys = [calendar(s, 30, num, top=(0, 150, 50)) for num in nums]
    s.flash(keys, times, 34, 32, end=t1)
    s.show(s.word("IN A ROW", GOLD, 2), c.w("in", t0), t1, 100, 32, enter="pop", z=Z_WORD)


def g_glee(s, t0, t1):
    c = s.cues
    sh = c.w("shouting", t0)
    beats = c.beats_in(sh, t1)
    s.show(s.emoji("📣", 30), sh - 0.2, t1, 36, 32, enter="left", hits=beats, amp=2)
    s.show(s.word("GLEE", GOLD, 3), c.w("glee", t0), t1, 100, 30, enter="pop", z=Z_WORD)
    for k, b in enumerate(beats):
        s.ring(b, 52, 32, XMAS[k % 4], r=30, dur=0.5, width=2)
    s.show(s.emoji("😄", 22), t0, t1, 100, 12, enter="pop")


def g_peace(s, t0, t1):
    c = s.cues
    peace = c.w("peace", t0)
    s.show(s.word("NO MORE WARS", WHITE, 1), t0, peace, 70, 30, enter="pop", exit="fade", z=Z_WORD)
    s.show(s.emoji("☮️", 34), peace, t1, 70, 30, enter="pop", hits=c.beats_in(peace, t1)[::2])
    s.glide(s.emoji("🕊️", 20), [(peace, -12, 14), (t1, 152, 10)], z=Z_FRONT)
    s.show(s.word("PEACE", ICE, 2), peace, t1, 22, 48, enter="pop", z=Z_WORD)
    s.show(s.word("ON EARTH", GREEN, 1), c.w("earth", t0), t1, 114, 48, enter="pop", z=Z_WORD)
    s.ring(peace, 70, 30, WHITE, r=60, dur=1.2, width=2)


def g_world(s, t0, t1):
    c = s.cues
    wo = c.w("world", t0)
    s.show(s.emoji("🌍", 40), t0 + 0.2, t1, 70, 32, enter="pop", hits=c.beats_in(wo, t1)[::2])
    s.show(s.word("WONDERFUL", GOLD, 1), c.w("wonderful", t0), t1, 24, 30, enter="pop", z=Z_WORD)
    s.show(s.word("WORLD", GREEN, 2), wo, t1, 116, 30, enter="pop", z=Z_WORD)
    s.twinkle(t0, t1, (WHITE, GOLD, ICE), count=20, fade=0.5)


def g_parade(s, t0, t1):
    """Christmas every day, then the instrumental: the toy soldier marches, the bunny hops, presents pile up."""
    c = s.cues
    day = c.w("day", t0)
    s.show(s.word("CHRISTMAS", RED, 2), t0, day + 1.0, 70, 10, enter="pop", exit="fade", z=Z_WORD)
    s.show(s.word("EVERY DAY", GREEN, 2), c.w("every", t0), day + 1.0, 70, 24, enter="pop", exit="fade", z=Z_WORD)
    beats = c.beats_in(day + 1.0, t1)
    if not beats:
        return
    march = [ss(s, "soldier", 44), ss(s, "soldier2", 44)]
    mid = beats[len(beats) // 2]
    # the soldier marches across, stepping on every beat
    for k, (a, b) in enumerate(zip(beats, beats[1:] + [t1])):
        x = -14 + (154 * (a - beats[0]) / max(0.1, t1 - beats[0]))
        x2 = -14 + (154 * (b - beats[0]) / max(0.1, t1 - beats[0]))
        s.pic(march[k % 2], a, b, x, 36, to=(x2, 36))
    s.show(ss(s, "bunny", 30), mid, t1, 112, 44, enter="pop", hits=c.beats_in(mid, t1), amp=5)
    drop_presents(s, beats[0], t1, 24, 58, 16, n=3, every=4)
    s.twinkle(beats[0], t1, XMAS, count=12, fade=0.5)
    sweeps(s, t0, t1, (GOLD, GREEN))


def g_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.3
    xs = [c.w("christmas", t0 + 0.5 + k * 3.3) for k in range(3)]
    day = c.w("day", xs[-1])
    for k, (x0, col) in enumerate(zip(xs, (RED, GREEN, GOLD))):
        s.show(s.word("CHRISTMAS", col, 1 if k < 2 else 2), x0, end, 70, (8, 18, 30)[k], enter="pop", exit="fade",
               exit_s=2.5, z=Z_WORD)
        s.ring(x0, 70, (8, 18, 30)[k], col, r=60, dur=1.0, width=2)
    s.show(s.word("EVERY DAY", WHITE, 2), c.w("every", xs[-1]), end, 70, 44, enter="pop", exit="fade", exit_s=2.5,
           z=Z_WORD)
    beats = c.beats_in(day, end - 2.5)
    s.show(s.emoji("🎄", 32), xs[0], end, 16, 40, enter="left", exit="fade", exit_s=2.5, hits=beats[0::2])
    s.show(ss(s, "santa", 40), xs[1], end, 125, 38, enter="right", exit="fade", exit_s=2.5, hits=beats[1::2])
    s.twinkle(day, t1, XMAS, count=20, fade=2.5)
    s.snow(day, t1, count=8, speed=5, fade=2.5)


GARAGE = dict(intro=g_intro, wish=g_wish, snow=g_snow, presents=g_presents, santa=g_santa, everyday=g_everyday,
              school=g_school, wonder=g_wonder, slippers=g_slippers, tv=g_tv, kid=g_kid, lights=g_lights,
              welcome=g_welcome, kiss=g_kiss, row=g_row, glee=g_glee, peace=g_peace, world=g_world,
              parade=g_parade, finale=g_finale)


# ================================================================ the two windows as one stage

def wins(s):
    return tuple(s.center(m)[0] for m in s.places)  # the two windows, in --model order


WY = 26


def w_intro(s, t0, t1):
    L, C = wins(s)
    s.twinkle(0.2, t1, (RED, GREEN, GOLD), count=6, fade=1.0)
    s.show(s.emoji("🎄", 34), 0.3, t1, L, WY, enter="fade", enter_s=1.5)
    s.show(s.emoji("🎁", 26), 2.0, t1, C, 30, enter="pop")


def w_wish(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    xm = c.w("christmas", t0)
    beats = c.beats_in(xm, t1)
    s.show(s.emoji("🌠", 24), t0, xm, L, WY, enter="fade", exit="shrink")
    s.show(s.word("WISH", GOLD, 2), c.w("wish", t0), xm, C, WY, enter="pop", z=Z_WORD)
    s.show(s.emoji("🎄", 34), xm, t1, L, 28, enter="pop", hits=beats[0::2])
    s.show(s.word("XMAS", RED, 2), xm, t1, C, 12, enter="pop", z=Z_WORD)
    s.show(s.word("EVERY", GREEN, 1), c.w("every", t0), t1, C, 30, enter="pop", z=Z_WORD)
    s.show(s.word("DAY", GREEN, 2), c.w("day", t0), t1, C, 40, enter="pop", z=Z_WORD)
    s.ring(xm, L, 28, GOLD, r=30, dur=1.0, width=2)
    sweeps(s, t0, t1)


def w_snow(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    s.snow(t0, t1, count=12, speed=8)
    s.show(s.emoji("⛄", 34), t0, t1, L, 28, enter="bottom", hits=beats[0::2])
    s.show(s.emoji("☃️", 34), t0 + 0.3, t1, C, 28, enter="bottom", hits=beats[1::2])
    s.show(s.word("SNOW", WHITE, 2), c.w("snow", t0), c.w("holiday", t0), C, 6, enter="pop", exit="top", z=Z_WORD)
    s.ring(c.w("holiday", t0), L, 28, ICE, r=30, dur=1.0, width=2)


def w_presents(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    tree_ = c.w("tree", t0)
    s.show(s.emoji("🎄", 40), c.w("under", t0) - 0.5, t1, L, 26, enter="pop", hits=c.beats_in(tree_, t1)[::2])
    drop_presents(s, t0, t1, C, 47, 15, n=3)
    s.twinkle(tree_, t1, (GOLD, RED, WHITE), count=15, fade=0.4, z=Z_FRONT + 1)


def w_santa(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    claus = c.w("claus", t0)
    # Santa comes in on the right, goes behind the wall and steps out in the left window
    sk = ss(s, "santa", 44)
    s.glide(sk, [(t0, s.W + 20, 25), (t0 + 1.2, C, 25), (claus, C, 25)])
    s.show(sk, claus, t1, C, 25, enter=None, hits=c.beats_in(claus, t1)[::2])
    s.show(s.word("HO HO", RED, 1), claus, t1, L, 16, enter="pop", z=Z_WORD)
    s.show(s.emoji("🎁", 20), c.w("way", t0), t1, L, 34, enter="pop")


def w_everyday(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    xm, day = c.w("christmas", t0), c.w("day", t0)
    s.show(calendar(s, 30), xm, t1, L, WY, enter="pop", hits=c.beats_in(day, t1)[::2])
    s.show(s.word("EVERY", GREEN, 1), c.w("every", t0), day + 1.0, C, 18, enter="pop", exit="fade", z=Z_WORD)
    s.show(s.word("DAY", GREEN, 2), day, day + 1.0, C, 30, enter="pop", exit="fade", z=Z_WORD)
    beats = c.beats_in(day + 1.0, t1)
    if beats:
        keys = [s.emoji(e, 28) for e in ("🎄", "🎁", "⛄", "🔔", "⭐")]
        s.flash(keys, beats, C, WY, end=t1)
    sweeps(s, t0, t1, (GOLD, RED))


def w_school(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    out, pj = c.w("out", t0), c.w("pj", t0)
    s.show(s.emoji("🏫", 30), t0, out + 0.6, L, 28, enter="pop", exit="bottom")
    s.glide(s.emoji("🎒", 16), [(out, L, 22), (out + 1.4, s.W + 12, -10)], z=Z_FRONT)
    s.show(ss(s, "guy", 44), pj - 0.4, t1, C, 25, enter="right", hits=c.beats_in(pj, t1)[::2])
    s.show(s.word("PJ", PINK, 3), pj, t1, L, 24, enter="pop", z=Z_WORD)


def w_wonder(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    s.snow(t0, t1, count=12, speed=6)
    s.show(pine(s, 40), t0, t1, L, 27, enter="fade", enter_s=0.6, z=Z_BACK)
    s.show(s.emoji("⛄", 30), c.w("wonderland", t0), t1, C, 30, enter="pop")


def w_slippers(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(c.w("slippers", t0), t1)
    s.show(s.emoji("🦌", 26), c.w("reindeer", t0), t1, L, 32, enter="pop", hits=beats[0::2], amp=4)
    s.show(s.emoji("🦌", 26, flip=True), c.w("reindeer", t0) + 0.2, t1, C, 32, enter="pop", hits=beats[1::2], amp=4)


def w_tv(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    keys = [tv(s, 36, col) for col in ((40, 120, 255), (230, 0, 0), (0, 200, 40), (255, 190, 0))]
    beats = c.beats_in(t0 + 0.3, t1)
    s.pic(keys[0], t0, t0 + 0.3, C, 26, scale=(10, 100))
    if beats:
        s.flash(keys, beats, C, 26, end=t1)
    s.show(ss(s, "guy", 40), t0, t1, L, 26, enter=None)


def w_kid(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    kid = c.w("kid", t0)
    s.show(s.emoji("🧒", 32), t0 + 0.2, t1, L, 28, enter="bottom", hits=c.beats_in(kid, t1), amp=3)
    s.show(s.word("KID", GOLD, 3), kid, t1, C, 24, enter="pop", z=Z_WORD)


def w_lights(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    for row, y in enumerate((10, 24, 38)):
        keys = [light_string(s, s.W - 4, p) for p in range(5)]  # one string across both windows
        start = t0 + 0.3 * row
        s.pic(keys[0], start, start + 0.4, s.W / 2, y, fade_in=0.3)
        b = [t for t in beats if t > start + 0.4]
        if b:
            s.flash(keys[row:] + keys[:row], b, s.W / 2, y, end=t1)


def w_welcome(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    best, year = c.w("best", t0), c.w("year", t0)
    s.show(s.word("BEST", GOLD, 2), best, t1, L, 18, enter="pop", z=Z_WORD)
    s.show(s.word("TIME", GOLD, 2), c.w("time", best), t1, L, 32, enter="pop", z=Z_WORD)
    s.show(s.word("YEAR", RED, 2), year, t1, C, 24, enter="pop", z=Z_WORD)
    for k, b in enumerate(c.beats_in(t0, t1)):
        x = (L, C)[k % 2]
        s.ring(b, x, (10, 40)[k // 2 % 2], XMAS[k % 4], r=14, dur=0.5, width=2)


def w_kiss(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    ml = c.w("mistletoe", t0)
    s.show(mistletoe_img(s, 20, 22), t0, t1, L, 12, enter="top")
    s.show(mistletoe_img(s, 20, 22), t0, t1, C, 12, enter="top")
    s.show(s.emoji("🙂", 22), t0 + 0.2, t1, L, 34, enter="left")
    s.show(s.emoji("🙂", 22, flip=True), t0 + 0.2, t1, C, 34, enter="right")
    # a kiss blown over the wall
    s.glide(s.emoji("💋", 12), [(ml, L + 8, 30), (ml + 1.2, C - 8, 30)], z=Z_FRONT)


def w_row(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    n = 14
    nums = [str(round(1 + 51 * (k / (n - 1)) ** 1.4)) for k in range(n)]
    span = max(0.8, c.w("row", t0) + 0.2 - t0)
    times = [t0 + span * (k / n) ** 0.7 for k in range(n)]
    s.flash([calendar(s, 30, num, top=(0, 150, 50)) for num in nums], times, L, WY, end=t1)
    s.show(s.word("IN A", GOLD, 1), c.w("in", t0), t1, C, 18, enter="pop", z=Z_WORD)
    s.show(s.word("ROW", GOLD, 2), c.w("row", t0), t1, C, 30, enter="pop", z=Z_WORD)


def w_glee(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    sh = c.w("shouting", t0)
    beats = c.beats_in(sh, t1)
    s.show(s.emoji("📣", 28), sh - 0.2, t1, L, WY, enter="left", hits=beats)
    s.show(s.emoji("😄", 30), t0, t1, C, WY, enter="pop", hits=beats[1::2])
    for k, b in enumerate(beats):
        s.ring(b, L, WY, XMAS[k % 4], r=24, dur=0.5, width=2)


def w_peace(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    peace = c.w("peace", t0)
    s.show(s.emoji("☮️", 30), peace, t1, L, WY, enter="pop", hits=c.beats_in(peace, t1)[::2])
    s.show(s.emoji("🌍", 30), c.w("earth", t0), t1, C, WY, enter="pop")
    s.glide(s.emoji("🕊️", 18), [(t0, -12, 12), (peace + 2.5, s.W + 12, 8)], z=Z_FRONT)


def w_world(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    wo = c.w("world", t0)
    s.show(s.emoji("🌍", 34), t0, t1, L, WY, enter="pop", hits=c.beats_in(wo, t1)[::2])
    s.show(s.word("WORLD", GREEN, 1), wo, t1, C, WY, enter="pop", z=Z_WORD)
    s.twinkle(t0, t1, (WHITE, GOLD, ICE), count=15, fade=0.5)


def w_parade(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    day = c.w("day", t0)
    s.show(calendar(s, 30), t0, day + 1.0, L, WY, enter="pop", exit="fade")
    beats = c.beats_in(day + 1.0, t1)
    if not beats:
        return
    march = [ss(s, "soldier", 38), ss(s, "soldier2", 38)]
    # the soldier marches from the left window, behind the wall, into the right one
    for k, (a, b) in enumerate(zip(beats, beats[1:] + [t1])):
        x = -12 + (s.W + 24) * (a - beats[0]) / max(0.1, t1 - beats[0])
        x2 = -12 + (s.W + 24) * (b - beats[0]) / max(0.1, t1 - beats[0])
        s.pic(march[k % 2], a, b, x, 28, to=(x2, 28))
    s.twinkle(beats[0], t1, XMAS, count=10, fade=0.5)


def w_finale(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    end = t1 - 0.3
    x0 = c.w("christmas", t0 + 0.5)
    x1 = c.w("christmas", x0 + 2.5)
    day = c.w("day", x1 + 2.5)
    s.show(s.emoji("🎄", 38), x0, end, L, 26, enter="pop", exit="fade", exit_s=2.5,
           hits=c.beats_in(day, end - 2.5)[0::2])
    s.show(ss(s, "santa", 42), x1, end, C, 25, enter="right", exit="fade", exit_s=2.5,
           hits=c.beats_in(day, end - 2.5)[1::2])
    s.twinkle(day, t1, XMAS, count=15, fade=2.5)
    s.snow(day, t1, count=8, speed=5, fade=2.5)


WINDOWS = dict(intro=w_intro, wish=w_wish, snow=w_snow, presents=w_presents, santa=w_santa, everyday=w_everyday,
               school=w_school, wonder=w_wonder, slippers=w_slippers, tv=w_tv, kid=w_kid, lights=w_lights,
               welcome=w_welcome, kiss=w_kiss, row=w_row, glee=w_glee, peace=w_peace, world=w_world,
               parade=w_parade, finale=w_finale)


# ================================================================ 200x42 matrix: 8 bushes, 25 px each

def bx(i):
    return 12.5 + 25 * i


BY = 22


def row(s, keys, t0, t1, *, hits=None, enter="pop", stagger=0.06, amp=3, y=BY, z=Z_PIC, **kw):
    for i in range(8):
        h = hits[i % 2::2] if hits else ()
        s.show(keys[i % len(keys)], t0 + stagger * i, t1, bx(i), y, enter=enter, hits=h, amp=amp, z=z, **kw)


def letters(s, text, t0, t1, colors, scale=4, gap=0.08, **kw):
    """One letter per bush (the tree spells words the same way)."""
    pad = (8 - len(text)) // 2
    for i, ch in enumerate(text):
        if ch != " ":
            s.show(s.word(ch, colors[i % len(colors)], scale), t0 + gap * i, t1, bx(pad + i), BY, enter="pop",
                   z=Z_WORD, **kw)


def b_intro(s, t0, t1):
    c = s.cues
    s.twinkle(0.2, t1, (RED, GREEN, GOLD), count=5, fade=1.0)
    beats = c.beats_in(0.5, t1)
    tree = s.emoji("🎄", 26)
    for i in range(8):
        b = beats[min(i, len(beats) - 1)]
        s.show(tree, b, t1, bx(i), BY, enter="pop", enter_s=0.2)


def b_wish(s, t0, t1):
    c = s.cues
    xm = c.w("christmas", t0)
    s.show(s.emoji("🌠", 22), t0, xm, 100, BY, enter="fade", exit="shrink")
    letters(s, "XMAS", xm, c.w("every", t0), (RED, GREEN))
    row(s, [s.emoji("🎄", 26), s.emoji("🎁", 22)], c.w("every", t0), t1, hits=c.beats_in(xm, t1))


def b_snow(s, t0, t1):
    c = s.cues
    s.snow(t0, t1, count=10, speed=8)
    row(s, [s.emoji("⛄", 26), s.emoji("❄️", 20)], t0, t1, hits=c.beats_in(t0, t1), enter="bottom")


def b_presents(s, t0, t1):
    c = s.cues
    tree_ = c.w("tree", t0)
    beats = c.beats_in(t0 + 0.3, tree_)
    gift = [s.emoji("🎁", 20), s.emoji("🎁", 20, flip=True)]
    for i in range(8):
        b = beats[i % max(1, len(beats))] if beats else t0
        s.pic(gift[i % 2], b, b + 0.25, bx(i), -12, to=(bx(i), BY))
        s.pic(gift[i % 2], b + 0.25, tree_, bx(i), BY)
    row(s, [s.emoji("🎄", 30)], tree_, t1, hits=c.beats_in(tree_, t1))
    s.twinkle(tree_, t1, (GOLD, RED, WHITE), count=12, fade=0.4, z=Z_FRONT + 1)


def b_santa(s, t0, t1):
    c = s.cues
    claus = c.w("claus", t0)
    row(s, [ss(s, "santa", 34)], claus, t1, hits=c.beats_in(claus, t1), stagger=0.1)
    s.show(s.word("HO HO HO", RED, 2), t0, claus, 100, BY, enter="pop", exit="fade", z=Z_WORD)


def b_everyday(s, t0, t1):
    c = s.cues
    xm, day = c.w("christmas", t0), c.w("day", t0)
    letters(s, "XMAS", xm, day + 1.0, (RED, GREEN), exit="fade")
    beats = c.beats_in(day + 1.0, t1)
    keys = [s.emoji(e, 22) for e in ("🎄", "🎁", "⛄", "🔔", "⭐")]
    for i in range(8):
        if beats:
            s.flash(keys[i % 5:] + keys[:i % 5], beats, bx(i), BY, end=t1)
    sweeps(s, t0, t1, (GOLD, RED))


def b_school(s, t0, t1):
    c = s.cues
    pj = c.w("pj", t0)
    row(s, [s.emoji("🎒", 20)], t0, pj, exit="top")
    row(s, [ss(s, "guy", 36), ss(s, "guy_arms", 36)], pj, t1, hits=c.beats_in(pj, t1), stagger=0.1)


def b_wonder(s, t0, t1):
    s.snow(t0, t1, count=10, speed=6)
    row(s, [pine(s, 36), s.emoji("⛄", 26)], t0, t1, enter="fade", enter_s=0.5)


def b_slippers(s, t0, t1):
    c = s.cues
    row(s, [s.emoji("🦌", 22), s.emoji("🦌", 22, flip=True)], c.w("reindeer", t0), t1,
        hits=c.beats_in(c.w("slippers", t0), t1), amp=4)


def b_tv(s, t0, t1):
    c = s.cues
    keys = [tv(s, 24, col) for col in ((40, 120, 255), (230, 0, 0), (0, 200, 40), (255, 190, 0))]
    beats = c.beats_in(t0 + 0.3, t1)
    for i in range(8):
        s.pic(keys[i % 4], t0 + 0.03 * i, t0 + 0.3, bx(i), BY, scale=(10, 100))
        if beats:
            s.flash(keys[i % 4:] + keys[:i % 4], beats, bx(i), BY, end=t1)


def b_kid(s, t0, t1):
    c = s.cues
    row(s, [s.emoji("🧒", 26), s.emoji("🎈", 22)], t0 + 0.2, t1, hits=c.beats_in(c.w("kid", t0), t1))


def b_lights(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    for row_, y in enumerate((10, 26)):
        keys = [light_string(s, 196, p) for p in range(5)]
        start = t0 + 0.3 * row_
        s.pic(keys[0], start, start + 0.4, 100, y, fade_in=0.3)
        b = [t for t in beats if t > start + 0.4]
        if b:
            s.flash(keys[row_:] + keys[:row_], b, 100, y, end=t1)


def b_welcome(s, t0, t1):
    c = s.cues
    year = c.w("year", t0)
    letters(s, "BEST", c.w("best", t0), year, (GOLD,), exit="fade")
    letters(s, "YEAR", year, t1, (RED, GREEN))
    for k, b in enumerate(c.beats_in(t0, t1)):
        s.ring(b, bx((k * 3) % 8), BY, XMAS[k % 4], r=14, dur=0.5, width=2)


def b_kiss(s, t0, t1):
    c = s.cues
    ml = c.w("mistletoe", t0)
    row(s, [mistletoe_img(s, 20, 22)], t0, t1, enter="top", y=11)
    row(s, [s.emoji("💋", 16)], ml, t1, hits=c.beats_in(ml, t1), y=32, z=Z_FRONT)


def b_row(s, t0, t1):
    """Every bush is a calendar, the pages flipping through the weeks, offset bush to bush."""
    c = s.cues
    n = 10
    nums = [str(round(1 + 51 * (k / (n - 1)))) for k in range(n)]
    keys = [calendar(s, 20, num, top=(0, 150, 50)) for num in nums]
    span = max(0.8, c.w("row", t0) + 0.2 - t0)
    times = [t0 + span * k / n for k in range(n)]
    for i in range(8):
        s.flash(keys, [t + 0.04 * i for t in times], bx(i), BY, end=t1)


def b_glee(s, t0, t1):
    c = s.cues
    sh = c.w("shouting", t0)
    row(s, [s.emoji("📣", 22), s.emoji("😄", 22)], sh - 0.2, t1, hits=c.beats_in(sh, t1))


def b_peace(s, t0, t1):
    c = s.cues
    peace = c.w("peace", t0)
    letters(s, "PEACE", peace, t1, (WHITE, ICE))
    s.glide(s.emoji("🕊️", 16), [(t0, -10, 8), (peace + 3.0, 210, 6)], z=Z_FRONT)
    s.show(s.word("NO WARS", WHITE, 2), t0, peace, 100, BY, enter="pop", exit="fade", z=Z_WORD)


def b_world(s, t0, t1):
    c = s.cues
    row(s, [s.emoji("🌍", 24), s.emoji("🌎", 24)], t0, t1, hits=c.beats_in(c.w("world", t0), t1))
    s.twinkle(t0, t1, (WHITE, GOLD, ICE), count=10, fade=0.5)


def b_parade(s, t0, t1):
    c = s.cues
    day = c.w("day", t0)
    letters(s, "XMAS", t0, day + 1.0, (RED, GREEN), exit="fade")
    beats = c.beats_in(day + 1.0, t1)
    if not beats:
        return
    march = [ss(s, "soldier", 34), ss(s, "soldier2", 34)]
    for k, (a, b) in enumerate(zip(beats, beats[1:] + [t1])):
        x = -12 + 224 * (a - beats[0]) / max(0.1, t1 - beats[0])
        x2 = -12 + 224 * (b - beats[0]) / max(0.1, t1 - beats[0])
        s.pic(march[k % 2], a, b, x, BY, to=(x2, BY))
        s.pic(march[(k + 1) % 2], a, b, x - 40, BY, to=(x2 - 40, BY))
    s.twinkle(beats[0], t1, XMAS, count=8, fade=0.5)


def b_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.3
    x0 = c.w("christmas", t0 + 0.5)
    day = c.w("day", x0 + 5.5)
    letters(s, "XMAS", x0, day, (RED, GREEN, GOLD), exit="fade")
    row(s, [s.emoji("🎄", 30), ss(s, "santa", 34)], day, end, hits=c.beats_in(day, end - 2.5), exit="fade",
        exit_s=2.5)
    s.twinkle(day, t1, XMAS, count=10, fade=2.5)
    s.snow(day, t1, count=6, speed=5, fade=2.5)


BUSHES = dict(intro=b_intro, wish=b_wish, snow=b_snow, presents=b_presents, santa=b_santa, everyday=b_everyday,
              school=b_school, wonder=b_wonder, slippers=b_slippers, tv=b_tv, kid=b_kid, lights=b_lights,
              welcome=b_welcome, kiss=b_kiss, row=b_row, glee=b_glee, peace=b_peace, world=b_world,
              parade=b_parade, finale=b_finale)
