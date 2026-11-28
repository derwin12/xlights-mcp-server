"""You're a Mean One matrix scenes, shared plan for the garage, the two windows (one stage) and the bushes.

The MegaTree carries the SuperStar story (the green villain, the eel, banana, empty heart, spiders, the pole,
the crocodile, skunk, socks, tomato, the sandwich); these scenes play the same insults as picture gags.
The Grinch pictures are the sequence's own SuperStar MegaTree images, aspect corrected (see grump()).
Words: faster-whisper (stories/lyrics/grinch.json); beats: the sequence's hand-counted "Beat Count" track.
"""
import html
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
from morph_backdrop import backdrop, pattern_sweeps  # noqa: E402,F401
from matrix_scenes import Cues  # noqa: E402
from rockin_common import (GOLD, PURPLE, RED, WHITE, Z_BACK, Z_FRONT, Z_PIC, Z_WORD)  # noqa: E402,F401

LYRICS = HERE.parent / "lyrics"
SLIME, SICK, MOSS = (90, 220, 30), (170, 230, 60), (30, 120, 20)
VIOLET = (150, 40, 200)
GRUMPY = (SLIME, PURPLE, RED)


def cues(xsq):
    """Words from whisper; beats from the counted 1-2-3-4 'Beat Count' track (clipped to the song)."""
    import json
    _SS["xsq"] = xsq
    root = ET.parse(xsq).getroot()
    dur = float(root.findtext("head/sequenceDuration"))
    beats, ones = [], []
    for e in root.find("ElementEffects"):
        if e.get("name") == "Beat Count":
            for f in e.find("EffectLayer"):
                t = int(f.get("startTime")) / 1000
                if t < dur:
                    beats.append(t)
                    if f.get("label") == "1":
                        ones.append(t)
    words = [(html.unescape(w["w"]).strip(), w["s"], w["e"])
             for p in json.loads((LYRICS / "grinch.json").read_text()) for w in p["words"]]
    c = Cues(words, beats, dur)
    c.bars = ones  # the counted downbeats, not every 4th detected beat
    return c


def plan(c):
    w = c.w
    t = [
        ("intro", 0.0),
        ("mean", w("you're") - 0.1),
        ("cactus", w("you're", 13) - 0.1),
        ("eel", w("as", 16.3) - 0.1),
        ("banana", w("you're", 20.5) - 0.1),
        ("stomp", 27.0),
        ("monster", w("you're", 34) - 0.1),
        ("brain", w("your", 42.5) - 0.1),
        ("pole", w("i", 50) - 0.1),
        ("vile", w("you're", 57.5) - 0.1),
        ("termites", w("you", 62) - 0.1),
        ("croc", w("you", 67) - 0.1),
        ("choice", w("given") - 0.1),
        ("skunk", w("you're", 84.5) - 0.1),
        ("socks", w("your", 94) - 0.1),
        ("gunk", w("your", 96.8) - 0.1),
        ("quote", w("grinch", 100.3) - 0.1),
        ("stink", w("stink") - 0.1),
        ("rotter", w("you're", 112) - 0.1),
        ("tomato", w("your", 121.4) - 0.1),
        ("dump", w("itch") - 0.1),
        ("nausea", w("you", 142.5) - 0.1),
        ("horse", w("you're", 152) - 0.1),
        ("sandwich", w("you're", 159.5) - 0.1),
        ("finale", w("exhaust") + 1.0),
    ]
    return [(n, t0, t[k + 1][1] if k + 1 < len(t) else c.duration) for k, (n, t0) in enumerate(t)]


def run(s, scenes):
    for name, t0, t1 in plan(s.cues):
        backdrop(s, t0, t1)
        fn = scenes.get(name)
        if fn:
            fn(s, t0, t1)


# ---------------------------------------------------------------- drawn props

# The Grinch himself comes from the sequence's own SuperStar import (the MegaTree "Front" pictures embedded in the
# .xsq), so the matrices show the same character as the tree. They are drawn for the tree's tall, narrow pixels:
# widen x3 to look right on a square-pixel matrix. Nothing is copied into this repo; cues() notes which .xsq to
# read them from.
SS_X = 3.0
SS_MOODS = {  # media path in the sequence -> what it shows
    "mean": "GrinchImages/GrinchImages_56.png",      # face, Santa hat, angry eyes, smirk
    "grin": "GrinchImages/GrinchImages_60.png",      # face, wide open grin
    "sick": "GrinchImages/GrinchImages_177.png",     # scowling head, no mouth
    "smile": "GrinchImages/GrinchImages_55.png",     # face, sly smile (finale)
    "shout": "GrinchImages/GrinchImages_80.png",     # face and collar, yelling
    "termites": "GrinchImages/GrinchImages_101.png", # toothy grin, purple bugs in the teeth
    "body": "GrinchImages/GrinchImages_24.png",      # full figure in the Santa suit
    "cactus": "GrinchImages/GrinchImages_28.png",    # the Grinch as a cactus
    "socks": "GrinchImages/GrinchImages_132.png",    # Santa suit, heart full of socks
    "king": "GrinchImages/GrinchImages_146.png",     # crown and goblet
}
_SS = {"xsq": None, "imgs": None}


def _ss_image(path):
    if _SS["imgs"] is None:
        import base64
        import io
        from PIL import Image
        root = ET.parse(_SS["xsq"]).getroot()
        _SS["imgs"] = {m.get("path"): Image.open(io.BytesIO(base64.b64decode(m.findtext("Data")))).convert("RGBA")
                       for m in root.find("SequenceMedia") if m.findtext("Data") and m.get("path") in
                       SS_MOODS.values()}
    return _SS["imgs"][path]


def grump(s, h, mood="mean"):
    """The SuperStar Grinch picture for `mood`, h LEDs tall (aspect corrected for the tree's pixels)."""
    from PIL import Image
    key = f"grinch_{mood}_{h}"
    if s._key(key) in s.images:
        return s._key(key)
    im = _ss_image(SS_MOODS[mood])
    bb = im.getbbox()
    im = im.crop(bb) if bb else im
    w = max(1, round(im.width * SS_X * h / im.height))
    im = im.resize((round(im.width * SS_X), im.height), Image.LANCZOS).resize((w, h), Image.LANCZOS)
    return s.image(key, im)


def flipped(s, key):
    name = key.rsplit("/", 1)[1][:-4] + "_flip"
    return s.image(name, s.images[key].transpose(0))


def eel(s, w):
    h = max(6, w // 4)

    def draw(d, im):
        pts = [(x, h / 2 + (h / 2 - 2) * math.sin(x / w * 3 * math.pi)) for x in range(0, w - 4)]
        d.line(pts, fill=(60, 200, 160, 255), width=max(2, h // 3))
        d.ellipse([w - 7, h / 2 - 3, w - 1, h / 2 + 3], fill=(60, 200, 160, 255))
        d.point((w - 3, h / 2 - 1), fill=(255, 255, 0, 255))
    return s.drawn(f"eel_{w}", w, h, draw)


def pole(s, w):
    def draw(d, im):
        d.rectangle([0, 0, w - 1, 2], fill=(200, 150, 80, 255))
        for x in range(0, w, 12):
            d.point((x, 1), fill=(120, 70, 30, 255))
    return s.drawn(f"pole_{w}", w, 3, draw)


def empty_heart(s, px):
    def draw(d, im):
        r = px / 4
        d.ellipse([0, 0, 2 * r, 2 * r], fill=(220, 0, 0, 255))
        d.ellipse([2 * r, 0, 4 * r - 1, 2 * r], fill=(220, 0, 0, 255))
        d.polygon([(0, r * 1.2), (px - 1, r * 1.2), (px / 2, px - 1)], fill=(220, 0, 0, 255))
        hr = px * 0.18
        d.ellipse([px / 2 - hr, px * 0.42 - hr, px / 2 + hr, px * 0.42 + hr], fill=(0, 0, 0, 0))
    return s.drawn(f"emptyheart_{px}", px, px, draw)


def moldy_tomato(s, px):
    def draw(d, im):
        d.ellipse([0, 2, px - 1, px - 1], fill=(220, 30, 20, 255))
        d.polygon([(px / 2, 0), (px / 2 - 4, 4), (px / 2 + 4, 4)], fill=(40, 150, 30, 255))
        for fx, fy, r in ((0.3, 0.45, 0.10), (0.65, 0.6, 0.13), (0.45, 0.78, 0.08), (0.72, 0.35, 0.07)):
            d.ellipse([px * (fx - r), px * (fy - r), px * (fx + r), px * (fy + r)], fill=VIOLET + (255,))
    return s.drawn(f"moldytomato_{px}", px, px, draw)


def knots(s, w, h):
    def draw(d, im):
        for k, col in enumerate(((200, 150, 80), (150, 220, 60), (180, 60, 200))):
            pts = [(x, h / 2 + (h / 2 - 2) * math.sin(x / w * (5 + k) * math.pi + k)) for x in range(w)]
            d.line(pts, fill=col + (255,), width=2)
    return s.drawn(f"knots_{w}_{h}", w, h, draw)


def stink_lines(s, h):
    w = max(8, h // 2)

    def draw(d, im):
        for k in range(3):
            x0 = 1 + k * (w - 2) / 2
            pts = [(x0 + 1.5 * math.sin(y / h * 3 * math.pi), h - 1 - y) for y in range(h)]
            d.line(pts, fill=SICK + (255,))
    return s.drawn(f"stink_{h}", w, h, draw)


def sandwich(s, w):
    """Three-decker: bread, kraut, bread, toadstool slice, bread."""
    h = round(w * 0.75)

    def draw(d, im):
        layers = [((220, 170, 90), 0.18), ((240, 230, 120), 0.12), ((220, 170, 90), 0.16),
                  ((200, 30, 30), 0.12), ((220, 170, 90), 0.16), ((240, 230, 120), 0.1), ((220, 170, 90), 0.16)]
        y = 0.0
        for col, fr in layers:
            d.rectangle([1 if col[0] != 220 else 0, y, w - 1, y + h * fr - 1], fill=col + (255,))
            y += h * fr
        for x in range(3, w - 2, 6):
            d.point((x, h * 0.62), fill=WHITE + (255,))  # toadstool spots
    return s.drawn(f"sandwich_{w}", w, h, draw)


def slime(s, w, h):
    def draw(d, im):
        d.rectangle([0, 0, w - 1, h * 0.3], fill=SLIME + (255,))
        for x in range(2, w, 7):
            L = h * (0.4 + 0.6 * ((x * 37) % 11) / 11)
            d.rectangle([x, 0, x + 2, L - 3], fill=SLIME + (255,))
            d.ellipse([x - 1, L - 5, x + 3, L - 1], fill=SLIME + (255,))
    return s.drawn(f"slime_{w}_{h}", w, h, draw)


def bar_sweeps(s, t0, t1, colors=(SLIME, PURPLE), every=1):
    """SuperStar-style Morph pattern groups on every other beat (none while the tree's are echoed)."""
    pattern_sweeps(s, t0, t1, colors, every)


# ================================================================ 140x60 matrix (the garage)

GX, GY = 70, 33


def g_intro(s, t0, t1):
    c = s.cues
    s.twinkle(0.3, t1, (SLIME, PURPLE), count=10, fade=1.0)
    g = grump(s, 50)
    s.glide(g, [(1.0, GX, 90), (t1 - 0.3, GX, GY)])
    s.ring(t1 - 0.3, GX, GY, SLIME, r=60)


def g_mean(s, t0, t1):
    c = s.cues
    heel = c.w("heel", t0)
    beats = c.beats_in(t0, t1)
    s.hold(grump(s, 50), t0, t1, GX, GY, hits=beats[::2], amp=2)
    s.show(s.word("MEAN ONE", SLIME, 2), c.w("mean", t0), heel, GX, 6, enter="pop", z=Z_WORD)
    s.show(s.emoji("👠", 24), heel, t1, 120, 36, enter="right")
    s.show(s.word("HEEL", RED, 2), heel, t1, 24, 30, enter="pop", z=Z_WORD)
    s.ring(c.w("mean", t0), GX, GY, SLIME, r=60)
    bar_sweeps(s, t0, t1)


def g_cactus(s, t0, t1):
    c = s.cues
    s.show(grump(s, 50), t0, t1, 96, GY, enter=None)
    s.show(grump(s, 56, "cactus"), t0 + 0.2, t1, 34, 31, enter="bottom", hits=[c.w("cactus", t0)], amp=3)
    s.show(s.word("CUDDLY", PURPLE, 2), c.w("cuddly", t0), t1, 34, 6, enter="pop", z=Z_WORD)


def g_eel(s, t0, t1):
    c = s.cues
    e = eel(s, 60)
    s.show(grump(s, 50, "grin"), t0, t1, 96, GY, enter=None)
    s.glide(e, [(c.w("charming", t0), -32, 40), (t1, 172, 30)], z=Z_FRONT)
    s.show(s.word("CHARMING", (60, 200, 160), 2), c.w("charming", t0), t1, GX, 6, enter="pop", z=Z_WORD)


def g_banana(s, t0, t1):
    c = s.cues
    bad, greasy = c.w("bad", t0), c.w("greasy", t0)
    s.show(grump(s, 50), t0, t1, 26, GY, enter="left")
    s.show(s.emoji("🍌", 40), c.w("banana", t0), t1, 96, 34, enter="pop", hits=c.beats_in(greasy, t1), amp=2)
    s.show(s.word("BAD BANANA", GOLD, 2), bad, greasy, GX, 6, enter="pop", z=Z_WORD)
    s.show(s.word("GREASY", MOSS, 2), greasy, t1, GX, 6, enter="pop", z=Z_WORD)
    s.ring(greasy, 96, 34, SICK, r=40)


def g_stomp(s, t0, t1):
    """Instrumental: the grump stomps across, slime drips on the bars."""
    c = s.cues
    g, gf = grump(s, 56, "body"), None
    gf = flipped(s, g)
    beats = c.beats_in(t0, t1)
    xs = [10 + 120 * k / max(1, len(beats) - 1) for k in range(len(beats))]
    for k, b in enumerate(beats[:-1]):
        key = g if (k // 6) % 2 == 0 else gf
        x0, x1 = (xs[k], xs[k + 1]) if (k // 6) % 2 == 0 else (xs[-1 - k], xs[-2 - k])
        s.pic(key, b, (b + beats[k + 1]) / 2, x0, 38, to=((x0 + x1) / 2, 34))
        s.pic(key, (b + beats[k + 1]) / 2, beats[k + 1], (x0 + x1) / 2, 34, to=(x1, 38))
        s.ring(beats[k + 1], x1, 58, SLIME, r=12, dur=0.35)
    s.show(slime(s, 140, 14), t0, t1, GX, 7, enter="top", enter_s=1.0, z=Z_BACK)
    bar_sweeps(s, t0, t1, (PURPLE, SLIME))


def g_monster(s, t0, t1):
    c = s.cues
    hole = c.w("hole", t0)
    s.show(grump(s, 56), t0, c.w("heart's", t0), GX, 31, enter="pop", hits=c.beats_in(t0, t1)[::2], amp=2)
    s.show(s.word("MONSTER", PURPLE, 3), c.w("monster", t0), c.w("heart's", t0), GX, 8, enter="pop", z=Z_WORD)
    s.show(empty_heart(s, 40), c.w("heart's", t0), t1, GX, 30, enter="pop")
    s.show(s.word("EMPTY", WHITE, 2), c.w("empty", t0), t1, 22, 30, enter="left", z=Z_WORD)
    s.ring(hole, GX, 27, WHITE, r=10, dur=0.6)
    s.ring(hole + 0.3, GX, 27, RED, r=40, dur=0.8)


def g_brain(s, t0, t1):
    c = s.cues
    spiders, garlic = c.w("spiders", t0), c.w("garlic", t0)
    s.show(s.emoji("🧠", 40), t0, t1, 46, 32, enter="pop")
    spider = s.emoji("🕷️", 12)
    for k in range(4):
        a = spiders - 0.6 + 0.25 * k
        s.glide(spider, [(a, 46 + (k - 1.5) * 8, -8), (a + 0.6, 46 + (k - 1.5) * 8, 24 + (k % 2) * 8),
                         (garlic, 46 + (k - 1.5) * 8, 24 + (k % 2) * 8)], z=Z_FRONT)
    s.show(s.word("SPIDERS", PURPLE, 2), spiders, garlic, GX, 6, enter="pop", z=Z_WORD)
    s.show(s.emoji("🧄", 36), garlic, t1, 108, 34, enter="right", hits=c.beats_in(garlic, t1), amp=2)
    s.show(s.word("GARLIC", WHITE, 2), garlic, t1, GX, 6, enter="pop", z=Z_WORD)
    s.ring(garlic, 108, 34, SICK, r=30)


def g_pole(s, t0, t1):
    c = s.cues
    touch, p = c.w("touch", t0), c.w("pole", t0)
    s.show(grump(s, 50), t0, t1, 118, GY, enter="right")
    s.show(s.emoji("🙅", 30), touch, t1, 18, 38, enter="left")
    # the pole slides out a long way... and only just reaches
    long = pole(s, 260)
    s.glide(long, [(c.w("thirty", t0), -130, 30), (p, 66, 30), (t1, 66, 30)], z=Z_FRONT)
    s.show(s.word("NO TOUCH", RED, 2), touch, c.w("thirty", t0), 60, 8, enter="pop", z=Z_WORD)
    s.show(s.word("LONG POLE", GOLD, 2), c.w("thirty", t0), t1, 60, 8, enter="pop", z=Z_WORD)
    s.ring(p, 96, 30, GOLD, r=20)


def g_vile(s, t0, t1):
    c = s.cues
    s.show(grump(s, 56, "grin"), t0, t1, GX, 31, enter="pop", hits=c.beats_in(t0, t1), amp=2)
    s.show(s.word("VILE ONE", VIOLET, 2), c.w("vile", t0), t1, GX, 6, enter="pop", z=Z_WORD)
    s.ring(c.w("vile", t0), GX, 31, VIOLET, r=60)


def g_termites(s, t0, t1):
    c = s.cues
    smile = c.w("smile", t0)
    s.show(grump(s, 50, "termites"), t0, t1, GX, GY, enter=None)
    ant = s.emoji("🐜", 10)
    for k in range(6):
        a = c.w("termites", t0) - 0.3 + 0.3 * k
        s.glide(ant, [(a, -8, 50 - (k % 2) * 4), (a + 2.2, GX - 6 + k * 2, 40)], z=Z_FRONT)
    s.show(s.word("TERMITES", SICK, 2), c.w("termites", t0), t1, GX, 6, enter="pop", z=Z_WORD)
    s.ring(smile, GX, 40, GOLD, r=20)


def g_croc(s, t0, t1):
    c = s.cues
    seasick = c.w("seasick", t0)
    s.show(s.emoji("🐊", 44), t0 + 0.3, t1, 46, 36, enter="left", hits=c.beats_in(t0, t1)[::2], amp=2)
    s.show(s.emoji("🤢", 24), seasick, t1, 46, 12, enter="pop", z=Z_FRONT)
    s.show(s.word("SEASICK", SICK, 2), seasick, t1, 108, 10, enter="pop", z=Z_WORD)
    s.show(s.emoji("🌊", 22), seasick, t1, 108, 40, enter="bottom", hits=c.beats_in(seasick, t1), amp=3)
    s.ring(seasick, 46, 36, SICK, r=40)


def g_choice(s, t0, t1):
    c = s.cues
    take = c.w("take", t0)
    s.show(grump(s, 44), t0, take, 34, 34, enter="left")
    s.show(s.emoji("🐊", 40), t0 + 0.3, t1, 106, 36, enter="right")
    s.show(s.word("OR", WHITE, 2), t0 + 0.5, take, GX, 30, enter="pop", z=Z_WORD)
    s.pic(grump(s, 44), take, take + 0.8, 34, 34, to=(-30, 34))
    s.show(s.word("CROC WINS", GOLD, 2), take + 0.6, t1, GX, 6, enter="pop", z=Z_WORD)
    s.ring(take + 0.6, 106, 36, GOLD, r=50)
    s.twinkle(take + 0.6, t1, (GOLD, SLIME), count=15, fade=0.4)


def g_skunk(s, t0, t1):
    c = s.cues
    foul, skunk = c.w("foul", t0), c.w("skunk", t0)
    s.show(grump(s, 50), t0, t1, 30, GY, enter="left")
    s.show(s.word("FOUL ONE", MOSS, 2), foul, c.w("nasty", t0), GX, 6, enter="pop", z=Z_WORD)
    s.show(s.word("NASTY", SICK, 2), c.w("nasty", t0), t1, GX, 6, enter="pop", z=Z_WORD)
    s.show(s.emoji("🦨", 40), skunk - 0.3, t1, 104, 36, enter="right")
    s.show(stink_lines(s, 20), skunk, t1, 104, 10, enter="bottom", hits=c.beats_in(skunk, t1), amp=2)
    s.ring(skunk, 104, 36, SICK, r=40)


def g_socks(s, t0, t1):
    c = s.cues
    socks = c.w("socks", t0)
    s.show(empty_heart(s, 40), t0, t1, GX, 30, enter="pop")
    sock = s.emoji("🧦", 14)
    for k, (x, y) in enumerate(((64, 26), (76, 26), (70, 36))):
        s.show(sock, socks - 0.4 + 0.2 * k, t1, x, y, enter="top", enter_s=0.25, z=Z_FRONT)
    s.show(s.word("SOCKS", WHITE, 2), socks, t1, GX, 6, enter="pop", z=Z_WORD)


def g_gunk(s, t0, t1):
    c = s.cues
    gunk = c.w("gunk", t0)
    s.show(grump(s, 44, "sick"), t0, t1, GX, 36, enter=None)
    s.show(slime(s, 140, 26), gunk - 0.3, t1, GX, 13, enter="top", enter_s=0.8, z=Z_FRONT)
    s.show(s.word("GUNK", SLIME, 3), gunk, t1, GX, 50, enter="pop", z=Z_WORD)


def g_quote(s, t0, t1):
    c = s.cues
    three = c.w("three", t0)
    s.show(grump(s, 50), t0, t1, 22, GY, enter=None)
    s.show(s.word("THREE WORDS", GOLD, 2), three, t1, 84, 12, enter="pop", z=Z_WORD)
    for k in range(3):
        s.show(s.emoji("❓", 14), c.w("follows", t0) + 0.4 * k, t1, 60 + 24 * k, 40, enter="pop")


def g_stink(s, t0, t1):
    c = s.cues
    ts = [c.w("stink", t0), c.w("stank", t0), c.w("stump", t0)]
    for k, (txt, t) in enumerate(zip(("STINK", "STANK", "STUNK"), ts)):
        s.show(s.word(txt, (SICK, VIOLET, RED)[k], 3), t, t1, GX, 10 + 18 * k, enter="pop", z=Z_WORD)
        s.ring(t, GX, 10 + 18 * k, (SICK, VIOLET, RED)[k], r=50, dur=0.6)
    s.show(stink_lines(s, 30), ts[0], t1, 14, 30, enter="bottom")
    s.show(stink_lines(s, 30), ts[1], t1, 126, 30, enter="bottom")


def g_rotter(s, t0, t1):
    c = s.cues
    king = c.w("king", t0)
    s.show(grump(s, 48, "shout"), t0, king, GX, 35, enter="pop", hits=c.beats_in(t0, king)[::2], amp=2)
    s.show(s.word("ROTTER", MOSS, 2), c.w("rotter", t0), king, GX, 6, enter="pop", z=Z_WORD)
    s.show(grump(s, 58, "king"), king, t1, GX, 30, enter="pop", hits=c.beats_in(king, t1)[::2], amp=2)
    s.show(s.word("KING", GOLD, 2), king, t1, 24, 30, enter="left", z=Z_WORD)
    s.ring(king, GX, 8, GOLD, r=30)


def g_tomato(s, t0, t1):
    c = s.cues
    moldy = c.w("moldy", t0)
    s.show(s.emoji("🍅", 40), c.w("dead", t0), moldy, 46, 32, enter="pop")
    s.show(moldy_tomato(s, 40), moldy, t1, 46, 32, enter=None)
    s.show(s.word("MOLDY", VIOLET, 2), moldy, t1, 104, 30, enter="right", z=Z_WORD)
    s.ring(moldy, 46, 32, VIOLET, r=40)


def g_dump(s, t0, t1):
    c = s.cues
    dump, tangled = c.w("dump", t0), c.w("tangled", t0)
    s.show(s.emoji("🗑️", 34), dump - 0.4, t1, GX, 40, enter="bottom")
    s.show(s.word("DUMP", MOSS, 2), dump, c.w("overflowing", t0), GX, 8, enter="pop", z=Z_WORD)
    junk = ["🍌", "🧦", "🦴", "🥫", "🐟", "👢"]
    for k, e in enumerate(junk):
        a = c.w("overflowing", t0) + 0.7 * k
        x = 20 + 20 * k
        s.show(s.emoji(e, 14), a, tangled, x, 52 - (k % 2) * 8, enter="top", enter_s=0.3)
    s.show(s.word("RUBBISH", SICK, 2), c.w("rubbish", t0), tangled, GX, 8, enter="pop", z=Z_WORD)
    s.show(knots(s, 140, 30), tangled, t1, GX, 30, enter="fade", enter_s=0.5, z=Z_FRONT)
    s.show(s.word("TANGLED", GOLD, 2), tangled, t1, GX, 6, enter="pop", z=Z_WORD)


def g_nausea(s, t0, t1):
    c = s.cues
    s.show(s.emoji("🤢", 40), t0, t1, 34, 32, enter="pop", hits=c.beats_in(t0, t1)[::2], amp=2)
    s.show(s.emoji("🤮", 40), c.w("nauseous", t0), t1, 106, 32, enter="pop")
    s.show(s.word("YUCK", SICK, 3), c.w("nauseate", t0), t1, GX, 14, enter="pop", z=Z_WORD)
    s.wash(c.w("nauseous", t0), t1, (20, 50, 0), z=0, fade_in=0.5, fade_out=0.3)


def g_horse(s, t0, t1):
    c = s.cues
    horse = c.w("horse", t0)
    s.show(s.word("CROOKED", PURPLE, 2), c.w("crooked", t0), t1, GX, 6, enter="pop", z=Z_WORD)
    g = grump(s, 26, "grin")
    h = s.emoji("🐴", 34)
    # wobbly ride across
    pts_h, pts_g = [], []
    span = t1 - (horse - 1.5)
    for k in range(9):
        t = horse - 1.5 + span * k / 8
        x = -20 + 180 * k / 8
        y = 40 + (4 if k % 2 else -4)
        pts_h.append((t, x, y))
        pts_g.append((t, x - 2, y - 22))
    s.glide(h, pts_h)
    s.glide(g, pts_g, z=Z_FRONT)


def g_sandwich(s, t0, t1):
    c = s.cues
    sauer, toad = c.w("sauerkraut", t0), c.w("toadstool", t0)
    sw = sandwich(s, 44)
    s.show(s.word("THREE DECKER", GOLD, 2), c.w("three", t0), sauer, GX, 6, enter="pop", z=Z_WORD)
    s.show(sw, sauer - 0.3, t1, GX, 36, enter="top", enter_s=0.5, hits=c.beats_in(sauer + 1, t1)[::2], amp=2)
    s.show(s.emoji("🍄", 22), toad, t1, 22, 40, enter="left")
    s.show(s.emoji("🍄", 22), toad + 0.2, t1, 118, 40, enter="right")
    s.show(s.word("SANDWICH", SICK, 2), c.w("sandwich", t0), t1, GX, 6, enter="pop", z=Z_WORD)
    s.ring(c.w("sandwich", t0), GX, 36, GOLD, r=45)


def g_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.2
    mid = t0 + (end - t0) * 0.45
    s.show(grump(s, 50), t0, mid, GX, GY, enter="pop", hits=c.beats_in(t0, mid)[::2], amp=2)
    s.show(grump(s, 50, "smile"), mid, end, GX, GY, enter=None, exit="fade", exit_s=2.0)
    s.show(s.emoji("❤️", 10), mid, end, GX, GY + 6, enter="pop", exit="fade", exit_s=2.0, z=Z_FRONT)
    s.ring(mid, GX, GY + 6, RED, r=60, dur=1.0)
    s.show(s.emoji("🎄", 26), mid + 0.4, end, 18, 44, enter="bottom", exit="fade", exit_s=2.0)
    s.show(s.emoji("🎄", 26), mid + 0.6, end, 122, 44, enter="bottom", exit="fade", exit_s=2.0)
    s.twinkle(mid, t1, (RED, SLIME, GOLD, WHITE), count=18, fade=2.0)


GARAGE = dict(intro=g_intro, mean=g_mean, cactus=g_cactus, eel=g_eel, banana=g_banana, stomp=g_stomp,
              monster=g_monster, brain=g_brain, pole=g_pole, vile=g_vile, termites=g_termites, croc=g_croc,
              choice=g_choice, skunk=g_skunk, socks=g_socks, gunk=g_gunk, quote=g_quote, stink=g_stink,
              rotter=g_rotter, tomato=g_tomato, dump=g_dump, nausea=g_nausea, horse=g_horse, sandwich=g_sandwich,
              finale=g_finale)


# ================================================================ the two windows as one stage

def wins(s):
    return tuple(s.center(m)[0] for m in s.places)  # the two windows, in --model order


WY = 26


def w_intro(s, t0, t1):
    L, C = wins(s)
    s.twinkle(0.3, t1, (SLIME, PURPLE), count=8, fade=1.0)
    g = grump(s, 30)
    # peeks into one window, then the other
    s.glide(g, [(0.8, L, 70), (1.8, L, 40), (2.4, L, 40), (3.0, L, 70)])
    s.glide(g, [(2.6, C, 70), (3.4, C, 40), (t1, C, 40)])


def w_mean(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    heel = c.w("heel", t0)
    s.show(grump(s, 36), t0, t1, C, WY, enter=None, hits=c.beats_in(t0, t1)[::2], amp=2)
    s.show(s.emoji("😠", 30), c.w("mean", t0), heel, L, WY, enter="pop")
    s.show(s.emoji("👠", 30), heel, t1, L, WY, enter="pop")
    s.ring(heel, L, WY, RED, r=26)


def w_cactus(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    s.show(grump(s, 46, "cactus"), t0 + 0.2, t1, L, WY, enter="bottom", hits=[c.w("cactus", t0)], amp=3)
    s.show(grump(s, 36), t0, t1, C, WY, enter=None)


def w_eel(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    e = eel(s, 40)
    s.glide(e, [(c.w("charming", t0), s.W + 22, 24), (t1, -22, 30)], z=Z_FRONT)
    s.show(grump(s, 36, "grin"), t0, t1, C, WY, enter=None)


def w_banana(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    greasy = c.w("greasy", t0)
    s.show(grump(s, 36), t0, t1, C, WY, enter=None)
    s.show(s.emoji("🍌", 34), c.w("banana", t0), t1, L, WY, enter="pop", hits=c.beats_in(greasy, t1), amp=2)
    s.ring(greasy, L, WY, SICK, r=26)


def w_stomp(s, t0, t1):
    c = s.cues
    g = grump(s, 44, "body")
    gf = flipped(s, g)
    k, a = 0, t0
    while a + 2.5 < t1:
        rt = k % 2 == 0
        x0, x1 = (-18, s.W + 18) if rt else (s.W + 18, -18)
        s.glide(g if rt else gf, [(a, x0, 30), (a + 2.5, x1, 30)])
        k, a = k + 1, a + 2.7
    s.show(slime(s, s.W, 10), t0, t1, s.W / 2, 5, enter="top", enter_s=1.0, z=Z_BACK)


def w_monster(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    heart = c.w("heart's", t0)
    s.show(grump(s, 38), t0, t1, L, WY, enter="pop", hits=c.beats_in(t0, t1)[::2], amp=2)
    s.show(s.emoji("👹", 30), t0 + 0.3, heart, C, WY, enter="pop")
    s.show(empty_heart(s, 30), heart, t1, C, WY, enter="pop")
    s.ring(c.w("hole", t0), C, WY - 3, WHITE, r=8, dur=0.6)


def w_brain(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    spiders, garlic = c.w("spiders", t0), c.w("garlic", t0)
    s.show(s.emoji("🧠", 34), t0, t1, L, WY, enter="pop")
    spider = s.emoji("🕷️", 10)
    for k in range(3):
        a = spiders - 0.3 + 0.3 * k
        s.glide(spider, [(a, L - 10 + 10 * k, -6), (a + 0.6, L - 10 + 10 * k, 20 + 4 * (k % 2)),
                         (t1, L - 10 + 10 * k, 20 + 4 * (k % 2))], z=Z_FRONT)
    s.show(s.emoji("🧄", 32), garlic, t1, C, WY, enter="right")
    s.ring(garlic, C, WY, SICK, r=26)


def w_pole(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    s.show(grump(s, 36), t0, t1, C, WY, enter=None)
    s.show(s.emoji("🙅", 30), c.w("touch", t0), t1, L, WY, enter="pop")
    s.glide(pole(s, 150), [(c.w("thirty", t0), -80, 22), (c.w("pole", t0), C - 90, 22), (t1, C - 90, 22)],
            z=Z_FRONT)


def w_vile(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    s.show(grump(s, 38, "grin"), t0, t1, L, WY, enter="pop", hits=beats[0::2], amp=3)
    s.show(grump(s, 38), t0 + 0.2, t1, C, WY, enter="pop", hits=beats[1::2], amp=3)


def w_termites(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    s.show(grump(s, 40, "termites"), t0, t1, C, WY, enter=None)
    ant = s.emoji("🐜", 9)
    for k in range(5):  # a line of termites marching from the left window over the wall to his smile
        a = c.w("termites", t0) + 0.35 * k
        s.glide(ant, [(a, -6, 40), (a + 2.4, C, 34)], z=Z_FRONT)


def w_croc(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    seasick = c.w("seasick", t0)
    s.show(s.emoji("🐊", 34), t0, t1, L, WY, enter="left", hits=c.beats_in(t0, t1)[::2], amp=2)
    s.show(s.emoji("🤢", 30), seasick, t1, C, WY, enter="pop")
    s.ring(seasick, C, WY, SICK, r=26)


def w_choice(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    take = c.w("take", t0)
    s.show(grump(s, 36), t0, take + 0.3, L, WY, enter="pop", exit="bottom")
    s.show(s.emoji("🐊", 34), t0 + 0.2, t1, C, WY, enter="pop")
    s.show(s.emoji("✅", 16), take + 0.4, t1, C, 8, enter="pop", z=Z_FRONT)
    s.ring(take + 0.4, C, WY, GOLD, r=26)
    s.twinkle(take, t1, (GOLD, SLIME), count=12, fade=0.4)


def w_skunk(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    skunk = c.w("skunk", t0)
    s.show(grump(s, 36), t0, t1, L, WY, enter=None)
    s.show(s.emoji("😤", 30), t0 + 0.3, skunk - 0.3, C, WY, enter="pop")
    s.show(s.emoji("🦨", 34), skunk - 0.3, t1, C, WY + 4, enter="right")
    # the stink drifts from the skunk over the wall into his window
    st = stink_lines(s, 16)
    s.glide(st, [(skunk, C, 8), (t1, L + 6, 6)], z=Z_FRONT)


def w_socks(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    socks = c.w("socks", t0)
    s.show(empty_heart(s, 30), t0, t1, L, WY, enter="pop")
    sock = s.emoji("🧦", 14)
    s.glide(sock, [(socks - 0.6, C, 60), (socks, C, WY), (socks + 0.8, L, WY - 2), (t1, L, WY - 2)], z=Z_FRONT)
    s.show(grump(s, 46, "socks"), socks, t1, C, WY, enter="pop")


def w_gunk(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    gunk = c.w("gunk", t0)
    s.show(grump(s, 36, "sick"), t0, t1, L, 30, enter=None)
    s.show(slime(s, s.W, 22), gunk - 0.3, t1, s.W / 2, 11, enter="top", enter_s=0.8, z=Z_FRONT)


def w_quote(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    s.show(grump(s, 36), t0, t1, L, WY, enter=None)
    s.show(s.emoji("📜", 30), c.w("three", t0), t1, C, WY, enter="pop")


def w_stink(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    ts = [c.w("stink", t0), c.w("stank", t0), c.w("stump", t0)]
    pics = ("🤢", "🦨", "🤮")
    # STINK (left) until STUNK replaces it; STANK (right) stays to the end
    for k, (txt, t) in enumerate(zip(("STINK", "STANK", "STUNK"), ts)):
        x = (L, C, L)[k]
        end = ts[2] if k == 0 else t1
        s.show(s.emoji(pics[k], 28), t, end, x, 30, enter="pop")
        s.show(s.word(txt, (SICK, VIOLET, RED)[k], 1), t, end, x, 8, enter="pop", z=Z_WORD)
        s.ring(t, x, 30, (SICK, VIOLET, RED)[k], r=26, dur=0.5)


def w_rotter(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    king = c.w("king", t0)
    g = grump(s, 34, "shout")
    s.show(g, t0, king + 0.8, C, WY + 4, enter="pop", hits=c.beats_in(t0, king)[::2], amp=2)
    crown = s.emoji("👑", 18)
    s.show(crown, t0 + 0.4, king, L, WY, enter="pop")
    s.glide(crown, [(king, L, WY), (king + 0.8, C, 6)], z=Z_FRONT)
    s.show(grump(s, 46, "king"), king + 0.8, t1, C, WY, enter=None, hits=c.beats_in(king + 1, t1)[::2], amp=2)


def w_tomato(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    moldy = c.w("moldy", t0)
    s.show(s.emoji("🍅", 32), c.w("dead", t0), moldy, L, WY, enter="pop")
    s.show(moldy_tomato(s, 32), moldy, t1, L, WY, enter=None)
    s.show(grump(s, 36, "sick"), t0, t1, C, WY, enter=None)
    s.ring(moldy, L, WY, VIOLET, r=26)


def w_dump(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    tangled = c.w("tangled", t0)
    s.show(s.emoji("🗑️", 32), c.w("dump", t0) - 0.3, tangled, L, WY + 4, enter="bottom")
    junk = ["🍌", "🧦", "🦴", "🥫"]
    for k, e in enumerate(junk):
        a = c.w("overflowing", t0) + 0.9 * k
        s.glide(s.emoji(e, 12), [(a, L, 20), (a + 0.9, C - 10 + 7 * k, 40 - (k % 2) * 6),
                                 (tangled, C - 10 + 7 * k, 40 - (k % 2) * 6)])
    s.show(knots(s, s.W, 30), tangled, t1, s.W / 2, WY, enter="fade", enter_s=0.5, z=Z_FRONT)


def w_nausea(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    s.show(s.emoji("🤢", 32), t0, t1, L, WY, enter="pop", hits=c.beats_in(t0, t1)[::2], amp=2)
    s.show(s.emoji("🤮", 32), c.w("nauseous", t0), t1, C, WY, enter="pop")


def w_horse(s, t0, t1):
    c = s.cues
    horse = c.w("horse", t0)
    h = s.emoji("🐴", 28)
    g = grump(s, 20, "grin")
    pts_h, pts_g = [], []
    span = t1 - (horse - 1.5)
    for k in range(9):
        t = horse - 1.5 + span * k / 8
        x = -18 + (s.W + 36) * k / 8
        y = 32 + (3 if k % 2 else -3)
        pts_h.append((t, x, y))
        pts_g.append((t, x - 2, y - 18))
    s.glide(h, pts_h)
    s.glide(g, pts_g, z=Z_FRONT)


def w_sandwich(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    sauer = c.w("sauerkraut", t0)
    s.show(sandwich(s, 34), sauer - 0.3, t1, L, WY, enter="top", enter_s=0.5, hits=c.beats_in(sauer + 1, t1)[::2])
    s.show(s.emoji("🍄", 28), c.w("toadstool", t0), t1, C, WY, enter="pop")
    s.ring(c.w("sandwich", t0), L, WY, GOLD, r=26)


def w_finale(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    end = t1 - 0.2
    mid = t0 + (end - t0) * 0.45
    s.show(grump(s, 36), t0, mid, L, WY, enter="pop")
    s.show(grump(s, 36, "smile"), mid, end, L, WY, enter=None, exit="fade", exit_s=2.0)
    heart = s.emoji("❤️", 12)
    s.glide(heart, [(mid, L, WY + 4), (mid + 1.2, C, WY)], z=Z_FRONT)
    s.show(s.emoji("❤️", 30), mid + 1.2, end, C, WY, enter="pop", exit="fade", exit_s=2.0)
    s.ring(mid + 1.2, C, WY, RED, r=30)
    s.twinkle(mid, t1, (RED, SLIME, GOLD), count=15, fade=2.0)


WINDOWS = dict(intro=w_intro, mean=w_mean, cactus=w_cactus, eel=w_eel, banana=w_banana, stomp=w_stomp,
               monster=w_monster, brain=w_brain, pole=w_pole, vile=w_vile, termites=w_termites, croc=w_croc,
               choice=w_choice, skunk=w_skunk, socks=w_socks, gunk=w_gunk, quote=w_quote, stink=w_stink,
               rotter=w_rotter, tomato=w_tomato, dump=w_dump, nausea=w_nausea, horse=w_horse, sandwich=w_sandwich,
               finale=w_finale)


# ================================================================ 200x42 matrix: 8 bushes, 25 px each

def bx(i):
    return 12.5 + 25 * i


BY = 22


def row(s, keys, t0, t1, *, hits=None, enter="pop", stagger=0.06, amp=3, z=Z_PIC):
    """One picture per bush (keys cycle); hits alternate between odd and even bushes."""
    for i in range(8):
        h = hits[i % 2::2] if hits else ()
        s.show(keys[i % len(keys)], t0 + stagger * i, t1, bx(i), BY, enter=enter, hits=h, amp=amp, z=z)


def b_intro(s, t0, t1):
    g = grump(s, 26)
    for i in range(8):
        a = 0.8 + 0.35 * i
        s.glide(g, [(a, bx(i), 60), (a + 0.3, bx(i), BY), (a + 0.6, bx(i), 60)])
    s.twinkle(0.3, t1, (SLIME, PURPLE), count=6, fade=1.0)


def b_mean(s, t0, t1):
    c = s.cues
    heel = c.w("heel", t0)
    beats = c.beats_in(t0, t1)
    row(s, [grump(s, 30), s.emoji("😠", 22)], t0, heel, hits=beats, enter="bottom")
    row(s, [s.emoji("👠", 22), grump(s, 30)], heel, t1, hits=beats)


def b_cactus(s, t0, t1):
    row(s, [grump(s, 40, "cactus")], t0 + 0.1, t1, enter="bottom")


def b_eel(s, t0, t1):
    c = s.cues
    e = eel(s, 40)
    for k in range(2):
        a = c.w("charming", t0) + 1.2 * k
        s.glide(e, [(a, -24 if k == 0 else 224, 18 + 8 * k), (a + 3.0, 224 if k == 0 else -24, 18 + 8 * k)])


def b_banana(s, t0, t1):
    c = s.cues
    row(s, [s.emoji("🍌", 24)], c.w("banana", t0), t1, hits=c.beats_in(c.w("greasy", t0), t1))


def b_stomp(s, t0, t1):
    c = s.cues
    g = grump(s, 36, "body")
    beats = c.beats_in(t0, t1)
    path = list(range(8)) + list(range(6, 0, -1))
    for k, b in enumerate(beats[:-1]):
        i, j = path[k % len(path)], path[(k + 1) % len(path)]
        m = (b + beats[k + 1]) / 2
        s.pic(g, b, m, bx(i), 24, to=((bx(i) + bx(j)) / 2, 12))
        s.pic(g, m, beats[k + 1], (bx(i) + bx(j)) / 2, 12, to=(bx(j), 24))
        s.ring(beats[k + 1], bx(j), 40, SLIME, r=10, dur=0.35)


def b_monster(s, t0, t1):
    c = s.cues
    heart = c.w("heart's", t0)
    row(s, [grump(s, 30)], t0, heart, hits=c.beats_in(t0, heart), enter="bottom")
    row(s, [empty_heart(s, 22)], heart, t1)


def b_brain(s, t0, t1):
    c = s.cues
    garlic = c.w("garlic", t0)
    row(s, [s.emoji("🧠", 22), s.emoji("🕷️", 20)], t0, garlic, hits=c.beats_in(c.w("spiders", t0), garlic))
    row(s, [s.emoji("🧄", 24)], garlic, t1, enter="top")


def b_pole(s, t0, t1):
    c = s.cues
    s.glide(pole(s, 260), [(c.w("thirty", t0), -130, 22), (c.w("pole", t0) + 0.5, 100, 22), (t1, 100, 22)])
    row(s, [s.emoji("🙅", 22)], c.w("touch", t0), c.w("thirty", t0), enter="pop")


def b_vile(s, t0, t1):
    c = s.cues
    row(s, [grump(s, 30, "grin"), grump(s, 30)], t0, t1, hits=c.beats_in(t0, t1), enter="bottom")


def b_termites(s, t0, t1):
    c = s.cues
    ant = s.emoji("🐜", 10)
    for k in range(10):
        a = c.w("termites", t0) + 0.25 * k
        s.glide(ant, [(a, -6, 34), (a + 4.0, 206, 34)])
    row(s, [grump(s, 30, "termites")], c.w("smile", t0) - 0.3, t1, enter="pop", z=Z_BACK)


def b_croc(s, t0, t1):
    c = s.cues
    seasick = c.w("seasick", t0)
    row(s, [s.emoji("🐊", 24)], t0, seasick, hits=c.beats_in(t0, seasick), enter="bottom")
    row(s, [s.emoji("🤢", 22), s.emoji("🐊", 24)], seasick, t1, hits=c.beats_in(seasick, t1))


def b_choice(s, t0, t1):
    c = s.cues
    take = c.w("take", t0)
    for i in range(8):
        k = grump(s, 28) if i < 4 else s.emoji("🐊", 24)
        s.show(k, t0 + 0.06 * i, take if i < 4 else t1, bx(i), BY, enter="bottom", exit="bottom" if i < 4 else None)
    s.twinkle(take, t1, (GOLD, SLIME), count=8, fade=0.4)


def b_skunk(s, t0, t1):
    c = s.cues
    skunk = c.w("skunk", t0)
    row(s, [grump(s, 28), s.emoji("😤", 22)], t0, skunk - 0.3, hits=c.beats_in(t0, skunk), enter="bottom")
    row(s, [s.emoji("🦨", 24)], skunk - 0.3, t1, enter="bottom")
    row(s, [stink_lines(s, 16)], skunk + 0.4, t1, enter="bottom", z=Z_FRONT, hits=c.beats_in(skunk, t1))


def b_socks(s, t0, t1):
    row(s, [s.emoji("🧦", 22)], t0 + 0.1, t1, enter="top", stagger=0.1)


def b_gunk(s, t0, t1):
    gunk = s.cues.w("gunk", t0)
    s.show(slime(s, 200, 30), gunk - 0.4, t1, 100, 15, enter="top", enter_s=0.8)


def b_quote(s, t0, t1):
    c = s.cues
    row(s, [grump(s, 28)], t0, c.w("follows", t0), hits=c.beats_in(t0, c.w("follows", t0)), enter="bottom")
    for k in range(3):
        s.show(s.emoji("❓", 20), c.w("follows", t0) + 0.4 * k, t1, bx(2 + 2 * k - 1) + 12.5, BY, enter="pop")


def b_stink(s, t0, t1):
    c = s.cues
    ts = [c.w("stink", t0), c.w("stank", t0), c.w("stump", t0)]
    letters = [("STINK", 0), ("STANK", 0), ("STUNK", 3)]
    for k, ((wd, start), t) in enumerate(zip(letters, ts)):
        end = ts[k + 1] if k < 2 else t1
        st = 1 if k < 2 else 1
        for i, ch in enumerate(wd):
            s.show(s.word(ch, (SICK, VIOLET, RED)[k], 5), t + 0.05 * i, end, bx(st + i), BY, enter="pop",
                   enter_s=0.15, z=Z_WORD)


def b_rotter(s, t0, t1):
    c = s.cues
    king = c.w("king", t0)
    row(s, [grump(s, 28, "grin")], t0, king, hits=c.beats_in(t0, king), enter="bottom")
    row(s, [s.emoji("👑", 22)], king, t1, enter="top")


def b_tomato(s, t0, t1):
    c = s.cues
    moldy = c.w("moldy", t0)
    row(s, [s.emoji("🍅", 22)], c.w("dead", t0), moldy)
    row(s, [moldy_tomato(s, 22)], moldy, t1, enter=None, stagger=0.1)


def b_dump(s, t0, t1):
    c = s.cues
    tangled = c.w("tangled", t0)
    junk = ["🗑️", "🍌", "🧦", "🦴", "🥫", "🐟", "👢", "🗑️"]
    for i, e in enumerate(junk):
        s.show(s.emoji(e, 22), t0 + 0.2 + 0.7 * i, tangled, bx(i), BY, enter="top", enter_s=0.3)
    s.show(knots(s, 200, 30), tangled, t1, 100, BY, enter="fade", enter_s=0.5)


def b_nausea(s, t0, t1):
    c = s.cues
    row(s, [s.emoji("🤢", 22), s.emoji("🤮", 22)], t0, t1, hits=c.beats_in(t0, t1))


def b_horse(s, t0, t1):
    c = s.cues
    horse = c.w("horse", t0)
    h, g = s.emoji("🐴", 24), grump(s, 16, "grin")
    pts_h, pts_g = [], []
    span = t1 - (horse - 1.5)
    for k in range(11):
        t = horse - 1.5 + span * k / 10
        x = -16 + 232 * k / 10
        y = 28 + (3 if k % 2 else -3)
        pts_h.append((t, x, y))
        pts_g.append((t, x - 2, y - 15))
    s.glide(h, pts_h)
    s.glide(g, pts_g, z=Z_FRONT)


def b_sandwich(s, t0, t1):
    c = s.cues
    sauer = c.w("sauerkraut", t0)
    row(s, [sandwich(s, 22), s.emoji("🍄", 22)], sauer - 0.3, t1, enter="top",
        hits=c.beats_in(sauer + 1, t1), amp=2)


def b_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.2
    mid = t0 + (end - t0) * 0.45
    row(s, [grump(s, 30)], t0, mid, hits=c.beats_in(t0, mid), enter="pop")
    for i in range(8):
        s.show(grump(s, 30, "smile") if i % 2 == 0 else s.emoji("❤️", 20), mid + 0.1 * i, end, bx(i), BY,
               enter=None if i % 2 == 0 else "pop", exit="fade", exit_s=2.0)
    s.twinkle(mid, t1, (RED, SLIME, GOLD), count=10, fade=2.0)


BUSHES = dict(intro=b_intro, mean=b_mean, cactus=b_cactus, eel=b_eel, banana=b_banana, stomp=b_stomp,
              monster=b_monster, brain=b_brain, pole=b_pole, vile=b_vile, termites=b_termites, croc=b_croc,
              choice=b_choice, skunk=b_skunk, socks=b_socks, gunk=b_gunk, quote=b_quote, stink=b_stink,
              rotter=b_rotter, tomato=b_tomato, dump=b_dump, nausea=b_nausea, horse=b_horse, sandwich=b_sandwich,
              finale=b_finale)
