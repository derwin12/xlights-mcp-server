"""Feliz Navidad matrix scenes: windows (see feliz_navidad_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from feliz_navidad_common import WINDOWS, cues, run  # noqa: E402

PREFIX = "feliz_navidad_windows"
cues = cues


def build(s):
    run(s, WINDOWS)
