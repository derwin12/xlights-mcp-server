"""Regression tests for the live automation client's open/add/save sequencing.

xLights' `loadSequence` automation command reloads the sequence from disk
unconditionally whenever it's called — it never checks whether the requested
file is already the open one — discarding any unsaved in-memory edits. Since
`add_effect_live` (and render_frame/render_clip) used to call `open_sequence`
before every single operation, adding several effects in a batch before one
`save_sequence_live` call silently dropped all but the last add: each new add
would trigger a reload that wiped every earlier unsaved add.

`ensure_sequence_open` fixes this by skipping the reload when the requested
sequence is already open. These tests use a fake in-process xLights automation
engine (not a real xLights instance) that models exactly that reload-wipes-
unsaved-changes behavior, so the test would fail if the caller went back to
calling `open_sequence` unconditionally.
"""

from __future__ import annotations

import copy

import pytest

from xlights_mcp.xlights import automation_client
from xlights_mcp.xlights.automation_client import AutomationError


class FakeXLights:
    """Minimal stateful model of the automation API's save/reload behavior."""

    def __init__(self):
        self.open_path: str | None = None
        self.memory_effects: dict[tuple[str, str], list[dict]] = {}
        self.disk_effects: dict[tuple[str, str], list[dict]] = {}

    def dispatch(self, cmd: str, params: dict) -> dict:
        if cmd == "loadSequence":
            seq = params.get("seq") or ""
            if not seq:
                return self._open_sequence_info()
            # Real xLights behavior: always reloads from the last-saved disk
            # state, regardless of whether `seq` matches what's already open.
            self.open_path = seq
            self.memory_effects = copy.deepcopy(self.disk_effects)
            return {"msg": "Loaded.", "res": 200}
        if cmd == "getOpenSequence":
            if self.open_path is None:
                return {"msg": "Sequence not open.", "res": 503}
            return self._open_sequence_info()
        if cmd == "addEffect":
            key = (params["target"], params["layer"])
            self.memory_effects.setdefault(key, []).append({
                "effect": params["effect"],
                "start": params["startTime"],
                "end": params["endTime"],
            })
            return {"msg": "Added Effects.", "worked": "true", "res": 200}
        if cmd == "saveSequence":
            self.disk_effects = copy.deepcopy(self.memory_effects)
            return {"msg": "Sequence Saved.", "res": 200}
        raise AssertionError(f"unexpected cmd {cmd!r}")

    def _open_sequence_info(self) -> dict:
        return {"seq": "test", "fullseq": self.open_path, "res": 200}


@pytest.fixture
def fake_xlights(monkeypatch):
    engine = FakeXLights()

    def fake_call(cmd, host=None, port=None, timeout=30.0, **params):
        data = engine.dispatch(cmd, params)
        if data.get("res", 200) != 200:
            raise AutomationError(f"xLights automation command '{cmd}' failed: {data}")
        return data

    monkeypatch.setattr(automation_client, "call", fake_call)
    return engine


SEQ_PATH = "F:/ShowFolderAI/funshine.xsq"


def test_ensure_sequence_open_skips_reload_when_already_open(fake_xlights):
    automation_client.ensure_sequence_open(SEQ_PATH)
    assert fake_xlights.open_path == SEQ_PATH

    # A second effect add against the same sequence must not trigger another
    # loadSequence — that would wipe the in-memory state below.
    automation_client.ensure_sequence_open(SEQ_PATH)
    automation_client.add_effect(
        "Matrix", "Shader", layer=1, start_time_ms=0, end_time_ms=2000,
    )
    automation_client.ensure_sequence_open(SEQ_PATH)
    automation_client.add_effect(
        "Matrix", "Shader", layer=1, start_time_ms=2000, end_time_ms=4000,
    )

    assert len(fake_xlights.memory_effects[("Matrix", "1")]) == 2


def test_multiple_effects_across_models_survive_one_save(fake_xlights):
    """Reproduces the exact bug report: 6 add_effect_live calls across 3
    models on the same sequence, one save, all 6 effects must persist."""
    additions = [
        ("Matrix", 0, 2000),
        ("Matrix", 2000, 4000),
        ("Matrix 2", 0, 2500),
        ("Matrix 2", 2500, 5000),
        ("Lyrics Matrix", 0, 3000),
        ("Lyrics Matrix", 3000, 6000),
    ]
    for target, start, end in additions:
        # Mirrors add_effect_live: ensure_sequence_open before every add.
        automation_client.ensure_sequence_open(SEQ_PATH)
        automation_client.add_effect(
            target, "Shader", layer=1, start_time_ms=start, end_time_ms=end,
        )

    automation_client.save_sequence()

    assert [e["start"] for e in fake_xlights.disk_effects[("Matrix", "1")]] == ["0", "2000"]
    assert [e["end"] for e in fake_xlights.disk_effects[("Matrix", "1")]] == ["2000", "4000"]
    assert [e["start"] for e in fake_xlights.disk_effects[("Matrix 2", "1")]] == ["0", "2500"]
    assert [e["start"] for e in fake_xlights.disk_effects[("Lyrics Matrix", "1")]] == ["0", "3000"]
    assert [e["end"] for e in fake_xlights.disk_effects[("Lyrics Matrix", "1")]] == ["3000", "6000"]


def test_unconditional_open_sequence_would_lose_earlier_adds(fake_xlights):
    """Control test: proves the fake engine models the real bug — calling
    open_sequence directly (the pre-fix behavior) between adds does drop
    earlier unsaved effects, so the fix above is actually load-bearing."""
    automation_client.open_sequence(SEQ_PATH)
    automation_client.add_effect(
        "Matrix", "Shader", layer=1, start_time_ms=0, end_time_ms=2000,
    )
    automation_client.open_sequence(SEQ_PATH)  # reloads, wiping the add above
    automation_client.add_effect(
        "Matrix", "Shader", layer=1, start_time_ms=2000, end_time_ms=4000,
    )

    assert len(fake_xlights.memory_effects[("Matrix", "1")]) == 1
