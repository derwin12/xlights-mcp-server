"""In-place editing of existing .xsq sequence files (add/update/delete effects).

Unlike xsq_writer (which builds a brand-new file from a SequenceSpec), these
functions parse an existing .xsq, mutate the ElementEffects/EffectDB/
ColorPalettes sections directly, and write the file back — preserving
everything else (timing tracks, header metadata, untouched models) byte-for-byte
in structure.

Every write keeps a timestamped backup of the previous file alongside it
(e.g. "MySong.xsq.bak.20260621120000") so a bad edit is always recoverable.
"""

from __future__ import annotations

import datetime
import logging
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from xlights_mcp.xlights.palettes import ColorPalette

logger = logging.getLogger(__name__)


def add_effect(
    xsq_path: Path,
    model_name: str,
    effect_name: str,
    start_time_ms: int,
    end_time_ms: int,
    settings: dict[str, str] | None = None,
    layer: int = 0,
    colors: list[str] | None = None,
    active_colors: list[int] | None = None,
) -> dict:
    """Add an effect placement to a model in an existing sequence."""
    tree = ET.parse(xsq_path)
    root = tree.getroot()

    _ensure_display_element(root, model_name)
    model_elem = _get_or_create_model_element(root, model_name)
    layer_elem = _get_or_create_layer(model_elem, layer)

    effect_elem = ET.SubElement(layer_elem, "Effect")
    effect_elem.set("name", effect_name)
    effect_elem.set("startTime", str(start_time_ms))
    effect_elem.set("endTime", str(end_time_ms))

    settings_str = _settings_str(settings or {})
    if settings_str:
        effect_elem.set("ref", str(_effect_db_ref(root, settings_str)))

    if colors:
        palette = ColorPalette(
            colors=colors, active_colors=active_colors or list(range(1, len(colors) + 1))
        )
        effect_elem.set("palette", str(_palette_ref(root, palette.to_xlights_string())))

    _sort_layer(layer_elem)
    index = list(layer_elem).index(effect_elem)

    backup_path = _backup_and_write(tree, xsq_path)
    return {
        "success": True,
        "model_name": model_name,
        "layer": layer,
        "index": index,
        "effect_name": effect_name,
        "backup": str(backup_path),
    }


def update_effect(
    xsq_path: Path,
    model_name: str,
    layer: int,
    index: int,
    effect_name: str | None = None,
    start_time_ms: int | None = None,
    end_time_ms: int | None = None,
    settings: dict[str, str] | None = None,
    colors: list[str] | None = None,
    active_colors: list[int] | None = None,
) -> dict:
    """Update fields on an existing effect, addressed by (layer, index)."""
    tree = ET.parse(xsq_path)
    root = tree.getroot()

    layer_elem = _find_layer(root, model_name, layer)
    if isinstance(layer_elem, dict):
        return layer_elem

    effects = list(layer_elem)
    if index >= len(effects) or index < 0:
        return {"error": f"Effect index {index} not found in layer {layer} (has {len(effects)} effects)"}
    effect_elem = effects[index]

    if effect_name is not None:
        effect_elem.set("name", effect_name)
    if start_time_ms is not None:
        effect_elem.set("startTime", str(start_time_ms))
    if end_time_ms is not None:
        effect_elem.set("endTime", str(end_time_ms))
    if settings is not None:
        settings_str = _settings_str(settings)
        if settings_str:
            effect_elem.set("ref", str(_effect_db_ref(root, settings_str)))
        elif "ref" in effect_elem.attrib:
            del effect_elem.attrib["ref"]
    if colors is not None:
        palette = ColorPalette(
            colors=colors, active_colors=active_colors or list(range(1, len(colors) + 1))
        )
        effect_elem.set("palette", str(_palette_ref(root, palette.to_xlights_string())))

    if start_time_ms is not None or end_time_ms is not None:
        _sort_layer(layer_elem)
        index = list(layer_elem).index(effect_elem)

    backup_path = _backup_and_write(tree, xsq_path)
    return {
        "success": True,
        "model_name": model_name,
        "layer": layer,
        "index": index,
        "backup": str(backup_path),
    }


def delete_effect(xsq_path: Path, model_name: str, layer: int, index: int) -> dict:
    """Delete an effect, addressed by (layer, index)."""
    tree = ET.parse(xsq_path)
    root = tree.getroot()

    layer_elem = _find_layer(root, model_name, layer)
    if isinstance(layer_elem, dict):
        return layer_elem

    effects = list(layer_elem)
    if index >= len(effects) or index < 0:
        return {"error": f"Effect index {index} not found in layer {layer} (has {len(effects)} effects)"}

    layer_elem.remove(effects[index])

    backup_path = _backup_and_write(tree, xsq_path)
    return {
        "success": True,
        "model_name": model_name,
        "layer": layer,
        "index": index,
        "deleted": True,
        "backup": str(backup_path),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_display_element(root: ET.Element, model_name: str) -> None:
    display_elems = root.find("DisplayElements")
    if display_elems is None:
        display_elems = ET.SubElement(root, "DisplayElements")
    if any(e.get("name") == model_name for e in display_elems):
        return
    de = ET.SubElement(display_elems, "Element")
    de.set("collapsed", "0")
    de.set("type", "model")
    de.set("name", model_name)
    de.set("visible", "1")
    de.set("active", "0")


def _get_or_create_model_element(root: ET.Element, model_name: str) -> ET.Element:
    element_effects = root.find("ElementEffects")
    if element_effects is None:
        element_effects = ET.SubElement(root, "ElementEffects")
    for e in element_effects:
        if e.get("name") == model_name:
            return e
    model_elem = ET.SubElement(element_effects, "Element")
    model_elem.set("type", "model")
    model_elem.set("name", model_name)
    return model_elem


def _get_or_create_layer(model_elem: ET.Element, layer: int) -> ET.Element:
    layers = list(model_elem)
    while len(layers) <= layer:
        ET.SubElement(model_elem, "EffectLayer")
        layers = list(model_elem)
    return layers[layer]


def _find_layer(root: ET.Element, model_name: str, layer: int) -> ET.Element | dict:
    """Look up an existing model's layer without creating anything. Returns an error dict on failure."""
    element_effects = root.find("ElementEffects")
    model_elem = None
    if element_effects is not None:
        for e in element_effects:
            if e.get("name") == model_name:
                model_elem = e
                break
    if model_elem is None:
        return {"error": f"Model '{model_name}' has no effects in this sequence"}

    layers = list(model_elem)
    if layer >= len(layers) or layer < 0:
        return {"error": f"Layer {layer} not found for model '{model_name}' (has {len(layers)} layers)"}
    return layers[layer]


def _settings_str(settings: dict[str, str]) -> str:
    return ",".join(f"{k}={v}" for k, v in sorted(settings.items()))


def _effect_db_ref(root: ET.Element, settings_str: str) -> int:
    """Find or create a deduplicated EffectDB entry, returning its index."""
    effect_db = root.find("EffectDB")
    if effect_db is None:
        effect_db = ET.SubElement(root, "EffectDB")
    for i, e in enumerate(effect_db):
        if (e.text or "") == settings_str:
            return i
    e = ET.SubElement(effect_db, "Effect")
    e.text = settings_str
    return len(list(effect_db)) - 1


def _palette_ref(root: ET.Element, palette_str: str) -> int:
    """Find or create a deduplicated ColorPalettes entry, returning its index."""
    palettes = root.find("ColorPalettes")
    if palettes is None:
        palettes = ET.SubElement(root, "ColorPalettes")
    for i, p in enumerate(palettes):
        if (p.text or "") == palette_str:
            return i
    p = ET.SubElement(palettes, "ColorPalette")
    p.text = palette_str
    return len(list(palettes)) - 1


def _sort_layer(layer_elem: ET.Element) -> None:
    """Keep effects within a layer ordered by startTime, matching xLights' own format."""
    effects = sorted(list(layer_elem), key=lambda e: int(e.get("startTime", "0")))
    for e in effects:
        layer_elem.remove(e)
    for e in effects:
        layer_elem.append(e)


def _backup_and_write(tree: ET.ElementTree, xsq_path: Path) -> Path:
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    backup_path = xsq_path.with_name(f"{xsq_path.name}.bak.{timestamp}")
    shutil.copy2(xsq_path, backup_path)

    ET.indent(tree, space="  ")
    with open(xsq_path, "w", encoding="UTF-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(f, encoding="unicode", xml_declaration=False)

    logger.info(f"Updated {xsq_path} (backup: {backup_path.name})")
    return backup_path
