"""Grandma Got Run Over By A Reindeer matrix scenes: garage (see grandma_common.py for the shared plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from grandma_common import GARAGE, cues, run  # noqa: E402

PREFIX = "grandma_garage"
cues = cues


def build(s):
    run(s, GARAGE)
