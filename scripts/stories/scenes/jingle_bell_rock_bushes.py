"""Jingle Bell Rock matrix scenes: bushes (see jingle_bell_rock_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jingle_bell_rock_common import BUSHES, cues, run  # noqa: E402

PREFIX = "jingle_bell_rock_bushes"
cues = cues


def build(s):
    run(s, BUSHES)
