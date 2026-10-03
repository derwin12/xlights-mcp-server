"""Generate a "Prop Test" .xsq that exercises every prop in a show folder.

Usage:
    python scripts/prop_test_sequence.py [--show F:/ShowFolderQA] [--out "Prop Test.xsq"]
                                          [--only-model NAME ...]

Phases (each has its own labelled timing track so you can read what is lit):
    1 Layout L->R   models chase across the house sorted by layout X position
    2 Port order    one model at a time, ordered controller -> port -> start channel,
                    one colour per controller (wrong prop lighting = wrong port)
    3 Node order    a first->last node chase on each model (wiring direction)
    4 States        every state of every model that defines states
    5 Submodels     first / middle / last submodel of each model
    6 Groups        each model group solid in turn; label flags empty groups and
                    members that don't resolve to a model, group or submodel

DMX, Image and no-controller models are skipped (On-style colour effects are
meaningless or unsafe on them).
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from xlights_mcp.xlights.palettes import ColorPalette

COLORS = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#00FFFF", "#FF00FF", "#FF8000", "#FFFFFF"]
SKIP_TYPES = {"Image", "DmxMovingHeadAdv", "DmxMovingHead", "DmxGeneral", "DmxServo", "DmxFloodlight"}

ON = "E_TEXTCTRL_Eff_On_Start=100,E_TEXTCTRL_Eff_On_End=100"
CHASE = (
    "E_NOTEBOOK_SSEFFECT_TYPE=Chase,E_CHOICE_Chase_Type1=Left-Right,"
    "E_SLIDER_Number_Chases=1,E_SLIDER_Color_Mix1=10,E_CHECKBOX_Chase_3dFade1=0,"
    "E_CHECKBOX_Chase_Group_All=0,E_SLIDER_Chase_Rotations=10"
)


@dataclass
class Plan:
    effects: list = field(default_factory=list)  # (element, sublayer|None, name, start, end, settings, colors)
    tracks: dict = field(default_factory=dict)  # track name -> [(label, start, end)]
    t: int = 0

    def label(self, track, text, start, end):
        self.tracks.setdefault(track, []).append((text, start, end))

    def add(self, element, name, start, end, settings, colors, sub=None):
        self.effects.append((element, sub, name, start, end, settings, colors))


def _int(v, d=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return d


def load_models(root):
    out = []
    for m in root.find("models").findall("model"):
        cc = m.find("ControllerConnection")
        ctrl = m.get("Controller") or ""
        sc = m.get("StartChannel", "")
        out.append({
            "name": m.get("name"),
            "type": m.get("DisplayAs", ""),
            "ctrl": ctrl,
            "port": _int(cc.get("Port")) if cc is not None else 0,
            "start": _int(re.sub(r"^.*:", "", sc)) if sc else 0,
            "x": float(m.get("WorldPosX", 0) or 0),
            "subs": [s.get("name") for s in m.findall("subModel")],
            "states": [s for s in m.findall("stateInfo")],
        })
    return out


def testable(m):
    return m["type"] not in SKIP_TYPES and m["ctrl"] not in ("", "No Controller")


def build(root, only=None):
    models = [m for m in load_models(root) if testable(m)]
    if only:
        models = [m for m in models if m["name"] in only]
    p = Plan()
    t = 0

    # 1. layout left -> right: colour fades red -> blue by X position
    xs = sorted(models, key=lambda m: m["x"])
    lo, hi = xs[0]["x"], xs[-1]["x"]
    step = 250
    for m in xs:
        f = (m["x"] - lo) / (hi - lo) if hi > lo else 0
        col = "#%02X00%02X" % (round(255 * (1 - f)), round(255 * f))
        p.add(m["name"], "On", t, t + step * 2, ON, [col])
        p.label("1 Layout L-R", m["name"], t, t + step)
        t += step
    t += step * 2 + 1000

    # 2. port order
    ordered = sorted(models, key=lambda m: (m["ctrl"], m["port"], m["start"], m["name"]))
    ctrl_color = {}
    for m in ordered:
        col = ctrl_color.setdefault(m["ctrl"], COLORS[len(ctrl_color) % len(COLORS)])
        p.add(m["name"], "On", t, t + 1000, ON, [col])
        p.label("2 Port order", f'{m["ctrl"]} P{m["port"]} {m["name"]}', t, t + 1000)
        t += 1000
    t += 1000

    # 3. node order first -> last
    for m in ordered:
        p.add(m["name"], "SingleStrand", t, t + 2000, CHASE, ["#FF0000", "#0000FF"])
        p.label("3 Node order", f'{m["ctrl"]} P{m["port"]} {m["name"]}', t, t + 2000)
        t += 2000
    t += 1000

    # 4. states
    for m in models:
        for si in m["states"]:
            defn = si.get("Name", "")
            names = [v for k, v in si.attrib.items() if re.fullmatch(r"s\d+-Name", k)]
            if not names:  # Type=SingleNode etc: states are the s### keys themselves
                names = [k for k in si.attrib if re.fullmatch(r"s\d+", k)]
            for sn in names:
                st = ("E_CHOICE_State_Color=Graduate,E_CHOICE_State_StateDefinition=%s,"
                      "E_CHOICE_State_State=%s,E_SLIDER_State_Fade_Time=0" % (defn, sn))
                p.add(m["name"], "State", t, t + 1500, st, ["#FFFFFF"])
                p.label("4 States", f'{m["name"]} [{defn}] {sn}', t, t + 1500)
                t += 1500
    t += 1000

    # 5. submodels: first / middle / last
    for m in models:
        subs = m["subs"]
        if not subs:
            continue
        picks = [subs[0], subs[len(subs) // 2], subs[-1]]
        picks = list(dict.fromkeys(picks))
        for i, sn in enumerate(picks):
            p.add(m["name"], "On", t, t + 1000, ON, [COLORS[i % len(COLORS)]], sub=sn)
            p.label("5 Submodels", f'{m["name"]}/{sn} ({subs.index(sn) + 1} of {len(subs)})', t, t + 1000)
            t += 1000
    t += 1000

    # 6. groups
    names = {m["name"] for m in load_models(root)}
    group_names = {g.get("name") for g in root.iter("modelGroup")}
    subnames = {f"{m['name']}/{s}" for m in load_models(root) for s in m["subs"]}
    for i, g in enumerate(root.iter("modelGroup")):
        gm = [x for x in (g.get("models") or "").split(",") if x]
        missing = [x for x in gm if x not in names | group_names | subnames]
        tag = ""
        if not gm:
            tag = " EMPTY GROUP"
        elif missing:
            tag = f" MISSING {len(missing)}: " + "; ".join(missing[:3])
        if gm:
            p.add(g.get("name"), "On", t, t + 1500, ON, [COLORS[i % len(COLORS)]])
        p.label("6 Groups", f'{g.get("name")} ({len(gm)}){tag}', t, t + 1500)
        t += 1500
    return p, t


def write(p, total_ms, out):
    root = ET.Element("xsequence", BaseChannel="0", ChanCtrlBasic="0", ChanCtrlColor="0",
                      FixedPointTiming="1", ModelBlending="true")
    head = ET.SubElement(root, "head")
    for k, v in [("version", "2025.13"), ("author", ""), ("song", "Prop Test"),
                 ("comment", "Generated by xLights MCP Server prop_test_sequence.py"),
                 ("sequenceTiming", "25 ms"), ("sequenceType", "Animation"),
                 ("mediaFile", ""), ("sequenceDuration", f"{total_ms / 1000:.3f}")]:
        ET.SubElement(head, k).text = v
    ET.SubElement(head, "imageDir")
    ET.SubElement(root, "nextid").text = "1"
    ET.SubElement(root, "Jukebox")

    pal_strs, eff_strs = [], []
    for _, _, _, _, _, st, cols in p.effects:
        ps = ColorPalette(colors=cols, active_colors=list(range(1, len(cols) + 1))).to_xlights_string()
        if ps not in pal_strs:
            pal_strs.append(ps)
        if st not in eff_strs:
            eff_strs.append(st)
    pals = ET.SubElement(root, "ColorPalettes")
    for s in pal_strs:
        ET.SubElement(pals, "ColorPalette").text = s
    db = ET.SubElement(root, "EffectDB")
    for s in eff_strs:
        ET.SubElement(db, "Effect").text = s
    dl = ET.SubElement(ET.SubElement(root, "DataLayers"), "DataLayer")
    dl.set("name", "Nutcracker"); dl.set("source", "1")

    by_el = {}
    for e in p.effects:
        by_el.setdefault(e[0], []).append(e)
    disp = ET.SubElement(root, "DisplayElements")
    for n in sorted(by_el):
        ET.SubElement(disp, "Element", collapsed="0", type="model", name=n, visible="1", active="0")
    for tn in sorted(p.tracks):
        ET.SubElement(disp, "Element", collapsed="0", type="timing", name=tn, visible="1", active="0")

    ee = ET.SubElement(root, "ElementEffects")
    for n in sorted(by_el):
        el = ET.SubElement(ee, "Element", type="model", name=n)
        main = ET.SubElement(el, "EffectLayer")
        subs = {}
        for _, sub, name, s, e, st, cols in by_el[n]:
            ps = ColorPalette(colors=cols, active_colors=list(range(1, len(cols) + 1))).to_xlights_string()
            layer = main if sub is None else subs.setdefault(sub, ET.Element("SubModelEffectLayer", name=sub))
            ET.SubElement(layer, "Effect", ref=str(eff_strs.index(st)), name=name,
                          startTime=str(s), endTime=str(e), palette=str(pal_strs.index(ps)))
        for layer in subs.values():
            el.append(layer)
    for tn in sorted(p.tracks):
        te = ET.SubElement(ee, "Element", type="timing", name=tn)
        lay = ET.SubElement(te, "EffectLayer")
        for text, s, e in p.tracks[tn]:
            ET.SubElement(lay, "Effect", label=text, startTime=str(s), endTime=str(e))
    ET.SubElement(root, "lastView").text = "0"
    ET.SubElement(root, "TimingTags")
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    with open(out, "w", encoding="UTF-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(f, encoding="unicode", xml_declaration=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", default="F:/ShowFolderQA")
    ap.add_argument("--out", default="Prop Test.xsq")
    ap.add_argument("--only-model", nargs="*")
    a = ap.parse_args()
    show = Path(a.show)
    root = ET.parse(show / "xlights_rgbeffects.xml").getroot()
    plan, total = build(root, set(a.only_model) if a.only_model else None)
    out = Path(a.out)
    if not out.is_absolute():
        out = show / out
    write(plan, total, out)
    print(f"{out}: {len(plan.effects)} effects, {total / 60000:.1f} min")
    for tn in sorted(plan.tracks):
        print(f"  {tn}: {len(plan.tracks[tn])} steps")


if __name__ == "__main__":
    main()
