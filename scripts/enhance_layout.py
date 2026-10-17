"""Add basic beat/section-driven layout effects to an existing .xsq, in place.

Adds House Outline chase, Trees VU meter, Arches chase + Ripple on section changes,
Stars/Mega Topper Shockwaves on chorus downbeats, Icicles and FloodLights washes.
Existing elements (Faces, moving heads, timing tracks) are not touched; groups missing from
the sequence are inserted in sorted position among the model rows.

    python scripts/enhance_layout.py SEQ.xsq [--mp3 SEQ.mp3] [--palettes story.json]

Re-running restores nothing by itself: copy SEQ.xsq.bak over SEQ.xsq first (the .bak is only made once).
"""
from __future__ import annotations

import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from xlights_mcp.audio.beats import detect_beats
from xlights_mcp.audio.structure import detect_structure

# section palette -> prop role -> (color1, color2); same colour story per section, different shades per prop
PALETTES = {
    "verse": {  # amber / warm white
        "outline": ("#FEB800", "#FFE9B0"), "trees": ("#FFE9B0", "#FFC040"), "arches": ("#FF8C00", "#FFC87A"),
        "stars": ("#FFD700", "#FFFFFF"), "topper": ("#FFFFFF", "#FEB800"), "icicles": ("#FFD9A0", "#FFF4DC"),
        "flood": ("#C07800", "#FF9A20"), "megatree": ("#FFC040", "#FF7A00", "#FFF0C8"),
    },
    "chorusA": {  # red / gold
        "outline": ("#E00000", "#FFD700"), "trees": ("#B00028", "#FF6A00"), "arches": ("#FF4500", "#FFB000"),
        "stars": ("#FFD700", "#FFFFFF"), "topper": ("#FFFFFF", "#E00000"), "icicles": ("#FF6A6A", "#FFFFFF"),
        "flood": ("#A00000", "#FF3000"), "megatree": ("#E00000", "#FFD700", "#FFFFFF"),
    },
    "chorusB": {  # green / white
        "outline": ("#00A000", "#FFFFFF"), "trees": ("#00C060", "#A0FFC0"), "arches": ("#00B8A0", "#80FF40"),
        "stars": ("#FFFFFF", "#C0FFC0"), "topper": ("#FFD700", "#00A000"), "icicles": ("#B0FFD0", "#FFFFFF"),
        "flood": ("#007030", "#00C040"), "megatree": ("#00B050", "#FFFFFF", "#00D8C0"),
    },
    "peak": {  # white / gold
        "outline": ("#FFFFFF", "#FFD700"), "trees": ("#FFD700", "#FF8000"), "arches": ("#FFFFFF", "#FF4040"),
        "stars": ("#FFFFFF", "#FFD700"), "topper": ("#FFD700", "#FFFFFF"), "icicles": ("#FFF0C0", "#FFFFFF"),
        "flood": ("#FFD070", "#FFFFFF"), "megatree": ("#FFFFFF", "#FFD700", "#FF3030"),
    },
    "outro": {  # red / white
        "outline": ("#E00000", "#FFFFFF"), "trees": ("#FF2040", "#FFB0B0"), "arches": ("#FF6000", "#FFFFFF"),
        "stars": ("#FFFFFF", "#FF8080"), "topper": ("#FFD700", "#E00000"), "icicles": ("#FFD0D0", "#FFFFFF"),
        "flood": ("#C00000", "#FF4040"), "megatree": ("#E00000", "#FFFFFF", "#FF8040"),
    },
}
ROLE = {"House Outline": "outline", "Trees": "trees", "Arches": "arches", "Stars": "stars",
        "Mega Topper": "topper", "Mega Tree": "megatree", "Icicles": "icicles", "FloodLights": "flood"}

CHASE = ("B_CHOICE_BufferStyle=Per Model Single Line,E_CHECKBOX_Chase_Group_All=0,"
         "E_CHOICE_Chase_Type1={d},E_CHOICE_Fade_Type=From Head,E_CHOICE_SingleStrand_Colors=Palette,"
         "E_NOTEBOOK_SSEFFECT_TYPE=Chase,E_SLIDER_Color_Mix1=40,E_SLIDER_Number_Chases=1,"
         "E_TEXTCTRL_Chase_Offset=0.0,E_TEXTCTRL_Chase_Rotations=1.0")
VU = ("B_CHOICE_BufferStyle=Per Model Default,E_CHECKBOX_Regex=0,E_CHOICE_VUMeter_Type={t},"
      "E_SLIDER_VUMeter_Bars=8,E_SLIDER_VUMeter_Gain=0,E_SLIDER_VUMeter_Sensitivity=70,E_TEXTCTRL_Filter=")
RIPPLE = ("E_CHECKBOX_Ripple3D=0,E_CHOICE_Ripple_Draw_Style=Old,E_CHOICE_Ripple_Movement=Explode,"
          "E_CHOICE_Ripple_Object_To_Draw=Circle,E_SLIDER_Ripple_Thickness=5,E_SLIDER_Ripple_XC=0,"
          "E_SLIDER_Ripple_YC=0,E_TEXTCTRL_Ripple_Cycles=1,T_CHECKBOX_Canvas=0,T_CHECKBOX_LayerMorph=0,"
          "T_CHOICE_LayerMethod=Normal,T_SLIDER_EffectLayerMix=0")
SHOCK = ("E_CHECKBOX_Shockwave_Blend_Edges=1,E_CHECKBOX_Shockwave_Scale=1,E_CHOICE_Shockwave_TimingTrack=,"
         "E_NOTEBOOK_Shockwave=Position,E_SLIDER_Shockwave_Accel=0,E_SLIDER_Shockwave_CenterX=50,"
         "E_SLIDER_Shockwave_CenterY=50,E_SLIDER_Shockwave_Cycles=1,E_SLIDER_Shockwave_End_Radius={r},"
         "E_SLIDER_Shockwave_End_Width=40,E_SLIDER_Shockwave_Start_Radius=1,E_SLIDER_Shockwave_Start_Width=0,"
         "T_CHECKBOX_Canvas=0,T_CHECKBOX_LayerMorph=0,T_CHOICE_LayerMethod=Normal,T_SLIDER_EffectLayerMix=0,"
         "T_TEXTCTRL_Fadeout=0.2")
# Aurora colour mode 1 paints its R/G/B ribbons with palette colours 1/2/3 (the "color mask")
AURORA = ("E_0FILEPICKERCTRL_IFS=F:/ShowFolderAI/Shaders/Aurora.fs,E_CHOICE_SHADERXYZZY_uColMode=Alternate Color Palette (3 used) ,"
          "E_CHECKBOX_SHADERXYZZY_uContRot=1,E_SLIDER_SHADERXYZZY_uIntensity=100,E_SLIDER_SHADERXYZZY_uZoom=100,"
          "E_SLIDER_SHADERXYZZY_uRotate=0,E_SLIDER_Shader_Speed=100,E_TEXTCTRL_Shader_LeadIn=0,E_TEXTCTRL_Shader_Offset_X=0,"
          "E_TEXTCTRL_Shader_Offset_Y=0,E_TEXTCTRL_Shader_Zoom=0,T_TEXTCTRL_Fadein=0.5,T_TEXTCTRL_Fadeout=0.5")
ON_TINT = ("E_CHECKBOX_On_Shimmer=0,E_TEXTCTRL_Eff_On_End=100,E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_On_Cycles=1.0,"
           "T_CHECKBOX_Canvas=0,T_CHECKBOX_LayerMorph=0,T_CHOICE_LayerMethod=Average,T_SLIDER_EffectLayerMix=0")
ON = "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100,E_CHECKBOX_On_Shimmer=0,E_TEXTCTRL_On_Cycles=1.0"


# contrasting sparkle colour per section story (xLights defaults to white)
SPARKLE_COLOR = {"verse": "#40C0FF", "chorusA": "#00FF50", "chorusB": "#FF2030", "peak": "#FF2030", "outro": "#00FF50"}


def palette_text(c1: str, *more: str, sparkle: bool = False, sparkle_color: str = "#FFFFFF") -> str:
    cols = [c1, *more]
    btn = cols + ["#FFFFFF"] * (8 - len(cols))
    chk = [1] * len(cols) + [0] * (8 - len(cols))
    parts = [f"C_BUTTON_Palette{i + 1}={c}" for i, c in enumerate(btn)]
    parts += [f"C_CHECKBOX_Palette{i + 1}={v}" for i, v in enumerate(chk)]
    parts += ["C_SLIDER_Brightness=100", "C_SLIDER_Contrast=0", "C_SLIDER_SparkleFrequency=0",
              f"C_CHECKBOX_MusicSparkles={1 if sparkle else 0}", f"C_COLOURPICKERCTRL_SparklesColour={sparkle_color}"]
    return ",".join(parts)


def section_plan(sections, bars):
    """Return per-bar palette names and the list of (start_ms, end_ms, kind, energy) sections."""
    secs = []
    for s in sections:
        kind = {"chorus": "chorus", "outro": "outro"}.get(s.label, "verse")
        if s.label == "transition":
            kind = "verse"
        secs.append((int(s.start_time * 1000), int(s.end_time * 1000), kind, s.energy_level))
    return secs


class Seq:
    def __init__(self, path: Path):
        self.tree = ET.parse(path)
        self.root = self.tree.getroot()
        self.db = self.root.find("EffectDB")
        self.pals = self.root.find("ColorPalettes")
        self._db, self._pal = {}, {}
        for i, e in enumerate(self.db):
            self._db.setdefault(e.text or "", i)
        self.disp = self.root.find("DisplayElements")
        self.eff = self.root.find("ElementEffects")

    def ref(self, settings: str) -> int:
        if settings not in self._db:
            ET.SubElement(self.db, "Effect").text = settings
            self._db[settings] = len(self.db) - 1
        return self._db[settings]

    def pal(self, key: str, role: str) -> int:
        if (key, role) not in self._pal:
            # tint0..2 = one colour of the Mega Tree set, so a tint layer can step through them
            if role == "treetint":
                cols = (PALETTES[key]["trees"][0],)
            elif role.startswith("tint"):
                cols = (PALETTES[key]["megatree"][int(role[4:])],)
            else:
                cols = PALETTES[key][role]
            # no sparkles on the floods; the tint layer is Average-blended over the shader, so they go on the shader layer
            sparkle = role not in ("treetint", "flood")
            ET.SubElement(self.pals, "ColorPalette").text = palette_text(*cols, sparkle=sparkle, sparkle_color=SPARKLE_COLOR[key])
            self._pal[(key, role)] = len(self.pals) - 1
        return self._pal[(key, role)]

    def layers(self, name: str):
        for e in self.eff:
            if e.get("name") == name and e.get("type") == "model":
                return e
        self._insert(self.disp, ET.Element("Element", {"collapsed": "0", "type": "model", "name": name, "visible": "1"}))
        el = ET.Element("Element", {"type": "model", "name": name})
        self._insert(self.eff, el)
        return el

    @staticmethod
    def _insert(parent, el):
        """Insert in sorted position among model rows (before the first timing row)."""
        idx = len(parent)
        for i, e in enumerate(parent):
            if e.get("type") == "timing":
                idx = i
                break
        for i, e in enumerate(list(parent)[:idx]):
            if e.get("name", "").lower() > el.get("name").lower():
                idx = i
                break
        parent.insert(idx, el)

    def add(self, model: str, layer: int, name: str, start: int, end: int, settings: str, palkey: str, role: str | None = None):
        el = self.layers(model)
        while len(el.findall("EffectLayer")) <= layer:
            ET.SubElement(el, "EffectLayer")
        lay = el.findall("EffectLayer")[layer]
        ET.SubElement(lay, "Effect", {
            "name": name, "startTime": str(start), "endTime": str(end),
            "ref": str(self.ref(settings)), "palette": str(self.pal(palkey, role or ROLE[model])),
        })


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xsq")
    ap.add_argument("--mp3")
    ap.add_argument("--palettes", help='JSON overriding the colour story: {"chorusA": {"trees": ["#hex", "#hex"]}, '
                    '"sparkle": {"chorusA": "#hex"}}; only the roles given are replaced')
    args = ap.parse_args()
    if args.palettes:
        over = json.load(open(args.palettes, encoding="utf-8"))
        SPARKLE_COLOR.update(over.pop("sparkle", {}))
        for key, roles in over.items():
            PALETTES[key].update({role: tuple(cols) for role, cols in roles.items()})
    xsq = Path(args.xsq)
    mp3 = Path(args.mp3) if args.mp3 else xsq.with_suffix(".mp3")

    beats = detect_beats(mp3)
    secs = section_plan(detect_structure(mp3), None)
    dur = int(float(ET.parse(xsq).getroot().findtext("head/sequenceDuration")) * 1000)
    bars = [int(t * 1000) for t in beats.downbeat_times]
    bars.append(min(dur, bars[-1] + (bars[-1] - bars[-2])))
    print(f"{beats.tempo:.0f} BPM, {len(bars) - 1} bars, {len(secs)} sections")

    bak = xsq.with_suffix(".xsq.bak")
    if not bak.exists():
        shutil.copy2(xsq, bak)
    sq = Seq(xsq)

    def sec_at(t):
        for s in secs:
            if s[0] <= t < s[1]:
                return s
        return secs[-1]

    # per-bar palette: chorus alternates A/B every 8 bars of chorus; peak overrides stars only
    chorus_bar = 0
    bar_pal, bar_kind, bar_peak = [], [], []
    for i in range(len(bars) - 1):
        s = sec_at(bars[i])
        kind = s[2]
        if kind == "chorus":
            pk = "chorusA" if (chorus_bar // 8) % 2 == 0 else "chorusB"
            chorus_bar += 1
        elif kind == "outro":
            pk = "outro"
        else:
            pk = "verse"
        bar_pal.append(pk)
        bar_kind.append(kind)
        bar_peak.append(s[3] >= 0.9)

    n = len(bars) - 1
    # House Outline: chase every bar
    for i in range(n):
        sq.add("House Outline", 0, "SingleStrand", bars[i], bars[i + 1],
               CHASE.format(d="Left-Right" if i % 2 == 0 else "Right-Left"), bar_pal[i])
    # Trees: VU meter per section, split at 16 bars; the Mega Tree switches colour on the same blocks
    tree_blocks = []  # (first bar, last bar, palette key)
    for s0, s1, kind, _ in secs:
        idx = [i for i in range(n) if s0 <= bars[i] < s1]
        for k in range(0, len(idx), 16):
            chunk = idx[k:k + 16]
            tree_blocks.append((chunk[0], chunk[-1], bar_pal[chunk[0]]))
    for blk, (b0, b1, pk) in enumerate(tree_blocks):
        sq.add("Trees", 0, "VU Meter", bars[b0], bars[b1 + 1],
               VU.format(t="Spectrogram" if blk % 2 == 0 else "Volume Bars"), pk)
    # Arches: chase every other bar (layer 1), Ripple on first bar of each section (layer 0, top)
    for i in range(0, n, 2):
        sq.add("Arches", 1, "SingleStrand", bars[i], bars[min(i + 2, n)],
               CHASE.format(d="Left-Right" if (i // 2) % 2 == 0 else "Right-Left"), bar_pal[i])
    for s0, *_ in secs[1:]:
        i = min(range(n), key=lambda j: abs(bars[j] - s0))
        sq.add("Arches", 0, "Ripple", bars[i], bars[i + 1], RIPPLE, bar_pal[i])
    # Stars + Mega Topper: shockwave on chorus downbeats; bigger and white/gold at peaks
    for i in range(n):
        if bar_kind[i] != "chorus":
            continue
        pk = "peak" if bar_peak[i] else bar_pal[i]
        end = min(bars[i] + 450, bars[i + 1])
        for m in ("Stars", "Mega Topper"):
            sq.add(m, 0, "Shockwave", bars[i], end, SHOCK.format(r=160 if bar_peak[i] else 100), pk)
    # Mega Tree: Aurora shader (palette-masked) with a one-colour On (Average blend) on top. Both change
    # only when the Trees VU meter does, and the tint is the Trees' first colour so the two trees match.
    for b0, b1, pk in tree_blocks:
        sq.add("Mega Tree", 1, "Shader", bars[b0], bars[b1 + 1], AURORA, pk)
        sq.add("Mega Tree", 0, "On", bars[b0], bars[b1 + 1], ON_TINT, pk, role="treetint")
    # Icicles: wash per 2 bars, FloodLights: wash per section
    for i in range(0, n, 2):
        sq.add("Icicles", 0, "On", bars[i], bars[min(i + 2, n)], ON, bar_pal[i])
    for s0, s1, kind, _ in secs:
        idx = [i for i in range(n) if s0 <= bars[i] < s1]
        if idx:
            sq.add("FloodLights", 0, "On", bars[idx[0]], bars[idx[-1] + 1], ON, bar_pal[idx[0]])

    # hide model/group rows with no effects (timing rows stay as they are)
    used = {e.get("name") for e in sq.eff if e.get("type") == "model" and e.findall(".//Effect")}
    hidden = 0
    for e in sq.disp:
        if e.get("type") == "model" and e.get("name") not in used and e.get("visible") != "0":
            e.set("visible", "0")
            hidden += 1
    print(f"hid {hidden} unused rows, {len(used)} visible")
    # sequences were cut at the last lyric; stretch to the audio so the outro isn't clipped
    sq.root.find("head/sequenceDuration").text = f"{max(dur, secs[-1][1]) / 1000:.3f}"
    ET.indent(sq.tree, space="  ")
    sq.tree.write(xsq, encoding="utf-8", xml_declaration=True)
    print("updated", xsq, "| palettes:", len(sq.pals), "| effect defs:", len(sq.db))


if __name__ == "__main__":
    main()
