"""Rudolph the Red-Nosed Reindeer matrix scenes: windows (see rudolph_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rudolph_common import WINDOWS, cues, run  # noqa: E402

PREFIX = "rudolph_windows"
cues = cues


def build(s):
    run(s, WINDOWS)
