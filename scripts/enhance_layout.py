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
import collections
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from xlights_mcp.audio.beats import detect_beats
from xlights_mcp.audio.structure import detect_structure

from grid_tracks import add_grid_tracks

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
for _p in PALETTES.values():
    _p["text"] = ("#FFFFFF",)
TREE_LIKE = ("Trees", "Pixel Forest")  # the Pixel Forest (5 small matrices) gets exactly what the Trees get
ROLE = {"House Outline": "outline", "Trees": "trees", "Pixel Forest": "trees", "Arches": "arches", "Stars": "stars",
        "Mega Topper": "topper", "Mega Tree": "megatree", "Trees Stars": "trees", "Icicles": "icicles", "FloodLights": "flood"}

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
FADE = "T_TEXTCTRL_Fadein=0.5,T_TEXTCTRL_Fadeout=0.5"
_SPD = "E_TEXTCTRL_Shader_LeadIn=0,E_TEXTCTRL_Shader_Offset_X=0,E_TEXTCTRL_Shader_Offset_Y=0,E_TEXTCTRL_Shader_Zoom=0"
# Mega Tree shaders. Settings are copied from the user's own sequences (Sequences/*.xsqz, most common Mega Tree
# variant) minus the layer-blend method; Audio - PlasmaLike had no uses so it gets defaults. Aurora's colour mode 1
# and Spiral Over Beams' paint their ribbons with palette colours 1/2/3 (the "color mask"); the rest are fixed-colour
# and are recoloured by the Average-blend On tint layer on top.
SHADERS = {
    "Aurora": ("E_CHOICE_SHADERXYZZY_uColMode=Alternate Color Palette (3 used) ,E_CHECKBOX_SHADERXYZZY_uContRot=1,"
               "E_SLIDER_SHADERXYZZY_uIntensity=100,E_SLIDER_SHADERXYZZY_uZoom=100,E_SLIDER_SHADERXYZZY_uRotate=0,"
               "E_SLIDER_Shader_Speed=100," + _SPD),
    "Vortex V2": ("B_CHOICE_BufferStyle=Per Preview,E_SLIDER_SHADERXYZZY_ColorB=0,E_SLIDER_SHADERXYZZY_ColorG=0,"
                  "E_SLIDER_SHADERXYZZY_Filling=296,E_SLIDER_SHADERXYZZY_Half=0,E_SLIDER_SHADERXYZZY_Rotation=50,"
                  "E_SLIDER_SHADERXYZZY_Stripe=2900,E_SLIDER_Shader_Speed=302,E_TEXTCTRL_Shader_LeadIn=0,"
                  "E_TEXTCTRL_Shader_Offset_X=100,E_TEXTCTRL_Shader_Offset_Y=0,E_TEXTCTRL_Shader_Zoom=100"),
    "Black Cherry Cosmos": ("E_SLIDER_SHADERXYZZY_mouseX=0,E_SLIDER_SHADERXYZZY_mouseY=0,E_SLIDER_Shader_Speed=100,"
                            "E_TEXTCTRL_Shader_LeadIn=0,E_TEXTCTRL_Shader_Offset_X=0,E_TEXTCTRL_Shader_Offset_Y=0,"
                            "E_TEXTCTRL_Shader_Zoom=68"),
    "Continua Variation": ("E_SLIDER_Shader_Speed=500,E_TEXTCTRL_Shader_LeadIn=0,E_TEXTCTRL_Shader_Offset_X=0,"
                           "E_TEXTCTRL_Shader_Offset_Y=0,E_TEXTCTRL_Shader_Zoom=-20,T_CHECKBOX_Canvas=1"),
    "Spiral Over Beams": ("E_CHOICE_SHADERXYZZY_uColMode=Alternate Color Palette (3 used) ,E_SLIDER_SHADERXYZZY_uCore=26,"
                          "E_SLIDER_SHADERXYZZY_uIntensity=64,E_SLIDER_SHADERXYZZY_uOffsetX=0,E_SLIDER_SHADERXYZZY_uOffsetY=0,"
                          "E_SLIDER_SHADERXYZZY_uZoom=861,E_SLIDER_Shader_Speed=52,E_TEXTCTRL_Shader_LeadIn=0,"
                          "E_TEXTCTRL_Shader_Offset_X=0,E_TEXTCTRL_Shader_Offset_Y=100,E_TEXTCTRL_Shader_Zoom=5"),
    "Blue Streaks": ("B_CHOICE_BufferStyle=Per Preview,B_CHOICE_BufferTransform=Flip Horizontal,B_CHOICE_PerPreviewCamera=2D,"
                     "E_CHECKBOX_SHADERXYZZY_uContRot=1,E_CHOICE_SHADERXYZZY_uColMode=Shader Defaults ,"
                     "E_SLIDER_SHADERXYZZY_uIntensity=100,E_SLIDER_SHADERXYZZY_uOffsetX=0,E_SLIDER_SHADERXYZZY_uOffsetY=0,"
                     "E_SLIDER_SHADERXYZZY_uRotate=737,E_SLIDER_SHADERXYZZY_uZoom=500,E_SLIDER_Shader_Speed=100," + _SPD),
    "Fly Through": ("E_SLIDER_SHADERXYZZY_c0=0,E_SLIDER_SHADERXYZZY_c1=0,E_SLIDER_SHADERXYZZY_c2=0,E_SLIDER_SHADERXYZZY_j=50,"
                    "E_SLIDER_SHADERXYZZY_k=50,E_SLIDER_Shader_Speed=300," + _SPD),
    "Hex Vortex": ("E_SLIDER_SHADERXYZZY_B=25,E_SLIDER_SHADERXYZZY_G=12,E_SLIDER_SHADERXYZZY_R=5,E_SLIDER_SHADERXYZZY_centerX=50,"
                   "E_SLIDER_SHADERXYZZY_centerY=50,E_SLIDER_SHADERXYZZY_rotation=5,E_SLIDER_SHADERXYZZY_shapeX=200,"
                   "E_SLIDER_SHADERXYZZY_shapeY=225,E_SLIDER_SHADERXYZZY_speed=50,E_SLIDER_Shader_Speed=100," + _SPD),
    "InnerDimensionalMatrix": ("E_CHECKBOX_SHADERXYZZY_color=1,E_CHECKBOX_SHADERXYZZY_mirror=0,E_SLIDER_SHADERXYZZY_cycle=100,"
                               "E_SLIDER_SHADERXYZZY_flash=750,E_SLIDER_SHADERXYZZY_line=1,E_SLIDER_SHADERXYZZY_rate=100,"
                               "E_SLIDER_SHADERXYZZY_scale=100,E_SLIDER_SHADERXYZZY_seed1=15500,E_SLIDER_SHADERXYZZY_seed2=64900,"
                               "E_SLIDER_SHADERXYZZY_zoom=17,E_SLIDER_Shader_Speed=100," + _SPD),
    "Audio - PlasmaLike": "E_SLIDER_Shader_Speed=100," + _SPD,
}
# shader rotation per section story; consecutive sections of a story step through its list
SHADER_PICK = {
    "verse": ["Continua Variation", "Fly Through", "Aurora"],
    "chorusA": ["Vortex V2", "Hex Vortex"],
    "chorusB": ["Spiral Over Beams", "Blue Streaks", "Audio - PlasmaLike"],
    "peak": ["Black Cherry Cosmos", "InnerDimensionalMatrix"],
    "outro": ["Aurora", "Continua Variation"],
}


def shader_settings(name: str, shader_dir: str) -> str:
    return f"E_0FILEPICKERCTRL_IFS={shader_dir}/{name}.fs,{SHADERS[name]},{FADE}"


PINWHEEL = ("E_CHECKBOX_Pinwheel_Rotation=0,E_CHOICE_Pinwheel_3D=3D Inverted,E_CHOICE_Pinwheel_Style=New Render Method,"
            "E_SLIDER_PinwheelXC=0,E_SLIDER_PinwheelYC=0,E_SLIDER_Pinwheel_ArmSize=100,E_SLIDER_Pinwheel_Arms=2,"
            "E_SLIDER_Pinwheel_Offset=0,E_SLIDER_Pinwheel_Speed=10,E_SLIDER_Pinwheel_Thickness=30,E_SLIDER_Pinwheel_Twist=0,"
            "T_CHECKBOX_Canvas=0,T_CHECKBOX_LayerMorph=0,T_CHOICE_LayerMethod=Normal,T_SLIDER_EffectLayerMix=0")
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
            if role == "lyric":
                cols = (PALETTES[key]["stars"][0],)
            elif role == "lyricbg":
                c = PALETTES[key]["flood"][0].lstrip("#")
                cols = ("#" + "".join(f"{int(int(c[k:k + 2], 16) * 0.3):02X}" for k in (0, 2, 4)),)
            elif role == "treetint":
                cols = (PALETTES[key]["trees"][0],)
            elif role.startswith("tint"):
                cols = (PALETTES[key]["megatree"][int(role[4:])],)
            else:
                cols = PALETTES[key][role]
            # no sparkles on the floods; the tint layer is Average-blended over the shader, so they go on the shader layer
            sparkle = role not in ("treetint", "flood", "text", "lyric", "lyricbg")
            ET.SubElement(self.pals, "ColorPalette").text = palette_text(*cols, sparkle=sparkle, sparkle_color=SPARKLE_COLOR[key])
            self._pal[(key, role)] = len(self.pals) - 1
        return self._pal[(key, role)]

    def layers(self, name: str):
        for d in self.disp:
            if d.get("type") == "model" and d.get("name") == name:
                d.set("visible", "1")
        for e in self.eff:
            if e.get("name") == name and e.get("type") == "model":
                return e
        self._insert(self.disp, ET.Element("Element", {"collapsed": "0", "type": "model", "name": name, "visible": "1"}))
        el = ET.Element("Element", {"type": "model", "name": name})
        self._insert(self.eff, el)
        return el

    def add_sub(self, model: str, sub: str, name: str, start: int, end: int, settings: str, palkey: str, role: str):
        """Effect on a submodel row (xLights stores these as SubModelEffectLayer inside the model's Element)."""
        el = self.layers(model)
        if el.find("EffectLayer") is None:
            el.insert(0, ET.Element("EffectLayer"))
        lay = next((l for l in el.findall("SubModelEffectLayer") if l.get("name") == sub), None)
        if lay is None:
            lay = ET.SubElement(el, "SubModelEffectLayer", {"name": sub})
        ref = self.ref(settings)
        attrs = {"ref": str(ref), "name": name}
        dup = sum(1 for e in lay if e.get("ref") == str(ref))
        if dup:
            attrs["id"] = str(dup)  # xLights numbers repeats of the same settings on one row
        attrs.update(startTime=str(start), endTime=str(end), palette=str(self.pal(palkey, role)))
        ET.SubElement(lay, "Effect", attrs)

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


MH_MODELS = [f"MH-{i}" for i in range(1, 9)]
MH_PAN = 90.0  # pan 90 keeps every beam in the camera plane: tilt is then the left/right lean (positive = right)
MH_WHITE = (0.0, 0.0, 1.0)
MH_ANY = "#FFFFFF"
MH_PRE_MS = 1000  # longest lead-in a head gets to reach its next pose


VIDEO = ("E_CHECKBOX_SynchroniseWithAudio=0,E_CHECKBOX_Video_AspectRatio=0,E_CHECKBOX_Video_TransparentBlack=0,"
         "E_CHOICE_Video_DurationTreatment=Normal,E_FILEPICKERCTRL_Video_Filename={f},E_TEXTCTRL_SampleSpacing=0,"
         "E_TEXTCTRL_Video_CropBottom={cb},E_TEXTCTRL_Video_CropLeft={cl},E_TEXTCTRL_Video_CropRight={cr},E_TEXTCTRL_Video_CropTop={ct},"
         "E_TEXTCTRL_Video_Starttime=0.0,E_TEXTCTRL_Video_TransparentBlack=0,T_CHECKBOX_LayerMorph=0,T_CHOICE_LayerMethod=Normal,"
         "T_SLIDER_EffectLayerMix=0")
MEGA_TREE_LIKE = ("Mega Tree", "Matrix", "Matrix 2")
RADIO = "Radio_EFL"
RADIO_TEXT = ("E_CHECKBOX_Text_Color_PerWord=0,E_CHECKBOX_Text_PixelOffsets=0,E_CHOICE_Text_Count=none,E_CHOICE_Text_Dir=left,"
              "E_CHOICE_Text_Effect=normal,E_CHOICE_Text_Font=5-5x5 Mono,E_FILEPICKERCTRL_Text_File=,"
              "E_FONTPICKER_Text_Font='segoe ui',E_NOTEBOOK=Start Position,E_SLIDER_Text_XEnd=0,E_SLIDER_Text_XStart=0,"
              "E_SLIDER_Text_YEnd=0,E_SLIDER_Text_YStart=0,E_TEXTCTRL_Text={t},E_TEXTCTRL_Text_Speed=10,"
              "T_CHECKBOX_LayerMorph=0,T_CHOICE_LayerMethod=Normal,T_SLIDER_EffectLayerMix=0")
RADIO_VU = ("B_CHOICE_BufferStyle=Default,E_CHECKBOX_Regex=0,E_CHOICE_VUMeter_Type={t},E_SLIDER_VUMeter_Bars=20,"
            "E_SLIDER_VUMeter_Gain=0,E_SLIDER_VUMeter_Sensitivity=70,E_TEXTCTRL_Filter=")
STROBE = "E_CHECKBOX_Strobe_Music=1,E_SLIDER_Number_Strobes=2,E_SLIDER_Strobe_Duration=8,E_SLIDER_Strobe_Type=1"


_NO_PUNCT = str.maketrans("", "", ".,!?;:")  # trailing punctuation only eats width on the matrix
LYRIC_TEXT = ("E_CHECKBOX_Text_Color_PerWord=0,E_CHECKBOX_Text_PixelOffsets=0,E_CHOICE_Text_Count=none,E_CHOICE_Text_Dir=none,"
              "E_CHOICE_Text_Effect=normal,E_CHOICE_Text_Font=12-15x15 Bold,E_CHOICE_Text_LyricTrack=,"
              "E_FILEPICKERCTRL_Text_File=,E_FONTPICKER_Text_Font='segoe ui',E_NOTEBOOK=Start Position,E_SLIDER_Text_XEnd={xe},"
              "E_SLIDER_Text_XStart={xs},E_SLIDER_Text_YEnd=0,E_SLIDER_Text_YStart=0,E_TEXTCTRL_Text={w},E_TEXTCTRL_Text_Speed=10,"
              "T_CHECKBOX_LayerMorph=0,T_CHOICE_LayerMethod=Normal,T_SLIDER_EffectLayerMix=0")
LYRIC_CHAR_PX, LYRIC_NARROW_PX, LYRIC_MATRIX_PX, LYRIC_MARGIN_PX = 13, 8, 120, 4  # 12-15x15 Bold glyph advance, Lyrics Matrix width


def lyric_drift(word: str) -> int:
    """Half-travel (percent of the matrix width) for a word wider than the matrix, else 0: it drifts left to right."""
    width = sum(LYRIC_NARROW_PX if ch in "I'-1 " else LYRIC_CHAR_PX for ch in word)
    over = width - (LYRIC_MATRIX_PX - 2 * LYRIC_MARGIN_PX)
    return 0 if over <= 0 else min(200, int(round((over / 2 + 2) / LYRIC_MATRIX_PX * 100)))


def add_lyric_words(sq: Seq, tree_blocks, bars) -> None:
    """Lyrics Matrix: the sung words (one at a time, from a 'Lyrics - Words' timing track made from the singing props' word
    layer) in a palette colour over a dark shade of the section's colour; both change with the Trees VU blocks."""
    src = None
    for el in sq.eff:
        if el.get("type") == "timing" and el.get("name", "").startswith("Lyrics - "):
            layers = el.findall("EffectLayer")
            if len(layers) == 3 and (src is None or len(layers[1]) > len(src[1])):
                src = layers  # phrases, words, phonemes
    if src is None:
        print("lyrics matrix: no lyric tracks, skipped")
        return
    # The Text effect's "Lyrics - Words" choice = a timing track named "Lyrics" with phrase/word/phoneme layers, as in the
    # user's own sequences; the singing props' tracks have other names, so copy the fullest one under that name
    # (upper case for readability on the matrix; the props' own tracks keep their case).
    if not any(e.get("name") == "Lyrics" and e.get("type") == "timing" for e in sq.eff):
        ET.SubElement(sq.disp, "Element", {"collapsed": "0", "type": "timing", "name": "Lyrics", "visible": "1", "active": "0"})
        track = ET.SubElement(sq.eff, "Element", {"type": "timing", "name": "Lyrics"})
        for layer in src:
            lay = ET.SubElement(track, "EffectLayer")
            for e in layer.findall("Effect"):
                ET.SubElement(lay, "Effect", {"label": e.get("label", "").upper().translate(_NO_PUNCT).strip(), "startTime": e.get("startTime"), "endTime": e.get("endTime")})
    best = src[1]
    # colour per word = colour story of the Trees block it falls in; the background On layer runs per block
    for b0, b1, pk in tree_blocks:
        sq.add("Lyrics Matrix", 1, "On", bars[b0], bars[b1 + 1], ON, pk, role="lyricbg")
    block_of = lambda t: next((pk for b0, b1, pk in tree_blocks if bars[b0] <= t < bars[b1 + 1]), tree_blocks[-1][2])
    words = [(int(e.get("startTime")), int(e.get("endTime")), e.get("label", "").upper().translate(_NO_PUNCT).replace("&", "AND").replace(",", "").strip())
             for e in best.findall("Effect")]
    drifting = 0
    for a, b, w in words:
        if not w or b - a < 25:
            continue
        d = lyric_drift(w)
        drifting += d > 0
        sq.add("Lyrics Matrix", 0, "Text", a, b, LYRIC_TEXT.format(w=w, xs=-d, xe=d), block_of(a), role="lyric")
    print(f"lyrics matrix: {len(words)} words ({drifting} drift left to right), {len(tree_blocks)} colour blocks")


def add_radio(sq: Seq, bars, bar_kind, bar_peak, bar_pal, tree_blocks, title: str, dur: int, artist: str = "Eclipse 6") -> None:
    """Radio_EFL: scrolling "now playing" text on the Tune to Matrix, a VU meter on the Large matrix (changing with the
    Trees VU blocks), beat pulses on the speakers, bar-driven shockwaves on the spinners and a chase on the outline/handle.
    Submodel rows follow how the user's own sequences drive this model."""
    n = len(bars) - 1
    text = f"NOW PLAYING: {title} - {artist}".upper().replace(",", "").replace("&", "AND")
    sq.add_sub(RADIO, "Tune to Matrix", "Text", 0, dur, RADIO_TEXT.format(t=text), "verse", "text")
    for blk, (b0, b1, pk) in enumerate(tree_blocks):
        t = "Spectrogram" if blk % 2 == 0 else "Volume Bars"
        sq.add_sub(RADIO, "Large matrix", "VU Meter", bars[b0], bars[b1 + 1], RADIO_VU.format(t=t), pk, "trees")
    shock = "B_CHOICE_BufferStyle=Per Preview," + SHOCK
    for i in range(n):
        q = [bars[i] + (bars[i + 1] - bars[i]) * k // 4 for k in range(5)]
        pk, chorus = bar_pal[i], bar_kind[i] == "chorus"
        r = 160 if bar_peak[i] else 100
        for sub in ("Outline", "Handle"):
            sq.add_sub(RADIO, sub, "SingleStrand", bars[i], bars[i + 1],
                       CHASE.format(d="Left-Right" if i % 2 == 0 else "Right-Left"), pk, "outline")
        # speakers ping-pong in choruses: circles on beats 1 and 3, star on beats 2 and 4; otherwise one pulse per bar
        beats = range(4) if chorus else (0,)
        for k in beats:
            end = min(q[k] + 450, q[k + 1] if chorus else bars[i + 1])
            if k % 2 == 0:
                sq.add_sub(RADIO, "Speaker Circles", "Shockwave", q[k], end, shock.format(r=r), pk, "icicles")
            else:
                sq.add_sub(RADIO, "Speaker Star", "Shockwave", q[k], end, shock.format(r=r), pk, "stars")
        if not chorus:
            sq.add_sub(RADIO, "Speaker Star", "SingleStrand", q[2], bars[i + 1],
                       CHASE.format(d="Right-Left" if i % 2 == 0 else "Left-Right"), pk, "stars")
        sq.add_sub(RADIO, "5x5 Spinners", "Shockwave", bars[i], min(bars[i] + 450, bars[i + 1]), shock.format(r=r), pk, "arches")
        if bar_peak[i] and chorus:
            sq.add_sub(RADIO, "5x5 Spinners", "Strobe", q[2], q[3], STROBE, "peak", "arches")
    print(f"radio: '{text}'")


def add_moving_heads(sq: Seq, bars, bar_kind, bar_peak, secs) -> None:
    """A few white moving-head moves tied to the sections: a soft fan 'pool' in verses, a sweep on each section
    change, left/right bank ping-pong on chorus beats, a skyward strobe burst on peak-chorus downbeats and a
    converge-and-fade over the last two bars. Heads are dark between effects."""
    from video_beams_to_xsq import mh_settings  # full xLights key set, so the effects survive export/import

    n = len(bars) - 1
    pal = len(sq.pals)
    ET.SubElement(sq.pals, "ColorPalette").text = palette_text(MH_ANY)

    def fan(i):  # -1 (leftmost head) .. +1 (rightmost)
        return (i - 3.5) / 3.5

    plan = [[] for _ in MH_MODELS]  # per head: (start, end, tilt0, tilt1, dimmer)

    def put(i, start, end, t0, t1, dimmer):
        plan[i].append((start, end, t0, t1, dimmer))

    def emit(i, start, end, t0, t1, dimmer, link=False):
        settings = mh_settings(MH_PAN, MH_PAN, t0, t1, MH_WHITE, "Dimmer: " + dimmer if dimmer else "", link=link)
        el = sq.layers(MH_MODELS[i])
        if not el.findall("EffectLayer"):
            ET.SubElement(el, "EffectLayer")
        ET.SubElement(el.find("EffectLayer"), "Effect", {
            "name": "Moving Head", "startTime": str(start), "endTime": str(end), "ref": str(sq.ref(settings)), "palette": str(pal)})

    def curve(*pts):
        return "&comma;".join(f"{v}" for p in pts for v in p)

    FADE_UP_DOWN = curve((0, 0), (0.5, 0.6), (1, 0))
    SWEEP_DIM = curve((0, 0), (0.15, 1), (0.7, 1), (1, 0))
    PING_DIM = curve((0, 1), (1, 0))
    BURST_DIM = curve((0, 1), (0.12, 0), (0.25, 1), (0.37, 0), (0.5, 1), (0.62, 0), (0.75, 1), (1, 0))
    OUTRO_DIM = curve((0, 0), (0.4, 0.8), (1, 0))

    kind = ["pool"] * n
    for i in range(n):
        if bar_kind[i] == "chorus":
            kind[i] = "chorus"
    for s0, *_ in secs[1:]:
        kind[min(range(n), key=lambda j: abs(bars[j] - s0))] = "sweep"
    if n >= 6:
        kind[n - 2] = kind[n - 1] = "outro"

    pool_run = []

    def flush_pool():
        for k in range(0, len(pool_run), 2):
            chunk = pool_run[k:k + 2]
            for h in range(8):
                put(h, bars[chunk[0]], bars[chunk[-1] + 1], fan(h) * 12, fan(h) * 12, FADE_UP_DOWN)
        pool_run.clear()

    count = 0
    for i in range(n):
        if kind[i] == "pool":
            if pool_run and pool_run[-1] != i - 1:
                flush_pool()
            pool_run.append(i)
            continue
        flush_pool()
        s, e = bars[i], bars[i + 1]
        if kind[i] == "sweep":  # outside to inside over the bar
            for h in range(8):
                put(h, s, e, fan(h) * 55, fan(h) * 10, SWEEP_DIM)
        elif kind[i] == "chorus":
            q = [s + (e - s) * k // 4 for k in range(5)]
            for k in range(4):
                if k == 0 and bar_peak[i]:
                    for h in range(8):
                        put(h, q[0], min(q[0] + 500, q[1]), 0, 0, BURST_DIM)
                    continue
                swing = 18 if (i + k) % 2 == 0 else -18
                for h in range(8):
                    if h % 2 == k % 2:  # heads 1,3,5,7 on beats 1,3; heads 2,4,6,8 on beats 2,4
                        put(h, q[k], q[k + 1], fan(h) * 20 - swing, fan(h) * 20 + swing, PING_DIM)
        elif kind[i] == "outro" and kind[i - 1] != "outro":
            for h in range(8):
                put(h, s, bars[i + 2], fan(h) * 40, 0, OUTRO_DIM)
        count += 1
    flush_pool()
    # Before every beam, a dark pan/tilt-only effect with "link to next effect" moves the head to the beam's start pose
    # (the motors are slow: otherwise the beam would appear while the head is still swinging in from its last pose).
    pre = 0
    for h, effs in enumerate(plan):
        cursor, tilt = 0, 0.0  # rest pose: pan 90, tilt 0 (straight up)
        for start, end, t0, t1, dimmer in sorted(effs):
            if start - cursor >= 25:
                emit(h, max(cursor, start - MH_PRE_MS), start, tilt, t0, "", link=True)
                pre += 1
            emit(h, start, end, t0, t1, dimmer)
            cursor, tilt = end, t1
    print(f"moving heads: {count} non-pool bars, 8 heads, white, {pre} pre-position effects")


def order_rows(sq: Seq, show_dir: Path) -> None:
    """Master view order: model groups first, then models, each alphabetical. Timing rows keep their slots."""
    groups = {g.get("name") for g in ET.parse(show_dir / "xlights_rgbeffects.xml").getroot().iter("modelGroup")}

    def key(e):
        name = e.get("name", "")
        return (name not in groups, name.lower())

    for parent in (sq.disp, sq.eff):
        children = list(parent)
        ordered = iter(sorted((c for c in children if c.get("type") == "model"), key=key))
        rebuilt = [next(ordered) if c.get("type") == "model" else c for c in children]
        for c in children:
            parent.remove(c)
        parent.extend(rebuilt)
    print(f"row order: {sum(1 for e in sq.disp if e.get('type') == 'model' and e.get('name') in groups)} groups first, then models A-Z")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xsq")
    ap.add_argument("--mp3")
    ap.add_argument("--palettes", help='JSON overriding the colour story: {"chorusA": {"trees": ["#hex", "#hex"]}, '
                    '"sparkle": {"chorusA": "#hex"}}; only the roles given are replaced')
    ap.add_argument("--artist", default="Eclipse 6", help="artist shown in the radio's now-playing text")
    ap.add_argument("--video", help="video file path as the show folder sees it (e.g. Videos/Name.mp4) to play on --video-model")
    ap.add_argument("--video-model", default="Matrix", help="matrix that plays --video instead of the Mega Tree effects")
    ap.add_argument("--video-crop", type=int, default=0, help="percent of the video height cropped from the top and from the bottom (fits 16:9 on a 2:1 matrix)")
    ap.add_argument("--video-crop-x", type=int, default=0, help="percent of the video width cropped from the left and from the right (fits 16:9 on a 4:3 matrix: 12)")
    ap.add_argument("--no-lyrics", action="store_true", help="leave the Lyrics Matrix blank")
    ap.add_argument("--no-radio", action="store_true", help="leave the Radio_EFL model blank")
    ap.add_argument("--no-heads", action="store_true", help="leave the moving heads (MH-1..MH-8) blank")
    args = ap.parse_args()
    if args.palettes:
        over = json.load(open(args.palettes, encoding="utf-8"))
        SPARKLE_COLOR.update(over.pop("sparkle", {}))
        for key, roles in over.items():
            PALETTES[key].update({role: tuple(cols) for role, cols in roles.items()})
    xsq = Path(args.xsq)
    mp3 = Path(args.mp3) if args.mp3 else xsq.with_suffix(".mp3")

    beats = detect_beats(mp3)
    parts = detect_structure(mp3)
    secs = section_plan(parts, None)
    dur = int(float(ET.parse(xsq).getroot().findtext("head/sequenceDuration")) * 1000)
    bars = [int(t * 1000) for t in beats.downbeat_times]
    # a song that opens before the first detected downbeat (intro, count-in): extend the bar grid back to 0
    if len(bars) > 1 and bars[0] > 0:
        period = bars[1] - bars[0]
        lead = []
        t = bars[0] - period
        while t > 0:
            lead.append(t)
            t -= period
        bars = [0] + lead[::-1] + bars
    bars.append(min(dur, bars[-1] + (bars[-1] - bars[-2])))
    print(f"{beats.tempo:.0f} BPM, {len(bars) - 1} bars, {len(secs)} sections")

    bak = xsq.with_suffix(".xsq.bak")
    if not bak.exists():
        shutil.copy2(xsq, bak)
    sq = Seq(xsq)
    shader_dir = (xsq.parent / "Shaders").resolve().as_posix()

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
        for m in TREE_LIKE:
            sq.add(m, 1, "VU Meter", bars[b0], bars[b1 + 1],
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
            shock = SHOCK.format(r=160 if bar_peak[i] else 100)
            if m == "Stars":  # group: each star gets its own shockwave rather than one across the group
                shock = "B_CHOICE_BufferStyle=Per Model Default," + shock
            sq.add(m, 0, "Shockwave", bars[i], end, shock, pk)
    # Mini trees and their tops ping-pong in chorus bars: Trees on beats 1 and 3, Trees Stars on beats 2 and 4
    for i in range(n):
        if bar_kind[i] != "chorus":
            continue
        q = [bars[i] + (bars[i + 1] - bars[i]) * k // 4 for k in range(5)]
        r = 160 if bar_peak[i] else 100
        shock = "B_CHOICE_BufferStyle=Per Model Default," + SHOCK.format(r=r)
        for k in range(4):
            for model in (TREE_LIKE if k % 2 == 0 else ("Trees Stars",)):
                sq.add(model, 0, "Shockwave", q[k], min(q[k] + 450, q[k + 1]), shock, bar_pal[i])
    # Trees Stars are lit all song: slow Ripple per bar outside choruses (layer 1), Pinwheel under each chorus run
    # (layer 2), and a full-size Shockwave on the first beat of every section (layer 0, with the chorus ping-pong)
    ts_shock = "B_CHOICE_BufferStyle=Per Model Default," + SHOCK.format(r=160)
    starts = sorted({min(range(n), key=lambda j: abs(bars[j] - s0)) for s0, *_ in secs})
    for i in starts:
        q1 = bars[i] + (bars[i + 1] - bars[i]) // 4
        sq.add("Trees Stars", 0, "Shockwave", bars[i], min(bars[i] + 450, q1), ts_shock, bar_pal[i])
    for i in range(n):
        if bar_kind[i] != "chorus":
            sq.add("Trees Stars", 1, "Ripple", bars[i], bars[i + 1], "B_CHOICE_BufferStyle=Per Model Default," + RIPPLE, bar_pal[i])
    i = 0
    while i < n:
        if bar_kind[i] != "chorus":
            i += 1
            continue
        j = i
        while j + 1 < n and bar_kind[j + 1] == "chorus" and bar_pal[j + 1] == bar_pal[i] and j + 1 - i < 16:
            j += 1
        sq.add("Trees Stars", 2, "Pinwheel", bars[i], bars[j + 1], "B_CHOICE_BufferStyle=Per Model Default," + PINWHEEL, bar_pal[i])
        i = j + 1
    # Mega Tree: Aurora shader (palette-masked) with a one-colour On (Average blend) on top. Both change
    # only when the Trees VU meter does, and the tint is the Trees' first colour so the two trees match.
    used = collections.Counter()
    # shader "peak" = only the song's loudest choruses (the absolute 0.9 cut-off marks most choruses on some songs)
    top = 0.97 * max([x[3] for x in secs if x[2] == "chorus"] or [1.0])
    for b0, b1, pk in tree_blocks:
        story = "peak" if bar_kind[b0] == "chorus" and sec_at(bars[b0])[3] >= top else pk
        pick = SHADER_PICK[story]
        shader = pick[used[story] % len(pick)]
        used[story] += 1
        for m in MEGA_TREE_LIKE:  # the two matrices carry the same look as the Mega Tree
            if m == args.video_model and args.video:
                continue  # that matrix plays the video instead
            sq.add(m, 1, "Shader", bars[b0], bars[b1 + 1], shader_settings(shader, shader_dir), pk, role=ROLE["Mega Tree"])
            sq.add(m, 0, "On", bars[b0], bars[b1 + 1], ON_TINT, pk, role="treetint")
    # Icicles: wash per 2 bars, FloodLights: wash per section
    for i in range(0, n, 2):
        sq.add("Icicles", 0, "On", bars[i], bars[min(i + 2, n)], ON, bar_pal[i])
    for s0, s1, kind, _ in secs:
        idx = [i for i in range(n) if s0 <= bars[i] < s1]
        if idx:
            sq.add("FloodLights", 0, "On", bars[idx[0]], bars[idx[-1] + 1], ON, bar_pal[idx[0]])

    if args.video:
        sq.add(args.video_model, 0, "Video", 0, dur, VIDEO.format(f=args.video, ct=100 - args.video_crop, cb=args.video_crop,
                                                                   cl=args.video_crop_x, cr=100 - args.video_crop_x), "verse", "text")
        print(f"video: {args.video} on {args.video_model} (crop {args.video_crop}% top/bottom, {args.video_crop_x}% left/right)")
    if not args.no_lyrics:
        add_lyric_words(sq, tree_blocks, bars)
    if not args.no_radio:
        add_radio(sq, bars, bar_kind, bar_peak, bar_pal, tree_blocks, ET.parse(xsq).getroot().findtext("head/song") or xsq.stem, dur, args.artist)
    if not args.no_heads:
        add_moving_heads(sq, bars, bar_kind, bar_peak, secs)

    # hide model/group rows with no effects (timing rows stay as they are)
    used = {e.get("name") for e in sq.eff if e.get("type") == "model" and e.findall(".//Effect")}
    hidden = 0
    for e in sq.disp:
        if e.get("type") == "model" and e.get("name") not in used and e.get("visible") != "0":
            e.set("visible", "0")
            hidden += 1
    print(f"hid {hidden} unused rows, {len(used)} visible")
    add_grid_tracks(sq.disp, sq.eff, bars, parts)    # Beats / Bars / Song Parts timing tracks of this grid
    order_rows(sq, xsq.parent)
    # sequences were cut at the last lyric; stretch to the audio so the outro isn't clipped
    sq.root.find("head/sequenceDuration").text = f"{max(dur, secs[-1][1]) / 1000:.3f}"
    ET.indent(sq.tree, space="  ")
    sq.tree.write(xsq, encoding="utf-8", xml_declaration=True)
    print("updated", xsq, "| palettes:", len(sq.pals), "| effect defs:", len(sq.db))


if __name__ == "__main__":
    main()
