"""Little Drummer Boy matrix scenes: garage (see drummer_boy_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from drummer_boy_common import GARAGE, cues, run  # noqa: E402

PREFIX = "drummer_boy_garage"
cues = cues


def build(s):
    run(s, GARAGE)
