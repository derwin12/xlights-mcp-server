"""Frosty the Snowman matrix scenes: garage (see frosty_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from frosty_common import GARAGE, cues, run  # noqa: E402

PREFIX = "frosty_garage"
cues = cues


def build(s):
    run(s, GARAGE)
