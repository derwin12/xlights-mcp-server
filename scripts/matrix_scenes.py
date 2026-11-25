r"""Matrix scenes: a SuperStar-style picture story for a pixel matrix, written as xLights effects instead of a video.

Usage (from scripts/):
    python matrix_scenes.py STORY.py SONG.xsq --model NAME --size WxH --out OUT.xsq
    python matrix_scenes.py STORY.py SONG.xsq --model NAME --size WxH --sheet SHEET.png --at 3,8.5,12
    python matrix_scenes.py STORY.py SONG.xsq --model NAME --size WxH --preview PREVIEW.mp4 [--from 0 --to 30]

matrix_storybook.py draws every frame of the song into one long MP4 for a Video effect. This builds the same kind of
story from short effects on the matrix, the way a LOR SuperStar import builds the MegaTree:
  - pictures (Noto emoji posterised to flat colours, 3x5 pixel words, PIL-drawn props) are small PNGs at LED size,
    embedded in the sequence's <SequenceMedia> (nothing on disk), shown with Pictures effects: "none" to hold,
    "vector" to slide between pixel offsets, start/end scale to pop;
  - Morph bars sweep across on phrases, Shockwave rings burst on accents, Twinkle / Snowflakes / Color Wash
    fill the background - all ordinary effects that render fast and can be edited on the timeline.

STORY.py defines build(s: Story). s.cues has the word and beat times (see Cues); s.W/s.H is the matrix size.
Positions are sprite centres in LED pixels, x right and y down from the top-left LED.

Layers: every effect has a z (higher is in front). Effects are packed into layers per z, highest z first,
so the story never has to number layers itself.

--sheet / --preview draw a rough local preview (pictures exact; Morph, Shockwave, Twinkle and Snowflakes
approximated). Check the real thing in xLights before calling a scene done.
"""

from __future__ import annotations

import argparse
import base64
import importlib.util
import io
import json
import math
import random
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matrix_storybook as mb  # noqa: E402

mb.SS, mb.K, mb.FLAT = 1, 1, True
FRAME = 0.025  # 25 ms sequences: every time is snapped to a frame


def snap(t: float) -> int:
    """Seconds -> milliseconds on the frame grid."""
    return int(round(t / FRAME)) * int(FRAME * 1000)


def hexc(c) -> str:
    return "#{:02X}{:02X}{:02X}".format(*c[:3])


def palette(*colors) -> str:
    """A ColorPalette string with these colours checked (up to 8)."""
    base = ["#FFFFFF", "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#000000", "#00FFFF", "#FF00FF"]
    for i, c in enumerate(colors[:8]):
        base[i] = hexc(c)
    parts = [f"C_BUTTON_Palette{i + 1}={v}" for i, v in enumerate(base)]
    parts += [f"C_CHECKBOX_Palette{i + 1}=1" for i in range(len(colors[:8]))]
    return ",".join(parts)


# ---------------------------------------------------------------- cues

def norm(w: str) -> str:
    return re.sub(r"[^a-z]", "", w.lower())


class Cues:
    """Word and beat times (seconds). words: [(word, start, end)], beats: [t]; bars are every 4th beat."""

    def __init__(self, words, beats, duration):
        self.words = [(norm(w), s, e) for w, s, e in words]
        self.beats = sorted(beats)
        self.bars = self.beats[::4]
        self.duration = duration

    @classmethod
    def from_files(cls, words_json: Path, beats_json: Path, duration: float):
        """words_json from transcribe_words.py (phrases with words [{w, s, e}]), beats_json a list of times."""
        words = [(w["w"], w["s"], w["e"]) for p in json.loads(Path(words_json).read_text()) for w in p["words"]]
        return cls(words, json.loads(Path(beats_json).read_text()), duration)

    @classmethod
    def from_xsq(cls, xsq: Path):
        tm = mb.Timing(xsq)
        return cls(tm.words, tm.beats, tm.duration)

    def w(self, word: str, after: float = 0.0) -> float:
        """Start of the first sung word beginning with `word` at or after `after`."""
        key = norm(word)
        for w, s, _ in self.words:
            if s >= after - 0.05 and w.startswith(key):
                return s
        raise KeyError(f"no word {word!r} after {after:.2f}")

    def w_end(self, word: str, after: float = 0.0) -> float:
        key = norm(word)
        for w, s, e in self.words:
            if s >= after - 0.05 and w.startswith(key):
                return e
        raise KeyError(f"no word {word!r} after {after:.2f}")

    def beats_in(self, t0: float, t1: float) -> list[float]:
        return [b for b in self.beats if t0 <= b < t1]

    def bars_in(self, t0: float, t1: float) -> list[float]:
        return [b for b in self.bars if t0 <= b < t1]

    def beat_after(self, t: float) -> float:
        return next((b for b in self.beats if b >= t), t)


# ---------------------------------------------------------------- effects

@dataclass
class Fx:
    name: str
    t0: int  # ms
    t1: int
    settings: dict
    palette: str | None
    z: int
    look: dict = field(default_factory=dict)  # what the preview needs


class Story:
    def __init__(self, W: int, H: int, cues: Cues, prefix: str, images: dict | None = None):
        self.W, self.H, self.cues, self.prefix = W, H, cues, prefix
        self.fx: list[Fx] = []
        self.images: dict[str, Image.Image] = {} if images is None else images  # a Stage shares one set

    # ------------------------------------------------ pictures (assets)

    def _key(self, name: str) -> str:
        return f"MatrixScenes/{self.prefix}/{name}.png"

    def image(self, name: str, im: Image.Image) -> str:
        """Register a picture; returns its media path (the Pictures effect's filename)."""
        im = im.convert("RGBA")
        bb = im.getchannel("A").getbbox()
        im = im.crop(bb) if bb else im
        a = im.getchannel("A").point(lambda v: 255 if v >= 110 else 0)  # hard edges: an LED is on or off
        im.putalpha(a)
        key = self._key(name)
        self.images[key] = im
        return key

    def emoji(self, e: str, px: int, flip: bool = False) -> str:
        code = "-".join(f"{ord(c):x}" for c in e if ord(c) != 0xFE0F)
        key = self._key(f"{code}_{px}{'f' if flip else ''}")
        if key not in self.images:
            self.image(key.rsplit("/", 1)[1][:-4], mb.icon_image(e, px, flip))
        return key

    def word(self, s: str, color=(255, 255, 255), scale: int = 1, shadow: bool = False) -> str:
        w = mb.text_width(s, scale) + 2
        im = Image.new("RGBA", (w, 5 * scale + 2), (0, 0, 0, 0))
        mb.blit_text(im, s, 0, 0, tuple(color) + (255,), scale, shadow=shadow)
        return self.image(f"w_{norm(s) or 'x'}_{hexc(color)[1:]}_{scale}", im)

    def drawn(self, name: str, w: int, h: int, draw) -> str:
        """A PIL-drawn prop: draw(ImageDraw, Image) on a transparent w x h canvas."""
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw(ImageDraw.Draw(im), im)
        return self.image(name, im)

    def size(self, key: str) -> tuple[int, int]:
        return self.images[key].size

    # ------------------------------------------------ pictures (effects)

    def _offsets(self, key: str, x: float, y: float) -> tuple[int, int]:
        """Sprite centre (x, y down) -> Pictures pixel offsets (PicturesEffect.cpp NONE/VECTOR mapping)."""
        iw, ih = self.size(key)
        left, top = round(x - iw / 2), round(y - ih / 2)
        xc = left + int((iw - self.W) / 2)  # C++ integer division truncates toward zero
        yc = self.H - top - (self.H + ih) // 2
        return xc, yc

    def pic(self, key: str, t0: float, t1: float, x: float, y: float, *, to: tuple[float, float] | None = None,
            scale: tuple[int, int] | None = None, fade_in: float = 0, fade_out: float = 0, z: int = 20):
        """One Pictures effect: hold at (x, y), or slide to `to`, optionally scaling (percent, about its centre)."""
        if snap(t1) <= snap(t0):
            return
        xc, yc = self._offsets(key, x, y)
        ex, ey = self._offsets(key, *to) if to else (xc, yc)
        s0, s1 = scale or (100, 100)
        st = {
            "E_CHECKBOX_Pictures_PixelOffsets": "1",
            "E_CHECKBOX_Pictures_WrapX": "0",
            "E_CHOICE_Pictures_Direction": "vector" if (ex, ey) != (xc, yc) else "none",
            "E_CHOICE_Scaling": "No Scaling",
            "E_SLIDER_PicturesXC": str(xc),
            "E_SLIDER_PicturesYC": str(yc),
            "E_SLIDER_Pictures_StartScale": str(s0),
            "E_SLIDER_Pictures_EndScale": str(s1),
            "E_TEXTCTRL_Pictures_Filename": key,
            "E_TEXTCTRL_Pictures_FrameRateAdj": "1.0",
            "E_TEXTCTRL_Pictures_Speed": "1.0",
        }
        if (ex, ey) != (xc, yc):
            st["E_SLIDER_PicturesEndXC"] = str(ex)
            st["E_SLIDER_PicturesEndYC"] = str(ey)
        if fade_in:
            st["T_TEXTCTRL_Fadein"] = f"{fade_in:.2f}"
        if fade_out:
            st["T_TEXTCTRL_Fadeout"] = f"{fade_out:.2f}"
        self.fx.append(Fx("Pictures", snap(t0), snap(t1), st, None, z,
                          dict(key=key, a=(xc, yc), b=(ex, ey), s=(s0, s1), fi=fade_in, fo=fade_out)))

    def offscreen(self, key: str, x: float, y: float, side: str) -> tuple[float, float]:
        iw, ih = self.size(key)
        return {"left": (-iw / 2 - 1, y), "right": (self.W + iw / 2 + 1, y),
                "top": (x, -ih / 2 - 1), "bottom": (x, self.H + ih / 2 + 1)}[side]

    def show(self, key: str, t0: float, t1: float, x: float, y: float, *, enter: str | None = "pop",
             exit: str | None = None, enter_s: float = 0.35, exit_s: float = 0.35, hits=(), amp: float = 2,
             z: int = 20):
        """A picture's whole life: enter (left/right/top/bottom slide, pop, fade), hold - hopping `amp` pixels up
        on each of `hits` - then exit (a slide, fade or None to cut)."""
        enter_s = min(enter_s, (t1 - t0) / 3) if enter else 0
        exit_s = min(exit_s, (t1 - t0) / 3) if exit else 0
        a, b = t0 + enter_s, t1 - exit_s
        if enter in ("left", "right", "top", "bottom"):
            self.pic(key, t0, a, *self.offscreen(key, x, y, enter), to=(x, y), z=z)
        elif enter == "pop":
            m = t0 + enter_s * 0.7
            self.pic(key, t0, m, x, y, scale=(10, 120), z=z)
            self.pic(key, m, a, x, y, scale=(120, 100), z=z)
        elif enter == "fade":
            a = t0
        self.hold(key, a, b, x, y, hits=hits, amp=amp, fade_in=enter_s if enter == "fade" else 0,
                  fade_out=exit_s if exit == "fade" else 0, z=z)
        if exit in ("left", "right", "top", "bottom"):
            self.pic(key, b, t1, x, y, to=self.offscreen(key, x, y, exit), z=z)
        elif exit == "shrink":
            self.pic(key, b, t1, x, y, scale=(100, 10), z=z)

    def hold(self, key, t0, t1, x, y, *, hits=(), amp=2, fade_in=0, fade_out=0, z=20):
        """Hold still, hopping up `amp` pixels (0.1 s up, 0.15 s down) on each hit."""
        hits = [h for h in hits if t0 + 0.05 <= h <= t1 - 0.3]
        if fade_out and not hits:
            self.pic(key, t0, t1, x, y, fade_in=fade_in, fade_out=fade_out, z=z)
            return
        t = t0
        for h in hits:
            self.pic(key, t, h, x, y, fade_in=fade_in if t == t0 else 0, z=z)
            self.pic(key, h, h + 0.1, x, y, to=(x, y - amp), z=z)
            self.pic(key, h + 0.1, h + 0.25, x, y - amp, to=(x, y), z=z)
            t = h + 0.25
        self.pic(key, t, t1, x, y, fade_in=fade_in if t == t0 else 0, fade_out=fade_out, z=z)

    def glide(self, key, points: list[tuple[float, float, float]], z: int = 20):
        """Slide through keyframes [(t, x, y), ...]; a repeated position holds."""
        for (ta, xa, ya), (tb, xb, yb) in zip(points, points[1:]):
            self.pic(key, ta, tb, xa, ya, to=(xb, yb) if (xa, ya) != (xb, yb) else None, z=z)

    def flash(self, keys: list[str], times: list[float], x, y, z: int = 20, end: float | None = None):
        """Swap pictures on each time (SuperStar's quick image swaps): keys[i % n] from times[i] to times[i+1]."""
        ts = list(times) + [end if end is not None else times[-1] + 0.4]
        for i, (a, b) in enumerate(zip(ts, ts[1:])):
            self.pic(keys[i % len(keys)], a, b, x, y, z=z)

    # ------------------------------------------------ other effects

    def _pct(self, x: float, y: float) -> tuple[int, int]:
        """LED (x, y down) -> 0..100 percent, y up (Morph coordinates)."""
        return round(100 * x / max(1, self.W - 1)), round(100 * (self.H - 1 - y) / max(1, self.H - 1))

    def morph(self, t0, t1, a: tuple, b: tuple, color, tail=None, *, head: int = 3, duration: int = 45,
              z: int = 10):
        """A Morph bar: line a=((x1,y1),(x2,y2)) travels to line b (LED pixels), head colour then tail colour."""
        (ax1, ay1), (ax2, ay2) = (self._pct(*p) for p in a)
        (bx1, by1), (bx2, by2) = (self._pct(*p) for p in b)
        st = {
            "E_CHECKBOX_Morph_End_Link": "0", "E_CHECKBOX_Morph_Start_Link": "0", "E_CHECKBOX_ShowHeadAtStart": "0",
            "E_NOTEBOOK_Morph": "Start", "E_SLIDER_MorphAccel": "0", "E_SLIDER_MorphDuration": str(duration),
            "E_SLIDER_MorphEndLength": str(head), "E_SLIDER_MorphStartLength": str(head),
            "E_SLIDER_Morph_Start_X1": str(ax1), "E_SLIDER_Morph_Start_Y1": str(ay1),
            "E_SLIDER_Morph_Start_X2": str(ax2), "E_SLIDER_Morph_Start_Y2": str(ay2),
            "E_SLIDER_Morph_End_X1": str(bx1), "E_SLIDER_Morph_End_Y1": str(by1),
            "E_SLIDER_Morph_End_X2": str(bx2), "E_SLIDER_Morph_End_Y2": str(by2),
            "E_SLIDER_Morph_Repeat_Count": "0", "E_SLIDER_Morph_Repeat_Skip": "1", "E_SLIDER_Morph_Stagger": "0",
        }
        self.fx.append(Fx("Morph", snap(t0), snap(t1), st, palette(color, tail or color), z,
                          dict(a=a, b=b, c=color, tail=tail or color, dur=duration)))

    def sweep(self, t0, t1, color, side: str = "left", band: tuple[float, float] | None = None, tail=None,
              z: int = 10):
        """A bar sweeping across the matrix from `side`; band limits it to rows (y0, y1) or columns."""
        W, H = self.W - 1, self.H - 1
        if side in ("left", "right"):
            y0, y1 = band or (0, H)
            xs = (0, W) if side == "left" else (W, 0)
            self.morph(t0, t1, ((xs[0], y0), (xs[0], y1)), ((xs[1], y0), (xs[1], y1)), color, tail, z=z)
        else:
            x0, x1 = band or (0, W)
            ys = (0, H) if side == "top" else (H, 0)
            self.morph(t0, t1, ((x0, ys[0]), (x1, ys[0])), ((x0, ys[1]), (x1, ys[1])), color, tail, z=z)

    def ring(self, t: float, x: float, y: float, color, *, r: float = 24, width: float = 3, dur: float = 0.7,
             z: int = 12):
        """A Shockwave ring bursting out from (x, y) to radius r LED pixels."""
        st = {
            "E_CHECKBOX_Shockwave_Blend_Edges": "1", "E_CHECKBOX_Shockwave_Scale": "0",
            "E_NOTEBOOK_Shockwave": "Position", "E_SLIDER_Shockwave_Accel": "0",
            "E_SLIDER_Shockwave_CenterX": str(round(100 * x / self.W)),
            "E_SLIDER_Shockwave_CenterY": str(round(100 * (self.H - y) / self.H)),
            "E_SLIDER_Shockwave_Start_Radius": "0", "E_SLIDER_Shockwave_End_Radius": str(round(r)),
            "E_SLIDER_Shockwave_Start_Width": str(round(width)), "E_SLIDER_Shockwave_End_Width": str(round(width)),
        }
        self.fx.append(Fx("Shockwave", snap(t), snap(t + dur), st, palette(color), z,
                          dict(x=x, y=y, r=r, w=width, c=color)))

    def twinkle(self, t0, t1, colors=((255, 255, 255),), count: int = 12, steps: int = 40, z: int = 0,
                fade: float = 0.5):
        st = {"E_CHECKBOX_Twinkle_ReRandom": "1", "E_CHECKBOX_Twinkle_Strobe": "0",
              "E_CHOICE_Twinkle_Style": "New Render Method", "E_SLIDER_Twinkle_Count": str(count),
              "E_SLIDER_Twinkle_Steps": str(steps), "T_TEXTCTRL_Fadein": f"{fade:.2f}",
              "T_TEXTCTRL_Fadeout": f"{fade:.2f}"}
        self.fx.append(Fx("Twinkle", snap(t0), snap(t1), st, palette(*colors), z,
                          dict(colors=colors, count=count)))

    def snow(self, t0, t1, count: int = 6, speed: int = 10, z: int = 0, fade: float = 0.5):
        st = {"E_CHOICE_Falling": "Driving", "E_SLIDER_Snowflakes_Count": str(count),
              "E_SLIDER_Snowflakes_Speed": str(speed), "E_SLIDER_Snowflakes_Type": "1",
              "T_TEXTCTRL_Fadein": f"{fade:.2f}", "T_TEXTCTRL_Fadeout": f"{fade:.2f}"}
        self.fx.append(Fx("Snowflakes", snap(t0), snap(t1), st, palette((255, 255, 255)), z,
                          dict(count=count, speed=speed)))

    def wash(self, t0, t1, color, z: int = 0, fade_in: float = 0.0, fade_out: float = 0.0):
        st = {}
        if fade_in:
            st["T_TEXTCTRL_Fadein"] = f"{fade_in:.2f}"
        if fade_out:
            st["T_TEXTCTRL_Fadeout"] = f"{fade_out:.2f}"
        self.fx.append(Fx("Color Wash", snap(t0), snap(t1), st, palette(color), z,
                          dict(c=color, fi=fade_in, fo=fade_out)))

    # ------------------------------------------------ layering

    def layers(self) -> list[list[Fx]]:
        """Pack effects into layers: highest z first (layer 0 is the front), greedy per z so none overlap."""
        out: list[list[Fx]] = []
        for z in sorted({f.z for f in self.fx}, reverse=True):
            group: list[list[Fx]] = []
            for f in sorted((f for f in self.fx if f.z == z), key=lambda f: (f.t0, f.t1)):
                for lay in group:
                    if lay[-1].t1 <= f.t0:
                        lay.append(f)
                        break
                else:
                    group.append([f])
            out += group
        return out


# ---------------------------------------------------------------- several matrices as one stage

def model_geometry(layout: Path, name: str) -> dict:
    """A Matrix model's LED size and where it sits in the layout (centre and per-LED scale, world units)."""
    for m in ET.parse(layout).getroot().iter("model"):
        if m.get("name") != name:
            continue
        if "Matrix" not in (m.get("DisplayAs") or ""):
            raise SystemExit(f"{name} is a {m.get('DisplayAs')}, not a matrix")
        strands = int(m.get("NumStrings", 1)) * int(m.get("StrandsPerString", 1))
        nodes = int(m.get("NodesPerString", 1)) // int(m.get("StrandsPerString", 1))
        W, H = (strands, nodes) if m.get("Vertical") == "true" else (nodes, strands)
        rot = [abs(float(m.get(k, 0))) for k in ("RotateX", "RotateY", "RotateZ")]
        return dict(W=W, H=H, x=float(m.get("WorldPosX", 0)), y=float(m.get("WorldPosY", 0)),
                    sx=float(m.get("ScaleX", 1)), sy=float(m.get("ScaleY", 1)), rotated=max(rot) > 1)
    raise SystemExit(f"no model {name!r} in {layout}")


class Stage(Story):
    """Several matrices as one picture. Coordinates are stage LEDs (x right, y down) laid out as the models sit in
    the layout, so a picture can slide from one window, behind the wall between them, into the next. Every picture,
    sweep and ring goes to each model it reaches, in that model's own pixel offsets; the gap draws nothing.
    s.on(model) is that model's own Story (local coordinates) for things that belong to one window."""

    GAP = (26, 26, 30)  # preview colour of the wall between models

    def __init__(self, cues: Cues, prefix: str, places: list[tuple[str, int, int, int, int]]):
        x0, y0 = min(p[3] for p in places), min(p[4] for p in places)
        places = [(m, w, h, ox - x0, oy - y0) for m, w, h, ox, oy in places]
        super().__init__(max(p[3] + p[1] for p in places), max(p[4] + p[2] for p in places), cues, prefix)
        self.places = {m: (Story(w, h, cues, prefix, self.images), ox, oy) for m, w, h, ox, oy in places}

    @classmethod
    def from_layout(cls, layout: Path, models: list[str], cues: Cues, prefix: str):
        geo = [model_geometry(layout, m) for m in models]
        sx, sy = geo[0]["sx"], geo[0]["sy"]  # world units per LED, from the first model
        places = []
        for m, g in zip(models, geo):
            if g["rotated"]:
                print(f"warning: {m} is rotated in the layout; placing it by its front-view position only")
            if abs(g["sx"] / sx - 1) > 0.05 or abs(g["sy"] / sy - 1) > 0.05:
                print(f"warning: {m} has a different LED spacing; pictures will not line up across it")
            places.append((m, g["W"], g["H"], round(g["x"] / sx - g["W"] / 2), round(-g["y"] / sy - g["H"] / 2)))
        return cls(cues, prefix, places)

    def on(self, model: str) -> Story:
        return self.places[model][0]

    def center(self, model: str) -> tuple[float, float]:
        """Stage position of a model's centre."""
        st, ox, oy = self.places[model]
        return ox + st.W / 2, oy + st.H / 2

    def stories(self) -> dict[str, Story]:
        return {m: p[0] for m, p in self.places.items()}

    def pic(self, key: str, t0: float, t1: float, x: float, y: float, *, to=None, scale=None, fade_in: float = 0,
            fade_out: float = 0, z: int = 20):
        iw, ih = self.size(key)
        k = max(scale or (100, 100)) / 100
        hw, hh = iw * k / 2 + 1, ih * k / 2 + 1
        xs, ys = (x, to[0]) if to else (x,), (y, to[1]) if to else (y,)
        for st, ox, oy in self.places.values():
            if max(xs) + hw < ox or min(xs) - hw > ox + st.W or max(ys) + hh < oy or min(ys) - hh > oy + st.H:
                continue  # never reaches this model
            st.pic(key, t0, t1, x - ox, y - oy, to=(to[0] - ox, to[1] - oy) if to else None, scale=scale,
                   fade_in=fade_in, fade_out=fade_out, z=z)

    def sweep(self, t0, t1, color, side: str = "left", band=None, tail=None, z: int = 10):
        """Left/right: one bar travelling across the whole stage, reaching each model in turn (each model's Morph
        is timed to when the bar crosses it). Top/bottom: every model at once."""
        for st, ox, oy in self.places.values():
            if side in ("top", "bottom"):
                st.sweep(t0, t1, color, side, None, tail, z=z)
                continue
            T = (t1 - t0) * 0.45  # the Morph head travels for 45% of the effect
            a, b = ox / (self.W - 1), (ox + st.W - 1) / (self.W - 1)
            if side == "right":
                a, b = 1 - b, 1 - a
            te, tx = t0 + T * a, t0 + T * b
            lb = None
            if band:
                lb = (max(0, band[0] - oy), min(st.H - 1, band[1] - oy))
                if lb[0] > lb[1]:
                    continue
            st.sweep(te, te + (tx - te) / 0.45, color, side, lb, tail, z=z)

    def ring(self, t: float, x: float, y: float, color, **kw):
        """A Shockwave in the model that holds (x, y)."""
        for st, ox, oy in self.places.values():
            if ox <= x < ox + st.W and oy <= y < oy + st.H:
                st.ring(t, x - ox, y - oy, color, **kw)

    def twinkle(self, *a, **kw):
        for st in self.stories().values():
            st.twinkle(*a, **kw)

    def snow(self, *a, **kw):
        for st in self.stories().values():
            st.snow(*a, **kw)

    def wash(self, *a, **kw):
        for st in self.stories().values():
            st.wash(*a, **kw)

    def morph(self, *a, **kw):
        raise NotImplementedError("use s.sweep() across the stage, or s.on(model).morph() inside one model")

    def preview(self, t: float) -> Image.Image:
        canvas = Image.new("RGB", (self.W, self.H), self.GAP)
        for st, ox, oy in self.places.values():
            canvas.paste(preview_frame(st, t), (ox, oy))
        return canvas


# ---------------------------------------------------------------- write the sequence

def write_xsq(stories: dict[str, Story], src: Path, out: Path) -> dict:
    """Replace the effects on each model with its story's layers and embed the pictures they use."""
    tree = ET.parse(src)
    root = tree.getroot()

    # embedded pictures: drop any earlier copies of this story's media, then add the current ones
    media = root.find("SequenceMedia")
    if media is None:
        media = ET.SubElement(root, "SequenceMedia")
    first = next(iter(stories.values()))
    pre = f"MatrixScenes/{first.prefix}/"
    for c in list(media):
        if (c.get("path") or "").startswith(pre):
            media.remove(c)
    used = {f.settings["E_TEXTCTRL_Pictures_Filename"] for st in stories.values() for f in st.fx
            if f.name == "Pictures"}
    images = {k: v for st in stories.values() for k, v in st.images.items()}
    for key, im in sorted(images.items()):
        if key not in used:
            continue
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        node = ET.SubElement(media, "Image", path=key)
        ET.SubElement(node, "Data").text = base64.b64encode(buf.getvalue()).decode("ascii")

    db = root.find("EffectDB")
    pals = root.find("ColorPalettes")
    db_idx = {(e.text or ""): i for i, e in enumerate(db)}
    pal_idx = {(p.text or ""): i for i, p in enumerate(pals)}

    def ref(table, idx, tag, s):
        if s not in idx:
            ET.SubElement(table, tag).text = s
            idx[s] = len(idx)
        return idx[s]

    effects = root.find("ElementEffects")
    disp = root.find("DisplayElements")
    counts = {}
    for model, story in stories.items():
        elem = next((e for e in effects if e.get("type") == "model" and e.get("name") == model), None)
        if elem is None:
            elem = ET.SubElement(effects, "Element", type="model", name=model)
        for c in list(elem):
            elem.remove(c)
        lays = story.layers()
        for lay in lays:
            le = ET.SubElement(elem, "EffectLayer")
            for f in lay:
                s = ",".join(f"{k}={v}" for k, v in sorted(f.settings.items()))
                attrs = {"ref": str(ref(db, db_idx, "Effect", s)), "name": f.name,
                         "startTime": str(f.t0), "endTime": str(f.t1)}
                if f.palette:
                    attrs["palette"] = str(ref(pals, pal_idx, "ColorPalette", f.palette))
                ET.SubElement(le, "Effect", attrs)
        if not any(e.get("name") == model for e in disp):
            ET.SubElement(disp, "Element", collapsed="false", type="model", name=model, visible="true")
        counts[model] = {"layers": len(lays), "effects": len(story.fx)}

    ET.indent(tree, space="    ")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(fh, encoding="unicode", xml_declaration=False)
    ET.parse(out)  # validate
    return {"models": counts, "images": len(used)}


# ---------------------------------------------------------------- local preview (approximate)

def _pic_frame(story: Story, f: Fx, t: float, canvas: Image.Image):
    lk = f.look
    pos = (t * 1000 - f.t0) / max(1, f.t1 - f.t0)
    im = story.images[lk["key"]]
    s = lk["s"][0] + (lk["s"][1] - lk["s"][0]) * pos
    iw, ih = im.size
    if s != 100:
        iw, ih = max(1, round(iw * s / 100)), max(1, round(ih * s / 100))
        im = im.resize((iw, ih), Image.NEAREST)
    xc = round(lk["a"][0] + pos * (lk["b"][0] - lk["a"][0]))
    yc = round(lk["a"][1] + pos * (lk["b"][1] - lk["a"][1]))
    left = xc - int((iw - story.W) / 2)
    top = story.H - 1 - ((story.H + ih) // 2 + yc - 1)
    alpha = 1.0
    if lk["fi"]:
        alpha = min(alpha, (t * 1000 - f.t0) / (lk["fi"] * 1000))
    if lk["fo"]:
        alpha = min(alpha, (f.t1 - t * 1000) / (lk["fo"] * 1000))
    if alpha < 1:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0.0, alpha))))
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    layer.paste(im, (left, top), im)
    canvas.alpha_composite(layer)


def _lerp(a, b, u):
    return a + (b - a) * u


def preview_frame(story: Story, t: float) -> Image.Image:
    W, H = story.W, story.H
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(canvas)
    ms = t * 1000
    if getattr(story, "_lays_n", None) != len(story.fx):  # pack once per story, not per frame
        story._lays, story._lays_n = story.layers(), len(story.fx)
    for lay in reversed(story._lays):  # back to front
        for f in lay:
            if not (f.t0 <= ms < f.t1):
                continue
            pos = (ms - f.t0) / max(1, f.t1 - f.t0)
            lk = f.look
            if f.name == "Pictures":
                _pic_frame(story, f, t, canvas)
            elif f.name == "Morph":
                u = min(1.0, pos / (lk["dur"] / 100))
                (ax1, ay1), (ax2, ay2) = lk["a"]
                (bx1, by1), (bx2, by2) = lk["b"]
                for k, uu in enumerate((u, u - 0.04, u - 0.08)):
                    if uu < 0:
                        continue
                    c = tuple(lk["c"] if k == 0 else (int(v * (0.6 - 0.2 * k)) for v in lk["tail"]))
                    d.line([(_lerp(ax1, bx1, uu), _lerp(ay1, by1, uu)), (_lerp(ax2, bx2, uu), _lerp(ay2, by2, uu))],
                           fill=c, width=1)
            elif f.name == "Shockwave":
                r = lk["r"] * pos
                d.ellipse([lk["x"] - r, lk["y"] - r, lk["x"] + r, lk["y"] + r], outline=tuple(lk["c"]),
                          width=max(1, round(lk["w"] / 2)))
            elif f.name == "Twinkle":
                rnd = random.Random(f.t0)
                n = max(1, W * H * lk["count"] // 100 // 4)
                for i in range(n):
                    x, y, ph = rnd.randrange(W), rnd.randrange(H), rnd.random()
                    v = 0.5 + 0.5 * math.sin(2 * math.pi * (t * 0.8 + ph))
                    c = lk["colors"][i % len(lk["colors"])]
                    d.point((x, y), fill=tuple(int(cc * v) for cc in c))
            elif f.name == "Snowflakes":
                rnd = random.Random(f.t0)
                for _ in range(lk["count"] * 4):
                    x, y0 = rnd.randrange(W), rnd.random() * H
                    y = (y0 + (ms - f.t0) / 1000 * lk["speed"]) % H
                    d.point((int(x + y * 0.2) % W, int(y)), fill=(220, 220, 255))
            elif f.name == "Color Wash":
                d.rectangle([0, 0, W, H], fill=tuple(lk["c"]))
    return canvas.convert("RGB")


def frame_of(story: Story, t: float) -> Image.Image:
    return story.preview(t) if isinstance(story, Stage) else preview_frame(story, t)


def sheet(story: Story, times: list[float], out: Path, z: int = 6):
    cols = min(8, len(times))
    rows = math.ceil(len(times) / cols)
    W, H = story.W, story.H
    img = Image.new("RGB", (cols * (W * z + 8), rows * (H * z + 18)), (40, 40, 40))
    d = ImageDraw.Draw(img)
    for k, t in enumerate(times):
        im = frame_of(story, t).resize((W * z, H * z), Image.NEAREST)
        x, y = (k % cols) * (W * z + 8), (k // cols) * (H * z + 18)
        img.paste(im, (x, y))
        d.text((x + 2, y + H * z + 3), f"{t:.1f}", fill=(220, 220, 220))
    img.save(out)


def preview_video(story: Story, out: Path, t0: float, t1: float, audio: str | None, z: int = 10, fps: int = 20):
    W, H = story.W, story.H
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W * z}x{H * z}",
           "-r", str(fps), "-i", "-"]
    if audio:
        cmd += ["-ss", f"{t0:.3f}", "-i", audio, "-shortest", "-c:a", "aac"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int((t1 - t0) * fps)
    for i in range(n):
        p.stdin.write(frame_of(story, t0 + i / fps).resize((W * z, H * z), Image.NEAREST).tobytes())
    p.stdin.close()
    p.wait()


# ---------------------------------------------------------------- main

def load_story(path: Path):
    spec = importlib.util.spec_from_file_location("scene_story", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("story", type=Path)
    ap.add_argument("xsq", type=Path, help="sequence to read (and copy from, with --out)")
    ap.add_argument("--model", required=True, help="matrix model, or several comma-separated for a Stage")
    ap.add_argument("--size", help="matrix WxH in LEDs (default: from the layout)")
    ap.add_argument("--layout", type=Path, help="xlights_rgbeffects.xml (default: next to the sequence)")
    ap.add_argument("--out", type=Path, help="write the sequence here (may be the input; back it up first)")
    ap.add_argument("--sheet", type=Path)
    ap.add_argument("--at", default="")
    ap.add_argument("--preview", type=Path)
    ap.add_argument("--audio")
    ap.add_argument("--from", dest="t_from", type=float, default=0.0)
    ap.add_argument("--to", dest="t_to", type=float, default=None)
    a = ap.parse_args()
    layout = a.layout or a.xsq.parent / "xlights_rgbeffects.xml"
    models = [m.strip() for m in a.model.split(",") if m.strip()]
    mod = load_story(a.story)
    cues = mod.cues(a.xsq) if hasattr(mod, "cues") else Cues.from_xsq(a.xsq)
    prefix = getattr(mod, "PREFIX", a.story.stem)
    if len(models) > 1:
        story = Stage.from_layout(layout, models, cues, prefix)
        for m, (st, ox, oy) in story.places.items():
            print(f"  {m}: {st.W}x{st.H} at stage ({ox}, {oy})")
        print(f"  stage {story.W}x{story.H}")
    else:
        if a.size:
            W, H = (int(v) for v in a.size.lower().split("x"))
        else:
            g = model_geometry(layout, models[0])
            W, H = g["W"], g["H"]
        story = Story(W, H, cues, prefix)
    mod.build(story)
    stories = story.stories() if isinstance(story, Stage) else {models[0]: story}
    for m, st in stories.items():
        print(f"{m}: {len(st.fx)} effects, {len(st.layers())} layers")
    print(f"{len(story.images)} pictures")
    if a.sheet:
        times = [float(v) for v in a.at.split(",") if v]
        sheet(story, times, a.sheet)
        print("sheet:", a.sheet)
    if a.preview:
        preview_video(story, a.preview, a.t_from, a.t_to or cues.duration, a.audio)
        print("preview:", a.preview)
    if a.out:
        print(write_xsq(stories, a.xsq, a.out))


if __name__ == "__main__":
    main()
