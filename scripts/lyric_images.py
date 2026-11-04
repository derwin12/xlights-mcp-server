r"""Put pictures of sung words on the Mega Tree and matrices: COWBOY -> a cowboy face, CRYSTAL BALL -> a crystal ball.

Usage:
    python scripts/lyric_images.py SONG.xsq fixed.json [--show F:\ShowFolderAI] [--icons scripts/lyric_icons.json]
        [--hold 2.4] [--models "Mega Tree" Matrix "Matrix 2"]

fixed.json is lyrics_align.py's output (timed words). Words and phrases listed in lyric_icons.json (word -> emoji)
are found in the lyrics; each hit becomes a picture that lands on the word and holds for --hold seconds (pictures
never overlap, so busy lines show the first hit). The artwork is Noto Emoji (Apache 2.0, fine in sold sequences),
downloaded once into ~/.cache/xlights-mcp/noto and written per model size to <show>\Images\LyricIcons.

On each model one Pictures layer goes on top of the existing effects (shaders, tints): a 0.4 s entrance (grow,
slide in from left/right, rise or drop, always the same one for a given picture so choruses repeat), then a hold
that fades out. Transparent Black is on, so the background effects keep running around the picture (the user
wants the pictures laid over the background, not cut in over black).
Pictures uses "No Scaling" because xLights only applies Start/End Scale then; the PNGs are made at the size the
picture should have on each model. A missing image renders solid red: package with package_xsqz.py, which packs
the referenced pictures. Re-running replaces the layers it made before.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from PIL import Image, ImageEnhance

HERE = Path(__file__).resolve().parent
NOTO = "https://cdn.jsdelivr.net/gh/googlefonts/noto-emoji@v2.047/png/512/emoji_u{}.png"
CACHE = Path.home() / ".cache" / "xlights-mcp" / "noto"
IMG_SUB = "Images/LyricIcons"
# picture size in pixels per model (w, h): about the height of the matrix; the 20x75 Mega Tree is a 180-degree
# tree whose pixels are much further apart across than down, so its pictures are drawn twice as tall as wide
SIZES = {"Mega Tree": (20, 38), "Matrix": (56, 56), "Matrix 2": (28, 28)}
ENTRANCE_S = 0.4
REPEAT_S = 20.0     # the same picture again only after this long (This Christmas showed the tree 12 times)
BLACK_LEVEL = 30    # Transparent Black: pixels with R+G+B at or below this are not drawn, so the effects below show
# (start XC, start YC, start scale) -> centre at 100%; XC/YC are percent of the model
ENTRANCES = {"grow": (0, 0, 20), "slide-left": (-100, 0, 100), "slide-right": (100, 0, 100),
             "rise": (0, -100, 100), "drop": (0, 100, 100)}


def is_file(icon: str) -> bool:
    return icon.lower().endswith(".png")


def emoji_code(e: str) -> str:
    if is_file(e):
        return Path(e).stem
    return "_".join(f"{ord(c):04x}" for c in e if ord(c) != 0xFE0F)


def icon_png(emoji: str) -> Image.Image | None:
    if is_file(emoji):
        return Image.open(emoji).convert("RGBA")
    code = emoji_code(emoji)
    path = CACHE / f"{code}.png"
    if not path.exists():
        r = requests.get(NOTO.format(code), timeout=30)
        if r.status_code != 200:
            print(f"  no Noto image for {emoji} ({code})")
            return None
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_bytes(r.content)
    return Image.open(path).convert("RGBA")


def model_png(emoji: str, show: Path, size: tuple[int, int]) -> str | None:
    """Write the picture at the model size (RGB on black) and return its show-relative path."""
    rel = f"{IMG_SUB}/{emoji_code(emoji)}_{size[0]}x{size[1]}.png"
    out = show / rel
    if not out.exists():
        im = icon_png(emoji)
        if im is None:
            return None
        im = im.crop(im.getbbox()).resize(size, Image.LANCZOS)
        bg = Image.new("RGB", size, (0, 0, 0))
        bg.paste(im, mask=im.split()[3])
        # LEDs: grey artwork (music note, microphone, mountain) reads dim, so lift brightness and colour a little
        bg = ImageEnhance.Color(ImageEnhance.Brightness(bg).enhance(1.25)).enhance(1.3)
        out.parent.mkdir(parents=True, exist_ok=True)
        bg.save(out)
    return rel


def stems(word: str) -> list[str]:
    w = word.lower().strip("'")
    out = [w]
    if w.endswith("in"):
        out.append(w + "g")
    if w.endswith("ing"):
        out.append(w[:-1])          # choosing -> choosin (whichever the list has)
    if w.endswith("s") and len(w) > 3:
        out.append(w[:-1])
    return out


def find_hits(phrases: list[dict], icons: dict[str, str]) -> list[tuple[float, str, str]]:
    """[(time, matched text, emoji)] for every listed word/phrase in the sung words, in order."""
    words = [w for p in phrases for w in p["words"]]
    keys = {k: v for k, v in icons.items() if not k.startswith("_")}
    hits, i = [], 0
    while i < len(words):
        for n in (3, 2, 1):         # longest phrase first: "crystal ball" before "ball"
            if i + n > len(words):
                continue
            text = " ".join(w["w"].lower().strip("'") for w in words[i:i + n])
            cands = [text] if n > 1 else stems(text)
            key = next((c for c in cands if c in keys), None)
            if key:
                hits.append((words[i]["s"], key, keys[key]))
                i += n
                break
        else:
            i += 1
    return hits


def schedule(hits, hold: float) -> list[tuple[float, float, str, str]]:
    """Non-overlapping (start, end, key, emoji) pictures, each landing on its word."""
    out: list[tuple[float, float, str, str]] = []
    last: dict[str, float] = {}
    # a song's own pictures (e.g. a parody's shop sign) go first; emoji fill in around them, cut short to fit
    for group in ([h for h in hits if is_file(h[2])], [h for h in hits if not is_file(h[2])]):
        for t, key, emoji in group:
            start = max(0.0, t - ENTRANCE_S * 0.75)    # the entrance finishes as the word is sung
            end = start + hold
            nxt = min((s for s, *_ in out if s >= start), default=None)
            if nxt is not None and not is_file(emoji):
                end = min(end, nxt - 0.3)
                if end - start < 1.2:
                    continue
            if any(start < e + 0.3 and s < end + 0.3 for s, e, *_ in out):
                continue
            if not is_file(emoji) and start - last.get(emoji, -REPEAT_S) < REPEAT_S:   # "Christmas" every line:
                continue                                                          # leave room for other words
            last[emoji] = start
            out.append((start, end, key, emoji))
    return sorted(out)


def entrance_for(emoji: str) -> str:
    names = sorted(ENTRANCES)
    return names[int(hashlib.md5(emoji.encode()).hexdigest(), 16) % len(names)]


def pic_settings(rel: str, move: str | None, fade_out: float) -> str:
    s = {"B_CHOICE_BufferStyle": "Default", "E_CHECKBOX_Pictures_PixelOffsets": "0",
         "E_CHECKBOX_Pictures_TransparentBlack": "1", "E_TEXTCTRL_Pictures_TransparentBlack": str(BLACK_LEVEL),
         "E_CHECKBOX_Pictures_WrapX": "0",
         "E_CHOICE_Scaling": "No Scaling", "E_TEXTCTRL_Pictures_Filename": rel,
         "E_TEXTCTRL_Pictures_FrameRateAdj": "1.0", "E_TEXTCTRL_Pictures_Speed": "1.0"}
    if move:
        xc, yc, scale = ENTRANCES[move]
        s.update({"E_CHOICE_Pictures_Direction": "vector", "E_SLIDER_PicturesXC": str(xc), "E_SLIDER_PicturesYC": str(yc),
                  "E_SLIDER_PicturesEndXC": "0", "E_SLIDER_PicturesEndYC": "0",
                  "E_SLIDER_Pictures_StartScale": str(scale), "E_SLIDER_Pictures_EndScale": "100"})
    else:
        s.update({"E_CHOICE_Pictures_Direction": "none", "E_SLIDER_Pictures_StartScale": "100",
                  "E_SLIDER_Pictures_EndScale": "100", "T_TEXTCTRL_Fadeout": f"{fade_out:.2f}"})
    return ",".join(f"{k}={v}" for k, v in sorted(s.items()))



class Xsq:
    def __init__(self, path: Path):
        self.path = path
        self.tree = ET.parse(path)
        root = self.tree.getroot()
        self.db, self.pals, self.eff = root.find("EffectDB"), root.find("ColorPalettes"), root.find("ElementEffects")
        self._db = {e.text: i for i, e in reversed(list(enumerate(self.db)))}
        white = "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1"
        texts = [p.text for p in self.pals]
        if white not in texts:
            ET.SubElement(self.pals, "ColorPalette").text = white
            texts.append(white)
        self.palette = texts.index(white)

    def ref(self, settings: str) -> int:
        if settings not in self._db:
            ET.SubElement(self.db, "Effect").text = settings
            self._db[settings] = len(self.db) - 1
        return self._db[settings]

    def model(self, name: str):
        return next((e for e in self.eff if e.get("type") == "model" and e.get("name") == name), None)

    def strip_old(self, el) -> None:
        """Remove the picture layer a previous run put on top (and the Off layer older runs put under it)."""
        layers = el.findall("EffectLayer")
        if layers and any(IMG_SUB in (self.db[int(e.get("ref", -1))].text or "")
                          for e in layers[0].findall("Effect") if e.get("name") == "Pictures"):
            el.remove(layers[0])
            if len(layers) > 1 and layers[1].findall("Effect") and all(e.get("name") == "Off" for e in layers[1]):
                el.remove(layers[1])

    def save(self) -> None:
        ET.indent(self.tree, space="  ")
        self.tree.write(self.path, encoding="utf-8", xml_declaration=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xsq")
    ap.add_argument("phrases", help="fixed.json from lyrics_align.py")
    ap.add_argument("--show", default=r"F:\ShowFolderAI")
    ap.add_argument("--icons", nargs="+", default=[str(HERE / "lyric_icons.json")],
                    help="icon lists, later ones win; a value ending .png is a picture file (relative to its list)")
    ap.add_argument("--hold", type=float, default=2.4, help="seconds each picture stays up")
    ap.add_argument("--models", nargs="+", default=list(SIZES))
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # emoji in the report on a cp1252 console

    show = Path(a.show)
    phrases = [p for p in json.load(open(a.phrases, encoding="utf-8")) if p["words"]]
    icons = {}
    for f in a.icons:
        for k, v in json.load(open(f, encoding="utf-8")).items():
            icons[k] = str(Path(f).parent / v) if is_file(v) else v
    events = schedule(find_hits(phrases, icons), a.hold)
    sq = Xsq(Path(a.xsq))
    placed = []
    for name in a.models:
        el = sq.model(name)
        if el is None or name not in SIZES:
            print(f"skip {name}: not in the sequence or no picture size for it")
            continue
        sq.strip_old(el)
        pic = ET.Element("EffectLayer")
        for start, end, key, emoji in events:
            rel = model_png(emoji, show, SIZES[name])
            if not rel:
                continue
            s, m, e = (int(round(x * 1000)) for x in (start, start + ENTRANCE_S, end))
            move = entrance_for(emoji)
            for a_ms, b_ms, mv in ((s, m, move), (m, e, None)):
                ET.SubElement(pic, "Effect", {"ref": str(sq.ref(pic_settings(rel, mv, 0.3))), "name": "Pictures",
                                              "startTime": str(a_ms), "endTime": str(b_ms), "palette": str(sq.palette)})
            if name == a.models[0]:
                placed.append((start, key, emoji, move))
        el.insert(0, pic)       # first EffectLayer is the top one
    sq.save()
    for start, key, emoji, move in placed:
        print(f"  {int(start // 60)}:{start % 60:05.2f}  {Path(emoji).name if is_file(emoji) else emoji}  "
              f"{key:<14} {move}")
    print(f"{len(placed)} pictures on {', '.join(a.models)}")


if __name__ == "__main__":
    main()
