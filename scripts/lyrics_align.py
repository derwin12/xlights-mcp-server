"""Correct Whisper's words with lrclib.net lyrics and re-time them with NUSAutoLyrixAlign.

Usage:
    python scripts/lyrics_align.py song.mp3 words.json fixed.json --track "This Christmas" [--artist "Donny Hathaway"]
        [--lrclib-id 36958453] [--no-align] [--container karaokeer]

words.json comes from scripts/transcribe_words.py; fixed.json has the same shape (phrases with
{w, s, e, p} words) and goes to song_to_singing_props.py --words.

Why not just align lrclib's text: covers repeat verses and change ad-libs, and forced alignment
puts every given word somewhere, so text that is not what was sung drifts by whole verses.
Whisper decides what was sung and in what order; lrclib only fixes misheard words:
  1. lrclib candidates for the track (any artist unless --artist) are scored against the Whisper
     transcript and the closest wins (covers are listed under the original artist).
  2. Each Whisper phrase is compared with the best-matching run of 1-3 lrclib lines; where they agree
     closely enough, short stretches heard differently take lrclib's words. Nothing is added or dropped.
  3. The corrected text is aligned with NUSAutoLyrixAlign in the karaokeer container (about 80 s
     for a 4-minute song). A phrase whose aligned words fall well outside Whisper's phrase window
     keeps Whisper's timing for its words (spread evenly when the word count changed).
A report of the changes is printed; nothing is changed when lrclib has no close match.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

import requests

LRCLIB = "https://lrclib.net/api"
UA = {"User-Agent": "xlights-mcp-server song pipeline (https://github.com/derwin12)"}
MATCH_MIN = 0.5     # word-level similarity for a phrase to take fixes from an lrclib line
ANCHOR_MIN = 3      # ... and words it must share with that line
SPAN_MAX = 4        # longest differing stretch (either side) that is replaced
SONG_MIN = 0.35     # whole-song similarity below which lrclib is ignored
DRIFT_S = 1.5       # aligned phrase may start/end this far outside Whisper's window


def tokens(text: str) -> list[str]:
    """Upper-case words as the aligner sees them (apostrophes kept, everything else a space)."""
    text = re.sub(r"\[.*?\]|\(.*?\)", " ", text)
    text = text.replace("&", " and ").replace("’", "'").replace("‘", "'")
    text = re.sub(r"[^A-Za-z0-9' ]+", " ", text)
    return [w.strip("'").upper() for w in text.split() if w.strip("'")]


def ratio(a: list[str], b: list[str]) -> float:
    return difflib.SequenceMatcher(a=a, b=b, autojunk=False).ratio()


def lrclib_get(path: str, params: dict | None = None):
    for attempt in range(5):
        r = requests.get(f"{LRCLIB}/{path}", params=params, headers=UA, timeout=60)
        if r.status_code != 503:      # lrclib answers 503 "ServerOverloaded" at busy times
            r.raise_for_status()
            return r.json()
        time.sleep(3 * (attempt + 1))
    r.raise_for_status()


def pick_lyrics(track: str, artist: str | None, heard: list[str], lrclib_id: int | None):
    """Return (record, score) for the lrclib entry closest to what Whisper heard."""
    if lrclib_id:
        cands = [lrclib_get(f"get/{lrclib_id}")]
    else:
        params = {"track_name": track}
        if artist:
            params["artist_name"] = artist
        cands = [c for c in lrclib_get("search", params) if c.get("plainLyrics")]
    best, score = None, 0.0
    for c in cands:
        s = ratio(heard, tokens(c["plainLyrics"]))
        if s > score:
            best, score = c, s
    return best, score


def correct(phrases: list[dict], lines: list[list[str]]) -> tuple[list[list[str]], list[str]]:
    """New word list per phrase and a report of the changes.

    In a phrase that matches an lrclib line (MATCH_MIN, and at least ANCHOR_MIN words in common), each
    short stretch Whisper heard differently is replaced by lrclib's words (HIM REAL -> AMARILLO,
    OUT OF THE MORNING -> AS A WARNIN). Letters are no guide to mishearings, the matching rest of the
    phrase is. Stretches only one side has (a cover's extra or missing words, ad-libs) are never
    added or dropped, so a cover's own lines stay as sung.
    """
    windows = [sum(lines[i:i + n], []) for n in (1, 2, 3) for i in range(len(lines) - n + 1)]
    out, report = [], []
    for p in phrases:
        heard = tokens(" ".join(w["w"] for w in p["words"]))
        best = max(windows, key=lambda w: ratio(heard, w), default=[])
        new = list(heard)
        sm = difflib.SequenceMatcher(a=heard, b=best, autojunk=False)
        same = sum(n for _, _, n in sm.get_matching_blocks())
        if heard and ratio(heard, best) >= MATCH_MIN and same >= ANCHOR_MIN:
            new = []
            for tag, a1, a2, b1, b2 in sm.get_opcodes():
                if tag == "replace" and max(a2 - a1, b2 - b1) <= SPAN_MAX:
                    new += best[b1:b2]
                else:
                    new += heard[a1:a2]
        out.append(new)
        if new != heard:
            report.append(f"{p['start']:6.1f}s  {' '.join(heard)}\n         -> {' '.join(new)}")
    return out, report


def align(audio: Path, words: list[str], container: str) -> list[tuple[float, float, str]]:
    """Run NUSAutoLyrixAlign in the container; [(start, end, WORD)] in input order."""
    env = {**os.environ, "MSYS_NO_PATHCONV": "1"}   # keep Git Bash from rewriting /container/paths
    tag = f"xl{int(time.time())}"
    with tempfile.TemporaryDirectory() as td:
        wav, txt = Path(td) / "song.wav", Path(td) / "lyrics.txt"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(audio), "-ac", "1", "-ar", "16000",
                        str(wav)], check=True)
        txt.write_text(" ".join(words), encoding="utf-8")
        subprocess.run(["docker", "start", container], check=True, capture_output=True, env=env)
        for f in (wav, txt):
            subprocess.run(["docker", "cp", str(f), f"{container}:/tmp/{tag}_{f.name}"], check=True, env=env)
        subprocess.run(["docker", "exec", "-w", "/NUSAutoLyrixAlign", container, "./RunAlignment.sh",
                        f"/tmp/{tag}_song.wav", f"/tmp/{tag}_lyrics.txt", f"/tmp/{tag}_aligned.txt"],
                       check=True, capture_output=True, env=env)
        res = subprocess.run(["docker", "exec", container, "cat", f"/tmp/{tag}_aligned.txt"],
                             check=True, capture_output=True, text=True, env=env).stdout
        subprocess.run(["docker", "exec", container, "sh", "-c", f"rm -f /tmp/{tag}_*"], env=env)
    rows = [ln.split() for ln in res.splitlines() if ln.strip()]
    return [(float(s), float(e), w) for s, e, w in rows]


def rebuild(phrases, fixed, aligned) -> tuple[list[dict], int]:
    """Phrases with aligned word times; returns (phrases, phrases that kept Whisper timing)."""
    out, fallback, k = [], 0, 0
    for p, words in zip(phrases, fixed):
        got = aligned[k:k + len(words)]
        k += len(words)
        ok = got and got[0][0] >= p["start"] - DRIFT_S and got[-1][1] <= p["end"] + DRIFT_S
        if ok:
            ws = [{"w": w.lower(), "s": s, "e": max(e, s + 0.05), "p": 1.0} for s, e, w in got]
        else:
            fallback += 1
            if [w["w"].upper() for w in p["words"]] == words or len(words) == len(p["words"]):
                ws = [{**o, "w": w.lower()} for o, w in zip(p["words"], words)]
            else:   # word count changed: spread the new words over Whisper's phrase
                step = (p["end"] - p["start"]) / max(len(words), 1)
                ws = [{"w": w.lower(), "s": p["start"] + i * step, "e": p["start"] + (i + 1) * step, "p": 0.5}
                      for i, w in enumerate(words)]
        out.append({"start": ws[0]["s"] if ws else p["start"], "end": ws[-1]["e"] if ws else p["end"],
                    "text": " ".join(w["w"] for w in ws), "words": ws})
    return out, fallback


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("words", help="Whisper words.json from transcribe_words.py")
    ap.add_argument("out")
    ap.add_argument("--track", required=True, help="song title to look up on lrclib")
    ap.add_argument("--artist", help="restrict lrclib to this artist (default: any)")
    ap.add_argument("--lrclib-id", type=int, help="use this lrclib record")
    ap.add_argument("--no-align", action="store_true", help="fix words only, keep Whisper timing")
    ap.add_argument("--container", default="karaokeer")
    args = ap.parse_args()

    phrases = [p for p in json.load(open(args.words, encoding="utf-8")) if p["words"]]
    heard = [t for p in phrases for t in tokens(" ".join(w["w"] for w in p["words"]))]
    rec, score = pick_lyrics(args.track, args.artist, heard, args.lrclib_id)
    if not rec or score < SONG_MIN:
        print(f"lrclib: no close match (best {score:.2f}); words left as Whisper heard them")
        fixed = [tokens(" ".join(w["w"] for w in p["words"])) for p in phrases]
    else:
        print(f"lrclib: #{rec['id']} {rec['artistName']} - {rec['trackName']} ({rec['duration']:.0f} s), "
              f"similarity {score:.2f}")
        lines = [tokens(ln) for ln in rec["plainLyrics"].splitlines()]
        fixed, report = correct(phrases, [ln for ln in lines if ln])
        print(f"{len(report)} of {len(phrases)} phrases corrected")
        for r in report:
            print("  " + r)

    if args.no_align:
        result, _ = rebuild(phrases, fixed, [])
    else:
        words = [w for ws in fixed for w in ws]
        aligned = align(Path(args.audio), words, args.container)
        if len(aligned) != len(words):
            print(f"aligner returned {len(aligned)} of {len(words)} words; keeping Whisper timing")
            aligned = []
        result, fallback = rebuild(phrases, fixed, aligned)
        print(f"aligned {len(words)} words; {fallback} of {len(phrases)} phrases kept Whisper timing")
    Path(args.out).write_text(json.dumps(result, indent=1), encoding="utf-8")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
