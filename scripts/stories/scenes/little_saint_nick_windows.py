"""Little Saint Nick matrix scenes: windows (see little_saint_nick_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from little_saint_nick_common import WINDOWS, cues, run  # noqa: E402

PREFIX = "little_saint_nick_windows"
cues = cues


def build(s):
    run(s, WINDOWS)
