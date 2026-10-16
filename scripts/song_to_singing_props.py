"""Turn a song (YouTube URL or audio file) into an .xsq with singing props.

Usage:
    python scripts/song_to_singing_props.py --audio song.mp3 --words words.json \
        --show F:/ShowFolderAI --out "Song.xsq" [--cues cues.json] [--layout-effects]

    words.json comes from scripts/transcribe_words.py (faster-whisper, word timestamps):
    a list of {start, end, text, words: [{w, s, e, p}]} phrases.
    Needs: pip install faster-whisper cmudict librosa

Pipeline: word timestamps -> CMUdict phonemes -> xLights phoneme codes ->
one 3-layer lyric timing track (phrase / word / phoneme) per singing prop ->
a Faces effect per prop reading its own track.

Voice assignment (draft heuristic): each phrase's median pitch (pyin) splits
phrases into low / high. Low phrases go to the male tree, high phrases to the
female tree; both bulbs sing every phrase. Override per phrase with --cues, a
JSON list of [start_seconds, "male"|"female"|"all"] entries; a cue applies from
its start time until the next cue.

--layout-effects also sequences the rest of the layout from the beat map: a
Single Strand chase on the "House Outline" group (one per bar, direction
alternating, palette changing every 8 bars) and a VU Meter on the "Trees" group
(Spectrogram / Volume Bars alternating every 16 bars, one meter per tree).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from xlights_mcp.xlights.palettes import ColorPalette
from xlights_mcp.xlights.show import load_show_config
from xlights_mcp.xlights.xsq_writer import (
    EffectPlacement,
    SequenceSpec,
    TimingTrack,
    TimingTrackLabel,
    write_xsq,
)

OUTLINE_GROUP = "House Outline"
TREES_GROUP = "Trees"
BAR_PALETTES = [
    ["#FF0000", "#00FF00"],
    ["#FFFFFF", "#0000FF"],
    ["#FFB800", "#FF0000"],
    ["#00FF00", "#FFFFFF"],
]

# (model name, face definition, which phrases it sings)
PROPS = [
    ("Singing Tree Male", "Male Face", "male"),
    ("Singing Tree Female", "Female Face", "female"),
    ("Singing bulb Red (Left)", "Boscoyo ChromaBulb Face", "all"),
    ("Singing bulb Green (Right)", "Hanging Bulbs", "all"),
]

ARPA_TO_XL = {
    "AA": "AI", "AE": "AI", "AH": "AI", "AY": "AI",
    "EH": "E", "ER": "E", "IH": "E", "IY": "E", "EY": "E",
    "AO": "O", "OW": "O", "OY": "O", "AW": "O",
    "UH": "U", "UW": "U",
    "W": "WQ",
    "M": "MBP", "B": "MBP", "P": "MBP",
    "F": "FV", "V": "FV",
    "L": "L", "TH": "L", "DH": "L",
}
VOWELS = {"AA", "AE", "AH", "AY", "EH", "ER", "IH", "IY", "EY", "AO", "OW", "OY", "AW", "UH", "UW"}

_cmu = None


def word_phonemes(word: str) -> list[tuple[str, int]]:
    """Return [(xlights_code, weight)] for a word; vowels weigh more than consonants."""
    global _cmu
    if _cmu is None:
        import cmudict
        _cmu = cmudict.dict()
    w = re.sub(r"[^a-z']", "", word.lower())
    if not w:
        return [("etc", 1)]
    prons = _cmu.get(w)
    if not prons:
        return [("etc", 1)]
    out: list[tuple[str, int]] = []
    for ph in prons[0]:
        base = re.sub(r"\d", "", ph)
        code = ARPA_TO_XL.get(base, "etc")
        weight = 3 if base in VOWELS else 1
        if out and out[-1][0] == code:
            out[-1] = (code, out[-1][1] + weight)
        else:
            out.append((code, weight))
    return out


def phrase_pitches(wav: Path, phrases: list[dict]) -> list[float]:
    import librosa
    import numpy as np

    y, sr = librosa.load(wav, sr=16000)
    f0, voiced, _ = librosa.pyin(y, fmin=70, fmax=800, sr=sr, frame_length=1024)
    times = librosa.times_like(f0, sr=sr, hop_length=256)
    meds = []
    for p in phrases:
        sel = (times >= p["start"]) & (times <= p["end"]) & voiced & ~np.isnan(f0)
        meds.append(float(np.median(f0[sel])) if sel.any() else 0.0)
    return meds


def assign(phrases: list[dict], pitches: list[float], cues: list | None) -> list[str]:
    valid = sorted(p for p in pitches if p > 0)
    split = valid[len(valid) // 2] if valid else 0
    out = []
    for p, f0 in zip(phrases, pitches):
        voice = "male" if f0 and f0 < split else "female"
        if cues:
            for t, v in cues:
                if p["start"] >= t:
                    voice = v
        out.append(voice)
    return out


def build_tracks(phrases: list[dict], voices: list[str], who: str) -> TimingTrack:
    ph_l, wd_l, pn_l = [], [], []
    prev_end = 0
    for p, voice in zip(phrases, voices):
        if who != "all" and voice not in (who, "all"):
            continue
        ps, pe = int(p["start"] * 1000), int(p["end"] * 1000)
        ph_l.append(TimingTrackLabel(label=p["text"].strip(), start_time_ms=ps, end_time_ms=pe))
        for w in p["words"]:
            ws, we = int(w["s"] * 1000), int(w["e"] * 1000)
            if we <= ws:
                continue
            ws = max(ws, prev_end)
            if we <= ws:
                continue
            wd_l.append(TimingTrackLabel(label=w["w"], start_time_ms=ws, end_time_ms=we))
            phs = word_phonemes(w["w"])
            total = sum(wt for _, wt in phs)
            t = ws
            for i, (code, wt) in enumerate(phs):
                end = we if i == len(phs) - 1 else t + max(25, (we - ws) * wt // total)
                end = min(end, we)
                if end > t:
                    pn_l.append(TimingTrackLabel(label=code, start_time_ms=t, end_time_ms=end))
                t = end
            prev_end = we
    return TimingTrack(name="", labels=[ph_l, wd_l, pn_l])


def layout_effects(beats, duration_ms: int, groups: set[str]) -> list[EffectPlacement]:
    """House Outline chase (per bar) and Trees VU meter (per 16 bars) from a BeatMap."""
    bars = [int(t * 1000) for t in beats.downbeat_times]
    if len(bars) < 2:
        return []
    bars.append(min(duration_ms, bars[-1] + (bars[-1] - bars[-2])))
    out: list[EffectPlacement] = []

    if OUTLINE_GROUP in groups:
        for i in range(len(bars) - 1):
            pal = BAR_PALETTES[(i // 8) % len(BAR_PALETTES)]
            out.append(EffectPlacement(
                model_name=OUTLINE_GROUP, effect_name="SingleStrand",
                start_time_ms=bars[i], end_time_ms=bars[i + 1],
                palette=ColorPalette(colors=pal, active_colors=[1, 2]),
                settings={
                    "B_CHOICE_BufferStyle": "Per Model Single Line",
                    "E_CHECKBOX_Chase_Group_All": "0",
                    "E_CHOICE_Chase_Type1": "Left-Right" if i % 2 == 0 else "Right-Left",
                    "E_CHOICE_Fade_Type": "From Head",
                    "E_CHOICE_SingleStrand_Colors": "Palette",
                    "E_NOTEBOOK_SSEFFECT_TYPE": "Chase",
                    "E_SLIDER_Color_Mix1": "40", "E_SLIDER_Number_Chases": "1",
                    "E_TEXTCTRL_Chase_Offset": "0.0", "E_TEXTCTRL_Chase_Rotations": "1.0",
                },
            ))

    if TREES_GROUP in groups:
        for blk, start in enumerate(range(0, len(bars) - 1, 16)):
            end = bars[min(start + 16, len(bars) - 1)]
            pal = BAR_PALETTES[blk % len(BAR_PALETTES)]
            out.append(EffectPlacement(
                model_name=TREES_GROUP, effect_name="VU Meter",
                start_time_ms=bars[start], end_time_ms=end,
                palette=ColorPalette(colors=pal, active_colors=[1, 2]),
                settings={
                    "B_CHOICE_BufferStyle": "Per Model Default",
                    "E_CHECKBOX_Regex": "0",
                    "E_CHOICE_VUMeter_Type": "Spectrogram" if blk % 2 == 0 else "Volume Bars",
                    "E_SLIDER_VUMeter_Bars": "8", "E_SLIDER_VUMeter_Gain": "0",
                    "E_SLIDER_VUMeter_Sensitivity": "70", "E_TEXTCTRL_Filter": "",
                },
            ))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--wav16k", help="16 kHz mono wav for pitch analysis (default: --audio)")
    ap.add_argument("--words", required=True)
    ap.add_argument("--show", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--cues")
    ap.add_argument("--layout-effects", action="store_true",
                    help="also add a House Outline chase and Trees VU meter from the beat map")
    args = ap.parse_args()

    phrases = [p for p in json.load(open(args.words, encoding="utf-8")) if p["words"]]
    cues = json.load(open(args.cues)) if args.cues else None
    pitches = phrase_pitches(Path(args.wav16k or args.audio), phrases)
    voices = assign(phrases, pitches, cues)
    print({v: voices.count(v) for v in set(voices)}, "phrases by voice")

    show = load_show_config(Path(args.show))
    present = {m.name for m in show.models}
    duration_ms = int(max(p["end"] for p in phrases) * 1000) + 2000

    spec = SequenceSpec(
        song_title=args.title, media_file=str(Path(args.audio).resolve()),
        duration_ms=duration_ms,
    )
    palette = ColorPalette(colors=["#FFFFFF"], active_colors=[1])
    for model, face, who in PROPS:
        if model not in present:
            print("skip (not in show):", model)
            continue
        track = build_tracks(phrases, voices, who)
        track.name = f"Lyrics - {model}"
        spec.timing_tracks.append(track)
        spec.effects.append(EffectPlacement(
            model_name=model, effect_name="Faces", start_time_ms=0, end_time_ms=duration_ms,
            palette=palette,
            settings={
                "E_CHECKBOX_Faces_Fade": "0", "E_CHECKBOX_Faces_Outline": "1",
                "E_CHECKBOX_Faces_SuppressShimmer": "0",
                "E_CHECKBOX_Faces_SuppressWhenNotSinging": "0",
                "E_CHECKBOX_Faces_TransparentBlack": "0",
                "E_CHOICE_Faces_EyeBlinkDuration": "Normal",
                "E_CHOICE_Faces_EyeBlinkFrequency": "Normal",
                "E_CHOICE_Faces_Eyes": "Auto",
                "E_CHOICE_Faces_FaceDefinition": face,
                "E_CHOICE_Faces_TimingTrack": track.name,
                "E_CHOICE_Faces_UseState": "",
                "T_CHECKBOX_LayerMorph": "0", "T_CHOICE_LayerMethod": "Normal",
                "T_SLIDER_EffectLayerMix": "0",
            },
        ))
    if args.layout_effects:
        from xlights_mcp.audio.beats import detect_beats

        beats = detect_beats(Path(args.wav16k or args.audio))
        group_names = {g.name for g in show.model_groups}
        extra = layout_effects(beats, duration_ms, group_names)
        spec.effects.extend(extra)
        print(f"layout effects: {len(extra)} ({beats.tempo:.0f} BPM, {len(beats.downbeat_times)} bars)")
        for g in (OUTLINE_GROUP, TREES_GROUP):
            if g not in group_names:
                print("skip (group not in show):", g)
    out = write_xsq(spec, show, Path(args.out))
    print("wrote", out)


if __name__ == "__main__":
    main()
