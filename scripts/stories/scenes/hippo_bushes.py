"""'I Want a Hippopotamus for Christmas' matrix scenes: bushes (see hippo_common.py; windows: hippopotamus_windows.py)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hippo_common import BUSHES, cues, run  # noqa: E402

PREFIX = "hippo_bushes"
cues = cues


def build(s):
    run(s, BUSHES)
