"""Christmas Every Day matrix scenes: garage (see christmas_every_day_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from christmas_every_day_common import GARAGE, cues, run  # noqa: E402

PREFIX = "christmas_every_day_garage"
cues = cues


def build(s):
    run(s, GARAGE)
