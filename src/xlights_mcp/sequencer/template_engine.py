"""Template-based sequence generation.

Applies a style template (extracted from a real, human-made sequence) to a new
song and show layout. A template stores the structural rules of the source
sequence (roles, quantization, section grid) plus the actual xLights effect
settings strings and palettes it used, keyed by role:

  beat_pulse    — point props (stars, flakes, spinners): one pulse per beat,
                  alternating props on opposite beats (ping-pong)
  chase         — linear props (arches, canes, outlines): paired chase blocks
                  alternating per beat, in lockstep across all props
  hero_layered  — big pixel props (mega tree, matrices): layered composites
  global_accent — whole-display hits at section transitions

Templates live in sequencer/templates/*.json (see scripts that extracted
shockwave_beat_show.json from a vendor sequence).
"""

from __future__ import annotations

import bisect
import json
import logging
from pathlib import Path

from xlights_mcp.audio.analyzer import SongAnalysis
from xlights_mcp.xlights.models import LightModel, ShowConfig
from xlights_mcp.xlights.palettes import ColorPalette, get_theme_palettes
from xlights_mcp.xlights.xsq_writer import (
    EffectPlacement, SequenceSpec, TimingTrack, TimingTrackLabel, write_xsq,
)

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"

# Energy gates (match engine.py thresholds)
HIGH_ENERGY = 0.65
LOW_ENERGY = 0.35

# Effects that can't be reused from a template because they reference
# machine-local resources or sequence-specific content.
_SKIP_EFFECTS = {"Faces", "Text", "Video", "Shader", "Off"}


def list_templates() -> list[str]:
    """Names of available style templates."""
    if not TEMPLATES_DIR.exists():
        return []
    return sorted(p.stem for p in TEMPLATES_DIR.glob("*.json"))


def load_template(name: str) -> dict | None:
    path = TEMPLATES_DIR / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


# ---------------------------------------------------------------------------
# Parsing vendor settings/palette strings
# ---------------------------------------------------------------------------


def parse_settings_string(settings: str) -> dict[str, str]:
    """Parse an xLights EffectDB settings string into a settings dict.

    Tokens are comma-separated key=value pairs; a token without '=' is a
    comma that belonged to the previous value, so it is re-appended.
    """
    result: dict[str, str] = {}
    last_key: str | None = None
    for token in settings.split(","):
        if "=" in token:
            key, _, val = token.partition("=")
            result[key] = val
            last_key = key
        elif last_key is not None:
            result[last_key] += "," + token
    return result


def parse_palette_string(palette: str) -> ColorPalette:
    """Parse an xLights ColorPalette string into a ColorPalette."""
    fields = parse_settings_string(palette)
    colors: list[str] = []
    active: list[int] = []
    for i in range(1, 9):
        colors.append(fields.get(f"C_BUTTON_Palette{i}", "#FFFFFF"))
        if fields.get(f"C_CHECKBOX_Palette{i}") == "1":
            active.append(i)
    sparkle = int(fields.get("C_SLIDER_SparkleFrequency", "0") or 0)
    return ColorPalette(colors=colors, active_colors=active, sparkle_frequency=sparkle)


# ---------------------------------------------------------------------------
# Role mapping — assign the user's models/groups to template roles
# ---------------------------------------------------------------------------

_ROLE_NAME_HINTS: dict[str, list[str]] = {
    "hero_layered": ["mega tree", "megatree", "matrix"],
    "beat_pulse": ["star", "flake", "snow", "spinner", "topper", "burst", "bulb",
                   "stake", "pole", "present", "sphere", "wreath", "ornament", "cube"],
    "chase": ["arch", "cane", "icicle", "outline", "roofline", "roof", "line",
              "pillar", "fence", "window", "door", "eave", "horizontal", "vertical",
              "rail", "driveway", "flood"],
}

# Group-name markers for sub-part / spatial-slice groups ("Snowflake Arms",
# "PixStakes - Row1", "Spinners (Inner Band)") — these slice props into pieces
# and shouldn't be picked as template rows; the prop-level group covers them.
_SUBPART_MARKERS = ["(", " arm", " ring", " tip", " spoke", " petal", " pedal",
                    " band", "every other", " row", " half", " layer", " no ",
                    "minus", "override", " lines", "virtual"]

_WHOLE_HOUSE_HINTS = ["everything", "whole house", "wholehouse", "all"]
_WHOLE_HOUSE_NEGATIONS = ["no ", "minus", "override", "(", "w matrix", "w/"]

_ROLE_CATEGORY_FALLBACK: dict[str, str] = {
    "arch": "chase",
    "single_line": "chase",
    "poly_line": "chase",
    "window": "chase",
    "tree": "hero_layered",
    "custom": "beat_pulse",
    "other": "beat_pulse",
}

def _is_sequenceable(model: LightModel) -> bool:
    """Filter out utility/infrastructure rows that should never carry template
    effects: controller placeholders, null pixels, DMX channels, moving heads."""
    name = model.name.lower()
    if model.name.startswith("_") or "null" in name or "remote" in name:
        return False
    # Moving-head channel rows (pan/tilt/shutter/dimmer) aren't pixel props
    if any(h in name for h in ("pan", "tilt", "shutter", "dimmer")):
        return False
    display = model.display_as.lower()
    return not (display.startswith("dmx") or display == "channel block")


def _role_for_model(model: LightModel) -> str:
    name = model.name.lower()
    for role, hints in _ROLE_NAME_HINTS.items():
        if any(h in name for h in hints):
            # Small trees named e.g. "Mini Tree 1" should chase, not act as
            # hero props — only high-pixel trees/matrices carry layered composites.
            if role == "hero_layered" or model.model_category != "tree":
                return role
    role = _ROLE_CATEGORY_FALLBACK.get(model.model_category, "beat_pulse")
    if role == "hero_layered" and model.pixel_count and model.pixel_count < 400:
        return "chase"  # mini trees join the chase lockstep
    return role


def _group_role(group_name: str) -> str | None:
    """Role for a prop-level group, judged by its name; None if not a
    template row candidate (sub-part slice, utility, or unrecognized)."""
    name = group_name.lower()
    core = name.removeprefix("group - ")
    if " - " in core or any(m in name for m in _SUBPART_MARKERS):
        return None
    for role, hints in _ROLE_NAME_HINTS.items():
        if any(h in name for h in hints):
            return role
    return None


def map_roles(show_config: ShowConfig) -> tuple[dict[str, list[str]], str | None]:
    """Map the show's rows (groups preferred, else models) to template roles.

    Mirrors the vendor pattern: pulse and chase props are sequenced on their
    xLights group (one row drives all members in lockstep / ping-pong), hero
    props stay individual. Show groups overlap heavily (whole-house groups,
    spatial slices, sub-part groups), so each model is claimed by at most one
    row: the most comprehensive prop-level group that mentions it wins.
    Returns (role → row names, whole-house group name).
    """
    roles: dict[str, list[str]] = {"beat_pulse": [], "chase": [], "hero_layered": []}
    singing = {m.name for m in show_config.models if m.face_definitions}
    excluded = {m.name for m in show_config.models
                if m.name in singing or not _is_sequenceable(m)}
    model_by_name = {m.name: m for m in show_config.models}

    def resolved(mg) -> list[str]:
        return [n for n in mg.members if n in model_by_name and n not in excluded]

    # Whole-house row: biggest all-encompassing group without a negation
    whole_house: str | None = None
    wh_candidates = [
        mg for mg in show_config.model_groups
        if any(h in mg.name.lower() for h in _WHOLE_HOUSE_HINTS)
        and not any(neg in mg.name.lower() for neg in _WHOLE_HOUSE_NEGATIONS)
    ]
    if wh_candidates:
        whole_house = max(wh_candidates, key=lambda g: len(resolved(g))).name

    # Prop-level groups become rows: most comprehensive first, each model
    # claimed once so overlapping groups don't double-drive anything.
    grouped: set[str] = set()
    candidates = []
    for mg in show_config.model_groups:
        role = _group_role(mg.name)
        if role in ("beat_pulse", "chase"):
            members = resolved(mg)
            if len(members) >= 2:
                candidates.append((mg.name, role, members))
    for gname, role, members in sorted(candidates, key=lambda c: -len(c[2])):
        if any(n in grouped for n in members):
            continue
        roles[role].append(gname)
        grouped.update(members)

    for m in show_config.models:
        if m.name in grouped or m.name in excluded:
            continue
        roles[_role_for_model(m)].append(m.name)

    return roles, whole_house


# ---------------------------------------------------------------------------
# Template block selection
# ---------------------------------------------------------------------------


def _usable(block: dict) -> bool:
    if block["effect"] in _SKIP_EFFECTS:
        return False
    # Blocks referencing local files (shaders, pictures, videos) don't transfer
    return "FILEPICKER" not in block.get("settings", "")


def _pick_blocks(template: dict, role: str, effect: str, count: int = 1) -> list[dict]:
    """Top-N most-used usable blocks for a role+effect, ordered by usage."""
    candidates = [b for b in template.get("effect_blocks", [])
                  if b["role"] == role and b["effect"] == effect and _usable(b)]
    candidates.sort(key=lambda b: -b["uses"])
    return candidates[:count]


def _block_palettes(block: dict, override: list[ColorPalette] | None) -> list[ColorPalette]:
    if override:
        return override
    pals = [parse_palette_string(p) for p in block.get("palettes", [])]
    return pals or [ColorPalette(colors=["#FFFFFF"], active_colors=[1])]


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def build_beat_grid(analysis: SongAnalysis) -> tuple[list[int], int] | None:
    """Beat grid in ms (with one synthetic end beat) and the median beat gap.

    Returns None when the audio has too few beats for beat-driven work.
    """
    beat_ms = [int(b * 1000) for b in analysis.beats.beat_times
               if b * 1000 < analysis.duration_ms]
    if len(beat_ms) < 8:
        return None
    gaps = sorted(b - a for a, b in zip(beat_ms, beat_ms[1:]))
    median_gap = gaps[len(gaps) // 2]
    beat_ms.append(min(beat_ms[-1] + median_gap, analysis.duration_ms))
    return beat_ms, median_gap


def snap_sections_to_beats(
    analysis: SongAnalysis, beat_ms: list[int]
) -> list[tuple[int, int, float, str]]:
    """Sections as (start_beat_idx, end_beat_idx, energy, label), boundaries
    snapped to the beat grid — the rule measured from the source sequence."""
    def nearest(t_ms: int) -> int:
        return min(range(len(beat_ms)), key=lambda i: abs(beat_ms[i] - t_ms))

    sections = []
    for s in analysis.sections:
        b0, b1 = nearest(s.start_time_ms), nearest(s.end_time_ms)
        if b1 > b0:
            sections.append((b0, b1, s.energy_level, s.label))
    if not sections:
        sections = [(0, len(beat_ms) - 1, 0.5, "song")]
    return sections


def build_base_timing_tracks(
    analysis: SongAnalysis,
    beat_ms: list[int],
    median_gap: int,
    sections: list[tuple[int, int, float, str]],
) -> list[TimingTrack]:
    """Beats + Sections timing tracks the way xLights/vendors build them:
    contiguous cells, beats numbered by bar position (1-2-3-4 from downbeats,
    else alternating 1-2)."""
    downbeat_ms = sorted(int(t * 1000) for t in analysis.beats.downbeat_times)

    def near_downbeat(t: int) -> bool:
        i = bisect.bisect_left(downbeat_ms, t)
        return any(0 <= j < len(downbeat_ms) and abs(downbeat_ms[j] - t) <= median_gap // 3
                   for j in (i - 1, i))

    beat_labels = []
    counter = 0
    for i, t in enumerate(beat_ms[:-1]):
        if downbeat_ms:
            counter = 1 if near_downbeat(t) or counter >= 8 else counter + 1
        else:
            counter = 1 if i % 2 == 0 else 2
        beat_labels.append(TimingTrackLabel(
            label=str(counter), start_time_ms=t, end_time_ms=beat_ms[i + 1]))

    section_labels = [
        TimingTrackLabel(label=label, start_time_ms=beat_ms[b0], end_time_ms=beat_ms[b1])
        for b0, b1, _e, label in sections
    ]
    return [
        TimingTrack(name="Beats", labels=[beat_labels]),
        TimingTrack(name="Sections", labels=[section_labels]),
    ]


def _unique_output_path(show_path: Path, base_name: str) -> Path:
    output_path = Path(show_path) / f"{base_name}.xsq"
    counter = 1
    while output_path.exists():
        output_path = Path(show_path) / f"{base_name} (generated {counter}).xsq"
        counter += 1
    return output_path


def create_base_sequence(
    analysis: SongAnalysis,
    show_config: ShowConfig,
    mp3_path: Path,
) -> dict:
    """Create a base sequence: Beats + Sections timing tracks, no effects.

    The starting point for building a show up pattern by pattern."""
    grid = build_beat_grid(analysis)
    if grid is None:
        return {"error": "Not enough beats detected in the audio"}
    beat_ms, median_gap = grid
    sections = snap_sections_to_beats(analysis, beat_ms)
    timing_tracks = build_base_timing_tracks(analysis, beat_ms, median_gap, sections)

    spec = SequenceSpec(
        song_title=mp3_path.stem, media_file=str(mp3_path),
        duration_ms=analysis.duration_ms, timing_ms=25,
        palettes=[], effects=[], timing_tracks=timing_tracks,
    )
    output_path = _unique_output_path(Path(show_config.show_path), mp3_path.stem)
    write_xsq(spec, show_config, output_path)

    return {
        "success": True,
        "output_path": str(output_path),
        "song": mp3_path.stem,
        "duration": f"{analysis.duration_seconds:.1f}s",
        "tempo": f"{analysis.beats.tempo:.0f} BPM",
        "beats": len(beat_ms) - 1,
        "sections": [{"label": lbl, "start": f"{beat_ms[b0]/1000:.1f}s",
                      "end": f"{beat_ms[b1]/1000:.1f}s", "energy": round(e, 2)}
                     for b0, b1, e, lbl in sections],
        "message": f"Base sequence created (timing tracks only): {output_path.name}",
    }


def apply_pulse_pattern(
    xsq_path: Path,
    on_beat_rows: list[str],
    off_beat_rows: list[str],
    template_name: str = "shockwave_beat_show",
    offset_mode: str = "alternate_beats",
) -> dict:
    """Duplicate the source sequence's star pulse layout onto target rows.

    Every pulse uses the template's Shockwave block verbatim (settings and
    palette strings straight from the source) and the target sequence's own
    Beats timing track as the grid. Edits the .xsq in place with a
    timestamped backup.

    offset_mode controls the ping-pong timing:
      "alternate_beats" — on_beat_rows fire on beats 1,3,5...; off_beat_rows
          answer on beats 2,4,6... Every pulse starts exactly on a beat.
      "half_beat" — vendor-literal: both sets fire every beat, off_beat_rows
          shifted half a beat. Suits slower songs (~90 BPM); reads as
          strobing at fast tempos.
      "every_beat" — all rows pulse together on every beat.
    """
    import xml.etree.ElementTree as ET

    from xlights_mcp.xlights.xsq_editor import (
        _backup_and_write, _effect_db_ref, _ensure_display_element,
        _get_or_create_layer, _get_or_create_model_element, _palette_ref,
        _sort_layer,
    )

    template = load_template(template_name)
    if template is None:
        return {"error": f"Template not found: {template_name}",
                "available_templates": list_templates()}
    blocks = _pick_blocks(template, "beat_pulse", "Shockwave", 1)
    if not blocks:
        return {"error": f"Template '{template_name}' has no beat_pulse Shockwave block"}
    block = blocks[0]
    settings_str = block["settings"]
    palette_str = (block.get("palettes") or [""])[0]

    xsq_path = Path(xsq_path)
    if not xsq_path.exists():
        return {"error": f"Sequence not found: {xsq_path}"}
    tree = ET.parse(xsq_path)
    root = tree.getroot()

    beats: list[int] = []
    element_effects = root.find("ElementEffects")
    if element_effects is not None:
        for el in element_effects.findall("Element"):
            if el.get("type") == "timing" and el.get("name") == "Beats":
                for layer in el.findall("EffectLayer"):
                    for e in layer.findall("Effect"):
                        beats.append(int(e.get("startTime", 0)))
    beats = sorted(set(beats))
    if len(beats) < 8:
        return {"error": "Sequence has no usable 'Beats' timing track — "
                         "create a base sequence first"}
    gaps = sorted(b - a for a, b in zip(beats, beats[1:]))
    gap = gaps[len(gaps) // 2]

    def q(t: int) -> int:  # snap to the 25ms frame grid
        return round(t / 25) * 25

    ref = _effect_db_ref(root, settings_str)
    pal = _palette_ref(root, palette_str) if palette_str else None

    dur_on, dur_off = min(300, gap), min(350, gap)
    all_idx = list(range(len(beats)))
    if offset_mode == "half_beat":
        plans = [(on_beat_rows, all_idx, 0, dur_on),
                 (off_beat_rows, all_idx, gap // 2, dur_off)]
    elif offset_mode == "every_beat":
        plans = [(on_beat_rows + off_beat_rows, all_idx, 0, dur_on)]
    elif offset_mode == "alternate_beats":
        plans = [(on_beat_rows, all_idx[0::2], 0, dur_on),
                 (off_beat_rows, all_idx[1::2], 0, dur_on)]
    else:
        return {"error": f"Unknown offset_mode: {offset_mode}. "
                         "Use: alternate_beats, half_beat, every_beat"}

    placed = 0
    for rows, idxs, offset, dur in plans:
        for row in rows:
            _ensure_display_element(root, row)
            model_elem = _get_or_create_model_element(root, row)
            layer_elem = _get_or_create_layer(model_elem, 0)
            for i in idxs:
                start = q(beats[i] + offset)
                next_start = q(beats[i + 1] + offset) if i + 1 < len(beats) else start + dur
                end = min(q(start + dur), next_start)
                if end <= start:
                    continue
                e = ET.SubElement(layer_elem, "Effect")
                e.set("name", "Shockwave")
                e.set("startTime", str(start))
                e.set("endTime", str(end))
                e.set("ref", str(ref))
                if pal is not None:
                    e.set("palette", str(pal))
                placed += 1
            _sort_layer(layer_elem)

    backup = _backup_and_write(tree, xsq_path)
    return {
        "success": True,
        "sequence": str(xsq_path),
        "backup": str(backup),
        "pattern": f"star pulse ({offset_mode})",
        "offset_mode": offset_mode,
        "on_beat_rows": on_beat_rows,
        "off_beat_rows": off_beat_rows,
        "beats_used": len(beats),
        "effects_added": placed,
        "message": f"Added {placed} Shockwave pulses across "
                   f"{len(on_beat_rows) + len(off_beat_rows)} rows",
    }


def apply_accent_pulse_pattern(
    xsq_path: Path,
    rows: list[str],
    template_name: str = "shockwave_beat_show",
    subdivision: str = "beat",
) -> dict:
    """Duplicate the source's Trees Stars layout: a continuous Shockwave pulse
    with a bigger accent variant on every bar downbeat.

    Measured from the source: one pulse every half-beat, and every 8th pulse
    (= each bar's downbeat) swaps to a second, more dramatic Shockwave block.
    Underneath the pulses (layer 1), an Off effect spans the whole row —
    exactly like the source — so background group effects can't bleed onto
    these props. Uses the sequence's own Beats track — the accent lands
    wherever the beat label is "1".

    subdivision:
      "beat" — one pulse per beat with bar-downbeat accents (Trees Stars
          technique, tempo-adapted for fast songs);
      "half_beat" — vendor-literal Trees Stars: one pulse every half beat
          with bar-downbeat accents (~90 BPM feel);
      "two_beat" — the Snowflakes technique: one full-beat-long pulse on
          every 2nd beat, no accents. Gentle, works at any tempo.
    """
    import xml.etree.ElementTree as ET

    from xlights_mcp.xlights.xsq_editor import (
        _backup_and_write, _effect_db_ref, _ensure_display_element,
        _get_or_create_layer, _get_or_create_model_element, _palette_ref,
        _sort_layer,
    )

    if subdivision not in ("beat", "half_beat", "two_beat"):
        return {"error": f"Unknown subdivision: {subdivision}. "
                         "Use: beat, half_beat, two_beat"}

    template = load_template(template_name)
    if template is None:
        return {"error": f"Template not found: {template_name}",
                "available_templates": list_templates()}
    blocks = _pick_blocks(template, "beat_pulse", "Shockwave", 3)
    if not blocks:
        return {"error": f"Template '{template_name}' has no beat_pulse Shockwave block"}
    # By usage: [0] the stars block, [1] the trees-stars main block,
    # [2] the rare accent variant. Fall back gracefully on smaller templates.
    main = blocks[1] if len(blocks) > 1 else blocks[0]
    accent = blocks[-1] if len(blocks) > 2 else main

    xsq_path = Path(xsq_path)
    if not xsq_path.exists():
        return {"error": f"Sequence not found: {xsq_path}"}
    tree = ET.parse(xsq_path)
    root = tree.getroot()

    marks: list[tuple[int, str]] = []
    element_effects = root.find("ElementEffects")
    if element_effects is not None:
        for el in element_effects.findall("Element"):
            if el.get("type") == "timing" and el.get("name") == "Beats":
                for layer in el.findall("EffectLayer"):
                    for e in layer.findall("Effect"):
                        marks.append((int(e.get("startTime", 0)), e.get("label", "")))
    marks = sorted(set(marks))
    if len(marks) < 8:
        return {"error": "Sequence has no usable 'Beats' timing track — "
                         "create a base sequence first"}
    beats = [t for t, _ in marks]
    gaps = sorted(b - a for a, b in zip(beats, beats[1:]))
    gap = gaps[len(gaps) // 2]

    def q(t: int) -> int:
        return round(t / 25) * 25

    main_ref = _effect_db_ref(root, main["settings"])
    accent_ref = _effect_db_ref(root, accent["settings"])
    main_pal = _palette_ref(root, (main.get("palettes") or [""])[0]) \
        if main.get("palettes") else None
    accent_pal = _palette_ref(root, (accent.get("palettes") or [""])[0]) \
        if accent.get("palettes") else main_pal

    # pulse slots: (start, is_bar_downbeat)
    slots: list[tuple[int, bool]] = []
    if subdivision == "two_beat":
        # Snowflakes technique: every 2nd beat, full-beat pulse, no accents
        slots = [(t, False) for t, _label in marks[::2]]
        step = gap * 2
        dur_main = dur_accent = min(650, gap)
    else:
        for i, (t, label) in enumerate(marks):
            slots.append((t, label == "1"))
            if subdivision == "half_beat":
                half = t + (beats[i + 1] - t) // 2 if i + 1 < len(beats) else t + gap // 2
                slots.append((half, False))
        step = gap if subdivision == "beat" else gap // 2
        dur_main, dur_accent = min(300, step), min(350, step)

    placed = accents = 0
    for row in rows:
        _ensure_display_element(root, row)
        model_elem = _get_or_create_model_element(root, row)
        layer_elem = _get_or_create_layer(model_elem, 0)
        for i, (t, is_downbeat) in enumerate(slots):
            start = q(t)
            next_start = q(slots[i + 1][0]) if i + 1 < len(slots) else start + step
            dur = dur_accent if is_downbeat else dur_main
            end = min(q(start + dur), next_start)
            if end <= start:
                continue
            e = ET.SubElement(layer_elem, "Effect")
            e.set("name", "Shockwave")
            e.set("startTime", str(start))
            e.set("endTime", str(end))
            e.set("ref", str(accent_ref if is_downbeat else main_ref))
            pal = accent_pal if is_downbeat else main_pal
            if pal is not None:
                e.set("palette", str(pal))
            placed += 1
            accents += is_downbeat
        _sort_layer(layer_elem)

        # Off across the row's whole duration on the layer below the pulses,
        # matching the source's Trees Stars layout
        off_ref = _effect_db_ref(root, "")
        off_layer = _get_or_create_layer(model_elem, 1)
        off = ET.SubElement(off_layer, "Effect")
        off.set("name", "Off")
        off.set("startTime", str(q(slots[0][0])))
        off.set("endTime", str(q(slots[-1][0]) + step))
        off.set("ref", str(off_ref))
        _sort_layer(off_layer)

    backup = _backup_and_write(tree, xsq_path)
    return {
        "success": True,
        "sequence": str(xsq_path),
        "backup": str(backup),
        "pattern": f"accent pulse ({subdivision}, bar-downbeat accents, Off underlay)",
        "rows": rows,
        "effects_added": placed,
        "accent_pulses": accents,
        "message": f"Added {placed} Shockwave pulses ({accents} bar-downbeat accents) "
                   f"across {len(rows)} row(s)",
    }


ROLE_DESCRIPTIONS = {
    "beat_pulse": "Shockwave pulse on every beat, rows alternate on opposite beats (ping-pong)",
    "chase": "paired chase blocks alternating per beat, identical timeline on every row (lockstep)",
    "hero_layered": "layered Spirals/Pinwheel/On composite in 8-beat blocks — the visual centerpiece rows",
}


def generate_from_template(
    analysis: SongAnalysis,
    show_config: ShowConfig,
    mp3_path: Path,
    template_name: str = "shockwave_beat_show",
    theme: str | None = None,
    role_assignments: dict[str, list[str]] | None = None,
    whole_house_row: str | None = None,
) -> dict:
    """Generate a sequence by applying a style template to the analyzed song.

    Two-step flow: when role_assignments is None, nothing is written — the
    proposed model/group → role mapping is returned for the user to review.
    Call again with the validated role_assignments (and optionally
    whole_house_row) to actually generate the sequence.
    """
    template = load_template(template_name)
    if template is None:
        return {
            "error": f"Template not found: {template_name}",
            "available_templates": list_templates(),
        }

    grid_info = build_beat_grid(analysis)
    if grid_info is None:
        return {"error": "Not enough beats detected in the audio to apply a beat-driven template"}
    beat_ms, median_gap = grid_info

    if role_assignments is None:
        proposed, wh = map_roles(show_config)
        return {
            "needs_role_confirmation": True,
            "template": template_name,
            "song": mp3_path.stem,
            "tempo": f"{analysis.beats.tempo:.0f} BPM",
            "sections": len(analysis.sections),
            "role_descriptions": ROLE_DESCRIPTIONS,
            "proposed_roles": {r: rows for r, rows in proposed.items()},
            "proposed_whole_house": wh,
            "message": (
                "No file was written. Review the proposed mapping with the user: "
                "rows may be model names or group names; remove rows that shouldn't "
                "be sequenced, move rows between roles, or add missing groups. Then "
                "call again with role_assignments={role: [rows]} and optionally "
                "whole_house_row to generate."
            ),
        }

    valid_rows = ({m.name for m in show_config.models}
                  | {g.name for g in show_config.model_groups})
    bad_roles = set(role_assignments) - {"beat_pulse", "chase", "hero_layered"}
    if bad_roles:
        return {"error": f"Unknown roles: {sorted(bad_roles)}. "
                         "Valid: beat_pulse, chase, hero_layered"}
    unknown = [r for rows in role_assignments.values() for r in rows
               if r not in valid_rows]
    if unknown:
        return {"error": f"Unknown model/group names in role_assignments: {unknown}"}
    if whole_house_row and whole_house_row not in valid_rows:
        return {"error": f"Unknown whole_house_row: {whole_house_row}"}

    roles = {role: list(role_assignments.get(role, []))
             for role in ("beat_pulse", "chase", "hero_layered")}
    whole_house = whole_house_row
    logger.info(f"Template role mapping (user-validated): {roles}, "
                f"whole_house={whole_house}")

    # Theme override replaces vendor palettes entirely
    theme_palettes = list(get_theme_palettes(theme).values()) if theme else None

    # Pull the signature blocks from the template
    pulse_blocks = _pick_blocks(template, "beat_pulse", "Shockwave", 2)
    chase_pair = _pick_blocks(template, "chase", "SingleStrand", 2)
    chase_bed = _pick_blocks(template, "chase", "On", 1)
    hero_spirals = _pick_blocks(template, "hero_layered", "Spirals", 2)
    hero_pinwheel = _pick_blocks(template, "hero_layered", "Pinwheel", 1)
    hero_bed = _pick_blocks(template, "hero_layered", "On", 1)
    accent_blocks = _pick_blocks(template, "global_accent", "Pinwheel", 1)

    if not (pulse_blocks or chase_pair or hero_spirals):
        return {"error": f"Template '{template_name}' has no usable effect blocks"}

    all_effects: list[EffectPlacement] = []
    all_palettes: list[ColorPalette] = list(theme_palettes or [])

    def place(row: str, layer: int, block: dict, start_ms: int, end_ms: int,
              palette: ColorPalette) -> None:
        if end_ms <= start_ms:
            return
        if palette not in all_palettes:
            all_palettes.append(palette)
        all_effects.append(EffectPlacement(
            model_name=row, layer=layer, effect_name=block["effect"],
            start_time_ms=start_ms, end_time_ms=int(min(end_ms, analysis.duration_ms)),
            settings=parse_settings_string(block["settings"]), palette=palette,
        ))

    # Section boundaries snapped to the beat grid (the template's core rule)
    sections = snap_sections_to_beats(analysis, beat_ms)

    # Color rules measured per-layer from the source sequence:
    #   pulse rows keep ONE stable palette for ~a third of the song;
    #   chase rows run CONSTANT white — the beat alternation is motion
    #   (left/right chase blocks), not color;
    #   On-wash beds cycle a different color EVERY hit (7-13 distinct);
    #   hero layers rotate palettes every few effects — the color variety.
    total_beats = len(beat_ms) - 1

    # Template-wide palette pool: the source's full color variety, drawn on
    # by the On-wash beds and hero layers.
    palette_pool: list[ColorPalette] = list(theme_palettes or [])
    if not palette_pool:
        seen_pal: set[str] = set()
        for b in template.get("effect_blocks", []):
            if _usable(b):
                for p in b.get("palettes", []):
                    if p not in seen_pal:
                        seen_pal.add(p)
                        palette_pool.append(parse_palette_string(p))
    if not palette_pool:
        palette_pool = [ColorPalette(colors=["#FFFFFF"], active_colors=[1])]

    # --- beat_pulse rows: one Shockwave per beat, ping-pong across rows ---
    for sec_idx, (b0, b1, energy, _label) in enumerate(sections):
        if energy < LOW_ENERGY or not pulse_blocks:
            continue
        song_third = min(2, 3 * b0 // max(total_beats, 1))
        for row_idx, row in enumerate(roles["beat_pulse"]):
            block = pulse_blocks[row_idx % len(pulse_blocks)]
            pals = _block_palettes(block, theme_palettes)
            # stable per-row color identity, shifting only per song third
            palette = pals[(row_idx + song_third) % len(pals)]
            dur = min(block.get("median_duration_ms", 300) or 300, median_gap)
            for bi in range(b0, b1):
                if bi % 2 != row_idx % 2:  # ping-pong: opposite beats
                    continue
                place(row, 0, block, beat_ms[bi], beat_ms[bi] + dur, palette)

    # --- chase rows: paired blocks alternate per beat, lockstep across rows ---
    # The chase color itself stays constant (source: white) — motion carries
    # the beat; the colorful On-wash bed underneath cycles per hit.
    for sec_idx, (b0, b1, energy, _label) in enumerate(sections):
        if energy < LOW_ENERGY or not chase_pair:
            continue
        for bi in range(b0, b1):
            block = chase_pair[bi % len(chase_pair)]
            pals = _block_palettes(block, theme_palettes)
            for row in roles["chase"]:
                place(row, 0, block, beat_ms[bi], beat_ms[bi + 1], pals[0])
        # On-wash bed under the chases in high-energy sections: 4 beats per
        # hit, a different color from the pool on every hit
        if energy >= HIGH_ENERGY and chase_bed:
            bed = chase_bed[0]
            for j, bi in enumerate(range(b0, b1, 4)):
                end = beat_ms[min(bi + 4, b1)]
                for row in roles["chase"]:
                    place(row, 1, bed, beat_ms[bi], end,
                          palette_pool[(sec_idx * 5 + j) % len(palette_pool)])

    # --- hero rows: layered composite in 8-beat blocks ---
    # Heroes are the color playground: rotate through the template's entire
    # palette variety (the source used 32-36 distinct palettes on hero props).
    grid = int(template.get("timing", {}).get("section_grid_beats", 8)) or 8
    for sec_idx, (b0, b1, energy, _label) in enumerate(sections):
        for row_idx, row in enumerate(roles["hero_layered"]):
            for j, bi in enumerate(range(b0, b1, grid)):
                end = beat_ms[min(bi + grid, b1)]
                if hero_spirals:
                    block = hero_spirals[j % len(hero_spirals)]
                    place(row, 1, block, beat_ms[bi], end,
                          palette_pool[(sec_idx * 3 + j + row_idx) % len(palette_pool)])
                if energy >= HIGH_ENERGY and hero_pinwheel:
                    block = hero_pinwheel[0]
                    place(row, 0, block, beat_ms[bi], beat_ms[min(bi + 2, b1)],
                          palette_pool[(sec_idx * 3 + j + row_idx + 1) % len(palette_pool)])
            # colorful On bed: a different color from the pool every 4 beats,
            # matching the source's per-hit color cycling on hero On layers
            if energy >= HIGH_ENERGY and hero_bed:
                for j, bi in enumerate(range(b0, b1, 4)):
                    end = beat_ms[min(bi + 4, b1)]
                    place(row, 2, hero_bed[0], beat_ms[bi], end,
                          palette_pool[(sec_idx * 7 + j + row_idx) % len(palette_pool)])

    # --- whole-house accents at high-energy section starts ---
    if whole_house and accent_blocks:
        block = accent_blocks[0]
        pals = _block_palettes(block, theme_palettes)
        for sec_idx, (b0, b1, energy, _label) in enumerate(sections):
            if energy >= HIGH_ENERGY:
                place(whole_house, 0, block, beat_ms[b0],
                      beat_ms[min(b0 + 2, b1)], pals[sec_idx % len(pals)])

    if not all_effects:
        return {"error": "No effects generated — no models matched the template roles",
                "role_mapping": roles}

    # --- timing tracks: Beats + Sections (labels snapped to the beat grid) ---
    timing_tracks = build_base_timing_tracks(analysis, beat_ms, median_gap, sections)

    spec = SequenceSpec(
        song_title=mp3_path.stem, media_file=str(mp3_path),
        duration_ms=analysis.duration_ms, timing_ms=int(template.get("timing", {}).get("frame_ms", 25)),
        palettes=all_palettes, effects=all_effects, timing_tracks=timing_tracks,
    )

    output_path = _unique_output_path(Path(show_config.show_path), mp3_path.stem)
    write_xsq(spec, show_config, output_path)

    return {
        "success": True,
        "output_path": str(output_path),
        "template": template_name,
        "song": mp3_path.stem,
        "duration": f"{analysis.duration_seconds:.1f}s",
        "tempo": f"{analysis.beats.tempo:.0f} BPM",
        "sections": len(sections),
        "total_effects": len(all_effects),
        "unique_palettes": len(all_palettes),
        "role_mapping": {r: rows for r, rows in roles.items() if rows},
        "whole_house_row": whole_house,
        "message": f"Sequence created from template '{template_name}': {output_path.name}",
    }
