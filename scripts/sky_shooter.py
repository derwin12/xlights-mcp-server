r"""Sky Shooter (Christmas formation shooter) on the matrices, playing along with the song.

Usage:
    python scripts/sky_shooter.py SONG.xsq [--show F:\ShowFolderAI] [--models Matrix] [--colours "#DC1E28" green blue]
        [--section-colours "Chorus=#FFD700/#FF0000/#00FF00"] [--off "Ending"] [--energy 1.0]
        [--start 88] [--end 120] [--over-pictures] [--over-video]

A sleigh cannon shoots down a swaying formation of baubles, snowflakes and presents: one ornament per kick, a new
wave when one is cleared. Kicks come from a "Kick Hits" track, or drum hits found in the audio. One Shader effect
per bar on a new top layer, running <show>\Shaders\Sky Shooter.fs; ornament colours are the palette. Matrices
with a Video effect are skipped, and the game steps aside while a matrix shows its own pictures. Running it again
replaces the layer it made before.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from xlights_mcp.sprites.place import parse_section_map
from xlights_mcp.sprites.shooter_place import place_shooter


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xsq")
    ap.add_argument("--show", default=r"F:\ShowFolderAI")
    ap.add_argument("--models", nargs="+", default=["Matrix"])
    ap.add_argument("--colours", nargs="+", help="ornament colours (3): names or #RRGGBB")
    ap.add_argument("--section-colours", help='ornament colours per section, e.g. "Chorus=#FFD700/#FF0000/#00FF00"')
    ap.add_argument("--off", default="", help='sections with no game, e.g. "Ending,Intro"')
    ap.add_argument("--section-track", default="Sections")
    ap.add_argument("--start", type=float, default=0.0, help="seconds: play from the first bar starting here")
    ap.add_argument("--end", type=float, help="seconds: play up to the last bar ending by here")
    ap.add_argument("--energy", type=float, default=1.0, help="how much the loudness makes the formation dip")
    ap.add_argument("--over-pictures", action="store_true", help="keep playing while the matrix shows its pictures")
    ap.add_argument("--over-video", action="store_true", help="also use matrices that show a Video effect")
    a = ap.parse_args()

    off = [s.strip() for s in a.off.split(",") if s.strip()]
    cols = {k: v.split("/") for k, v in parse_section_map(a.section_colours).items()}
    for p in place_shooter(Path(a.xsq), Path(a.show), a.models, a.colours, a.energy,
                           section_track=a.section_track if (cols or off) else None, section_colours=cols,
                           off_sections=off, over_video=a.over_video, over_pictures=a.over_pictures,
                           start_s=a.start, end_s=a.end):
        if p.skipped:
            print(f"{p.model}: skipped, {p.skipped} (--over-video to use it anyway)")
        else:
            print(f"{p.model}: {p.effects} Shader effects, {p.waves} waves; kicks from {p.kick_source}")


if __name__ == "__main__":
    main()
