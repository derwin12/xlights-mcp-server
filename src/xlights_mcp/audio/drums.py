"""Drum hits found in the audio (used by enhance_layout's --mh-hits and the skeleton band's drummer)."""

from __future__ import annotations

from pathlib import Path


def drum_accents(mp3: Path, min_gap_ms: int = 280) -> list[tuple[int, float]]:
    """Drum accents: onset peaks of the percussive part (low end weighted), each scaled by the loudest onset within
    +-1.5 s so quiet and loud passages both get accents; weak ones (< 0.45) dropped. [(ms, 0..1)]."""
    import librosa
    import numpy as np
    from scipy.signal import find_peaks
    y, sr = librosa.load(str(mp3), sr=22050, mono=True)
    yp = librosa.effects.percussive(y)
    hop = 256
    S = np.abs(librosa.stft(yp, n_fft=2048, hop_length=hop))
    f = librosa.fft_frequencies(sr=sr, n_fft=2048)
    lo = S[(f >= 30) & (f < 150)].sum(0)
    full = S.sum(0)
    on = lambda e: np.maximum(0, np.diff(e, prepend=e[0])) / max(float(e.max()), 1e-9)
    o = 2 * on(lo) + on(full)
    w = int(1.5 * sr / hop)
    local = np.array([o[max(0, k - w):k + w].max() for k in range(len(o))])
    pk, _ = find_peaks(o, distance=int(min_gap_ms / 1000 * sr / hop))
    t = librosa.frames_to_time(pk, sr=sr, hop_length=hop) * 1000
    out = [(int(tt), float(o[k] / local[k])) for tt, k in zip(t, pk) if local[k] > 0 and o[k] / local[k] >= 0.45
           and o[k] >= 0.08 * o.max()]
    return out
