r"""Skeleton band (guitarist, singer, drummer) on the matrices, playing along with the song.

Usage:
    python scripts/skeleton_band.py SONG.xsq [--show F:\ShowFolderAI] [--models Matrix] [--figure male|female|mixed]
        [--stage] [--energy 1.0] [--shirts purple red teal] [--section-shirts "Chorus=#FF4000/#FFC000/#FF4000"]
        [--off "Ending,Instrumental"] [--over-pictures] [--over-video]

One Shader effect per bar on a new top layer, running <show>\Shaders\Skeleton Band.fs. The drummer's kick
follows a "Kick Hits" track, or drum hits found in the audio; the singer's jaw follows the lyric phonemes.
Matrices with a Video effect are skipped, and the band steps aside while a matrix shows its own pictures.
Running it again replaces the band layer it made before (the dance crew's layer is left alone).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from xlights_mcp.sprites import dancers as d
from xlights_mcp.sprites.band_place import place_band
from xlights_mcp.sprites.place import parse_section_map


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xsq")
    ap.add_argument("--show", default=r"F:\ShowFolderAI")
    ap.add_argument("--models", nargs="+", default=["Matrix"])
    ap.add_argument("--figure", default="male", choices=d.FIGURES, help="mixed alternates, starting female")
    ap.add_argument("--shirts", nargs="+", help="guitarist, singer, drummer colours: names or #RRGGBB")
    ap.add_argument("--section-shirts", help='colours per section, e.g. "Chorus=#FF4000/#FFC000/#FF4000"')
    ap.add_argument("--off", default="", help='sections with no band, e.g. "Ending,Instrumental"')
    ap.add_argument("--section-track", default="Sections")
    ap.add_argument("--stage", action="store_true", help="floor, beat-swapping spotlights and sparkles")
    ap.add_argument("--energy", type=float, default=1.0, help="how much the loudness drives the head bobs")
    ap.add_argument("--over-pictures", action="store_true", help="keep playing while the matrix shows its pictures")
    ap.add_argument("--over-video", action="store_true", help="also use matrices that show a Video effect")
    a = ap.parse_args()

    off = [s.strip() for s in a.off.split(",") if s.strip()]
    shirts = {k: v.split("/") for k, v in parse_section_map(a.section_shirts).items()}
    for p in place_band(Path(a.xsq), Path(a.show), a.models, a.figure, a.shirts, a.stage, a.energy,
                        section_track=a.section_track if (shirts or off) else None, section_shirts=shirts,
                        off_sections=off, over_video=a.over_video, over_pictures=a.over_pictures):
        if p.skipped:
            print(f"{p.model}: skipped, {p.skipped} (--over-video to use it anyway)")
        else:
            print(f"{p.model}: {p.effects} Shader effects; kick from {p.kick_source}, singing from {p.vocal_source}")


if __name__ == "__main__":
    main()
