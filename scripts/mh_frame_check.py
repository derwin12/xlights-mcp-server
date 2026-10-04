"""Write and check the "MH Frame Calibration" sequence so a render of the "MH Preview" can be trusted.

render_clip captures whatever the House Preview pane shows, at the pane's pixel size. The pane must be at max
size with the "MH Preview" layout group selected; this checks that the frame is what the comparisons assume.

    python scripts/mh_frame_check.py write                 # writes F:/ShowFolderAI/MH Frame Calibration.xsq
    (render it with render_clip, 0-6000 ms)
    python scripts/mh_frame_check.py check VIDEO.mp4       # compares lit-lens positions with the expected frame

The sequence lights MH-2..MH-7 in steer poses (leans -40, -17, -6, 8, 24, 42 deg) from 3 to 6 s.
"""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

SIZE = (1920, 1058)  # width, height of the MH Preview export with the House Preview pane at max size
LENS_X = (409, 554, 695, 1096, 1242, 1390)  # lens centre x of MH-2..MH-7 in that frame (+-15 px)
LENS_Y = 912  # approximate
LEANS = (-40.0, -17.0, -6.0, 8.0, 24.0, 42.0)
LEANS8 = (-46.0, -40.0, -17.0, -6.0, 8.0, 24.0, 42.0, 48.0)  # --heads 8: MH-1..MH-8 for a wider preview
LENS_X8 = (268, 408, 553, 694, 1095, 1242, 1389, 1532)  # lens centre x of MH-1..MH-8, --heads 8 (+-15 px)
HEAD_ROW_CROP8 = "crop=1500:110:190:870"  # ffmpeg crop of the MH-1..MH-8 head row
SHOW = Path("F:/ShowFolderAI")
HEAD_ROW_CROP = "crop=1100:110:340:870"  # ffmpeg crop of the MH-2..MH-7 head row in a frame of SIZE


def write(heads=6):
    import prop_test_sequence as pts
    import video_beams_to_xsq as v
    on = "Dimmer: 0.0&comma;1.0&comma;1.0&comma;1.0"
    leans = LEANS8 if heads == 8 else LEANS
    first = 1 if heads == 8 else 2
    pan, tilt = v.steer_pose(np.array(leans))
    plan = pts.Plan()
    for i, (p, t) in enumerate(zip(pan, tilt)):
        m = f"MH-{i + first}"
        plan.add(m, "Moving Head", 0, 3000, v.mh_settings(p, p, t, t, (0.0, 0.0, 1.0), v.DARK_DIMMER, False, False), ["#FFFFFF"])
        plan.add(m, "Moving Head", 3000, 6000, v.mh_settings(p, p, t, t, (0.0, 0.0, 1.0), on, True, False), ["#FFFFFF"])
    out = SHOW / "MH Frame Calibration.xsq"
    pts.write(plan, 6000, out)
    print(f"wrote {out}; render it with render_clip (0-6000 ms) and run: mh_frame_check.py check VIDEO")


def check(video, heads=6):
    lens_x = LENS_X8 if heads == 8 else LENS_X
    cap = cv2.VideoCapture(video)
    cap.set(cv2.CAP_PROP_POS_MSEC, 5000)
    ok, f = cap.read()
    if not ok:
        sys.exit("could not read a frame at 5 s")
    h, w = f.shape[:2]
    print(f"frame {w}x{h} (expected {SIZE[0]}x{SIZE[1]})")
    if (w, h) != SIZE:
        print("WRONG FRAME SIZE: the House Preview pane is not at max size (and the MH Preview may not be selected). "
              "Maximise the House Preview, select the 'MH Preview' layout group, and render again; "
              "do not compare against the source until this passes.")
        sys.exit(1)
    b, g, r = (f[..., i].astype(int) for i in range(3))
    lens = ((g > 150) & (b > 150) & (r < 120) & (g - r > 60)).astype(np.uint8)  # the cyan lens of a lit head, tilted or not
    n, _, stats, cent = cv2.connectedComponentsWithStats(lens)
    blobs = sorted((c[0], c[1], s[cv2.CC_STAT_AREA]) for c, s in zip(cent[1:], stats[1:]) if s[cv2.CC_STAT_AREA] > 100)
    xs = [round(b_[0]) for b_ in blobs]
    print("lit lens centres x:", xs, "| expected:", list(lens_x) if lens_x else "not measured yet")
    if len(xs) != heads:
        print("MISMATCH: expected", heads, "lit lenses (is the MH Preview selected and the sequence rendered 3-6 s?)")
        sys.exit(1)
    if not lens_x:
        print(f"8 lenses found: set LENS_X8 = {tuple(xs)} here, then re-run check")
        return
    off = [a - e for a, e in zip(xs, lens_x)]
    scale = (xs[-1] - xs[0]) / (lens_x[-1] - lens_x[0])
    print(f"offsets {off}; scale vs expected {scale:.3f}")
    if (w, h) == SIZE and max(abs(o) for o in off) <= 15 and abs(scale - 1) < 0.02:
        print("OK: the MH Preview framing matches; the head-row crop and comparisons are valid")
    else:
        print("DIFFERENT framing: re-measure the head positions before comparing (update LENS_X / SIZE here and in the skill)")
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["write", "check"])
    ap.add_argument("video", nargs="?")
    ap.add_argument("--heads", type=int, choices=[6, 8], default=6, help="6 = MH-2..MH-7 (default), 8 = MH-1..MH-8 wide preview")
    a = ap.parse_args()
    write(a.heads) if a.cmd == "write" else check(a.video or sys.exit("check needs a VIDEO"), a.heads)


if __name__ == "__main__":
    main()
