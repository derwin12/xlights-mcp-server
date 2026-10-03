"""Download a video (YouTube or any site yt-dlp supports) for beam analysis.

video_beam_analysis.py calls this when given a URL instead of a file, so
    python scripts/video_beam_analysis.py "https://www.youtube.com/watch?v=..." beams.json --heads ...
works directly. Files are cached by video id, so a repeat run reuses the download.

Standalone:
    python scripts/fetch_video.py URL [--out-dir DIR] [--audio] [--max-height 1080] [--info]
        --audio   also write the soundtrack as <id>.mp3 next to the video (for video_beams_to_xsq.py --audio)
        --info    print title / duration / resolution only, download nothing

Needs a recent yt-dlp (pip install -U yt-dlp; YouTube changes often) and Node.js on PATH for YouTube.
A "403 Forbidden" partway through a download means one of those is missing or out of date.
Only download videos you have the right to use; YouTube's terms restrict downloading.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_DIR = Path.home() / ".cache" / "xlights-mcp" / "videos"


def _ydl(opts):
    try:
        import yt_dlp
    except ImportError:
        sys.exit("yt-dlp is required for URLs: pip install yt-dlp")
    # YouTube stream URLs need a small JS challenge solved: without a runtime the download starts, then
    # 403s partway through. yt-dlp only enables Deno by default, so enable Node when it is installed.
    js = {"js_runtimes": {"node": {}}, "remote_components": ["ejs:github"]} if shutil.which("node") else {}
    return yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "noprogress": True, **js, **opts})


def info(url):
    """Title, duration and best resolution without downloading."""
    with _ydl({"skip_download": True}) as y:
        i = y.extract_info(url, download=False)
    return {"id": i["id"], "title": i.get("title"), "duration": i.get("duration"),
            "width": i.get("width"), "height": i.get("height"), "fps": i.get("fps")}


def fetch(url, out_dir=DEFAULT_DIR, max_height=1080, audio=False):
    """Download url as an mp4 under out_dir (cached by id) and return its path."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    opts = {"outtmpl": str(out_dir / "%(id)s.%(ext)s"), "merge_output_format": "mp4",
            "format": f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]/best"}
    with _ydl(opts) as y:
        meta = y.extract_info(url, download=False)
        path = out_dir / f"{meta['id']}.mp4"
        if path.exists():
            print(f"using cached {path}", file=sys.stderr)
        else:
            print(f"downloading {meta.get('title')!r} ({meta.get('duration')}s) -> {path}", file=sys.stderr)
            y.download([url])
    if audio:
        mp3 = path.with_suffix(".mp3")
        if not mp3.exists():
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-vn",
                            "-c:a", "libmp3lame", "-q:a", "2", str(mp3)], check=True)
    return path


def is_url(s):
    return str(s).lower().startswith(("http://", "https://"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--out-dir", default=str(DEFAULT_DIR))
    ap.add_argument("--max-height", type=int, default=1080)
    ap.add_argument("--audio", action="store_true")
    ap.add_argument("--info", action="store_true")
    a = ap.parse_args()
    if a.info:
        print(info(a.url))
        return
    print(fetch(a.url, a.out_dir, a.max_height, a.audio))


if __name__ == "__main__":
    main()
