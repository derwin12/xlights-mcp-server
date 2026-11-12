"""Put Sky Shooter (shooter_shader.py) on matrix models of an .xsq, one Shader effect per bar.

The game is played out first (shooter.simulate) over the bars it is shown in, using the same
kick sources as the skeleton band (Kick Hits track, else drum hits in the audio, else
beats 1 and 3), so every bar's effect starts from the right wave and survivors.
Like the dancers and the band it skips matrices with a Video, steps aside for the
matrix's own pictures, and takes colours (and "off") per section.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from xlights_mcp.sprites import dancers as d
from xlights_mcp.sprites import shooter as g
from xlights_mcp.sprites.band_place import kick_times, slot_masks
from xlights_mcp.sprites.place import (MIN_PIECE_BEATS, Xsq, busy_spans, free_pieces, group_bars, model_size,
                                       read_beats, section_key)
from xlights_mcp.sprites.shooter_shader import SHADER_NAME, build_shader, shooter_settings

DEFAULT_COLOURS = ["#DC1E28", "#1EC850", "#2878FF"]      # Christmas red, green, blue ornaments


@dataclass
class ShooterPlacement:
    model: str
    effects: int
    waves: int
    kick_source: str
    skipped: str | None = None


def place_shooter(xsq: Path, show: Path, models: list[str], colours: list[str] | None = None,
                  energy: float = 1.0, track: str = "Beats", section_track: str | None = None,
                  section_colours: dict[str, list[str]] | None = None, off_sections: list[str] | None = None,
                  over_video: bool = False, over_pictures: bool = False,
                  media: Path | None = None, start_s: float = 0.0,
                  end_s: float | None = None) -> list[ShooterPlacement]:
    sq = Xsq(xsq)
    beats = read_beats(sq.root, track)
    bars = group_bars(beats)
    if not bars:
        raise ValueError("no bars in the Beats track")
    sections = read_beats(sq.root, section_track) if section_track else []
    section_colours = section_colours or {}
    off = [o.lower() for o in (off_sections or [])]
    for c in [*(colours or []), *(c for v in section_colours.values() for c in v)]:
        d.colour(c)
    if media is None:
        mf = sq.root.findtext("head/mediaFile")
        media = Path(mf) if mf else None
    kicks, ksrc = kick_times(sq.root, media, beats)
    labels = [next((lab for s, e, lab in sections if s <= b[0][0] < e), None) for b in bars]
    shown = [(b, lab) for b, lab in zip(bars, labels)
             if (lab is None or not section_key(lab, off)) and b[0][0] >= start_s * 1000
             and (end_s is None or b[-1][1] <= end_s * 1000)]
    if not shown:
        raise ValueError("no bars left to play in (sections off or the time range)")
    # the game is played over the bars it is shown in, so it starts with a fresh wave when it first appears
    masks = [slot_masks(b[0][0], b[-1][1], len(b), kicks, [])[0] for b, _ in shown]
    states = g.simulate(masks, [len(b) for b, _ in shown])
    path = show / "Shaders" / SHADER_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_shader(), encoding="utf-8")
    out = []
    for name in models:
        if model_size(show, name) is None:
            raise ValueError(f"{name}: not a Matrix model in the show's layout")
        el = sq.model(name)
        if not over_video and sq.has_video(el):
            if sq.strip_old(el, SHADER_NAME, gifs=False):
                sq.drop_if_empty(el)
            out.append(ShooterPlacement(name, 0, 0, ksrc, skipped="has a Video effect"))
            continue
        el = sq.model(name, add=True)
        sq.strip_old(el, SHADER_NAME, gifs=False)
        busy = [] if over_pictures else busy_spans(el)
        layer = ET.Element("EffectLayer")
        count = 0
        for (bar, label), st in zip(shown, states):
            t0, t1 = bar[0][0], bar[-1][1]
            cs = colours
            if label is not None:
                k = section_key(label, section_colours)
                if k:
                    cs = section_colours[k]
            cols = [d.colour(c) for c in (cs or DEFAULT_COLOURS)]
            cols = (cols * 3)[:3]
            per_ms = len(bar) / max(t1 - t0, 1)
            for a, b in free_pieces(t0, t1, busy):
                nb = (b - a) * per_ms
                if nb < MIN_PIECE_BEATS:
                    continue
                stt = shooter_settings(path.as_posix(), st, (a - t0) * per_ms, nb, energy)
                ET.SubElement(layer, "Effect", {
                    "ref": str(sq.ref(",".join(f"{k}={v}" for k, v in sorted(stt.items())))), "name": "Shader",
                    "startTime": str(a), "endTime": str(b), "palette": str(sq.palette_ref(cols))})
                count += 1
        el.insert(0, layer)
        out.append(ShooterPlacement(name, count, states[-1].wave + 1, ksrc))
    sq.save()
    return out
