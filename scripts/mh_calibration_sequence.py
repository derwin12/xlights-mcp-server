"""Generate "MH Calibration.xsq": one moving head holds a grid of known pan/tilt poses.

Each pose lasts 1 s. Render a frame mid-pose and measure the beam's screen angle to
learn how pan/tilt map to what a fixed camera sees (see video_beam_analysis.py).

Usage:
    python scripts/mh_calibration_sequence.py [--show F:/ShowFolderAI] [--model MH-1]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import prop_test_sequence as pts  # noqa: E402  (reuses its .xsq writer)

PANS = [-90, -45, 0, 45, 90]
TILTS = [-60, -30, 0, 30, 60]
POSE_MS = 1000


def mh_settings(pan, tilt, head=1, rgb_hsv="0.000000&comma;0.000000&comma;1.000000"):
    slot = (f"Color: {rgb_hsv};Dimmer: 0.000000&comma;1.000000&comma;1.000000&comma;1.000000;"
            f"Pan: {pan:.1f};Tilt: {tilt:.1f};PanOffset: 0.0;TiltOffset: 0.0;"
            f"Groupings: 1.0;Cycles: 1.0;Heads: {head};Shutter: On")
    return (f"B_CHOICE_BufferStyle=Per Model Default,E_CHECKBOX_MHIgnorePan=0,E_CHECKBOX_MHIgnoreTilt=0,"
            f"E_NOTEBOOK1=Position,E_NOTEBOOK2=Color,E_SLIDER_MHCycles=10,E_SLIDER_MHGroupings=1,"
            f"E_SLIDER_MHPan={int(pan * 10)},E_SLIDER_MHPanOffset=0,E_SLIDER_MHPathScale=0,"
            f"E_SLIDER_MHTilt={int(tilt * 10)},E_SLIDER_MHTiltOffset=0,E_SLIDER_MHTimeOffset=0,"
            f"E_TEXTCTRL_MH1_Settings={slot}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", default="F:/ShowFolderAI")
    ap.add_argument("--model", default="MH-1")
    ap.add_argument("--name", default="MH Calibration")
    args = ap.parse_args()

    p = pts.Plan()
    poses = []
    t = 0
    for pan in PANS:
        for tilt in TILTS:
            p.add(args.model, "Moving Head", t, t + POSE_MS, mh_settings(pan, tilt), ["#FFFFFF"])
            poses.append({"pan": pan, "tilt": tilt, "start": t, "mid": t + POSE_MS // 2})
            t += POSE_MS
    out = Path(args.show) / f"{args.name}.xsq"
    pts.write(p, t, out)
    (Path(args.show) / f"{args.name}.poses.json").write_text(json.dumps(poses, indent=1))
    print(f"wrote {out} ({len(poses)} poses, {t / 1000:.0f}s)")


if __name__ == "__main__":
    main()
