"""Tests for create_beat_effect_sequence MCP tool."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from xlights_mcp.audio.beats import BeatMap
from xlights_mcp.xlights.xsq_reader import read_xsq_summary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_beat_map(n_beats: int = 16, tempo: float = 120.0) -> BeatMap:
    """Return a synthetic BeatMap with evenly-spaced beats."""
    interval = 60.0 / tempo  # seconds
    beat_times = [round(i * interval, 3) for i in range(n_beats)]
    return BeatMap(
        tempo=tempo,
        beat_times=beat_times,
        downbeat_times=beat_times[::4],
        onset_times=beat_times,
        beats_per_bar=4,
    )


def _fake_audio(n_beats: int = 16, tempo: float = 120.0, sr: int = 22050):
    """Return (y, sr) whose duration exactly covers n_beats so extrapolation doesn't fire."""
    # last beat at (n_beats-1)*interval; duration = last beat + one interval
    interval_s = 60.0 / tempo
    duration_s = n_beats * interval_s
    return np.zeros(int(duration_s * sr)), sr


def _make_fake_mp3(tmp_path: Path) -> Path:
    """Write a placeholder file so Path.exists() passes."""
    p = tmp_path / "test_song.mp3"
    p.write_bytes(b"FAKE")
    return p


def _call_tool(mp3_path, tmp_path, **kwargs):
    """Call create_beat_effect_sequence with the show folder wired to tmp_path."""
    from xlights_mcp.server import create_beat_effect_sequence

    fake_config = SimpleNamespace(
        active_show_path=tmp_path,
        shows=[SimpleNamespace(name="Test", path=tmp_path)],
        audio=SimpleNamespace(),
    )

    # detect_beats and librosa are imported inside the function body, so patch
    # them at their source modules rather than on the server module.
    with (
        patch("xlights_mcp.server.get_config", return_value=fake_config),
        patch("xlights_mcp.server._resolve_show", return_value=tmp_path),
        patch("xlights_mcp.audio.beats.detect_beats", return_value=_fake_beat_map()),
        patch("librosa.load", return_value=_fake_audio(n_beats=16, tempo=120.0)),
    ):
        return create_beat_effect_sequence(
            mp3_path=str(mp3_path),
            **kwargs,
        )


# ---------------------------------------------------------------------------
# Settings parsing
# ---------------------------------------------------------------------------

class TestCopyFormatParsing:
    """create_beat_effect_sequence strips C_* palette entries from effect_settings."""

    def test_e_and_t_params_kept(self, tmp_path):
        mp3 = _make_fake_mp3(tmp_path)
        result = _call_tool(
            mp3, tmp_path,
            sequence_name="out",
            models=["Tree 1"],
            effect_name="Shockwave",
            effect_settings=(
                "E_SLIDER_Shockwave_End_Radius=96,"
                "T_CHOICE_LayerMethod=Normal,"
                "C_BUTTON_Palette1=#ffffff,"
                "C_CHECKBOX_Palette1=1"
            ),
        )
        assert result["success"]
        root = ET.parse(tmp_path / "out.xsq").getroot()
        db_effects = root.findall(".//EffectDB/Effect")
        assert db_effects, "EffectDB should have an entry"
        settings_text = db_effects[0].text or ""
        assert "E_SLIDER_Shockwave_End_Radius=96" in settings_text
        assert "T_CHOICE_LayerMethod=Normal" in settings_text
        assert "C_BUTTON_Palette1" not in settings_text

    def test_no_settings_writes_clean_effect(self, tmp_path):
        mp3 = _make_fake_mp3(tmp_path)
        result = _call_tool(
            mp3, tmp_path,
            sequence_name="out",
            models=["Tree 1"],
            effect_name="Fire",
        )
        assert result["success"]


# ---------------------------------------------------------------------------
# Beat placement
# ---------------------------------------------------------------------------

class TestBeatPlacement:
    """Effects land on the correct beats."""

    def test_stride_2_offset_0_uses_even_indices(self, tmp_path):
        mp3 = _make_fake_mp3(tmp_path)
        result = _call_tool(
            mp3, tmp_path,
            sequence_name="out",
            models=["Tree 1"],
            effect_name="Shockwave",
            beat_stride=2,
            beat_offset=0,
        )
        assert result["success"]
        root = ET.parse(tmp_path / "out.xsq").getroot()
        effects = root.findall(".//ElementEffects/Element[@name='Tree 1']/EffectLayer/Effect")
        # 16 beats, stride 2, offset 0 → 8 effects
        assert len(effects) == 8

    def test_stride_1_uses_every_beat(self, tmp_path):
        mp3 = _make_fake_mp3(tmp_path)
        result = _call_tool(
            mp3, tmp_path,
            sequence_name="out",
            models=["Tree 1"],
            effect_name="Chase",
            beat_stride=1,
        )
        root = ET.parse(tmp_path / "out.xsq").getroot()
        effects = root.findall(".//ElementEffects/Element[@name='Tree 1']/EffectLayer/Effect")
        assert len(effects) == 16

    def test_alternating_models_get_opposite_beats(self, tmp_path):
        mp3 = _make_fake_mp3(tmp_path)
        result = _call_tool(
            mp3, tmp_path,
            sequence_name="out",
            models=["Tree 1"],
            effect_name="Shockwave",
            beat_stride=2,
            beat_offset=0,
            alternating_models=["TreeStar 1"],
        )
        assert result["success"]
        root = ET.parse(tmp_path / "out.xsq").getroot()

        tree_fx = root.findall(".//ElementEffects/Element[@name='Tree 1']/EffectLayer/Effect")
        star_fx = root.findall(".//ElementEffects/Element[@name='TreeStar 1']/EffectLayer/Effect")

        # Both get 8 effects from 16 beats
        assert len(tree_fx) == 8
        assert len(star_fx) == 8

        # No shared start times — they truly alternate
        tree_starts = {int(e.get("startTime")) for e in tree_fx}
        star_starts = {int(e.get("startTime")) for e in star_fx}
        assert tree_starts.isdisjoint(star_starts)

    def test_alternating_covers_all_beats(self, tmp_path):
        mp3 = _make_fake_mp3(tmp_path)
        _call_tool(
            mp3, tmp_path,
            sequence_name="out",
            models=["Tree 1"],
            effect_name="Shockwave",
            beat_stride=2,
            beat_offset=0,
            alternating_models=["TreeStar 1"],
        )
        root = ET.parse(tmp_path / "out.xsq").getroot()
        tree_starts = {int(e.get("startTime")) for e in root.findall(
            ".//ElementEffects/Element[@name='Tree 1']/EffectLayer/Effect")}
        star_starts = {int(e.get("startTime")) for e in root.findall(
            ".//ElementEffects/Element[@name='TreeStar 1']/EffectLayer/Effect")}
        # Together they cover all 16 beats
        assert len(tree_starts | star_starts) == 16


# ---------------------------------------------------------------------------
# Timing tracks
# ---------------------------------------------------------------------------

class TestTimingTracks:
    """Beats and Bars timing tracks have correct labels."""

    def _get_timing_labels(self, root: ET.Element, track_name: str) -> list[str]:
        el = root.find(f".//ElementEffects/Element[@name='{track_name}']")
        if el is None:
            return []
        return [e.get("label", "") for e in el.findall(".//Effect")]

    def test_beats_track_labels_cycle_1234(self, tmp_path):
        mp3 = _make_fake_mp3(tmp_path)
        _call_tool(mp3, tmp_path, sequence_name="out",
                   models=["Tree 1"], effect_name="Shockwave")
        root = ET.parse(tmp_path / "out.xsq").getroot()
        labels = self._get_timing_labels(root, "Beats")
        assert labels[:8] == ["1", "2", "3", "4", "1", "2", "3", "4"]

    def test_bars_track_labels_are_sequential(self, tmp_path):
        mp3 = _make_fake_mp3(tmp_path)
        _call_tool(mp3, tmp_path, sequence_name="out",
                   models=["Tree 1"], effect_name="Shockwave")
        root = ET.parse(tmp_path / "out.xsq").getroot()
        labels = self._get_timing_labels(root, "Bars")
        # 16 beats → 4 bars
        assert labels == ["1", "2", "3", "4"]

    def test_no_tracks_when_disabled(self, tmp_path):
        mp3 = _make_fake_mp3(tmp_path)
        _call_tool(mp3, tmp_path, sequence_name="out",
                   models=["Tree 1"], effect_name="Shockwave",
                   include_beats_track=False, include_bars_track=False)
        root = ET.parse(tmp_path / "out.xsq").getroot()
        assert self._get_timing_labels(root, "Beats") == []
        assert self._get_timing_labels(root, "Bars") == []

    def test_last_bar_ends_one_interval_after_last_beat(self, tmp_path):
        mp3 = _make_fake_mp3(tmp_path)
        _call_tool(mp3, tmp_path, sequence_name="out",
                   models=["Tree 1"], effect_name="Shockwave")
        root = ET.parse(tmp_path / "out.xsq").getroot()
        bars_el = root.find(".//ElementEffects/Element[@name='Bars']")
        last_bar = list(bars_el.findall(".//Effect"))[-1]
        last_beat_el = list(
            root.find(".//ElementEffects/Element[@name='Beats']").findall(".//Effect")
        )[-1]
        # last bar end > last beat start
        assert int(last_bar.get("endTime")) > int(last_beat_el.get("startTime"))


# ---------------------------------------------------------------------------
# Return value
# ---------------------------------------------------------------------------

class TestReturnValue:
    def test_returns_expected_keys(self, tmp_path):
        mp3 = _make_fake_mp3(tmp_path)
        result = _call_tool(mp3, tmp_path, sequence_name="out",
                            models=["Tree 1"], effect_name="Shockwave")
        assert result["success"] is True
        assert Path(result["sequence"]).exists()
        assert result["tempo_bpm"] == pytest.approx(120.0)
        assert result["beats_total"] >= result["beats_detected"]
        assert result["effects_placed"] > 0

    def test_file_not_found_returns_error(self, tmp_path):
        from xlights_mcp.server import create_beat_effect_sequence
        from types import SimpleNamespace

        fake_config = SimpleNamespace(active_show_path=tmp_path, shows=[], audio=SimpleNamespace())
        with (
            patch("xlights_mcp.server.get_config", return_value=fake_config),
            patch("xlights_mcp.server._resolve_show", return_value=tmp_path),
        ):
            result = create_beat_effect_sequence(
                mp3_path=str(tmp_path / "nonexistent.mp3"),
                sequence_name="out",
                models=["Tree 1"],
                effect_name="Shockwave",
            )
        assert "error" in result
