"""White Christmas matrix scenes: garage (see white_christmas_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from white_christmas_common import GARAGE, cues, run  # noqa: E402

PREFIX = "white_christmas_garage"
cues = cues


def build(s):
    run(s, GARAGE)
