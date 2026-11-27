"""Frosty the Snowman matrix scenes: bushes (see frosty_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from frosty_common import BUSHES, cues, run  # noqa: E402

PREFIX = "frosty_bushes"
cues = cues


def build(s):
    run(s, BUSHES)
