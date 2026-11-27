"""Crazy Frog Jingle Bells matrix scenes: bushes (see crazy_frog_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crazy_frog_common import BUSHES, cues, run  # noqa: E402

PREFIX = "crazy_frog_bushes"
cues = cues


def build(s):
    run(s, BUSHES)
