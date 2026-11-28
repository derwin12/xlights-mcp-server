"""Christmas Every Day matrix scenes: bushes (see christmas_every_day_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from christmas_every_day_common import BUSHES, cues, run  # noqa: E402

PREFIX = "christmas_every_day_bushes"
cues = cues


def build(s):
    run(s, BUSHES)
