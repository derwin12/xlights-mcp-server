"""Source separation using Demucs (optional dependency)."""

from __future__ import annotations

import logging
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class StemPaths(BaseModel):
    """Paths to separated audio stems."""

    vocals: str = ""
    drums: str = ""
    bass: str = ""
    other: str = ""
    available: bool = False


def separate_stems(
    audio_path: Path,
    output_dir: Path | None = None,
    model: str = "htdemucs",
    timeout_s: float = 180.0,
) -> StemPaths:
    """Separate audio into stems using Demucs.

    Requires the 'separation' optional dependency:
        pip install xlights-mcp-server[separation]

    Demucs separation is CPU-bound and can take minutes per song with no
    progress feedback, so it's bounded by `timeout_s` — if it doesn't finish
    in time this returns `StemPaths(available=False)` instead of hanging
    the caller indefinitely. The underlying worker thread is not killed (no
    cross-platform way to cancel CPU-bound work in-process); it keeps
    running and populates the on-disk cache for next time, but this call
    returns either way.

    Args:
        audio_path: Path to audio file
        output_dir: Where to save stems (defaults to audio_cache)
        model: Demucs model name
        timeout_s: Max seconds to wait for separation before giving up
    """
    try:
        import torch
        import demucs.separate
    except ImportError:
        logger.warning(
            "Demucs not installed. Install with: pip install xlights-mcp-server[separation]"
        )
        return StemPaths(available=False)

    if output_dir is None:
        output_dir = audio_path.parent / "stems" / audio_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check cache — vocals is the minimum required stem
    stems = StemPaths(available=True)
    expected = {
        "vocals": output_dir / "vocals.wav",
        "drums": output_dir / "drums.wav",
        "bass": output_dir / "bass.wav",
        "other": output_dir / "other.wav",
    }

    vocals_cached = expected["vocals"].exists()
    if vocals_cached:
        logger.info("Using cached stems")
        stems.vocals = str(expected["vocals"])
        for name in ("drums", "bass", "other"):
            if expected[name].exists():
                setattr(stems, name, str(expected[name]))
        return stems

    logger.info(f"Separating stems with {model}: {audio_path}")

    def do_separation() -> StemPaths:
        result_stems = StemPaths(available=True)

        # Fix SSL cert issues on macOS
        import os
        try:
            import certifi
            os.environ.setdefault("SSL_CERT_FILE", certifi.where())
            os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
        except ImportError:
            pass

        # Run the model directly via demucs' low-level API (pretrained.get_model +
        # apply.apply_model), saving with soundfile. This sidesteps two broken
        # paths: the installed demucs==4.0.1 has no demucs.api module at all
        # (ModuleNotFoundError, not ImportError, in this release), and the CLI
        # (`python -m demucs.separate`) saves via torchaudio.save, which on
        # this torch/torchaudio pairing requires the optional `torchcodec`
        # package (itself broken without a matching FFmpeg shared-lib build).
        # librosa/soundfile have no such dependency.
        import numpy as np
        import soundfile as sf
        import torch
        from demucs.apply import apply_model
        from demucs.pretrained import get_model

        dmodel = get_model(model)
        dmodel.eval()

        wav, native_sr = sf.read(str(audio_path), dtype="float32", always_2d=True)
        wav = wav.T  # (channels, frames)
        if wav.shape[0] == 1:
            wav = np.repeat(wav, 2, axis=0)
        elif wav.shape[0] > 2:
            wav = wav[:2]

        if native_sr != dmodel.samplerate:
            import librosa
            wav = librosa.resample(wav, orig_sr=native_sr, target_sr=dmodel.samplerate)

        mix = torch.from_numpy(wav).float().unsqueeze(0)  # (1, channels, frames)
        with torch.no_grad():
            sources = apply_model(dmodel, mix, device="cpu", progress=False)[0]

        for stem_name, source in zip(dmodel.sources, sources):
            out_path = output_dir / f"{stem_name}.wav"
            sf.write(str(out_path), source.numpy().T, dmodel.samplerate)
            setattr(result_stems, stem_name, str(out_path))

        logger.info(f"Stems saved to {output_dir}")
        return result_stems

    import concurrent.futures

    # Not a context manager: ThreadPoolExecutor.__exit__ calls shutdown(wait=True),
    # which would block on the worker thread and defeat the timeout below.
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(do_separation)
    try:
        result = future.result(timeout=timeout_s)
        executor.shutdown(wait=False)
        return result
    except concurrent.futures.TimeoutError:
        executor.shutdown(wait=False)
        logger.warning(
            f"Stem separation exceeded {timeout_s:.0f}s timeout for "
            f"{audio_path.name} — continuing without stems. The "
            "separation may still finish in the background and "
            "populate the cache for next time."
        )
        return StemPaths(available=False)
    except Exception as e:
        executor.shutdown(wait=False)
        logger.error(f"Stem separation failed: {e}")
        return StemPaths(available=False)
