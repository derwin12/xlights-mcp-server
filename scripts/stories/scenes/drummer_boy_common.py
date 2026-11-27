"""Little Drummer Boy matrix scenes, shared plan for the garage, the two windows (one stage) and the bushes.

The characters are the sequence's own SuperStar MegaTree pictures (the drummer boy's drumming poses, Mary, the
robed King, the manger scene), loaded from the .xsq at build time and widened x3 for square matrix pixels (see
ss()). Nothing from that import is copied into this repo.
Words: faster-whisper (stories/lyrics/drummer_boy.json; it misses whole verses, so some scenes are placed at fixed
times that match the tree's story). Beats: librosa (drummer_boy_beats.json, ~89 BPM). Drum hits: the sequence's
own unlabelled "New Timing" track, used for rings.
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
from morph_backdrop import backdrop, pattern_sweeps  # noqa: E402,F401
from matrix_scenes import Cues  # noqa: E402
from rockin_common import BLUE, GOLD, ICE, PINK, RED, WHITE, Z_BACK, Z_FRONT, Z_WORD  # noqa: E402,F401

LYRICS = HERE.parent / "lyrics"
NIGHT, AMBER, BROWN, STRAW = (20, 30, 110), (255, 140, 0), (110, 60, 20), (220, 180, 60)
WARM = (GOLD, RED, BLUE)

SS_X = 3.0
SS = {  # media path in the sequence -> what it shows
    "drum1": "DrummerBoyImages/DrummerBoy_182.png",  # the drummer boy, sticks in various positions
    "drum2": "DrummerBoyImages/DrummerBoy_183.png",
    "drum3": "DrummerBoyImages/DrummerBoy_184.png",
    "drum4": "DrummerBoyImages/DrummerBoy_185.png",
    "drum5": "DrummerBoyImages/DrummerBoy_186.png",
    "boy": "DrummerBoyImages/DrummerBoy_120.png",    # standing with the drum
    "mary": "DrummerBoyImages/DrummerBoy_511.png",   # Mary in a blue glow
    "king": "DrummerBoyImages/DrummerBoy_122.png",   # robed, bearded figure (the King)
    "manger": "DrummerBoyImages/DrummerBoy_593.png", # stable and manger
}
DRUM = ["drum1", "drum2", "drum3", "drum4", "drum5"]
_SS = {"xsq": None, "imgs": None}


def cues(xsq):
    _SS["xsq"] = xsq
    root = ET.parse(xsq).getroot()
    dur = float(root.findtext("head/sequenceDuration"))
    c = Cues.from_files(LYRICS / "drummer_boy.json", LYRICS / "drummer_boy_beats.json", dur)
    hits = []
    for e in root.find("ElementEffects"):
        if e.get("type") == "timing" and e.get("name") == "New Timing":
            hits = [int(f.get("startTime")) / 1000 for f in e.find("EffectLayer")]
    c.hits = hits
    return c


def ss(s, name, h):
    """A SuperStar picture h LEDs tall, aspect corrected for the tree's tall pixels."""
    from PIL import Image
    key = f"db_{name}_{h}"
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
    return s.image(key, im)


def drums(s, h):
    return [ss(s, n, h) for n in DRUM]


def hits_in(c, t0, t1, gap=0.3):
    out = []
    for t in c.hits:
        if t0 <= t < t1 and (not out or t - out[-1] >= gap):
            out.append(t)
    return out


def plan(c):
    w = c.w
    t = [
        ("intro", 0.0),
        ("come", w("count") - 0.2),
        ("king", w("newborn") - 0.8),
        ("gifts", w("finest") - 0.8),
        ("before", w("late") - 0.8),
        ("honor", w("honor") - 2.0),
        ("star", w("come", 61) + 1.5),
        ("baby", w("little") - 0.6),
        ("poor", w("poor") - 1.6),
        ("nogift", w("gift", w("poor")) - 1.6),  # not the earlier "gifts"
        ("play", w("fit") - 1.0),
        ("mary", 120.3),
        ("ox", 128.0),
        ("best", w("played") - 1.0),
        ("smile", w("smiled") - 1.5),
        ("drumming", 162.0),
        ("finale", 191.0),
    ]
    return [(n, t0, t[k + 1][1] if k + 1 < len(t) else c.duration) for k, (n, t0) in enumerate(t)]


def run(s, scenes):
    for name, t0, t1 in plan(s.cues):
        backdrop(s, t0, t1)
        fn = scenes.get(name)
        if fn:
            fn(s, t0, t1)


# ---------------------------------------------------------------- drawn props

def star_img(s, px):
    def draw(d, im):
        import math
        c = px / 2
        pts = []
        for k in range(10):
            r = c - 0.5 if k % 2 == 0 else c * 0.42
            a = math.radians(-90 + 36 * k)
            pts.append((c + r * math.cos(a), c + r * math.sin(a)))
        d.polygon(pts, fill=(255, 220, 60, 255))
        d.ellipse([c - px * 0.12, c - px * 0.12, c + px * 0.12, c + px * 0.12], fill=(255, 255, 220, 255))
    return s.drawn(f"star_{px}", px, px, draw)


def stable_img(s, w, h):
    """A simple wooden stable: peaked roof, posts, straw floor and a manger."""
    def draw(d, im):
        d.polygon([(0, h * 0.35), (w / 2, 0), (w - 1, h * 0.35), (w - 1, h * 0.45), (w / 2, h * 0.1),
                   (0, h * 0.45)], fill=BROWN + (255,))
        for x in (2, w - 4):
            d.rectangle([x, h * 0.4, x + 2, h - 1], fill=BROWN + (255,))
        d.rectangle([0, h - 4, w - 1, h - 1], fill=STRAW + (255,))
        mx = w / 2
        d.polygon([(mx - w * 0.18, h * 0.72), (mx + w * 0.18, h * 0.72), (mx + w * 0.12, h - 5),
                   (mx - w * 0.12, h - 5)], fill=(150, 90, 30, 255))
        d.rectangle([mx - w * 0.15, h * 0.68, mx + w * 0.15, h * 0.73], fill=STRAW + (255,))
    return s.drawn(f"stable_{w}_{h}", w, h, draw)


def glow(s, px, color=(255, 220, 120)):
    def draw(d, im):
        d.ellipse([0, 0, px - 1, px - 1], fill=color + (255,))
    return s.drawn(f"glow_{px}_{color[0]}", px, px, draw)


def bar_sweeps(s, t0, t1, colors=WARM, every=1):
    """SuperStar-style Morph pattern groups on every other beat (none while the tree's are echoed)."""
    pattern_sweeps(s, t0, t1, colors, every)


def drum_roll(s, t0, t1, x, y, h, *, every=1, offset=0):
    """The drummer boy playing: swap his poses on the beats."""
    beats = s.cues.beats_in(t0, t1)[offset::every]
    if beats:
        s.flash(drums(s, h), [t0] + beats, x, y, end=t1)
    else:
        s.pic(ss(s, "drum1", h), t0, t1, x, y)


# ================================================================ 140x60 matrix (the garage)

GX, GY = 70, 31


def g_intro(s, t0, t1):
    c = s.cues
    s.twinkle(0.3, t1, (WHITE, GOLD), count=14, fade=2.0)
    star = star_img(s, 18)
    s.glide(star, [(2.0, -12, 30), (t1 - 1.0, GX, 10), (t1, GX, 10)], z=Z_FRONT)
    for i, h in enumerate(hits_in(c, 0.5, t1, gap=1.3)):
        s.ring(h, GX if i % 2 else 30, 50, (GOLD, RED, BLUE)[i % 3], r=16, dur=0.5)


def g_come(s, t0, t1):
    c = s.cues
    s.show(star_img(s, 18), t0, t1, GX, 10, enter=None, hits=c.beats_in(t0, t1)[::2], amp=1, z=Z_FRONT)
    s.glide(ss(s, "boy", 52), [(t0, -12, GY), (t1, 34, GY)])
    s.show(s.word("COME", GOLD, 2), c.w("count", t0) + 0.2, t1, 100, 30, enter="pop", z=Z_WORD)
    s.twinkle(t0, t1, (WHITE, GOLD), count=10)


def g_king(s, t0, t1):
    c = s.cues
    king = c.w("king", t0)
    s.show(star_img(s, 18), t0, t1, GX, 10, enter=None, z=Z_FRONT)
    s.show(ss(s, "boy", 52), t0, t1, 34, GY, enter=None)
    s.show(s.word("NEWBORN", WHITE, 2), c.w("newborn", t0), king, 100, 22, enter="pop", z=Z_WORD)
    s.show(s.emoji("👑", 26), king, t1, 104, 34, enter="top", hits=c.beats_in(king, t1)[::2], amp=2)
    s.show(s.word("KING", GOLD, 2), king, t1, 104, 52, enter="pop", z=Z_WORD)
    s.ring(king, 104, 34, GOLD, r=34)


def g_gifts(s, t0, t1):
    c = s.cues
    gifts = c.w("gifts", t0)
    for k, (x, e) in enumerate(((26, "🎁"), (70, "🏺"), (114, "🎁"))):
        s.show(s.emoji(e, 24, flip=k == 2), gifts + 0.3 * k, t1, x, 40, enter="top", enter_s=0.4)
        s.ring(gifts + 0.3 * k + 0.4, x, 40, GOLD, r=18, dur=0.5)
    s.show(s.word("FINEST GIFTS", GOLD, 2), c.w("finest", t0), t1, GX, 8, enter="pop", z=Z_WORD)
    s.twinkle(gifts, t1, (GOLD, WHITE), count=14, fade=0.3)


def g_before(s, t0, t1):
    c = s.cues
    king = c.w("king", t0)
    s.show(ss(s, "king", 56), t0, t1, GX, 31, enter="fade", enter_s=1.0, hits=c.beats_in(king, t1)[::4], amp=1)
    s.show(s.emoji("🎁", 18), t0, t1, 30, 50, enter="left")
    s.show(s.emoji("🏺", 18), t0 + 0.3, t1, 110, 50, enter="right")
    s.ring(king, GX, 31, GOLD, r=50, dur=1.0)
    s.twinkle(t0, t1, (GOLD, WHITE), count=12)
    bar_sweeps(s, king, t1, (GOLD, WHITE), every=2)


def g_honor(s, t0, t1):
    c = s.cues
    honor = c.w("honor", t0)
    s.show(ss(s, "boy", 52), t0, t1, 30, GY, enter="left")
    s.show(s.word("HONOR", GOLD, 2), honor, t1, 96, 18, enter="pop", z=Z_WORD)
    s.show(s.emoji("🥁", 24), honor + 0.5, t1, 96, 42, enter="pop", hits=c.beats_in(honor, t1), amp=2)
    for i, h in enumerate(hits_in(c, honor, t1, gap=0.6)):
        s.ring(h, 96, 42, WARM[i % 3], r=20, dur=0.4)


def g_star(s, t0, t1):
    """Instrumental: the star leads across the night sky to the stable."""
    c = s.cues
    star = star_img(s, 20)
    s.glide(star, [(t0, -14, 12), (t0 + (t1 - t0) * 0.7, 100, 10), (t1, 100, 10)], z=Z_FRONT)
    s.show(stable_img(s, 50, 40), t0 + 2.0, t1, 100, 40, enter="bottom", enter_s=1.5, z=Z_BACK)
    s.twinkle(t0, t1, (WHITE, ICE, GOLD), count=18, fade=1.0)
    bar_sweeps(s, t0, t1, (NIGHT, BLUE), every=2)
    s.ring(t0 + (t1 - t0) * 0.7, 100, 10, GOLD, r=30, dur=1.0)


def g_baby(s, t0, t1):
    c = s.cues
    baby = c.w("baby", t0)
    s.show(ss(s, "manger", 54), t0, t1, GX, 32, enter="fade", enter_s=0.8)
    s.show(star_img(s, 14), t0, t1, GX, 6, enter="top", z=Z_FRONT)
    s.show(s.word("BABY", ICE, 2), baby, t1, 24, 30, enter="left", z=Z_WORD)
    s.ring(baby, GX, 40, GOLD, r=40, dur=1.0)


def g_poor(s, t0, t1):
    c = s.cues
    boy = c.w("boy", t0)
    s.show(ss(s, "boy", 54), t0, t1, GX, 32, enter="pop", hits=c.beats_in(t0, t1)[::2], amp=1)
    s.show(s.word("POOR", WHITE, 2), c.w("poor", t0), t1, 26, 26, enter="left", z=Z_WORD)
    s.show(s.word("BOY", GOLD, 2), boy, t1, 114, 26, enter="right", z=Z_WORD)
    s.ring(boy, GX, 32, AMBER, r=34)


def g_nogift(s, t0, t1):
    c = s.cues
    gift = c.w("gift", t0)
    s.show(ss(s, "boy", 54), t0, t1, 30, 32, enter=None)
    s.show(s.emoji("🎁", 30), t0 + 0.3, t1, 100, 34, enter="pop")
    s.show(s.emoji("🚫", 36), gift, t1, 100, 34, enter="pop", z=Z_FRONT)
    s.show(s.word("NO GIFT", RED, 2), gift, t1, 100, 8, enter="pop", z=Z_WORD)
    s.ring(gift, 100, 34, RED, r=30)


def g_play(s, t0, t1):
    c = s.cues
    drum_roll(s, t0, t1, GX, 32, 54)
    s.show(s.word("PLAY", GOLD, 2), t0 + 0.5, t1, 24, 12, enter="left", z=Z_WORD)
    s.show(s.emoji("🥁", 22), t0 + 0.5, t1, 116, 44, enter="right", hits=c.beats_in(t0, t1), amp=2)
    for i, h in enumerate(hits_in(c, t0, t1, gap=0.6)):
        s.ring(h, GX, 46, WARM[i % 3], r=26, dur=0.45)
    bar_sweeps(s, t0, t1, WARM, every=2)


def g_mary(s, t0, t1):
    c = s.cues
    s.show(ss(s, "mary", 54), t0, t1, 36, 32, enter="fade", enter_s=1.0, hits=c.beats_in(t0 + 2, t1)[::4], amp=1)
    s.show(glow(s, 50, (60, 120, 255)), t0, t1, 36, 32, enter="fade", enter_s=1.5, z=Z_BACK - 1)
    drum_roll(s, t0, t1, 104, 32, 54, every=2)
    s.ring(t0 + 1.0, 36, 32, BLUE, r=40, dur=1.0)
    s.twinkle(t0, t1, (ICE, WHITE), count=12)


def g_ox(s, t0, t1):
    """The ox and lamb keep time: they bob on every beat beside the drummer."""
    c = s.cues
    beats = c.beats_in(t0, t1)
    s.show(s.emoji("🐂", 30), t0, t1, 22, 42, enter="left", hits=beats[0::2], amp=3)
    s.show(s.emoji("🐑", 26, flip=True), t0 + 0.3, t1, 118, 44, enter="right", hits=beats[1::2], amp=3)
    drum_roll(s, t0, t1, GX, 32, 54)
    s.show(s.word("KEEP TIME", GOLD, 1), t0 + 1.0, t1, GX, 4, enter="pop", z=Z_WORD)
    for i, b in enumerate(beats):
        s.ring(b, 22 if i % 2 == 0 else 118, 56, (GOLD, AMBER)[i % 2], r=14, dur=0.35)


def g_best(s, t0, t1):
    c = s.cues
    best = c.w("best", t0)
    drum_roll(s, t0, t1, GX, 32, 56)
    s.show(s.word("MY BEST", GOLD, 2), best, t1, 112, 30, enter="right", z=Z_WORD)
    for i, h in enumerate(hits_in(c, t0, t1, gap=0.45)):
        s.ring(h, GX, 48, WARM[i % 3], r=40, dur=0.5)
    s.twinkle(best, t1, (GOLD, RED, WHITE), count=20, steps=15, fade=0.3)


def g_smile(s, t0, t1):
    c = s.cues
    smiled = c.w("smiled", t0)
    s.show(ss(s, "king", 56), t0, t1, 36, 31, enter="fade", enter_s=1.0)
    s.show(ss(s, "boy", 52), t0, t1, 108, 31, enter="right")
    s.show(s.emoji("😊", 22), smiled, t1, 72, 20, enter="pop", z=Z_FRONT)
    s.show(s.emoji("❤️", 16), smiled + 0.8, t1, 72, 44, enter="pop", hits=c.beats_in(smiled + 1, t1), amp=2)
    s.ring(smiled, 36, 31, GOLD, r=60, dur=1.2)
    s.twinkle(smiled, t1, (GOLD, WHITE, PINK), count=20, fade=0.5)


def g_drumming(s, t0, t1):
    """The long drum section: the boy plays, rings on every hit, colours cycle by bar."""
    c = s.cues
    drum_roll(s, t0, t1, GX, 32, 56)
    for x, flip in ((22, False), (118, True)):
        s.show(s.emoji("🥁", 24, flip=flip), t0 + 0.4, t1, x, 40, enter="pop",
               hits=c.beats_in(t0, t1)[int(flip)::2], amp=3)
    for i, h in enumerate(hits_in(c, t0, t1, gap=0.4)):
        s.ring(h, 22 if i % 2 == 0 else 118, 40, WARM[i % 3], r=22, dur=0.4)
    bar_sweeps(s, t0, t1, (RED, GOLD, BLUE, (0, 170, 60)))
    s.twinkle(t0, t1, (GOLD, WHITE), count=10)


def g_finale(s, t0, t1):
    end = t1 - 0.1
    s.show(star_img(s, 22), t0, end, GX, 12, enter="top", exit="fade", exit_s=2.0, z=Z_FRONT)
    s.show(ss(s, "manger", 44), t0 + 0.4, end, GX, 38, enter="fade", exit="fade", exit_s=2.0)
    s.twinkle(t0, t1, (GOLD, WHITE), count=18, fade=2.0)
    s.ring(t0 + 0.4, GX, 12, GOLD, r=60, dur=1.5)


GARAGE = dict(intro=g_intro, come=g_come, king=g_king, gifts=g_gifts, before=g_before, honor=g_honor, star=g_star,
              baby=g_baby, poor=g_poor, nogift=g_nogift, play=g_play, mary=g_mary, ox=g_ox, best=g_best,
              smile=g_smile, drumming=g_drumming, finale=g_finale)


# ================================================================ the two windows as one stage

def wins(s):
    return tuple(s.center(m)[0] for m in s.places)  # the two windows, in --model order


WY = 24


def w_intro(s, t0, t1):
    L, C = wins(s)
    s.twinkle(0.3, t1, (WHITE, GOLD), count=10, fade=2.0)
    star = star_img(s, 16)
    # the star crosses from the left window, behind the wall, into the right window
    s.glide(star, [(2.0, -10, 10), (t1, C, 8)], z=Z_FRONT)


def w_come(s, t0, t1):
    L, C = wins(s)
    s.show(star_img(s, 16), t0, t1, C, 8, enter=None, z=Z_FRONT)
    s.glide(ss(s, "boy", 40), [(t0, -10, 26), (t1, L, 26)])


def w_king(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    king = c.w("king", t0)
    s.show(ss(s, "boy", 40), t0, t1, L, 26, enter=None)
    s.show(star_img(s, 16), t0, king, C, 8, enter=None, z=Z_FRONT)
    s.show(s.emoji("👑", 28), king, t1, C, 26, enter="top", hits=c.beats_in(king, t1)[::2], amp=2)
    s.ring(king, C, 26, GOLD, r=28)


def w_gifts(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    gifts = c.w("gifts", t0)
    s.show(s.emoji("🎁", 28), gifts, t1, L, 26, enter="pop")
    s.show(s.emoji("🏺", 26), gifts + 0.4, t1, C, 26, enter="pop")
    s.ring(gifts, L, 26, GOLD, r=26)
    s.ring(gifts + 0.4, C, 26, GOLD, r=26)


def w_before(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    king = c.w("king", t0)
    s.show(ss(s, "king", 44), t0, t1, C, 24, enter="fade", enter_s=1.0)
    gift = s.emoji("🎁", 16)
    # a gift carried over the wall and set before the King
    s.glide(gift, [(t0, L, 30), (king, L, 30), (king + 1.2, C - 12, 40), (t1, C - 12, 40)], z=Z_FRONT)
    s.show(ss(s, "boy", 40), t0, t1, L, 26, enter=None)
    s.ring(king, C, 24, GOLD, r=30)


def w_honor(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    honor = c.w("honor", t0)
    s.show(ss(s, "boy", 40), t0, t1, L, 26, enter=None)
    s.show(s.emoji("🥁", 26), honor, t1, C, 28, enter="pop", hits=c.beats_in(honor, t1), amp=2)
    for i, h in enumerate(hits_in(c, honor, t1, gap=0.8)):
        s.ring(h, C, 28, WARM[i % 3], r=24, dur=0.4)


def w_star(s, t0, t1):
    """The star travels from the left window, over the wall, to stop above the stable in the right window."""
    L, C = wins(s)
    stop = t0 + (t1 - t0) * 0.7
    s.glide(star_img(s, 14), [(t0, -10, 8), (stop, C, 7), (t1, C, 7)], z=Z_FRONT)
    s.show(stable_img(s, 38, 32), t0 + 2.0, t1, C, 32, enter="bottom", enter_s=1.5, z=Z_BACK)
    s.ring(stop, C, 7, GOLD, r=24, dur=1.0)
    s.twinkle(t0, t1, (WHITE, ICE), count=14, fade=1.0)


def w_baby(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    baby = c.w("baby", t0)
    s.show(ss(s, "manger", 40), t0, t1, C, 26, enter="fade", enter_s=0.8)
    s.show(s.emoji("👶", 28), baby, t1, L, 26, enter="pop")
    s.ring(baby, L, 26, GOLD, r=26, dur=1.0)


def w_poor(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    s.show(ss(s, "boy", 42), t0, t1, L, 25, enter="pop")
    s.show(s.emoji("🥺", 26), c.w("boy", t0), t1, C, 26, enter="pop")


def w_nogift(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    gift = c.w("gift", t0)
    s.show(ss(s, "boy", 42), t0, t1, L, 25, enter=None)
    s.show(s.emoji("🎁", 26), t0 + 0.3, t1, C, 26, enter="pop")
    s.show(s.emoji("🚫", 32), gift, t1, C, 26, enter="pop", z=Z_FRONT)


def w_play(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    drum_roll(s, t0, t1, L, 25, 42)
    s.show(ss(s, "king", 44), t0, t1, C, 24, enter="fade", enter_s=1.0)
    for i, h in enumerate(hits_in(c, t0, t1, gap=0.8)):
        s.ring(h, L, 36, WARM[i % 3], r=22, dur=0.4)


def w_mary(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    drum_roll(s, t0, t1, L, 25, 42, every=2)
    s.show(ss(s, "mary", 44), t0, t1, C, 24, enter="fade", enter_s=1.5, hits=c.beats_in(t0 + 2, t1)[::4], amp=1)
    s.ring(t0 + 1.0, C, 24, BLUE, r=30, dur=1.0)
    s.twinkle(t0, t1, (ICE, WHITE), count=10)


def w_ox(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    beats = c.beats_in(t0, t1)
    s.show(s.emoji("🐂", 30), t0, t1, L, 28, enter="left", hits=beats[0::2], amp=3)
    s.show(s.emoji("🐑", 28, flip=True), t0 + 0.3, t1, C, 28, enter="right", hits=beats[1::2], amp=3)


def w_best(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    drum_roll(s, t0, t1, L, 25, 44)
    drum_roll(s, t0, t1, C, 25, 44, offset=1)
    for i, h in enumerate(hits_in(c, t0, t1, gap=0.6)):
        s.ring(h, L if i % 2 == 0 else C, 36, WARM[i % 3], r=26, dur=0.45)


def w_smile(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    smiled = c.w("smiled", t0)
    s.show(ss(s, "boy", 42), t0, t1, L, 25, enter=None)
    s.show(ss(s, "king", 44), t0, t1, C, 24, enter="fade", enter_s=1.0)
    heart = s.emoji("❤️", 14)
    s.glide(heart, [(smiled, C, 12), (smiled + 1.5, L, 10), (t1, L, 10)], z=Z_FRONT)
    s.ring(smiled, C, 24, GOLD, r=30, dur=1.0)


def w_drumming(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    bars = c.bars_in(t0, t1)
    # the drummer boy changes windows every two bars, drumming the whole time
    marks = [t0] + bars[2::2] + [t1]
    for k, (a, b) in enumerate(zip(marks, marks[1:])):
        drum_roll(s, a, b, L if k % 2 == 0 else C, 25, 42)
        s.show(s.emoji("🥁", 24), a, b, C if k % 2 == 0 else L, 30, enter="pop",
               hits=c.beats_in(a, b), amp=3)
    for i, h in enumerate(hits_in(c, t0, t1, gap=0.6)):
        s.ring(h, L if i % 2 == 0 else C, 36, WARM[i % 3], r=22, dur=0.4)
    bar_sweeps(s, t0, t1, (RED, GOLD, BLUE))


def w_finale(s, t0, t1):
    L, C = wins(s)
    end = t1 - 0.1
    s.show(star_img(s, 22), t0, end, L, 22, enter="top", exit="fade", exit_s=2.0)
    s.show(ss(s, "manger", 38), t0 + 0.4, end, C, 26, enter="fade", exit="fade", exit_s=2.0)
    s.twinkle(t0, t1, (GOLD, WHITE), count=12, fade=2.0)


WINDOWS = dict(intro=w_intro, come=w_come, king=w_king, gifts=w_gifts, before=w_before, honor=w_honor, star=w_star,
               baby=w_baby, poor=w_poor, nogift=w_nogift, play=w_play, mary=w_mary, ox=w_ox, best=w_best,
               smile=w_smile, drumming=w_drumming, finale=w_finale)


# ================================================================ 200x42 matrix: 8 bushes, 25 px each

def bx(i):
    return 12.5 + 25 * i


BY = 21


def row(s, keys, t0, t1, *, hits=None, enter="pop", stagger=0.06, amp=3, y=BY):
    for i in range(8):
        h = hits[i % 2::2] if hits else ()
        s.show(keys[i % len(keys)], t0 + stagger * i, t1, bx(i), y, enter=enter, hits=h, amp=amp)


def b_intro(s, t0, t1):
    c = s.cues
    s.twinkle(0.3, t1, (WHITE, GOLD), count=6, fade=2.0)
    star = star_img(s, 14)
    for i, h in enumerate(hits_in(c, 2.0, t1, gap=1.2)[:8]):
        s.show(star, h, t1, bx(i), BY, enter="pop", enter_s=0.2)


def b_come(s, t0, t1):
    s.glide(ss(s, "boy", 38), [(t0, -8, BY), (t1, 212, BY)])
    s.twinkle(t0, t1, (WHITE, GOLD), count=6)


def b_king(s, t0, t1):
    c = s.cues
    king = c.w("king", t0)
    row(s, [s.emoji("👑", 22)], king, t1, hits=c.beats_in(king, t1), enter="top")
    for i in range(8):
        s.ring(king + 0.05 * i, bx(i), BY, GOLD, r=12, dur=0.5)


def b_gifts(s, t0, t1):
    c = s.cues
    gifts = c.w("gifts", t0)
    row(s, [s.emoji("🎁", 22), s.emoji("🏺", 22)], gifts, t1, enter="top", stagger=0.15)


def b_before(s, t0, t1):
    c = s.cues
    row(s, [ss(s, "king", 38), s.emoji("🎁", 20)], t0, t1, enter="pop", stagger=0.1,
        hits=c.beats_in(c.w("king", t0), t1)[::2], amp=1)


def b_honor(s, t0, t1):
    c = s.cues
    honor = c.w("honor", t0)
    row(s, [s.emoji("🥁", 22)], honor, t1, hits=c.beats_in(honor, t1), enter="bottom")


def b_star(s, t0, t1):
    s.glide(star_img(s, 14), [(t0, -8, 10), (t1, 208, 10)], z=Z_FRONT)
    s.show(stable_img(s, 26, 24), t0 + 2.0, t1, bx(7), 29, enter="bottom", enter_s=1.5, z=Z_BACK)
    s.twinkle(t0, t1, (WHITE, ICE), count=8)


def b_baby(s, t0, t1):
    c = s.cues
    row(s, [ss(s, "manger", 38), s.emoji("👶", 22)], t0, t1, enter="fade", stagger=0.12)
    s.twinkle(c.w("baby", t0), t1, (GOLD, WHITE), count=8)


def b_poor(s, t0, t1):
    c = s.cues
    row(s, [ss(s, "boy", 38)], t0, t1, enter="bottom", hits=c.beats_in(t0, t1)[::2], amp=1)


def b_nogift(s, t0, t1):
    c = s.cues
    gift = c.w("gift", t0)
    row(s, [s.emoji("🎁", 22)], t0, t1, enter="pop")
    row(s, [s.emoji("🚫", 24)], gift, t1, enter="pop", stagger=0.08)


def b_play(s, t0, t1):
    c = s.cues
    for i in range(8):
        drum_roll(s, t0 + 0.05 * i, t1, bx(i), BY, 38, every=2, offset=i % 2)
    for i, h in enumerate(hits_in(c, t0, t1, gap=0.4)):
        s.ring(h, bx(i % 8), 36, WARM[i % 3], r=12, dur=0.35)


def b_mary(s, t0, t1):
    c = s.cues
    row(s, [ss(s, "mary", 38), ss(s, "drum1", 38)], t0, t1, enter="fade", stagger=0.15)
    s.twinkle(t0, t1, (ICE, WHITE), count=8)


def b_ox(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    row(s, [s.emoji("🐂", 22), s.emoji("🐑", 22, flip=True)], t0, t1, hits=beats, enter="bottom")


def b_best(s, t0, t1):
    c = s.cues
    for i in range(8):
        drum_roll(s, t0 + 0.05 * i, t1, bx(i), BY, 38, offset=i % 2)
    for i, h in enumerate(hits_in(c, t0, t1, gap=0.3)):
        s.ring(h, bx((i * 3) % 8), 36, WARM[i % 3], r=12, dur=0.35)


def b_smile(s, t0, t1):
    c = s.cues
    smiled = c.w("smiled", t0)
    row(s, [ss(s, "king", 38), s.emoji("😊", 20)], t0, t1, enter="fade", stagger=0.12)
    row(s, [s.emoji("❤️", 12)], smiled + 0.5, t1, enter="pop", y=6)


def b_drumming(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    # the drummer boy marches from bush to bush, one bush per beat, there and back
    path = list(range(8)) + list(range(6, 0, -1))
    keys = drums(s, 38)
    for k, (a, b) in enumerate(zip(beats, beats[1:])):
        i = path[k % len(path)]
        s.pic(keys[k % len(keys)], a, b, bx(i), BY)
        s.ring(a, bx(i), 36, WARM[k % 3], r=12, dur=0.35)


def b_finale(s, t0, t1):
    end = t1 - 0.1
    for i in range(8):
        s.show(star_img(s, 16) if i % 2 == 0 else ss(s, "manger", 34), t0 + 0.08 * i, end, bx(i), BY,
               enter="pop", exit="fade", exit_s=2.0)
    s.twinkle(t0, t1, (GOLD, WHITE), count=8, fade=2.0)


BUSHES = dict(intro=b_intro, come=b_come, king=b_king, gifts=b_gifts, before=b_before, honor=b_honor, star=b_star,
              baby=b_baby, poor=b_poor, nogift=b_nogift, play=b_play, mary=b_mary, ox=b_ox, best=b_best,
              smile=b_smile, drumming=b_drumming, finale=b_finale)
