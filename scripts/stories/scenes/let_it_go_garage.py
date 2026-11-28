"""Let It Go matrix scenes: garage (see let_it_go_common.py for the shared scene plan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from let_it_go_common import GARAGE, cues, run  # noqa: E402

PREFIX = "let_it_go_garage"
cues = cues


def build(s):
    run(s, GARAGE)
