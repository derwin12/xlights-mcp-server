"""Keyboard/mouse navigation for opening xLights dialogs before screenshotting.

Uses pyautogui to send keystrokes and click menu items. All actions operate
on the foreground xLights window, so ``find_xlights_window()`` should be
called first (which also brings the window to front).
"""

from __future__ import annotations

import time

import pyautogui

# Safety: pyautogui will raise FailSafeException if the mouse is in a corner.
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.15  # short delay between actions


def open_menu_path(path: list[str], *, close_after: bool = False) -> None:
    """Open a top-level menu then navigate through submenus by label.

    Example::

        open_menu_path(["Settings", "Preferences"])

    *path[0]* is clicked; subsequent items are moved-to and clicked.
    If *close_after* is True, Escape is sent after reaching the final item
    (useful if you just want the dialog that opens, not the menu itself).
    """
    if not path:
        raise ValueError("path must have at least one item")

    pyautogui.hotkey("alt", path[0][0].lower())  # Alt+first-letter opens menu
    time.sleep(0.25)

    for item in path[1:]:
        # Try clicking by image if available, else by keyboard search
        _click_menu_item(item)
        time.sleep(0.2)

    if close_after:
        pyautogui.press("escape")


def _click_menu_item(label: str) -> None:
    """Move to and click a visible menu item whose text starts with *label*."""
    # Find the item by scanning for its accelerator key in the label.
    # Most xLights menu items have an underlined letter; press it.
    for ch in label:
        if ch.isalpha():
            pyautogui.press(ch.lower())
            return
    # Fallback: type the first character
    pyautogui.press(label[0].lower())


def press_hotkey(*keys: str) -> None:
    """Send a keyboard shortcut to the foreground window.

    Example::

        press_hotkey("ctrl", "s")   # save sequence
    """
    pyautogui.hotkey(*keys)
    time.sleep(0.2)


def click_at_fraction(window_rect, x_frac: float, y_frac: float) -> None:
    """Click at a position expressed as a fraction of the window size."""
    from .screenshot import WindowRect

    if isinstance(window_rect, WindowRect):
        r = window_rect
    else:
        raise TypeError("window_rect must be a WindowRect")

    x = r.left + int(x_frac * r.width)
    y = r.top + int(y_frac * r.height)
    pyautogui.click(x, y)
    time.sleep(0.2)


# ---------------------------------------------------------------------------
# Named scene definitions
# ---------------------------------------------------------------------------
# Each scene maps to a list of steps that put xLights in the right state for
# a screenshot. Steps are dicts with a "type" key.
#
# Supported step types:
#   {"type": "automation", "cmd": "...", **kwargs}   – POST to automation API
#   {"type": "menu", "path": ["Menu", "Item"]}       – open a menu path
#   {"type": "hotkey", "keys": ["ctrl", "p"]}        – send a hotkey
#   {"type": "wait", "seconds": 0.5}                 – pause
#
# These are executed by xlights_navigate() in server.py.
# ---------------------------------------------------------------------------

SCENES: dict[str, list[dict]] = {
    # ---- No navigation — screenshot current state ----
    "main_window": [],
    "sequencer": [],

    # ---- Main tab switching (clicks the tab by position in the toolbar) ----
    # xLights tabs are the three notebook tabs at the top: Controllers (0),
    # Layout (1), Sequencer (2). We click them by fractional window position.
    # These require xLights to be running; a sequence must be open for the
    # Sequencer tab to show content.
    "tab_controllers": [
        {"type": "click_fraction", "x": 0.027, "y": 0.133},
        {"type": "wait", "seconds": 0.5},
    ],
    "tab_layout": [
        {"type": "click_fraction", "x": 0.059, "y": 0.133},
        {"type": "wait", "seconds": 0.5},
    ],
    "tab_sequencer": [
        {"type": "click_fraction", "x": 0.094, "y": 0.133},
        {"type": "wait", "seconds": 0.5},
    ],

    # ---- File menu ----
    "new_sequence_dialog": [
        {"type": "hotkey", "keys": ["ctrl", "n"]},
        {"type": "wait", "seconds": 0.6},
    ],
    "open_sequence_dialog": [
        {"type": "hotkey", "keys": ["ctrl", "o"]},
        {"type": "wait", "seconds": 0.6},
    ],
    "preferences": [
        # File > Preferences...  (Ctrl+,)
        {"type": "hotkey", "keys": ["ctrl", ","]},
        {"type": "wait", "seconds": 0.7},
    ],
    "sequence_settings": [
        # File > Sequence Settings
        {"type": "menu", "path": ["File", "Sequence Settings"]},
        {"type": "wait", "seconds": 0.6},
    ],
    "key_bindings": [
        {"type": "menu", "path": ["File", "Key bindings"]},
        {"type": "wait", "seconds": 0.6},
    ],
    "select_show_folder": [
        {"type": "menu", "path": ["File", "Select Show Folder"]},
        {"type": "wait", "seconds": 0.6},
    ],

    # ---- Edit menu ----
    "color_replace": [
        {"type": "menu", "path": ["Edit", "Color Replace"]},
        {"type": "wait", "seconds": 0.6},
    ],
    "shift_effects": [
        {"type": "menu", "path": ["Edit", "Shift Effects And Timing"]},
        {"type": "wait", "seconds": 0.6},
    ],

    # ---- Tools menu ----
    "test_dialog": [
        # Tools > Test  (hardware test)
        {"type": "menu", "path": ["Tools", "Test"]},
        {"type": "wait", "seconds": 0.7},
    ],
    "check_sequence": [
        {"type": "menu", "path": ["Tools", "Check Sequence"]},
        {"type": "wait", "seconds": 0.7},
    ],
    "batch_render": [
        {"type": "menu", "path": ["Tools", "Batch Render"]},
        {"type": "wait", "seconds": 0.6},
    ],
    "fpp_connect": [
        {"type": "menu", "path": ["Tools", "FPP Connect"]},
        {"type": "wait", "seconds": 0.7},
    ],
    "bulk_controller_upload": [
        {"type": "menu", "path": ["Tools", "Bulk Controller Upload"]},
        {"type": "wait", "seconds": 0.7},
    ],
    "generate_custom_model": [
        {"type": "menu", "path": ["Tools", "Generate Custom Model"]},
        {"type": "wait", "seconds": 0.7},
    ],
    "generate_2d_path": [
        {"type": "menu", "path": ["Tools", "Generate 2D Path"]},
        {"type": "wait", "seconds": 0.7},
    ],
    "convert_dialog": [
        {"type": "menu", "path": ["Tools", "Convert"]},
        {"type": "wait", "seconds": 0.6},
    ],
    "prepare_audio": [
        {"type": "menu", "path": ["Tools", "Prepare Audio"]},
        {"type": "wait", "seconds": 0.6},
    ],
    "run_scripts": [
        {"type": "menu", "path": ["Tools", "Run Scripts"]},
        {"type": "wait", "seconds": 0.6},
    ],
    "view_log": [
        {"type": "menu", "path": ["Tools", "View Log"]},
        {"type": "wait", "seconds": 0.6},
    ],
    "download_sequences": [
        {"type": "menu", "path": ["Tools", "Download Sequences/Lyrics"]},
        {"type": "wait", "seconds": 0.7},
    ],
    "generate_lyrics": [
        {"type": "menu", "path": ["Tools", "Generate Lyrics From Data"]},
        {"type": "wait", "seconds": 0.6},
    ],
    "generate_ai_image": [
        {"type": "menu", "path": ["Tools", "Generate AI Image"]},
        {"type": "wait", "seconds": 0.7},
    ],

    # ---- View menu panels (toggle on if not visible) ----
    "display_elements_panel": [
        {"type": "menu", "path": ["View", "Windows", "Display Elements"]},
        {"type": "wait", "seconds": 0.4},
    ],
    "model_preview_panel": [
        {"type": "menu", "path": ["View", "Windows", "Model Preview"]},
        {"type": "wait", "seconds": 0.4},
    ],
    "house_preview_panel": [
        {"type": "menu", "path": ["View", "Windows", "House Preview"]},
        {"type": "wait", "seconds": 0.4},
    ],
    "effect_settings_panel": [
        {"type": "menu", "path": ["View", "Windows", "Effect Settings"]},
        {"type": "wait", "seconds": 0.4},
    ],
    "colors_panel": [
        {"type": "menu", "path": ["View", "Windows", "Colors"]},
        {"type": "wait", "seconds": 0.4},
    ],
    "layer_blending_panel": [
        {"type": "menu", "path": ["View", "Windows", "Layer Blending"]},
        {"type": "wait", "seconds": 0.4},
    ],
    "layer_settings_panel": [
        {"type": "menu", "path": ["View", "Windows", "Layer Settings"]},
        {"type": "wait", "seconds": 0.4},
    ],
    "effect_dropper_panel": [
        {"type": "menu", "path": ["View", "Windows", "Effect Dropper"]},
        {"type": "wait", "seconds": 0.4},
    ],
    "value_curves_panel": [
        {"type": "menu", "path": ["View", "Windows", "Value Curves"]},
        {"type": "wait", "seconds": 0.4},
    ],
    "effect_presets_panel": [
        {"type": "menu", "path": ["View", "Windows", "Effect Presets"]},
        {"type": "wait", "seconds": 0.4},
    ],
    "search_effects_panel": [
        {"type": "menu", "path": ["View", "Windows", "Search Effects"]},
        {"type": "wait", "seconds": 0.4},
    ],
    "video_preview_panel": [
        {"type": "menu", "path": ["View", "Windows", "Video Preview"]},
        {"type": "wait", "seconds": 0.4},
    ],
    "jukebox_panel": [
        {"type": "menu", "path": ["View", "Windows", "Jukebox"]},
        {"type": "wait", "seconds": 0.4},
    ],
    "find_effect_data_panel": [
        {"type": "menu", "path": ["View", "Windows", "Find Effect Data"]},
        {"type": "wait", "seconds": 0.4},
    ],
    "reset_toolbars": [
        {"type": "menu", "path": ["View", "Reset Toolbars"]},
        {"type": "wait", "seconds": 0.5},
    ],

    # ---- Import menu ----
    "import_effects": [
        {"type": "menu", "path": ["Import", "Import Effects"]},
        {"type": "wait", "seconds": 0.6},
    ],
}


def list_scenes() -> list[str]:
    return sorted(SCENES)
