r"""A pixel dancer doing the Cupid Shuffle on the Mega Tree and Matrix, in time with the sung calls.

Usage:
    python scripts/shuffle_dancer.py SONG.xsq fixed.json [--show F:\ShowFolderAI] [--models "Mega Tree" Matrix]

The dancer is drawn as ASCII art below (one letter per colour). Every sung call in fixed.json moves it:
"to the right" x4 -> four steps right, "to the left" x4 -> four steps left, "now kick" x4 -> kicks right/left,
"now walk it by yourself" -> two walking steps and a turn. Each pose lands on the word ("right", "left", "kick",
"walk"/"yourself") and holds until the next call; outside the refrains the dancer is gone.

The frames are full-model PNGs (20x75 Mega Tree, 120x60 Matrix) with the figure baked in at its position, shown
with "No Scaling" so each pixel lands on one light. Transparent Black is on, so the shader keeps running around
the dancer; a near-black outline (just over the Transparent Black level) keeps the figure readable on busy shaders.
One Pictures layer goes on top of each model; re-running replaces it.
"""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from lyric_images import BLACK_LEVEL, Xsq

IMG_SUB = "Images/Dancer"
COLORS = {"H": (210, 110, 20), "K": (255, 180, 120), "E": (60, 140, 255), "R": (255, 0, 0), "P": (255, 60, 170),
          "B": (0, 70, 255), "Y": (255, 220, 0)}
OUTLINE = (BLACK_LEVEL + 6,) * 3     # drawn (above the Transparent Black level) but reads as black on the lights
# model size, scale of one ASCII cell (x, y), pixels per step: the 180-degree Mega Tree's pixels are much further
# apart across than down, so the figure is drawn twice as tall there
MODELS = {"Mega Tree": ((20, 75), (1, 2), 1), "Matrix": ((120, 60), (2, 2), 8)}
HOLD_LAST_S = 1.2

HEAD = [".....HHHH.....",
        "....HHHHHH....",
        "....KKKKKK....",
        "....KEKKEK....",
        "....KKKKKK....",
        "....KKRRKK....",
        ".....KKKK....."]
SHIRT = ["....RPRRPR....",
         "....RPPPPR....",
         "....RRPPRR....",
         "....RRRRRR...."]
HIPS = ["....BBBBBB....",
        "....BBBBBB...."]


def _pose(head, arms, legs):
    return [*head, *arms, *legs]


ARMS_DOWN = ["...RRRRRRRR...",
             "..RRRRRRRRRR..",
             ".RR.RRRRRR.RR.",
             ".RR.RPRRPR.RR.",
             ".RR.RPPPPR.RR.",
             ".KK.RRPPRR.KK.",
             ".KK.RRRRRR.KK."]
ARMS_OUT = ["...RRRRRRRR...",
            "KKRRRRRRRRRRKK",
            "....RRRRRR....",
            *SHIRT]
ARMS_UP_HEAD = [".....HHHH.....",
                ".K..HHHHHH..K.",
                ".KK.KKKKKK.KK.",
                ".KK.KEKKEK.KK.",
                ".RR.KKKKKK.RR.",
                ".RR.KKRRKK.RR.",
                "..RR.KKKK.RR.."]
ARMS_UP = ["...RRRRRRRR...",
           "....RRRRRR....",
           "....RRRRRR....",
           *SHIRT]
LEGS_TOGETHER = [*HIPS,
                 "....BB..BB....",
                 "....BB..BB....",
                 "....BB..BB....",
                 "....BB..BB....",
                 "....BB..BB....",
                 "....BB..BB....",
                 "...YYY..YYY..."]
LEGS_APART = [*HIPS,
              "...BBB..BBB...",
              "..BB......BB..",
              "..BB......BB..",
              ".BB........BB.",
              ".BB........BB.",
              ".BB........BB.",
              "YYY........YYY"]
LEGS_KICK = [*HIPS,
             "....BB..BBB...",
             "....BB...BBB..",
             "....BB....BBYY",
             "....BB.....YYY",
             "....BB........",
             "....BB........",
             "...YYY........"]
WALK_ARMS = ["...RRRRRRRR...",
             "..RRRRRRRRRRR.",
             ".RR.RRRRRR.KK.",
             ".RR.RPRRPR.KK.",
             ".RR.RPPPPR....",
             ".KK.RRPPRR....",
             ".KK.RRRRRR...."]
WALK_LEGS = [*HIPS,
             "....BB..BB....",
             "....BB..BB....",
             "....BB..BB....",
             "....BB.YYY....",
             "....BB........",
             "....BB........",
             "...YYY........"]
SIDE = ["....HHHH......",
        "...HHHHHH.....",
        "...HHKKKK.....",
        "...HKKKEK.....",
        "....KKKKKK....",
        "....KKKRK.....",
        ".....KKK......",
        "....RRRRR.....",
        "....RRRRR.....",
        "....RRRRRR....",
        "....RRRKKK....",
        "....RRRR......",
        "....RRRR......",
        "....RRRR......",
        "....BBBB......",
        "....BBBB......",
        "....BB.BB.....",
        "...BB...BB....",
        "...BB....BB...",
        "..BB......BB..",
        "..BB......BB..",
        "..BB.......B..",
        ".YYY.......YYY"]


def mirror(rows):
    return [r[::-1] for r in rows]


POSES = {
    "stand": _pose(HEAD, ARMS_DOWN, LEGS_TOGETHER),
    "step": _pose(HEAD, ARMS_OUT, LEGS_APART),
    "kick_r": _pose(ARMS_UP_HEAD, ARMS_UP, LEGS_KICK),
    "kick_l": mirror(_pose(ARMS_UP_HEAD, ARMS_UP, LEGS_KICK)),
    "walk_a": _pose(HEAD, WALK_ARMS, WALK_LEGS),
    "walk_b": mirror(_pose(HEAD, WALK_ARMS, WALK_LEGS)),
    "side": SIDE,
}
assert all(len(r) == 14 for p in POSES.values() for r in p) and all(len(p) == 23 for p in POSES.values())


def frame(pose: str, x: int, size, scale) -> Image.Image:
    """Full-model RGB frame with the pose centred, shifted x pixels right."""
    rows = POSES[pose]
    w, h = len(rows[0]), len(rows)
    sx, sy = scale
    fig = Image.new("RGB", (w + 2, h + 2), (0, 0, 0))
    px = fig.load()
    for y, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != ".":
                px[c + 1, y + 1] = COLORS[ch]
    for y in range(h + 2):          # outline: empty cells touching the figure
        for c in range(w + 2):
            if px[c, y] == (0, 0, 0) and any(
                    0 <= c + dc < w + 2 and 0 <= y + dy < h + 2 and px[c + dc, y + dy] not in ((0, 0, 0), OUTLINE)
                    for dc in (-1, 0, 1) for dy in (-1, 0, 1)):
                px[c, y] = OUTLINE
    fig = fig.resize(((w + 2) * sx, (h + 2) * sy), Image.NEAREST)
    out = Image.new("RGB", size, (0, 0, 0))
    left = (size[0] - fig.width) // 2 + x
    out.paste(fig, (left, max(0, (size[1] - fig.height) // 2)))
    return out


def moves(phrases: list[dict]) -> list[tuple[float, float, str, int]]:
    """(start, end, pose, step offset) for every sung call; end = the next call, or the line's end + a hold."""
    calls, x = [], 0
    for p in phrases:
        words = [w["w"].lower().strip(",.!'") for w in p["words"]]
        text = " ".join(words)
        line_end = p["end"]
        if "right" in words and ("to the right" in text or text.startswith("the right")):
            x = -3      # each refrain starts at the left: four steps take the dancer across, the left line brings it back
            for k, w in enumerate(p["words"]):
                if words[k] == "right":
                    x = min(x + 1, 2)
                    calls.append([w["s"], line_end, "step" if len(calls) % 2 == 0 else "stand", x])
        elif "left" in words and ("to the left" in text or text.startswith("the left")):
            for k, w in enumerate(p["words"]):
                if words[k] == "left":
                    x = max(x - 1, -2)
                    calls.append([w["s"], line_end, "step" if len(calls) % 2 == 0 else "stand", x])
        elif text.startswith("now kick"):
            kicks = [w for k, w in enumerate(p["words"]) if words[k] == "kick"]
            for k, w in enumerate(kicks):
                calls.append([w["s"], line_end, "kick_r" if k % 2 == 0 else "kick_l", x])
        elif "walk it by yourself" in text:
            hits = [w for k, w in enumerate(p["words"]) if words[k] in ("walk", "yourself")]
            for k, w in enumerate(hits):
                pose = "side" if k == len(hits) - 1 else ("walk_a" if k % 2 == 0 else "walk_b")
                calls.append([w["s"], line_end, pose, x])
    for a, b in zip(calls, calls[1:]):      # hold each pose until the next call when it comes soon
        a[1] = b[0] if b[0] - a[0] < 2.0 else min(a[1] + HOLD_LAST_S, b[0])
    if calls:
        calls[-1][1] += HOLD_LAST_S
    return [tuple(c) for c in calls if c[1] - c[0] >= 0.05]


def settings(rel: str) -> str:
    s = {"B_CHOICE_BufferStyle": "Default", "E_CHECKBOX_Pictures_PixelOffsets": "0",
         "E_CHECKBOX_Pictures_TransparentBlack": "1", "E_TEXTCTRL_Pictures_TransparentBlack": str(BLACK_LEVEL),
         "E_CHECKBOX_Pictures_WrapX": "0", "E_CHOICE_Scaling": "No Scaling", "E_TEXTCTRL_Pictures_Filename": rel,
         "E_TEXTCTRL_Pictures_FrameRateAdj": "1.0", "E_TEXTCTRL_Pictures_Speed": "1.0",
         "E_CHOICE_Pictures_Direction": "none", "E_SLIDER_Pictures_StartScale": "100", "E_SLIDER_Pictures_EndScale": "100"}
    return ",".join(f"{k}={v}" for k, v in sorted(s.items()))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xsq")
    ap.add_argument("phrases", help="fixed.json from lyrics_align.py")
    ap.add_argument("--show", default=r"F:\ShowFolderAI")
    ap.add_argument("--models", nargs="+", default=list(MODELS))
    a = ap.parse_args()

    show = Path(a.show)
    calls = moves([p for p in json.load(open(a.phrases, encoding="utf-8")) if p["words"]])
    sq = Xsq(Path(a.xsq))
    for name in a.models:
        el = sq.model(name)
        if el is None or name not in MODELS:
            print(f"skip {name}: not in the sequence or no dancer size for it")
            continue
        size, scale, step_px = MODELS[name]
        layers = el.findall("EffectLayer")      # replace our own layer from an earlier run
        if layers and any(IMG_SUB in (sq.db[int(e.get("ref", -1))].text or "") for e in layers[0].findall("Effect")):
            el.remove(layers[0])
        lay = ET.Element("EffectLayer")
        for start, end, pose, x in calls:
            rel = f"{IMG_SUB}/{pose}_{x:+d}_{size[0]}x{size[1]}.png"
            out = show / rel
            if not out.exists():
                out.parent.mkdir(parents=True, exist_ok=True)
                frame(pose, x * step_px, size, scale).save(out)
            ET.SubElement(lay, "Effect", {"ref": str(sq.ref(settings(rel))), "name": "Pictures",
                                          "startTime": str(int(round(start * 1000))), "endTime": str(int(round(end * 1000))),
                                          "palette": str(sq.palette)})
        el.insert(0, lay)       # first EffectLayer is the top one
    sq.save()
    blocks = sum(1 for c, d in zip(calls, calls[1:]) if d[0] - c[1] > 1.0) + bool(calls)
    print(f"dancer: {len(calls)} moves in {blocks} refrain block(s) on {', '.join(a.models)}")


if __name__ == "__main__":
    main()
