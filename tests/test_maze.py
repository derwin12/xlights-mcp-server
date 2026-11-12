"""Maze Chase: the maze, the runner's tour and steps, the shader source and placement."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET

from xlights_mcp.sprites import maze as m
from xlights_mcp.sprites import maze_place as mp
from xlights_mcp.sprites import maze_shader as ms

K = lambda *slots: sum(1 << s for s in slots)  # noqa: E731


def test_maze_is_a_perfect_maze_and_the_tour_visits_every_cell_by_neighbouring_moves():
    n = m.CW * m.CH
    assert len(m.PASSAGES) == n - 1                       # a spanning tree
    assert set(m.TOUR) == set(range(n)) and m.LAP == 2 * (n - 1)
    for a, b in zip(m.TOUR, m.TOUR[1:] + m.TOUR[:1]):     # every move (and the loop back) goes through a passage
        assert (min(a, b), max(a, b)) in m.PASSAGES


def test_walls_close_the_outside_and_open_the_passages():
    w = m.WALLS
    assert all(w[m.OY][m.OX + x] for x in range(m.CW * 4 + 1))
    (a, b) = next(iter(sorted(m.PASSAGES)))
    ax, ay = m.cell_xy(a)
    if b == a + 1:
        assert not w[ay + 1][ax + 3]                      # the wall between them is open
    else:
        assert not w[ay + 3][ax + 1]


def test_steps_and_dashes():
    assert m.steps_in_bar(0, 16) == 16
    assert m.steps_in_bar(K(0, 4), 16) == 18 and m.steps_in_bar(K(0, 4), 1) == 2
    assert m.runner_q(0, K(1), 4 + 2) == 4 + 2 * 2           # mid-dash: 1 step done, then 2 quarter steps per quarter


def test_peppermints_disappear_as_the_runner_passes_and_return_next_maze():
    cols = [(220, 30, 40), (30, 200, 80), (40, 120, 255)]
    c = m.TOUR[10]
    x, y = m.cell_xy(c)
    early = m.render(0, 0, 0.1 / 4, cols)
    later = m.render(12, 0, 0.1 / 4, cols)               # step 12: past the tour's 10th cell
    next_maze = m.render(m.LAP, 0, 0.1 / 4, cols)
    mint = m.MINT_RED if c % 2 == 0 else m.WHITE
    assert early.getpixel((x + 1, y + 1)) == mint and later.getpixel((x + 1, y + 1)) != mint
    assert next_maze.getpixel((x + 1, y + 1)) == mint
    assert next_maze.getpixel((m.OX, m.OY)) == cols[1]   # second maze: second wall colour


def test_shader_source_hygiene_and_settings():
    src = ms.build_shader()
    head = json.loads(src[src.index("/*") + 2:src.index("*/")])
    assert head["DESCRIPTION"] == "xLights Audio2"
    for inp in head["INPUTS"]:
        assert inp["TYPE"] != "long" or ("LABELS" in inp and "VALUES" in inp), inp["NAME"]
    body = re.sub(r"//[^\n]*", "", src[src.index("*/") + 2:])
    assert not ({"half", "sample", "input", "output", "filter", "common", "smooth", "flat", "this"}
                & set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", body)))
    st = ms.maze_settings("x.fs", 123, K(0, 8), 0.5, 3.5)
    assert st["E_SLIDER_SHADERXYZZY_startStep"] == "12300" and st["E_SLIDER_SHADERXYZZY_barBeat"] == "50"


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


def test_place_maze_counts_steps_across_bars(tmp_path):
    beats = "".join(f'<Effect label="{i % 4 + 1}" startTime="{i * 400}" endTime="{i * 400 + 400}"/>' for i in range(8))
    kicks = "".join(f'<Effect startTime="{t}" endTime="{t + 10}"/>' for t in (0, 400, 800))
    (tmp_path / "song.xsq").write_text(XSQ.format(beats=beats, kicks=kicks), encoding="utf-8")
    (tmp_path / "xlights_rgbeffects.xml").write_text(RGB, encoding="utf-8")
    res = mp.place_maze(tmp_path / "song.xsq", tmp_path, ["Matrix"])
    assert res[0].effects == 2 and res[0].kick_source == "Kick Hits track"
    assert (tmp_path / "Shaders" / "Maze Chase.fs").exists()
    root = ET.parse(tmp_path / "song.xsq").getroot()
    model = next(e for e in root.iter("Element") if e.get("name") == "Matrix")
    texts = [root.find("EffectDB")[int(e.get("ref"))].text for e in model.findall("EffectLayer")[0]]
    assert "startStep=0," in texts[0] and f"startStep={(16 + 3) * 100}," in texts[1]   # 16 slots + 3 dashes
