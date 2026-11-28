"""'Rockin' Around the Christmas Tree' matrix scenes: windows (see rockin_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rockin_common import WINDOWS, cues, run  # noqa: E402

PREFIX = "rockin_windows"
cues = cues


def build(s):
    run(s, WINDOWS)
