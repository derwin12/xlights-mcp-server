"""Render every crash-dump sequence under a root folder to a full-house MP4.

Each subfolder is treated as its own xLights show folder: switch xLights to it
(changeShowFolder), load the .xsq inside, renderAll, exportVideoPreview.
Videos go to <root>/../rendered_videos by default. Already-rendered videos are
skipped, so the script can be re-run to resume. Requires xLights running with
xFade automation enabled.

Usage: python scripts/batch_render_crash_dumps.py [--root DIR] [--out DIR] [--top N] [--limit N] [--only SUBSTR]
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from xlights_mcp.xlights import automation_client as ac  # noqa: E402

DEFAULT_ROOT = Path(r"C:\Users\daryl\PycharmProjects\xlCrash\extracted_xsq")


def safe_name(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()[:150]


def xsq_size(folder: Path) -> int:
    return max((f.stat().st_size for f in folder.glob("*.xsq")), default=0)


def as_animation(xsq: Path) -> Path | None:
    """If the sequence's audio isn't on disk, write a temp Animation-type copy
    beside it (no mediaFile; sequenceDuration is kept). Returns None if the
    media exists and the original can be used as-is."""
    text = xsq.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<mediaFile>([^<]*)</mediaFile>", text)
    if m and m.group(1).strip() and Path(m.group(1).strip()).exists():
        return None
    text = re.sub(r"<mediaFile>[^<]*</mediaFile>", "<mediaFile></mediaFile>", text)
    text = re.sub(r"<sequenceType>[^<]*</sequenceType>", "<sequenceType>Animation</sequenceType>", text)
    anim = xsq.with_name(xsq.stem + "__anim.xsq")
    anim.write_text(text, encoding="utf-8")
    return anim


def process(folder: Path, out_dir: Path) -> str:
    xsqs = sorted(folder.glob("*.xsq"))
    if not xsqs:
        return "skip: no xsq"
    xsq = xsqs[0]
    video = out_dir / f"{safe_name(folder.name)}.mp4"
    if video.exists() and video.stat().st_size > 0:
        return "skip: already rendered"

    ac.call(
        "changeShowFolder", timeout=ac._RENDER_TIMEOUT,
        folder=str(folder).replace("\\", "/"), force="true",
    )
    anim = as_animation(xsq)
    try:
        ac.open_sequence(str(anim or xsq), force=True)
        ac.render_all()
        ac.export_video_preview(str(video))
    finally:
        if anim:
            anim.unlink(missing_ok=True)
    if not video.exists():
        raise ac.AutomationError("export reported success but no video file was written")
    return f"ok: {video.stat().st_size / 1e6:.1f} MB"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--top", type=int, default=None, help="only the N folders with the largest .xsq")
    p.add_argument("--only", default=None, help="only folders whose name contains this text")
    args = p.parse_args()

    out_dir = args.out or args.root.parent / "rendered_videos"
    out_dir.mkdir(parents=True, exist_ok=True)
    ac.get_version()  # fail fast if xLights isn't reachable

    folders = sorted(d for d in args.root.iterdir() if d.is_dir())
    if args.only:
        folders = [d for d in folders if args.only.lower() in d.name.lower()]
    if args.top:
        folders = sorted(folders, key=xsq_size, reverse=True)[: args.top]
    if args.limit:
        folders = folders[: args.limit]

    log = out_dir / "render_log.txt"
    failures = 0
    for i, folder in enumerate(folders, 1):
        t0 = time.time()
        try:
            status = process(folder, out_dir)
        except Exception as e:  # keep going; one bad dump shouldn't stop the batch
            status = f"FAIL: {e}"
            failures += 1
        line = f"[{i}/{len(folders)}] {time.time() - t0:5.0f}s {folder.name} -> {status}"
        print(line, flush=True)
        with log.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    print(f"done. {failures} failure(s). videos in {out_dir}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
