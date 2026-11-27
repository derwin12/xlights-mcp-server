"""Add Lyrics / Beats / Bars timing tracks to a sequence from transcribe_words.py words and a beat list.

Usage (from scripts/):
    python add_timing_tracks.py SONG.xsq --words stories/lyrics/NAME.json --beats stories/lyrics/NAME_beats.json
        [--every 2] [--out OUT.xsq] [--replace]

Lyrics is the usual xLights three-layer track (phrases, words, phonemes; phonemes from CMUdict when it is
installed, else left for xLights' "Breakdown Words"). Beats are labelled 1-2-3-4 and Bars 1, 2, 3... from the
first beat. --every 2 keeps every other beat, for slow songs where librosa locks onto double time. Existing
tracks with the same names are kept unless --replace. matrix_storybook.Timing / matrix_scenes Cues.from_xsq read
these names, so later stories can time from the sequence itself.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def _phonemes(word: str) -> list[tuple[str, int]]:
    try:
        from song_to_singing_props import word_phonemes
        return word_phonemes(word)
    except Exception:
        return []


def _insert(disp, eff, name: str, layers: list[list[tuple[str, int, int]]], replace: bool) -> bool:
    if any(e.get("type") == "timing" and e.get("name") == name for e in eff):
        if not replace:
            print(f"  {name}: already there, kept")
            return False
        for parent in (disp, eff):
            for el in [e for e in parent if e.get("type") == "timing" and e.get("name") == name]:
                parent.remove(el)
    for parent, attrs in ((disp, {"collapsed": "0", "type": "timing", "name": name, "visible": "1", "active": "0"}),
                          (eff, {"type": "timing", "name": name})):
        idx = max((i for i, e in enumerate(parent) if e.get("type") == "timing"), default=-1) + 1
        el = ET.Element("Element", attrs)
        if parent is eff:
            for rows in layers:
                layer = ET.SubElement(el, "EffectLayer")
                for label, s, e in rows:
                    if e > s:
                        ET.SubElement(layer, "Effect", {"label": label, "startTime": str(s), "endTime": str(e)})
        parent.insert(idx, el)
    print(f"  {name}: " + ", ".join(str(len(r)) for r in layers))
    return True


def lyric_layers(phrases: list[dict]) -> list[list[tuple[str, int, int]]]:
    ph, wd, pn = [], [], []
    prev = 0
    for p in phrases:
        ps, pe = max(int(p["start"] * 1000), prev), int(p["end"] * 1000)
        if pe <= ps:
            continue
        ph.append((p["text"].strip(), ps, pe))
        for w in p["words"]:
            ws, we = max(int(w["s"] * 1000), prev), int(w["e"] * 1000)
            ws, we = max(ws, ps), min(we, pe)
            if we <= ws:
                continue
            label = w["w"].strip()
            wd.append((label, ws, we))
            phs = _phonemes(label)
            total = sum(wt for _, wt in phs) or 1
            t = ws
            for i, (code, wt) in enumerate(phs):
                end = we if i == len(phs) - 1 else min(we, t + max(25, (we - ws) * wt // total))
                if end > t:
                    pn.append((code, t, end))
                t = end
            prev = we
        prev = max(prev, pe)
    return [ph, wd, pn]


def beat_layers(beats: list[float], duration_ms: int) -> tuple[list, list]:
    ms = [int(round(b * 1000 / 25)) * 25 for b in beats]
    ms = sorted(set(ms))
    nxt = ms[1:] + [min(duration_ms, ms[-1] + (ms[-1] - ms[-2] if len(ms) > 1 else 500))]
    beat_rows = [(str(i % 4 + 1), s, e) for i, (s, e) in enumerate(zip(ms, nxt))]
    bar_ms = ms[::4]
    bar_nxt = bar_ms[1:] + [nxt[-1]]
    bar_rows = [(str(i + 1), s, e) for i, (s, e) in enumerate(zip(bar_ms, bar_nxt))]
    return beat_rows, bar_rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("xsq", type=Path)
    ap.add_argument("--words", type=Path)
    ap.add_argument("--beats", type=Path)
    ap.add_argument("--every", type=int, default=1, help="keep every Nth beat (2 for double-time detections)")
    ap.add_argument("--out", type=Path, help="default: rewrite the input (back it up first)")
    ap.add_argument("--replace", action="store_true", help="replace existing Lyrics/Beats/Bars tracks")
    a = ap.parse_args()
    tree = ET.parse(a.xsq)
    root = tree.getroot()
    disp, eff = root.find("DisplayElements"), root.find("ElementEffects")
    dur = int(float(root.findtext("head/sequenceDuration") or 0) * 1000)
    print(a.xsq.name)
    if a.words:
        _insert(disp, eff, "Lyrics", lyric_layers(json.loads(a.words.read_text())), a.replace)
    if a.beats:
        beats = json.loads(a.beats.read_text())[::a.every]
        beat_rows, bar_rows = beat_layers(beats, dur)
        _insert(disp, eff, "Beats", [beat_rows], a.replace)
        _insert(disp, eff, "Bars", [bar_rows], a.replace)
    out = a.out or a.xsq
    ET.indent(tree, space="    ")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(fh, encoding="unicode", xml_declaration=False)
    ET.parse(out)


if __name__ == "__main__":
    main()
