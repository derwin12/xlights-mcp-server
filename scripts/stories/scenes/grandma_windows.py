"""Grandma Got Run Over By A Reindeer matrix scenes: windows (see grandma_common.py for the shared plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from grandma_common import WINDOWS, cues, run  # noqa: E402

PREFIX = "grandma_windows"
cues = cues


def build(s):
    run(s, WINDOWS)
