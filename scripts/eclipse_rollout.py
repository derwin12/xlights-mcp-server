r"""Re-run every Eclipse6 song in F:\ShowFolderAI through song_to_package.py (the 2026-10-25 rollout).

    python scripts/eclipse_rollout.py [--only Hamildolph ...] [--redo words] [--log-dir DIR]

Each song's mp3 is already in the show folder; its official Eclipse 6 video (matched by title and length,
within 1 s) supplies the lyrics from its manual captions. Covers of originals also get an lrclib title and a
Genius page for the Sections track. Songs run one after another (xLights exports one video at a time) and a
failure is logged and skipped. Back up first: F:\ShowFolderAI\Backup\pre-pipeline-20261025 holds the old files.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHOW = Path(r"F:\ShowFolderAI")
YT = "https://www.youtube.com/watch?v="

# file suffix -> (YouTube id, title for lrclib and the radio, Genius page or None)
SONGS = {
    "This-Christmas": ("", "This Christmas", "https://genius.com/Donny-hathaway-this-christmas-lyrics"),
    "Mean-Grinchs-Wicked-Story": ("eu0PrA10i1I", "Mean Grinch's Wicked Story", None),
    "2013-Hits-Santa-Style": ("6cqcb0wNoBM", "2013 Hits Santa Style", None),
    "2015-Hits-Santa-Style": ("zqZMfBVI49A", "2015 Hits Santa Style", None),
    "2016-Hits-Santa-Style": ("OLqDqEu5M6E", "2016 Hits Santa Style", None),
    "2019-Hits-Santa-Style": ("LXmH8hH_8tE", "2019 Hits Santa Style", None),
    "2021-Hits-Santa-Style": ("MSLmQ0fezy0", "2021 Hits Santa Style", None),
    "80s-Hits-Santa-Style": ("lz8yBut3TIA", "80s Hits Santa Style", None),
    "90s-Santa-Style": ("P9lZWus8V-4", "90s Hits Santa Style", None),
    "All-I-Want-For-Christmas": ("RXVaaOYGRdo", "All I Want for Christmas Is You",
                                 "https://genius.com/Mariah-carey-all-i-want-for-christmas-is-you-lyrics"),
    "Come-All-Ye-Faithful": ("ip3LtdM_Klg", "O Come All Ye Faithful", None),
    "Deck-the-Halls": ("E0CRM5bUS6c", "Deck the Halls", None),
    "Hamildolph": ("M7sm49fHlyI", "Hamildolph", None),
    "Ill-Be-Home-for-Christmas": ("BpsLN3jmk1E", "I'll Be Home for Christmas",
                                  "https://genius.com/Bing-crosby-ill-be-home-for-christmas-lyrics"),
    "O-Holy-Night": ("2stv6K9gVaU", "O Holy Night", None),
    "Santa-Style-Wonka-Edition": ("m8Gb4QvK5O8", "Santa Style Wonka Edition", None),
    "Shake-Up-Christmas": ("YT-pSxNYEds", "Shake Up Christmas", "https://genius.com/Train-shake-up-christmas-lyrics"),
    "The-Greatest-Snowman": ("HBJBITkAjC4", "The Greatest Snowman", None),
}
DONE_IN_PILOT = {"This-Christmas", "Mean-Grinchs-Wicked-Story"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="+", help="song suffixes to run (default: all but the two pilots)")
    ap.add_argument("--redo", default="words", help="song_to_package.py --redo step (default: words = everything)")
    ap.add_argument("--log-dir", default=str(SHOW / "SongWork" / "_rollout_logs"))
    a = ap.parse_args()
    logs = Path(a.log_dir)
    logs.mkdir(parents=True, exist_ok=True)
    todo = a.only or [s for s in SONGS if s not in DONE_IN_PILOT]
    results = []
    for i, s in enumerate(todo, 1):
        yt, title, genius = SONGS[s]
        cmd = [sys.executable, str(HERE / "song_to_package.py"), str(SHOW / f"Eclipse6-{s}.mp3"), "--track", title,
               "--radio-artist", "Eclipse 6", "--with-media", "--redo", a.redo]
        if yt:
            cmd += ["--source-url", YT + yt]
        if genius:
            cmd += ["--genius-url", genius]
        t0 = time.time()
        print(f"[{i}/{len(todo)}] {s} ...", flush=True)
        with open(logs / f"{s}.log", "w", encoding="utf-8") as log:
            rc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT,
                                env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"}).returncode
        mins = (time.time() - t0) / 60
        results.append((s, rc, mins))
        print(f"    {'ok' if rc == 0 else f'FAILED ({rc})'} in {mins:.1f} min - log {logs / (s + '.log')}", flush=True)
    print("\nsummary:")
    for s, rc, mins in results:
        print(f"  {s:28} {'ok' if rc == 0 else 'FAILED'}  {mins:5.1f} min")


if __name__ == "__main__":
    main()
