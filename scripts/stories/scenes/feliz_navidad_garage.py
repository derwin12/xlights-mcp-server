"""Feliz Navidad matrix scenes: garage (see feliz_navidad_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from feliz_navidad_common import GARAGE, cues, run  # noqa: E402

PREFIX = "feliz_navidad_garage"
cues = cues


def build(s):
    run(s, GARAGE)
