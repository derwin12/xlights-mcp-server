"""Skeleton band: sprites, slot masks, sources for kicks and singing, the shader and placement."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET

import pytest

from xlights_mcp.sprites import band as b
from xlights_mcp.sprites import band_place as bp
from xlights_mcp.sprites import band_shader as bs
from xlights_mcp.sprites import dancers as d


def _state(slot, kick=False, vocal=False, loud=0.0, bob=0):
    return b.SlotState(slot // 4, slot, kick, vocal, loud, bob)


def test_every_layer_is_13x17_and_uses_known_codes():
    for name, rows in b.LAYERS.items():
        assert len(rows) == b.H and all(len(r) == b.W for r in rows), name
        assert set("".join(rows)) <= set(bs.CODES), name


def test_drummer_reacts_to_kicks_snares_and_beat_one():
    shirt = d.SHIRTS["teal"]
    plain = b.draw_member("drums", _state(2), shirt)
    kicked = b.draw_member("drums", _state(2, kick=True), shirt)
    assert plain.getpixel((6, 12)) == b.DRUM_HEAD and kicked.getpixel((6, 12)) == b.DRUM_FLASH
    snare = b.draw_member("drums", _state(4), shirt)
    assert snare.getpixel((2, 11)) == b.DRUM_FLASH and plain.getpixel((2, 11)) == b.DRUM_HEAD
    assert b.draw_member("drums", _state(0), shirt).getpixel((11, 6)) == b.CYMBAL_FLASH
    assert plain.getpixel((11, 6)) == b.CYMBAL


def test_singer_jaw_and_free_arm():
    shirt = d.SHIRTS["red"]
    shut = b.draw_member("singer", _state(0, vocal=False), shirt)
    sung = b.draw_member("singer", _state(0, vocal=True), shirt)
    assert shut.getpixel((6, 2)) == d.BONE and sung.getpixel((6, 2)) == d.BLACK
    assert sung.getpixel((6, 4)) == d.BONE                      # dropped jaw
    assert b.singer_arm(0.1) == "free_down" and b.singer_arm(0.5) == "free_out" and b.singer_arm(0.9) == "free_up"


def test_guitar_strums_down_on_the_beat_and_up_off_it():
    assert b.layers_for("guitar", _state(0))[-1] == "strum_down"
    assert b.layers_for("guitar", _state(2))[-1] == "strum_up"


def test_band_frame_dresses_like_the_crew():
    img = b.band_frame(_state(0), ["purple", "red", "teal"], "female", scale=2)
    assert img.size == (3 * b.W * 2, b.H * 2)
    looks = d.crew_from_style(3, "unison", ["purple", "red", "teal"], "female")
    assert img.getpixel((3 * 2, 2 * 2)) == d.HAIR[looks[0].hair]       # guitarist's hair


def test_slot_masks():
    # a 4-beat bar from 0 to 1600 ms: slots of 100 ms
    kick, vocal = bp.slot_masks(0, 1600, 4, kicks=[0, 450, 1599], vocals=[(800, 1000)])
    assert kick == (1 << 0) | (1 << 4) | (1 << 15)
    assert vocal == (1 << 8) | (1 << 9)
    kick5, _ = bp.slot_masks(0, 2000, 5, kicks=[1950], vocals=[])   # 20 slots: the 20th does not fit 16 bits
    assert kick5 == 0


XSQ = """<?xml version="1.0" encoding="UTF-8"?>
<xsequence><head><sequenceDuration>4.000</sequenceDuration><mediaFile></mediaFile></head>
<ColorPalettes/><EffectDB/><DisplayElements/>
<ElementEffects>
  <Element type="timing" name="Beats"><EffectLayer>{beats}</EffectLayer></Element>
  {extra}
  <Element type="model" name="Matrix"><EffectLayer/></Element>
</ElementEffects></xsequence>"""
RGB = """<xrgb><models>
<model name="Matrix" DisplayAs="Matrix" NumStrings="60" NodesPerString="120" StrandsPerString="1" Vertical="false"/>
</models></xrgb>"""


def _show(tmp_path, extra=""):
    beats = "".join(f'<Effect label="{i % 4 + 1}" startTime="{i * 400}" endTime="{i * 400 + 400}"/>' for i in range(8))
    (tmp_path / "song.xsq").write_text(XSQ.format(beats=beats, extra=extra), encoding="utf-8")
    (tmp_path / "xlights_rgbeffects.xml").write_text(RGB, encoding="utf-8")
    return tmp_path / "song.xsq"


LYRICS = ('<Element type="timing" name="Lyrics"><EffectLayer><Effect label="la" startTime="0" endTime="800"/>'
          '</EffectLayer><EffectLayer><Effect label="la" startTime="0" endTime="800"/></EffectLayer><EffectLayer>'
          '<Effect label="MBP" startTime="0" endTime="200"/><Effect label="AI" startTime="200" endTime="800"/>'
          '</EffectLayer></Element>'
          '<Element type="timing" name="Kick Hits"><EffectLayer><Effect startTime="0" endTime="10"/>'
          '<Effect startTime="1650" endTime="1660"/></EffectLayer></Element>')


def test_place_band_reads_kicks_and_phonemes(tmp_path):
    xsq = _show(tmp_path, LYRICS)
    res = bp.place_band(xsq, tmp_path, ["Matrix"], figure="mixed", stage=True)
    assert res[0].effects == 2 and res[0].kick_source == "Kick Hits track" and "phonemes" in res[0].vocal_source
    assert (tmp_path / "Shaders" / "Skeleton Band.fs").exists()
    root = ET.parse(xsq).getroot()
    model = next(e for e in root.iter("Element") if e.get("name") == "Matrix")
    top = model.findall("EffectLayer")[0].findall("Effect")
    texts = [root.find("EffectDB")[int(e.get("ref"))].text for e in top]
    # bar 1 (0-1600, 100 ms slots): kick in slot 0, mouth open in slots 2-7 (AI 200-800)
    assert f"E_SLIDER_SHADERXYZZY_kick={1 * 100}," in texts[0]
    assert f"E_SLIDER_SHADERXYZZY_vocal={0b11111100 * 100}," in texts[0]
    assert f"E_SLIDER_SHADERXYZZY_kick={(1 << 0) * 100}," in texts[1]      # 1650 is slot 0 of bar 2
    assert "E_CHOICE_SHADERXYZZY_figure=Mixed" in texts[0] and "E_CHECKBOX_SHADERXYZZY_stage=1" in texts[0]
    bp.place_band(xsq, tmp_path, ["Matrix"])                    # again: replaces its own layer
    model = next(e for e in ET.parse(xsq).getroot().iter("Element") if e.get("name") == "Matrix")
    assert len(model.findall("EffectLayer")) == 2


def test_without_tracks_or_audio_kicks_fall_back_to_beats_one_and_three(tmp_path):
    xsq = _show(tmp_path)
    res = bp.place_band(xsq, tmp_path, ["Matrix"])
    assert res[0].kick_source == "beats 1 and 3" and res[0].vocal_source.startswith("none")
    root = ET.parse(xsq).getroot()
    model = next(e for e in root.iter("Element") if e.get("name") == "Matrix")
    text = root.find("EffectDB")[int(model.findall("EffectLayer")[0][0].get("ref"))].text
    assert f"E_SLIDER_SHADERXYZZY_kick={((1 << 0) | (1 << 8)) * 100}," in text


def test_band_and_crew_keep_their_own_layers(tmp_path):
    from xlights_mcp.sprites import place
    xsq = _show(tmp_path)
    place.place_crew(xsq, tmp_path, ["Matrix"], shader=True)
    bp.place_band(xsq, tmp_path, ["Matrix"])
    place.place_crew(xsq, tmp_path, ["Matrix"], shader=True)
    bp.place_band(xsq, tmp_path, ["Matrix"])
    root = ET.parse(xsq).getroot()
    model = next(e for e in root.iter("Element") if e.get("name") == "Matrix")
    db = root.find("EffectDB")
    files = [db[int(layer[0].get("ref"))].text.split("IFS=")[1].split(",")[0].split("/")[-1]
             for layer in model.findall("EffectLayer") if len(layer)]
    assert sorted(files) == ["Dance Crew.fs", "Skeleton Band.fs"]


def test_band_shader_header_and_glsl_hygiene():
    src = bs.build_shader()
    head = json.loads(src[src.index("/*") + 2:src.index("*/")])
    assert head["DESCRIPTION"] == "xLights Audio2"
    for inp in head["INPUTS"]:
        assert inp["TYPE"] != "long" or ("LABELS" in inp and "VALUES" in inp), inp["NAME"]
    body = re.sub(r"//[^\n]*", "", src[src.index("*/") + 2:])
    assert not ({"half", "sample", "input", "output", "filter", "common", "smooth", "flat", "this"}
                & set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", body)))
    assert f"int LAYERS[{len(b.LAYERS) * b.W * b.H}]" in src


def test_band_settings_validate_masks():
    with pytest.raises(ValueError):
        bs.band_settings("x.fs", "male", 1 << 16, 0, 0.0, 4.0)
