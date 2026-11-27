"""The Fox matrix scenes: bushes (see the_fox_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from the_fox_common import BUSHES, cues, run  # noqa: E402

PREFIX = "the_fox_bushes"
cues = cues


def build(s):
    run(s, BUSHES)
