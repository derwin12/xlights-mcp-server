"""Tests for screenshot.py and dialog_nav.py.

All tests are mock-based — no running xLights required.
We patch `screenshot._imports` so the module's top-level import is a no-op
and each test controls exactly what psutil/win32 return.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_imports(*, pids_by_name=None, windows=None):
    """Return a fake _imports() callable that yields controllable mocks."""
    mss_mod = MagicMock()
    mss_tools = MagicMock()

    psutil_mod = MagicMock()
    procs = []
    for name, pid in (pids_by_name or {}).items():
        p = MagicMock()
        p.pid = pid
        p.info = {"pid": pid, "name": name}
        procs.append(p)
    psutil_mod.process_iter.return_value = procs

    win32con = MagicMock()
    win32con.SW_SHOWMINIMIZED = 2
    win32con.SW_RESTORE = 9

    win32gui = MagicMock()
    win32process = MagicMock()

    if windows is not None:
        # windows: list of (hwnd, pid, title, rect_tuple)
        win32gui.IsWindowVisible.return_value = True

        def mock_enum(cb, extra):
            for hwnd, pid, title, rect in windows:
                win32process.GetWindowThreadProcessId.return_value = (0, pid)
                win32gui.GetWindowText.return_value = title
                win32gui.GetWindowRect.return_value = rect
                cb(hwnd, None)

        win32gui.EnumWindows.side_effect = mock_enum
    else:
        win32gui.IsWindowVisible.return_value = False

    def fake_imports_fn():
        return mss_mod, mss_tools, psutil_mod, win32con, win32gui, win32process

    return fake_imports_fn, mss_mod, mss_tools, psutil_mod, win32con, win32gui, win32process


# ---------------------------------------------------------------------------
# screenshot.py tests
# ---------------------------------------------------------------------------

class TestXLightsNotRunning:
    def test_raises_when_no_xlights_process(self):
        fake_imp, *_ = _fake_imports(pids_by_name={})
        with patch("xlights_mcp.xlights.screenshot._imports", fake_imp):
            from xlights_mcp.xlights.screenshot import find_xlights_window, XLightsNotRunning
            with pytest.raises(XLightsNotRunning, match="not running"):
                find_xlights_window()


class TestFindXLightsWindow:
    def test_finds_by_exe_name(self):
        fake_imp, *_ = _fake_imports(
            pids_by_name={"xLights.exe": 1234},
            windows=[
                (100, 1234, "xLights 2024.12", (0, 0, 1920, 1080)),
                (200, 1234, "xLights toolbar", (0, 0, 50, 20)),  # tiny, skipped
            ],
        )
        with patch("xlights_mcp.xlights.screenshot._imports", fake_imp):
            from xlights_mcp.xlights.screenshot import find_xlights_window
            win = find_xlights_window()
            assert win.hwnd == 100
            assert win.rect.width == 1920
            assert win.rect.height == 1080
            assert win.pid == 1234

    def test_ignores_windows_from_other_pids(self):
        fake_imp, *rest = _fake_imports(
            pids_by_name={"xLights.exe": 9999},
            windows=[(1, 5555, "Other App", (0, 0, 800, 600))],
        )
        # Override: GetWindowThreadProcessId returns wrong pid
        win32process = rest[5]
        win32process.GetWindowThreadProcessId.return_value = (0, 5555)

        with patch("xlights_mcp.xlights.screenshot._imports", fake_imp):
            from xlights_mcp.xlights.screenshot import find_xlights_window
            with pytest.raises(RuntimeError, match="no visible window"):
                find_xlights_window()

    def test_recognises_xlights64_exe(self):
        fake_imp, *_ = _fake_imports(
            pids_by_name={"xLights64.exe": 42},
            windows=[(77, 42, "xLights 2024", (100, 100, 1100, 900))],
        )
        with patch("xlights_mcp.xlights.screenshot._imports", fake_imp):
            from xlights_mcp.xlights.screenshot import find_xlights_window
            win = find_xlights_window()
            assert win.hwnd == 77

    def test_picks_largest_window(self):
        fake_imp, *_ = _fake_imports(
            pids_by_name={"xLights.exe": 1},
            windows=[
                (10, 1, "xLights", (0, 0, 400, 300)),    # 120000 px
                (20, 1, "xLights", (0, 0, 1920, 1080)),  # 2073600 px — largest
                (30, 1, "xLights", (0, 0, 200, 150)),    # 30000 px
            ],
        )
        with patch("xlights_mcp.xlights.screenshot._imports", fake_imp):
            from xlights_mcp.xlights.screenshot import find_xlights_window
            win = find_xlights_window()
            assert win.hwnd == 20


class TestNamedRegions:
    def test_list_named_regions_returns_all(self):
        from xlights_mcp.xlights.screenshot import list_named_regions, NAMED_REGIONS
        regions = list_named_regions()
        assert set(regions) == set(NAMED_REGIONS.keys())
        assert "full" in regions
        assert "sequencer" in regions
        assert "effects_panel" in regions

    def test_invalid_region_raises_value_error(self):
        fake_imp, *_ = _fake_imports(
            pids_by_name={"xLights.exe": 1},
            windows=[(1, 1, "xLights", (0, 0, 1920, 1080))],
        )
        with patch("xlights_mcp.xlights.screenshot._imports", fake_imp):
            from xlights_mcp.xlights.screenshot import capture_region
            with pytest.raises(ValueError, match="Unknown region"):
                capture_region("nonexistent_region", "/tmp/out.png", bring_to_front=False)


# ---------------------------------------------------------------------------
# dialog_nav.py tests
# ---------------------------------------------------------------------------

class TestSceneRegistry:
    def test_all_scenes_have_valid_steps(self):
        from xlights_mcp.xlights.dialog_nav import SCENES, list_scenes

        assert len(SCENES) > 20
        for name, steps in SCENES.items():
            assert isinstance(steps, list), f"Scene {name!r} steps must be a list"
            for step in steps:
                assert "type" in step, f"Step in {name!r} missing 'type'"
                assert step["type"] in ("automation", "menu", "hotkey", "wait", "click_fraction"), \
                    f"Unknown step type {step['type']!r} in scene {name!r}"

        assert list_scenes() == sorted(SCENES)

    def test_menu_steps_have_path(self):
        from xlights_mcp.xlights.dialog_nav import SCENES
        for name, steps in SCENES.items():
            for step in steps:
                if step["type"] == "menu":
                    assert "path" in step, f"Menu step in {name!r} missing 'path'"
                    assert len(step["path"]) >= 1

    def test_key_scenes_present(self):
        from xlights_mcp.xlights.dialog_nav import SCENES
        for expected in (
            "preferences", "test_dialog", "fpp_connect",
            "effect_settings_panel", "colors_panel",
            "new_sequence_dialog", "key_bindings",
        ):
            assert expected in SCENES, f"Expected scene {expected!r} missing"

    def test_hotkey_steps_have_keys(self):
        from xlights_mcp.xlights.dialog_nav import SCENES
        for name, steps in SCENES.items():
            for step in steps:
                if step["type"] == "hotkey":
                    assert "keys" in step, f"Hotkey step in {name!r} missing 'keys'"
                    assert len(step["keys"]) >= 1


# ---------------------------------------------------------------------------
# MCP tool smoke tests (no xLights needed)
# ---------------------------------------------------------------------------

class TestXlightsScreenshotTool:
    def test_returns_error_when_not_running(self):
        fake_imp, *_ = _fake_imports(pids_by_name={})
        with patch("xlights_mcp.xlights.screenshot._imports", fake_imp):
            from xlights_mcp.server import xlights_screenshot
            result = xlights_screenshot("out.png")
        assert result["status"] == "error"
        assert "not running" in result["error"].lower()

    def test_list_regions_tool(self):
        from xlights_mcp.server import xlights_list_regions
        result = xlights_list_regions()
        assert "regions" in result
        assert "full" in result["regions"]
        assert "sequencer" in result["regions"]

    def test_list_scenes_tool(self):
        from xlights_mcp.server import xlights_list_scenes
        result = xlights_list_scenes()
        assert "scenes" in result
        assert "preferences" in result["scenes"]
        assert "fpp_connect" in result["scenes"]


# ---------------------------------------------------------------------------
# Annotation tool tests
# ---------------------------------------------------------------------------

class TestAnnotateTool:
    def test_annotate_creates_output(self, tmp_path):
        from PIL import Image
        from xlights_mcp.server import xlights_annotate_screenshot

        src = tmp_path / "src.png"
        out = tmp_path / "annotated.png"
        Image.new("RGB", (800, 600), color=(200, 200, 200)).save(str(src))

        result = xlights_annotate_screenshot(
            str(src),
            str(out),
            [
                {"type": "label", "x": 10, "y": 10, "text": "Test label"},
                {"type": "box", "x": 100, "y": 100, "width": 200, "height": 100, "text": "Box"},
                {"type": "arrow", "x": 50, "y": 50, "x2": 150, "y2": 150, "text": "Arrow"},
            ],
        )

        assert result["status"] == "ok"
        assert result["annotation_count"] == 3
        assert out.exists()
        annotated = Image.open(str(out))
        assert annotated.size == (800, 600)

    def test_annotate_empty_list(self, tmp_path):
        from PIL import Image
        from xlights_mcp.server import xlights_annotate_screenshot

        src = tmp_path / "src.png"
        out = tmp_path / "out.png"
        Image.new("RGB", (400, 300)).save(str(src))

        result = xlights_annotate_screenshot(str(src), str(out), [])
        assert result["status"] == "ok"
        assert result["annotation_count"] == 0

    def test_annotate_missing_input_returns_error(self, tmp_path):
        from xlights_mcp.server import xlights_annotate_screenshot
        result = xlights_annotate_screenshot(
            str(tmp_path / "doesnt_exist.png"),
            str(tmp_path / "out.png"),
            [],
        )
        assert result["status"] == "error"
