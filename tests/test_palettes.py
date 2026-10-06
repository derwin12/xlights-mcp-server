"""Tests for palette suggestion based on song title and audio feel."""

from __future__ import annotations

from xlights_mcp.xlights.palettes import (
    classify_song_energy,
    infer_theme_from_title,
    suggest_palette,
)


def test_infer_theme_from_title():
    assert infer_theme_from_title("Ashes Last - Christmas Dance") == "christmas"
    assert infer_theme_from_title("Spooky Scary Skeletons") == "halloween"
    assert infer_theme_from_title("Shut Up and Dance") is None


def test_classify_song_energy_bold_for_fast_bass_heavy_track():
    energy = classify_song_energy(
        tempo=136, average_loudness=0.23, dynamic_range=1.9, bass_peak_ratio=0.62
    )
    assert energy == "bold"


def test_classify_song_energy_soft_for_slow_quiet_track():
    energy = classify_song_energy(
        tempo=70, average_loudness=0.08, dynamic_range=4.0, bass_peak_ratio=0.2
    )
    assert energy == "soft"


def test_classify_song_energy_defaults_to_medium_with_no_data():
    assert classify_song_energy() == "medium"


def test_suggest_palette_infers_theme_and_matches_energy():
    result = suggest_palette(
        title="Ashes Last - Christmas Dance",
        tempo=136,
        average_loudness=0.23,
        dynamic_range=1.9,
        bass_peak_ratio=0.62,
    )
    assert result["theme"] == "christmas"
    assert result["song_energy"] == "bold"
    assert result["recommended"]["energy"] == "bold"
    assert len(result["alternatives"]) == 2


def test_suggest_palette_respects_explicit_theme_override():
    result = suggest_palette(title="Untitled Track", theme="halloween", tempo=90)
    assert result["theme"] == "halloween"
    assert result["recommended"]["name"] in {"classic", "spooky", "fire", "ghostly", "rainbow", "white", "warm_white"}
