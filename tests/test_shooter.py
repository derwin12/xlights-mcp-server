"""Sky Shooter: game rules, simulation across bars, the shader source and placement."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET

import pytest

from xlights_mcp.sprites import shooter as g
from xlights_mcp.sprites import shooter_place as sp
from xlights_mcp.sprites import shooter_shader as ss

K = lambda *slots: sum(1 << s for s in slots)  # noqa: E731


def test_kills_follow_kicks_in_kill_order_and_wait_for_the_fly_in():
    assert g.kills(K(0, 4, 8), g.ALL_ALIVE, entry=True) == [(4, g.KILL_ORDER[0]), (8, g.KILL_ORDER[1])]
    assert g.kills(K(0, 4), g.ALL_ALIVE, entry=False) == [(0, g.KILL_ORDER[0]), (4, g.KILL_ORDER[1])]
    alive = 1 << g.KILL_ORDER[-1]
    assert g.kills(K(1, 2, 3), alive, entry=False) == [(1, g.KILL_ORDER[-1])]


def test_simulate_carries_survivors_and_starts_new_waves():
    every_16th = (1 << 16) - 1
    states = g.simulate([K(4, 8), every_16th, every_16th, K(0)], [4, 4, 4, 4])
    assert states[0] == g.BarState(K(4, 8), g.ALL_ALIVE, 0, True, 0)
    assert bin(states[1].alive).count("1") == 10 and not states[1].entry and states[1].song_beat == 4
    assert states[2].wave == 1 and states[2].entry and states[2].alive == g.ALL_ALIVE      # 10 cleared in bar 2
    assert states[3].wave == 2 and states[3].entry                 # 12 kicks after the fly-in clear wave 1


def test_render_shows_formation_player_and_sparkle():
    cols = [(220, 30, 40), (30, 200, 80), (40, 120, 255)]
    st = g.BarState(K(4), g.ALL_ALIVE, 0, False, 0)
    img = g.render(st, 4.1 / 4, cols)                   # slot 4: the first kill sparkles
    e = g.KILL_ORDER[0]
    x, y = g.enemy_pos(e, 1, False, 1.0, 0)
    assert img.getpixel((x + 2, y)) == g.SPARK_W
    assert g.RED in [img.getpixel((xx, g.PLAYER_Y + 2)) for xx in range(g.PW)]
    before = g.render(st, 3.1 / 4, cols)
    later = g.render(st, 8.1 / 4, cols)
    ornament = cols[(e // g.COLS) % 3]
    assert before.getpixel((x + 2, y + 2)) == ornament and later.getpixel((x + 2, y + 2)) != ornament


def test_shader_source_hygiene_and_settings():
    src = ss.build_shader()
    head = json.loads(src[src.index("/*") + 2:src.index("*/")])
    assert head["DESCRIPTION"] == "xLights Audio2"
    for inp in head["INPUTS"]:
        assert inp["TYPE"] != "long" or ("LABELS" in inp and "VALUES" in inp), inp["NAME"]
    body = re.sub(r"//[^\n]*", "", src[src.index("*/") + 2:])
    assert not ({"half", "sample", "input", "output", "filter", "common", "smooth", "flat", "this"}
                & set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", body)))
    st = ss.shooter_settings("x.fs", g.BarState(K(0, 8), 4095, 3, True, 12), 1.5, 2.5)
    assert st["E_SLIDER_SHADERXYZZY_kick"] == str(K(0, 8) * 100) and st["E_CHECKBOX_SHADERXYZZY_entry"] == "1"
    assert st["E_SLIDER_SHADERXYZZY_songBeat"] == "1200" and st["E_SLIDER_SHADERXYZZY_barBeat"] == "150"
    with pytest.raises(ValueError):
        ss.shooter_settings("x.fs", g.BarState(0, 0, 0, False, 0), 0, 99)


XSQ = """<?xml version="1.0" encoding="UTF-8"?>
<xsequence><head><sequenceDuration>4.000</sequenceDuration><mediaFile></mediaFile></head>
<ColorPalettes/><EffectDB/><DisplayElements/>
<ElementEffects>
  <Element type="timing" name="Beats"><EffectLayer>{beats}</EffectLayer></Element>
  <Element type="timing" name="Kick Hits"><EffectLayer>{kicks}</EffectLayer></Element>
  <Element type="model" name="Matrix"><EffectLayer/></Element>
</ElementEffects></xsequence>"""
RGB = """<xrgb><models>
<model name="Matrix" DisplayAs="Matrix" NumStrings="60" NodesPerString="120" StrandsPerString="1" Vertical="false"/>
</models></xrgb>"""


def test_place_shooter_simulates_across_bars(tmp_path):
    beats = "".join(f'<Effect label="{i % 4 + 1}" startTime="{i * 400}" endTime="{i * 400 + 400}"/>' for i in range(8))
    kicks = "".join(f'<Effect startTime="{t}" endTime="{t + 10}"/>' for t in (0, 400, 800, 1600, 2000))
    (tmp_path / "song.xsq").write_text(XSQ.format(beats=beats, kicks=kicks), encoding="utf-8")
    (tmp_path / "xlights_rgbeffects.xml").write_text(RGB, encoding="utf-8")
    res = sp.place_shooter(tmp_path / "song.xsq", tmp_path, ["Matrix"])
    assert res[0].effects == 2 and res[0].kick_source == "Kick Hits track"
    assert (tmp_path / "Shaders" / "Sky Shooter.fs").exists()
    root = ET.parse(tmp_path / "song.xsq").getroot()
    model = next(e for e in root.iter("Element") if e.get("name") == "Matrix")
    texts = [root.find("EffectDB")[int(e.get("ref"))].text for e in model.findall("EffectLayer")[0]]
    # bar 1 kicks at slots 0, 4, 8 while flying in: 2 kills (slot 0 waits), so bar 2 starts with 10 alive
    second = re.search(r"alive=(\d+)", texts[1]).group(1)
    assert bin(int(second) // 100).count("1") == 10 and "songBeat=400," in texts[1]
    pal = root.find("ColorPalettes")[int(model.findall("EffectLayer")[0][0].get("palette"))].text
    assert pal.startswith("C_BUTTON_Palette1=#DC1E28")


def test_game_starts_fresh_where_it_is_first_shown(tmp_path):
    beats = "".join(f'<Effect label="{i % 4 + 1}" startTime="{i * 400}" endTime="{i * 400 + 400}"/>' for i in range(8))
    kicks = "".join(f'<Effect startTime="{t}" endTime="{t + 10}"/>' for t in (400, 800, 1200))
    secs = ('<Element type="timing" name="Sections"><EffectLayer><Effect label="Verse 1" startTime="0" '
            'endTime="1600"/><Effect label="Ending" startTime="1600" endTime="3200"/></EffectLayer></Element>')
    text = XSQ.format(beats=beats, kicks=kicks).replace("<ElementEffects>", "<ElementEffects>" + secs)
    (tmp_path / "song.xsq").write_text(text, encoding="utf-8")
    (tmp_path / "xlights_rgbeffects.xml").write_text(RGB, encoding="utf-8")
    res = sp.place_shooter(tmp_path / "song.xsq", tmp_path, ["Matrix"], section_track="Sections", off_sections=["verse"])
    assert res[0].effects == 1
    root = ET.parse(tmp_path / "song.xsq").getroot()
    model = next(e for e in root.iter("Element") if e.get("name") == "Matrix")
    text = root.find("EffectDB")[int(model.findall("EffectLayer")[0][0].get("ref"))].text
    assert f"alive={g.ALL_ALIVE * 100}," in text and "E_CHECKBOX_SHADERXYZZY_entry=1" in text   # a fresh wave
