"""You're a Mean One matrix scenes: garage (see grinch_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from grinch_common import GARAGE, cues, run  # noqa: E402

PREFIX = "grinch_garage"
cues = cues


def build(s):
    run(s, GARAGE)
