"""Put the skeleton band (band_shader.py) on matrix models of an .xsq, one Shader effect per bar.

For each bar the placer works out which 16th-note slots have a kick and which have a
sung vowel and passes them to the shader as 16-bit masks:
  * kicks: a "Kick Hits" timing track if the sequence has one, else drum hits found in
    the song's audio (audio.drums.drum_accents), else beats 1 and 3;
  * singing: the phoneme layer of a lyrics track (jaw open on vowels, shut on M/B/P,
    F/V and rests), else its word layer, else an "Onsets (vocals)" track.
Like the dance crew it skips matrices showing a Video, steps aside while the matrix
shows its own pictures, and can take colours (and "off") per section.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from xlights_mcp.sprites import dancers as d
from xlights_mcp.sprites.band import SLOTS_PER_BEAT
from xlights_mcp.sprites.band_shader import SHADER_NAME, band_settings, build_shader
from xlights_mcp.sprites.place import (MIN_PIECE_BEATS, Xsq, busy_spans, free_pieces, group_bars, model_size,
                                       read_beats, section_key)

OPEN_PHONEMES = {"AI", "E", "O", "U", "WQ", "L", "etc"}
SLOTS = 16


@dataclass
class BandPlacement:
    model: str
    effects: int
    kick_source: str
    vocal_source: str
    skipped: str | None = None


def _timing(root: ET.Element, name: str) -> list[ET.Element] | None:
    for e in root.find("ElementEffects"):
        if e.get("type") == "timing" and e.get("name") == name:
            return e.findall("EffectLayer")
    return None


def kick_times(root: ET.Element, media: Path | None, beats) -> tuple[list[int], str]:
    layers = _timing(root, "Kick Hits")
    if layers:
        return [int(x.get("startTime")) for x in layers[0].findall("Effect")], "Kick Hits track"
    if media is not None and media.exists():
        from xlights_mcp.audio.drums import drum_accents
        return [t for t, _ in drum_accents(media)], "drum hits found in the audio"
    return [s for s, _, lab in beats if lab in ("1", "3")], "beats 1 and 3"


def vocal_spans(root: ET.Element) -> tuple[list[tuple[int, int]], str]:
    """Time spans when the singer's mouth is open."""
    names = [e.get("name") for e in root.find("ElementEffects") if e.get("type") == "timing"]
    lyric = sorted((n for n in names if n.lower().startswith("lyrics")), key=lambda n: (n != "Lyrics", n))
    for n in lyric:
        layers = _timing(root, n)
        if len(layers) >= 3 and layers[2].findall("Effect"):
            return ([(int(x.get("startTime")), int(x.get("endTime"))) for x in layers[2].findall("Effect")
                     if (x.get("label") or "") in OPEN_PHONEMES], f"phonemes of '{n}'")
    for n in lyric:
        layers = _timing(root, n)
        if len(layers) >= 2 and layers[1].findall("Effect"):
            return [(int(x.get("startTime")), int(x.get("endTime"))) for x in layers[1].findall("Effect")], \
                f"words of '{n}'"
    layers = _timing(root, "Onsets (vocals)")
    if layers:
        return [(int(x.get("startTime")), int(x.get("startTime")) + 120) for x in layers[0].findall("Effect")], \
            "vocal onsets"
    return [], "none (mouth closed)"


def slot_masks(t0: int, t1: int, nbeats: int, kicks: list[int], vocals: list[tuple[int, int]]) -> tuple[int, int]:
    """16-bit masks of the bar's 16th-note slots (spread evenly over the bar, as the shader does) with a kick
    starting in them, and with the mouth open at their middle."""
    per = (t1 - t0) / max(nbeats * SLOTS_PER_BEAT, 1)
    kick = vocal = 0
    for s in range(min(SLOTS, nbeats * SLOTS_PER_BEAT)):
        a, b = t0 + s * per, t0 + (s + 1) * per
        if any(a <= k < b for k in kicks):
            kick |= 1 << s
        mid = (a + b) / 2
        if any(va <= mid < vb for va, vb in vocals):
            vocal |= 1 << s
    return kick, vocal


def place_band(xsq: Path, show: Path, models: list[str], figure: str = "male", shirts: list[str] | None = None,
               stage: bool = False, energy: float = 1.0, track: str = "Beats", section_track: str | None = None,
               section_shirts: dict[str, list[str]] | None = None, off_sections: list[str] | None = None,
               over_video: bool = False, over_pictures: bool = False,
               media: Path | None = None) -> list[BandPlacement]:
    """off_sections: label prefixes (lower case) of sections with no band, e.g. ["ending"]."""
    d.crew_from_style(3, figure=figure)                       # unknown figure fails before writing
    sq = Xsq(xsq)
    beats = read_beats(sq.root, track)
    bars = group_bars(beats)
    if not bars:
        raise ValueError("no bars in the Beats track")
    sections = read_beats(sq.root, section_track) if section_track else []
    section_shirts = section_shirts or {}
    off = [o.lower() for o in (off_sections or [])]
    if media is None:
        mf = sq.root.findtext("head/mediaFile")
        media = Path(mf) if mf else None
    kicks, ksrc = kick_times(sq.root, media, beats)
    vocals, vsrc = vocal_spans(sq.root)
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
            out.append(BandPlacement(name, 0, ksrc, vsrc, skipped="has a Video effect"))
            continue
        el = sq.model(name, add=True)
        sq.strip_old(el, SHADER_NAME, gifs=False)
        busy = [] if over_pictures else busy_spans(el)
        layer = ET.Element("EffectLayer")
        count = 0
        for bar in bars:
            t0, t1 = bar[0][0], bar[-1][1]
            label = next((lab for s, e, lab in sections if s <= t0 < e), None)
            if label is not None and section_key(label, off):
                continue
            sh = shirts
            if label is not None:
                k = section_key(label, section_shirts)
                if k:
                    sh = section_shirts[k]
            cols = [d.colour(c) for c in (sh or ["purple", "red", "teal"])]
            cols = (cols * 3)[:3]
            kick, vocal = slot_masks(t0, t1, len(bar), kicks, vocals)
            per_ms = len(bar) / max(t1 - t0, 1)
            for a, b in free_pieces(t0, t1, busy):
                nb = (b - a) * per_ms
                if nb < MIN_PIECE_BEATS:
                    continue
                st = band_settings(path.as_posix(), figure, kick, vocal, (a - t0) * per_ms, nb, energy, stage)
                ET.SubElement(layer, "Effect", {
                    "ref": str(sq.ref(",".join(f"{k}={v}" for k, v in sorted(st.items())))), "name": "Shader",
                    "startTime": str(a), "endTime": str(b), "palette": str(sq.palette_ref(cols))})
                count += 1
        el.insert(0, layer)
        out.append(BandPlacement(name, count, ksrc, vsrc))
    sq.save()
    return out
