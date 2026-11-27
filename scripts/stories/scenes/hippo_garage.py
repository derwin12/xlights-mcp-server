"""'I Want a Hippopotamus for Christmas' matrix scenes: garage (see hippo_common.py; windows: hippopotamus_windows.py)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hippo_common import GARAGE, cues, run  # noqa: E402

PREFIX = "hippo_garage"
cues = cues


def build(s):
    run(s, GARAGE)
