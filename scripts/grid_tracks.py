"""Beats / Bars / Song Parts timing tracks from the grid enhance_layout.py sequences to.

enhance_layout.py already finds the bars (beats = each bar split in 4) and the song's parts from the
sound, then used to throw them away. Writing them as timing tracks (as SequenceStarter does) lets the
user see and reuse the grid in xLights, and gives songs without a Genius page (parodies) a parts track.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

PART_NAMES = {"intro": "Intro", "verse": "Verse", "chorus": "Chorus", "bridge": "Bridge", "outro": "Outro",
              "transition": "Transition", "instrumental": "Instrumental"}


def _track(disp, eff, name: str, rows: list[tuple[str, int, int]]) -> None:
    """Replace timing track `name` with one layer of (label, start ms, end ms), after the last timing row."""
    for parent in (disp, eff):
        for el in [e for e in parent if e.get("type") == "timing" and e.get("name") == name]:
            parent.remove(el)
    for parent, attrs in ((disp, {"collapsed": "0", "type": "timing", "name": name, "visible": "1", "active": "0"}),
                          (eff, {"type": "timing", "name": name})):
        idx = max((i for i, e in enumerate(parent) if e.get("type") == "timing"), default=-1) + 1
        el = ET.Element("Element", attrs)
        if parent is eff:
            layer = ET.SubElement(el, "EffectLayer")
            for label, s, e in rows:
                if e > s:
                    ET.SubElement(layer, "Effect", {"label": label, "startTime": str(s), "endTime": str(e)})
        parent.insert(idx, el)


def add_grid_tracks(disp, eff, bars: list[int], sections) -> None:
    """bars: bar start times in ms with the song end appended; sections: detect_structure() results."""
    beats, bar_rows = [], []
    for i in range(len(bars) - 1):
        bar_rows.append((str(i + 1), bars[i], bars[i + 1]))
        q = [bars[i] + (bars[i + 1] - bars[i]) * k // 4 for k in range(5)]
        beats += [(str(k + 1), q[k], q[k + 1]) for k in range(4)]
    merged: list[list] = []     # detection cuts long stretches into runs (Chorus 3..8): one part per run
    for s in sections:
        name = PART_NAMES.get(s.label, s.label.title())
        if merged and merged[-1][0] == name:
            merged[-1][2] = int(s.end_time * 1000)
        else:
            merged.append([name, int(s.start_time * 1000), int(s.end_time * 1000)])
    counts: dict[str, int] = {}
    parts = []
    for name, s, e in merged:
        counts[name] = counts.get(name, 0) + 1
        parts.append((f"{name} {counts[name]}", s, e))
    _track(disp, eff, "Beats", beats)
    _track(disp, eff, "Bars", bar_rows)
    _track(disp, eff, "Song Parts", parts)
