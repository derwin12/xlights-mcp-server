"""Screenshot capture for the xLights application window.

Finds xLights by process name (xLights.exe) rather than window title so that
browser tabs, IDE windows, etc. with "xLights" in their title are never
confused for the real app.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

def _imports():
    """Lazy-import platform-specific packages so this module loads cleanly in
    test environments or on non-Windows machines without those packages."""
    import mss as _mss
    import mss.tools as _mss_tools
    import psutil as _psutil
    import win32con as _w32con
    import win32gui as _w32gui
    import win32process as _w32proc
    return _mss, _mss_tools, _psutil, _w32con, _w32gui, _w32proc


# PIL is only needed for annotation (in server.py); not imported here.

# Executable names that belong to xLights
_XLIGHTS_EXES = {"xlights.exe", "xlights64.exe"}

# Named regions relative to the main window (fraction of w/h).
# These are approximate and may need tuning across xLights versions.
NAMED_REGIONS: dict[str, tuple[float, float, float, float]] = {
    # (left_frac, top_frac, right_frac, bottom_frac)
    "full": (0.0, 0.0, 1.0, 1.0),
    "sequencer": (0.0, 0.35, 1.0, 1.0),
    "toolbar": (0.0, 0.0, 1.0, 0.08),
    "model_list": (0.0, 0.08, 0.18, 1.0),
    "effects_panel": (0.18, 0.08, 1.0, 0.35),
    "color_panel": (0.75, 0.08, 1.0, 0.35),
}


class WindowRect(NamedTuple):
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


@dataclass
class XLightsWindow:
    hwnd: int
    title: str
    rect: WindowRect
    pid: int


class XLightsNotRunning(RuntimeError):
    """Raised when xLights.exe is not found among running processes."""


def _xlights_pids() -> list[int]:
    _, _, psutil, _, _, _ = _imports()
    return [
        p.pid
        for p in psutil.process_iter(["pid", "name"])
        if (p.info["name"] or "").lower() in _XLIGHTS_EXES
    ]


def _enum_callback(hwnd: int, results: list[XLightsWindow], pids: set[int]) -> bool:
    _, _, _, _, win32gui, win32process = _imports()
    if not win32gui.IsWindowVisible(hwnd):
        return True
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
    except Exception:
        return True
    if pid not in pids:
        return True
    title = win32gui.GetWindowText(hwnd)
    if not title:
        return True
    rect = win32gui.GetWindowRect(hwnd)
    r = WindowRect(*rect)
    if r.width < 100 or r.height < 100:
        return True  # skip tiny helper windows
    results.append(XLightsWindow(hwnd=hwnd, title=title, rect=r, pid=pid))
    return True


def find_xlights_window() -> XLightsWindow:
    """Return the main xLights application window.

    Raises XLightsNotRunning if xLights.exe is not running.
    Raises RuntimeError if the process is running but no visible window found.
    """
    _, _, _, _, win32gui, _ = _imports()

    pids = _xlights_pids()
    if not pids:
        raise XLightsNotRunning(
            "xLights is not running. Start xLights before taking screenshots."
        )

    windows: list[XLightsWindow] = []
    win32gui.EnumWindows(lambda hwnd, _: _enum_callback(hwnd, windows, set(pids)), None)

    if not windows:
        raise RuntimeError(
            "xLights process found but no visible window detected. "
            "The app may be minimized or still loading."
        )

    # Pick the largest window (main frame, not toolbars / popups)
    return max(windows, key=lambda w: w.rect.width * w.rect.height)


def _bring_to_front(hwnd: int) -> None:
    """Restore and focus the window so it isn't occluded."""
    _, _, _, win32con, win32gui, _ = _imports()
    placement = win32gui.GetWindowPlacement(hwnd)
    if placement[1] == win32con.SW_SHOWMINIMIZED:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.3)  # let the compositor repaint


def capture_window(
    output_path: str | Path,
    *,
    bring_to_front: bool = True,
) -> Path:
    """Capture the full xLights window and save to *output_path* (PNG).

    Returns the resolved output path.
    """
    mss, mss_tools, _, _, _, _ = _imports()

    win = find_xlights_window()
    if bring_to_front:
        _bring_to_front(win.hwnd)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    r = win.rect
    monitor = {"left": r.left, "top": r.top, "width": r.width, "height": r.height}
    with mss.mss() as sct:
        img = sct.grab(monitor)
        mss_tools.to_png(img.rgb, img.size, output=str(output_path))

    return output_path


def capture_region(
    region: str | tuple[int, int, int, int],
    output_path: str | Path,
    *,
    bring_to_front: bool = True,
) -> Path:
    """Capture a named region or absolute pixel rect of the xLights window.

    *region* is either:
    - A name from NAMED_REGIONS (e.g. ``"sequencer"``, ``"effects_panel"``)
    - A 4-tuple ``(left, top, right, bottom)`` in absolute screen coordinates

    Returns the resolved output path.
    """
    mss, mss_tools, _, _, _, _ = _imports()

    win = find_xlights_window()
    if bring_to_front:
        _bring_to_front(win.hwnd)

    if isinstance(region, str):
        if region not in NAMED_REGIONS:
            raise ValueError(
                f"Unknown region {region!r}. "
                f"Available: {', '.join(sorted(NAMED_REGIONS))}"
            )
        lf, tf, rf, bf = NAMED_REGIONS[region]
        r = win.rect
        left = r.left + int(lf * r.width)
        top = r.top + int(tf * r.height)
        right = r.left + int(rf * r.width)
        bottom = r.top + int(bf * r.height)
    else:
        left, top, right, bottom = region

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    monitor = {"left": left, "top": top, "width": right - left, "height": bottom - top}
    with mss.mss() as sct:
        img = sct.grab(monitor)
        mss_tools.to_png(img.rgb, img.size, output=str(output_path))

    return output_path


def list_named_regions() -> list[str]:
    return sorted(NAMED_REGIONS)
