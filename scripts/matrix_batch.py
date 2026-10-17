"""Run matrix_video_extract over the todo rows of the Pixel Pro matrix CSV.

    python scripts/matrix_batch.py CSV OUT_DIR WORK_DIR [--limit N]

For each row with status "todo": download the YouTube preview into WORK_DIR, detect the 50x24 grid, write
<prefix>-24x50-matrix-native-50x24.mp4 and <prefix>-24x50-matrix-800x384.mp4 into OUT_DIR, sanity-check the result,
then update the CSV (status done / failed + note) and delete the download. A failure never stops the batch.
"""
from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent


def prefix(name: str) -> str:
    n = re.sub(r"\bmatrix\b", "", name, flags=re.I)
    n = re.sub(r"[^A-Za-z0-9]+", "-", n).strip("-")
    return n


def duration(p: Path) -> float:
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(p)]).decode())


def mean_brightness(p: Path) -> float:
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vf", "fps=1,scale=50:24,format=gray", "-f", "rawvideo", "-"],
                         capture_output=True).stdout
    return sum(out) / max(len(out), 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("out_dir")
    ap.add_argument("work_dir")
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    csv_path, out_dir, work = Path(a.csv), Path(a.out_dir), Path(a.work_dir)
    work.mkdir(parents=True, exist_ok=True)

    def load():
        return list(csv.DictReader(open(csv_path, encoding="utf-8")))

    def save(rows):
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    rows = load()
    todo = [i for i, r in enumerate(rows) if r["status"] == "todo"]
    if a.limit:
        todo = todo[:a.limit]
    print(f"{len(todo)} to do", flush=True)
    for n, i in enumerate(todo, 1):
        r = rows[i]
        pre = prefix(r["name"])
        vid = r["youtube_url"].split("v=")[-1]
        d = work / vid
        d.mkdir(exist_ok=True)
        note = ""
        try:
            subprocess.run([sys.executable, str(HERE / "fetch_video.py"), r["youtube_url"], "--out-dir", str(d)],
                           check=True, capture_output=True)
            src = d / f"{vid}.mp4"
            big = out_dir / f"{pre}-24x50-matrix-800x384.mp4"
            nat = out_dir / f"{pre}-24x50-matrix-native-50x24.mp4"
            p = subprocess.run([sys.executable, str(HERE / "matrix_video_extract.py"), str(src), str(big), "--auto",
                                "--cols", "50", "--rows", "24", "--agg", "max", "--scale", "16", "--filter", "neighbor",
                                "--native", str(nat)], capture_output=True, text=True)
            if p.returncode:
                raise RuntimeError((p.stdout + p.stderr).strip().splitlines()[-1][:200])
            ds, dn = duration(src), duration(nat)
            br = mean_brightness(nat)
            if abs(ds - dn) > 1.0:
                raise RuntimeError(f"length {dn:.1f}s vs source {ds:.1f}s")
            if br < 1.0:
                raise RuntimeError(f"output nearly black (mean {br:.2f})")
            extra = "; ".join(l[6:].strip() for l in p.stdout.splitlines() if l.startswith("note:"))
            r["status"], r["output_prefix"], note = "done", pre, f"{dn:.0f}s, mean brightness {br:.1f}" + (f"; {extra}" if extra else "")
        except Exception as e:  # noqa: BLE001 - keep going, record why
            r["status"], r["output_prefix"], note = "failed", pre, str(e)[:200]
        r["note"] = note
        save(rows)
        shutil.rmtree(d, ignore_errors=True)
        print(f"[{n}/{len(todo)}] {r['status']:6} {pre} {note}", flush=True)
    print("BATCH DONE", flush=True)


if __name__ == "__main__":
    main()
