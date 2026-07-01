"""Narrated Reel showcasing the xLights Radial Effect Wheel (a sequencer UI
feature, not a light effect — see TipOfDay/00057.html in the xLights source).

Usage:
    python scripts/feature_showcase_radial_wheel.py --reel

Produces: feature_showcase_RadialEffectWheel_reel.mp4

Unlike effect_showcase.py (which renders model output through the automation
API's exportVideoPreview), this script screen-records the sequencer grid while
performing the real double-click / pick-a-slice interaction, since the wheel
only exists in the app's UI chrome — it can't be captured by rendering lights.

The recorded clip is then handed to effect_showcase.build_video_shorts(),
which does the vertical-crop/blur/overlay/narration/intro-outro assembly
exactly as it does for the effect showcase reels.
"""

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pyautogui

import effect_showcase as engine
from xlights_mcp.xlights import automation_client as ac
from xlights_mcp.xlights import screenshot as ss
from xlights_mcp.xlights.dialog_nav import click_at_fraction

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

# ── Configuration ───────────────────────────────────────────────────────────

FEATURE = "Radial Effect Wheel"
engine.TITLE_LINE2 = "Feature Showcase"
engine.TITLE_LINE3 = "Radial Wheel"
engine.OUTRO_LINE1 = "Thanks For"
engine.OUTRO_LINE2 = "Watching!"
engine.OUTRO_LINE3 = "Like & Subscribe"
engine.OUT_FILE = Path(__file__).parent.parent / "feature_showcase_RadialEffectWheel.mp4"

# The grid/timeline area within the xLights window (fractions of the main
# window rect) — this is where the wheel actually appears, so we crop the
# recording to it instead of the whole app (Model Preview, Color panel, etc.).
CAPTURE_BOX_FRAC = (0.451, 0.435, 1.0, 0.992)   # left, top, right, bottom

# Each section: (label, subtitle, narration, short_narration, action)
# `action.spot` is a point within CAPTURE_BOX_FRAC (fractions 0..1) to
# double-click. `action.pick_offset` is a pixel offset from that point that
# lands on a specific wheel slice — the wheel's slice layout is fixed
# (tied to the session's effect keybindings), so a fixed offset reliably
# lands on the same slice every time. Verified empirically against this
# xLights build's keybinding layout.
SECTIONS = [
    (
        "Radial Effect Wheel",
        "Double-click an empty cell",
        "Double-click any empty part of the sequencer grid, not the timing track, "
        "and a small radial wheel pops up right around your cursor with all of "
        "your effect keybindings.",
        "Double-click an empty grid cell to pop up the radial wheel.",
        {"spot": (0.35, 0.55), "pick_offset": (-67, -35)},   # lands on "Snowflakes"
    ),
    (
        "Anywhere On The Grid",
        "Pick a different effect",
        "It works the exact same way no matter where you double-click, so "
        "dropping a different effect from your keybindings is always just one "
        "click away.",
        "It works the same anywhere on the grid — one click away.",
        {"spot": (0.70, 0.68), "pick_offset": (39, 88)},     # lands on "Fire"
    ),
]
engine.SECTIONS = SECTIONS


# ── Screen recording ─────────────────────────────────────────────────────────

def capture_rect(win_rect) -> tuple[int, int, int, int]:
    """Absolute (left, top, width, height) of CAPTURE_BOX_FRAC within *win_rect*."""
    lf, tf, rf, bf = CAPTURE_BOX_FRAC
    left = win_rect.left + int(lf * win_rect.width)
    top = win_rect.top + int(tf * win_rect.height)
    right = win_rect.left + int(rf * win_rect.width)
    bottom = win_rect.top + int(bf * win_rect.height)
    w, h = right - left, bottom - top
    w -= w % 2
    h -= h % 2
    return left, top, w, h


def window_point(win_rect, spot_frac: tuple[float, float]) -> tuple[int, int]:
    """Map a point (fractions 0..1 within CAPTURE_BOX_FRAC) to absolute screen coords."""
    lf, tf, rf, bf = CAPTURE_BOX_FRAC
    sx, sy = spot_frac
    x_frac = lf + sx * (rf - lf)
    y_frac = tf + sy * (bf - tf)
    return (
        win_rect.left + int(x_frac * win_rect.width),
        win_rect.top + int(y_frac * win_rect.height),
    )


def start_recording(rect: tuple[int, int, int, int], dest: Path, framerate: int = 10):
    left, top, w, h = rect
    cmd = [
        "ffmpeg", "-y", "-f", "gdigrab", "-framerate", str(framerate),
        "-offset_x", str(left), "-offset_y", str(top),
        "-video_size", f"{w}x{h}", "-i", "desktop",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        str(dest),
    ]
    # CREATE_NO_WINDOW: ffmpeg is a console app: without this it opens its own
    # console window, which steals foreground focus away from xLights right as
    # the demo starts clicking.
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    return subprocess.Popen(cmd, stdin=subprocess.PIPE,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=creationflags)


def stop_recording(proc: subprocess.Popen, timeout: float = 10.0) -> None:
    try:
        proc.communicate(input=b"q", timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.terminate()
        proc.wait(timeout=5)


def perform_demo(win, section_durations: list[float], lead_in: float = 0.5) -> None:
    """Drive the actual double-click / pick-a-slice interaction in real time,
    timed to land within each section's recorded window.

    The 1.2s dwell after the double-click is deliberate: it's how long the
    wheel stays visible on screen before we pick a slice, so viewers actually
    get to see it (gdigrab also has real startup latency, so the caller pads
    an extra buffer before calling this — see start_recording's caller).
    """
    time.sleep(lead_in)
    for (label, _, _, _, spec), dur in zip(SECTIONS, section_durations):
        t0 = time.time()
        x, y = window_point(win.rect, spec["spot"])
        print(f"    {label}: double-click ({x}, {y})")
        pyautogui.moveTo(x, y, duration=0.3)
        time.sleep(0.3)
        pyautogui.doubleClick(x, y, interval=0.15)
        time.sleep(1.2)   # let the wheel stay on screen long enough to read
        dx, dy = spec["pick_offset"]
        pyautogui.click(x + dx, y + dy)
        elapsed = time.time() - t0
        time.sleep(max(0.0, dur - elapsed))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg not found on PATH")
    if shutil.which("ffprobe") is None:
        sys.exit("ffprobe not found on PATH")

    try:
        ac.call("getVersion", timeout=3.0)
    except Exception as e:
        sys.exit(
            "Cannot reach xLights automation API on port 49913.\n"
            "Please open xLights and enable xFade in Preferences > xFade, then retry.\n"
            f"Details: {e}"
        )

    min_s = float(engine.SHORTS_MIN_S)
    narr_tail = 0.3

    with tempfile.TemporaryDirectory(prefix="feature_showcase_") as tmp_str:
        tmp = Path(tmp_str)

        # Pass 1: generate all narration upfront so durations are known
        print("Pass 1: generating narration for all sections...")
        narr_files: list[Path] = []
        section_durations: list[float] = []
        for i, (label, _, _, short_narration, _) in enumerate(SECTIONS):
            narr_mp3 = tmp / f"narr_{i:02d}.mp3"
            print(f"  [{i+1}/{len(SECTIONS)}] {label}")
            engine.generate_narration(short_narration, narr_mp3)
            dur = engine._probe_audio_duration(narr_mp3)
            sec_dur = max(min_s, dur + narr_tail)
            narr_files.append(narr_mp3)
            section_durations.append(sec_dur)
            print(f"          narration={dur:.1f}s  section={sec_dur:.1f}s")

        intro_narr = tmp / "intro_narr.mp3"
        print("  [intro]")
        engine.generate_narration(
            f"xLights Bonus Gem. {engine.TITLE_LINE3} feature showcase.", intro_narr
        )
        intro_dur = engine._probe_audio_duration(intro_narr)
        print(f"          narration={intro_dur:.1f}s  (intro)")

        outro_narr = tmp / "outro_narr.mp3"
        print("  [outro]")
        engine.generate_narration("Thanks for watching! Like and subscribe.", outro_narr)
        outro_dur = engine._probe_audio_duration(outro_narr)
        print(f"          narration={outro_dur:.1f}s  (outro)")

        # Pass 2: reset to a fresh sequence and switch to the Sequencer tab
        print("\nPass 2: preparing xLights sequencer...")
        ac.close_sequence(force=True)
        total_secs = int(sum(section_durations)) + 5
        ac.new_sequence(total_secs, frame_ms=50)
        time.sleep(1.0)
        win = ss.find_xlights_window()
        ss.bring_to_front(win)
        click_at_fraction(win.rect, 0.094, 0.133)   # Sequencer tab
        time.sleep(0.5)

        # Pass 3: screen-record while performing the live demo
        print("Pass 3: recording the live demo...")
        raw_video = tmp / "raw.mp4"
        rect = capture_rect(win.rect)
        ss.bring_to_front(win)   # re-assert focus right before we start clicking
        proc = start_recording(rect, raw_video)
        time.sleep(1.5)   # gdigrab has real startup latency before frames flow
        try:
            perform_demo(win, section_durations)
        finally:
            time.sleep(1.0)
            stop_recording(proc)

        vid_dur = engine._probe_audio_duration(raw_video)
        print(f"  Recorded: {vid_dur:.1f}s")

        # Pass 4: assemble the Reel (reuses effect_showcase's vertical-crop /
        # blur / overlay / narration / intro-outro pipeline unchanged)
        print("\nPass 4: producing showcase video...")
        out = engine.build_video_shorts(
            raw_video, tmp, narr_files, section_durations,
            intro_narr, intro_dur, outro_narr, outro_dur,
        )

    total = sum(section_durations) + max(4.0, intro_dur) + max(4.0, outro_dur)
    print(f"\nDone! Saved to: {out}")
    print(f"Total duration: ~{total:.0f}s")


if __name__ == "__main__":
    main()
