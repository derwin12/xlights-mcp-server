"""Yellow Snow (a "Let It Snow" parody about a dog marking the yard): shared plan for the garage, the two windows
(one snowy yard) and the bushes.

The dog, the snowman, the steam cloud and the "puppy drawing" smiley are the sequence's own SuperStar MegaTree
pictures, read from the .xsq at build time and widened x3 for square matrix pixels (see ss()); nothing is copied
into this repo. Words: faster-whisper (stories/lyrics/yellow_snow.json); beats: librosa (yellow_snow_beats.json).
Family friendly: the joke is yellow patches appearing in the snow.
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
from matrix_scenes import Cues  # noqa: E402
from morph_backdrop import backdrop, pattern_sweeps  # noqa: E402,F401
from rockin_common import (GOLD, GREEN, ICE, PINK, RED, WHITE, XMAS, Z_BACK, Z_FRONT, Z_PIC,  # noqa: E402,F401
                           Z_WORD, bar_sweeps)

LYRICS = HERE.parent / "lyrics"
YELLOW, PEE = (255, 220, 0), (240, 200, 0)
SNOWC = (235, 245, 255)
Z_GROUND = 15
Z_SPOT = 16


def cues(xsq):
    _SS["xsq"] = xsq
    dur = float(ET.parse(xsq).getroot().findtext("head/sequenceDuration"))
    return Cues.from_files(LYRICS / "yellow_snow.json", LYRICS / "yellow_snow_beats.json", dur)


def plan(c):
    w = c.w
    t = [
        ("intro", 0.0),
        ("weather", w("weather") - 0.1),
        ("noplace", w("he's", 22) - 0.1),
        ("sniff", w("and", 30.5) - 0.1),
        ("everywhere", w("you", 38) - 0.1),
        ("storm", w("when", 45) - 0.1),
        ("pride", w("he'll", 53) - 0.1),
        ("drawings", w("when", 61) - 0.1),
        ("vangogh", w("he's", 69) - 0.1),
        ("frosty", w("come", 76.5) - 0.1),
        ("pride", w("you'll", 85) - 0.1),
        ("wag", w("when", 92) - 0.1),
        ("sag", w("but", 95.5) - 0.1),
        ("write", w("there's", 99.5) - 0.1),
        ("chorus", w("yellow", 103.5) - 0.1),
        ("patches", w("yellow", 115.3) - 0.1),
        ("finale", w("those", 122) - 0.1),
    ]
    return [(n, t0, t[k + 1][1] if k + 1 < len(t) else c.duration) for k, (n, t0) in enumerate(t)]


def run(s, scenes):
    for name, t0, t1 in plan(s.cues):
        backdrop(s, t0, t1)
        fn = scenes.get(name)
        if fn:
            fn(s, t0, t1)


# ---------------------------------------------------------------- SuperStar pictures

SS_X = 3.0
SS = {  # mood -> media path in the sequence
    "steam": "YellowSnowImages/YellowSnow_293.png",    # grey steam cloud
    "smiley": "YellowSnowImages/YellowSnow_s150.png",  # the yellow "puppy drawing" smiley
    "snowman": "YellowSnowImages/YellowSnow_288.png",  # snowman, top hat
    "snowman_y": "YellowSnowImages/YellowSnow_217.png",   # snowman with a yellow side
    "snowman_sag": "YellowSnowImages/YellowSnow_216.png",  # snowman sagging
}
_SS = {"xsq": None, "imgs": None}


DOGS = {"sit", "run", "wag", "santa", "face"}  # the dog is an emoji: the tree's dog pictures read poorly on the matrices


def dog(s, mood, h, flip=False):
    """Yeller, h LEDs tall, facing right (flip: left). Noto 🐕 side on; 🐶 face for 'come here'; 'santa' adds a hat."""
    import matrix_storybook as mb
    from PIL import Image, ImageDraw
    face = mood == "face"
    im = mb.icon_image("🐶" if face else "🐕", round(h * (1.1 if face else 1.7)), False)
    bb = im.getchannel("A").getbbox()
    im = im.crop(bb) if bb else im
    im = im.resize((max(1, round(im.width * h / im.height)), h), Image.LANCZOS)
    if not face:
        im = im.transpose(0)  # Noto's dog faces left
    if mood == "santa":
        hh = max(4, h // 3)
        out = Image.new("RGBA", (im.width + 2, h + hh - 2), (0, 0, 0, 0))
        out.alpha_composite(im, (0, hh - 2))
        d = ImageDraw.Draw(out)
        hx = round(im.width * (0.5 if face else 0.78))  # over the head
        d.polygon([(hx - hh * 0.6, hh), (hx + hh * 0.6, hh), (hx + hh * 0.9, 1)], fill=(220, 0, 0, 255))
        d.rectangle([hx - hh * 0.7, hh - 1, hx + hh * 0.7, hh + 1], fill=(255, 255, 255, 255))
        d.ellipse([hx + hh * 0.8 - 1, 0, hx + hh * 0.8 + 2, 3], fill=(255, 255, 255, 255))
        im = out
    if flip:
        im = im.transpose(0)
    return im


def ss(s, mood, h, flip=False):
    """The picture for `mood`, h LEDs tall: the dog as an emoji, the rest from the SuperStar import
    (aspect corrected for the tree's narrow pixels)."""
    from PIL import Image
    key = f"ys_{mood}_{h}{'f' if flip else ''}"
    if s._key(key) in s.images:
        return s._key(key)
    if mood in DOGS:
        return s.image(key, dog(s, mood, h, flip))
    if _SS["imgs"] is None:
        import base64
        import io
        root = ET.parse(_SS["xsq"]).getroot()
        _SS["imgs"] = {m.get("path"): Image.open(io.BytesIO(base64.b64decode(m.findtext("Data")))).convert("RGBA")
                       for m in root.find("SequenceMedia") if m.findtext("Data") and m.get("path") in SS.values()}
    im = _SS["imgs"][SS[mood]]
    bb = im.getbbox()
    im = im.crop(bb) if bb else im
    w = max(1, round(im.width * SS_X * h / im.height))
    im = im.resize((round(im.width * SS_X), im.height), Image.LANCZOS).resize((w, h), Image.LANCZOS)
    if flip:
        im = im.transpose(0)
    return s.image(key, im)


# ---------------------------------------------------------------- drawn props

def ground(s, w, h):
    """A snowy yard: white drifts along the bottom."""
    def draw(d, im):
        import math
        for x in range(w):
            top = h * 0.35 + h * 0.25 * math.sin(x / 9.0) + h * 0.1 * math.sin(x / 3.7)
            d.line([(x, top), (x, h - 1)], fill=SNOWC + (255,))
    return s.drawn(f"ground_{w}_{h}", w, h, draw)


def spot(s, w):
    h = max(2, round(w * 0.45))

    def draw(d, im):
        d.ellipse([0, 0, w - 1, h - 1], fill=PEE + (255,))
        if w >= 6:
            d.ellipse([w * 0.25, h * 0.2, w * 0.6, h * 0.6], fill=(255, 245, 120, 255))
    return s.drawn(f"spot_{w}", w, h, draw)


def scribble(s, w, h):
    """'Puppy drawings': a yellow squiggle signature in the snow."""
    def draw(d, im):
        import math
        pts = [(x, h / 2 + (h / 2 - 1) * math.sin(x / w * 4 * math.pi) * (0.4 + 0.6 * (x % 7) / 7)) for x in range(w)]
        d.line(pts, fill=PEE + (255,), width=max(1, h // 8))
    return s.drawn(f"scribble_{w}_{h}", w, h, draw)


def flake_rows(s, t0, t1, count=8):
    s.snow(t0, t1, count=count, fade=0.5)


def spots_on(s, times, xs, y, w, t1, ring=True):
    """A yellow spot pops onto the snow at each time (x positions cycle)."""
    k = spot(s, w)
    for i, t in enumerate(times):
        x = xs[i % len(xs)]
        s.show(k, t, t1, x, y, enter="pop", enter_s=0.2, z=Z_SPOT)
        if ring:
            s.ring(t, x, y, YELLOW, r=max(6, w), dur=0.4)


def ywords(c, t0, t1):
    return [t for wd, t, _ in c.words if t0 <= t < t1 and wd.startswith("yellow")]


# ================================================================ 140x60 matrix (the garage)

GY = 52  # snow line


def g_ground(s, t0, t1, enter=None):
    s.show(ground(s, 140, 14), t0, t1, 70, 53, enter=enter, enter_s=1.0, z=Z_GROUND)


def g_intro(s, t0, t1):
    c = s.cues
    flake_rows(s, 0.2, t1, 10)
    g_ground(s, 0.3, t1, enter="bottom")
    s.show(ss(s, "sit", 40), 3.0, t1, 70, 31, enter="left", enter_s=1.5, hits=c.beats_in(5, t1)[::4], amp=1)
    s.twinkle(0.5, t1, (WHITE, ICE), count=8, fade=1.0)


def g_weather(s, t0, t1):
    c = s.cues
    fr = c.w("frightening", t0)
    g_ground(s, t0, t1)
    s.show(s.word("WEATHER", ICE, 2), t0, fr - 0.3, 70, 6, enter="pop", z=Z_WORD)
    s.show(ss(s, "sit", 40), t0, fr, 70, 31, enter=None)
    s.show(ss(s, "run", 30), fr, t1, 70, 36, enter=None, hits=c.beats_in(fr, t1), amp=3)
    s.show(s.word("UH OH", YELLOW, 2), fr, t1, 70, 6, enter="pop", z=Z_WORD)
    s.ring(fr, 70, 36, YELLOW, r=40)
    flake_rows(s, t0, t1, 10)


def g_noplace(s, t0, t1):
    c = s.cues
    ys = ywords(c, t0, t1)
    g_ground(s, t0, t1)
    s.show(ss(s, "sit", 40), t0, t1, 24, 31, enter=None)
    s.show(s.word("NO PLACE TO GO", WHITE, 1), t0 + 0.2, ys[0] if ys else t1, 82, 10, enter="pop", z=Z_WORD)
    for i, t in enumerate(ys):
        s.show(s.word("YELLOW SNOW" if i % 2 == 0 else "YELLOW", YELLOW, 2), t, t1, 86, 8 + 14 * (i % 3), enter="pop",
               z=Z_WORD)
    spots_on(s, ys, [60, 92, 120], 54, 12, t1)
    flake_rows(s, t0, t1, 8)


def g_sniff(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    g_ground(s, t0, t1)
    dog, dogf = ss(s, "run", 26), ss(s, "run", 26, flip=True)
    half = (t0 + t1) / 2
    s.glide(dog, [(t0, -30, 38), (half, 170, 40)])
    s.glide(dogf, [(half, 170, 40), (t1, -30, 38)])
    s.show(s.word("SNIFF", ICE, 2), c.w("sniffs", t0), t1, 70, 8, enter="pop", z=Z_WORD)
    spots_on(s, beats[2::4], [22, 48, 76, 104, 128], 54, 8, t1, ring=False)
    s.show(s.word("NO STOPPING", RED, 1), c.w("stopping", t0), c.w("sniffs", t0), 70, 8, enter="pop", z=Z_WORD)


def g_everywhere(s, t0, t1):
    c = s.cues
    ys = ywords(c, t0, t1)
    beats = c.beats_in(t0, t1)
    g_ground(s, t0, t1)
    s.show(s.word("EVERYWHERE", YELLOW, 2), c.w("everywhere", t0), t1, 70, 8, enter="pop", z=Z_WORD)
    spots_on(s, beats[::2], [12, 34, 58, 82, 106, 128, 46, 94], 54, 10, t1, ring=False)
    for t in ys:
        s.ring(t, 70, 54, YELLOW, r=70, dur=0.8)
    s.show(ss(s, "wag", 34), t0, t1, 70, 34, enter="bottom", hits=beats[::2], amp=2)


def g_storm(s, t0, t1):
    c = s.cues
    fr = c.w("frolicking", t0)
    beats = c.beats_in(fr, t1)
    g_ground(s, t0, t1)
    s.snow(t0, t1, count=20, speed=20)
    s.show(s.word("OUTSIDE", ICE, 2), c.w("outside", t0), fr, 70, 8, enter="pop", z=Z_WORD)
    dog, dogf = ss(s, "run", 30), ss(s, "run", 30, flip=True)
    # frolicking: bounding back and forth, a hop on each beat
    for k, b in enumerate(beats[:-1]):
        n = len(beats) - 1
        x0 = 20 + 100 * (k % 6) / 5 if (k // 6) % 2 == 0 else 120 - 100 * (k % 6) / 5
        x1 = 20 + 100 * ((k % 6) + 1) / 5 if (k // 6) % 2 == 0 else 120 - 100 * ((k % 6) + 1) / 5
        key = dog if (k // 6) % 2 == 0 else dogf
        m = (b + beats[k + 1]) / 2
        s.pic(key, b, m, x0, 38, to=((x0 + x1) / 2, 28))
        s.pic(key, m, beats[k + 1], (x0 + x1) / 2, 28, to=(x1, 38))
    s.show(s.word("FROLIC", PINK, 2), fr, t1, 70, 8, enter="pop", z=Z_WORD)
    s.twinkle(t0, t1, (WHITE, ICE), count=15)


def g_pride(s, t0, t1):
    c = s.cues
    pride, steam = c.w("pride", t0), c.w("steam", t0)
    g_ground(s, t0, t1)
    s.show(ss(s, "sit", 40), t0, t1, 36, 31, enter="left")
    s.show(s.word("MARKING", YELLOW, 2), c.w("marking", t0), pride, 92, 8, enter="pop", z=Z_WORD)
    s.show(s.emoji("👑", 16), pride, t1, 40, 6, enter="top", z=Z_FRONT)
    s.show(s.word("PRIDE", GOLD, 2), pride, steam, 92, 8, enter="pop", z=Z_WORD)
    s.ring(pride, 40, 10, GOLD, r=20)
    spots_on(s, [pride - 0.2], [92], 54, 18, t1)
    cloud = ss(s, "steam", 16)
    for k in range(3):
        a = steam + 0.4 * k
        s.glide(cloud, [(a, 92 + 6 * (k - 1), 48), (min(t1, a + 1.6), 92 + 10 * (k - 1), 18)], z=Z_FRONT)
    s.show(s.word("STEAM", WHITE, 2), steam, t1, 92, 8, enter="pop", z=Z_WORD)


def g_drawings(s, t0, t1):
    c = s.cues
    pup = c.w("puppy", t0)
    g_ground(s, t0, t1)
    s.show(ss(s, "run", 28), t0, pup - 0.6, 30, 36, enter="left", hits=c.beats_in(t0, pup), amp=2)
    s.show(scribble(s, 60, 8), c.w("reveals", t0), t1, 40, 53, enter="fade", enter_s=0.8, z=Z_SPOT)
    s.show(ss(s, "smiley", 40), pup, t1, 100, 26, enter="pop", hits=c.beats_in(pup, t1), amp=2)
    s.show(s.word("PUPPY ART", YELLOW, 2), pup, t1, 46, 8, enter="pop", z=Z_WORD)
    s.ring(pup, 100, 26, YELLOW, r=40)


def g_vangogh(s, t0, t1):
    c = s.cues
    ys = ywords(c, t0, t1)
    g_ground(s, t0, t1)
    s.show(s.emoji("🎨", 24), c.w("van", t0), t1, 22, 30, enter="pop", z=Z_FRONT)
    s.show(s.emoji("🖼️", 34), c.w("van", t0) + 0.3, t1, 112, 28, enter="pop")
    s.show(ss(s, "smiley", 22), c.w("van", t0) + 0.3, t1, 112, 28, enter="pop", z=Z_FRONT)
    s.show(s.word("VAN GOGH", GOLD, 2), c.w("van", t0), ys[0] if ys else t1, 66, 8, enter="pop", z=Z_WORD)
    for i, t in enumerate(ys):
        s.pic(s.word("YELLOW SNOW", YELLOW, 2), t, min(t + 0.6, t1), 66, 8 + 6 * (i % 2), z=Z_WORD)
    spots_on(s, ys, [50, 70, 90], 54, 12, t1)
    s.show(ss(s, "wag", 30), t0, t1, 66, 36, enter="bottom", hits=c.beats_in(t0, t1)[::2], amp=2)


def g_frosty(s, t0, t1):
    c = s.cues
    boy, doggy, fro = c.w("boy", t0), c.w("doggy", t0), c.w("frosty", t0)
    g_ground(s, t0, t1)
    s.show(ss(s, "snowman", 46), t0, fro + 0.4, 108, 30, enter="right")
    s.show(ss(s, "face", 40), t0, boy + 0.5, 36, 31, enter="pop", hits=c.beats_in(t0, boy), amp=2)
    s.show(s.word("HERE BOY", GOLD, 2), t0 + 0.5, doggy, 40, 6, enter="pop", z=Z_WORD)
    dog = ss(s, "run", 28)
    s.glide(dog, [(boy + 0.5, 36, 38), (fro - 0.5, 84, 38), (t1, 84, 38)])
    s.show(s.word("GOOD DOGGY", GREEN, 2), doggy, fro, 40, 6, enter="pop", z=Z_WORD)
    s.show(ss(s, "snowman_y", 46), fro + 0.4, t1, 108, 30, enter=None)
    s.show(s.word("NOT FROSTY", RED, 2), fro, t1, 54, 6, enter="pop", z=Z_WORD)
    s.ring(fro + 0.4, 108, 30, YELLOW, r=30)


def g_wag(s, t0, t1):
    c = s.cues
    g_ground(s, t0, t1)
    s.show(ss(s, "wag", 40), t0, t1, 70, 31, enter="pop", hits=c.beats_in(t0, t1), amp=3)
    s.show(s.word("HAPPY", PINK, 2), c.w("happy", t0), t1, 24, 10, enter="left", z=Z_WORD)
    s.show(s.word("WAG", GOLD, 2), c.w("wagging", t0), t1, 116, 10, enter="right", z=Z_WORD)


def g_sag(s, t0, t1):
    c = s.cues
    sag = c.w("sagging", t0)
    g_ground(s, t0, t1)
    s.show(ss(s, "snowman_y", 46), t0, sag, 70, 30, enter=None)
    s.pic(ss(s, "snowman_sag", 46), sag, t1, 70, 30, to=(72, 32))
    s.show(s.word("SAGGING", YELLOW, 2), sag, t1, 70, 6, enter="pop", z=Z_WORD)
    s.ring(sag, 70, 30, YELLOW, r=40)


def g_write(s, t0, t1):
    c = s.cues
    wr = c.w("write", t0)
    g_ground(s, t0, t1)
    s.show(ss(s, "sit", 40), t0, t1, 20, 31, enter="left")
    # writing in the snow, a letter at a time
    for i, ch in enumerate("BELOW"):
        s.show(s.word(ch, YELLOW, 2), wr + 0.25 * i, t1, 56 + 14 * i, 50, enter="pop", enter_s=0.15, z=Z_WORD)
    s.show(s.word("MORE TO WRITE", WHITE, 1), t0 + 0.2, t1, 84, 10, enter="pop", z=Z_WORD)


def g_chorus(s, t0, t1):
    c = s.cues
    ys = ywords(c, t0, t1)
    beats = c.beats_in(t0, t1)
    g_ground(s, t0, t1)
    for i, t in enumerate(ys):
        nxt = ys[i + 1] if i + 1 < len(ys) else t1
        s.pic(s.word("YELLOW", YELLOW, 3), t, nxt, 70, 12, z=Z_WORD)
        s.pic(s.word("SNOW", WHITE, 3), t + 0.5, nxt, 70, 30, z=Z_WORD)
        s.ring(t, 70, 20, YELLOW, r=70, dur=0.8)
    spots_on(s, beats[::2], [10, 30, 50, 90, 110, 130, 20, 120], 54, 10, t1, ring=False)
    s.show(ss(s, "santa", 34), t0, t1, 128, 36, enter="right", hits=beats[::2], amp=2)
    bar_sweeps(s, t0, t1, (YELLOW, WHITE))


def g_patches(s, t0, t1):
    c = s.cues
    pat = c.w("patches", t0)
    g_ground(s, t0, t1)
    beats = c.beats_in(pat, t1)
    spots_on(s, beats, [8, 26, 44, 62, 80, 98, 116, 132, 17, 53, 89, 125], 54, 7, t1, ring=False)
    s.show(s.word("LITTLE PATCHES", YELLOW, 2), pat, t1, 70, 10, enter="pop", z=Z_WORD)
    s.show(ss(s, "wag", 30), t0, t1, 70, 34, enter="bottom", hits=c.beats_in(t0, t1)[::2], amp=2)


def g_finale(s, t0, t1):
    c = s.cues
    dont = c.w("don't", t0)
    end = t1 - 0.2
    g_ground(s, t0, end)
    s.show(spot(s, 30), t0, end, 70, 52, enter="pop", z=Z_SPOT)
    s.show(s.emoji("🚫", 36), dont, end, 70, 40, enter="pop", z=Z_FRONT)
    s.ring(dont, 70, 40, RED, r=50)
    s.show(s.word("DONT GO THERE", RED, 2), t0 + 0.2, dont + 2.0, 70, 8, enter="pop", z=Z_WORD)
    s.show(s.word("MERRY XMAS", GREEN, 2), dont + 2.0, end, 70, 8, enter="pop", z=Z_WORD)
    s.show(ss(s, "santa", 40), dont + 1.0, end, 18, 31, enter="left", hits=c.beats_in(dont + 1.5, end - 1)[::2], amp=2)
    s.show(ss(s, "snowman", 40), dont + 1.0, end, 122, 31, enter="right")
    flake_rows(s, t0, t1, 10)
    s.twinkle(t0, t1, XMAS, count=12, fade=1.5)


GARAGE = dict(intro=g_intro, weather=g_weather, noplace=g_noplace, sniff=g_sniff, everywhere=g_everywhere,
              storm=g_storm, pride=g_pride, drawings=g_drawings, vangogh=g_vangogh, frosty=g_frosty, wag=g_wag,
              sag=g_sag, write=g_write, chorus=g_chorus, patches=g_patches, finale=g_finale)


# ================================================================ the two windows as one snowy yard

def wins(s):
    return tuple(s.center(m)[0] for m in s.places)  # the two windows, in --model order


WY = 24


def w_ground(s, t0, t1, enter=None):
    s.show(ground(s, s.W, 12), t0, t1, s.W / 2, s.H - 6, enter=enter, enter_s=1.0, z=Z_GROUND)


def w_intro(s, t0, t1):
    L, C = wins(s)
    flake_rows(s, 0.2, t1, 8)
    w_ground(s, 0.3, t1, enter="bottom")
    s.show(ss(s, "sit", 34), 4.0, t1, L, 26, enter="left", enter_s=1.5)


def w_weather(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    fr = c.w("frightening", t0)
    w_ground(s, t0, t1)
    s.show(ss(s, "sit", 34), t0, fr, L, 26, enter=None)
    s.show(s.emoji("🌨️", 28), t0 + 0.3, t1, C, 20, enter="pop")
    s.glide(ss(s, "run", 24), [(fr, L, 30), (t1, C, 30)])
    s.ring(fr, L, 26, YELLOW, r=26)
    flake_rows(s, t0, t1, 8)


def w_noplace(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    ys = ywords(c, t0, t1)
    w_ground(s, t0, t1)
    s.show(ss(s, "sit", 34), t0, t1, C, 26, enter=None)
    spots_on(s, ys, [L - 10, L + 10, L], s.H - 6, 10, t1)
    for i, t in enumerate(ys):
        s.pic(s.word("YELLOW", YELLOW, 1), t, min(t + 0.6, t1), L, 10, z=Z_WORD)


def w_sniff(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    w_ground(s, t0, t1)
    dog, dogf = ss(s, "run", 22), ss(s, "run", 22, flip=True)
    half = (t0 + t1) / 2
    # sniffing along the yard, behind the wall and back
    s.glide(dog, [(t0, -24, 32), (half, s.W + 24, 32)])
    s.glide(dogf, [(half, s.W + 24, 32), (t1, -24, 32)])
    L, C = wins(s)
    spots_on(s, beats[2::4], [L - 12, C + 10, L + 8, C - 8], s.H - 6, 7, t1, ring=False)


def w_everywhere(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    w_ground(s, t0, t1)
    spots_on(s, beats[::2], [L - 12, C + 12, L + 6, C - 6, L, C], s.H - 6, 8, t1, ring=False)
    s.show(s.emoji("👀", 26), t0, t1, L, WY, enter="pop", hits=beats[::2], amp=2)
    s.show(ss(s, "wag", 30), t0 + 0.3, t1, C, 26, enter="pop", hits=beats[1::2], amp=2)


def w_storm(s, t0, t1):
    c = s.cues
    fr = c.w("frolicking", t0)
    w_ground(s, t0, t1)
    s.snow(t0, t1, count=18, speed=20)
    dog, dogf = ss(s, "run", 24), ss(s, "run", 24, flip=True)
    k, a = 0, fr
    while a + 1.8 < t1:
        rt = k % 2 == 0
        x0, x1 = (-20, s.W + 20) if rt else (s.W + 20, -20)
        s.glide(dog if rt else dogf, [(a, x0, 30), (a + 1.8, x1, 30)])
        k, a = k + 1, a + 2.0


def w_pride(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    pride, steam = c.w("pride", t0), c.w("steam", t0)
    w_ground(s, t0, t1)
    s.show(ss(s, "sit", 34), t0, t1, L, 26, enter="left")
    s.show(s.emoji("👑", 14), pride, t1, L, 6, enter="top", z=Z_FRONT)
    spots_on(s, [pride - 0.2], [C], s.H - 6, 16, t1)
    cloud = ss(s, "steam", 14)
    for k in range(3):
        a = steam + 0.4 * k
        s.glide(cloud, [(a, C + 6 * (k - 1), 40), (min(t1, a + 1.6), C + 8 * (k - 1), 10)], z=Z_FRONT)


def w_drawings(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    pup = c.w("puppy", t0)
    w_ground(s, t0, t1)
    # one long squiggle across the whole yard, behind the wall
    s.show(scribble(s, s.W, 7), c.w("reveals", t0), t1, s.W / 2, s.H - 6, enter="fade", enter_s=0.8, z=Z_SPOT)
    s.show(ss(s, "smiley", 34), pup, t1, C, 22, enter="pop", hits=c.beats_in(pup, t1), amp=2)
    s.show(ss(s, "run", 22), t0, t1, L, 30, enter="left")


def w_vangogh(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    ys = ywords(c, t0, t1)
    w_ground(s, t0, t1)
    s.show(s.emoji("🎨", 26), c.w("van", t0), t1, L, WY, enter="pop")
    s.show(s.emoji("🖼️", 32), c.w("van", t0) + 0.3, t1, C, WY, enter="pop")
    s.show(ss(s, "smiley", 20), c.w("van", t0) + 0.3, t1, C, WY, enter="pop", z=Z_FRONT)
    spots_on(s, ys, [L - 8, L + 8, L], s.H - 6, 9, t1)


def w_frosty(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    boy, fro = c.w("boy", t0), c.w("frosty", t0)
    w_ground(s, t0, t1)
    s.show(ss(s, "snowman", 38), t0, fro + 0.4, C, 24, enter="right")
    s.show(ss(s, "face", 34), t0, boy + 0.5, L, 26, enter="pop")
    # the dog runs behind the wall to Frosty
    s.glide(ss(s, "run", 22), [(boy + 0.5, L, 32), (fro - 0.3, C - 12, 32), (t1, C - 12, 32)], z=Z_FRONT)
    s.show(ss(s, "snowman_y", 38), fro + 0.4, t1, C, 24, enter=None)
    s.show(s.emoji("😱", 26), fro, t1, L, WY, enter="pop")
    s.ring(fro + 0.4, C, 24, YELLOW, r=26)


def w_wag(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    w_ground(s, t0, t1)
    s.show(ss(s, "wag", 32), t0, t1, L, 26, enter="pop", hits=beats, amp=3)
    s.show(s.emoji("😄", 26), t0 + 0.2, t1, C, WY, enter="pop", hits=beats[1::2], amp=2)


def w_sag(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    sag = c.w("sagging", t0)
    w_ground(s, t0, t1)
    s.show(ss(s, "snowman_y", 38), t0, sag, C, 24, enter=None)
    s.pic(ss(s, "snowman_sag", 38), sag, t1, C, 24, to=(C + 2, 26))
    s.show(s.emoji("😬", 26), t0, t1, L, WY, enter="pop")


def w_write(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    wr = c.w("write", t0)
    w_ground(s, t0, t1)
    s.show(ss(s, "sit", 34), t0, t1, L, 26, enter=None)
    for i, ch in enumerate("BELOW"):
        s.show(s.word(ch, YELLOW, 1), wr + 0.25 * i, t1, C - 12 + 6 * i, s.H - 6, enter="pop", enter_s=0.15,
               z=Z_WORD)


def w_chorus(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    ys = ywords(c, t0, t1)
    w_ground(s, t0, t1)
    for i, t in enumerate(ys):
        nxt = ys[i + 1] if i + 1 < len(ys) else t1
        s.pic(s.word("YELLOW", YELLOW, 1), t, nxt, L, 14, z=Z_WORD)
        s.pic(s.word("SNOW", WHITE, 2), t + 0.5, nxt, C, 14, z=Z_WORD)
        s.ring(t, L, 20, YELLOW, r=26, dur=0.6)
    spots_on(s, c.beats_in(t0, t1)[::2], [L - 12, C + 12, L + 10, C - 10, L, C], s.H - 6, 8, t1, ring=False)


def w_patches(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    w_ground(s, t0, t1)
    spots_on(s, c.beats_in(c.w("patches", t0), t1), [L - 14, L - 4, L + 6, L + 14, C - 14, C - 4, C + 6, C + 14],
             s.H - 6, 5, t1, ring=False)
    s.show(ss(s, "wag", 28), t0, t1, C, 24, enter="pop", hits=c.beats_in(t0, t1)[::2], amp=2)


def w_finale(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    dont = c.w("don't", t0)
    end = t1 - 0.2
    w_ground(s, t0, end)
    s.show(spot(s, 22), t0, end, L, s.H - 6, enter="pop", z=Z_SPOT)
    s.show(s.emoji("🚫", 30), dont, end, L, 30, enter="pop", z=Z_FRONT)
    s.ring(dont, L, 30, RED, r=28)
    s.show(ss(s, "santa", 34), dont + 1.0, end, C, 26, enter="right", hits=c.beats_in(dont + 1.5, end - 1)[::2], amp=2)
    flake_rows(s, t0, t1, 8)
    s.twinkle(t0, t1, XMAS, count=10, fade=1.5)


WINDOWS = dict(intro=w_intro, weather=w_weather, noplace=w_noplace, sniff=w_sniff, everywhere=w_everywhere,
               storm=w_storm, pride=w_pride, drawings=w_drawings, vangogh=w_vangogh, frosty=w_frosty, wag=w_wag,
               sag=w_sag, write=w_write, chorus=w_chorus, patches=w_patches, finale=w_finale)


# ================================================================ 200x42 matrix: 8 bushes, 25 px each

def bx(i):
    return 12.5 + 25 * i


BY = 20


def b_ground(s, t0, t1, enter=None):
    s.show(ground(s, 200, 8), t0, t1, 100, 38, enter=enter, enter_s=1.0, z=Z_GROUND)


def row(s, keys, t0, t1, *, hits=None, enter="pop", stagger=0.06, amp=3, y=BY, z=Z_PIC):
    for i in range(8):
        h = hits[i % 2::2] if hits else ()
        s.show(keys[i % len(keys)], t0 + stagger * i, t1, bx(i), y, enter=enter, hits=h, amp=amp, z=z)


def b_intro(s, t0, t1):
    b_ground(s, 0.3, t1, enter="bottom")
    flake_rows(s, 0.2, t1, 6)
    row(s, [ss(s, "sit", 30)], 4.0, t1, enter="bottom", stagger=0.3)


def b_weather(s, t0, t1):
    c = s.cues
    fr = c.w("frightening", t0)
    b_ground(s, t0, t1)
    row(s, [s.emoji("❄️", 20)], t0, fr, enter="top")
    row(s, [ss(s, "run", 22)], fr, t1, hits=c.beats_in(fr, t1), enter="pop")
    flake_rows(s, t0, t1, 6)


def b_noplace(s, t0, t1):
    c = s.cues
    ys = ywords(c, t0, t1)
    b_ground(s, t0, t1)
    row(s, [ss(s, "sit", 30)], t0, ys[0] if ys else t1, enter=None)
    for k, t in enumerate(ys):
        for i in range(k % 2, 8, 2):
            s.show(spot(s, 12), t + 0.04 * i, t1, bx(i), 37, enter="pop", enter_s=0.2, z=Z_SPOT)
    for i, ch in enumerate("YELLOW"):
        s.show(s.word(ch, YELLOW, 3), ys[0] + 0.1 * i if ys else t0, t1, bx(i + 1), BY - 2, enter="pop",
               enter_s=0.15, z=Z_WORD)


def b_sniff(s, t0, t1):
    c = s.cues
    b_ground(s, t0, t1)
    dog, dogf = ss(s, "run", 22), ss(s, "run", 22, flip=True)
    half = (t0 + t1) / 2
    s.glide(dog, [(t0, -20, 26), (half, 220, 26)])
    s.glide(dogf, [(half, 220, 26), (t1, -20, 26)])
    beats = c.beats_in(t0, t1)[2::4]
    for k, t in enumerate(beats):
        s.show(spot(s, 8), t, t1, bx([1, 6, 3, 4, 0, 7, 2, 5][k % 8]), 37, enter="pop", enter_s=0.2, z=Z_SPOT)


def b_everywhere(s, t0, t1):
    c = s.cues
    b_ground(s, t0, t1)
    beats = c.beats_in(t0, t1)
    for k, t in enumerate(beats[:16]):
        i = [0, 7, 3, 4, 1, 6, 2, 5][k % 8]
        s.show(spot(s, 10 if k < 8 else 6), t, t1, bx(i) + (4 if k >= 8 else 0), 37, enter="pop", enter_s=0.2,
               z=Z_SPOT)
    row(s, [s.emoji("👀", 18)], t0, t1, hits=beats, enter="pop", y=16)


def b_storm(s, t0, t1):
    c = s.cues
    fr = c.w("frolicking", t0)
    b_ground(s, t0, t1)
    s.snow(t0, t1, count=14, speed=20)
    beats = c.beats_in(fr, t1)
    dog = ss(s, "run", 24)
    path = list(range(8)) + list(range(6, 0, -1))
    for k, b in enumerate(beats[:-1]):
        i, j = path[k % len(path)], path[(k + 1) % len(path)]
        m = (b + beats[k + 1]) / 2
        s.pic(dog, b, m, bx(i), 24, to=((bx(i) + bx(j)) / 2, 12))
        s.pic(dog, m, beats[k + 1], (bx(i) + bx(j)) / 2, 12, to=(bx(j), 24))


def b_pride(s, t0, t1):
    c = s.cues
    pride, steam = c.w("pride", t0), c.w("steam", t0)
    b_ground(s, t0, t1)
    row(s, [ss(s, "sit", 30), s.emoji("👑", 16)], t0, steam, enter="bottom")
    row(s, [ss(s, "steam", 14)], steam, t1, enter="bottom", y=24, stagger=0.1)
    for i in range(8):
        s.show(spot(s, 12), pride + 0.05 * i, t1, bx(i), 37, enter="pop", enter_s=0.2, z=Z_SPOT)


def b_drawings(s, t0, t1):
    c = s.cues
    pup = c.w("puppy", t0)
    b_ground(s, t0, t1)
    s.show(scribble(s, 200, 6), c.w("reveals", t0), t1, 100, 37, enter="fade", enter_s=0.8, z=Z_SPOT)
    row(s, [ss(s, "smiley", 26)], pup, t1, hits=c.beats_in(pup, t1), enter="pop")


def b_vangogh(s, t0, t1):
    c = s.cues
    van = c.w("van", t0)
    b_ground(s, t0, t1)
    row(s, [s.emoji("🎨", 20), ss(s, "smiley", 22)], van, t1, enter="pop", hits=c.beats_in(van, t1))


def b_frosty(s, t0, t1):
    c = s.cues
    fro = c.w("frosty", t0)
    b_ground(s, t0, t1)
    row(s, [ss(s, "face", 30)], t0, fro - 1.0, enter="pop", hits=c.beats_in(t0, fro - 1))
    row(s, [ss(s, "snowman", 32)], fro - 1.0, fro + 0.4, enter="bottom")
    row(s, [ss(s, "snowman_y", 32)], fro + 0.4, t1, enter=None, stagger=0.05)


def b_wag(s, t0, t1):
    c = s.cues
    b_ground(s, t0, t1)
    row(s, [ss(s, "wag", 28)], t0, t1, hits=c.beats_in(t0, t1), enter="pop")


def b_sag(s, t0, t1):
    c = s.cues
    sag = c.w("sagging", t0)
    b_ground(s, t0, t1)
    row(s, [ss(s, "snowman_y", 32)], t0, sag, enter=None, stagger=0)
    row(s, [ss(s, "snowman_sag", 32)], sag, t1, enter=None, stagger=0.06)


def b_write(s, t0, t1):
    c = s.cues
    wr = c.w("write", t0)
    b_ground(s, t0, t1)
    for i, ch in enumerate("BELOW"):
        s.show(s.word(ch, YELLOW, 4), wr + 0.25 * i, t1, bx(i + 1) + 12, 20, enter="pop", enter_s=0.15, z=Z_WORD)


def b_chorus(s, t0, t1):
    c = s.cues
    ys = ywords(c, t0, t1)
    b_ground(s, t0, t1)
    for k, t in enumerate(ys):
        nxt = ys[k + 1] if k + 1 < len(ys) else t1
        word = "YELLOW" if k % 2 == 0 else "SNOW"
        for i, ch in enumerate(word):
            j = i + (1 if word == "YELLOW" else 2)
            s.pic(s.word(ch, YELLOW if word == "YELLOW" else WHITE, 4), t + 0.06 * i, nxt, bx(j), 18, z=Z_WORD)
    for k, t in enumerate(c.beats_in(t0, t1)[::2]):
        s.show(spot(s, 8), t, t1, bx(k % 8) + (5 if (k // 8) % 2 else -5), 37, enter="pop", enter_s=0.2, z=Z_SPOT)


def b_patches(s, t0, t1):
    c = s.cues
    b_ground(s, t0, t1)
    for k, t in enumerate(c.beats_in(c.w("patches", t0), t1)):
        s.show(spot(s, 6), t, t1, 6 + (k * 37) % 190, 37, enter="pop", enter_s=0.2, z=Z_SPOT)
    row(s, [ss(s, "wag", 28)], t0, t1, enter="bottom", hits=c.beats_in(t0, t1))


def b_finale(s, t0, t1):
    c = s.cues
    dont = c.w("don't", t0)
    end = t1 - 0.2
    b_ground(s, t0, end)
    row(s, [spot(s, 16)], t0, end, enter="pop", y=36, z=Z_SPOT)
    row(s, [s.emoji("🚫", 24)], dont, dont + 2.5, enter="pop", z=Z_FRONT)
    row(s, [ss(s, "santa", 30), ss(s, "snowman", 32)], dont + 2.5, end, enter="pop",
        hits=c.beats_in(dont + 3, end - 1))
    s.twinkle(t0, t1, XMAS, count=10, fade=1.5)


BUSHES = dict(intro=b_intro, weather=b_weather, noplace=b_noplace, sniff=b_sniff, everywhere=b_everywhere,
              storm=b_storm, pride=b_pride, drawings=b_drawings, vangogh=b_vangogh, frosty=b_frosty, wag=b_wag,
              sag=b_sag, write=b_write, chorus=b_chorus, patches=b_patches, finale=b_finale)
