"""The Fox (What Does the Fox Say?) matrix scenes: garage, the two windows (one stage) and the bushes.

The animals and the fox are the sequence's own SuperStar MegaTree pictures, read from the .xsq at build time and
widened x3 for square matrix pixels (see ss()); nothing is copied into this repo.
Words: faster-whisper (stories/lyrics/the_fox.json); beats: librosa (the_fox_beats.json, ~129 BPM).
Scene boundaries follow the song's sections (the tree's own story changes at the same places).
"""
import base64
import io
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
import matrix_storybook as mb  # noqa: E402
from morph_backdrop import backdrop, pattern_sweeps  # noqa: E402,F401
from matrix_scenes import Cues  # noqa: E402
from rockin_common import (BLUE, GOLD, GREEN, ICE, PINK, PURPLE, RED, WHITE, Z_BACK, Z_FRONT,  # noqa: E402,F401
                           Z_PIC, Z_WORD)

mb.FONT.setdefault("Q", [".#.", "#.#", "#.#", "##.", ".##"])  # QUACK, SQUEAK (the 3x5 font has no Q)

LYRICS = HERE.parent / "lyrics"
ORANGE, FOXRED, MOON = (255, 110, 0), (230, 40, 0), (255, 240, 170)
FOXY = (ORANGE, GOLD, RED, PURPLE)

# ---------------------------------------------------------------- SuperStar pictures

SS_X = 3.0
SS = {  # name -> media path in the sequence
    "dog": "TheFoxImages/TheFox_0.png", "cat": "TheFoxImages/TheFox_5.png", "bird": "TheFoxImages/TheFox_10.png",
    "mouse": "TheFoxImages/TheFox_20.png", "cow": "TheFoxImages/TheFox_25.png",
    "frog": "TheFoxImages/TheFox_26.png", "elephant": "TheFoxImages/TheFox_31.png",
    "duck": "TheFoxImages/TheFox_36.png", "fish": "TheFoxImages/TheFox_38.png", "seal": "TheFoxImages/TheFox_41.png",
    "fox_sit": "TheFoxImages/TheFox_68.png", "fox_dance": "TheFoxImages/TheFox_90.png",
    "fox_kick": "TheFoxImages/TheFox_99.png", "fox_walk": "TheFoxImages/TheFox_133.png",
    "fox_stand": "TheFoxImages/TheFox_149.png", "fox_jump": "TheFoxImages/TheFox_139.png",
    "face": "TheFoxImages/TheFox_167.png", "face_eyes": "TheFoxImages/TheFox_161.png",
    "face_open": "TheFoxImages/TheFox_236.png", "faces4": "TheFoxImages/TheFox_220.png",
    "hole": "TheFoxImages/TheFox_176.png", "angel": "TheFoxImages/TheFox_201.png",
    "horse": "TheFoxImages/TheFox_215.png",
}
FOX_DANCE = ("fox_dance", "fox_kick", "fox_jump", "fox_stand")
_SS = {"xsq": None, "imgs": None}

ANIMALS = [  # (picture, name word, sound word as sung, sound shown)
    ("dog", "dog", "woof", "WOOF"), ("cat", "cat", "meow", "MEOW"), ("bird", "bird", "tweet", "TWEET"),
    ("mouse", "mouse", "squeak", "SQUEAK"), ("cow", "cow", "mo", "MOO"), ("frog", "frog", "croak", "CROAK"),
    ("elephant", "elephant", "toot", "TOOT"), ("duck", "dogs", "quack", "QUACK"), ("fish", "fish", "blub", "BLUB"),
    ("seal", "seal", None, "OW OW OW"),
]


def cues(xsq):
    _SS["xsq"] = xsq
    dur = float(ET.parse(xsq).getroot().findtext("head/sequenceDuration"))
    return Cues.from_files(LYRICS / "the_fox.json", LYRICS / "the_fox_beats.json", dur)


def ss(s, name, h):
    """SuperStar picture `name`, h LEDs tall, aspect corrected for the tree's tall pixels."""
    from PIL import Image
    key = f"ss_{name}_{h}"
    if s._key(key) in s.images:
        return s._key(key)
    if _SS["imgs"] is None:
        root = ET.parse(_SS["xsq"]).getroot()
        want = set(SS.values())
        _SS["imgs"] = {m.get("path"): Image.open(io.BytesIO(base64.b64decode(m.findtext("Data")))).convert("RGBA")
                       for m in root.find("SequenceMedia") if m.get("path") in want and m.findtext("Data")}
    im = _SS["imgs"][SS[name]]
    bb = im.getbbox()
    im = im.crop(bb) if bb else im
    w = max(1, round(im.width * SS_X * h / im.height))
    im = im.resize((round(im.width * SS_X), im.height), Image.LANCZOS).resize((w, h), Image.LANCZOS)
    return s.image(key, im)


def flipped(s, key):
    return s.image(key.rsplit("/", 1)[1][:-4] + "_flip", s.images[key].transpose(0))


# ---------------------------------------------------------------- plan

def animal_times(c):
    """[(picture, t_name, t_sound, shown)] from the first verse's words."""
    out, t = [], 7.0
    for pic, name, sound, shown in ANIMALS:
        tn = c.w(name, t)
        ts = c.w(sound, tn) if sound else tn + 0.9
        out.append((pic, tn, ts, shown))
        t = ts
    return out


def plan(c):
    w = c.w
    t = [
        ("intro", 0.0),
        ("animals", w("dog") - 0.4),
        ("onesound", 30.4),            # "but there's one sound that no one knows" (not transcribed)
        # Each fox noise is three bars after a one-bar "what does the fox say?" (bar times from the
        # sequence's imported bar track; whisper hears none of this section).
        ("ask0", c.beat_after(35.5)),
        ("ring", c.beat_after(37.45)),  # ring-ding-ding-ding-dingeringeding
        ("ask1", c.beat_after(42.95)),
        ("wapow", c.beat_after(44.95)),
        ("ask2", c.beat_after(50.45)),
        ("hatee", c.beat_after(52.45)),
        ("ask3", c.beat_after(57.95)),
        ("joff", c.beat_after(59.9)),
        ("chorus", c.beat_after(65.5)),
        ("verse2", w("blin", 67) - 0.3),
        ("horse", w("but", 89.5) - 0.2),
        ("speak", w("how", 101) - 0.2),
        ("chorus2", c.beat_after(110.45)),
        ("jacha", c.beat_after(112.45)),
        ("ask4", c.beat_after(117.95)),
        ("fraka", c.beat_after(119.9)),
        ("ask5", c.beat_after(125.45)),
        ("ahee", c.beat_after(127.45)),
        ("ask6", c.beat_after(132.95)),
        ("aoo", c.beat_after(134.95)),
        ("chorus3", c.beat_after(140.45)),
        ("mystery", w("the", 143) - 0.2),
        ("whatsay", w("what", 170) - 0.2),
        ("angel", w("you're", 177.5) - 0.2),
        ("finale", w("what", 184.5) - 0.2),
    ]
    return [(n, t0, t[k + 1][1] if k + 1 < len(t) else c.duration) for k, (n, t0) in enumerate(t)]


NOISES = {  # scene -> the fox's words, one per beat
    "ring": ["RING", "DING", "DING", "DING", "DINGERING", "EDING"],
    "wapow": ["WA", "PA", "PA", "PA", "PA", "PA", "POW"],
    "hatee": ["HATEE", "HATEE", "HATEE", "HO"],
    "joff": ["JOFF", "TCHOFF", "TCHOFFO", "TCHOFF"],
    "jacha": ["JACHA", "CHACHA", "CHACHA", "CHOW"],
    "fraka": ["FRAKA", "KAKA", "KAKA", "KOW"],
    "ahee": ["A HEE", "AHEE", "HA HEE"],
    "aoo": ["A OO", "OO", "OO", "OOO"],
}
NOISE_COLORS = {"ring": GOLD, "wapow": GREEN, "hatee": PURPLE, "joff": ORANGE, "jacha": PINK, "fraka": GOLD,
                "ahee": ICE, "aoo": PURPLE}


def run(s, scenes):
    for name, t0, t1 in plan(s.cues):
        backdrop(s, t0, t1)
        fn = scenes.get(name) or (scenes.get("chorus") if name.startswith("ask") else None)
        if fn:
            fn(s, t0, t1, name) if name in NOISES else fn(s, t0, t1)


def bar_sweeps(s, t0, t1, colors=FOXY, every=1):
    """SuperStar-style Morph pattern groups on every other beat (none while the tree's are echoed)."""
    pattern_sweeps(s, t0, t1, colors, every)


def noise_words(s, scene, t0, t1, x, y, scale):
    """The fox's nonsense words swapping on every beat (SuperStar-style quick swaps)."""
    beats = s.cues.beats_in(t0, t1)
    if not beats:
        return beats
    col = NOISE_COLORS[scene]
    words = NOISES[scene]
    keys = [s.word(wd, col if k % 2 == 0 else WHITE, scale if len(wd) <= 6 else 1) for k, wd in enumerate(words)]
    s.flash(keys, beats, x, y, z=Z_WORD, end=t1)
    return beats


def morse_img(s, dash, px):
    w = px * 3 if dash else px

    def draw(d, im):
        d.rectangle([0, 0, w - 1, px - 1], fill=GOLD + (255,))
    return s.drawn(f"morse_{'dash' if dash else 'dot'}_{px}", w, px, draw)


# ================================================================ 140x60 matrix (the garage)

GX, GY = 70, 30


def g_intro(s, t0, t1):
    s.twinkle(0.2, t1, (ORANGE, WHITE), count=8, fade=1.0)
    s.show(s.word("WHAT DOES THE", WHITE, 2), 1.0, t1 - 0.2, GX, 20, enter="fade", enter_s=1.0, z=Z_WORD)
    s.show(s.word("FOX SAY", ORANGE, 3), 3.0, t1 - 0.2, GX, 38, enter="pop", z=Z_WORD)


def g_animals(s, t0, t1):
    seq = animal_times(s.cues)
    for k, (pic, tn, ts, shown) in enumerate(seq):
        end = seq[k + 1][1] if k + 1 < len(seq) else t1
        x = 40 if k % 2 == 0 else 100
        s.show(ss(s, pic, 46), tn, end, x, GY + 2, enter="left" if k % 2 == 0 else "right", enter_s=0.3,
               hits=[ts], amp=4)
        wx = 104 if k % 2 == 0 else 36
        s.show(s.word(shown, GOLD if k % 2 == 0 else ICE, 2 if len(shown) < 7 else 1), ts, end, wx, GY,
               enter="pop", z=Z_WORD)
        s.ring(ts, wx, GY, (GOLD, ICE)[k % 2], r=30, dur=0.5)


def g_onesound(s, t0, t1):
    c = s.cues
    s.show(s.emoji("❓", 34), t0, t1, GX, 26, enter="pop", hits=c.beats_in(t0 + 0.5, t1)[::2], amp=2)
    s.show(s.word("ONE SOUND", WHITE, 2), t0 + 0.4, t1, GX, 52, enter="pop", z=Z_WORD)
    bar_sweeps(s, t0, t1, (RED, ORANGE, GOLD, GREEN, BLUE, PURPLE))


def g_noise(s, t0, t1, scene):
    beats = noise_words(s, scene, t0, t1, 98, 30, 2)
    pose = FOX_DANCE[list(NOISES).index(scene) % len(FOX_DANCE)]
    fox = ss(s, pose, 54)
    s.hold(fox, t0, t1, 30, 31, hits=beats, amp=3)
    for i, b in enumerate(beats[::2]):
        s.ring(b, 98, 30, FOXY[i % 4], r=40, dur=0.45)
    bar_sweeps(s, t0, t1, (NOISE_COLORS[scene], WHITE))


def g_chorus(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    say = [w_ for w_ in c.words if t0 <= w_[1] < t1 and w_[0].startswith(("what", "whats"))] or [("", t0 + 0.1, 0)]
    s.show(ss(s, "face", 52), t0, t1, GX, 30, enter="pop", hits=beats[::2], amp=2)
    for _, t, _e in say:
        s.show(s.word("WHAT DOES", WHITE, 1), t, t + 1.3, 20, 30, enter="left", z=Z_WORD)
        s.show(s.word("FOX SAY", ORANGE, 1), t + 0.6, t + 1.9, 120, 30, enter="right", z=Z_WORD)
        s.ring(t + 0.6, GX, 30, ORANGE, r=60, dur=0.8)
    s.twinkle(t0, t1, FOXY, count=15, steps=15, fade=0.3)


def g_verse2(s, t0, t1):
    c = s.cues
    eyes, nose, holes, paws, still, fur, angel = (c.w(k, t0) for k in
                                                  ("eyes", "nose", "holes", "tiny", "still", "fur", "angel"))
    s.show(ss(s, "face_eyes", 52), t0, holes - 0.8, GX, 30, enter="pop")
    s.show(s.word("BLUE EYES", BLUE, 1), eyes, nose, 20, 30, enter="pop", z=Z_WORD)
    s.show(s.word("POINTY NOSE", ORANGE, 1), nose, holes - 0.8, 116, 30, enter="pop", z=Z_WORD)
    s.show(s.emoji("🐭", 16), holes - 2.2, holes - 0.8, 120, 46, enter="right")
    s.show(ss(s, "hole", 54), holes - 0.8, paws, GX, 31, enter="bottom")
    s.show(s.word("DIGGING", ORANGE, 1), holes - 0.4, paws, 118, 10, enter="pop", z=Z_WORD)
    # tiny paws up the hill, then standing still
    fox = ss(s, "fox_walk", 34)

    def hill(d, im):
        d.polygon([(0, im.height - 1), (im.width - 1, 0), (im.width - 1, im.height - 1)], fill=(235, 245, 255, 255))
    s.show(s.drawn("hill_140", 140, 30, hill), paws, fur, GX, 45, enter="bottom", z=Z_BACK)
    s.glide(fox, [(paws, 10, 44), (still, 110, 18), (fur, 110, 18)])
    s.show(s.word("STILL", ICE, 2), still, fur, 40, 10, enter="pop", z=Z_WORD)
    s.show(ss(s, "fox_stand", 54), fur, angel, GX, 31, enter="pop")
    s.show(s.word("BEAUTIFUL", RED, 2), fur + 0.8, angel, GX, 6, enter="pop", z=Z_WORD)
    s.show(ss(s, "angel", 54), angel, t1, GX, 31, enter="fade", enter_s=0.6)
    s.twinkle(angel, t1, (WHITE, ICE, GOLD), count=20, steps=15, fade=0.3)
    s.snow(t0, t1, count=4)


def g_horse(s, t0, t1):
    c = s.cues
    horse_t, morse = c.w("host", t0), c.w("more", t0)
    s.show(ss(s, "horse", 50), horse_t - 0.4, t1, 32, 32, enter="left", hits=c.beats_in(horse_t, t1)[::4], amp=2)
    s.show(ss(s, "fox_sit", 50), t0, t1, 112, 32, enter="right")
    s.show(s.word("HORSE", GOLD, 2), horse_t, morse, GX, 8, enter="pop", z=Z_WORD)
    s.show(s.word("MORSE", GOLD, 2), morse, t1, GX, 8, enter="pop", z=Z_WORD)
    # dots and dashes flying from the fox to the horse
    code = [0, 0, 0, 1, 1, 1, 0, 0, 0]  # ... --- ...
    beats = c.beats_in(morse, t1)
    for k, b in enumerate(beats[:len(code) * 2:2]):
        key = morse_img(s, code[k], 4)
        s.glide(key, [(b, 92, 26), (b + 0.9, 52, 26)], z=Z_FRONT)


def g_speak(s, t0, t1):
    c = s.cues
    s.show(ss(s, "horse", 50), t0, t1, 32, 32, enter=None)
    s.show(ss(s, "fox_stand", 50), t0, t1, 112, 32, enter=None, hits=c.beats_in(t0, t1)[::2], amp=2)
    s.show(s.emoji("❓", 20), c.w("speak", t0), t1, GX, 26, enter="pop", hits=c.beats_in(t0 + 1, t1)[::2], amp=2)
    s.show(s.word("SPEAK", ICE, 2), c.w("speak", t0), t1, GX, 8, enter="pop", z=Z_WORD)


def g_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.2
    beats = c.beats_in(t0, end - 2.5)
    s.show(ss(s, "fox_jump", 54), t0, end, 34, 31, enter="pop", exit="fade", exit_s=2.0, hits=beats, amp=3)
    s.show(s.word("WHAT IS", WHITE, 2), t0 + 0.2, t0 + 3.0, 100, 22, enter="pop", z=Z_WORD)
    s.show(s.word("YOUR SOUND", ORANGE, 2), t0 + 1.0, t0 + 3.0, 100, 38, enter="pop", z=Z_WORD)
    s.show(s.word("MERRY", RED, 2), t0 + 3.2, end, 100, 22, enter="pop", exit="fade", exit_s=2.0, z=Z_WORD)
    s.show(s.word("CHRISTMAS", GREEN, 2), t0 + 3.6, end, 100, 38, enter="pop", exit="fade", exit_s=2.0, z=Z_WORD)
    s.twinkle(t0, t1, FOXY, count=15, fade=2.0)
    s.snow(t0, t1, count=6, fade=2.0)


def mystery_common(s, t0, t1, W, H, moon_x, fox_h):
    """Quiet bridge: night forest, falling snow, the moon, a fox peeking out then trotting across."""
    c = s.cues
    deep, hiding, sound, know = (c.w(k, t0) for k in ("somewhere", "hiding", "sound", "ever"))
    s.show(s.emoji("🌙", max(12, H // 4)), t0, t1, moon_x, H * 0.2, enter="fade", enter_s=1.5, z=Z_BACK)
    s.snow(t0, t1, count=8, speed=6)
    s.twinkle(t0, t1, (WHITE, ICE), count=6, fade=1.0)
    return deep, hiding, sound, know


def g_mystery(s, t0, t1):
    c = s.cues
    deep, hiding, sound, know = mystery_common(s, t0, t1, 140, 60, 118, 30)
    s.show(s.word("SECRET", PURPLE, 2), c.w("secret", t0), c.w("ancient", t0), 50, 12, enter="fade", z=Z_WORD)
    s.show(s.word("MYSTERY", PURPLE, 2), c.w("ancient", t0), deep, 50, 12, enter="fade", z=Z_WORD)
    for k, x in enumerate((12, 34, 56, 82, 104, 128)):
        s.show(s.emoji("🌲", 26 + 6 * (k % 2)), deep + 0.3 * k, t1, x, 46, enter="bottom", enter_s=0.6, z=Z_PIC)
    peek = ss(s, "face", 18)
    s.show(peek, hiding, sound, 46, 50, enter="bottom", enter_s=0.8, z=Z_FRONT)
    s.show(s.word("HIDING", ICE, 1), hiding, sound, 46, 34, enter="fade", z=Z_WORD)
    s.show(s.emoji("❓", 18), sound, know, 70, 20, enter="pop", z=Z_WORD)
    fox = ss(s, "fox_walk", 22)
    s.glide(flipped(s, fox), [(know, 150, 50), (t1, -20, 50)], z=Z_FRONT)


def g_whatsay(s, t0, t1):
    c = s.cues
    beats = c.beats_in(t0, t1)
    s.show(ss(s, "face_open", 52), t0, t1, GX, 30, enter="pop", hits=beats[::2], amp=2)
    s.show(s.emoji("❓", 20), t0 + 0.6, t1, 24, 30, enter="left", hits=beats[0::2], amp=3)
    s.show(s.emoji("❓", 20), t0 + 0.8, t1, 116, 30, enter="right", hits=beats[1::2], amp=3)


def g_angel(s, t0, t1):
    c = s.cues
    s.show(ss(s, "angel", 54), t0, c.w("hiding", t0), 40, 31, enter="fade", enter_s=0.6)
    s.show(s.word("GUARDIAN", WHITE, 2), c.w("guardian", t0), t1, 104, 12, enter="pop", z=Z_WORD)
    s.show(s.word("ANGEL", GOLD, 2), c.w("angel", t0), t1, 104, 28, enter="pop", z=Z_WORD)
    s.show(ss(s, "hole", 54), c.w("hiding", t0), t1, 40, 31, enter="bottom")
    s.twinkle(t0, t1, (WHITE, GOLD), count=15, fade=0.5)


GARAGE = dict(intro=g_intro, animals=g_animals, onesound=g_onesound, ring=g_noise, wapow=g_noise, hatee=g_noise,
              joff=g_noise, chorus=g_chorus, verse2=g_verse2, horse=g_horse, speak=g_speak, chorus2=g_chorus,
              jacha=g_noise, fraka=g_noise, ahee=g_noise, aoo=g_noise, chorus3=g_chorus, mystery=g_mystery,
              whatsay=g_whatsay, angel=g_angel, finale=g_finale)


# ================================================================ the two windows as one stage

def wins(s):
    return tuple(s.center(m)[0] for m in s.places)  # the two windows, in --model order


WY = 25


def w_intro(s, t0, t1):
    L, C = wins(s)
    s.twinkle(0.2, t1, (ORANGE, WHITE), count=6, fade=1.0)
    s.show(s.emoji("❓", 26), 2.0, t1 - 0.2, L, WY, enter="fade", enter_s=1.0)
    s.show(ss(s, "fox_sit", 40), 3.5, t1 - 0.2, C, WY, enter="fade", enter_s=1.0)


def w_animals(s, t0, t1):
    """Each animal pops into one window; its sound answers from the other, across the wall."""
    L, C = wins(s)
    seq = animal_times(s.cues)
    for k, (pic, tn, ts, shown) in enumerate(seq):
        end = seq[k + 1][1] if k + 1 < len(seq) else t1
        a, b = (L, C) if k % 2 == 0 else (C, L)
        s.show(ss(s, pic, 40), tn, end, a, WY + 2, enter="pop", hits=[ts], amp=3)
        s.show(s.word(shown, GOLD, 2 if len(shown) <= 5 else 1), ts, end, b, WY, enter="pop", z=Z_WORD)
        s.ring(ts, b, WY, GOLD, r=24, dur=0.45)


def w_onesound(s, t0, t1):
    L, C = wins(s)
    c = s.cues
    s.show(s.emoji("❓", 26), t0, t1, L, WY, enter="pop", hits=c.beats_in(t0, t1)[0::2], amp=2)
    s.show(s.emoji("❓", 26), t0 + 0.3, t1, C, WY, enter="pop", hits=c.beats_in(t0, t1)[1::2], amp=2)
    bar_sweeps(s, t0, t1, (RED, ORANGE, GOLD, GREEN, BLUE, PURPLE))


def w_noise(s, t0, t1, scene):
    """The fox dances in one window while its words flash in the other; they swap windows every bar."""
    L, C = wins(s)
    c = s.cues
    beats = c.beats_in(t0, t1)
    pose = FOX_DANCE[list(NOISES).index(scene) % len(FOX_DANCE)]
    fox = ss(s, pose, 44)
    bars = c.bars_in(t0, t1)
    edges = [t0] + [b for b in bars if b > t0 + 0.2] + [t1]
    col = NOISE_COLORS[scene]
    words = NOISES[scene]
    for k, (a, b) in enumerate(zip(edges, edges[1:])):
        fx, wx = (L, C) if k % 2 == 0 else (C, L)
        s.hold(fox, a, b, fx, WY + 2, hits=c.beats_in(a, b), amp=3)
        bb = c.beats_in(a, b)
        if bb:
            keys = [s.word(wd, col if j % 2 == 0 else WHITE, 1 if len(wd) > 5 else 2) for j, wd in enumerate(words)]
            s.flash(keys, bb, wx, WY, z=Z_WORD, end=b)
        s.ring(a, wx, WY, col, r=26, dur=0.5)


def w_chorus(s, t0, t1):
    L, C = wins(s)
    c = s.cues
    beats = c.beats_in(t0, t1)
    s.show(ss(s, "face", 40), t0, t1, L, WY, enter="pop", hits=beats[0::2], amp=2)
    s.show(ss(s, "face_eyes", 40), t0 + 0.2, t1, C, WY, enter="pop", hits=beats[1::2], amp=2)
    for _, t, _e in [w_ for w_ in c.words if t0 <= w_[1] < t1 and w_[0].startswith("what")] or [("", t0 + 0.1, 0)]:
        s.ring(t, L, WY, ORANGE, r=26)
        s.ring(t + 0.5, C, WY, ORANGE, r=26)


def w_verse2(s, t0, t1):
    L, C = wins(s)
    c = s.cues
    eyes, holes, paws, still, fur, angel = (c.w(k, t0) for k in ("eyes", "holes", "tiny", "still", "fur", "angel"))
    s.show(ss(s, "face_eyes", 40), t0, holes - 0.8, L, WY, enter="pop")
    s.show(s.emoji("👃", 24), c.w("nose", t0), holes - 0.8, C, WY, enter="pop")
    s.show(s.emoji("👀", 24), eyes, c.w("nose", t0), C, WY, enter="pop")
    s.show(ss(s, "hole", 44), holes - 0.8, paws, C, WY + 1, enter="bottom")
    s.show(s.emoji("🐭", 14), holes - 0.8, paws, L, 38, enter="left")
    fox = ss(s, "fox_walk", 26)
    s.glide(fox, [(paws, -16, 36), (still, L + 64 - 6, 14), (fur, L + 64 - 6, 14)])
    s.show(ss(s, "fox_stand", 44), fur, angel, L, WY + 1, enter="pop")
    s.show(s.emoji("❤️", 24), fur + 0.6, angel, C, WY, enter="pop")
    s.show(ss(s, "angel", 44), angel, t1, C, WY + 1, enter="fade", enter_s=0.6)
    s.show(ss(s, "fox_sit", 40), angel, t1, L, WY + 2, enter=None)
    s.snow(t0, t1, count=4)


def w_horse(s, t0, t1):
    L, C = wins(s)
    c = s.cues
    horse_t, morse = c.w("host", t0), c.w("more", t0)
    s.show(ss(s, "fox_sit", 40), t0, t1, L, WY + 2, enter="left")
    s.show(ss(s, "horse", 40), horse_t - 0.4, t1, C, WY + 2, enter="right")
    code = [0, 0, 0, 1, 1, 1, 0, 0, 0]
    for k, b in enumerate(c.beats_in(morse, t1)[:len(code) * 2:2]):  # over the wall to the horse
        s.glide(morse_img(s, code[k], 3), [(b, L + 10, 12), (b + 0.9, C - 10, 12)], z=Z_FRONT)


def w_speak(s, t0, t1):
    L, C = wins(s)
    c = s.cues
    s.show(ss(s, "fox_stand", 40), t0, t1, L, WY + 2, enter=None, hits=c.beats_in(t0, t1)[::2], amp=2)
    s.show(ss(s, "horse", 40), t0, t1, C, WY + 2, enter=None)
    s.show(s.emoji("❓", 14), c.w("speak", t0), t1, C, 8, enter="pop", z=Z_FRONT)


def w_mystery(s, t0, t1):
    L, C = wins(s)
    c = s.cues
    deep, hiding, sound, know = mystery_common(s, t0, t1, s.W, s.H, C + 10, 24)
    for k, x in enumerate((L - 10, L + 10, C - 12, C + 6)):
        s.show(s.emoji("🌲", 22 + 4 * (k % 2)), deep + 0.4 * k, t1, x, 36, enter="bottom", enter_s=0.6)
    s.show(ss(s, "face", 16), hiding, sound, L, 40, enter="bottom", enter_s=0.8, z=Z_FRONT)
    s.show(s.emoji("❓", 16), sound, know, C, 22, enter="pop", z=Z_WORD)
    fox = flipped(s, ss(s, "fox_walk", 20))  # trots from the right window, behind the wall, into the left
    s.glide(fox, [(know, s.W + 14, 40), (t1, -14, 40)], z=Z_FRONT)


def w_whatsay(s, t0, t1):
    L, C = wins(s)
    c = s.cues
    beats = c.beats_in(t0, t1)
    s.show(ss(s, "face_open", 40), t0, t1, L, WY, enter="pop", hits=beats[0::2], amp=2)
    s.show(s.emoji("❓", 26), t0 + 0.3, t1, C, WY, enter="pop", hits=beats[1::2], amp=3)


def w_angel(s, t0, t1):
    L, C = wins(s)
    c = s.cues
    s.show(ss(s, "angel", 44), t0, t1, L, WY + 1, enter="fade", enter_s=0.6)
    s.show(ss(s, "hole", 44), c.w("hiding", t0), t1, C, WY + 1, enter="bottom")
    s.twinkle(t0, t1, (WHITE, GOLD), count=12, fade=0.5)


def w_finale(s, t0, t1):
    L, C = wins(s)
    c = s.cues
    end = t1 - 0.2
    beats = c.beats_in(t0, end - 2.5)
    s.show(ss(s, "fox_jump", 44), t0, end, L, WY + 1, enter="pop", exit="fade", exit_s=2.0, hits=beats[0::2], amp=3)
    s.show(ss(s, "fox_dance", 44), t0 + 0.2, end, C, WY + 1, enter="pop", exit="fade", exit_s=2.0,
           hits=beats[1::2], amp=3)
    s.twinkle(t0, t1, FOXY, count=12, fade=2.0)
    s.snow(t0, t1, count=5, fade=2.0)


WINDOWS = dict(intro=w_intro, animals=w_animals, onesound=w_onesound, ring=w_noise, wapow=w_noise, hatee=w_noise,
               joff=w_noise, chorus=w_chorus, verse2=w_verse2, horse=w_horse, speak=w_speak, chorus2=w_chorus,
               jacha=w_noise, fraka=w_noise, ahee=w_noise, aoo=w_noise, chorus3=w_chorus, mystery=w_mystery,
               whatsay=w_whatsay, angel=w_angel, finale=w_finale)


# ================================================================ 200x42 matrix: 8 bushes, 25 px each

def bx(i):
    return 12.5 + 25 * i


BY = 22


def row(s, keys, t0, t1, *, hits=None, enter="pop", stagger=0.06, amp=3, y=BY, z=Z_PIC, **kw):
    for i in range(8):
        h = hits[i % 2::2] if hits else ()
        s.show(keys[i % len(keys)], t0 + stagger * i, t1, bx(i), y, enter=enter, hits=h, amp=amp, z=z, **kw)


def b_intro(s, t0, t1):
    s.twinkle(0.2, t1, (ORANGE, WHITE), count=4, fade=1.0)
    row(s, [s.emoji("❓", 20)], 2.0, t1 - 0.2, enter="top", stagger=0.3)


def b_animals(s, t0, t1):
    """The animals fill the bushes one by one; each says its sound on the next bush."""
    seq = animal_times(s.cues)
    for k, (pic, tn, ts, shown) in enumerate(seq):
        i = k % 8
        end = seq[k + 8][1] if k + 8 < len(seq) else t1
        s.show(ss(s, pic, 34), tn, end, bx(i), BY + 2, enter="top", enter_s=0.25, hits=[ts], amp=3)
        s.ring(ts, bx(i), BY, GOLD, r=14, dur=0.4)


def b_onesound(s, t0, t1):
    row(s, [s.emoji("❓", 22)], t0, t1, enter="pop", hits=s.cues.beats_in(t0, t1))


def b_noise(s, t0, t1, scene):
    """One noise word spread across the bushes, a fox on the rest, swapping each beat."""
    c = s.cues
    beats = c.beats_in(t0, t1)
    col = NOISE_COLORS[scene]
    pose = FOX_DANCE[list(NOISES).index(scene) % len(FOX_DANCE)]
    fox = ss(s, pose, 36)
    letters = "".join(NOISES[scene]).replace(" ", "")
    for i in range(8):
        if i % 2 == 0:
            s.hold(fox, t0 + 0.04 * i, t1, bx(i), BY + 1, hits=beats[(i // 2) % 2::2], amp=3)
        else:
            keys = [s.word(ch, col if j % 2 == 0 else WHITE, 5) for j, ch in enumerate(letters[i // 2::4] or "O")]
            if beats:
                s.flash(keys, beats, bx(i), BY, z=Z_WORD, end=t1)
    for b in c.bars_in(t0, t1):
        s.ring(b, 100, BY, col, r=60, dur=0.6)


def b_chorus(s, t0, t1):
    c = s.cues
    row(s, [ss(s, "face", 36), ss(s, "face_eyes", 36)], t0, t1, hits=c.beats_in(t0, t1), y=BY + 1)


def b_verse2(s, t0, t1):
    c = s.cues
    holes, paws, fur, angel = (c.w(k, t0) for k in ("holes", "tiny", "fur", "angel"))
    row(s, [ss(s, "face_eyes", 36)], t0, holes - 0.8, y=BY + 1)
    row(s, [ss(s, "hole", 36)], holes - 0.8, paws, enter="bottom", y=BY + 1)
    fox = ss(s, "fox_walk", 26)
    s.glide(fox, [(paws, -14, 26), (fur - 0.2, 214, 26)])
    row(s, [s.emoji("❤️", 20)], fur, angel, stagger=0.1)
    row(s, [ss(s, "angel", 36)], angel, t1, enter="fade", enter_s=0.5, y=BY + 1)


def b_horse(s, t0, t1):
    c = s.cues
    horse_t, morse = c.w("host", t0), c.w("more", t0)
    row(s, [ss(s, "fox_sit", 34), ss(s, "horse", 34)], horse_t - 0.4, t1, y=BY + 2,
        hits=c.beats_in(horse_t, t1)[::2])
    code = [0, 0, 0, 1, 1, 1, 0, 0, 0]
    for k, b in enumerate(c.beats_in(morse, t1)[:len(code) * 2:2]):
        s.glide(morse_img(s, code[k], 3), [(b, -10, 6), (b + 1.6, 210, 6)], z=Z_FRONT)


def b_speak(s, t0, t1):
    row(s, [ss(s, "fox_stand", 34), s.emoji("❓", 20)], t0, t1, y=BY + 2, hits=s.cues.beats_in(t0, t1))


def b_mystery(s, t0, t1):
    c = s.cues
    deep, know = c.w("somewhere", t0), c.w("ever", t0)
    s.snow(t0, t1, count=5, speed=6)
    row(s, [s.emoji("🌲", 26)], deep, t1, enter="bottom", stagger=0.4, enter_s=0.6, z=Z_BACK)
    fox = flipped(s, ss(s, "fox_walk", 20))
    s.glide(fox, [(know, 214, 32), (t1, -14, 32)], z=Z_FRONT)
    s.show(s.emoji("🌙", 16), t0, deep, 100, 14, enter="fade", enter_s=1.5)


def b_whatsay(s, t0, t1):
    row(s, [ss(s, "face_open", 36), s.emoji("❓", 22)], t0, t1, hits=s.cues.beats_in(t0, t1), y=BY + 1)


def b_angel(s, t0, t1):
    row(s, [ss(s, "angel", 36)], t0, t1, enter="fade", enter_s=0.5, stagger=0.15, y=BY + 1)
    s.twinkle(t0, t1, (WHITE, GOLD), count=8, fade=0.5)


def b_finale(s, t0, t1):
    c = s.cues
    end = t1 - 0.2
    beats = c.beats_in(t0, end - 2.5)
    row(s, [ss(s, p, 36) for p in FOX_DANCE], t0, end, hits=beats, exit="fade", exit_s=2.0, y=BY + 1)
    s.twinkle(t0, t1, FOXY, count=8, fade=2.0)


BUSHES = dict(intro=b_intro, animals=b_animals, onesound=b_onesound, ring=b_noise, wapow=b_noise, hatee=b_noise,
              joff=b_noise, chorus=b_chorus, verse2=b_verse2, horse=b_horse, speak=b_speak, chorus2=b_chorus,
              jacha=b_noise, fraka=b_noise, ahee=b_noise, aoo=b_noise, chorus3=b_chorus, mystery=b_mystery,
              whatsay=b_whatsay, angel=b_angel, finale=b_finale)
