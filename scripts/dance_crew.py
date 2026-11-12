r"""Pixel skeleton dance crew on the matrices, a pose on every beat.

Usage:
    python scripts/dance_crew.py SONG.xsq [--show F:\ShowFolderAI] [--models "Matrix 2" "Lyrics Matrix"]
        [--routine thriller|party|wave] [--style unison|mirror|canon] [--dancers 3] [--scale 1]
        [--figure male|female|mixed] [--bounce] [--start 30] [--end 60]
        [--sections "Intro=wave,Verse=robot,Chorus=shuffle,Ending=none"] [--section-shirts "Chorus=teal/pink"]
        [--section-dancers "Intro=1,Verse=2,Chorus=3"]
        [--stage] [--shader [--smoothing 0.35] [--energy 1.0] [--per-section]]
    python scripts/dance_crew.py --preview OUT_DIR [--routine thriller] [--style canon] [--dancers 3]
    python scripts/dance_crew.py SONG.xsq --remove --models "Lyrics Matrix"

Reads the sequence's Beats timing track (labels 1..4 mark the downbeats) and puts one Pictures effect per bar on a
new top layer of each model, a GIF with one frame per beat (two with --bounce, the second dipping a row). Loop GIF
is off, so xLights stretches each GIF over its bar and the poses follow the tempo. Transparent Black is on, so
effects underneath keep running around the dancers. Matrices showing a Video effect are left alone
unless --over-video. The GIFs go to <show>\Images\Dancers. Re-running replaces
the layer it made before. --preview just writes an enlarged looping GIF and a pose sheet to look at.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

from xlights_mcp.sprites import dancers as d
from xlights_mcp.sprites.place import parse_section_map, place_crew, remove_crew


def preview(out: Path, routine: str, style: str, n: int, bounce: bool, figure: str = "male") -> None:
    out.mkdir(parents=True, exist_ok=True)
    poses = d.timeline(routine, sum(len(b) for b in d.ROUTINES[routine]) + n)
    crew = d.Crew(d.crew_from_style(n, style, figure=figure), scale=10)
    fpb = 2 if bounce else 1
    gif = out / f"{routine}-{style}-{figure}-preview.gif"
    d.save_gif(d.bar_frames(crew, poses, 0, len(poses), fpb), gif, ms_per_frame=500 // fpb)
    names = sorted(d.POSES)
    s, cols = 8, 5
    sheet = Image.new("RGB", (cols * (d.W + 2) * s, -(-len(names) // cols) * (d.H + 2) * s), (30, 30, 30))
    for i, name in enumerate(names):
        im = crew.dancers[0].draw(d.POSES[name]).resize((d.W * s, d.H * s), Image.NEAREST)
        sheet.paste(im, ((i % cols) * (d.W + 2) * s, (i // cols) * (d.H + 2) * s))
    sheet.save(out / "poses.png")
    print(f"wrote {gif} and {out / 'poses.png'}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xsq", nargs="?")
    ap.add_argument("--show", default=r"F:\ShowFolderAI")
    ap.add_argument("--models", nargs="+", default=["Matrix 2"])
    ap.add_argument("--routine", default="thriller", choices=sorted(d.ROUTINES))
    ap.add_argument("--style", default="unison", choices=["unison", "mirror", "canon"])
    ap.add_argument("--dancers", type=int, help="default: as many as fit")
    ap.add_argument("--scale", type=int, help="LEDs per sprite pixel; default: largest that fits")
    ap.add_argument("--shirts", nargs="+", help=f"shirt or dress colours: {', '.join(d.SHIRTS)} or #RRGGBB")
    ap.add_argument("--sections", help='routine per section of --section-track, by label prefix, e.g. '
                    '"Intro=wave,Verse=robot,Chorus=shuffle,Ending=none" (none = no dancers)')
    ap.add_argument("--section-shirts", help='colours per section, e.g. "Verse=purple/pink,Chorus=#00E0FF/pink"')
    ap.add_argument("--section-dancers", help='dancer count per section, e.g. "Intro=1,Verse=2,Chorus=3,Bridge=0"')
    ap.add_argument("--section-track", default="Sections")
    ap.add_argument("--shader", action="store_true",
                    help="use the Dance Crew shader (smooth moves, bounce follows the music) instead of GIFs")
    ap.add_argument("--smoothing", type=float, default=0.35, help="shader: 0 snaps pose to pose, 1 glides all beat")
    ap.add_argument("--energy", type=float, default=1.0, help="shader: how much the loudness drives the bounce")
    ap.add_argument("--per-section", action="store_true",
                    help="shader: one effect per section instead of per bar, so value curves can span a section")
    ap.add_argument("--over-pictures", action="store_true",
                    help="keep dancing while the matrix shows its own pictures (by default the crew steps aside)")
    ap.add_argument("--stage", action="store_true",
                    help="floor, beat-swapping spotlights and sparkles around the crew, drawn at the matrix size")
    ap.add_argument("--figure", default="male", choices=d.FIGURES, help="mixed alternates, starting female")
    ap.add_argument("--bounce", action="store_true", help="dip a row on every off-beat")
    ap.add_argument("--track", default="Beats")
    ap.add_argument("--start", type=float, default=0.0, help="seconds")
    ap.add_argument("--end", type=float, help="seconds")
    ap.add_argument("--preview", help="write a preview GIF and pose sheet to this folder instead")
    ap.add_argument("--over-video", action="store_true",
                    help="also put dancers on matrices that show a Video effect (skipped by default)")
    ap.add_argument("--remove", action="store_true",
                    help="take the crew layer off --models instead (a model left empty leaves the sequence)")
    a = ap.parse_args()

    if a.preview:
        preview(Path(a.preview), a.routine, a.style, a.dancers or 3, a.bounce, a.figure)
        return
    if not a.xsq:
        ap.error("give an .xsq, or --preview DIR")
    if a.remove:
        print("removed from:", ", ".join(remove_crew(Path(a.xsq), a.models)) or "nothing")
        return
    for p in place_crew(Path(a.xsq), Path(a.show), a.models, a.routine, a.style, a.dancers, a.scale, a.shirts,
                        2 if a.bounce else 1, a.track, start_s=a.start, end_s=a.end, over_video=a.over_video,
                        figure=a.figure, section_track=a.section_track if (a.sections or a.section_shirts or a.section_dancers) else None,
                        section_routines=parse_section_map(a.sections),
                        section_shirts={k: v.split("/") for k, v in parse_section_map(a.section_shirts).items()},
                        stage=a.stage, shader=a.shader, smoothing=a.smoothing, energy=a.energy,
                        section_dancers={k: int(v) for k, v in parse_section_map(a.section_dancers).items()},
                        per_section=a.per_section, over_pictures=a.over_pictures):
        if p.skipped:
            print(f"{p.model}: skipped, {p.skipped} (--over-video to use it anyway)")
        else:
            what = "Shader effects" if a.shader else f"bars, {p.files} GIFs"
            print(f"{p.model}: up to {p.dancers} dancers at scale {p.scale}, {p.bars} {what}")


if __name__ == "__main__":
    main()
