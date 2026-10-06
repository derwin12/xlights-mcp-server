"""Generate "MH Head Templates.xsq": every moving head sweeps a grid of pan/tilt poses with the
beam off (dimmer 0, shutter closed), so only the head/yoke body is visible in the render.

Poses are ordered as a serpentine (pan sweeps one way, then the other, stepping tilt between
sweeps) so each move is small and the motors' slew limit settles within POSE_MS.
Render it with render_clip, then pose k is on screen at (k + 0.9) * POSE_MS.

Usage:
    python scripts/mh_head_templates_sequence.py [--show F:/ShowFolderAI] [--pan-step 20]
        [--tilt-step 15] [--pose-ms 500]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import mh_calibration_sequence as cal  # noqa: E402
import prop_test_sequence as pts  # noqa: E402

DARK = "Dimmer: 0.000000&comma;0.000000&comma;1.000000&comma;0.000000;"


def dark_settings(pan, tilt):
    s = cal.mh_settings(pan, tilt)
    s = s.replace("Dimmer: 0.000000&comma;1.000000&comma;1.000000&comma;1.000000;", DARK)
    return s.replace(";Shutter: On", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", default="F:/ShowFolderAI")
    ap.add_argument("--name", default="MH Head Templates")
    ap.add_argument("--pan-step", type=int, default=20)
    ap.add_argument("--tilt-step", type=int, default=15)
    ap.add_argument("--pose-ms", type=int, default=500)
    ap.add_argument("--models", default=",".join(f"MH-{i}" for i in range(1, 9)))
    args = ap.parse_args()

    pans = list(range(-180, 181, args.pan_step))
    tilts = list(range(-90, 91, args.tilt_step))
    poses, t = [], 0
    for i, tilt in enumerate(tilts):
        for pan in (pans if i % 2 == 0 else pans[::-1]):
            poses.append({"pan": pan, "tilt": tilt, "start": t, "snap": t + int(args.pose_ms * 0.9)})
            t += args.pose_ms

    p = pts.Plan()
    for model in args.models.split(","):
        for ps in poses:
            p.add(model, "Moving Head", ps["start"], ps["start"] + args.pose_ms,
                  dark_settings(ps["pan"], ps["tilt"]), ["#FFFFFF"])
    out = Path(args.show) / f"{args.name}.xsq"
    pts.write(p, t, out)
    (Path(args.show) / f"{args.name}.poses.json").write_text(json.dumps(poses, indent=1))
    print(f"wrote {out}: {len(poses)} poses x {len(args.models.split(','))} heads, {t / 1000:.0f}s")


if __name__ == "__main__":
    main()
