r"""Make a storybook video for a pixel matrix: animated picture scenes that tell a song's story, timed to its lyrics.

Usage:
    python scripts/matrix_storybook.py STORY.py SONG.xsq OUT.mp4 [--size 30x40] [--fps 40] [--scale 10]
        [--sheet sheet.png --at 20,46.5,90] [--from 40 --to 60] [--ss 4] [--jobs 1]

HD: lay the story out on the matrix grid and set --k so grid x K is the video size, e.g. a 48x27 story with
--k 40 --ss 1 --scale 1 is a 1920x1080 video; pictures then come from Noto's SVGs (needs resvg_py) and words use a
TrueType font.

STORY.py defines build(tm) -> list of Scene, where tm is a Timing read from the sequence (lyric words from the
Lyrics track's word layer, Beats, Bars). Scenes run from their start to the next scene's start and crossfade into
the next one. Each scene is a stack of layers (backgrounds, emoji pictures, drawn props, words), drawn at 4x the
matrix size and box-filtered down so edges anti-alias into the LEDs; words are drawn after that, pixel-exact.

Pictures are Noto Emoji (Apache 2.0, fine in sold sequences), via lyric_images.icon_png's download cache.
The video is the matrix size blown up --scale times with nearest-neighbour so each LED is a solid block and the
xLights Video effect (aspect ratio off) samples exactly one colour per pixel.
"""

from __future__ import annotations

import argparse
import importlib.util
import html
import math
import os
import random
import subprocess
import sys
from collections import OrderedDict
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lyric_images import emoji_code, icon_png, is_file  # noqa: E402

SS = 4  # supersampling factor (per output pixel x K)
FLAT = False  # --flat: pictures posterised to a few solid colours with hard edges (pixel-art look)
K = 1  # output pixels per story pixel (--k): the story is laid out on the --size grid, drawn K times finer


def LW():
    """Line width on the supersampled canvas: one output pixel, but never thinner than a third of a story pixel
    (so drawn props stay visible in an HD video)."""
    return max(1, SS // K, SS // 3)
XF = 0.3  # crossfade seconds


# ---------------------------------------------------------------- timing

class Timing:
    def __init__(self, xsq: Path):
        root = ET.parse(xsq).getroot()
        self.duration = float(root.findtext("head/sequenceDuration") or 0)
        self.words: list[tuple[str, float, float]] = []
        self.beats: list[float] = []
        self.bars: list[float] = []
        self.sections: list[tuple[str, float]] = []
        for e in root.find("ElementEffects"):
            layers = e.findall("EffectLayer")
            if not layers:
                continue
            name = e.get("name")
            if name == "Lyrics" and len(layers) > 1:
                # xLights saves apostrophes as literal "&apos;" text inside labels: decode them
                self.words = [(html.unescape(f.get("label")), int(f.get("startTime")) / 1000,
                               int(f.get("endTime")) / 1000)
                              for f in layers[1] if f.get("label")]
            elif name == "Beats":
                self.beats = [int(f.get("startTime")) / 1000 for f in layers[0]]
            elif name == "Bars":
                self.bars = [int(f.get("startTime")) / 1000 for f in layers[0]]
            elif name == "Sections":
                self.sections = [(f.get("label"), int(f.get("startTime")) / 1000) for f in layers[0]]
            elif not self.beats and name not in ("Lyrics",) and layers[0] and all(
                    (f.get("label") or "").isdigit() for f in layers[0]):
                # no Beats track yet: a counted 1-2-3-4 track (e.g. a vendor's "Timing") gives beats and bars
                self._counted = [(f.get("label"), int(f.get("startTime")) / 1000) for f in layers[0]]
        if not self.beats and getattr(self, "_counted", None):
            self.beats = [s for _lab, s in self._counted]
            if not self.bars:
                self.bars = [s for lab, s in self._counted if lab == "1"]

    def w(self, key: str) -> float:
        """Start of a sung word: 'SHAKE#3' is the third SHAKE in the song (#1 if no number)."""
        word, _, n = key.partition("#")
        n = int(n or 1)
        for label, s, _e in self.words:
            if label == word:
                n -= 1
                if n == 0:
                    return s
        raise KeyError(key)

    def word_times(self, word: str, t0: float, t1: float) -> list[float]:
        return [s for label, s, _e in self.words if label == word and t0 <= s < t1]

    def beats_in(self, t0: float, t1: float) -> list[float]:
        return [b for b in self.beats if t0 <= b < t1]

    def word_at(self, t: float) -> tuple[str, float, float] | None:
        cur = None
        for wd in self.words:
            if wd[1] <= t:
                cur = wd
            else:
                break
        return cur


# ---------------------------------------------------------------- frame + scene

@dataclass
class Frame:
    img: Image.Image  # supersampled RGBA canvas
    t: float  # song time
    lt: float  # time since scene start
    start: float
    end: float
    tm: Timing
    post: list = field(default_factory=list)  # callables drawing on the native-size image

    @property
    def W(self):
        return self.img.width // SS

    @property
    def H(self):
        return self.img.height // SS


Layer = Callable[[Frame], None]


@dataclass
class Scene:
    start: float
    layers: list[Layer]
    name: str = ""
    cut: bool = False  # hard cut into this scene instead of a crossfade


def val(v, f: Frame):
    return v(f) if callable(v) else v


def ease(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def back_out(x: float) -> float:
    x = min(1.0, max(0.0, x))
    c = 1.7
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def since(hits, t: float) -> float | None:
    """Seconds since the latest hit at or before t."""
    best = None
    for h in hits:
        if h <= t:
            best = t - h
    return best


def kick(hits, t: float, tau: float = 0.25) -> float:
    s = since(hits, t)
    return 0.0 if s is None else math.exp(-s / tau)


def keyframes(points: list[tuple[float, float]], t: float, smooth: bool = True) -> float:
    """Interpolate (time, value) pairs at time t (absolute song time)."""
    if t <= points[0][0]:
        return points[0][1]
    for (t0, v0), (t1, v1) in zip(points, points[1:]):
        if t <= t1:
            x = (t - t0) / max(1e-6, t1 - t0)
            return v0 + (v1 - v0) * (ease(x) if smooth else x)
    return points[-1][1]


# ---------------------------------------------------------------- pictures

_icon_cache: OrderedDict = OrderedDict()
_src_cache: dict = {}
NOTO_SVG = "https://cdn.jsdelivr.net/gh/googlefonts/noto-emoji@v2.047/svg/emoji_u{}.svg"
SVG_CACHE = Path.home() / ".cache" / "xlights-mcp" / "noto-svg"
SVG_PX = 2048  # vector artwork is rasterised once at this size, then scaled down


def icon_svg(emoji: str) -> Image.Image | None:
    """Noto artwork rendered from its SVG (crisp in HD); None if no SVG or no resvg_py."""
    try:
        import io
        import requests
        import resvg_py
    except ImportError:
        return None
    if is_file(emoji):
        return None
    code = emoji_code(emoji)
    path = SVG_CACHE / f"{code}.svg"
    if not path.exists():
        r = requests.get(NOTO_SVG.format(code), timeout=30)
        if r.status_code != 200:
            return None
        SVG_CACHE.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")  # atomic: parallel renders may fetch at once
        tmp.write_bytes(r.content)
        try:
            os.replace(tmp, path)
        except OSError:  # another process got there first and has it open (Windows)
            tmp.unlink(missing_ok=True)
            if not path.exists():
                raise
    png = resvg_py.svg_to_bytes(svg_string=path.read_text(encoding="utf-8"), width=SVG_PX, height=SVG_PX)
    return Image.open(io.BytesIO(bytes(png))).convert("RGBA")


def icon_source(emoji: str, px: int) -> Image.Image:
    hd = px > 400
    key = (emoji, hd)
    if key not in _src_cache:
        src = (icon_svg(emoji) if hd else None) or icon_png(emoji)
        if src is None:
            raise SystemExit(f"no picture for {emoji!r}")
        _src_cache[key] = src.crop(src.getbbox())
    return _src_cache[key]


def flatten(im: Image.Image, colors: int = 8) -> Image.Image:
    """Pixel-art look: a few solid, saturated colours and hard (on/off) edges at the size it is drawn."""
    from PIL import ImageEnhance
    a = im.getchannel("A").point(lambda v: 255 if v >= 110 else 0)
    rgb = ImageEnhance.Color(im.convert("RGB")).enhance(1.5)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.15)
    q = rgb.quantize(colors=colors, method=Image.Quantize.MEDIANCUT).convert("RGB")
    q.putalpha(a)
    return q


def icon_image(emoji: str, px: int, flip: bool = False) -> Image.Image:
    key = (emoji, px, flip)
    if key in _icon_cache:
        _icon_cache.move_to_end(key)
        return _icon_cache[key]
    src = icon_source(emoji, px)
    sc = px / max(src.size)
    im = src.resize((max(1, round(src.width * sc)), max(1, round(src.height * sc))), Image.LANCZOS)
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if FLAT:
        im = flatten(im)
    _icon_cache[key] = im
    while len(_icon_cache) > 160:
        _icon_cache.popitem(last=False)
    return im


def paste_center(canvas: Image.Image, im: Image.Image, cx: float, cy: float, alpha: float = 1.0):
    if alpha <= 0.01:
        return
    if alpha < 0.999:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda a: int(a * alpha)))
    x, y = round(cx - im.width / 2), round(cy - im.height / 2)
    if x >= 0 and y >= 0 and x + im.width <= canvas.width and y + im.height <= canvas.height:
        canvas.alpha_composite(im, (x, y))
    else:
        _paste_clipped(canvas, im, cx, cy)


def _paste_clipped(canvas, im, cx, cy):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    layer.paste(im, (round(cx - im.width / 2), round(cy - im.height / 2)), im)
    canvas.alpha_composite(layer)


ENTER = {
    "grow": lambda e: dict(scale=back_out(e)),
    "pop": lambda e: dict(scale=back_out(e)),
    "fade": lambda e: dict(alpha=e),
    "left": lambda e: dict(dx=-(1 - ease(e)) * 30),
    "right": lambda e: dict(dx=(1 - ease(e)) * 30),
    "drop": lambda e: dict(dy=-(1 - back_out(e)) * 40),
    "rise": lambda e: dict(dy=(1 - ease(e)) * 40),
}


def icon(emoji: str, size, x, y, *, at: float | None = None, enter: str | None = "pop", enter_s: float = 0.4,
         until: float | None = None, exit_s: float = 0.3, motion: str | None = None, hits=None, amp: float = 1.0,
         rot=0.0, flip: bool = False, alpha=1.0, pivot_top: bool = False) -> Layer:
    """An emoji picture centred at native (x, y), size native pixels across its longest side.

    at/until: absolute song times it appears/leaves (default scene start/end). motion: bob, wobble, swing,
    pulse (scale kick on hits), bounce (jump on hits), shake (jitter on hits), float (drifts up).
    x, y, size, rot, alpha may be callables of the Frame.
    """

    def draw(f: Frame):
        t0 = f.start if at is None else at
        if f.t < t0:
            return
        e = (f.t - t0) / enter_s if enter else 1.0
        p = dict(scale=1.0, alpha=1.0, dx=0.0, dy=0.0, rot=0.0)
        if enter and e < 1:
            p.update(ENTER[enter](e))
        if until is not None:
            if f.t >= until:
                return
            p["alpha"] *= ease((until - f.t) / exit_s)
        lt = f.t - t0
        h = hits if hits is not None else f.tm.beats
        if motion == "bob":
            p["dy"] += math.sin(lt * 2 * math.pi * 0.8) * 0.7 * amp
        elif motion == "wobble":
            p["rot"] += math.sin(lt * 2 * math.pi * 1.2) * 8 * amp
        elif motion == "swing":
            p["rot"] += math.sin(lt * 2 * math.pi * 0.9) * 18 * amp
        elif motion == "pulse":
            p["scale"] *= 1 + 0.18 * amp * kick(h, f.t, 0.18)
        elif motion == "bounce":
            s = since(h, f.t)
            if s is not None and s < 0.35:
                p["dy"] -= math.sin(s / 0.35 * math.pi) * 3 * amp
        elif motion == "shake":
            k = kick(h, f.t, 0.3)
            p["dx"] += math.sin(f.t * 2 * math.pi * 9) * 1.5 * amp * k
            p["rot"] += math.sin(f.t * 2 * math.pi * 7) * 10 * amp * k
        elif motion == "float":
            p["dy"] -= lt * 2 * amp
        sz = val(size, f) * p["scale"]
        px = max(1, round(sz * SS))
        im = icon_image(emoji, px, flip)
        r = val(rot, f) + p["rot"]
        cx = (val(x, f) + p["dx"]) * SS
        cy = (val(y, f) + p["dy"]) * SS
        if abs(r) > 0.5:
            if pivot_top:
                # rotate about the top centre: pad so the top centre is the image centre
                pad = Image.new("RGBA", (im.width, im.height * 2), (0, 0, 0, 0))
                pad.paste(im, (0, im.height))
                cy -= im.height / 2  # the pivot (old top centre) is now the image centre
                im = pad.rotate(r, resample=Image.BICUBIC, expand=True)
            else:
                im = im.rotate(r, resample=Image.BICUBIC, expand=True)
        paste_center(f.img, im, cx, cy, p["alpha"] * val(alpha, f))

    return draw


# ---------------------------------------------------------------- backgrounds

_sky_cache: dict = {}


def sky(top=(0, 0, 18), bottom=(8, 10, 40)) -> Layer:
    """Vertical gradient, one colour per output-pixel row (one per LED row at --k 1, smooth in HD)."""

    def draw(f: Frame):
        key = (f.img.size, SS, K, tuple(top), tuple(bottom))
        if key not in _sky_cache:
            im = Image.new("RGBA", f.img.size)
            d = ImageDraw.Draw(im)
            h = f.img.height
            step = max(1, SS // K)
            for yy in range(0, h, step):
                k = yy / h
                c = tuple(round(a + (b - a) * k) for a, b in zip(top, bottom))
                d.rectangle([0, yy, f.img.width, yy + step - 1], fill=c + (255,))
            _sky_cache[key] = im
        f.img.paste(_sky_cache[key])
    return draw


def fill(color) -> Layer:
    def draw(f: Frame):
        f.img.paste(Image.new("RGBA", f.img.size, tuple(val(color, f)) + (255,)) if len(val(color, f)) == 3
                    else Image.new("RGBA", f.img.size, tuple(val(color, f))))
    return draw


def dot(d: ImageDraw.ImageDraw, x: float, y: float, c, r: float = 0.5):
    d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS - 1, (y + r) * SS - 1], fill=c)


def stars(n=18, seed=1, ymax=24, twinkle=1.0) -> Layer:
    rnd = random.Random(seed)
    pts = [(rnd.uniform(0, 30), rnd.uniform(0, ymax), rnd.uniform(0, 6.28), rnd.uniform(0.6, 1.6)) for _ in range(n)]

    def draw(f: Frame):
        d = ImageDraw.Draw(f.img)
        for x, y, ph, sp in pts:
            b = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(f.t * sp * 3 + ph)) ** 3 * twinkle
            c = round(255 * b)
            dot(d, (x * f.W / 30) % f.W, y * f.H / 40, (c, c, round(c * 0.85), 255), 0.5)
    return draw


def snow(n=40, seed=2, speed=4.0, wind=0.6, size=0.5, alpha=1.0) -> Layer:
    rnd = random.Random(seed)
    flakes = [(rnd.uniform(0, 30), rnd.uniform(0, 40), rnd.uniform(0.6, 1.4), rnd.uniform(0, 6.28),
               rnd.uniform(0.5, 1.0)) for _ in range(n)]

    def draw(f: Frame):
        a = val(alpha, f)
        if a <= 0:
            return
        d = ImageDraw.Draw(f.img)
        for x, y, sp, ph, b in flakes:
            yy = ((y + f.t * speed * sp) % 42 - 1) * f.H / 40
            xx = ((x + f.t * wind + math.sin(f.t * 1.5 + ph) * 0.8) % 30) * f.W / 30
            c = round(235 * b * a)
            dot(d, xx, yy, (c, c, min(255, c + 15), 255), size * (0.8 + 0.4 * b))
    return draw


def ground(top=33, color=(20, 90, 25), snowy=False, hill=1.5) -> Layer:
    def draw(f: Frame):
        d = ImageDraw.Draw(f.img)
        c = (225, 235, 250) if snowy else color
        d.ellipse([-f.W / 3 * SS, (top - hill) * SS, f.W * 4 / 3 * SS, (top + hill + 20) * SS], fill=tuple(c) + (255,))
        if (top + 2) * SS < f.img.height:
            d.rectangle([0, (top + 2) * SS, f.img.width, f.img.height], fill=tuple(c) + (255,))
        if not snowy:
            # a few darker grass tufts
            for i in range(round(8 * f.W / 30)):
                x = 2 + i * 3.7
                d.line([x * SS, (top + 1) * SS, (x + 0.5) * SS, (top - 0.3) * SS], fill=(40, 140, 40, 255), width=LW())
    return draw


def road(y=34, speed=14.0) -> Layer:
    def draw(f: Frame):
        d = ImageDraw.Draw(f.img)
        d.rectangle([0, y * SS, f.img.width, f.img.height], fill=(40, 40, 46, 255))
        off = (f.t * speed) % 8
        for i in range(-1, 6):
            x = i * 8 - off
            d.rectangle([x * SS, (y + 2.5) * SS, (x + 4) * SS, (y + 3.25) * SS], fill=(230, 200, 40, 255))
    return draw


def glow(x, y, r, color, strength=0.6) -> Layer:
    def draw(f: Frame):
        lay = Image.new("RGBA", f.img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        cx, cy, rr = val(x, f) * SS, val(y, f) * SS, val(r, f) * SS
        st = val(strength, f)
        for i in range(8, 0, -1):
            k = i / 8
            a = round(255 * st * (1 - k) ** 1.5)
            d.ellipse([cx - rr * k, cy - rr * k, cx + rr * k, cy + rr * k], fill=tuple(color) + (a,))
        f.img.alpha_composite(lay)
    return draw


def spotlight(x=15, color=(255, 230, 150), strength=0.35) -> Layer:
    def draw(f: Frame):
        lay = Image.new("RGBA", f.img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        cx = val(x, f) * SS
        h = f.H * SS
        d.polygon([(cx - 2 * SS, 0), (cx + 2 * SS, 0), (cx + 13 * SS, h), (cx - 13 * SS, h)],
                  fill=tuple(color) + (round(255 * strength),))
        f.img.alpha_composite(lay)
    return draw


def siren(hz=3.0) -> Layer:
    def draw(f: Frame):
        d = ImageDraw.Draw(f.img)
        ph = (f.t * hz) % 1
        left = (150, 0, 0) if ph < 0.5 else (0, 0, 150)
        right = (0, 0, 150) if ph < 0.5 else (150, 0, 0)
        d.rectangle([0, 0, f.img.width // 2 - 1, f.img.height], fill=left + (255,))
        d.rectangle([f.img.width // 2, 0, f.img.width, f.img.height], fill=right + (255,))
    return draw


def confetti(n=30, seed=5, colors=((255, 40, 40), (40, 220, 60), (255, 210, 30), (60, 140, 255), (255, 80, 220)),
             speed=7.0, at: float | None = None) -> Layer:
    rnd = random.Random(seed)
    bits = [(rnd.uniform(0, 30), rnd.uniform(-40, 0), rnd.uniform(0.7, 1.3), rnd.choice(colors), rnd.uniform(0, 6))
            for _ in range(n)]

    def draw(f: Frame):
        t0 = f.start if at is None else at
        if f.t < t0:
            return
        d = ImageDraw.Draw(f.img)
        lt = f.t - t0
        for x, y, sp, c, ph in bits:
            yy = y + lt * speed * sp
            if yy > 41:
                yy = (yy % 44) - 2
            yy *= f.H / 40
            xx = x * f.W / 30 + math.sin(lt * 3 + ph) * 1.2
            d.rectangle([xx * SS, yy * SS, (xx + 0.75) * SS, (yy + 0.75) * SS], fill=c + (255,))
    return draw


def sparkles(n=8, seed=7, box=(0, 0, 30, 40), color=(255, 255, 220), rate=2.0) -> Layer:
    rnd = random.Random(seed)
    sp = [(rnd.uniform(box[0], box[2]), rnd.uniform(box[1], box[3]), rnd.uniform(0, 1), rnd.uniform(0.7, 1.3))
          for _ in range(n)]

    def draw(f: Frame):
        d = ImageDraw.Draw(f.img)
        for x, y, ph, r in sp:
            k = (f.t * rate * r + ph) % 1
            b = math.sin(k * math.pi) ** 4
            if b < 0.05:
                continue
            c = tuple(round(v * b) for v in color) + (255,)
            dot(d, x, y, c, 0.5)
            if b > 0.6:
                cc = tuple(round(v * b * 0.5) for v in color) + (255,)
                for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    dot(d, x + ddx, y + ddy, cc, 0.5)
    return draw


def fireworks(hits, seed=9, colors=((255, 60, 60), (60, 255, 90), (255, 220, 40), (90, 160, 255), (255, 90, 230))
              ) -> Layer:
    rnd = random.Random(seed)
    bursts = [(h, rnd.uniform(6, 24), rnd.uniform(5, 16), rnd.choice(colors)) for h in hits]

    def draw(f: Frame):
        d = ImageDraw.Draw(f.img)
        for h, x, y, c in bursts:
            s = f.t - h
            if not 0 <= s < 1.3:
                continue
            r = 7 * (1 - math.exp(-s * 4))
            b = (1 - s / 1.3) ** 1.5
            for i in range(12):
                a = i / 12 * 2 * math.pi
                dot(d, x + math.cos(a) * r, y + math.sin(a) * r + s * s * 2,
                    tuple(round(v * b) for v in c) + (255,), 0.5)
            if s < 0.15:
                dot(d, x, y, (255, 255, 255, 255), 1.0)
    return draw


def steam(x, y, n=3, height=8, color=(200, 200, 210)) -> Layer:
    def draw(f: Frame):
        lay = Image.new("RGBA", f.img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for i in range(n):
            ox = val(x, f) + (i - (n - 1) / 2) * 2.2
            for j in range(10):
                k = ((f.t * 0.8 + i * 0.33 + j / 10) % 1)
                yy = val(y, f) - k * height
                xx = ox + math.sin(k * 6 + f.t * 2 + i) * 0.9
                a = round(220 * math.sin(k * math.pi))
                d.ellipse([(xx - 0.45) * SS, (yy - 0.45) * SS, (xx + 0.45) * SS, (yy + 0.45) * SS],
                          fill=tuple(color) + (a,))
        f.img.alpha_composite(lay)
    return draw


def rising(emoji: str, n=5, seed=11, size=4, box=(4, 26), speed=5.0, at: float | None = None) -> Layer:
    """Small pictures (hearts...) floating up and fading."""
    rnd = random.Random(seed)
    items = [(rnd.uniform(*box), rnd.uniform(0, 1)) for _ in range(n)]

    def draw(f: Frame):
        t0 = f.start if at is None else at
        if f.t < t0:
            return
        im = icon_image(emoji, size * SS)
        for x, ph in items:
            k = ((f.t - t0) * speed / 40 + ph) % 1
            yy = f.H - k * (f.H + 4)
            xx = x + math.sin(k * 8 + ph * 6) * 1.5
            paste_center(f.img, im, xx * SS, yy * SS, math.sin(k * math.pi))
    return draw


# ---------------------------------------------------------------- drawn props

def snow_globe(content: list[tuple[str, float, float, float]], hits, cx=15.0, cy=16.5, r=12.5, seed=3,
               at: float | None = None, enter: str | None = "pop") -> Layer:
    """A snow globe on a red base. content: (emoji, size, x, y) placed inside, relative to the globe centre.
    hits: song times it gets shaken (it jolts, the snow swirls up, then settles)."""
    rnd = random.Random(seed)
    flakes = []
    for _ in range(46):
        ang = rnd.uniform(0, 2 * math.pi)
        rr = math.sqrt(rnd.uniform(0.02, 1)) * (r - 1.5)
        rest_x = rnd.uniform(-r * 0.7, r * 0.7)
        rest_y = r * 0.55 + rnd.uniform(-0.8, 0.8) - abs(rest_x) * 0.12
        flakes.append((ang, rr, rnd.uniform(0.8, 2.2) * rnd.choice((-1, 1)), rest_x, rest_y, rnd.uniform(0.6, 1)))

    def draw(f: Frame):
        t0 = f.start if at is None else at
        if f.t < t0:
            return
        e = (f.t - t0) / 0.5
        scale = back_out(e) if (enter and e < 1) else 1.0
        # agitation: jumps to 1 on each hit, decays over ~2 s
        a = 0.0
        last = None
        for h in hits:
            if h <= f.t:
                a = min(1.0, (a * math.exp(-(h - last) / 1.8) if last is not None else 0) + 0.85)
                last = h
        if last is not None:
            a *= math.exp(-(f.t - last) / 1.8)
        jolt = kick(hits, f.t, 0.28)
        dx = math.sin(f.t * 2 * math.pi * 8) * 1.4 * jolt
        rot = math.sin(f.t * 2 * math.pi * 6) * 7 * jolt

        size = 32 * SS
        lay = Image.new("RGBA", (size, round(size * 1.25)), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        gx, gy, R = size / 2, r * SS + SS, r * SS
        # inside: dark blue water
        mask = Image.new("L", lay.size, 0)
        ImageDraw.Draw(mask).ellipse([gx - R, gy - R, gx + R, gy + R], fill=255)
        inner = Image.new("RGBA", lay.size, (0, 0, 0, 0))
        di = ImageDraw.Draw(inner)
        di.ellipse([gx - R, gy - R, gx + R, gy + R], fill=(12, 22, 60, 255))
        di.ellipse([gx - R * 1.1, gy + R * 0.45, gx + R * 1.1, gy + R * 1.6], fill=(215, 225, 245, 255))
        for em, sz, ox, oy in content:
            im = icon_image(em, round(sz * SS))
            inner.alpha_composite(im, (round(gx + ox * SS - im.width / 2), round(gy + oy * SS - im.height / 2)))
        # snow
        for ang, rr, w, rx, ry, b in flakes:
            sx = math.cos(ang + f.t * w) * rr
            sy = math.sin(ang + f.t * w) * rr
            fx = rx + (sx - rx) * a
            fy = ry + (sy - ry) * a
            c = round(255 * b)
            di.ellipse([gx + (fx - 0.5) * SS, gy + (fy - 0.5) * SS, gx + (fx + 0.5) * SS - 1,
                        gy + (fy + 0.5) * SS - 1], fill=(c, c, min(255, c + 10), 255))
        lay.paste(inner, (0, 0), mask)
        # glass rim and shine
        d.ellipse([gx - R, gy - R, gx + R, gy + R], outline=(110, 160, 220, 255), width=LW())
        d.arc([gx - R + 2.5 * SS, gy - R + 2.5 * SS, gx + R - 2.5 * SS, gy + R - 2.5 * SS], 200, 250,
              fill=(230, 240, 255, 255), width=LW())
        # base
        top = gy + R * 0.82
        d.polygon([(gx - R * 0.85, top), (gx + R * 0.85, top), (gx + R * 1.0, top + 7 * SS),
                   (gx - R * 1.0, top + 7 * SS)], fill=(170, 18, 18, 255))
        d.rectangle([gx - R * 0.92, top + 2.5 * SS, gx + R * 0.92, top + 3.5 * SS], fill=(230, 180, 40, 255))
        if abs(rot) > 0.3:
            lay = lay.rotate(rot, resample=Image.BICUBIC, center=(gx, top + 7 * SS))
        if scale != 1.0:
            lay = lay.resize((max(1, round(lay.width * scale)), max(1, round(lay.height * scale))), Image.LANCZOS)
        paste_center(f.img, lay, (cx + dx) * SS, (cy + (lay.height / SS / 2 - (gy / SS) * scale)) * SS)

    return draw


def cinnamon_roll(cx=15, cy=21, r=11, at: float | None = None) -> Layer:
    def draw(f: Frame):
        t0 = f.start if at is None else at
        if f.t < t0:
            return
        s = back_out((f.t - t0) / 0.45)
        R = r * SS * s
        if R < 1:
            return
        lay = Image.new("RGBA", f.img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        x, y = cx * SS, cy * SS
        d.ellipse([x - R, y - R, x + R, y + R], fill=(200, 125, 55, 255))
        # spiral of cinnamon
        pts = []
        spin = f.t * 1.2
        for i in range(160):
            k = i / 160
            a = k * 3.2 * 2 * math.pi + spin
            rr = R * 0.92 * k
            pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
        d.line(pts, fill=(105, 50, 15, 255), width=LW())
        # icing drizzle
        for row in (-0.35, 0.3):
            ip = [(x + (i / 30 * 1.5 - 0.75) * R, y + (row + math.sin(i / 30 * 2 * math.pi * 1.5) * 0.12) * R)
                  for i in range(31)]
            d.line(ip, fill=(250, 245, 235, 255), width=LW())
        f.img.alpha_composite(lay)
    return draw


def mistletoe(cx=15, top=0, length=11, at: float | None = None) -> Layer:
    def draw(f: Frame):
        t0 = f.start if at is None else at
        if f.t < t0:
            return
        drop = back_out((f.t - t0) / 0.5)
        ang = math.sin((f.t - t0) * 2 * math.pi * 0.7) * 0.18
        ln = length * drop
        hx = cx + math.sin(ang) * ln
        hy = top + math.cos(ang) * ln
        d = ImageDraw.Draw(f.img)
        d.line([cx * SS, top * SS, hx * SS, hy * SS], fill=(200, 30, 40, 255), width=max(1, LW() // 2))
        for a, l in ((-0.9, 5), (-0.3, 5.5), (0.35, 5.5), (0.95, 5)):
            aa = math.pi / 2 + a + ang
            ex, ey = hx + math.cos(aa) * l, hy + math.sin(aa) * l
            mx, my = (hx + ex) / 2, (hy + ey) / 2
            nx, ny = -math.sin(aa) * 1.3, math.cos(aa) * 1.3
            d.polygon([(hx * SS, hy * SS), ((mx + nx) * SS, (my + ny) * SS), (ex * SS, ey * SS),
                       ((mx - nx) * SS, (my - ny) * SS)], fill=(40, 150, 50, 255))
        for bx, by in ((-0.8, 0.6), (0.8, 0.6), (0, 1.4)):
            dot(d, hx + bx, hy + by, (240, 30, 40, 255), 0.85)
        # bow
        d.polygon([(hx * SS, hy * SS), ((hx - 2.2) * SS, (hy - 1.4) * SS), ((hx - 2.2) * SS, (hy + 1.0) * SS)],
                  fill=(220, 20, 30, 255))
        d.polygon([(hx * SS, hy * SS), ((hx + 2.2) * SS, (hy - 1.4) * SS), ((hx + 2.2) * SS, (hy + 1.0) * SS)],
                  fill=(220, 20, 30, 255))
    return draw


def tinsel(box=(6, 9, 24, 33), color=(255, 205, 40), loops=4) -> Layer:
    """Gold tinsel tangled across a tree: wandering loops that crawl and glint."""

    def draw(f: Frame):
        d = ImageDraw.Draw(f.img)
        x0, y0, x1, y1 = box
        for j in range(loops):
            pts = []
            for i in range(60):
                k = i / 59
                y = y0 + (y1 - y0) * (j + 0.6) / loops + math.sin(k * 9 + j * 2 + f.t * 2.5) * 1.8
                half = (x1 - x0) / 2 * ((y - y0) / (y1 - y0)) * 0.9 + 1
                x = (x0 + x1) / 2 + (k * 2 - 1) * half + math.sin(k * 17 + f.t * 3 + j) * 1.2
                pts.append((x * SS, y * SS))
            d.line(pts, fill=color + (255,), width=LW())
            gl = (f.t * 1.7 + j * 0.37) % 1
            gx, gy = pts[int(gl * 59)]
            d.ellipse([gx - SS, gy - SS, gx + SS, gy + SS], fill=(255, 255, 230, 255))
    return draw


def pour(x0, y0, x1, y1, color=(190, 110, 40), at: float | None = None) -> Layer:
    def draw(f: Frame):
        t0 = f.start if at is None else at
        if f.t < t0:
            return
        d = ImageDraw.Draw(f.img)
        n = 14
        for i in range(n):
            k = ((f.t * 2 + i / n) % 1)
            x = x0 + (x1 - x0) * k
            y = y0 + (y1 - y0) * k * k
            dot(d, x, y, color + (255,), 0.55)
    return draw


def tree_lights(box=(6, 7, 24, 33), n=16, seed=13, hits=None) -> Layer:
    """Twinkling coloured bulbs over a tree picture."""
    rnd = random.Random(seed)
    cols = [(255, 40, 40), (255, 210, 40), (60, 140, 255), (255, 80, 220), (255, 255, 255)]
    pts = []
    x0, y0, x1, y1 = box
    while len(pts) < n:
        y = rnd.uniform(y0 + 4, y1 - 3)
        half = (x1 - x0) / 2 * (y - y0) / (y1 - y0) * 0.8
        pts.append(((x0 + x1) / 2 + rnd.uniform(-half, half), y, rnd.choice(cols), rnd.uniform(0, 6)))

    def draw(f: Frame):
        d = ImageDraw.Draw(f.img)
        k = kick(hits, f.t, 0.3) if hits else 0
        for x, y, c, ph in pts:
            b = 0.35 + 0.65 * max(k, (0.5 + 0.5 * math.sin(f.t * 4 + ph)) ** 2)
            dot(d, x, y, tuple(round(v * b) for v in c) + (255,), 0.6)
    return draw


def dim(amount) -> Layer:
    """Darken everything drawn so far (amount 0..1, may be a callable)."""

    def draw(f: Frame):
        a = val(amount, f)
        if a > 0:
            f.img.alpha_composite(Image.new("RGBA", f.img.size, (0, 0, 0, round(255 * min(1, a)))))
    return draw


# ---------------------------------------------------------------- words (drawn pixel-exact, after downsampling)

FONT = {
    "A": [".#.", "#.#", "###", "#.#", "#.#"], "B": ["##.", "#.#", "##.", "#.#", "##."],
    "C": [".##", "#..", "#..", "#..", ".##"], "D": ["##.", "#.#", "#.#", "#.#", "##."],
    "E": ["###", "#..", "##.", "#..", "###"], "F": ["###", "#..", "##.", "#..", "#.."],
    "G": [".##", "#..", "#.#", "#.#", ".##"], "H": ["#.#", "#.#", "###", "#.#", "#.#"],
    "I": ["###", ".#.", ".#.", ".#.", "###"], "J": ["..#", "..#", "..#", "#.#", ".#."],
    "K": ["#.#", "#.#", "##.", "#.#", "#.#"], "L": ["#..", "#..", "#..", "#..", "###"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"], "N": ["#..#", "##.#", "#.##", "#..#", "#..#"],
    "O": [".#.", "#.#", "#.#", "#.#", ".#."], "P": ["##.", "#.#", "##.", "#..", "#.."],
    "R": ["##.", "#.#", "##.", "#.#", "#.#"], "S": [".##", "#..", ".#.", "..#", "##."],
    "T": ["###", ".#.", ".#.", ".#.", ".#."], "U": ["#.#", "#.#", "#.#", "#.#", "###"],
    "V": ["#.#", "#.#", "#.#", "#.#", ".#."], "W": ["#...#", "#...#", "#.#.#", "##.##", "#...#"],
    "X": ["#.#", "#.#", ".#.", "#.#", "#.#"], "Y": ["#.#", "#.#", ".#.", ".#.", ".#."],
    "!": [".#.", ".#.", ".#.", "...", ".#."], "'": [".#.", ".#.", "...", "...", "..."],
    " ": ["..", "..", "..", "..", ".."],
}


HD_FONT_URL = "https://raw.githubusercontent.com/google/fonts/main/apache/luckiestguy/LuckiestGuy-Regular.ttf"
FONT_CACHE = Path.home() / ".cache" / "xlights-mcp" / "fonts"
_hd_fonts: dict = {}


def hd() -> bool:
    """HD output (--k 8 or more): words use a TrueType font instead of the 3x5 LED font."""
    return K >= 8


def hd_font(scale: int):
    """A font whose capitals are as tall as the 3x5 font's 5 rows at this scale (Luckiest Guy, OFL/Apache)."""
    if scale not in _hd_fonts:
        from PIL import ImageFont
        path = FONT_CACHE / "LuckiestGuy-Regular.ttf"
        if not path.exists():
            try:
                import requests
                r = requests.get(HD_FONT_URL, timeout=30)
                r.raise_for_status()
                FONT_CACHE.mkdir(parents=True, exist_ok=True)
                path.write_bytes(r.content)
            except Exception:  # noqa: BLE001 - fall back to a system font
                path = Path("C:/Windows/Fonts/arialbd.ttf")
        size = 10
        font = ImageFont.truetype(str(path), size)
        cap = font.getbbox("H")[3] - font.getbbox("H")[1]
        _hd_fonts[scale] = ImageFont.truetype(str(path), max(4, round(size * 5 * scale / cap)))
    return _hd_fonts[scale]


def text_width(s: str, scale: int = 1) -> int:
    if hd():
        return round(hd_font(scale).getlength(s)) + 2 * max(2, scale // 2)
    return sum(len(FONT.get(ch, FONT[" "])[0]) + 1 for ch in s) * scale - scale


def blit_text(img: Image.Image, s: str, x: int, y: int, color, scale: int = 1, shadow=True):
    if hd():
        font = hd_font(scale)
        sw = max(2, scale // 2)
        top = font.getbbox("H")[1]
        ImageDraw.Draw(img).text((x + sw, y - top), s, font=font, fill=tuple(color),
                                 stroke_width=sw if shadow else 0, stroke_fill=(0, 0, 0))
        return
    px = img.load()
    W, H = img.size
    for pas in ((1, (0, 0, 0)), (0, color)) if shadow else ((0, color),):
        off, c = pas
        cx = x
        for ch in s:
            g = FONT.get(ch, FONT[" "])
            for gy, row in enumerate(g):
                for gx, on in enumerate(row):
                    if on == "#":
                        for sy in range(scale):
                            for sx in range(scale):
                                X, Y = cx + gx * scale + sx + off, y + gy * scale + sy + off
                                if 0 <= X < W and 0 <= Y < H:
                                    px[X, Y] = tuple(c)
            cx += (len(g[0]) + 1) * scale


def text(s: str, y: int, color=(255, 255, 255), scale: int = 1, *, at: float | None = None,
         until: float | None = None, scroll: float = 0.0, blink: float = 0.0) -> Layer:
    """Words in a 3x5 pixel font, centred (or scrolling right-to-left at scroll px/s)."""

    def draw(f: Frame):
        t0 = f.start if at is None else at
        if f.t < t0 or (until is not None and f.t >= until):
            return
        if blink and ((f.t - t0) * blink) % 1 > 0.6:
            return

        def post(img):
            sk = scale * K
            w = text_width(s, sk)
            if scroll:
                x = round(img.width - (f.t - t0) * scroll * K)
                if x < -w:
                    return
            else:
                x = (img.width - w) // 2
            blit_text(img, s, x, y * K, val(color, f), sk)
        f.post.append(post)
    return draw


def sung_words(words: dict[str, str], y: int, color=(255, 255, 255), scale: int = 1, hold: float = 0.7,
               colors: dict[str, tuple] | None = None) -> Layer:
    """Show each sung word (key, from the Lyrics words) as it's sung, as the mapped text."""

    def draw(f: Frame):
        cur = f.tm.word_at(f.t)
        if not cur or cur[0] not in words or f.t - cur[1] > max(hold, cur[2] - cur[1]):
            return
        s = words[cur[0]]
        c = (colors or {}).get(cur[0], color)
        k = f.t - cur[1]
        sc = scale * K

        def post(img):
            yy = (y - (1 if k < 0.08 else 0)) * K
            for line_i, line in enumerate(s.split("/")):
                blit_text(img, line, (img.width - text_width(line, sc)) // 2, yy + line_i * 6 * sc, c, sc)
        f.post.append(post)
    return draw


# ---------------------------------------------------------------- render

def render_scene(scene: Scene, t: float, end: float, tm: Timing, W: int, H: int) -> Image.Image:
    f = Frame(Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 255)), t, t - scene.start, scene.start, end, tm)
    for layer in scene.layers:
        layer(f)
    small = f.img.convert("RGB").resize((W * K, H * K), Image.BOX)
    for p in f.post:
        p(small)
    return small


def render(scenes: list[Scene], t: float, tm: Timing, W: int, H: int) -> Image.Image:
    i = max(0, max((k for k, s in enumerate(scenes) if s.start <= t), default=0))
    end = scenes[i + 1].start if i + 1 < len(scenes) else tm.duration
    img = render_scene(scenes[i], t, end, tm, W, H)
    if i + 1 < len(scenes) and not scenes[i + 1].cut and t > end - XF:
        nxt = render_scene(scenes[i + 1], t, scenes[i + 2].start if i + 2 < len(scenes) else tm.duration, tm, W, H)
        img = Image.blend(img, nxt, ease((t - (end - XF)) / XF))
    return img


def load_story(path: Path):
    spec = importlib.util.spec_from_file_location("story", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_worker: dict = {}


def _setup(story: Path, xsq: Path, k: int, ss: int, flat: bool = False):
    global SS, K, FLAT
    FLAT = flat
    K = k
    SS = ss * k
    tm = Timing(xsq)
    return tm, sorted(load_story(story).build(tm), key=lambda s: s.start)


def _init_worker(story, xsq, k, ss, W, H, flat=False):
    tm, scenes = _setup(story, xsq, k, ss, flat)
    _worker.update(tm=tm, scenes=scenes, W=W, H=H)


def _frame(t: float) -> bytes:
    w = _worker
    return render(w["scenes"], t, w["tm"], w["W"], w["H"]).tobytes()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("story", type=Path)
    ap.add_argument("xsq", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--size", default="30x40", help="matrix WxH in pixels")
    ap.add_argument("--k", type=int, default=1, help="output resolution multiple (2 = a 60x80 video for a 30x40 story)")
    ap.add_argument("--flat", action="store_true", help="posterise pictures to a few solid colours (pixel-art look)")
    ap.add_argument("--ss", type=int, default=4, help="supersampling per output pixel (1 is plenty for HD)")
    ap.add_argument("--jobs", type=int, default=1, help="render frames in this many processes")
    ap.add_argument("--fps", type=int, default=40)
    ap.add_argument("--scale", type=int, default=10, help="block size in the video per output pixel")
    ap.add_argument("--sheet", type=Path, help="write a contact sheet of the --at times instead of the video")
    ap.add_argument("--at", default="", help="comma-separated times for --sheet")
    ap.add_argument("--from", dest="t_from", type=float, default=0.0)
    ap.add_argument("--to", dest="t_to", type=float, default=None)
    a = ap.parse_args()
    W, H = (int(v) for v in a.size.lower().split("x"))
    tm, scenes = _setup(a.story, a.xsq, a.k, a.ss, a.flat)

    if a.sheet:
        times = [float(v) for v in a.at.split(",") if v] or [s.start + 1.0 for s in scenes]
        cols = min(8, len(times))
        rows = math.ceil(len(times) / cols)
        z = 6
        sheet = Image.new("RGB", (cols * (W * z + 8), rows * (H * z + 18)), (40, 40, 40))
        d = ImageDraw.Draw(sheet)
        for k, t in enumerate(times):
            im = render(scenes, t, tm, W, H).resize((W * z, H * z), Image.NEAREST)
            x, y = (k % cols) * (W * z + 8), (k // cols) * (H * z + 18)
            sheet.paste(im, (x, y))
            d.text((x + 2, y + H * z + 3), f"{t:.1f}", fill=(220, 220, 220))
        sheet.save(a.sheet)
        print(f"wrote {a.sheet}")
        return

    t_end = a.t_to if a.t_to is not None else tm.duration
    n = int((t_end - a.t_from) * a.fps)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W * K}x{H * K}", "-r", str(a.fps),
           "-i", "-", "-vf", f"scale={W * K * a.scale}:{H * K * a.scale}:flags=neighbor", "-c:v", "libx264", "-crf", "14",
           "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(a.out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    times = [a.t_from + k / a.fps for k in range(n)]
    if a.jobs > 1:
        import multiprocessing as mp
        with mp.Pool(a.jobs, _init_worker, (a.story, a.xsq, a.k, a.ss, W, H, a.flat)) as pool:
            for k, buf in enumerate(pool.imap(_frame, times, chunksize=4)):
                p.stdin.write(buf)
                if k % (a.fps * 10) == 0:
                    print(f"  {times[k]:6.1f}s", flush=True)
    else:
        for k, t in enumerate(times):
            p.stdin.write(render(scenes, t, tm, W, H).tobytes())
            if k % (a.fps * 10) == 0:
                print(f"  {t:6.1f}s", flush=True)
    p.stdin.close()
    p.wait()
    print(f"wrote {a.out} ({n} frames, {n / a.fps:.1f}s)")


if __name__ == "__main__":
    # run through the importable module so the story (which imports matrix_storybook) shares its SS/K settings
    import matrix_storybook
    matrix_storybook.main()
