"""Sleigh Ride matrix scenes: windows (see sleigh_ride_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sleigh_ride_common import WINDOWS, cues, run  # noqa: E402

PREFIX = "sleigh_ride_windows"
cues = cues


def build(s):
    run(s, WINDOWS)
