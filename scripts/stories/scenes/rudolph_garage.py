"""Rudolph the Red-Nosed Reindeer matrix scenes: garage (see rudolph_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rudolph_common import GARAGE, cues, run  # noqa: E402

PREFIX = "rudolph_garage"
cues = cues


def build(s):
    run(s, GARAGE)
