"""Yellow Snow matrix scenes: windows (see yellow_snow_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yellow_snow_common import WINDOWS, cues, run  # noqa: E402

PREFIX = "yellow_snow_windows"
cues = cues


def build(s):
    run(s, WINDOWS)
