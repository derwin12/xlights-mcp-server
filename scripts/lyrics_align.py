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

HERE = Path(__file__).resolve().parent

LRCLIB = "https://lrclib.net/api"
UA = {"User-Agent": "xlights-mcp-server song pipeline (https://github.com/derwin12)"}
MATCH_MIN = 0.5     # word-level similarity for a phrase to take fixes from an lrclib line
ANCHOR_MIN = 3      # ... and words it must share with that line
LOOSE_MIN, LOOSE_ANCHOR = 0.4, 4    # or a weaker match sharing more words: I WASN'T A MATCH | BUT BACK ON FORK
                                    # vs ... FOR THAT KIND OF SPARK is 0.47 with 4 words in common
SPAN_MAX = 5        # longest differing stretch (either side) that is replaced
SONG_MIN = 0.35     # whole-song similarity below which lrclib is ignored
DRIFT_S = 1.5       # aligned phrase may start/end this far outside Whisper's window
CHUNK_S = 600.0     # longest stretch aligned in one run; memory is fixed by the per-song lexicon now
                    # (nus_small_align.sh), so only very long songs are split - whole songs align as validated
SMALL_ALIGN = "/NUSAutoLyrixAlign/xl_small_align.sh"
CHUNK_PAD_S = 2.0   # audio kept either side of a chunk's phrases
SNAP_S = 0.12      # a word start moves to a voice onset at most this far away
ORDER_TIE = 0.15   # a line this close to the best match, at or after the song position reached, wins
SUNG_REL = 0.2     # vocal-stem loudness (x its 90th percentile) that counts as singing for fill_gaps
GAP_SUNG_S = 1.5    # seconds of singing a gap needs before lrclib lines are put into it
PACE = (0.35, 1.2)  # seconds per word an inserted line must fit: singing runs ~0.3-0.6 (HANG ALL THE MISTLETOE
                    # 0.85); 0.15-0.25 let 11 words into the held last note of Choosin Texas
LINE_S = 7.0       # phrases longer than this are split at their widest pause (about one sung line)


def tokens(text: str) -> list[str]:
    """Upper-case words as the aligner sees them (apostrophes kept, everything else a space)."""
    text = re.sub(r"\[.*?\]|\(.*?\)", " ", text)
    text = text.replace("&", " and ").replace("’", "'").replace("‘", "'")
    text = re.sub(r"[^A-Za-z0-9' ]+", " ", text)
    return [w.strip("'").upper() for w in text.split() if w.strip("'")]


def split_long(phrases: list[dict]) -> list[dict]:
    """Cut phrases longer than LINE_S at the widest pauses between words, into lyric-line-sized pieces.

    Whisper on separated vocals returns runs of several lines as one phrase (up to 26 s); one line per
    phrase keeps the lrclib/Genius line matching, the drift check and the Faces phrase layer meaningful.
    """
    out = []
    for p in phrases:
        ws = p["words"]
        cut = max(range(3, len(ws) - 2), key=lambda i: ws[i]["s"] - ws[i - 1]["e"], default=0)  # >=3 words a side
        # held notes make short lines long, so only long, wordy phrases are cut (Whisper's word times
        # often touch, so the widest pause may be 0 s - it is still the best place)
        if p["end"] - p["start"] <= LINE_S or len(ws) < 8 or not cut:
            out.append(p)
            continue
        out += split_long([{"start": part[0]["s"], "end": part[-1]["e"],
                            "text": " ".join(w["w"] for w in part), "words": part} for part in (ws[:cut], ws[cut:])])
    return out


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
    """Return (record, score) for the lrclib entry closest to what Whisper heard ((None, 0) if lrclib is down)."""
    try:
        if lrclib_id:
            cands = [lrclib_get(f"get/{lrclib_id}")]
        else:
            params = {"track_name": track}
            if artist:
                params["artist_name"] = artist
            cands = [c for c in lrclib_get("search", params) if c.get("plainLyrics")]
    except requests.RequestException as e:
        print(f"lrclib unavailable ({e}); re-run with --redo fix later for word fixes")
        return None, 0.0
    best, score = None, 0.0
    for c in cands:
        s = ratio(heard, tokens(c["plainLyrics"]))
        if s > score:
            best, score = c, s
    return best, score


def correct(phrases: list[dict], lines: list[list[str]]) -> tuple[list[list[str]], list[str], list]:
    """New word list per phrase, a report of the changes and, per phrase, the (first, after-last) lrclib
    line indices it matched (None when it matched no line).

    In a phrase that matches an lrclib line (MATCH_MIN, and at least ANCHOR_MIN words in common), each
    short stretch Whisper heard differently is replaced by lrclib's words (HIM REAL -> AMARILLO,
    OUT OF THE MORNING -> AS A WARNIN). Letters are no guide to mishearings, the matching rest of the
    phrase is. Stretches only one side has (a cover's extra or missing words, ad-libs) are never
    added or dropped, so a cover's own lines stay as sung.
    """
    windows = [((i, i + n), sum(lines[i:i + n], [])) for n in (1, 2, 3) for i in range(len(lines) - n + 1)]
    out, report, where = [], [], []
    pos = 0     # lyric position reached: a repeated chorus line maps to its next occurrence, not the first
    for p in phrases:
        heard = tokens(" ".join(w["w"] for w in p["words"]))
        # the words are fixed from the best line; the song position from the next near-equal line at or
        # after where we are (the last chorus's "THERE'S NOTHIN I CAN DO NO" over the first chorus's line)
        _, best = max(windows, key=lambda w: ratio(heard, w[1]), default=(None, []))
        tied = [w for w in windows if ratio(heard, w[1]) >= ratio(heard, best) - ORDER_TIE]
        span = min(tied, key=lambda w: (w[0][0] < pos - 1, w[0][0], w[0][1]), default=(None, []))[0]
        new = list(heard)
        sm = difflib.SequenceMatcher(a=heard, b=best, autojunk=False)
        same = sum(n for _, _, n in sm.get_matching_blocks())
        r = ratio(heard, best)
        matched = heard and ((r >= MATCH_MIN and same >= ANCHOR_MIN) or (r >= LOOSE_MIN and same >= LOOSE_ANCHOR))
        where.append(span if matched else None)
        if matched:
            pos = span[1]
            new = []
            for tag, a1, a2, b1, b2 in sm.get_opcodes():
                # a mishearing keeps roughly the word count: WE'LL -> HOW MUCH FUN IT'S GONNA would add unsung words
                if tag == "replace" and max(a2 - a1, b2 - b1) <= SPAN_MAX and abs((a2 - a1) - (b2 - b1)) <= 2:
                    new += best[b1:b2]
                else:
                    new += heard[a1:a2]
        out.append(new)
        if new != heard:
            report.append(f"{p['start']:6.1f}s  {' '.join(heard)}\n         -> {' '.join(new)}")
    return out, report, where


def sung_spans(vocals: Path):
    """(times, active) per frame of the vocal stem: active = loud enough to be singing."""
    import librosa
    import numpy as np

    y, _ = librosa.load(vocals, sr=16000)
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    t = librosa.times_like(rms, sr=16000, hop_length=512)
    return t, rms / (float(np.percentile(rms, 90)) or 1.0) >= SUNG_REL


def fill_gaps(phrases, fixed, where, lines, vocals: Path, duration: float):
    """Insert lrclib lines Whisper missed (the opening "HANG ALL THE MISTLETOE" of This Christmas).

    A gap between heard phrases gets the lyric lines that come between its neighbours' matched lines
    (before the first one at the song start, after the last one at the end) when the vocal stem shows
    singing there for GAP_SUNG_S and the words fit it at a singing pace. At most 2 lines per gap; the
    aligner then times them. Returns new (phrases, fixed) and a report.
    """
    t, active = sung_spans(vocals)
    out_p, out_f, report = [], [], []
    for k in range(len(phrases) + 1):
        lo = phrases[k - 1]["end"] + 0.2 if k else 0.0
        hi = phrases[k]["start"] - 0.2 if k < len(phrases) else duration
        prev = where[k - 1] if k else None
        nxt = where[k] if k < len(phrases) else None
        if nxt is not None and (prev is not None or k == 0):
            cands = lines[prev[1] if prev else max(0, nxt[0] - 2):nxt[0]][-2:]    # lines just before the next one
        elif prev is not None and k == len(phrases):
            cands = lines[prev[1]:prev[1] + 2]                                   # song end
        else:
            cands = []
        sel = (t >= lo) & (t <= hi) & active
        if cands and hi > lo and sel.sum() * (t[1] - t[0]) >= GAP_SUNG_S:
            s0, s1 = float(t[sel][0]), float(t[sel][-1])
            while cands:
                words = [w for ln in cands for w in ln]
                if PACE[0] <= (s1 - s0) / len(words) <= PACE[1]:
                    step = (s1 - s0) / len(words)
                    out_p.append({"start": s0, "end": s1, "text": " ".join(words),
                                  "words": [{"w": w, "s": s0 + i * step, "e": s0 + (i + 1) * step, "p": 0.3}
                                            for i, w in enumerate(words)]})
                    out_f.append(words)
                    report.append(f"{s0:6.1f}s  + {' '.join(words)}")
                    break
                cands = cands[1:]       # too many words for the gap: keep the line nearest the next phrase
        if k < len(phrases):
            out_p.append(phrases[k])
            out_f.append(fixed[k])
    return out_p, out_f, report


def snap_onsets(phrases: list[dict], vocals: Path) -> int:
    """Move each word start to the nearest voice onset in the vocal stem within SNAP_S (in place).

    The aligner works in 30 ms frames on the full mix and Whisper's times are looser still; the mouths
    look sharpest opening exactly when the voice does (SequenceStarter snaps its word edits the same way).
    """
    import librosa
    import numpy as np

    y, sr = librosa.load(vocals, sr=16000)
    onsets = librosa.onset.onset_detect(y=y, sr=sr, units="time", backtrack=True, hop_length=160)
    if not len(onsets):
        return 0
    moved, prev_end = 0, 0.0
    for p in phrases:
        for w in p["words"]:
            i = int(np.argmin(np.abs(onsets - w["s"])))
            o = float(onsets[i])
            if abs(o - w["s"]) <= SNAP_S and o >= prev_end and o < w["e"] - 0.05 and o != w["s"]:
                w["s"] = o
                moved += 1
            prev_end = w["e"]
        if p["words"]:
            p["start"] = p["words"][0]["s"]
    return moved


def align_chunked(audio: Path, phrases: list[dict], fixed: list[list[str]], container: str):
    """Align in chunks of up to CHUNK_S, cut in the gaps between phrases; one (s, e, WORD) or None per word.

    The aligner's memory grows with the length of what it aligns: whole 6-8 minute medleys ran the machine
    out of memory (Claude Code stopped the rollout twice in this step). A chunk that fails or returns the
    wrong word count gives None for its words, so only its phrases keep Whisper timing.
    """
    import librosa

    dur = librosa.get_duration(path=str(audio))
    groups, cur = [], []
    for i, p in enumerate(phrases):
        if cur and p["end"] - phrases[cur[0]]["start"] > CHUNK_S:
            groups.append(cur)
            cur = []
        cur.append(i)
    if cur:
        groups.append(cur)
    out: list = []
    for g, idx in enumerate(groups):
        # window: the phrases plus padding, never past the middle of the gap to the neighbouring chunk
        lo = phrases[idx[0]]["start"] - CHUNK_PAD_S
        hi = phrases[idx[-1]]["end"] + CHUNK_PAD_S
        if g:
            lo = max(lo, (phrases[groups[g - 1][-1]]["end"] + phrases[idx[0]]["start"]) / 2)
        if g + 1 < len(groups):
            hi = min(hi, (phrases[idx[-1]]["end"] + phrases[groups[g + 1][0]]["start"]) / 2)
        lo, hi = max(0.0, lo), min(dur, hi)
        words = [w for i in idx for w in fixed[i]]
        try:
            got = align(audio, words, container, lo, hi)
        except subprocess.CalledProcessError as e:
            print(f"  chunk {g + 1}/{len(groups)} ({lo:.0f}-{hi:.0f} s): aligner failed ({e.returncode})")
            got = []
        if len(got) != len(words):
            print(f"  chunk {g + 1}/{len(groups)} ({lo:.0f}-{hi:.0f} s): {len(got)} of {len(words)} words; "
                  "its phrases keep Whisper timing")
            got = [None] * len(words)
        out += got
    print(f"aligned in {len(groups)} chunk(s) of up to {CHUNK_S:.0f} s")
    return out


def align(audio: Path, words: list[str], container: str, start: float | None = None,
          end: float | None = None) -> list[tuple[float, float, str]]:
    """Run NUSAutoLyrixAlign in the container on audio[start:end]; [(start, end, WORD)] in song time."""
    env = {**os.environ, "MSYS_NO_PATHCONV": "1"}   # keep Git Bash from rewriting /container/paths
    tag = f"xl{time.time_ns()}"
    cut = (["-ss", f"{start:.3f}"] if start else []) + (["-to", f"{end:.3f}"] if end else [])
    with tempfile.TemporaryDirectory() as td:
        wav, txt = Path(td) / "song.wav", Path(td) / "lyrics.txt"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(audio), *cut, "-ac", "1", "-ar", "16000",
                        str(wav)], check=True)
        txt.write_text(" ".join(words), encoding="utf-8")
        subprocess.run(["docker", "start", container], check=True, capture_output=True, env=env)
        # per-song lexicon instead of the stock 4.2 GB L.fst: 2 GB instead of 14 GB of RAM, twice as fast, same times
        subprocess.run(["docker", "cp", str(HERE / "nus_small_align.sh"), f"{container}:{SMALL_ALIGN}"],
                       check=True, env=env)
        subprocess.run(["docker", "exec", container, "sh", "-c", f"sed -i 's/\\r$//' {SMALL_ALIGN} && chmod +x {SMALL_ALIGN}"],
                       check=True, env=env)
        for f in (wav, txt):
            subprocess.run(["docker", "cp", str(f), f"{container}:/tmp/{tag}_{f.name}"], check=True, env=env)
        subprocess.run(["docker", "exec", "-w", "/NUSAutoLyrixAlign", container, SMALL_ALIGN,
                        f"/tmp/{tag}_song.wav", f"/tmp/{tag}_lyrics.txt", f"/tmp/{tag}_aligned.txt"],
                       check=True, capture_output=True, env=env)
        res = subprocess.run(["docker", "exec", container, "cat", f"/tmp/{tag}_aligned.txt"],
                             check=True, capture_output=True, text=True, env=env).stdout
        subprocess.run(["docker", "exec", container, "sh", "-c", f"rm -f /tmp/{tag}_*"], env=env)
    rows = [ln.split() for ln in res.splitlines() if ln.strip()]
    off = start or 0.0
    return [(float(s) + off, float(e) + off, w) for s, e, w in rows]


def rebuild(phrases, fixed, aligned) -> tuple[list[dict], int]:
    """Phrases with aligned word times; returns (phrases, phrases that kept Whisper timing)."""
    out, fallback, k = [], 0, 0
    for p, words in zip(phrases, fixed):
        got = aligned[k:k + len(words)]
        k += len(words)
        ok = got and None not in got and got[0][0] >= p["start"] - DRIFT_S and got[-1][1] <= p["end"] + DRIFT_S
        if ok:
            # times only: a word missing from the aligner's dictionary comes back labelled BREATH* (BOOYAH,
            # GRINCHIFICATION, WHOVILLE), so the label is always our own word
            ws = [{"w": word.lower(), "s": s, "e": max(e, s + 0.05), "p": 1.0} for (s, e, _), word in zip(got, words)]
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
    ap.add_argument("--lyrics-file", help="lyrics text to use instead of lrclib (e.g. a parody's YouTube captions)")
    ap.add_argument("--vocals", help="vocal stem (transcribe_words.py --separate --wav16k): fill sung gaps from lrclib")
    args = ap.parse_args()

    phrases = split_long([p for p in json.load(open(args.words, encoding="utf-8")) if p["words"]])
    heard = [t for p in phrases for t in tokens(" ".join(w["w"] for w in p["words"]))]
    if args.lyrics_file:    # the uploader's own lyrics (YouTube captions of a parody) instead of lrclib
        text = Path(args.lyrics_file).read_text(encoding="utf-8")
        rec = {"id": "file", "artistName": "lyrics file", "trackName": Path(args.lyrics_file).name,
               "duration": 0, "plainLyrics": text}
        score = ratio(heard, tokens(text))
    else:
        rec, score = pick_lyrics(args.track, args.artist, heard, args.lrclib_id)
    if not rec or (score < SONG_MIN and not args.lyrics_file):
        print(f"lrclib: no close match (best {score:.2f}); words left as Whisper heard them")
        fixed = [tokens(" ".join(w["w"] for w in p["words"])) for p in phrases]
    else:
        print(f"lrclib: #{rec['id']} {rec['artistName']} - {rec['trackName']} ({rec['duration']:.0f} s), "
              f"similarity {score:.2f}")
        lines = [ln for ln in (tokens(x) for x in rec["plainLyrics"].splitlines()) if ln]
        fixed, report, where = correct(phrases, lines)
        print(f"{len(report)} of {len(phrases)} phrases corrected")
        for r in report:
            print("  " + r)
        if args.vocals:
            import librosa

            phrases, fixed, added = fill_gaps(phrases, fixed, where, lines, Path(args.vocals),
                                              librosa.get_duration(path=args.audio))
            print(f"{len(added)} missed lines filled from lrclib")
            for r in added:
                print("  " + r)

    if args.no_align:
        result, _ = rebuild(phrases, fixed, [])
    else:
        words = [w for ws in fixed for w in ws]
        aligned = align_chunked(Path(args.audio), phrases, fixed, args.container)
        result, fallback = rebuild(phrases, fixed, aligned)
        print(f"aligned {len(words)} words; {fallback} of {len(phrases)} phrases kept Whisper timing")
    if args.vocals:
        moved = snap_onsets(result, Path(args.vocals))
        print(f"{moved} word starts snapped to the voice onset")
    Path(args.out).write_text(json.dumps(result, indent=1), encoding="utf-8")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
