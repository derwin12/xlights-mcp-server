"""Tests for reading timing tracks from .xsq files."""

from __future__ import annotations

from pathlib import Path

from xlights_mcp.xlights.xsq_reader import read_xsq_timing_tracks

FIXTURE = Path(__file__).parent / "fixtures" / "remapping" / "minimal_sequence.xsq"


def test_lists_timing_tracks_without_marks_by_default():
    tracks = read_xsq_timing_tracks(FIXTURE)

    assert len(tracks) == 1
    assert tracks[0]["name"] == "Lyrics"
    assert tracks[0]["mark_count"] == 2
    assert tracks[0]["marks"] == []


def test_returns_marks_for_requested_track():
    tracks = read_xsq_timing_tracks(FIXTURE, track_name="Lyrics")

    assert tracks[0]["mark_count"] == 2
    marks = tracks[0]["marks"]
    assert len(marks) == 2
    assert marks[0] == {
        "label": "La la la", "start_time_ms": 0, "end_time_ms": 2000, "index": 0,
    }
    assert marks[1]["label"] == "Do re mi"


def test_ignores_model_elements():
    tracks = read_xsq_timing_tracks(FIXTURE, track_name="Mega Tree")

    assert len(tracks) == 1
    assert tracks[0]["name"] == "Lyrics"
