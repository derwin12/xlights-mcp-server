r"""YouTube song -> singing-faces sequence -> .xsqz package, in one go.

Usage:
    python scripts/song_to_package.py URL [--name "Artist - Title"] [--track T] [--artist A]
        [--show F:\ShowFolderAI] [--faces-only] [--with-media] [--cues cues.json] [--lrclib-id N] [--redo STEP]

Steps (each skipped when its output exists, so a re-run resumes; --redo words|fix|xsq|sections|preview|package from there on):
  audio    fetch_video.py            -> <show>\<name>.mp3   (and the video, cached by id)
  words    transcribe_words.py       -> <show>\SongWork\<name>\words.json  (Whisper)
  fix      lyrics_align.py           -> ...\fixed.json  (lrclib word fixes + NUSAutoLyrixAlign timing)
  xsq      song_to_singing_props.py  -> <show>\<name>.xsq  (lyric tracks + Faces on the 4 singing props)
           enhance_layout.py (house effects as for the Eclipse6 songs; --faces-only skips it)
  sections song_sections.py          -> "Sections" timing track (Verse 1 / Chorus 1 ...) from Genius, ...\genius.txt
           lyric_images.py           -> pictures of sung words (lyric_icons.json) on Mega Tree / Matrix / Matrix 2
                                        (--no-images or --faces-only skip it)
  preview  xLights automation        -> <show>\HousePreviewVideos\<name>.mp4  (xLights must be running on --port with
           the show folder open and the house preview selected; skipped otherwise; --no-preview)
  package  package_xsqz.py           -> <show>\packages\<name>.xsqz  (no audio unless --with-media)

--name defaults to "<artist> - <track>" from YouTube's music tags, else the cleaned video title.
URL can also be an mp3 already in the show folder, to redo an older song with this pipeline, e.g.
    song_to_package.py F:\ShowFolderAI\Eclipse6-This-Christmas.mp3 --track "This Christmas" --radio-artist "Eclipse 6"
        --genius-url https://genius.com/Donny-hathaway-this-christmas-lyrics
--track/--artist are what lrclib is searched for; for a cover give the original artist or leave it out.
Needs the karaokeer container (NUSAutoLyrixAlign) in Docker; without it use --redo with lyrics_align --no-align by hand.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fetch_video  # noqa: E402
import lyrics_align  # noqa: E402

STEPS = ["audio", "words", "fix", "xsq", "sections", "preview", "package"]
LYRIC_LINES = 12    # a YouTube description needs this many short lines in a row to count as lyrics
PREVIEW_SIZE = (1920, 1058)    # house preview at full size regardless of the pane (eclipse-song-pipeline)


def show_secs(xsq: Path) -> float:
    m = re.search(r"<sequenceDuration>([\d.]+)</sequenceDuration>", xsq.read_text(encoding="utf-8"))
    return float(m.group(1)) if m else 0.0


def video_secs(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:      # "moov atom not found": a stalled export left a truncated file
        return 0.0


def render_preview(xsq: Path, out: Path, port: int, duration: float) -> None:
    """Open the sequence in the running xLights, render it and export the house preview as an mp4.

    Needs xLights running with automation on `port`, the show folder open and the normal house preview
    selected (the API cannot pick the preview). Skipped, not failed, when xLights is unavailable or the
    open sequence has unsaved changes - it is never closed with force.
    """
    sys.path.insert(0, str(HERE.parent / "src"))
    from xlights_mcp.xlights import automation_client as xl

    try:
        xl.get_version(port=port)
        xl.close_sequence(port=port)
    except xl.AutomationError as e:
        print(f"preview: skipped ({e}). Render later with --redo preview.")
        return
    out.parent.mkdir(exist_ok=True)
    for attempt in (1, 2):      # a long export can stall and leave a truncated mp4; one retry fixes it
        print(f"preview: rendering {xsq.name} on port {port} (attempt {attempt}) ...", flush=True)
        try:
            xl.open_sequence(str(xsq), force=True, port=port)
            xl.render_all(port=port)
            xl.export_video_preview(str(out), width=PREVIEW_SIZE[0], height=PREVIEW_SIZE[1], port=port)
        except xl.AutomationError as e:
            print(f"preview: xLights error: {e}")
        got = video_secs(out) if out.exists() else 0.0
        if got >= duration - 1:
            print(f"preview: {out} ({got:.1f} s)")
            break
        print(f"preview: video is {got:.1f} s of {duration:.1f} s")
    try:
        xl.close_sequence(port=port)
    except xl.AutomationError:
        pass


def clean_title(title: str) -> str:
    title = re.sub(r"\s*[\(\[][^\)\]]*[\)\]]", "", title)          # (Official Video), [Lyrics] ...
    title = re.sub(r"\s*\|.*$", "", title)
    return re.sub(r"\s+", " ", title).strip(" -")


def guess(meta: dict) -> tuple[str, str | None]:
    """(track, artist) from YouTube's music tags or an 'Artist - Title' video title."""
    if meta.get("track"):
        return meta["track"], meta.get("artist")
    channel = (meta.get("channel") or "").removesuffix(" - Topic").strip()
    title = clean_title(meta.get("title") or "")
    if channel:     # remix channels add "by <channel>" ("Choosin Texas" (EDM REMIX) by Country Night)
        title = re.sub(rf"(?i)\s+by\s+{re.escape(channel)}\s*$", "", title)
    title = re.sub(r"[\"“”]", "", title)
    parts = [p.strip() for p in title.split(" - ")]
    parts = [p for p in parts if p and not re.match(r"(?i)(official|lyric|animation|video|audio|hd\b|4k\b)", p)]
    if channel and any(p.lower() == channel.lower() for p in parts):    # "Title - Artist" or "Artist - Title"
        rest = [p for p in parts if p.lower() != channel.lower()]
        return (rest[0] if rest else parts[0]), channel
    if len(parts) >= 2:     # "Artist - Title" is usual but not universal: let lrclib say which is the track
        for track, artist in ((parts[1], parts[0]), (parts[0], parts[1])):
            try:
                hits = lyrics_align.lrclib_get("search", {"track_name": track, "artist_name": artist})
            except Exception:
                hits = []
            if hits:
                return track, artist
        return parts[1], parts[0]
    return (parts[0] if parts else "untitled"), None


def description_lyrics(desc: str) -> str | None:
    """Lyrics pasted in a YouTube description (parody channels like Eclipse 6 often do), else None.

    The longest run of short lines (blank lines allowed between verses) with no links or hashtags,
    when it has at least LYRIC_LINES lines.
    """
    blocks, cur = [], []
    for line in desc.splitlines() + ["http"]:
        s = line.strip()
        if s and (len(s) > 80 or re.search(r"https?://|www\.|#\w|@\w|\b(subscribe|follow|instagram|tiktok|"
                                             r"spotify|itunes|patreon|merch|lyrics by|written by)\b", s, re.I)):
            blocks.append(cur)
            cur = []
        elif s or cur:
            cur.append(s)
    best = max(blocks, key=lambda b: sum(1 for s in b if s), default=[])
    return "\n".join(best).strip() if sum(1 for s in best if s) >= LYRIC_LINES else None


def safe(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]+', "", name).strip()


def run(*cmd: str) -> None:
    print("\n>", " ".join(f'"{c}"' if " " in c else c for c in cmd), flush=True)
    env = {**os.environ, "PYTHONPATH": str(HERE.parent / "src")}
    subprocess.run([sys.executable, *cmd], check=True, env=env)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("url", help="YouTube link, or an mp3 on disk (then pass --track and --name)")
    ap.add_argument("--radio-artist", help="artist in the radio's NOW PLAYING text when it differs from --artist "
                                           '(Eclipse6 songs: "Eclipse 6", while lrclib searches the original)')
    ap.add_argument("--name", help='sequence name (default "<artist> - <track>")')
    ap.add_argument("--track", help="song title for lrclib (default from YouTube)")
    ap.add_argument("--artist", help="artist for lrclib (default from YouTube; for a cover the original artist)")
    ap.add_argument("--show", default=r"F:\ShowFolderAI")
    ap.add_argument("--faces-only", action="store_true", help="skip the Eclipse6 house layout effects")
    ap.add_argument("--with-media", action="store_true", help="put the mp3 in the package")
    ap.add_argument("--cues", help="voice cues for song_to_singing_props.py")
    ap.add_argument("--lrclib-id", type=int)
    ap.add_argument("--genius-url", help="Genius lyrics page for the Sections track (default: guessed)")
    ap.add_argument("--source-url", help="the song's YouTube video when URL is an mp3 on disk: its captions or "
                                         "description supply the lyrics")
    ap.add_argument("--lyrics", help="lyrics text file used instead of lrclib (parodies); default: SongWork\\<name>\\"
                                     "lyrics.txt, written from the video's manual captions or description if they "
                                     "hold the lyrics")
    ap.add_argument("--redo", choices=STEPS[1:], help="re-run from this step on")
    ap.add_argument("--no-preview", action="store_true", help="skip the house preview video")
    ap.add_argument("--no-images", action="store_true", help="no lyric pictures on the Mega Tree / matrices")
    ap.add_argument("--port", type=int, default=int(os.environ.get("XLIGHTS_AUTOMATION_PORT", 49914)),
                    help="xLights automation port (49914 on this machine)")
    a = ap.parse_args()

    local = None if fetch_video.is_url(a.url) else Path(a.url)
    if local:       # an mp3 already on disk (e.g. re-doing an Eclipse6 song): name/track come from flags
        meta = {"title": local.stem, "duration": None, "channel": None}
        track, artist = a.track or local.stem, a.artist
    else:
        meta = fetch_video.info(a.url)
        track, artist = guess(meta)
        track, artist = a.track or track, a.artist or artist
    name = safe(a.name or (local.stem if local else f"{artist} - {track}" if artist else track))
    show = Path(a.show)
    work = show / "SongWork" / name
    work.mkdir(parents=True, exist_ok=True)
    mp3, words, fixed = show / f"{name}.mp3", work / "words.json", work / "fixed.json"
    wav, xsq = work / "song16k.wav", show / f"{name}.xsq"
    pkg, genius = show / "packages" / f"{name}.xsqz", work / "genius.txt"
    video = show / "HousePreviewVideos" / f"{name}.mp4"
    print(f"{meta['title']!r} ({meta['duration']} s) -> {name!r}; lrclib track={track!r} artist={artist!r}")

    redo = STEPS.index(a.redo) if a.redo else len(STEPS)
    todo = lambda step, out: STEPS.index(step) >= redo or not out.exists()  # noqa: E731

    if not mp3.exists():
        if local:
            shutil.copyfile(local, mp3)
        else:
            download = fetch_video.fetch(a.url, audio=True)
            shutil.copyfile(download.with_suffix(".mp3"), mp3)
    if todo("words", words):
        run(str(HERE / "transcribe_words.py"), str(mp3), str(words), "--wav16k", str(wav), "--separate")
    lyrics = Path(a.lyrics) if a.lyrics else work / "lyrics.txt"
    src = a.source_url or (None if local else a.url)
    if not a.lyrics and not lyrics.exists() and src:
        # the uploader's own words beat lrclib (which has nothing for parodies): manual captions, then description
        for where, text in (("captions", fetch_video.captions(src)),
                            ("description", description_lyrics(fetch_video.info(src).get("description") or ""))):
            if text and text.count("\n") + 1 >= LYRIC_LINES:
                lyrics.write_text(text, encoding="utf-8")
                print(f"lyrics: {text.count(chr(10)) + 1} lines from the YouTube {where} -> {lyrics}")
                break
    if todo("fix", fixed):
        cmd = [str(HERE / "lyrics_align.py"), str(mp3), str(words), str(fixed), "--track", track,
               "--vocals", str(wav)]    # the vocal stem from transcribe_words --separate: fills missed lines
        if lyrics.exists():
            cmd += ["--lyrics-file", str(lyrics)]
        if artist and a.artist:     # YouTube's artist may be the cover band; only restrict when asked
            cmd += ["--artist", artist]
        if a.lrclib_id:
            cmd += ["--lrclib-id", str(a.lrclib_id)]
        run(*cmd)
    built = False
    if todo("xsq", xsq):
        cmd = [str(HERE / "song_to_singing_props.py"), "--audio", str(mp3), "--wav16k", str(wav),
               "--words", str(fixed), "--show", str(show), "--out", str(xsq), "--title", track]
        if a.cues:
            cmd += ["--cues", a.cues]
        run(*cmd)
        if not a.faces_only:
            xsq.with_suffix(".xsq.bak").unlink(missing_ok=True)   # enhance_layout keeps the first .bak
            run(str(HERE / "enhance_layout.py"), str(xsq), "--artist",
                a.radio_artist or artist or meta.get("channel") or "")
        built = True
    if built or STEPS.index("sections") >= redo:
        cmd = [str(HERE / "song_sections.py"), str(xsq), str(fixed), "--artist", a.artist or artist or "",
               "--track", track, "--save", str(genius), "--genius-file", str(genius)]
        if a.genius_url:
            cmd += ["--genius-url", a.genius_url]
        try:
            run(*cmd)
        except subprocess.CalledProcessError:   # no Genius page: the sequence is still usable
            print("sections: skipped (Genius page not found; pass --genius-url)")
        if not a.faces_only and not a.no_images:
            run(str(HERE / "lyric_images.py"), str(xsq), str(fixed), "--show", str(show))
    if not a.no_preview and (todo("preview", video) or built):
        render_preview(xsq, video, a.port, show_secs(xsq))
    if todo("package", pkg):
        cmd = [str(HERE / "package_xsqz.py"), name, "--show", str(show)]
        if not a.with_media:
            cmd.append("--no-media")
        run(*cmd)
    print(f"\ndone: {xsq}\n      {pkg}")


if __name__ == "__main__":
    main()
