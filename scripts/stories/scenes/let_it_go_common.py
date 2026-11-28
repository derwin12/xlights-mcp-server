"""Let It Go matrix scenes, shared plan for the garage, the two windows (one stage) and the bushes.

The MegaTree carries the SuperStar story (the ice queen in her blue gown, her bare hand, the door panels, the
snowman, ice stripes, her big face at the end); these scenes follow the same lyric lines on the other matrices:
the snowy mountain with no footprint, the crown, the storm, the doors she keeps shut, the glove thrown away on
the first "let it go", fractal snowflakes, the ice palace rising, the dawn and the door slammed at the end.
An icy palette (ice, white, aqua, violet); fades on the quiet verses, pops on the choruses.
The queen and the snowman are the sequence's own SuperStar MegaTree pictures, aspect corrected (see ss()).
Words: faster-whisper (stories/lyrics/let_it_go.json); beats: librosa (let_it_go_beats.json, ~136 BPM, the real
tempo - the quiet verses hop on every other beat).
"""
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
from morph_backdrop import backdrop, pattern_sweeps  # noqa: E402
from matrix_scenes import Cues  # noqa: E402
from rockin_common import GOLD, ICE, WHITE, Z_BACK, Z_FRONT, Z_PIC, Z_WORD  # noqa: E402

LYRICS = HERE.parent / "lyrics"
AQUA, VIOLET, DEEP = (0, 225, 240), (150, 90, 255), (40, 90, 255)
DAWN, ROSE = (255, 150, 50), (255, 120, 170)
ICY = (ICE, WHITE, AQUA, VIOLET)

SS_X = 3.0
SS = {  # media path in the sequence -> what it shows
    "queen": "LetItGo/LetItGo_2.png",     # the queen standing, hands down
    "arms": "LetItGo/LetItGo_5.png",      # arms raised, casting
    "wide": "LetItGo/LetItGo_12.png",     # arms out to the sides
    "walk": "LetItGo/LetItGo_10.png",     # side on, one arm out
    "ice": "LetItGo/LetItGo_16.png",      # standing on an ice step
    "face": "LetItGo/LetItGo_133.png",    # the big face with the braid (finale)
    "snowman": "LetItGo/LetItGo_68.png",  # the little snowman
}
_SS = {"xsq": None, "imgs": None}


def cues(xsq):
    _SS["xsq"] = xsq
    dur = float(ET.parse(xsq).getroot().findtext("head/sequenceDuration"))
    return Cues.from_files(LYRICS / "let_it_go.json", LYRICS / "let_it_go_beats.json", dur)


def ss(s, name, h, flip=False):
    """A SuperStar picture h LEDs tall, aspect corrected for the tree's tall pixels."""
    from PIL import Image, ImageOps
    key = f"lig_{name}_{h}{'f' if flip else ''}"
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


def exact(c, word, t0, t1):
    """Start times of exactly `word` in [t0, t1) (c.w matches prefixes: "go" would also find "going", "gone")."""
    return [st for w, st, _ in c.words if w == word and t0 <= st < t1]


def plan(c):
    w = c.w
    t = [
        ("intro", 0.0),
        ("mountain", w("the", 13) - 0.2),
        ("kingdom", w("kingdom", 20) - 0.5),
        ("storm", w("wind", 27.5) - 0.9),
        ("doors", w("dont", 41.5) - 0.2),
        ("conceal", w("conceal", 49) - 0.2),
        ("chorus1", w("well", 54) - 0.2),
        ("holdback", w("cant", 62) - 0.2),
        ("chorus1b", w("let", 64.8) - 0.1),
        ("slam", w("turn", 69) - 0.2),
        ("care", w("i", 73.2) - 0.2),
        ("rage", w("let", 79) - 0.2),
        ("cold", w("the", 83.4) - 0.2),
        ("small", w("funny", 91) - 0.3),
        ("breakthrough", w("cant", 100.5) - 0.2),
        ("free", w("no", 112) - 0.2),
        ("chorus2", w("let", 119.8) - 0.1),
        ("stand", w("here", 134) - 0.2),
        ("rage", w("let", 140.8) - 0.2),
        ("power", w("my", 151.5) - 0.5),
        ("fractals", w("we", 159.2) - 0.2),
        ("crystal", w("and", 166) - 0.2),
        ("never", w("im", 173.2) - 0.2),
        ("chorus3", w("let", 181.2) - 0.1),
        ("daylight", w("here", 195.6) - 0.2),
        ("rage", w("let", 203.8) - 0.2),
        ("finale", w("the", 209.5) - 0.2),
    ]
    return [(n, t0, t[k + 1][1] if k + 1 < len(t) else c.duration) for k, (n, t0) in enumerate(t)]


def run(s, scenes):
    for name, t0, t1 in plan(s.cues):
        backdrop(s, t0, t1)
        fn = scenes.get(name)
        if fn:
            fn(s, t0, t1)


def slow(c, t0, t1):
    """Every other beat, for hops on the quiet verses."""
    return c.beats_in(t0, t1)[::2]


# ---------------------------------------------------------------- drawn props

def flake(s, px, depth=2, color=ICE):
    """A fractal snowflake: six arms, each branching `depth` levels deep."""
    r = px / 2 - 0.5

    def draw(d, im):
        c = (px - 1) / 2

        def arm(x, y, ang, ln, lv):
            x2, y2 = x + ln * math.cos(ang), y + ln * math.sin(ang)
            d.line([(x, y), (x2, y2)], fill=(color if lv < depth else WHITE) + (255,), width=1)
            if lv > 0:
                for f in (0.45, 0.75):
                    bx, by = x + ln * f * math.cos(ang), y + ln * f * math.sin(ang)
                    for side in (-1, 1):
                        arm(bx, by, ang + side * math.pi / 3, ln * 0.38, lv - 1)
        for k in range(6):
            arm(c, c, k * math.pi / 3 - math.pi / 2, r, depth)
        d.ellipse([c - 1, c - 1, c + 1, c + 1], fill=WHITE + (255,))
    return s.drawn(f"flake_{px}_{depth}_{color[0]}", px, px, draw)


def growing(s, px, color=ICE):
    """The same flake growing branch by branch (for the frozen fractals)."""
    return [flake(s, max(5, round(px * f)), d, color) for f, d in ((0.3, 0), (0.55, 1), (0.8, 2), (1.0, 3))]


def mountains(s, w, h):
    def draw(d, im):
        for (cx, top, half, col) in ((0.22, 0.25, 0.3, (80, 80, 160)), (0.78, 0.15, 0.32, (90, 90, 175)),
                                     (0.5, 0.0, 0.36, (110, 110, 200))):
            x, y0, hw = cx * w, top * h, half * w
            d.polygon([(x - hw, h), (x, y0), (x + hw, h)], fill=col + (255,))
            sy = y0 + (h - y0) * 0.32
            d.polygon([(x - hw * 0.32, sy), (x, y0), (x + hw * 0.32, sy), (x + hw * 0.1, sy - 2),
                       (x - hw * 0.12, sy - 1)], fill=(245, 250, 255, 255))
    return s.drawn(f"mountains_{w}_{h}", w, h, draw)


def door(s, w, h):
    """One castle door: deep blue with two aqua-framed panels (like the tree's door panels)."""
    def draw(d, im):
        d.rectangle([0, 0, w - 1, h - 1], fill=(20, 50, 180, 255))
        d.rectangle([0, 0, w - 1, h - 1], outline=AQUA + (255,))
        m = max(2, w // 6)
        ph = (h - 3 * m) / 2
        for k in range(2):
            y = m + k * (ph + m)
            d.rectangle([m, y, w - 1 - m, y + ph], outline=AQUA + (255,))
            d.rectangle([m + 2, y + 2, w - 3 - m, y + ph - 2], fill=(40, 90, 230, 255))
        d.point([(w - m // 2 - 1, h // 2)], fill=GOLD + (255,))
    return s.drawn(f"door_{w}_{h}", w, h, draw)


def palace(s, w, h):
    """An ice palace: a tall centre spire between two towers."""
    def draw(d, im):
        body, edge = (110, 190, 255, 255), (235, 250, 255, 255)

        def tower(cx, tw, top):
            d.rectangle([cx - tw / 2, top + tw, cx + tw / 2, h - 1], fill=body, outline=edge)
            d.polygon([(cx - tw / 2 - 1, top + tw), (cx, top), (cx + tw / 2 + 1, top + tw)], fill=edge)
        tower(w * 0.2, w * 0.2, h * 0.35)
        tower(w * 0.8, w * 0.2, h * 0.35)
        tower(w * 0.5, w * 0.3, 0)
        d.rectangle([w * 0.42, h * 0.72, w * 0.58, h - 1], fill=VIOLET + (255,))
        for x in (w * 0.2, w * 0.5, w * 0.8):
            d.rectangle([x - 1, h * 0.55, x + 1, h * 0.6], fill=VIOLET + (255,))
    return s.drawn(f"palace_{w}_{h}", w, h, draw)


def sun(s, px):
    def draw(d, im):
        c = (px - 1) / 2
        r = px * 0.28
        for k in range(12):
            a = k * math.pi / 6
            d.line([(c + r * 1.2 * math.cos(a), c + r * 1.2 * math.sin(a)),
                    (c + (px / 2 - 1) * math.cos(a), c + (px / 2 - 1) * math.sin(a))], fill=GOLD + (255,))
        d.ellipse([c - r, c - r, c + r, c + r], fill=DAWN + (255,))
        d.ellipse([c - r * 0.6, c - r * 0.7, c + r * 0.3, c], fill=(255, 210, 110, 255))
    return s.drawn(f"sun_{px}", px, px, draw)


def ice_wall(s, w, h, half=None):
    """A wall of ice with cracks; half='l'/'r' gives that half for the breakthrough."""
    def draw(d, im):
        x0 = 0 if half != "r" else -w
        full = w if half is None else 2 * w
        d.rectangle([0, 0, w - 1, h - 1], fill=(120, 200, 255, 255))
        for k in range(6):
            x = x0 + full * (k + 0.5) / 6
            d.line([(x, 0), (x + 3, h * 0.4), (x - 2, h * 0.7), (x + 1, h - 1)], fill=(220, 245, 255, 255))
        d.line([(x0 + full / 2, 0), (x0 + full / 2 - 3, h / 2), (x0 + full / 2 + 2, h - 1)],
               fill=(255, 255, 255, 255), width=1)
    return s.drawn(f"wall_{w}_{h}_{half}", w, h, draw)


def frost(s, w, h):
    """An icy floor spreading over the ground."""
    def draw(d, im):
        d.ellipse([-w * 0.1, 0, w * 1.1, h * 2.2], fill=(170, 225, 255, 255))
        for k in range(8):
            x = w * (k + 0.5) / 8
            d.line([(x, h * 0.4), (x + 2, h - 1)], fill=(255, 255, 255, 255))
    return s.drawn(f"frost_{w}_{h}", w, h, draw)


# ================================================================ 140x60 matrix (the garage)

QX, QY = 70, 33  # the queen, centre stage


def g_intro(s, t0, t1):
    s.twinkle(0.3, t1, (WHITE, ICE), count=10, steps=60, fade=2.0)
    s.show(mountains(s, 140, 34), 1.0, t1, 70, 43, enter="fade", enter_s=3.0, z=Z_BACK)
    s.snow(5.0, t1, count=6, speed=4, fade=2.0)
    big = flake(s, 30, 3)
    s.show(big, 6.5, t1 - 0.3, 70, 16, enter="fade", exit="fade", enter_s=2.0, exit_s=1.0, z=Z_PIC)


def g_mountain(s, t0, t1):
    c = s.cues
    white, foot, seen = c.w("white", t0), c.w("footprint", t0), c.w("seen", t0)
    s.show(mountains(s, 140, 34), t0, t1, 70, 43, enter=None, exit="fade", exit_s=1.0, z=Z_BACK)
    s.show(s.word("SNOW", WHITE, 2), c.w("snow", t0), foot - 0.2, 70, 8, enter="fade", exit="fade", z=Z_WORD)
    s.ring(white, 70, 26, WHITE, r=60, dur=1.4, width=2)
    s.show(s.emoji("👣", 18), foot, t1, 70, 48, enter="pop", exit="fade", z=Z_FRONT)
    s.show(s.emoji("🚫", 22), seen, t1, 70, 48, enter="pop", exit="fade", z=Z_FRONT + 1)
    s.snow(t0, t1, count=8, speed=5)


def g_kingdom(s, t0, t1):
    c = s.cues
    queen = c.w("queen", t0)
    s.show(mountains(s, 140, 34), t0, t1, 70, 43, enter="fade", exit="fade", enter_s=1.0, z=Z_BACK)
    s.show(ss(s, "queen", 36), t0 + 0.4, t1, 70, 40, enter="fade", enter_s=1.5, hits=slow(c, t0 + 2, t1), amp=1)
    s.show(s.word("ISOLATION", ICE, 1), c.w("isolation", t0), queen - 0.3, 70, 6, enter="fade", exit="fade",
           z=Z_WORD)
    s.glide(s.emoji("👑", 12), [(queen - 0.6, 70, -8), (queen, 70, 17), (t1, 70, 17)], z=Z_FRONT)
    s.ring(queen, 70, 17, GOLD, r=40, dur=1.2, width=2)
    s.snow(t0, t1, count=6, speed=5)


def swirl(s, t0, t1, x, y, px, every=0.22):
    """A spinning storm swirl: the swirl and its mirror image swapped quickly."""
    keys = [s.emoji("🌀", px), s.emoji("🌀", px, flip=True)]
    n = max(1, int((t1 - t0) / every))
    s.flash(keys, [t0 + k * every for k in range(n)], x, y, end=t1)


def g_storm(s, t0, t1):
    c = s.cues
    storm, keep = c.w("storm", t0), c.w("couldnt", t0)
    s.show(s.emoji("🌬️", 26), t0 + 0.3, storm, 18, 20, enter="left", exit="fade", z=Z_FRONT)
    s.show(ss(s, "queen", 44), t0, t1, 70, 36, enter="fade", hits=c.beats_in(t0, t1), amp=1)
    swirl(s, storm - 0.3, keep, 24, 28, 26)
    swirl(s, storm, keep, 116, 28, 26)
    s.ring(storm, 70, 30, VIOLET, r=60, dur=1.2, width=2)
    # she can't keep it in: ice crystals pop out around her, one a bar
    spots = ((40, 14), (100, 14), (34, 44), (106, 44), (52, 6), (88, 6), (24, 30), (116, 30))
    for k, b in enumerate(c.bars_in(keep, t1)):
        x, y = spots[k % len(spots)]
        s.show(flake(s, 14, 2), b, t1, x, y, enter="pop", exit="fade", exit_s=0.5, z=Z_FRONT)
    s.ring(c.w("tried", t0), 70, 30, ICE, r=50, dur=1.0, width=2)
    s.snow(t0, t1, count=14, speed=16)


def g_doors(s, t0, t1):
    c = s.cues
    din, see, good = c.w("in", t0), c.w("see", t0), c.w("good", t0)
    d = door(s, 26, 46)
    # the two doors slide in from the sides and shut on "in"
    s.glide(d, [(t0, -14, 36), (din, 57, 36), (t1, 57, 36)], z=Z_PIC)
    s.glide(d, [(t0, 154, 36), (din, 83, 36), (t1, 83, 36)], z=Z_PIC)
    s.ring(din, 70, 36, AQUA, r=40, dur=0.8, width=2)
    s.show(s.word("DON'T LET THEM IN", ICE, 1), t0 + 0.2, see - 0.1, 70, 5, enter="fade", exit="fade", z=Z_WORD)
    s.show(s.emoji("🙈", 18), see, good, 70, 30, enter="pop", exit="fade", z=Z_FRONT)
    s.show(s.word("GOOD GIRL", ROSE, 1), good, t1, 70, 5, enter="fade", exit="fade", z=Z_WORD)
    s.show(ss(s, "queen", 30), good, t1, 20, 44, enter="fade", z=Z_FRONT)
    s.show(ss(s, "queen", 30, flip=True), good + 0.3, t1, 120, 44, enter="fade", z=Z_FRONT)


def g_conceal(s, t0, t1):
    c = s.cues
    con, feel, know = c.w("conceal", t0), c.w("feel", t0), c.w("know", t0)
    s.show(ss(s, "queen", 44), t0, t1, 70, 36, enter="fade", enter_s=0.6)
    s.show(s.emoji("🧤", 14), con, t1, 58, 44, enter="pop", z=Z_FRONT)
    s.show(s.emoji("🧤", 14, flip=True), con + 0.3, t1, 82, 44, enter="pop", z=Z_FRONT)
    s.show(s.word("CONCEAL", ICE, 2), con, t1, 26, 14, enter="fade", exit="fade", z=Z_WORD)
    s.show(s.word("DON'T FEEL", VIOLET, 1), feel, t1, 114, 14, enter="fade", exit="fade", z=Z_WORD)
    s.show(s.word("DON'T LET THEM KNOW", WHITE, 1), know - 0.8, t1, 70, 56, enter="fade", exit="fade", z=Z_WORD)


def g_chorus(s, t0, t1, *, glove=False, queen="arms"):
    """Let it go: the big word, a snowflake burst on each "go", the queen casting in the middle."""
    c = s.cues
    lets, gos = exact(c, "let", t0, t1), exact(c, "go", t0, t1)
    s.show(ss(s, queen, 46), t0, t1, QX, 36, enter="pop", hits=c.beats_in(t0 + 0.5, t1), amp=1)
    for k, l in enumerate(lets):
        end = lets[k + 1] if k + 1 < len(lets) else t1
        s.show(s.word("LET IT GO", (WHITE, ICE)[k % 2], 2), l, end, 70, 6, enter="pop", z=Z_WORD)
    big = flake(s, 34, 3)
    for k, g in enumerate(gos):
        x = (24, 116)[k % 2]
        s.show(big, g, min(t1, g + 1.2), x, 32, enter="pop", exit="fade", exit_s=0.5, z=Z_FRONT)
        s.ring(g, x, 32, (ICE, AQUA)[k % 2], r=36, dur=0.8, width=2)
    if glove and gos:
        g = gos[0]
        s.glide(s.emoji("🧤", 14), [(g, 82, 26), (g + 1.4, 150, -12)], z=Z_FRONT + 1)
    pattern_sweeps(s, t0, t1, ICY)
    s.snow(t0, t1, count=10, speed=10)


def g_chorus1(s, t0, t1):
    c = s.cues
    know = c.w("know", t0)
    s.show(s.word("NOW THEY KNOW", ROSE, 1), c.w("now", t0), know + 1.2, 70, 6, enter="fade", exit="fade",
           z=Z_WORD)
    g_chorus(s, know + 1.3, t1, glove=True)


def g_holdback(s, t0, t1):
    c = s.cues
    s.show(ss(s, "wide", 46), t0, t1, QX, 36, enter=None, hits=c.beats_in(t0, t1), amp=1)
    s.show(s.word("CAN'T HOLD IT BACK", ICE, 1), t0 + 0.1, t1, 70, 6, enter="fade", z=Z_WORD)
    sm = flake(s, 10, 1)
    for k, b in enumerate(c.beats_in(c.w("back", t0), t1)):
        a = k * 0.9
        s.glide(sm, [(b, QX, 30), (b + 0.8, QX + 80 * math.cos(a), 30 + 40 * math.sin(a))], z=Z_FRONT)
    s.ring(c.w("anymore", t0), QX, 30, WHITE, r=60, dur=1.0, width=2)


def g_slam(s, t0, t1):
    c = s.cues
    slam, dr = c.w("slam", t0), c.w("door", t0)
    d = door(s, 26, 46)
    s.show(ss(s, "walk", 44, flip=True), t0, slam, 70, 36, enter=None, exit="fade", exit_s=0.4)
    s.glide(d, [(t0, -14, 36), (slam, -14, 36), (dr, 57, 36), (t1, 57, 36)], z=Z_FRONT)
    s.glide(d, [(t0, 154, 36), (slam, 154, 36), (dr, 83, 36), (t1, 83, 36)], z=Z_FRONT)
    s.ring(dr, 70, 36, WHITE, r=70, dur=0.8, width=3)
    s.show(s.word("SLAM!", WHITE, 2), dr, t1, 70, 6, enter="pop", z=Z_WORD)


def g_care(s, t0, t1):
    c = s.cues
    care = c.w("care", t0)
    s.show(ss(s, "queen", 44, flip=True), t0, t1, 70, 36, enter="fade", hits=slow(c, t0, t1), amp=1)
    s.show(s.word("I DON'T CARE", ICE, 1), care, t1, 70, 5, enter="fade", exit="fade", z=Z_WORD)
    spots = ((24, 22), (116, 30), (30, 46), (110, 12), (18, 34), (122, 48))
    bub = s.emoji("💬", 16)
    for k, b in enumerate(c.bars_in(c.w("what", t0), t1)):
        x, y = spots[k % len(spots)]
        s.show(bub, b, t1, x, y, enter="pop", exit="fade", exit_s=0.4, z=Z_FRONT)
        s.show(s.emoji("🚫", 18), b + 0.5, t1, x, y, enter="pop", exit="fade", exit_s=0.4, z=Z_FRONT + 1)


def g_rage(s, t0, t1):
    c = s.cues
    storm = c.w("storm", t0)
    s.wash(t0, t1, (30, 10, 60), z=0, fade_in=0.4, fade_out=0.8)
    s.show(ss(s, "arms", 46), t0, t1, QX, 36, enter="pop", hits=c.beats_in(t0, t1), amp=1)
    swirl(s, t0, t1, 22, 30, 30)
    swirl(s, t0 + 0.11, t1, 118, 30, 30)
    s.show(s.word("STORM", VIOLET, 2), storm, t1, 70, 6, enter="pop", exit="fade", z=Z_WORD)
    for k, b in enumerate(c.bars_in(storm, t1)):
        s.ring(b, QX, 30, (VIOLET, ICE)[k % 2], r=70, dur=1.0, width=2)
    s.snow(t0, t1, count=16, speed=22)


def g_cold(s, t0, t1):
    c = s.cues
    cold, never = c.w("cold", t0), c.w("never", t0)
    s.show(ss(s, "wide", 46), t0, t1, QX, 36, enter="fade", hits=slow(c, t0, t1), amp=1)
    s.show(s.word("THE COLD", ICE, 2), cold, t1 - 3.5, 70, 6, enter="fade", exit="fade", z=Z_WORD)
    s.show(s.word("NEVER", WHITE, 1), never, t1 - 3.5, 24, 30, enter="fade", exit="fade", z=Z_WORD)
    s.show(s.word("BOTHERED ME", WHITE, 1), never + 0.4, t1 - 3.5, 116, 30, enter="fade", exit="fade", z=Z_WORD)
    # the instrumental: flakes bloom one a beat across the garage
    xs = (16, 124, 34, 106, 52, 88, 16, 124)
    for k, b in enumerate(slow(c, t1 - 3.6, t1)):
        s.show(flake(s, 16, 2, (ICE, AQUA, VIOLET)[k % 3]), b, t1, xs[k % 8], 50 - 4 * (k % 3), enter="pop",
               exit="fade", exit_s=0.4, z=Z_FRONT)
    s.twinkle(t0, t1, (WHITE, ICE), count=15, steps=30)


def g_small(s, t0, t1):
    c = s.cues
    dist, small, fears = c.w("distance", t0), c.w("small", t0), c.w("fears", t0)
    pal = palace(s, 50, 44)
    s.show(mountains(s, 140, 34), t0, t1, 70, 43, enter="fade", exit="fade", z=Z_BACK)
    s.pic(pal, t0, dist, 70, 36, fade_in=0.8)
    s.pic(pal, dist, small, 70, 36, scale=(100, 30))  # distance makes everything seem small
    s.pic(pal, small, fears, 70, 36, scale=(30, 30))
    s.show(s.word("SMALL", ICE, 1), small, fears, 70, 6, enter="fade", exit="fade", z=Z_WORD)
    fear = s.emoji("😨", 14)
    for k, (x, y) in enumerate(((30, 20), (110, 20), (40, 46), (100, 46))):
        s.show(fear, fears + 0.3 * k, t1, x, y, enter="pop", exit="fade", exit_s=0.8, z=Z_FRONT)


def g_breakthrough(s, t0, t1):
    c = s.cues
    allw, time_, test, brk = c.w("all", t0), c.w("time", t0), c.w("test", t0), c.w("breakthrough", t0)
    s.show(s.word("CAN'T GET TO ME", WHITE, 1), t0 + 0.2, allw + 0.6, 70, 6, enter="fade", exit="fade", z=Z_WORD)
    fear = s.emoji("😨", 18)
    s.show(fear, t0, allw, 70, 30, enter="fade", exit="shrink", exit_s=0.5)
    s.show(s.emoji("🚫", 22), c.w("me", t0 + 1), allw + 0.4, 70, 30, enter="pop", exit="fade", z=Z_FRONT)
    s.show(ss(s, "arms", 46), time_, t1, 30, 36, enter="fade", hits=slow(c, time_, t1), amp=1)
    s.twinkle(time_, test, (WHITE, ICE, AQUA), count=20, steps=20)
    s.show(s.word("TEST THE LIMITS", ICE, 1), test, t1, 70, 6, enter="fade", exit="fade", z=Z_WORD)
    # an ice wall, which splits and falls away on "breakthrough"
    s.show(ice_wall(s, 20, 48, "l"), test, brk, 92, 36, enter="fade")
    s.show(ice_wall(s, 20, 48, "r"), test, brk, 112, 36, enter="fade")
    s.pic(ice_wall(s, 20, 48, "l"), brk, brk + 0.6, 92, 36, to=(82, 80))
    s.pic(ice_wall(s, 20, 48, "r"), brk, brk + 0.6, 112, 36, to=(124, 80))
    s.ring(brk, 102, 36, WHITE, r=70, dur=0.8, width=3)


def g_free(s, t0, t1):
    c = s.cues
    free = c.w("free", t0)
    for k, (wd, y) in enumerate((("light", 12), ("road", 26), ("rules", 40))):
        t = c.w(wd, t0)
        s.show(s.word("NO " + wd.upper(), ICE, 2), t, free - 0.4, 70, y, enter="pop", exit="fade", z=Z_WORD)
    s.show(s.word("FREE", WHITE, 4), free, t1, 70, 30, enter="pop", exit="fade", z=Z_WORD)
    s.ring(free, 70, 30, WHITE, r=80, dur=1.4, width=3)
    for k in range(4):
        s.glide(s.emoji("🕊️", 14, flip=k % 2 == 1), [(free + 0.3 * k, 70, 30),
                                                    (free + 2.0 + 0.3 * k, (10, 130, 30, 110)[k], -10)],
                z=Z_FRONT)
    s.twinkle(free, t1, (WHITE, ICE), count=20, steps=20)


def g_chorus2(s, t0, t1):
    c = s.cues
    g_chorus(s, t0, t1, queen="wide")
    one, cry = c.w("one", t0), c.w("cry", t0)
    s.show(s.emoji("🌬️", 18), one, one + 2.4, 34, 50, enter="left", exit="fade", z=Z_FRONT)
    s.show(s.emoji("☁️", 18), one + 0.5, one + 2.4, 106, 50, enter="right", exit="fade", z=Z_FRONT)
    s.show(s.emoji("😢", 16), c.w("never", t0), cry + 1.0, 106, 50, enter="pop", exit="fade", z=Z_FRONT)
    s.show(s.emoji("🚫", 20), cry, cry + 1.0, 106, 50, enter="pop", exit="fade", z=Z_FRONT + 1)


def g_stand(s, t0, t1):
    c = s.cues
    stand, stay = c.w("stand", t0), c.w("stay", t0)
    s.show(palace(s, 70, 58), t0 + 0.5, t1, 70, 31, enter="bottom", enter_s=3.0, exit="fade", z=Z_BACK)
    s.show(ss(s, "ice", 48), t0, t1, 70, 35, enter="fade", hits=slow(c, stand, t1), amp=1)
    s.show(s.word("HERE I STAND", WHITE, 1), stand - 1.0, t1, 70, 5, enter="fade", exit="fade", z=Z_WORD)
    s.ring(stand, 70, 30, ICE, r=60, dur=1.0, width=2)
    s.ring(stay, 70, 30, AQUA, r=60, dur=1.0, width=2)


def g_power(s, t0, t1):
    c = s.cues
    flur, ground = c.w("flurries", t0), c.w("ground", t0)
    s.show(ss(s, "arms", 46), t0, t1, QX, 34, enter="fade", hits=slow(c, t0, t1), amp=1)
    sm = [flake(s, 10, 1), flake(s, 12, 2, AQUA)]
    for k, b in enumerate(c.beats_in(flur, ground)):
        x0 = (30, 110)[k % 2]
        s.glide(sm[k % 2], [(b, QX, 20), (b + 0.6, x0, 18), (b + 1.4, x0 + (-12, 12)[k % 2], 56)], z=Z_FRONT)
    s.show(frost(s, 140, 10), ground, t1, 70, 55, enter="fade", enter_s=0.8, z=Z_BACK)
    s.ring(ground, 70, 58, ICE, r=70, dur=1.2, width=2)
    s.show(s.word("POWER", AQUA, 1), c.w("power", t0), flur + 1.5, 70, 5, enter="fade", exit="fade", z=Z_WORD)


def g_fractals(s, t0, t1):
    c = s.cues
    spiral, fract = c.w("spiraling", t0), c.w("fractals", t0)
    s.show(frost(s, 140, 10), t0, t1, 70, 55, enter=None, exit="fade", z=Z_BACK)
    s.spin(spiral, fract, ICY, turns=1.0)
    beats = c.beats_in(spiral, t1)
    for k, (x, y, px, col) in enumerate(((70, 28, 44, ICE), (22, 24, 30, AQUA), (118, 24, 30, VIOLET))):
        keys = growing(s, px, col)
        times = beats[k:k + 8:2][:4]
        if times:
            s.flash(keys, times, x, y, end=t1, z=Z_PIC)
            s.ring(times[-1], x, y, col, r=px, dur=0.8, width=2)
    s.show(s.word("FRACTALS", ICE, 1), fract, t1, 70, 55, enter="fade", exit="fade", z=Z_WORD)


def g_crystal(s, t0, t1):
    c = s.cues
    cry, blast = c.w("crystallizes", t0), c.w("blast", t0)
    s.show(palace(s, 70, 58), t0, t1, 70, 31, enter="bottom", enter_s=min(3.0, cry - t0 + 1.0), z=Z_BACK)
    s.show(s.word("ICY BLAST", WHITE, 2), blast, t1, 70, 6, enter="pop", exit="fade", z=Z_WORD)
    s.ring(blast, 70, 30, WHITE, r=80, dur=1.0, width=3)
    s.burst(blast, blast + 0.8, ICY, n=8)
    sm = flake(s, 12, 2)
    for k in range(8):
        a = k * math.pi / 4
        s.glide(sm, [(blast, 70, 30), (blast + 0.9, 70 + 80 * math.cos(a), 30 + 40 * math.sin(a))], z=Z_FRONT)
    s.twinkle(cry, t1, (WHITE, ICE), count=20, steps=20)


def g_never(s, t0, t1):
    c = s.cues
    back, past = c.w("back", t0), c.w("past", t0)
    s.show(palace(s, 70, 58), t0, t0 + 1.2, 70, 31, enter=None, exit="fade", exit_s=1.0, z=Z_BACK)
    s.glide(ss(s, "walk", 44), [(t0, 160, 36), (back, 100, 36), (t1, 100, 36)])
    crown = s.emoji("👑", 12)
    s.show(crown, t0, past, 100, 12, enter="fade", z=Z_FRONT)
    s.glide(crown, [(past, 100, 12), (past + 1.2, -10, -10)], z=Z_FRONT)  # the past is in the past
    s.show(s.word("NEVER GOING BACK", ICE, 1), c.w("never", t0), past - 0.1, 50, 5, enter="fade", exit="fade",
           z=Z_WORD)
    s.show(s.word("THE PAST", VIOLET, 1), past, t1, 50, 5, enter="fade", exit="fade", z=Z_WORD)


def g_chorus3(s, t0, t1):
    c = s.cues
    rise, perfect, gone = c.w("rise", t0), c.w("perfect", t0), c.w("gone", t0)
    g_chorus(s, t0, t1)
    s.wash(rise, t1, (60, 25, 10), z=0, fade_in=1.5, fade_out=1.0)
    s.glide(sun(s, 40), [(rise, 70, 84), (rise + 2.0, 70, 22), (t1, 70, 22)], z=Z_BACK)
    s.show(ss(s, "queen", 36), perfect, gone + 0.6, 116, 40, enter="fade", exit="fade", exit_s=0.8,
           z=Z_FRONT + 1)


def g_daylight(s, t0, t1):
    c = s.cues
    light = c.w("light", t0)
    s.wash(t0, t1, (60, 30, 10), z=0, fade_out=1.0)
    s.show(sun(s, 40), t0, t1, 70, 22, enter=None, exit="fade", z=Z_BACK)
    s.show(ss(s, "ice", 48), t0, t1, 70, 35, enter="fade", hits=slow(c, t0, t1), amp=1)
    s.show(s.word("LIGHT OF DAY", GOLD, 1), light, t1, 70, 5, enter="fade", exit="fade", z=Z_WORD)
    s.ring(light, 70, 22, GOLD, r=70, dur=1.4, width=2)


def g_finale(s, t0, t1):
    c = s.cues
    cold, end = c.w("cold", t0), t1 - 0.2
    slam = c.w("you", t0) if c.words[-1][1] > t0 else end - 3.0
    s.show(ss(s, "face", 56), t0, slam, 70, 30, enter="fade", exit="fade", enter_s=1.5, exit_s=0.6)
    s.show(s.word("THE COLD", ICE, 1), cold, slam, 22, 26, enter="fade", exit="fade", z=Z_WORD)
    s.show(s.word("NEVER", WHITE, 1), c.w("never", t0), slam, 118, 22, enter="fade", exit="fade", z=Z_WORD)
    s.show(s.word("BOTHERED ME", WHITE, 1), c.w("bothered", t0), slam, 118, 32, enter="fade", exit="fade",
           z=Z_WORD)
    s.twinkle(t0, end, (WHITE, ICE, VIOLET), count=20, steps=40, fade=2.0)
    # and she slams the door
    d = door(s, 26, 46)
    s.glide(d, [(slam - 0.5, -14, 36), (slam, 57, 36), (end - 1.5, 57, 36)], z=Z_FRONT)
    s.glide(d, [(slam - 0.5, 154, 36), (slam, 83, 36), (end - 1.5, 83, 36)], z=Z_FRONT)
    s.pic(d, end - 1.5, end, 57, 36, fade_out=1.5, z=Z_FRONT)
    s.pic(d, end - 1.5, end, 83, 36, fade_out=1.5, z=Z_FRONT)
    s.ring(slam, 70, 36, WHITE, r=70, dur=0.8, width=3)
    s.snow(t0, t1, count=8, speed=5, fade=2.0)


GARAGE = dict(intro=g_intro, mountain=g_mountain, kingdom=g_kingdom, storm=g_storm, doors=g_doors,
              conceal=g_conceal, chorus1=g_chorus1, holdback=g_holdback, chorus1b=g_chorus, slam=g_slam,
              care=g_care, rage=g_rage, cold=g_cold, small=g_small, breakthrough=g_breakthrough, free=g_free,
              chorus2=g_chorus2, stand=g_stand, power=g_power, fractals=g_fractals, crystal=g_crystal,
              never=g_never, chorus3=g_chorus3, daylight=g_daylight, finale=g_finale)


# ================================================================ the two windows as one stage

def wins(s):
    return tuple(s.center(m)[0] for m in s.places)  # the two windows, in --model order


WY = 26


def w_intro(s, t0, t1):
    s.twinkle(0.3, t1, (WHITE, ICE), count=8, steps=60, fade=2.0)
    s.show(mountains(s, s.W, 26), 1.0, t1, s.W / 2, 35, enter="fade", enter_s=3.0, z=Z_BACK)
    s.snow(5.0, t1, count=5, speed=4, fade=2.0)
    L, C = wins(s)
    s.show(flake(s, 24, 3), 6.5, t1 - 0.3, L, 14, enter="fade", exit="fade", enter_s=2.0, exit_s=1.0)
    s.show(flake(s, 24, 3, AQUA), 7.5, t1 - 0.3, C, 14, enter="fade", exit="fade", enter_s=2.0, exit_s=1.0)


def w_mountain(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    foot, seen = c.w("footprint", t0), c.w("seen", t0)
    s.show(mountains(s, s.W, 26), t0, t1, s.W / 2, 35, enter=None, exit="fade", z=Z_BACK)
    s.ring(c.w("white", t0), L, 20, WHITE, r=30, dur=1.4, width=2)
    s.show(s.emoji("👣", 16), foot, t1, C, 36, enter="pop", exit="fade", z=Z_FRONT)
    s.show(s.emoji("🚫", 20), seen, t1, C, 36, enter="pop", exit="fade", z=Z_FRONT + 1)
    s.snow(t0, t1, count=6, speed=5)


def w_kingdom(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    queen = c.w("queen", t0)
    s.show(ss(s, "queen", 36), t0 + 0.4, t1, L, 29, enter="fade", enter_s=1.5, hits=slow(c, t0 + 2, t1), amp=1)
    s.show(s.word("ALONE", ICE, 1), c.w("isolation", t0), t1, C, 24, enter="fade", exit="fade", z=Z_WORD)
    s.glide(s.emoji("👑", 10), [(queen - 0.6, L, -8), (queen, L, 7), (t1, L, 7)], z=Z_FRONT)
    s.ring(queen, L, 7, GOLD, r=24, dur=1.2, width=2)
    s.snow(t0, t1, count=5, speed=5)


def w_storm(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    storm, keep = c.w("storm", t0), c.w("couldnt", t0)
    s.show(ss(s, "queen", 40), t0, t1, L, 26, enter="fade", hits=c.beats_in(t0, t1), amp=1)
    s.show(s.emoji("🌬️", 22), t0 + 0.3, storm, C, WY, enter="right", exit="fade", z=Z_FRONT)
    swirl(s, storm, keep, C, WY, 26)
    for k, b in enumerate(c.bars_in(keep, t1)):
        x, y = ((C - 10, 12), (C + 10, 36), (C + 10, 12), (C - 10, 36))[k % 4]
        s.show(flake(s, 14, 2), b, t1, x, y, enter="pop", exit="fade", exit_s=0.5, z=Z_FRONT)
    s.snow(t0, t1, count=12, speed=16)


def w_doors(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    din, see, good = c.w("in", t0), c.w("see", t0), c.w("good", t0)
    d = door(s, 18, 40)
    # each window gets a pair of doors that shut on "in"
    for x in (L, C):
        s.glide(d, [(t0, x - 30, 26), (din, x - 9, 26), (t1, x - 9, 26)], z=Z_PIC)
        s.glide(d, [(t0, x + 30, 26), (din, x + 9, 26), (t1, x + 9, 26)], z=Z_PIC)
        s.ring(din, x, 26, AQUA, r=26, dur=0.8, width=2)
    s.show(s.emoji("🙈", 16), see, good, L, 26, enter="pop", exit="fade", z=Z_FRONT)
    s.show(ss(s, "queen", 30), good, t1, C, 28, enter="fade", z=Z_FRONT)


def w_conceal(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    con, feel = c.w("conceal", t0), c.w("feel", t0)
    s.show(ss(s, "queen", 40), t0, t1, L, 26, enter="fade", enter_s=0.6)
    s.show(s.emoji("🧤", 12), con, t1, L + 10, 34, enter="pop", z=Z_FRONT)
    s.show(s.word("HIDE", ICE, 2), con, feel, C, 18, enter="fade", exit="fade", z=Z_WORD)
    s.show(s.word("DON'T", VIOLET, 1), feel, t1, C, 18, enter="fade", exit="fade", z=Z_WORD)
    s.show(s.word("FEEL", VIOLET, 2), feel + 0.2, t1, C, 30, enter="fade", exit="fade", z=Z_WORD)


def w_chorus(s, t0, t1, *, glove=False, queen="arms"):
    c = s.cues
    L, C = wins(s)
    lets, gos = exact(c, "let", t0, t1), exact(c, "go", t0, t1)
    s.show(ss(s, queen, 42), t0, t1, L, 27, enter="pop", hits=c.beats_in(t0 + 0.5, t1), amp=1)
    for k, l in enumerate(lets):
        end = lets[k + 1] if k + 1 < len(lets) else t1
        s.show(s.word("LET IT", (WHITE, ICE)[k % 2], 1), l, end, C, 8, enter="pop", z=Z_WORD)
    sm = flake(s, 12, 2)
    for k, g in enumerate(gos):
        end = min(t1, g + 1.2)
        s.show(s.word("GO", (ICE, AQUA)[k % 2], 3), g, end, C, 30, enter="pop", exit="fade", exit_s=0.4, z=Z_WORD)
        for dx, y in ((-13, 18), (13, 18), (-13, 42), (13, 42)):  # small flakes in the corners, clear of the word
            s.show(sm, g, end, C + dx, y, enter="pop", exit="fade", exit_s=0.4, z=Z_FRONT)
        s.ring(g, C, 30, (ICE, AQUA)[k % 2], r=26, dur=0.8, width=2)
    if glove and gos:
        g = gos[0]
        s.glide(s.emoji("🧤", 12), [(g, L + 10, 20), (g + 0.9, (L + C) / 2, 0), (g + 1.6, C + 30, -12)],
                z=Z_FRONT + 1)
    pattern_sweeps(s, t0, t1, ICY)
    s.snow(t0, t1, count=8, speed=10)


def w_chorus1(s, t0, t1):
    know = s.cues.w("know", t0)
    L, C = wins(s)
    s.show(s.word("NOW", ROSE, 2), s.cues.w("now", t0), know + 1.2, L, WY, enter="fade", exit="fade", z=Z_WORD)
    s.show(s.word("THEY KNOW", ROSE, 1), know, know + 1.2, C, WY, enter="fade", exit="fade", z=Z_WORD)
    w_chorus(s, know + 1.3, t1, glove=True)


def w_holdback(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    s.show(ss(s, "wide", 42), t0, t1, L, 27, enter=None, hits=c.beats_in(t0, t1), amp=1)
    sm = flake(s, 10, 1)
    for k, b in enumerate(c.beats_in(t0 + 0.5, t1)):
        s.glide(sm, [(b, L, 20), (b + 0.9, C + (-12, 12, 0)[k % 3], (6, 40, 24)[k % 3])], z=Z_FRONT)
    s.ring(c.w("anymore", t0), C, WY, WHITE, r=30, dur=1.0, width=2)


def w_slam(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    slam, dr = c.w("slam", t0), c.w("door", t0)
    s.show(ss(s, "walk", 40, flip=True), t0, slam, L, 26, enter=None, exit="fade", exit_s=0.4)
    d = door(s, 18, 40)
    for x in (L, C):
        s.glide(d, [(t0, x - 30, 26), (slam, x - 30, 26), (dr, x - 9, 26), (t1, x - 9, 26)], z=Z_FRONT)
        s.glide(d, [(t0, x + 30, 26), (slam, x + 30, 26), (dr, x + 9, 26), (t1, x + 9, 26)], z=Z_FRONT)
        s.ring(dr, x, 26, WHITE, r=30, dur=0.8, width=3)


def w_care(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    s.show(ss(s, "queen", 40, flip=True), t0, t1, L, 26, enter="fade", hits=slow(c, t0, t1), amp=1)
    bub = s.emoji("💬", 14)
    for k, b in enumerate(c.bars_in(c.w("what", t0), t1)):
        x, y = ((C - 8, 12), (C + 8, 34), (C + 8, 12), (C - 8, 34))[k % 4]
        s.show(bub, b, t1, x, y, enter="pop", exit="fade", exit_s=0.4, z=Z_FRONT)
        s.show(s.emoji("🚫", 16), b + 0.5, t1, x, y, enter="pop", exit="fade", exit_s=0.4, z=Z_FRONT + 1)


def w_rage(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    s.wash(t0, t1, (30, 10, 60), z=0, fade_in=0.4, fade_out=0.8)
    s.show(ss(s, "arms", 42), t0, t1, L, 27, enter="pop", hits=c.beats_in(t0, t1), amp=1)
    swirl(s, t0, t1, C, WY, 30)
    for k, b in enumerate(c.bars_in(c.w("storm", t0), t1)):
        s.ring(b, (L, C)[k % 2], WY, (VIOLET, ICE)[k % 2], r=30, dur=1.0, width=2)
    s.snow(t0, t1, count=14, speed=22)


def w_cold(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    cold = c.w("cold", t0)
    s.show(ss(s, "wide", 42), t0, t1, L, 27, enter="fade", hits=slow(c, t0, t1), amp=1)
    s.show(s.word("COLD", ICE, 2), cold, t1 - 3.5, C, 16, enter="fade", exit="fade", z=Z_WORD)
    s.show(s.word("NEVER", WHITE, 1), c.w("never", t0), t1 - 3.5, C, 32, enter="fade", exit="fade", z=Z_WORD)
    for k, b in enumerate(slow(c, t1 - 3.6, t1)):
        s.show(flake(s, 14, 2, (ICE, AQUA, VIOLET)[k % 3]), b, t1, C + (-10, 10)[k % 2], (12, 36)[k // 2 % 2],
               enter="pop", exit="fade", exit_s=0.4, z=Z_FRONT)
    s.twinkle(t0, t1, (WHITE, ICE), count=12, steps=30)


def w_small(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    dist, small, fears = c.w("distance", t0), c.w("small", t0), c.w("fears", t0)
    pal = palace(s, 36, 36)
    s.pic(pal, t0, dist, C, 28, fade_in=0.8)
    s.pic(pal, dist, small, C, 28, scale=(100, 30))
    s.pic(pal, small, fears, C, 28, scale=(30, 30))
    s.show(ss(s, "queen", 40), t0, t1, L, 26, enter="fade")
    fear = s.emoji("😨", 12)
    for k, (dx, y) in enumerate(((-10, 12), (10, 36), (10, 12), (-10, 36))):
        s.show(fear, fears + 0.3 * k, t1, C + dx, y, enter="pop", exit="fade", exit_s=0.8, z=Z_FRONT)


def w_breakthrough(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    allw, time_, test, brk = c.w("all", t0), c.w("time", t0), c.w("test", t0), c.w("breakthrough", t0)
    s.show(s.emoji("😨", 18), t0, allw, C, WY, enter="fade", exit="shrink", exit_s=0.5)
    s.show(s.emoji("🚫", 22), c.w("me", t0 + 1), allw + 0.4, C, WY, enter="pop", exit="fade", z=Z_FRONT)
    s.show(ss(s, "arms", 42), time_, t1, L, 27, enter="fade", hits=slow(c, time_, t1), amp=1)
    s.show(ice_wall(s, 18, 44, "l"), test, brk, C - 9, 24, enter="fade")
    s.show(ice_wall(s, 18, 44, "r"), test, brk, C + 9, 24, enter="fade")
    s.pic(ice_wall(s, 18, 44, "l"), brk, brk + 0.6, C - 9, 24, to=(C - 18, 70))
    s.pic(ice_wall(s, 18, 44, "r"), brk, brk + 0.6, C + 9, 24, to=(C + 18, 70))
    s.ring(brk, C, WY, WHITE, r=40, dur=0.8, width=3)


def w_free(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    free = c.w("free", t0)
    for k, wd in enumerate(("light", "road", "rules")):
        t = c.w(wd, t0)
        s.show(s.word("NO", ICE, 2), t, free - 0.4, L, 10 + 14 * k, enter="pop", exit="fade", z=Z_WORD)
        s.show(s.word(wd.upper(), ICE, 1), t, free - 0.4, C, 10 + 14 * k, enter="pop", exit="fade", z=Z_WORD)
    s.show(s.word("FREE", WHITE, 2), free, t1, C, WY, enter="pop", exit="fade", z=Z_WORD)
    s.ring(free, C, WY, WHITE, r=40, dur=1.4, width=3)
    for k in range(3):
        s.glide(s.emoji("🕊️", 12, flip=k % 2 == 1), [(free + 0.3 * k, L, 30), (free + 2.0 + 0.3 * k,
                                                                               L + (-20, 20, 60)[k], -10)],
                z=Z_FRONT)


def w_chorus2(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    w_chorus(s, t0, t1, queen="wide")
    cry = c.w("cry", t0)
    s.show(s.emoji("😢", 14), c.w("never", t0), cry + 1.0, C, 44 - 7, enter="pop", exit="fade", z=Z_FRONT + 2)
    s.show(s.emoji("🚫", 18), cry, cry + 1.0, C, 37, enter="pop", exit="fade", z=Z_FRONT + 3)


def w_stand(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    stand, stay = c.w("stand", t0), c.w("stay", t0)
    s.show(palace(s, 38, 44), t0 + 0.5, t1, C, 25, enter="bottom", enter_s=3.0, exit="fade", z=Z_BACK)
    s.show(ss(s, "ice", 44), t0, t1, L, 25, enter="fade", hits=slow(c, stand, t1), amp=1)
    s.ring(stand, L, 24, ICE, r=30, dur=1.0, width=2)
    s.ring(stay, C, 24, AQUA, r=30, dur=1.0, width=2)


def w_power(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    flur, ground = c.w("flurries", t0), c.w("ground", t0)
    s.show(ss(s, "arms", 42), t0, t1, L, 25, enter="fade", hits=slow(c, t0, t1), amp=1)
    sm = [flake(s, 10, 1), flake(s, 12, 2, AQUA)]
    for k, b in enumerate(c.beats_in(flur, ground)):
        s.glide(sm[k % 2], [(b, L + 8, 12), (b + 0.8, (L + C) / 2, 2), (b + 1.6, C + (-12, 12)[k % 2], 44)],
                z=Z_FRONT)
    s.show(frost(s, s.W, 8), ground, t1, s.W / 2, 44, enter="fade", z=Z_BACK)
    s.ring(ground, C, 46, ICE, r=40, dur=1.2, width=2)


def w_fractals(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    spiral = c.w("spiraling", t0)
    s.show(frost(s, s.W, 8), t0, t1, s.W / 2, 44, enter=None, exit="fade", z=Z_BACK)
    s.spin(spiral, c.w("fractals", t0), ICY, turns=1.0)
    beats = c.beats_in(spiral, t1)
    for k, (x, col) in enumerate(((L, ICE), (C, VIOLET))):
        times = beats[k:k + 8:2][:4]
        if times:
            s.flash(growing(s, 36, col), times, x, 22, end=t1, z=Z_PIC)
            s.ring(times[-1], x, 22, col, r=30, dur=0.8, width=2)


def w_crystal(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    cry, blast = c.w("crystallizes", t0), c.w("blast", t0)
    for x in (L, C):
        s.show(palace(s, 38, 44), t0, t1, x, 25, enter="bottom", enter_s=min(3.0, cry - t0 + 1.0), z=Z_BACK)
        s.ring(blast, x, 24, WHITE, r=36, dur=1.0, width=3)
    s.burst(blast, blast + 0.8, ICY, n=8)
    s.twinkle(cry, t1, (WHITE, ICE), count=15, steps=20)


def w_never(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    back, past = c.w("back", t0), c.w("past", t0)
    s.show(palace(s, 38, 44), t0, t1, C, 25, enter=None, exit="fade", exit_s=1.0, z=Z_BACK)
    s.glide(ss(s, "walk", 40), [(t0, s.W + 20, 26), (back, C, 26), (past, C, 26), (t1, L, 26)])
    crown = s.emoji("👑", 10)
    s.show(crown, t0 + 0.5, past, L, 10, enter="fade", z=Z_FRONT)
    s.glide(crown, [(past, L, 10), (past + 1.2, -10, -10)], z=Z_FRONT)


def w_chorus3(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    rise, perfect, gone = c.w("rise", t0), c.w("perfect", t0), c.w("gone", t0)
    w_chorus(s, t0, t1)
    s.wash(rise, t1, (60, 25, 10), z=0, fade_in=1.5, fade_out=1.0)
    s.glide(sun(s, 30), [(rise, C, 70), (rise + 2.0, C, 26), (t1, C, 26)], z=Z_BACK)


def w_daylight(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    light = c.w("light", t0)
    s.wash(t0, t1, (60, 30, 10), z=0, fade_out=1.0)
    s.show(sun(s, 30), t0, t1, C, 26, enter=None, exit="fade", z=Z_BACK)
    s.show(ss(s, "ice", 44), t0, t1, L, 25, enter="fade", hits=slow(c, t0, t1), amp=1)
    s.ring(light, C, 26, GOLD, r=40, dur=1.4, width=2)


def w_finale(s, t0, t1):
    c = s.cues
    L, C = wins(s)
    end = t1 - 0.2
    slam = c.w("you", t0) if c.words[-1][1] > t0 else end - 3.0
    s.show(ss(s, "face", 44), t0, slam, L, 25, enter="fade", exit="fade", enter_s=1.5, exit_s=0.6)
    s.show(ss(s, "snowman", 38), t0 + 1.0, slam, C, 27, enter="fade", exit="fade", enter_s=1.5, exit_s=0.6,
           hits=slow(c, t0 + 2, slam - 0.5), amp=1)
    d = door(s, 18, 40)
    for x in (L, C):
        s.glide(d, [(slam - 0.5, x - 30, 26), (slam, x - 9, 26), (end - 1.5, x - 9, 26)], z=Z_FRONT)
        s.glide(d, [(slam - 0.5, x + 30, 26), (slam, x + 9, 26), (end - 1.5, x + 9, 26)], z=Z_FRONT)
        s.pic(d, end - 1.5, end, x - 9, 26, fade_out=1.5, z=Z_FRONT)
        s.pic(d, end - 1.5, end, x + 9, 26, fade_out=1.5, z=Z_FRONT)
        s.ring(slam, x, 26, WHITE, r=30, dur=0.8, width=3)
    s.twinkle(t0, end, (WHITE, ICE, VIOLET), count=15, steps=40, fade=2.0)
    s.snow(t0, t1, count=6, speed=5, fade=2.0)


WINDOWS = dict(intro=w_intro, mountain=w_mountain, kingdom=w_kingdom, storm=w_storm, doors=w_doors,
               conceal=w_conceal, chorus1=w_chorus1, holdback=w_holdback, chorus1b=w_chorus, slam=w_slam,
               care=w_care, rage=w_rage, cold=w_cold, small=w_small, breakthrough=w_breakthrough, free=w_free,
               chorus2=w_chorus2, stand=w_stand, power=w_power, fractals=w_fractals, crystal=w_crystal,
               never=w_never, chorus3=w_chorus3, daylight=w_daylight, finale=w_finale)


# ================================================================ 200x42 matrix: 8 bushes, 25 px each

def bx(i):
    return 12.5 + 25 * i


BY = 22


def row(s, keys, t0, t1, *, hits=None, enter="pop", stagger=0.08, amp=2, y=BY, exit=None, z=Z_PIC):
    for i in range(8):
        h = hits[i % 2::2] if hits else ()
        s.show(keys[i % len(keys)], t0 + stagger * i, t1, bx(i), y, enter=enter, exit=exit, hits=h, amp=amp, z=z)


def letters(s, text, t0, t1, colors, *, scale=4, first=0, stagger=0.1, exit="fade"):
    for i, ch in enumerate(text):
        if ch != " ":
            s.show(s.word(ch, colors[i % len(colors)], scale), t0 + stagger * i, t1, bx(first + i), BY,
                   enter="pop", exit=exit, z=Z_WORD)


def b_intro(s, t0, t1):
    s.twinkle(0.3, t1, (WHITE, ICE), count=6, steps=60, fade=2.0)
    keys = [flake(s, 20, 3), flake(s, 20, 3, AQUA), flake(s, 20, 3, VIOLET)]
    for i in range(8):
        s.show(keys[i % 3], 4.0 + 0.8 * i, t1 - 0.3, bx(i), BY, enter="fade", exit="fade", enter_s=1.5)
    s.snow(5.0, t1, count=4, speed=4, fade=2.0)


def b_mountain(s, t0, t1):
    c = s.cues
    foot, seen = c.w("footprint", t0), c.w("seen", t0)
    s.show(mountains(s, 200, 30), t0, t1, 100, 27, enter="fade", exit="fade", z=Z_BACK)
    s.show(s.emoji("👣", 16), foot, t1, bx(3) + 12, 32, enter="pop", exit="fade", z=Z_FRONT)
    s.show(s.emoji("🚫", 20), seen, t1, bx(3) + 12, 32, enter="pop", exit="fade", z=Z_FRONT + 1)
    s.snow(t0, t1, count=5, speed=5)


def b_kingdom(s, t0, t1):
    c = s.cues
    queen = c.w("queen", t0)
    s.show(ss(s, "queen", 36), t0 + 0.4, t1, bx(3) + 12, 22, enter="fade", enter_s=1.5)
    crown = s.emoji("👑", 14)
    for i in range(8):
        if i not in (3, 4):
            s.show(crown, queen + 0.08 * i, t1, bx(i), BY, enter="pop", z=Z_FRONT)
    s.snow(t0, t1, count=4, speed=5)


def b_storm(s, t0, t1):
    c = s.cues
    storm, keep = c.w("storm", t0), c.w("couldnt", t0)
    for i in range(8):
        swirl(s, t0 + 0.6 + 0.12 * i, keep, bx(i), BY, 22)
    fl = flake(s, 20, 2)
    for k, b in enumerate(c.bars_in(keep, t1)[:8]):
        s.show(fl, b, t1, bx((k * 3) % 8), BY, enter="pop", exit="fade", exit_s=0.5, z=Z_FRONT)
    s.ring(storm, 100, BY, VIOLET, r=100, dur=1.2, width=2)
    s.snow(t0, t1, count=10, speed=16)


def b_doors(s, t0, t1):
    c = s.cues
    din, see = c.w("in", t0), c.w("see", t0)
    d = door(s, 11, 34)
    for i in range(8):  # every bush shuts its pair of doors on "in"
        s.glide(d, [(t0, bx(i) - 20, BY), (din, bx(i) - 5.5, BY), (see, bx(i) - 5.5, BY)], z=Z_PIC)
        s.glide(d, [(t0, bx(i) + 20, BY), (din, bx(i) + 5.5, BY), (see, bx(i) + 5.5, BY)], z=Z_PIC)
    row(s, [s.emoji("🙈", 18)], see, t1, exit="fade")


def b_conceal(s, t0, t1):
    c = s.cues
    con, feel = c.w("conceal", t0), c.w("feel", t0)
    row(s, [s.emoji("🧤", 16), s.emoji("🧤", 16, flip=True)], con, feel - 0.1, exit="fade")
    letters(s, "DONTFEEL", feel, t1, (ICE,) * 4 + (VIOLET,) * 4, scale=4)


def b_chorus(s, t0, t1, *, glove=False):
    c = s.cues
    lets, gos = exact(c, "let", t0, t1), exact(c, "go", t0, t1)
    big = flake(s, 22, 3)
    for k, l in enumerate(lets):
        end = gos[k] if k < len(gos) else min(t1, l + 1.0)
        for i, w in enumerate(("L", "E", "T", "I", "T")):
            s.show(s.word(w, (WHITE, ICE)[k % 2], 4), l + 0.05 * i, end, bx(i + (1 if i > 2 else 0)), BY,
                   enter="pop", z=Z_WORD)
    for k, g in enumerate(gos):
        end = lets[k + 1] if k + 1 < len(lets) else t1
        for i in range(8):
            s.show(big, g + 0.03 * i, end, bx(i), BY, enter="pop", exit="fade", exit_s=0.3, z=Z_FRONT)
        s.ring(g, 100, BY, (ICE, AQUA)[k % 2], r=100, dur=0.8, width=2)
    if glove and gos:
        g = gos[0]
        s.glide(s.emoji("🧤", 14), [(g, bx(3), BY), (g + 1.4, 215, -10)], z=Z_FRONT + 1)
    pattern_sweeps(s, t0, t1, ICY)
    s.snow(t0, t1, count=6, speed=10)


def b_chorus1(s, t0, t1):
    know = s.cues.w("know", t0)
    letters(s, "NOW", s.cues.w("now", t0), know + 1.2, (ROSE,), first=1)
    letters(s, "KNOW", know, know + 1.2, (ROSE,), first=4)
    b_chorus(s, know + 1.3, t1, glove=True)


def b_holdback(s, t0, t1):
    c = s.cues
    row(s, [ss(s, "wide", 38)], t0, t1, hits=c.beats_in(t0 + 0.4, t1), amp=1)
    s.ring(c.w("anymore", t0), 100, BY, WHITE, r=100, dur=1.0, width=2)


def b_slam(s, t0, t1):
    c = s.cues
    slam, dr = c.w("slam", t0), c.w("door", t0)
    d = door(s, 11, 34)
    for i in range(8):
        s.glide(d, [(slam, bx(i) - 20, BY), (dr, bx(i) - 5.5, BY), (t1, bx(i) - 5.5, BY)], z=Z_PIC)
        s.glide(d, [(slam, bx(i) + 20, BY), (dr, bx(i) + 5.5, BY), (t1, bx(i) + 5.5, BY)], z=Z_PIC)
    s.ring(dr, 100, BY, WHITE, r=100, dur=0.8, width=3)


def b_care(s, t0, t1):
    c = s.cues
    bub, no = s.emoji("💬", 18), s.emoji("🚫", 20)
    for k, b in enumerate(c.beats_in(c.w("care", t0), t1)[:8]):
        i = (k * 5) % 8
        s.show(bub, b, t1, bx(i), BY, enter="pop", exit="fade", exit_s=0.4)
        s.show(no, b + 0.4, t1, bx(i), BY, enter="pop", exit="fade", exit_s=0.4, z=Z_FRONT)


def b_rage(s, t0, t1):
    c = s.cues
    s.wash(t0, t1, (30, 10, 60), z=0, fade_in=0.4, fade_out=0.8)
    for i in range(8):
        swirl(s, t0 + 0.05 * i, t1, bx(i), BY, 24)
    for k, b in enumerate(c.bars_in(c.w("storm", t0), t1)):
        s.ring(b, 100, BY, (VIOLET, ICE)[k % 2], r=100, dur=1.0, width=2)
    s.snow(t0, t1, count=12, speed=22)


def b_cold(s, t0, t1):
    c = s.cues
    letters(s, "COLD", c.w("cold", t0), t1 - 3.6, (ICE,), first=2)
    keys = [flake(s, 18, 2, col) for col in (ICE, AQUA, VIOLET)]
    for k, b in enumerate(slow(c, t1 - 3.6, t1)):
        s.show(keys[k % 3], b, t1, bx((k * 3) % 8), BY, enter="pop", exit="fade", exit_s=0.4, z=Z_FRONT)
    s.twinkle(t0, t1, (WHITE, ICE), count=10, steps=30)


def b_small(s, t0, t1):
    c = s.cues
    dist, small, fears = c.w("distance", t0), c.w("small", t0), c.w("fears", t0)
    pal = palace(s, 24, 34)
    for i in range(8):
        s.pic(pal, t0 + 0.1 * i, dist, bx(i), BY, fade_in=0.6)
        s.pic(pal, dist, small, bx(i), BY, scale=(100, 35))
        s.pic(pal, small, fears, bx(i), BY, scale=(35, 35))
    row(s, [s.emoji("😨", 16)], fears, t1, exit="fade", stagger=0.15)


def b_breakthrough(s, t0, t1):
    c = s.cues
    allw, test, brk = c.w("all", t0), c.w("test", t0), c.w("breakthrough", t0)
    row(s, [s.emoji("🚫", 20)], c.w("me", t0 + 1), allw + 0.5, exit="fade")
    l, r = ice_wall(s, 12, 40, "l"), ice_wall(s, 12, 40, "r")
    for i in range(8):
        s.show(l, test + 0.05 * i, brk, bx(i) - 6, 21, enter="fade")
        s.show(r, test + 0.05 * i, brk, bx(i) + 6, 21, enter="fade")
        s.pic(l, brk, brk + 0.6, bx(i) - 6, 21, to=(bx(i) - 12, 70))
        s.pic(r, brk, brk + 0.6, bx(i) + 6, 21, to=(bx(i) + 12, 70))
    s.ring(brk, 100, BY, WHITE, r=100, dur=0.8, width=3)


def b_free(s, t0, t1):
    c = s.cues
    free = c.w("free", t0)
    for k, wd in enumerate(("light", "road", "rules")):
        s.show(s.word("NO", ICE, 3), c.w(wd, t0), free - 0.4, bx(1 + 2 * k), BY, enter="pop", exit="fade",
               z=Z_WORD)
    letters(s, "FREE", free, t1, (WHITE,), first=2)
    s.ring(free, 100, BY, WHITE, r=100, dur=1.4, width=3)
    for k in range(4):
        s.glide(s.emoji("🕊️", 14, flip=k % 2 == 1), [(free + 0.3 * k, bx(2 + k), BY),
                                                    (free + 2.0 + 0.3 * k, bx(2 + k) + (-40, 40)[k % 2], -10)],
                z=Z_FRONT)


def b_stand(s, t0, t1):
    c = s.cues
    stand = c.w("stand", t0)
    row(s, [palace(s, 24, 36)], t0 + 0.5, t1, enter="bottom", exit="fade", stagger=0.2, y=23, z=Z_BACK)
    s.ring(stand, 100, BY, ICE, r=100, dur=1.0, width=2)
    s.ring(c.w("stay", t0), 100, BY, AQUA, r=100, dur=1.0, width=2)


def b_power(s, t0, t1):
    c = s.cues
    flur, ground = c.w("flurries", t0), c.w("ground", t0)
    sm = [flake(s, 10, 1), flake(s, 12, 2, AQUA)]
    for k, b in enumerate(c.beats_in(flur, ground)):
        x = bx((k * 3) % 8)
        s.glide(sm[k % 2], [(b, x, -6), (b + 1.4, x + (-6, 6)[k % 2], 38)], z=Z_FRONT)
    s.show(frost(s, 200, 8), ground, t1, 100, 38, enter="fade", z=Z_BACK)
    s.ring(ground, 100, 41, ICE, r=100, dur=1.2, width=2)


def b_fractals(s, t0, t1):
    c = s.cues
    spiral = c.w("spiraling", t0)
    s.spin(spiral, c.w("fractals", t0), ICY, turns=1.0)
    beats = c.beats_in(spiral, t1)
    cols = (ICE, AQUA, VIOLET)
    for i in range(8):
        times = beats[i % 2:i % 2 + 8:2][:4]
        if times:
            s.flash(growing(s, 24, cols[i % 3]), [t + 0.05 * i for t in times], bx(i), BY, end=t1)


def b_crystal(s, t0, t1):
    c = s.cues
    cry, blast = c.w("crystallizes", t0), c.w("blast", t0)
    row(s, [palace(s, 24, 36)], t0, t1, enter="bottom", stagger=0.25, y=23, z=Z_BACK)
    s.ring(blast, 100, BY, WHITE, r=100, dur=1.0, width=3)
    s.burst(blast, blast + 0.8, ICY, n=8)
    s.twinkle(cry, t1, (WHITE, ICE), count=12, steps=20)


def b_never(s, t0, t1):
    c = s.cues
    past = c.w("past", t0)
    s.glide(ss(s, "walk", 36), [(t0, 215, BY), (past, 100, BY), (t1, -15, BY)])
    crown = s.emoji("👑", 14)
    for i in (0, 1, 6, 7):
        s.show(crown, t0 + 0.2 * i, past, bx(i), BY, enter="pop", z=Z_FRONT)
        s.glide(crown, [(past, bx(i), BY), (past + 1.0, bx(i), -12)], z=Z_FRONT)


def b_chorus3(s, t0, t1):
    c = s.cues
    rise = c.w("rise", t0)
    b_chorus(s, t0, t1)
    s.wash(rise, t1, (60, 25, 10), z=0, fade_in=1.5, fade_out=1.0)


def b_daylight(s, t0, t1):
    c = s.cues
    s.wash(t0, t1, (60, 30, 10), z=0, fade_out=1.0)
    row(s, [sun(s, 24)], t0, t1, enter="bottom", exit="fade", stagger=0.15)
    s.ring(c.w("light", t0), 100, BY, GOLD, r=100, dur=1.4, width=2)


def b_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.2
    slam = c.w("you", t0) if c.words[-1][1] > t0 else end - 3.0
    s.show(ss(s, "face", 40), t0, slam, bx(3) + 12, 21, enter="fade", exit="fade", enter_s=1.5)
    s.show(ss(s, "snowman", 36), t0 + 1.0, slam, bx(0) + 4, 21, enter="fade", exit="fade", enter_s=1.5)
    s.show(ss(s, "snowman", 36, flip=True), t0 + 1.0, slam, bx(7) - 4, 21, enter="fade", exit="fade", enter_s=1.5)
    d = door(s, 11, 34)
    for i in range(8):
        s.glide(d, [(slam - 0.5, bx(i) - 20, BY), (slam, bx(i) - 5.5, BY), (end - 1.5, bx(i) - 5.5, BY)], z=Z_FRONT)
        s.glide(d, [(slam - 0.5, bx(i) + 20, BY), (slam, bx(i) + 5.5, BY), (end - 1.5, bx(i) + 5.5, BY)], z=Z_FRONT)
        s.pic(d, end - 1.5, end, bx(i) - 5.5, BY, fade_out=1.5, z=Z_FRONT)
        s.pic(d, end - 1.5, end, bx(i) + 5.5, BY, fade_out=1.5, z=Z_FRONT)
    s.ring(slam, 100, BY, WHITE, r=100, dur=0.8, width=3)
    s.twinkle(t0, end, (WHITE, ICE, VIOLET), count=10, steps=40, fade=2.0)
    s.snow(t0, t1, count=5, speed=5, fade=2.0)


BUSHES = dict(intro=b_intro, mountain=b_mountain, kingdom=b_kingdom, storm=b_storm, doors=b_doors,
              conceal=b_conceal, chorus1=b_chorus1, holdback=b_holdback, chorus1b=b_chorus, slam=b_slam,
              care=b_care, rage=b_rage, cold=b_cold, small=b_small, breakthrough=b_breakthrough, free=b_free,
              chorus2=b_chorus, stand=b_stand, power=b_power, fractals=b_fractals, crystal=b_crystal,
              never=b_never, chorus3=b_chorus3, daylight=b_daylight, finale=b_finale)
