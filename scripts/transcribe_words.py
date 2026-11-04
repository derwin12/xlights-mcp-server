"""Transcribe a song to word-level timestamps for song_to_singing_props.py.

Usage:
    python scripts/transcribe_words.py song.mp3 words.json [--model small.en]
    python scripts/transcribe_words.py song.mp3 words.json --wav16k song16k.wav [--separate [--container karaokeer]]

Writes a list of phrases: {start, end, text, words: [{w, s, e, p}]} (seconds;
p is Whisper's word probability). Needs ffmpeg on PATH and
pip install faster-whisper librosa.

The audio is decoded with ffmpeg to 16 kHz mono and passed to Whisper as an
array, because faster-whisper's own decoder (PyAV) fails on some installs.
Pass --wav16k to keep the converted wav (song_to_singing_props.py reuses it
for pitch analysis); otherwise a temporary file is used and removed.

--separate splits the vocals from the music with Spleeter (2 stems) in the karaokeer Docker container
(~30 s); --wav16k then holds the vocals, which also suits the pitch analysis. No single Whisper setting is
reliable on singing (This Christmas): the mix alone dropped sung passages as "no speech" and differed run to
run (271 / 179 words); vocals at temperature 0 were fullest but looped "ba-ba-ba" for 28 s over a whole
verse; vocals with temperature retries broke the loop but skipped the chant (a fixed ctranslate2 seed did
not make them repeatable). Silero VAD (tuned for speech) cut whole sung sections, so it is off. So three
passes - vocals at temperature 0, vocals with retries, the mix - are merged: the fullest pass without its
looped phrases is the base and its gaps are filled from the others. Phrases over a near-silent vocal track
are then dropped as Whisper inventions (QUIET_REL).
"""

import argparse
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

QUIET_REL = 0.05    # phrase dropped when the vocal track's median loudness under it is below this x its 90th pct
                    # (silence measures < 0.05; 0.15 dropped quiet spoken lines of Mean Grinch at 0.08-0.13)

_ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
         "seventeen eighteen nineteen").split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def number_words(n: int) -> list[str]:
    """Spoken words for 0..999999: 500 -> five hundred, 1985 -> nineteen eighty five (years are sung that way)."""
    if n < 20:
        return [_ONES[n]]
    if n < 100:
        return [_TENS[n // 10]] + ([_ONES[n % 10]] if n % 10 else [])
    if 1100 <= n <= 2099 and n % 100 and not 2000 <= n <= 2009:   # a year: nineteen eighty five, twenty twenty one
        return number_words(n // 100) + (["oh"] if n % 100 < 10 else []) + number_words(n % 100)
    if n < 1000:
        return [_ONES[n // 100], "hundred"] + (number_words(n % 100) if n % 100 else [])
    return number_words(n // 1000) + ["thousand"] + (number_words(n % 1000) if n % 1000 else [])


def spell_numbers(text: str) -> str:
    """Digits as sung words ('500 toys' -> 'five hundred toys', '80s' -> 'eighties'): the aligner and CMUdict
    have no digits, so a '500' got a 50 ms word with no mouth shapes (80s Hits Santa Style)."""
    def one(m):
        n = int(m.group(1).replace(",", ""))
        words = number_words(n) if n < 1_000_000 else list(m.group(1))
        if m.group(2):  # 80s / 1980's -> eighties
            last = words[-1]
            words[-1] = last[:-1] + "ies" if last.endswith("y") else last + "s"
        return " ".join(words)
    return re.sub(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+)('?s)?(?![\w.])", one, text)


def spell_word_numbers(phrases: list[dict]) -> list[dict]:
    """spell_numbers on every word; a number word becomes several words sharing its time. Whisper squeezes a
    number into a sliver (500 at 24.50-24.55 s, sung over 23.24-24.75), so it first takes the silent gap
    around it, up to 0.6 s per spoken word."""
    for p in phrases:
        out = []
        ws = p["words"]
        for i, w in enumerate(ws):
            spoken = spell_numbers(w["w"]).split()
            if len(spoken) == 1 and spoken[0] == w["w"]:
                out.append(w)
                continue
            lo = out[-1]["e"] if out else max(p["start"], w["s"] - 1.0)
            hi = ws[i + 1]["s"] if i + 1 < len(ws) else min(p["end"], w["e"] + 1.0)
            want = 0.6 * len(spoken)
            s, e = w["s"], w["e"]
            if e - s < want:  # grow into the gap, mostly backwards (the number is usually sung before Whisper's stamp)
                s = max(lo, e - want)
                e = min(hi, max(e, s + want))
            step = (e - s) / len(spoken)
            out += [{"w": t, "s": s + k * step, "e": s + (k + 1) * step, "p": w.get("p", 0.5)}
                    for k, t in enumerate(spoken)]
        p["words"] = out
        p["text"] = spell_numbers(p["text"])
    return phrases


def to_wav16k(audio: Path, wav: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(audio), "-ac", "1", "-ar", "16000", str(wav)],
        check=True,
    )


def separate_vocals(audio: Path, wav: Path, container: str) -> None:
    """Spleeter 2-stem vocals of audio, written to wav as 16 kHz mono."""
    env = {**os.environ, "MSYS_NO_PATHCONV": "1"}   # keep Git Bash from rewriting /container/paths
    tag = f"sep{int(time.time())}"
    subprocess.run(["docker", "start", container], check=True, capture_output=True, env=env)
    subprocess.run(["docker", "cp", str(audio), f"{container}:/tmp/{tag}{audio.suffix}"], check=True, env=env)
    subprocess.run(["docker", "exec", container, "spleeter", "separate", "-o", f"/tmp/{tag}_out",
                    "-p", "spleeter:2stems", "-c", "wav", f"/tmp/{tag}{audio.suffix}"],
                   check=True, capture_output=True, env=env)
    with tempfile.TemporaryDirectory() as td:
        vox = Path(td) / "vocals.wav"
        subprocess.run(["docker", "cp", f"{container}:/tmp/{tag}_out/{tag}/vocals.wav", str(vox)], check=True, env=env)
        to_wav16k(vox, wav)
    subprocess.run(["docker", "exec", container, "sh", "-c", f"rm -rf /tmp/{tag}*"], env=env)


def transcribe(wav: Path, model: str, vocals: bool = False, mix: Path | None = None) -> list[dict]:
    """Whisper phrases; with vocals, three passes merged (see merge_passes)."""
    import librosa
    from faster_whisper import WhisperModel

    y, _ = librosa.load(wav, sr=16000)
    m = WhisperModel(model, device="cpu", compute_type="int8")
    if not vocals:
        return whisper(m, y)
    passes = [whisper(m, y, temperature=0.0, no_speech_threshold=None),   # fullest, but can loop
              whisper(m, y, no_speech_threshold=None)]                    # retries break loops, skips some
    if mix:
        ym, _ = librosa.load(mix, sr=16000)
        passes.append(whisper(m, ym))                                     # the full mix, as before
    for i, p in enumerate(passes):
        print(f"pass {i + 1}: {len(p)} phrases {sum(len(x['words']) for x in p)} words")
    return drop_quiet(y, merge_passes(passes))


def whisper(m, y, **opts) -> list[dict]:
    # condition_on_previous_text=False stops a bad phrase from derailing the rest
    segs, _ = m.transcribe(
        y, word_timestamps=True, vad_filter=False, condition_on_previous_text=False, **opts
    )
    return [
        {
            "start": s.start,
            "end": s.end,
            "text": s.text,
            "words": [
                {"w": w.word.strip(), "s": w.start, "e": w.end, "p": w.probability}
                for w in (s.words or [])
            ],
        }
        for s in segs
        if s.words
    ]


def looped(p: dict) -> bool:
    """Whisper repetition loop: one token making up half of a long phrase (BA-BA-BA-BA... for 28 s)."""
    toks = [t for t in re.split(r"[\s\-,.!?]+", p["text"].lower()) if t]
    return len(toks) >= 12 and max(toks.count(t) for t in set(toks)) / len(toks) >= 0.5


def merge_passes(passes: list[list[dict]]) -> list[dict]:
    """The pass with the most words (loops removed) as the base; its gaps filled from the other passes."""
    clean = [[p for p in ps if not looped(p)] for ps in passes]
    order = sorted(range(len(clean)), key=lambda i: -sum(len(p["words"]) for p in clean[i]))
    merged = list(clean[order[0]])
    for i in order[1:]:
        for p in clean[i]:
            if all(p["end"] <= q["start"] + 0.2 or p["start"] >= q["end"] - 0.2 for q in merged):
                merged.append(p)
    merged.sort(key=lambda p: p["start"])
    print(f"merged: base pass {order[0] + 1}, {len(merged)} phrases {sum(len(p['words']) for p in merged)} words"
          f" ({sum(looped(p) for ps in passes for p in ps)} looped phrases removed)")
    return merged


def drop_quiet(y, phrases: list[dict]) -> list[dict]:
    import librosa
    import numpy as np

    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    t = librosa.times_like(rms, sr=16000, hop_length=512)
    ref = float(np.percentile(rms, 90)) or 1.0
    keep = []
    for p in phrases:
        sel = (t >= p["start"]) & (t <= p["end"])
        level = float(np.median(rms[sel])) / ref if sel.any() else 0.0
        if level >= QUIET_REL:
            keep.append(p)
        else:
            print(f"dropped (no vocals under it, {level:.2f}): {p['start']:.1f}s {p['text'].strip()[:60]}")
    return keep


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("out")
    ap.add_argument("--model", default="small.en")
    ap.add_argument("--wav16k", help="where to keep the 16 kHz mono wav (default: temp file)")
    ap.add_argument("--separate", action="store_true", help="transcribe Spleeter vocals (karaokeer container)")
    ap.add_argument("--container", default="karaokeer")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as td:
        wav = Path(args.wav16k) if args.wav16k else Path(td) / "song16k.wav"
        mix = Path(td) / "mix16k.wav"
        to_wav16k(Path(args.audio), mix)
        if args.separate:
            separate_vocals(Path(args.audio), wav, args.container)
            phrases = transcribe(wav, args.model, vocals=True, mix=mix)
        else:
            if wav != mix:
                to_wav16k(Path(args.audio), wav)
            phrases = transcribe(wav, args.model)

    phrases = spell_word_numbers(phrases)
    Path(args.out).write_text(json.dumps(phrases, indent=1), encoding="utf-8")
    print(len(phrases), "phrases", sum(len(p["words"]) for p in phrases), "words")


if __name__ == "__main__":
    main()
