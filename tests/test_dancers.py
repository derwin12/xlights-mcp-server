"""Pixel dance crew: poses, GIF frame counts, bar grouping and placement on an .xsq."""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET

import pytest
from PIL import Image

from xlights_mcp.sprites import dancers as d
from xlights_mcp.sprites import place


def test_every_routine_pose_exists_and_moves_mirror():
    for name, bars in d.ROUTINES.items():
        assert len(d.timeline(name, 32)) == 32
    for side in ("claw", "lunge", "kick", "point", "wave", "shuffle_out", "shuffle_kick", "knee_up", "robot",
                 "floss", "sprinkler"):
        assert f"{side}_left" in d.POSES and f"{side}_right" in d.POSES
    assert d.POSES["lunge_right"] == d.POSES["lunge_left"].mirrored()


def test_slide_moves_the_whole_dancer_and_mirrors():
    shirt = d.SHIRTS["red"]
    still = d.draw_dancer(d.Pose((3, 7), (3, 9), (9, 7), (9, 9)), shirt)
    slid = d.draw_dancer(d.Pose((3, 7), (3, 9), (9, 7), (9, 9), slide=2), shirt)
    assert slid.getpixel((7, 15)) == still.getpixel((5, 15)) == d.BONE     # left foot moved 2 right
    assert slid.getpixel((8, 1)) == still.getpixel((6, 1))                 # and the head with it
    assert d.POSES["shuffle_out_left"].slide == -d.POSES["shuffle_out_right"].slide == -1


def test_female_figure_has_hair_and_a_skirt():
    hair, dress = d.HAIR["pink"], d.SHIRTS["teal"]
    im = d.draw_dancer(d.POSES["stand"], dress, figure="female", hair=hair)
    assert im.getpixel((3, 2)) == im.getpixel((9, 2)) == im.getpixel((6, 0)) == hair
    assert im.getpixel((9, 10)) == dress                                    # skirt flares past the hips
    male = d.draw_dancer(d.POSES["stand"], dress)
    assert male.getpixel((3, 2)) == d.BLACK and male.getpixel((9, 10)) == d.BLACK


def test_crew_figures_and_hair_contrast():
    mixed = d.crew_from_style(4, figure="mixed")
    assert [x.figure for x in mixed] == ["female", "male", "female", "male"]
    girls = d.crew_from_style(8, figure="female", shirts=["pink"])
    assert all(x.hair != "pink" for x in girls)
    with pytest.raises(ValueError):
        d.crew_from_style(2, figure="robot")


def test_hex_colours_and_hair_avoids_a_matching_dress():
    assert d.colour("#00E0FF") == (0, 224, 255)
    with pytest.raises(ValueError):
        d.colour("mauve")
    hot_pink = d.crew_from_style(3, figure="female", shirts=["#FF00A0"])
    assert all(x.hair not in ("pink", "violet") for x in hot_pink)


def test_section_map_and_label_matching():
    m = place.parse_section_map("Intro=wave, Verse=robot,Chorus=shuffle,Chorus 3=floss,Ending=none")
    assert m["intro"] == "wave" and m["ending"] == "none"
    assert place.section_key("Chorus 2", m) == "chorus"
    assert place.section_key("Chorus 3", m) == "chorus 3"
    assert place.section_key("Bridge", m) is None
    with pytest.raises(ValueError):
        place.parse_section_map("Verse")


def test_plan_bars_switches_routine_and_restarts_each_section():
    bars = [[(i * 400 + j * 100, i * 400 + j * 100 + 100) for j in range(4)] for i in range(5)]
    sections = [(0, 800, "Verse 1"), (800, 1600, "Chorus 1"), (1600, 2000, "Ending")]
    plans = place.plan_bars(bars, "party", None, sections, {"verse": "robot", "chorus": "shuffle", "ending": "none"},
                            {"chorus": ["teal", "pink"]})
    assert [p.routine for p in plans] == ["robot", "robot", "shuffle", "shuffle", None]
    assert [p.beat for p in plans] == [0, 4, 0, 4, 0]
    assert plans[0].shirts is None and plans[2].shirts == ["teal", "pink"]


def test_stage_frame_fills_the_matrix_and_swaps_lights_each_beat():
    from xlights_mcp.sprites.stage import FLOOR, light_colours, stage_frame
    crew = d.Crew(d.crew_from_style(3, shirts=["purple", "teal"]))
    img = d.crew_frame(crew, ["stand"], 0)
    cols = light_colours(crew)
    assert len(cols) == 2
    f0, f1 = stage_frame(img, (40, 30), 1, cols, 0), stage_frame(img, (40, 30), 1, cols, 1)
    assert f0.size == (40, 30)
    assert f0.getpixel((0, 0)) == cols[0] and f1.getpixel((0, 0)) == cols[1]
    assert FLOOR in [f0.getpixel((x, 29)) for x in range(40)]
    assert f0.getpixel((19, 13 + 2)) == img.getpixel((19 - 0, 2))       # dancers drawn over the beams


def test_timeline_rejects_unknown_pose():
    with pytest.raises(ValueError, match="moonwalk"):
        d.timeline([["stand", "moonwalk"]], 4)


def test_mirrored_drawing_is_a_flip():
    shirt = d.SHIRTS["red"]
    a = d.draw_dancer(d.POSES["kick_right"], shirt)
    b = d.draw_dancer(d.POSES["kick_left"], shirt)
    lit = lambda im: im.convert("L").point(lambda v: 255 if v else 0).tobytes()  # noqa: E731
    assert lit(a.transpose(Image.FLIP_LEFT_RIGHT)) == lit(b)


def test_gif_keeps_one_frame_per_beat_when_poses_repeat():
    crew = d.Crew(d.crew_from_style(2, "unison"))
    frames = d.bar_frames(crew, ["stand"] * 4, 0, 4)
    buf = io.BytesIO()
    d.save_gif(frames, buf)
    buf.seek(0)
    gif = Image.open(buf)
    assert gif.n_frames == 4
    gif.seek(2)
    assert gif.convert("RGB").getpixel((6, 2)) == d.BONE


def test_canon_dancers_stand_until_their_entry():
    crew = d.Crew(d.crew_from_style(2, "canon"))
    f0 = d.crew_frame(crew, ["arms_up"] * 4, 0)
    lone = d.draw_dancer(d.POSES["stand"], *crew.dancers[1].colours())
    assert f0.crop((d.W, 0, 2 * d.W, d.H)).tobytes() == lone.tobytes()


def test_scale_and_crew_size():
    crew = d.Crew(d.crew_from_style(3), scale=3)
    assert crew.size == (3 * d.W * 3, d.H * 3)
    assert d.crew_frame(crew, ["stand"], 0).size == crew.size
    assert place.fit_crew((40, 30)) == (3, 1)
    assert place.fit_crew((120, 60)) == (3, 3)
    assert place.fit_crew((120, 30)) == (9, 1)


def test_group_bars_follows_downbeat_labels():
    beats = [(0, 100, "3"), (100, 200, "4"), (200, 300, "1"), (300, 400, "2"), (400, 500, "1")]
    assert place.group_bars(beats) == [[(0, 100), (100, 200)], [(200, 300), (300, 400)], [(400, 500)]]
    plain = [(i * 10, i * 10 + 10, "") for i in range(6)]
    assert [len(b) for b in place.group_bars(plain, 4)] == [4, 2]


XSQ = """<?xml version="1.0" encoding="UTF-8"?>
<xsequence><head><sequenceDuration>4.000</sequenceDuration></head>
<ColorPalettes/><EffectDB/><DisplayElements/>
<ElementEffects>
  <Element type="timing" name="Beats"><EffectLayer>{beats}</EffectLayer></Element>
  <Element type="model" name="Matrix 2"><EffectLayer><Effect ref="0" name="Off" startTime="0" endTime="100"/></EffectLayer></Element>
</ElementEffects></xsequence>"""
RGB = """<xrgb><models>
<model name="Matrix 2" DisplayAs="Matrix" NumStrings="30" NodesPerString="40" StrandsPerString="1" Vertical="false"/>
</models></xrgb>"""


def _show(tmp_path):
    beats = "".join(f'<Effect label="{i % 4 + 1}" startTime="{i * 500}" endTime="{i * 500 + 500}"/>'
                    for i in range(8))
    (tmp_path / "song.xsq").write_text(XSQ.format(beats=beats), encoding="utf-8")
    (tmp_path / "xlights_rgbeffects.xml").write_text(RGB, encoding="utf-8")
    return tmp_path / "song.xsq"


def test_place_crew_adds_one_top_layer_per_run(tmp_path):
    xsq = _show(tmp_path)
    assert place.model_size(tmp_path, "Matrix 2") == (40, 30)
    for _ in range(2):
        res = place.place_crew(xsq, tmp_path, ["Matrix 2"], routine="party", frames_per_beat=2)
    assert res[0].bars == 2 and res[0].dancers == 3
    root = ET.parse(xsq).getroot()
    model = next(e for e in root.iter("Element") if e.get("name") == "Matrix 2")
    layers = model.findall("EffectLayer")
    assert len(layers) == 2                      # ours on top, the original below
    top = layers[0].findall("Effect")
    assert [(e.get("startTime"), e.get("endTime")) for e in top] == [("0", "2000"), ("2000", "4000")]
    settings = root.find("EffectDB")[int(top[0].get("ref"))].text
    assert "E_CHECKBOX_LoopGIF=0" in settings and "Images/Dancers/" in settings
    gif = tmp_path / settings.split("E_TEXTCTRL_Pictures_Filename=")[1].split(",")[0]
    with Image.open(gif) as im:
        assert im.size == (39, 17) and im.n_frames == 8


def test_place_crew_adds_a_model_missing_from_the_sequence(tmp_path):
    xsq = _show(tmp_path)
    xsq.write_text(xsq.read_text(encoding="utf-8").replace('name="Matrix 2"', 'name="MH-1"'), encoding="utf-8")
    place.place_crew(xsq, tmp_path, ["Matrix 2"])
    root = ET.parse(xsq).getroot()
    assert [e.get("name") for e in root.find("DisplayElements")] == ["Matrix 2"]
    model = next(e for e in root.find("ElementEffects") if e.get("name") == "Matrix 2")
    assert len(model.findall("EffectLayer")) == 1


def test_remove_crew_keeps_the_models_own_effects(tmp_path):
    xsq = _show(tmp_path)
    place.place_crew(xsq, tmp_path, ["Matrix 2"])
    assert place.remove_crew(xsq, ["Matrix 2"]) == ["Matrix 2"]
    model = next(e for e in ET.parse(xsq).getroot().iter("Element") if e.get("name") == "Matrix 2")
    layers = model.findall("EffectLayer")
    assert len(layers) == 1 and layers[0][0].get("name") == "Off"
    assert place.remove_crew(xsq, ["Matrix 2"]) == []


def test_rerun_finds_the_crew_layer_below_a_newer_top_layer(tmp_path):
    xsq = _show(tmp_path)
    place.place_crew(xsq, tmp_path, ["Matrix 2"])
    text = xsq.read_text(encoding="utf-8")
    on_top = '<Element type="model" name="Matrix 2"><EffectLayer><Effect ref="0" name="On" startTime="0" endTime="50"/></EffectLayer>'
    xsq.write_text(text.replace('<Element type="model" name="Matrix 2">', on_top, 1), encoding="utf-8")
    place.place_crew(xsq, tmp_path, ["Matrix 2"])
    model = next(e for e in ET.parse(xsq).getroot().iter("Element") if e.get("name") == "Matrix 2")
    names = [layer[0].get("name") for layer in model.findall("EffectLayer")]
    assert names == ["Pictures", "On", "Off"]


def test_remove_crew_drops_a_model_that_was_only_there_for_it(tmp_path):
    xsq = _show(tmp_path)
    xsq.write_text(xsq.read_text(encoding="utf-8").replace('name="Matrix 2"', 'name="MH-1"'), encoding="utf-8")
    place.place_crew(xsq, tmp_path, ["Matrix 2"])
    place.remove_crew(xsq, ["Matrix 2"])
    root = ET.parse(xsq).getroot()
    assert all(e.get("name") != "Matrix 2" for e in root.iter("Element"))


def test_place_crew_skips_a_matrix_showing_video(tmp_path):
    xsq = _show(tmp_path)
    place.place_crew(xsq, tmp_path, ["Matrix 2"])
    xsq.write_text(xsq.read_text(encoding="utf-8").replace('name="Off"', 'name="Video"'), encoding="utf-8")
    res = place.place_crew(xsq, tmp_path, ["Matrix 2"])
    assert res[0].skipped and res[0].bars == 0
    model = next(e for e in ET.parse(xsq).getroot().iter("Element") if e.get("name") == "Matrix 2")
    assert [layer[0].get("name") for layer in model.findall("EffectLayer")] == ["Video"]
    place.place_crew(xsq, tmp_path, ["Matrix 2"], over_video=True)
    model = next(e for e in ET.parse(xsq).getroot().iter("Element") if e.get("name") == "Matrix 2")
    assert [layer[0].get("name") for layer in model.findall("EffectLayer")] == ["Pictures", "Video"]


def test_place_crew_by_section_leaves_none_sections_empty(tmp_path):
    xsq = _show(tmp_path)
    secs = ('<Element type="timing" name="Sections"><EffectLayer>'
            '<Effect label="Verse 1" startTime="0" endTime="2000"/><Effect label="Ending" startTime="2000" '
            'endTime="4000"/></EffectLayer></Element>')
    xsq.write_text(xsq.read_text(encoding="utf-8").replace("<ElementEffects>", "<ElementEffects>" + secs),
                   encoding="utf-8")
    res = place.place_crew(xsq, tmp_path, ["Matrix 2"], section_track="Sections",
                           section_routines={"verse": "robot", "ending": "none"})
    assert res[0].bars == 1
    model = next(e for e in ET.parse(xsq).getroot().iter("Element") if e.get("name") == "Matrix 2")
    top = model.findall("EffectLayer")[0].findall("Effect")
    assert [(e.get("startTime"), e.get("endTime")) for e in top] == [("0", "2000")]
    with pytest.raises(ValueError):
        place.place_crew(xsq, tmp_path, ["Matrix 2"], section_track="Sections", section_routines={"verse": "moonwalk"})


def test_place_crew_with_stage_writes_matrix_sized_gifs(tmp_path):
    xsq = _show(tmp_path)
    place.place_crew(xsq, tmp_path, ["Matrix 2"], stage=True)
    root = ET.parse(xsq).getroot()
    model = next(e for e in root.iter("Element") if e.get("name") == "Matrix 2")
    ref = int(model.findall("EffectLayer")[0][0].get("ref"))
    rel = root.find("EffectDB")[ref].text.split("E_TEXTCTRL_Pictures_Filename=")[1].split(",")[0]
    assert "-stage-" in rel
    with Image.open(tmp_path / rel) as im:
        assert im.size == (40, 30) and im.n_frames == 4


def test_shader_source_carries_every_pose_and_routine():
    import json as _json

    from xlights_mcp.sprites import shader
    src = shader.build_shader()
    head = _json.loads(src[src.index("/*") + 2:src.index("*/")])
    assert head["DESCRIPTION"] == "xLights Audio2"          # gives the shader the song's loudness
    names = {i["NAME"]: i for i in head["INPUTS"]}
    assert names["routine"]["LABELS"] == [r.title() for r in d.ROUTINES]
    assert f"const int NPOSES = {len(d.POSES)};" in src
    assert f"float POSES[{len(d.POSES) * 19}]" in src
    assert f"int ROUTINES[{len(d.ROUTINES) * 16}]" in src


def test_place_crew_with_shader_writes_the_shader_and_one_effect_per_bar(tmp_path):
    xsq = _show(tmp_path)
    place.place_crew(xsq, tmp_path, ["Matrix 2"], routine="shuffle", figure="female", style="mirror",
                     shirts=["#00E0FF", "pink"], shader=True, smoothing=0.5)
    assert (tmp_path / "Shaders" / "Dance Crew.fs").exists()
    root = ET.parse(xsq).getroot()
    model = next(e for e in root.iter("Element") if e.get("name") == "Matrix 2")
    top = model.findall("EffectLayer")[0].findall("Effect")
    assert [e.get("name") for e in top] == ["Shader", "Shader"]
    s1 = root.find("EffectDB")[int(top[1].get("ref"))].text
    for part in ("E_CHOICE_SHADERXYZZY_routine=Shuffle", "E_CHOICE_SHADERXYZZY_figure=Female",
                 "E_CHOICE_SHADERXYZZY_style=Mirror", "E_SLIDER_SHADERXYZZY_startBeat=400",
                 "E_SLIDER_SHADERXYZZY_beats=400", "E_SLIDER_SHADERXYZZY_smoothing=50", "E_CHOICE_SHADERXYZZY_dancers=3"):
        assert part in s1
    pal = root.find("ColorPalettes")[int(top[0].get("palette"))].text
    assert pal.startswith("C_BUTTON_Palette1=#00E0FF") and "C_BUTTON_Palette3=#00E0FF" in pal
    place.place_crew(xsq, tmp_path, ["Matrix 2"])               # switching back to GIFs replaces the layer
    model = next(e for e in ET.parse(xsq).getroot().iter("Element") if e.get("name") == "Matrix 2")
    assert [layer[0].get("name") for layer in model.findall("EffectLayer")] == ["Pictures", "Off"]
    with pytest.raises(ValueError, match="per_section"):
        place.place_crew(xsq, tmp_path, ["Matrix 2"], per_section=True)


def test_shader_uses_no_glsl_reserved_words_and_every_input_gets_a_control():
    # Vulkan GLSL (glslang) rejects reserved words that desktop OpenGL drivers let through ("half" did that).
    import re

    from xlights_mcp.sprites import shader
    src = shader.build_shader()
    body = re.sub(r"//[^\n]*", "", src[src.index("*/") + 2:])
    reserved = {"half", "fixed", "sample", "input", "output", "filter", "common", "partition", "active", "superp",
                "long", "short", "double", "unsigned", "hvec2", "fvec2", "sizeof", "cast", "namespace", "using",
                "external", "interface", "union", "enum", "typedef", "template", "this", "packed", "goto", "inline",
                "noinline", "volatile", "public", "static", "extern", "resource", "attribute", "varying", "subroutine",
                "buffer", "shared", "precise", "smooth", "flat", "patch", "noperspective", "sampler", "image"}
    used = set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", body))
    assert not (used & reserved), used & reserved
    import json as _json
    head = _json.loads(src[src.index("/*") + 2:src.index("*/")])
    for inp in head["INPUTS"]:
        # xLights' panel has no control for a "long" without LABELS/VALUES
        assert inp["TYPE"] != "long" or ("LABELS" in inp and "VALUES" in inp), inp["NAME"]


def test_shader_takes_the_stage_setting(tmp_path):
    xsq = _show(tmp_path)
    place.place_crew(xsq, tmp_path, ["Matrix 2"], shader=True, stage=True)
    root = ET.parse(xsq).getroot()
    model = next(e for e in root.iter("Element") if e.get("name") == "Matrix 2")
    text = root.find("EffectDB")[int(model.findall("EffectLayer")[0][0].get("ref"))].text
    assert "E_CHECKBOX_SHADERXYZZY_stage=1" in text


def test_stage_hash_is_the_fixed_uint32_hash_the_shader_uses():
    # Pinned values: the shader's hash32 does the same steps on uint, so a change here breaks GIF/shader parity.
    from xlights_mcp.sprites.stage import hash32
    assert [hash32(v) for v in (0, 1, 64, 123456789)] == [3232319850, 663891101, 3318304950, 2974685137]


def test_per_section_merges_bars_into_one_effect_per_section():
    bars = [[(i * 100 + j * 25, i * 100 + j * 25 + 25) for j in range(4)] for i in range(4)]
    one = place.merge_sections(place.plan_bars(bars, "party", None))
    assert len(one) == 1 and len(one[0].beats) == 16 and one[0].beat == 0
    sections = [(0, 200, "Verse 1"), (200, 400, "Chorus 1")]
    two = place.merge_sections(place.plan_bars(bars, "party", None, sections, {"chorus": "robot"}))
    assert [(p.routine, len(p.beats), p.beat) for p in two] == [("party", 8, 0), ("robot", 8, 0)]
    long = [[(i * 100 + j * 25, i * 100 + j * 25 + 25) for j in range(4)] for i in range(40)]   # 160 beats
    split = place.merge_sections(place.plan_bars(long, "party", None))
    assert [len(p.beats) for p in split] == [64, 64, 32] and [p.beat for p in split] == [0, 64, 128]


def test_section_dancer_counts_change_the_crew_and_zero_means_none():
    bars = [[(i * 400 + j * 100, i * 400 + j * 100 + 100) for j in range(4)] for i in range(3)]
    sections = [(0, 400, "Intro"), (400, 800, "Chorus 1"), (800, 1200, "Bridge")]
    plans = place.plan_bars(bars, "party", None, sections, section_dancers={"intro": 1, "chorus": 3, "bridge": 0})
    assert [p.dancers for p in plans] == [1, 3, 0]
    assert [p.routine for p in plans] == ["party", "party", None]


def test_place_crew_with_section_counts(tmp_path):
    xsq = _show(tmp_path)
    secs = ('<Element type="timing" name="Sections"><EffectLayer>'
            '<Effect label="Verse 1" startTime="0" endTime="2000"/><Effect label="Chorus 1" startTime="2000" '
            'endTime="4000"/></EffectLayer></Element>')
    xsq.write_text(xsq.read_text(encoding="utf-8").replace("<ElementEffects>", "<ElementEffects>" + secs),
                   encoding="utf-8")
    res = place.place_crew(xsq, tmp_path, ["Matrix 2"], section_track="Sections",
                           section_dancers={"verse": 1, "chorus": 3}, shader=True)
    assert res[0].dancers == 3
    root = ET.parse(xsq).getroot()
    model = next(e for e in root.iter("Element") if e.get("name") == "Matrix 2")
    texts = [root.find("EffectDB")[int(e.get("ref"))].text for e in model.findall("EffectLayer")[0]]
    assert "E_CHOICE_SHADERXYZZY_dancers=1" in texts[0] and "E_CHOICE_SHADERXYZZY_dancers=3" in texts[1]
    place.place_crew(xsq, tmp_path, ["Matrix 2"], section_track="Sections", section_dancers={"verse": 1})
    gifs = sorted((tmp_path / "Images" / "Dancers").glob("*.gif"))
    assert {Image.open(g).size for g in gifs} == {(13, 17), (39, 17)}


def test_free_pieces_cut_around_pictures():
    assert place.free_pieces(0, 1000, []) == [(0, 1000)]
    assert place.free_pieces(0, 1000, [(200, 400), (600, 700)]) == [(0, 200), (400, 600), (700, 1000)]
    assert place.free_pieces(0, 1000, [(-50, 300), (900, 2000)]) == [(300, 900)]
    assert place.free_pieces(0, 1000, [(0, 1000)]) == []


def _with_picture(xsq, start, end):
    text = xsq.read_text(encoding="utf-8").replace(
        '<Effect ref="0" name="Off" startTime="0" endTime="100"/>',
        f'<Effect ref="0" name="Off" startTime="0" endTime="100"/><Effect ref="0" name="Pictures" '
        f'startTime="{start}" endTime="{end}"/>')
    xsq.write_text(text, encoding="utf-8")


def test_shader_crew_steps_aside_for_the_models_pictures(tmp_path):
    xsq = _show(tmp_path)
    _with_picture(xsq, 2500, 3000)                      # one beat inside the second bar (2000-4000)
    place.place_crew(xsq, tmp_path, ["Matrix 2"], shader=True)
    root = ET.parse(xsq).getroot()
    model = next(e for e in root.iter("Element") if e.get("name") == "Matrix 2")
    top = model.findall("EffectLayer")[0].findall("Effect")
    assert [(e.get("startTime"), e.get("endTime")) for e in top] == [("0", "2000"), ("2000", "2500"), ("3000", "4000")]
    texts = [root.find("EffectDB")[int(e.get("ref"))].text for e in top]
    assert "E_SLIDER_SHADERXYZZY_startBeat=400," in texts[1] and "E_SLIDER_SHADERXYZZY_beats=100," in texts[1]
    assert "E_SLIDER_SHADERXYZZY_startBeat=600," in texts[2] and "E_SLIDER_SHADERXYZZY_beats=200," in texts[2]
    place.place_crew(xsq, tmp_path, ["Matrix 2"], shader=True, over_pictures=True)
    model = next(e for e in ET.parse(xsq).getroot().iter("Element") if e.get("name") == "Matrix 2")
    assert len(model.findall("EffectLayer")[0]) == 2


def test_gif_crew_leaves_out_bars_with_pictures(tmp_path):
    xsq = _show(tmp_path)
    _with_picture(xsq, 2500, 3000)
    res = place.place_crew(xsq, tmp_path, ["Matrix 2"])
    assert res[0].bars == 1


def test_place_crew_rejects_crew_too_wide(tmp_path):
    xsq = _show(tmp_path)
    with pytest.raises(ValueError, match="need"):
        place.place_crew(xsq, tmp_path, ["Matrix 2"], dancers=4)
