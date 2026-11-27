"""Little Drummer Boy matrix scenes: windows (see drummer_boy_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from drummer_boy_common import WINDOWS, cues, run  # noqa: E402

PREFIX = "drummer_boy_windows"
cues = cues


def build(s):
    run(s, WINDOWS)
