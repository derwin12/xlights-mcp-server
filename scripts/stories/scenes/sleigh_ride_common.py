"""Sleigh Ride matrix scenes, shared plan for the garage, the two windows (one stage) and the bushes.

The MegaTree carries the SuperStar story (the couple, the horse and sleigh, Farmer Gray's party, the fireplace,
coffee and pumpkin pie, a Currier & Ives frame, candy stripes at the end). The people, horse, sleigh and party
pictures here are that same SuperStar art, read from the sequence's <SequenceMedia> at build time (nothing is
copied into this repo) and widened x3 because they are drawn for the tree's tall, narrow pixels.
Words: faster-whisper (stories/lyrics/sleigh_ride.json); beats/bars: the sequence's own "Beats" track (labelled
1-2-3-4 marks are beats, blank marks are half beats).
"""
import base64
import io
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
from morph_backdrop import backdrop, pattern_sweeps  # noqa: E402,F401
from matrix_scenes import Cues  # noqa: E402
from rockin_common import (BLUE, GOLD, GREEN, ICE, PINK, RED, WHITE, XMAS, Z_BACK, Z_FRONT, Z_PIC,  # noqa: E402,F401
                           Z_WORD, bar_sweeps)

LYRICS = HERE.parent / "lyrics"
BROWN, ORANGE = (150, 80, 20), (255, 130, 0)
WINTER = (WHITE, ICE, BLUE)

# ---------------------------------------------------------------- timing

_SS = {"xsq": None, "imgs": None}


def cues(xsq):
    _SS["xsq"] = xsq
    import json
    root = ET.parse(xsq).getroot()
    dur = float(root.findtext("head/sequenceDuration"))
    beats, ones = [], []
    for e in root.find("ElementEffects"):
        if e.get("type") == "timing" and e.get("name") == "Beats":
            for f in e.find("EffectLayer"):
                lab, t = f.get("label") or "", int(f.get("startTime")) / 1000
                if lab and t < dur:
                    beats.append(t)
                    if lab == "1":
                        ones.append(t)
    words = [(w["w"].strip(), w["s"], w["e"]) for p in json.loads((LYRICS / "sleigh_ride.json").read_text())
             for w in p["words"]]
    c = Cues(words, beats, dur)
    c.bars = ones
    return c


def plan(c):
    w = c.w
    t = [
        ("intro", 0.0),
        ("bells", w("just") - 0.2),
        ("weather", w("come") - 0.2),
        ("snowfall", w("outside") - 0.2),
        ("weather", w("come", 22) - 0.2),
        ("giddy", w("giddy") - 0.2),
        ("wonder", w("riding", 33) - 0.2),
        ("grand", w("giddy", 37) - 0.2),
        ("fairy", w("riding", 42) - 0.2),
        ("cozy", w("our", 45.5) - 0.2),
        ("birds", w("snuggled") - 0.6),
        ("chorus", w("let's", 55) - 0.2),
        ("weather", w("come", 59) - 0.2),
        ("party", w("birthday") - 0.8),
        ("perfect", w("perfect") - 1.3),
        ("sing", w("singing") - 0.8),
        ("fire", w("fireplace") - 1.0),
        ("happy", w("happy", 83) - 0.9),
        ("pie", w("pass") - 0.9),
        ("print", w("nearly") - 0.9),
        ("remember", w("wonderful") - 1.0),
        ("bells", w("just", 106) - 0.2),
        ("weather", w("come", 110) - 0.2),
        ("snowfall", w("outside", 115) - 0.2),
        ("weather", w("come", 119.5) - 0.2),
        ("giddy", w("giddy", 125) - 0.2),
        ("wonder", w("riding", 130) - 0.2),
        ("grand", w("giddy", 134) - 0.2),
        ("fairy", w("gliding", 139) - 0.2),
        ("cozy", w("nice", 144) - 0.2),
        ("birds", w("snuggled", 147) - 0.6),
        ("chorus", w("let's", 152) - 0.2),
        ("finale", w("come", 157) - 0.2),
    ]
    return [(n, t0, t[k + 1][1] if k + 1 < len(t) else c.duration) for k, (n, t0) in enumerate(t)]


def run(s, scenes):
    for name, t0, t1 in plan(s.cues):
        backdrop(s, t0, t1)
        fn = scenes.get(name)
        if fn:
            fn(s, t0, t1)


# ---------------------------------------------------------------- the SuperStar pictures

SS_X = 3.0
SS = {  # name -> media path in the sequence
    "man": "SleighRideImages/SleighRide_4.png",        # man waving / calling
    "man2": "SleighRideImages/SleighRide_1.png",
    "girl": "SleighRideImages/SleighRide_88.png",      # rosy cheeks
    "boy": "SleighRideImages/SleighRide_89.png",
    "couple": "SleighRideImages/SleighRide_33.png",    # holding hands
    "faces": "SleighRideImages/SleighRide_58.png",     # the two of them, close up
    "horse": "SleighRideImages/SleighRide_26.png",     # trotting, two frames
    "horse2": "SleighRideImages/SleighRide_27.png",
    "leap": "SleighRideImages/SleighRide_25.png",      # rearing up
    "sleigh": "SleighRideImages/SleighRide_9.png",     # the couple in the sleigh
    "santa": "SleighRideImages/SleighRide_64.png",
    "farmer": "SleighRideImages/SleighRide_99.png",    # Farmer Gray with his pitchfork
    "cake": "SleighRideImages/SleighRide_103.png",
    "barn": "SleighRideImages/SleighRide_154.png",
    "fire": "SleighRideImages/SleighRide_18.png",      # fireplace
    "coffee": "SleighRideImages/SleighRide_90.png",
    "pie": "SleighRideImages/SleighRide_93.png",
    "world": "SleighRideImages/SleighRide_116.png",
    "happy": "SleighRideImages/SleighRide_130.png",
    "frame": "SleighRideImages/SleighRide_96.png",     # gold picture frame
}


def _ss_image(path):
    if _SS["imgs"] is None:
        root = ET.parse(_SS["xsq"]).getroot()
        want = set(SS.values())
        _SS["imgs"] = {m.get("path"): Image.open(io.BytesIO(base64.b64decode(m.findtext("Data")))).convert("RGBA")
                       for m in root.find("SequenceMedia") if m.get("path") in want and m.findtext("Data")}
    return _SS["imgs"][path]


FACES_LEFT = {"horse", "horse2"}


def ss(s, name, h, flip=False):
    """SuperStar picture `name`, h LEDs tall, aspect corrected for the tree's pixels. Unflipped, everything faces
    right (the tree's horse frames face left, so they are mirrored here; the sleigh already faces right)."""
    if name in FACES_LEFT:
        flip = not flip
    key = f"ss_{name}_{h}{'f' if flip else ''}"
    if s._key(key) in s.images:
        return s._key(key)
    im = _ss_image(SS[name])
    bb = im.getbbox()
    im = im.crop(bb) if bb else im
    w = max(1, round(im.width * SS_X * h / im.height))
    im = im.resize((round(im.width * SS_X), im.height), Image.LANCZOS).resize((w, h), Image.LANCZOS)
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return s.image(key, im)


def trot(s, h, t0, t1, x0, x1, y, flip=False, z=Z_PIC):
    """The horse trotting from x0 to x1, swapping frames and bobbing on the beats."""
    a, b = ss(s, "horse", h, flip), ss(s, "horse2", h, flip)
    ts = [t0] + [t for t in s.cues.beats_in(t0 + 0.1, t1 - 0.1)] + [t1]
    for k, (ta, tb) in enumerate(zip(ts, ts[1:])):
        xa = x0 + (x1 - x0) * (ta - t0) / (t1 - t0)
        xb = x0 + (x1 - x0) * (tb - t0) / (t1 - t0)
        s.pic(a if k % 2 == 0 else b, ta, tb, xa, y - (1 if k % 2 else 0), to=(xb, y - (1 if k % 2 else 0)), z=z)


def ride(s, h, t0, t1, x0, x1, y, z=Z_PIC):
    """Horse pulling the sleigh with the couple, crossing from x0 to x1 (horse leading)."""
    flip = x1 < x0
    sl = ss(s, "sleigh", h, flip)  # faces the way it travels, like the horse
    hw = s.size(ss(s, "horse", h, flip))[0]
    sw = s.size(sl)[0]
    gap = (hw + sw) / 2 - 2
    back = gap if not flip else -gap
    trot(s, h, t0, t1, x0, x1, y, flip, z=z)
    s.glide(sl, [(t0, x0 - back, y), (t1, x1 - back, y)], z=z)


# ---------------------------------------------------------------- drawn props

def bell_img(s, px, color=GOLD):
    def draw(d, im):
        d.pieslice([px * 0.1, px * 0.05, px * 0.9, px * 1.2], 180, 360, fill=color + (255,))
        d.rectangle([px * 0.1, px * 0.6, px * 0.9, px * 0.8], fill=color + (255,))
        d.rectangle([0, px * 0.78, px - 1, px * 0.88], fill=color + (255,))
        d.ellipse([px * 0.4, px * 0.82, px * 0.6, px - 1], fill=(120, 70, 0, 255))
    return s.drawn(f"bell_{px}_{color[0]}", px, px, draw)


def bird_img(s, px, color):
    def draw(d, im):
        d.ellipse([px * 0.1, px * 0.3, px * 0.85, px * 0.9], fill=color + (255,))
        d.ellipse([px * 0.55, px * 0.1, px * 0.95, px * 0.5], fill=color + (255,))
        d.polygon([(px * 0.95, px * 0.3), (px - 1, px * 0.38), (px * 0.9, px * 0.42)], fill=ORANGE + (255,))
        d.point((round(px * 0.8), round(px * 0.27)), fill=(0, 0, 0, 255))
        d.polygon([(px * 0.1, px * 0.6), (0, px * 0.4), (px * 0.2, px * 0.5)], fill=color + (255,))
    return s.drawn(f"bird_{px}_{color[0]}_{color[2]}", px, px, draw)


def snow_hills(s, w, h):
    def draw(d, im):
        d.ellipse([-w * 0.25, h * 0.3, w * 0.6, h * 2.2], fill=(235, 245, 255, 255))
        d.ellipse([w * 0.35, h * 0.1, w * 1.25, h * 2.4], fill=(205, 225, 255, 255))
    return s.drawn(f"snowhills_{w}_{h}", w, h, draw)


def pine(s, h):
    w = round(h * 0.7)

    def draw(d, im):
        for k in range(3):
            top = h * 0.05 + k * h * 0.25
            d.polygon([(w / 2, top), (w * (0.15 - 0.05 * k), top + h * 0.38), (w * (0.85 + 0.05 * k), top + h * 0.38)],
                      fill=(20, 110 + 20 * k, 40, 255))
        d.rectangle([w * 0.42, h * 0.85, w * 0.58, h - 1], fill=BROWN + (255,))
        for k in range(3):  # snow on the boughs
            top = h * 0.05 + k * h * 0.25 + h * 0.36
            d.line([(w * (0.2 - 0.05 * k), top), (w * (0.8 + 0.05 * k), top)], fill=(255, 255, 255, 255))
    return s.drawn(f"pine_{h}", w, h, draw)


def chestnut(s, px):
    def draw(d, im):
        d.ellipse([0, px * 0.15, px - 1, px - 1], fill=(110, 50, 15, 255))
        d.polygon([(px * 0.3, px * 0.3), (px / 2, 0), (px * 0.7, px * 0.3)], fill=(110, 50, 15, 255))
        d.ellipse([px * 0.25, px * 0.35, px * 0.45, px * 0.55], fill=(200, 140, 80, 255))
    return s.drawn(f"chestnut_{px}", px, px, draw)


def frame_img(s, w, h):
    """A gold picture frame (the Currier & Ives print) to hold a winter scene."""
    def draw(d, im):
        d.rectangle([0, 0, w - 1, h - 1], outline=GOLD + (255,), width=3)
        d.rectangle([3, 3, w - 4, h - 4], outline=(150, 100, 0, 255), width=1)
    return s.drawn(f"frame_{w}_{h}", w, h, draw)


def steam(s, h):
    def draw(d, im):
        for k, x in enumerate((2, 6)):
            pts = [(x + (1 if (y // 3 + k) % 2 else 0), y) for y in range(h)]
            d.line(pts, fill=(220, 220, 220, 255))
    return s.drawn(f"steam_{h}", 9, h, draw)


# ================================================================ 140x60 matrix (the garage)

GX, GY = 70, 34


def jingle(s, t0, t1, xs, y, px, every=1):
    """Bells hopping on every beat, alternating."""
    b = bell_img(s, px)
    beats = s.cues.beats_in(t0, t1)
    for i, x in enumerate(xs):
        s.show(b, t0 + 0.1 * i, t1, x, y, enter="top", hits=beats[i % 2::2][::every], amp=3)


def g_intro(s, t0, t1):
    c = s.cues
    s.snow(0.0, t1, count=6, fade=1.5)
    s.show(snow_hills(s, 140, 20), 0.3, t1, GX, 50, enter="bottom", enter_s=1.5, z=Z_BACK)
    for k, x in enumerate((20, 120)):
        s.show(pine(s, 30), 1.0 + 0.5 * k, t1, x, 36, enter="fade", enter_s=1.0, z=Z_BACK)
    ride(s, 30, 2.0, t1, -40, 190, 36)
    s.twinkle(0.5, t1, (WHITE, GOLD), count=10, fade=1.0)


def g_bells(s, t0, t1):
    c = s.cues
    sleigh, ring = c.w("sleigh", t0), c.w("ring", t0)
    jingle(s, t0, t1, (20, 45, 95, 120), 22, 18)
    s.show(s.word("SLEIGH BELLS", GOLD, 2), sleigh, ring, GX, 6, enter="pop", z=Z_WORD)
    s.show(s.word("RING TING", WHITE, 2), ring, t1, GX, 6, enter="pop", z=Z_WORD)
    s.show(ss(s, "sleigh", 34), t0 + 0.3, t1, GX, 40, enter="bottom", hits=c.beats_in(t0, t1)[::2], amp=2)
    for b in c.beats_in(ring, t1):
        s.ring(b, GX, 22, GOLD, r=40, dur=0.5)
    s.snow(t0, t1, count=5)


def g_weather(s, t0, t1):
    c = s.cues
    lovely = c.w("lovely", t0)
    ride_t = next((t for w_, t, _ in c.words if t0 <= t < t1 and w_.startswith(("ride", "together"))), t1 - 1.5)
    s.show(s.word("LOVELY", PINK, 2), lovely, ride_t, GX, 6, enter="pop", z=Z_WORD)
    s.show(s.word("WEATHER", ICE, 2), lovely + 0.4, ride_t, GX, 18, enter="pop", z=Z_WORD)
    ride(s, 32, ride_t - 0.4, t1 + 0.6, 190, -60, 38)
    s.show(s.word("TOGETHER", GOLD, 2), ride_t, t1, GX, 8, enter="pop", z=Z_WORD)
    s.snow(t0, t1, count=6)
    bar_sweeps(s, t0, t1, (ICE, WHITE))


def g_snowfall(s, t0, t1):
    c = s.cues
    snow, friends = c.w("snow", t0), c.w("friends", t0)
    s.snow(t0, t1, count=14, speed=12)
    s.show(snow_hills(s, 140, 18), t0, t1, GX, 51, enter="bottom", z=Z_BACK)
    s.show(s.word("SNOW", WHITE, 3), snow, friends, GX, 12, enter="top", z=Z_WORD)
    beats = c.beats_in(friends, t1)
    s.show(ss(s, "man", 40), friends, t1, 26, 30, enter="left", hits=beats[0::2], amp=2)
    s.show(ss(s, "man2", 40), friends + 0.3, t1, 114, 30, enter="right", hits=beats[1::2], amp=2)
    s.show(s.word("YOO HOO", GOLD, 2), c.w("calling", t0), t1, GX, 12, enter="pop", z=Z_WORD)


def g_giddy(s, t0, t1):
    c = s.cues
    go, show = c.w("go", t0), c.w("show", t0)
    giddies = [t for w_, t, _ in c.words if t0 <= t < go and w_.startswith("giddy")]
    for k, t in enumerate(giddies):
        s.pic(s.word("GIDDY UP", (GOLD, RED, GREEN)[k % 3], 2), t, t + 0.55, GX, 6, z=Z_WORD)
    trot(s, 40, t0, t1, -30, 170, 34)
    s.show(s.word("LETS GO", RED, 2), go, show, GX, 6, enter="pop", z=Z_WORD)
    s.show(s.word("SHOW", GOLD, 2), show, t1, GX, 6, enter="pop", z=Z_WORD)
    for b in c.beats_in(t0, t1):
        s.ring(b, GX, 58, BROWN, r=14, dur=0.3)


def g_wonder(s, t0, t1):
    c = s.cues
    won = c.w("wonderland", t0)
    s.show(snow_hills(s, 140, 20), t0, t1, GX, 50, enter="bottom", z=Z_BACK)
    for k, x in enumerate((14, 44, 96, 126)):
        s.show(pine(s, 26 + 4 * (k % 2)), t0 + 0.2 * k, t1, x, 36, enter="pop", z=Z_BACK)
    s.show(s.word("WONDERLAND", ICE, 2), won, t1, GX, 6, enter="pop", z=Z_WORD)
    ride(s, 26, won, t1, -40, 190, 38)
    s.snow(t0, t1, count=10)
    s.twinkle(won, t1, WINTER, count=14, fade=0.4)


def g_grand(s, t0, t1):
    c = s.cues
    grand, hand = c.w("grand", t0), c.w("hand", t0)
    trot(s, 36, t0, grand, 170, 20, 36, flip=True)
    s.show(ss(s, "leap", 44), grand, hand - 0.3, 26, 32, enter=None)
    s.show(s.word("GRAND", GOLD, 3), grand, hand - 0.3, 90, 30, enter="pop", z=Z_WORD)
    s.show(ss(s, "couple", 48), hand - 0.3, t1, GX, 32, enter="pop", hits=c.beats_in(hand, t1), amp=2)
    s.show(s.emoji("❤️", 16), hand, t1, GX, 8, enter="pop", z=Z_FRONT)
    s.ring(hand, GX, 32, PINK, r=40)


def g_fairy(s, t0, t1):
    c = s.cues
    song = c.w("song", t0)
    ride(s, 30, t0, t1, 190, -60, 36)
    s.show(s.emoji("🎶", 18), song, t1, 20, 10, enter="pop", hits=c.beats_in(song, t1), amp=3, z=Z_FRONT)
    s.show(s.word("FAIRYLAND", PINK, 2), song, t1, 88, 8, enter="pop", z=Z_WORD)
    s.twinkle(t0, t1, (PINK, ICE, WHITE, GOLD), count=24, steps=12, fade=0.3)
    s.snow(t0, t1, count=6)


def g_cozy(s, t0, t1):
    c = s.cues
    comfy, cozy = c.w("comfy", t0), c.w("cozy", t0)
    beats = c.beats_in(t0, t1)
    s.show(ss(s, "girl", 50), t0, t1, 44, 31, enter="left", hits=beats[0::2], amp=2)
    s.show(ss(s, "boy", 50), t0 + 0.3, t1, 96, 31, enter="right", hits=beats[1::2], amp=2)
    s.show(s.word("ROSY", PINK, 2), t0 + 0.4, comfy, GX, 6, enter="pop", z=Z_WORD)
    s.show(s.word("COMFY", GOLD, 2), comfy, cozy, GX, 6, enter="pop", z=Z_WORD)
    s.show(s.word("COZY", ORANGE, 2), cozy, t1, GX, 6, enter="pop", z=Z_WORD)
    s.ring(cozy, GX, 30, PINK, r=50)


def g_birds(s, t0, t1):
    c = s.cues
    birds = c.w("birds", t0)
    s.show(ss(s, "faces", 54), t0, birds, GX, 30, enter="pop")
    b1, b2 = bird_img(s, 22, (200, 30, 30)), bird_img(s, 22, (40, 120, 255))
    b2f = s.image("bird_flip", s.images[b2].transpose(Image.FLIP_LEFT_RIGHT))
    s.glide(b1, [(birds - 0.5, -14, 14), (birds + 0.6, 58, 30), (t1, 58, 30)])
    s.glide(b2f, [(birds - 0.3, 154, 14), (birds + 0.8, 82, 30), (t1, 82, 30)])
    s.show(s.emoji("❤️", 14), birds + 1.0, t1, GX, 14, enter="pop", hits=c.beats_in(birds + 1.2, t1), amp=2,
           z=Z_FRONT)
    s.show(s.word("FEATHER", ICE, 2), c.w("feather", t0), t1, GX, 52, enter="pop", z=Z_WORD)


def g_chorus(s, t0, t1):
    c = s.cues
    sing = c.w("sing", t0)
    beats = c.beats_in(t0, t1)
    ride(s, 28, t0, sing, -40, 60, 40)
    s.show(ss(s, "sleigh", 34), sing, t1, 60, 38, enter=None, hits=beats, amp=2)
    for k, e in enumerate(("🎵", "🎶", "🎵")):
        s.show(s.emoji(e, 16), sing + 0.25 * k, t1, 96 + 14 * k, 18 + 6 * (k % 2), enter="pop",
               hits=beats[k % 2::2], amp=3, z=Z_FRONT)
    s.show(s.word("SING", GOLD, 2), sing, t1, 110, 46, enter="pop", z=Z_WORD)


def g_party(s, t0, t1):
    c = s.cues
    birthday, home = c.w("birthday", t0), c.w("home", t0)
    s.show(ss(s, "barn", 46), t0, t1, 116, 32, enter="right", z=Z_BACK)
    s.show(s.word("BIRTHDAY", PINK, 2), birthday, home, 54, 6, enter="pop", z=Z_WORD)
    s.show(ss(s, "cake", 40), birthday, home, 54, 34, enter="pop")
    s.show(ss(s, "farmer", 50), home, t1, 54, 32, enter="bottom", hits=c.beats_in(home, t1)[::2], amp=2)
    s.show(s.word("FARMER GRAY", WHITE, 1), home + 0.8, t1, 54, 4, enter="pop", z=Z_WORD)
    s.twinkle(birthday, t1, (PINK, GOLD, BLUE), count=14, fade=0.3)


def g_perfect(s, t0, t1):
    c = s.cues
    perfect, day = c.w("perfect", t0), c.w("day", t0)
    s.show(ss(s, "cake", 46), t0, t1, 84, 32, enter="pop", hits=c.beats_in(t0, t1)[::2], amp=2)
    s.show(s.word("PERFECT", GOLD, 2), perfect, t1, 34, 30, enter="left", z=Z_WORD)
    s.show(s.word("DAY", WHITE, 3), day, t1, 122, 30, enter="right", z=Z_WORD)
    s.ring(day, 84, 30, GOLD, r=60, dur=0.9)
    s.twinkle(t0, t1, (GOLD, PINK, WHITE), count=20, fade=0.3)


def g_sing(s, t0, t1):
    c = s.cues
    stop = c.w("stop", t0)
    beats = c.beats_in(t0, t1)
    s.show(ss(s, "faces", 52), t0, t1, GX, 30, enter="pop", hits=beats[::2], amp=2)
    for i, b in enumerate(beats):
        x = 24 if i % 2 == 0 else 116
        s.pic(s.emoji("🎵" if i % 2 else "🎶", 16), b, b + 0.55, x, 20 + 8 * (i % 3), z=Z_FRONT)
    s.show(s.word("NONSTOP", RED, 2), stop - 0.3, t1, GX, 54, enter="pop", z=Z_WORD)


def g_fire(s, t0, t1):
    c = s.cues
    pop = c.w("pop", t0)
    s.show(ss(s, "fire", 54), t0, t1, GX, 30, enter="pop")
    nut = chestnut(s, 8)
    for k, b in enumerate(c.beats_in(c.w("chestnuts", t0) - 0.2, t1)):
        x = 50 + (k * 37) % 40
        s.glide(nut, [(b, GX, 40), (b + 0.4, x, 10 + (k % 3) * 4), (b + 0.8, x + 6, 50)], z=Z_FRONT)
        s.ring(b + 0.4, x, 10 + (k % 3) * 4, ORANGE, r=8, dur=0.3)
    s.show(s.word("POP", ORANGE, 3), pop, t1, 118, 30, enter="pop", z=Z_WORD)
    s.show(s.word("CHESTNUTS", (200, 140, 80), 1), c.w("chestnuts", t0), t1, 24, 30, enter="pop", z=Z_WORD)


def g_happy(s, t0, t1):
    c = s.cues
    world, buy = c.w("world", t0), c.w("buy", t0)
    s.show(ss(s, "happy", 50), t0, world, GX, 30, enter="pop", hits=c.beats_in(t0, world), amp=2)
    s.show(s.word("HAPPY", GOLD, 2), c.w("happy", t0), world, 26, 30, enter="pop", z=Z_WORD)
    s.show(ss(s, "world", 46), world, t1, GX, 30, enter="pop")
    s.show(s.emoji("🚫", 46), buy, t1, GX, 30, enter="pop", z=Z_FRONT)
    s.show(s.emoji("💲", 18), world + 0.2, t1, 116, 30, enter="right", z=Z_FRONT)


def g_pie(s, t0, t1):
    c = s.cues
    coffee = c.w("coffee", t0)
    pie = c.beat_after(coffee + 1.0)
    s.show(ss(s, "coffee", 40), coffee, t1, 40, 34, enter="left")
    s.show(steam(s, 10), coffee + 0.4, t1, 40, 9, enter="fade", z=Z_FRONT)
    s.show(ss(s, "pie", 44), pie, t1, 100, 32, enter="right", hits=c.beats_in(pie + 0.3, t1), amp=2)
    s.show(s.word("COFFEE", (200, 140, 80), 2), coffee, pie, GX, 6, enter="pop", z=Z_WORD)
    s.show(s.word("PUMPKIN PIE", ORANGE, 2), pie, t1, GX, 6, enter="pop", z=Z_WORD)


def print_scene(s, t0, t1, x, y, w, h, hpx):
    """A framed winter picture: snowy hills, a pine and the sleigh crossing inside the frame."""
    s.show(frame_img(s, w, h), t0, t1, x, y, enter="fade", enter_s=0.8, z=Z_FRONT)
    s.show(snow_hills(s, w - 6, h // 3), t0 + 0.3, t1, x, y + h / 2 - h / 6 - 3, enter="fade", z=Z_BACK)
    s.show(pine(s, h // 2), t0 + 0.5, t1, x - w / 4, y + 2, enter="fade", z=Z_BACK)


def g_print(s, t0, t1):
    c = s.cues
    picture = c.w("picture", t0)
    print_scene(s, t0, t1, GX, 30, 120, 52, 52)
    ride(s, 18, picture, t1, 128, 12, 38)
    s.snow(t0, t1, count=6)
    s.show(s.word("PICTURE", GOLD, 1), picture, t1, GX, 9, enter="pop", z=Z_WORD)


def g_remember(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    keys = [ss(s, "sleigh", 36), ss(s, "cake", 36), ss(s, "fire", 40), ss(s, "pie", 36), ss(s, "faces", 40),
            ss(s, "santa", 44)]
    s.flash(keys, c.bars_in(t0, t1) or [t0], GX, 32, end=t1)
    s.show(s.word("WONDERFUL", GOLD, 2), c.w("wonderful", t0), c.w("remember", t0), GX, 6, enter="pop", z=Z_WORD)
    s.show(s.word("REMEMBER", PINK, 2), c.w("remember", t0), t1, GX, 6, enter="pop", z=Z_WORD)
    for b in c.bars_in(t0, t1):
        s.ring(b, GX, 32, GOLD, r=50, dur=0.6)
    s.twinkle(t0, t1, XMAS, count=12)


def g_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.2
    sing_end = c.words[-1][2]
    ride(s, 30, t0, sing_end, -40, 190, 38)
    s.show(s.word("LOVELY WEATHER", PINK, 2), c.w("lovely", t0), sing_end, GX, 8, enter="pop", z=Z_WORD)
    a = sing_end
    s.show(ss(s, "santa", 52), a, end, GX, 30, enter="pop", exit="fade", exit_s=2.0,
           hits=c.beats_in(a + 0.4, end - 2.5)[::2], amp=2)
    s.show(s.word("MERRY", RED, 2), a + 0.4, end, 30, 22, enter="left", exit="fade", exit_s=2.0, z=Z_WORD)
    s.show(s.word("XMAS", GREEN, 2), a + 0.8, end, 112, 22, enter="right", exit="fade", exit_s=2.0, z=Z_WORD)
    jingle(s, a, end - 2.5, (30, 110), 44, 16)
    s.snow(t0, t1, count=8, fade=2.0)
    s.twinkle(a, t1, XMAS, count=16, fade=2.0)
    bar_sweeps(s, a, end - 2.0, (RED, WHITE))


GARAGE = dict(intro=g_intro, bells=g_bells, weather=g_weather, snowfall=g_snowfall, giddy=g_giddy, wonder=g_wonder,
              grand=g_grand, fairy=g_fairy, cozy=g_cozy, birds=g_birds, chorus=g_chorus, party=g_party,
              perfect=g_perfect, sing=g_sing, fire=g_fire, happy=g_happy, pie=g_pie, print=g_print,
              remember=g_remember, finale=g_finale)


# ================================================================ the two windows as one stage

def wins(s):
    return tuple(s.center(m)[0] for m in s.places)  # the two windows, in --model order


WY = 26


def w_intro(s, t0, t1):
    L, C = wins(s)
    s.snow(0.0, t1, count=6, fade=1.5)
    s.show(snow_hills(s, s.W, 14), 0.3, t1, s.W / 2, 41, enter="bottom", enter_s=1.5, z=Z_BACK)
    s.show(pine(s, 30), 1.0, t1, L, 26, enter="fade", enter_s=1.0, z=Z_BACK)
    s.show(pine(s, 30), 1.5, t1, C, 26, enter="fade", enter_s=1.0, z=Z_BACK)
    ride(s, 22, 3.0, t1, s.W + 30, -60, 30)  # crosses the right window, behind the wall, out the left


def w_bells(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    ring = c.w("ring", t0)
    beats = c.beats_in(t0, t1)
    s.show(bell_img(s, 30), t0, t1, L, WY, enter="top", hits=beats[0::2], amp=3)
    s.show(bell_img(s, 30, RED), t0 + 0.2, t1, C, WY, enter="top", hits=beats[1::2], amp=3)
    for i, b in enumerate(c.beats_in(ring, t1)):
        s.ring(b, L if i % 2 == 0 else C, WY, GOLD, r=26, dur=0.4)
    s.snow(t0, t1, count=5)


def w_weather(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    ride_t = next((t for w_, t, _ in c.words if t0 <= t < t1 and w_.startswith(("ride", "together"))), t1 - 1.5)
    s.show(s.emoji("☃️", 30), t0, ride_t, L, WY, enter="pop")
    s.show(s.emoji("❄️", 28), t0 + 0.3, ride_t, C, WY, enter="pop")
    ride(s, 22, ride_t - 0.6, t1 + 0.6, -60, s.W + 30, 30)  # left window, behind the wall, into the right
    s.snow(t0, t1, count=6)


def w_snowfall(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    friends = c.w("friends", t0)
    s.snow(t0, t1, count=12, speed=12)
    s.show(s.emoji("🌨️", 30), t0, friends, C, WY, enter="top")
    beats = c.beats_in(friends, t1)
    s.show(ss(s, "man", 40), friends, t1, L, 26, enter="left", hits=beats[0::2], amp=2)
    s.show(ss(s, "man2", 40), friends + 0.3, t1, C, 26, enter="right", hits=beats[1::2], amp=2)


def w_giddy(s, t0, t1):
    L, C = wins(s)
    trot(s, 30, t0, t1, -24, s.W + 24, 28)
    for b in s.cues.bars_in(t0, t1):
        s.ring(b, L, 44, BROWN, r=16, dur=0.4)
        s.ring(b + 0.3, C, 44, BROWN, r=16, dur=0.4)


def w_wonder(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    s.show(snow_hills(s, s.W, 14), t0, t1, s.W / 2, 41, enter="bottom", z=Z_BACK)
    s.show(pine(s, 28), t0, t1, L, 24, enter="pop", z=Z_BACK)
    s.show(pine(s, 32), t0 + 0.3, t1, C, 22, enter="pop", z=Z_BACK)
    ride(s, 18, c.w("wonderland", t0), t1, -40, s.W + 40, 32)
    s.twinkle(t0, t1, WINTER, count=14, fade=0.4)
    s.snow(t0, t1, count=8)


def w_grand(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    hand = c.w("hand", t0)
    s.show(ss(s, "leap", 38), t0, hand - 0.3, L, WY, enter="left", hits=c.beats_in(t0, hand), amp=2)
    s.show(ss(s, "couple", 40), hand - 0.6, t1, C, WY, enter="right", hits=c.beats_in(hand, t1), amp=2)
    heart = s.emoji("❤️", 14)
    s.glide(heart, [(hand, C, 6), (hand + 0.8, L, 20), (t1, L, 20)], z=Z_FRONT)
    s.ring(hand + 0.8, L, 20, PINK, r=24)


def w_fairy(s, t0, t1):
    L, C = wins(s)
    ride(s, 22, t0, t1, s.W + 30, -60, 30)
    s.twinkle(t0, t1, (PINK, ICE, WHITE, GOLD), count=24, steps=12, fade=0.3)


def w_cozy(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    s.show(ss(s, "girl", 44), t0, t1, L, WY, enter="pop", hits=beats[0::2], amp=2)
    s.show(ss(s, "boy", 44), t0 + 0.3, t1, C, WY, enter="pop", hits=beats[1::2], amp=2)
    s.ring(c.w("cozy", t0), L, WY, PINK, r=24)
    s.ring(c.w("cozy", t0) + 0.2, C, WY, PINK, r=24)


def w_birds(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    birds = c.w("birds", t0)
    b1, b2 = bird_img(s, 22, (200, 30, 30)), bird_img(s, 22, (40, 120, 255))
    b2f = s.image("bird_flip", s.images[b2].transpose(Image.FLIP_LEFT_RIGHT))
    # one bird in each window flies over the wall to meet the other
    s.show(b1, t0, birds, L, WY, enter="pop")
    s.show(b2f, t0 + 0.2, birds, C, WY, enter="pop")
    mid = s.W / 2
    s.glide(b1, [(birds, L, WY), (birds + 0.6, mid - 10, 4), (birds + 1.2, C - 8, WY), (t1, C - 8, WY)])
    s.glide(b2f, [(birds, C, WY), (birds + 1.2, C + 8, WY), (t1, C + 8, WY)])
    s.show(s.emoji("❤️", 14), birds + 1.3, t1, C, 8, enter="pop", z=Z_FRONT)


def w_chorus(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    s.show(ss(s, "sleigh", 34), t0, t1, L, WY, enter="left", hits=beats[0::2], amp=2)
    s.show(s.emoji("🎶", 28), c.w("sing", t0), t1, C, WY, enter="pop", hits=beats[1::2], amp=3)


def w_party(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    home = c.w("home", t0)
    s.show(ss(s, "cake", 36), c.w("birthday", t0), t1, L, WY, enter="pop", hits=c.beats_in(home, t1)[::2], amp=2)
    s.show(ss(s, "barn", 38), t0, home, C, WY, enter="right")
    s.show(ss(s, "farmer", 42), home, t1, C, WY, enter="bottom")
    s.twinkle(t0, t1, (PINK, GOLD, BLUE), count=12, fade=0.3)


def w_perfect(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    day = c.w("day", t0)
    s.show(s.emoji("🎉", 28), t0, t1, L, WY, enter="pop", hits=c.beats_in(t0, t1)[0::2], amp=2)
    s.show(s.emoji("🌅", 30), t0 + 0.3, t1, C, WY, enter="pop")
    s.ring(day, L, WY, GOLD, r=26)
    s.ring(day + 0.2, C, WY, GOLD, r=26)


def w_sing(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    s.show(ss(s, "faces", 42), t0, t1, L, WY, enter="pop", hits=beats[0::2], amp=2)
    note = s.emoji("🎵", 14)
    for k, b in enumerate(c.bars_in(t0, t1)):  # notes float over the wall
        s.glide(note, [(b, L + 10, 12), (b + 1.0, s.W / 2, 2), (b + 2.0, C, 14)], z=Z_FRONT)
    s.show(s.emoji("🎤", 26), t0 + 0.4, t1, C, 30, enter="pop", hits=beats[1::2], amp=2)


def w_fire(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    s.show(ss(s, "fire", 44), t0, t1, L, WY, enter="pop")
    nut = chestnut(s, 8)
    for k, b in enumerate(c.beats_in(c.w("chestnuts", t0) - 0.2, t1)):
        s.glide(nut, [(b, L, 30), (b + 0.4, (L + C) / 2, 4), (b + 0.8, C + (k % 3 - 1) * 8, 36)], z=Z_FRONT)
    s.show(s.word("POP", ORANGE, 2), c.w("pop", t0), t1, C, 14, enter="pop", z=Z_WORD)


def w_happy(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    world = c.w("world", t0)
    s.show(ss(s, "happy", 40), t0, t1, L, WY, enter="pop", hits=c.beats_in(t0, t1)[::2], amp=2)
    s.show(ss(s, "world", 36), world, t1, C, WY, enter="pop")
    s.show(s.emoji("🚫", 36), c.w("buy", t0), t1, C, WY, enter="pop", z=Z_FRONT)


def w_pie(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    coffee = c.w("coffee", t0)
    pie = c.beat_after(coffee + 1.0)
    s.show(ss(s, "coffee", 34), coffee, t1, L, 28, enter="left")
    s.show(steam(s, 8), coffee + 0.4, t1, L, 6, enter="fade", z=Z_FRONT)
    s.show(ss(s, "pie", 38), pie, t1, C, WY, enter="right", hits=c.beats_in(pie + 0.3, t1), amp=2)


def w_print(s, t0, t1):
    """One Currier & Ives print spanning both windows: the frame is the whole stage."""
    c = s.cues
    print_scene(s, t0, t1, s.W / 2, 24, s.W, s.H, s.H)
    ride(s, 16, c.w("picture", t0), t1, s.W - 8, 8, 32)
    s.snow(t0, t1, count=6)


def w_remember(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    bars = c.bars_in(t0, t1) or [t0]
    a = [ss(s, "sleigh", 32), ss(s, "fire", 36), ss(s, "faces", 36)]
    b = [ss(s, "cake", 32), ss(s, "pie", 32), ss(s, "santa", 40)]
    s.flash(a, bars, L, WY, end=t1)
    s.flash(b, bars, C, WY, end=t1)
    s.twinkle(t0, t1, XMAS, count=12)


def w_finale(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    end = t1 - 0.2
    sing_end = c.words[-1][2]
    ride(s, 22, t0, sing_end, -60, s.W + 30, 30)
    s.show(ss(s, "couple", 40), sing_end, end, L, WY, enter="pop", exit="fade", exit_s=2.0)
    s.show(ss(s, "santa", 42), sing_end + 0.4, end, C, WY, enter="pop", exit="fade", exit_s=2.0,
           hits=c.beats_in(sing_end + 0.8, end - 2.5)[::2], amp=2)
    s.snow(t0, t1, count=6, fade=2.0)
    s.twinkle(sing_end, t1, XMAS, count=14, fade=2.0)


WINDOWS = dict(intro=w_intro, bells=w_bells, weather=w_weather, snowfall=w_snowfall, giddy=w_giddy, wonder=w_wonder,
               grand=w_grand, fairy=w_fairy, cozy=w_cozy, birds=w_birds, chorus=w_chorus, party=w_party,
               perfect=w_perfect, sing=w_sing, fire=w_fire, happy=w_happy, pie=w_pie, print=w_print,
               remember=w_remember, finale=w_finale)


# ================================================================ 200x42 matrix: 8 bushes, 25 px each

def bx(i):
    return 12.5 + 25 * i


BY = 22


def row(s, keys, t0, t1, *, hits=None, enter="pop", stagger=0.06, amp=3, z=Z_PIC, y=BY):
    for i in range(8):
        h = hits[i % 2::2] if hits else ()
        s.show(keys[i % len(keys)], t0 + stagger * i, t1, bx(i), y, enter=enter, hits=h, amp=amp, z=z)


def b_intro(s, t0, t1):
    c = s.cues
    tree = pine(s, 32)
    for i in range(8):
        b = c.beats[2 + i] if len(c.beats) > 2 + i else t0
        s.show(tree, b, t1, bx(i), BY, enter="pop", enter_s=0.3)
    s.snow(0.0, t1, count=4, fade=1.5)


def b_bells(s, t0, t1):
    beats = s.cues.beats_in(t0, t1)
    row(s, [bell_img(s, 22), bell_img(s, 22, RED)], t0, t1, hits=beats, enter="top")


def b_weather(s, t0, t1):
    c = s.cues
    ride_t = next((t for w_, t, _ in c.words if t0 <= t < t1 and w_.startswith(("ride", "together"))), t1 - 1.5)
    row(s, [s.emoji("❄️", 20)], t0, ride_t, enter="top")
    ride(s, 24, ride_t - 0.6, t1 + 0.8, -40, 240, 24)


def b_snowfall(s, t0, t1):
    c = s.cues
    friends = c.w("friends", t0)
    s.snow(t0, t1, count=8, speed=12)
    row(s, [ss(s, "man", 36), ss(s, "man2", 36)], friends, t1, hits=c.beats_in(friends, t1), enter="bottom")


def b_giddy(s, t0, t1):
    c = s.cues
    trot(s, 32, t0, t1, -24, 224, 22)
    for k, b in enumerate(c.beats_in(t0, t1)):
        i = min(7, int(8 * (b - t0) / (t1 - t0)))
        s.ring(b, bx(i), 40, BROWN, r=10, dur=0.3)


def b_wonder(s, t0, t1):
    c = s.cues
    row(s, [pine(s, 32)], t0, t1, enter="pop", z=Z_BACK)
    ride(s, 20, c.w("wonderland", t0), t1, -40, 240, 28)
    s.snow(t0, t1, count=6)


def b_grand(s, t0, t1):
    c = s.cues
    hand = c.w("hand", t0)
    trot(s, 30, t0, hand, 224, -24, 22, flip=True)
    row(s, [ss(s, "couple", 38)], hand - 0.3, t1, hits=c.beats_in(hand, t1), enter="bottom", amp=2)
    row(s, [s.emoji("❤️", 10)], hand + 0.3, t1, enter="pop", y=6, z=Z_FRONT)


def b_fairy(s, t0, t1):
    ride(s, 22, t0, t1, 240, -40, 24)
    s.twinkle(t0, t1, (PINK, ICE, WHITE, GOLD), count=12, fade=0.3)


def b_cozy(s, t0, t1):
    row(s, [ss(s, "girl", 38), ss(s, "boy", 38)], t0, t1, hits=s.cues.beats_in(t0, t1), enter="bottom", amp=2)


def b_birds(s, t0, t1):
    c = s.cues
    birds = c.w("birds", t0)
    b1, b2 = bird_img(s, 20, (200, 30, 30)), bird_img(s, 20, (40, 120, 255))
    b2f = s.image("bird_flip", s.images[b2].transpose(Image.FLIP_LEFT_RIGHT))
    for i in range(4):  # pairs of birds meet on each pair of bushes
        x0, x1 = bx(2 * i), bx(2 * i + 1)
        s.glide(b1, [(birds - 0.4 + 0.1 * i, x0 - 12, 6), (birds + 0.4 + 0.1 * i, x0 + 3, BY), (t1, x0 + 3, BY)])
        s.glide(b2f, [(birds - 0.2 + 0.1 * i, x1 + 12, 6), (birds + 0.6 + 0.1 * i, x1 - 3, BY), (t1, x1 - 3, BY)])
    row(s, [s.emoji("❤️", 10)], birds + 1.0, t1, enter="pop", y=6, z=Z_FRONT)


def b_chorus(s, t0, t1):
    c = s.cues
    sing = c.w("sing", t0)
    row(s, [s.emoji("🎵", 20), s.emoji("🎶", 22)], sing, t1, hits=c.beats_in(sing, t1), enter="pop", amp=4)


def b_party(s, t0, t1):
    c = s.cues
    home = c.w("home", t0)
    row(s, [ss(s, "cake", 32)], c.w("birthday", t0), home, enter="pop")
    row(s, [ss(s, "farmer", 38), ss(s, "barn", 34)], home, t1, hits=c.beats_in(home, t1), enter="bottom", amp=2)


def b_perfect(s, t0, t1):
    c = s.cues
    day = c.w("day", t0)
    for i, ch in enumerate("PERFECT"):
        s.show(s.word(ch, GOLD if i % 2 == 0 else PINK, 5), c.w("perfect", t0) + 0.08 * i, day, bx(i), BY,
               enter="pop", enter_s=0.15, z=Z_WORD)
    row(s, [s.emoji("🎉", 22)], day, t1, enter="pop")


def b_sing(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    note = s.emoji("🎵", 18)
    for k, b in enumerate(beats):  # one note per beat, hopping along the bushes without a single stop
        i = k % 8
        s.pic(note, b, b + 0.55, bx(i), BY - (3 if k % 2 else 0), z=Z_FRONT)
    row(s, [ss(s, "faces", 34)], t0, t1, enter="pop", z=Z_BACK)


def b_fire(s, t0, t1):
    c = s.cues
    row(s, [ss(s, "fire", 38)], t0, t1, enter="pop", z=Z_BACK)
    nut = chestnut(s, 8)
    for k, b in enumerate(c.beats_in(c.w("chestnuts", t0) - 0.2, t1)):
        i = (k * 3) % 8
        s.glide(nut, [(b, bx(i), 28), (b + 0.35, bx(i), 4), (b + 0.7, bx(i) + 6, 30)], z=Z_FRONT)
        s.ring(b + 0.35, bx(i), 4, ORANGE, r=8, dur=0.3)


def b_happy(s, t0, t1):
    c = s.cues
    world = c.w("world", t0)
    row(s, [ss(s, "happy", 36)], t0, world, hits=c.beats_in(t0, world), enter="pop", amp=2)
    row(s, [ss(s, "world", 32)], world, t1, enter="pop")


def b_pie(s, t0, t1):
    c = s.cues
    coffee = c.w("coffee", t0)
    pie = c.beat_after(coffee + 1.0)
    row(s, [ss(s, "coffee", 30)], coffee, pie, enter="pop")
    row(s, [ss(s, "pie", 32)], pie, t1, hits=c.beats_in(pie, t1), enter="top", amp=2)


def b_print(s, t0, t1):
    c = s.cues
    for i in range(8):
        s.show(frame_img(s, 23, 38), t0 + 0.08 * i, t1, bx(i), 21, enter="fade", enter_s=0.6, z=Z_FRONT)
    row(s, [pine(s, 26)], t0 + 0.4, t1, enter="fade", z=Z_BACK, y=22)
    ride(s, 16, c.w("picture", t0), t1, 220, -20, 26)
    s.snow(t0, t1, count=4)


def b_remember(s, t0, t1):
    c = s.cues
    bars = c.bars_in(t0, t1) or [t0]
    keys = [ss(s, "sleigh", 30), ss(s, "cake", 30), ss(s, "fire", 34), ss(s, "pie", 30), ss(s, "faces", 34),
            ss(s, "santa", 38)]
    for i in range(8):
        s.flash(keys[i % 6:] + keys[:i % 6], bars, bx(i), BY, end=t1)


def b_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.2
    sing_end = c.words[-1][2]
    ride(s, 24, t0, sing_end, -40, 240, 24)
    beats = c.beats_in(sing_end + 0.3, end - 2.5)
    for i in range(8):
        key = (ss(s, "santa", 38), bell_img(s, 22), pine(s, 32), bell_img(s, 22, RED))[i % 4]
        s.show(key, sing_end + 0.06 * i, end, bx(i), BY, enter="pop", exit="fade", exit_s=2.0,
               hits=beats[i % 2::2], amp=2)
    s.twinkle(sing_end, t1, XMAS, count=10, fade=2.0)


BUSHES = dict(intro=b_intro, bells=b_bells, weather=b_weather, snowfall=b_snowfall, giddy=b_giddy, wonder=b_wonder,
              grand=b_grand, fairy=b_fairy, cozy=b_cozy, birds=b_birds, chorus=b_chorus, party=b_party,
              perfect=b_perfect, sing=b_sing, fire=b_fire, happy=b_happy, pie=b_pie, print=b_print,
              remember=b_remember, finale=b_finale)
