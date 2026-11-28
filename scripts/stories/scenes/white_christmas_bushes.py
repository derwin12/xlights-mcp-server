"""White Christmas matrix scenes: bushes (see white_christmas_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from white_christmas_common import BUSHES, cues, run  # noqa: E402

PREFIX = "white_christmas_bushes"
cues = cues


def build(s):
    run(s, BUSHES)
