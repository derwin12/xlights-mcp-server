"""Transcribe a song to word-level timestamps for song_to_singing_props.py.

Usage:
    python scripts/transcribe_words.py song.mp3 words.json [--model small.en]
    python scripts/transcribe_words.py song.mp3 words.json --wav16k song16k.wav

Writes a list of phrases: {start, end, text, words: [{w, s, e, p}]} (seconds;
p is Whisper's word probability). Needs ffmpeg on PATH and
pip install faster-whisper librosa.

The audio is decoded with ffmpeg to 16 kHz mono and passed to Whisper as an
array, because faster-whisper's own decoder (PyAV) fails on some installs.
Pass --wav16k to keep the converted wav (song_to_singing_props.py reuses it
for pitch analysis); otherwise a temporary file is used and removed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


def to_wav16k(audio: Path, wav: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(audio), "-ac", "1", "-ar", "16000", str(wav)],
        check=True,
    )


def transcribe(wav: Path, model: str) -> list[dict]:
    import librosa
    from faster_whisper import WhisperModel

    y, _ = librosa.load(wav, sr=16000)
    m = WhisperModel(model, device="cpu", compute_type="int8")
    # condition_on_previous_text=False stops a bad phrase from derailing the rest
    segs, _ = m.transcribe(
        y, word_timestamps=True, vad_filter=False, condition_on_previous_text=False
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
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("out")
    ap.add_argument("--model", default="small.en")
    ap.add_argument("--wav16k", help="where to keep the 16 kHz mono wav (default: temp file)")
    args = ap.parse_args()

    if args.wav16k:
        wav = Path(args.wav16k)
        to_wav16k(Path(args.audio), wav)
        phrases = transcribe(wav, args.model)
    else:
        with tempfile.TemporaryDirectory() as td:
            wav = Path(td) / "song16k.wav"
            to_wav16k(Path(args.audio), wav)
            phrases = transcribe(wav, args.model)

    Path(args.out).write_text(json.dumps(phrases, indent=1), encoding="utf-8")
    print(len(phrases), "phrases", sum(len(p["words"]) for p in phrases), "words")


if __name__ == "__main__":
    main()
