"""Tests for in-place .xsq editing (add/update/delete effects)."""

from __future__ import annotations

from pathlib import Path

import pytest

from xlights_mcp.xlights import xsq_editor
from xlights_mcp.xlights.models import LightModel, ShowConfig
from xlights_mcp.xlights.xsq_reader import read_xsq_summary
from xlights_mcp.xlights.xsq_writer import EffectPlacement, SequenceSpec, write_xsq


@pytest.fixture
def xsq_path(tmp_path) -> Path:
    """A minimal sequence with one model and one existing effect."""
    show = ShowConfig(
        show_path=str(tmp_path),
        show_name="Test",
        models=[LightModel(name="Arch1", model_category="arch")],
        controllers=[],
    )
    spec = SequenceSpec(
        song_title="Test",
        duration_ms=10000,
        effects=[
            EffectPlacement(
                model_name="Arch1", layer=0, effect_name="Twinkle",
                start_time_ms=0, end_time_ms=5000, settings={"a": "1"},
            )
        ],
    )
    path = tmp_path / "Test.xsq"
    write_xsq(spec, show, path)
    return path


def test_add_effect_appends_and_backs_up(xsq_path):
    result = xsq_editor.add_effect(
        xsq_path, "Arch1", "Chase", 5000, 7000,
        settings={"b": "2"}, layer=0, colors=["#FF0000"],
    )

    assert result["success"]
    assert result["layer"] == 0
    assert result["index"] == 1  # sorted after the existing 0-5000ms effect

    backup = Path(result["backup"])
    assert backup.exists()

    summary = read_xsq_summary(xsq_path, model_name="Arch1")
    effects = summary["models_with_effects"][0]["effects"]
    assert len(effects) == 2
    assert effects[1]["name"] == "Chase"
    assert effects[1]["start_time_ms"] == 5000
    assert effects[1]["palette_ref"] == "0"


def test_add_effect_on_new_model_creates_display_entry(xsq_path):
    result = xsq_editor.add_effect(xsq_path, "Arch2", "Twinkle", 0, 1000)
    assert result["success"]

    summary = read_xsq_summary(xsq_path, model_name="Arch2")
    arch2 = next(m for m in summary["models_with_effects"] if m["model_name"] == "Arch2")
    assert arch2["effect_count"] == 1


def test_update_effect_changes_time_and_resorts(xsq_path):
    added = xsq_editor.add_effect(xsq_path, "Arch1", "Chase", 5000, 7000)
    result = xsq_editor.update_effect(
        xsq_path, "Arch1", layer=0, index=added["index"], end_time_ms=9000
    )
    assert result["success"]

    summary = read_xsq_summary(xsq_path, model_name="Arch1")
    chase = next(e for e in summary["models_with_effects"][0]["effects"] if e["name"] == "Chase")
    assert chase["end_time_ms"] == 9000


def test_update_effect_unknown_model_returns_error(xsq_path):
    result = xsq_editor.update_effect(xsq_path, "NoSuchModel", layer=0, index=0, end_time_ms=1000)
    assert "error" in result


def test_delete_effect_removes_it(xsq_path):
    before = read_xsq_summary(xsq_path, model_name="Arch1")
    assert before["models_with_effects"][0]["effect_count"] == 1

    result = xsq_editor.delete_effect(xsq_path, "Arch1", layer=0, index=0)
    assert result["deleted"]

    after = read_xsq_summary(xsq_path, model_name="Arch1")
    # a model with zero effects is omitted from models_with_effects entirely
    assert all(m["model_name"] != "Arch1" for m in after["models_with_effects"])


def test_delete_effect_out_of_range_returns_error(xsq_path):
    result = xsq_editor.delete_effect(xsq_path, "Arch1", layer=0, index=99)
    assert "error" in result


def test_each_write_creates_a_distinct_backup(xsq_path):
    r1 = xsq_editor.add_effect(xsq_path, "Arch1", "Chase", 5000, 6000)
    r2 = xsq_editor.add_effect(xsq_path, "Arch1", "Plasma", 6000, 7000)
    assert r1["backup"] != r2["backup"]
    assert Path(r1["backup"]).exists()
    assert Path(r2["backup"]).exists()
