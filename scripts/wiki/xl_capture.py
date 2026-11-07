"""Drive the running xLights window for documentation screenshots.

Coordinates are window-relative pixels, i.e. the same as in a full-window shot
(take one first and read positions off it). Uses the MCP server's window finder.

    python scripts/wiki/xl_capture.py shot OUT.png [l t r b]     capture window (or a crop)
    python scripts/wiki/xl_capture.py click X Y [left|right|double] [wait_s]
    python scripts/wiki/xl_capture.py key KEY [KEY...]           press a key / hotkey (escape, ctrl a)
    python scripts/wiki/xl_capture.py type TEXT                  type into the focused control
    python scripts/wiki/xl_capture.py scroll X Y AMOUNT          scroll at a point (+up / -down)
    python scripts/wiki/xl_capture.py rect                       print the window rect

Safety rules (learned the hard way, see .claude/skills/manual-to-wiki):
- SetForegroundWindow is blocked by Windows; a click inside the window focuses it.
- Screen grabs include anything on top of xLights (chat windows!): look at the
  first full shot before cropping, and ask the user to clear the screen.
- Wait ~2-3 s after opening a panel/dialog before capturing, and move the mouse
  away first (tooltips); a panel shown for the first time may not be drawn yet.
- Only open/inspect: Cancel/Escape every dialog, never Save. The pyautogui
  fail-safe (mouse in a screen corner) means the user wants control back: stop.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import pyautogui  # noqa: E402
from PIL import ImageGrab  # noqa: E402

from xlights_mcp.xlights.screenshot import find_xlights_window  # noqa: E402

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


def window_rect() -> tuple[int, int, int, int]:
    r = find_xlights_window().rect
    return (r[0], r[1], r[2], r[3]) if isinstance(r, (tuple, list)) else (r.left, r.top, r.right, r.bottom)


def main() -> None:
    cmd, args = sys.argv[1], sys.argv[2:]
    L, T, R, B = window_rect()
    if cmd == "rect":
        print(L, T, R, B)
    elif cmd == "shot":
        box = (L, T, R, B) if len(args) == 1 else tuple(
            int(a) + (L if i % 2 == 0 else T) for i, a in enumerate(args[1:5]))
        ImageGrab.grab(bbox=box, all_screens=True).save(args[0])
        print("saved", args[0], box[2] - box[0], "x", box[3] - box[1])
    elif cmd == "click":
        x, y = L + int(args[0]), T + int(args[1])
        kind = args[2] if len(args) > 2 else "left"
        if kind == "double":
            pyautogui.doubleClick(x, y)
        else:
            pyautogui.click(x, y, button=kind)
        time.sleep(float(args[3]) if len(args) > 3 else 0.8)
        print("clicked", args[0], args[1], kind)
    elif cmd == "key":
        pyautogui.hotkey(*args) if len(args) > 1 else pyautogui.press(args[0])
        time.sleep(0.6)
        print("pressed", args)
    elif cmd == "type":
        pyautogui.write(" ".join(args), interval=0.03)
        time.sleep(0.8)
        print("typed", args)
    elif cmd == "scroll":
        pyautogui.moveTo(L + int(args[0]), T + int(args[1]))
        time.sleep(0.2)
        pyautogui.scroll(int(args[2]))
        time.sleep(0.8)
        print("scrolled", args)
    else:
        sys.exit(f"unknown command {cmd!r}")


if __name__ == "__main__":
    main()
