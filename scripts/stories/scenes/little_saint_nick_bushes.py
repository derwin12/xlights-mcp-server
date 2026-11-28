"""Little Saint Nick matrix scenes: bushes (see little_saint_nick_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from little_saint_nick_common import BUSHES, cues, run  # noqa: E402

PREFIX = "little_saint_nick_bushes"
cues = cues


def build(s):
    run(s, BUSHES)
