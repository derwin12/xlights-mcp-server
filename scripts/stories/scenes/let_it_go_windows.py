"""Let It Go matrix scenes: windows (see let_it_go_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from let_it_go_common import WINDOWS, cues, run  # noqa: E402

PREFIX = "let_it_go_windows"
cues = cues


def build(s):
    run(s, WINDOWS)
