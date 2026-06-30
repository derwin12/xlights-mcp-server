"""Thin client for xLights' live automation HTTP API (the same one xlDo uses).

Requires a running xLights instance with the xFade automation service enabled
(Preferences > xFade). Default instance "A" listens on port 49913; instance
"B" on 49914. Host/port can be overridden per-call or via the
XLIGHTS_AUTOMATION_HOST / XLIGHTS_AUTOMATION_PORT environment variables.

Command shapes are taken from xLights' own documentation
("documentation/xlDo Commands.txt" in the xLights source) and
src-ui-wx/automation/xLightsAutomations.cpp (ProcessxlDoAutomation).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 49913

_DEFAULT_TIMEOUT = 30.0
_RENDER_TIMEOUT = 1800.0  # renderAll/exportVideoPreview can take a long time


class AutomationError(RuntimeError):
    """Raised when xLights' automation API is unreachable or returns an error."""


def _host_port(host: str | None, port: int | None) -> tuple[str, int]:
    return (
        host or os.environ.get("XLIGHTS_AUTOMATION_HOST", DEFAULT_HOST),
        port or int(os.environ.get("XLIGHTS_AUTOMATION_PORT", DEFAULT_PORT)),
    )


def call(
    cmd: str,
    host: str | None = None,
    port: int | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
    **params,
) -> dict:
    """POST a command to xLights' /xlDoAutomation endpoint.

    Returns the parsed JSON response. Raises AutomationError if xLights isn't
    reachable, the response isn't JSON, or it reports a non-200 result.
    """
    h, p = _host_port(host, port)
    url = f"http://{h}:{p}/xlDoAutomation"
    body = json.dumps({"cmd": cmd, **params}).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    # xLights signals success/failure via the HTTP status code, not a "res"
    # field in the body — it returns plain {"version": "..."} etc. on 200
    # and a non-2xx status (with a {"msg": "..."} body) on failure.
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            status = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        status = e.code
    except urllib.error.URLError as e:
        raise AutomationError(
            f"Could not reach xLights automation API at {h}:{p} ({e}). "
            "Is xLights running with xFade enabled in Preferences?"
        ) from e

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise AutomationError(f"xLights returned a non-JSON response: {raw!r}") from e

    data.setdefault("res", status)
    if data["res"] != 200:
        raise AutomationError(f"xLights automation command '{cmd}' failed: {data}")
    return data


def get_version(*, host: str | None = None, port: int | None = None) -> dict:
    return call("getVersion", host=host, port=port)


def open_sequence(
    seq: str,
    *,
    force: bool = False,
    prompt_issues: bool = False,
    host: str | None = None,
    port: int | None = None,
) -> dict:
    # Opening a sequence loads audio and may trigger rendering — use the long
    # timeout so large sequences don't appear to fail when they just need more time.
    return call(
        "loadSequence",
        host=host,
        port=port,
        timeout=_RENDER_TIMEOUT,
        seq=seq.replace("\\", "/"),
        promptIssues="true" if prompt_issues else "false",
        force="true" if force else "false",
    )


def save_sequence(*, seq: str | None = None, host: str | None = None, port: int | None = None) -> dict:
    return call("saveSequence", host=host, port=port, seq=(seq or "").replace("\\", "/"))


def render_all(
    *, highdef: bool = False, host: str | None = None, port: int | None = None
) -> dict:
    return call(
        "renderAll", host=host, port=port, timeout=_RENDER_TIMEOUT,
        highdef="true" if highdef else "false",
    )


def export_video_preview(
    filename: str, *, host: str | None = None, port: int | None = None
) -> dict:
    # xLights' JSON request parser mishandles backslashes in Windows paths
    # (e.g. "\Users\" gets corrupted, likely by an extra escape pass on its
    # HTTP layer) — forward slashes work fine on Windows, so always use them.
    return call(
        "exportVideoPreview", host=host, port=port, timeout=_RENDER_TIMEOUT,
        filename=filename.replace("\\", "/"),
    )


def get_models(
    *, include_models: bool = True, include_groups: bool = True,
    host: str | None = None, port: int | None = None,
) -> dict:
    return call(
        "getModels", host=host, port=port,
        models="true" if include_models else "false",
        groups="true" if include_groups else "false",
    )


def get_effect_ids(model: str, *, host: str | None = None, port: int | None = None) -> dict:
    return call("getEffectIDs", host=host, port=port, model=model)


def get_effect_settings(
    model: str, layer: int, effect_id: int, *, host: str | None = None, port: int | None = None
) -> dict:
    return call(
        "getEffectSettings", host=host, port=port,
        model=model, layer=str(layer), id=str(effect_id),
    )


def set_effect_settings(
    model: str,
    layer: int,
    effect_id: int,
    *,
    name: str | None = None,
    settings: dict[str, str] | None = None,
    palette: dict[str, str] | None = None,
    start_time_ms: int | None = None,
    end_time_ms: int | None = None,
    host: str | None = None,
    port: int | None = None,
) -> dict:
    params: dict = {"model": model, "layer": str(layer), "id": str(effect_id)}
    if name is not None:
        params["name"] = name
    if settings is not None:
        params["settings"] = settings
    if palette is not None:
        params["palette"] = palette
    if start_time_ms is not None:
        params["startTime"] = str(start_time_ms)
    if end_time_ms is not None:
        params["endTime"] = str(end_time_ms)
    return call("setEffectSettings", host=host, port=port, **params)


def add_effect(
    target: str,
    effect: str,
    *,
    settings: str = "",
    palette: str = "",
    layer: int = 0,
    start_time_ms: int = 0,
    end_time_ms: int = 0,
    host: str | None = None,
    port: int | None = None,
) -> dict:
    """Add an effect via the live API. `settings`/`palette` use xLights'
    "KEY=value,KEY=value" string format (see xsq_editor._settings_str and
    ColorPalette.to_xlights_string), not JSON.

    xLights validates the model and effect layer exist; the response's
    "worked" field reflects whether the effect was actually added.
    """
    return call(
        "addEffect", host=host, port=port,
        target=target, effect=effect, settings=settings, palette=palette,
        layer=str(layer), startTime=str(start_time_ms), endTime=str(end_time_ms),
    )


def get_open_sequence(*, host: str | None = None, port: int | None = None) -> dict:
    """Return info about the currently-open sequence, or raise AutomationError if none is open."""
    return call("getOpenSequence", host=host, port=port)


def close_sequence(
    *,
    force: bool = False,
    quiet: bool = True,
    host: str | None = None,
    port: int | None = None,
) -> dict:
    """Close the currently-open sequence.

    Args:
        force: Discard unsaved changes without prompting. If False and the
            sequence has unsaved changes, raises AutomationError (504).
        quiet: Suppress the error when no sequence is open. Defaults to True.
    """
    return call(
        "closeSequence", host=host, port=port,
        force="true" if force else "false",
        quiet="true" if quiet else "false",
    )


def new_sequence(
    duration_secs: int,
    *,
    media_file: str = "",
    frame_ms: int = 50,
    host: str | None = None,
    port: int | None = None,
) -> dict:
    """Create a new blank sequence in the running xLights instance.

    Args:
        duration_secs: Sequence length in seconds.
        media_file: Optional audio file path. Empty for a silent sequence.
        frame_ms: Frame time in milliseconds (default 50ms = 20fps).
    """
    return call(
        "newSequence", host=host, port=port,
        durationSecs=str(duration_secs),
        mediaFile=media_file or "null",
        frameMS=str(frame_ms),
    )


def clone_model_effects(
    source: str,
    target: str,
    *,
    erase_target: bool = False,
    host: str | None = None,
    port: int | None = None,
) -> dict:
    """Copy all effects from *source* model onto *target* model.

    Args:
        source: Name of the model to copy effects from.
        target: Name of the model to copy effects onto.
        erase_target: If True, clear the target model's existing effects first.
    """
    return call(
        "cloneModelEffects", host=host, port=port,
        source=source, target=target,
        eraseModel="true" if erase_target else "false",
    )


def export_model_with_render(
    model: str,
    filename: str,
    *,
    format: str = "mp4highquality",
    highdef: bool = True,
    host: str | None = None,
    port: int | None = None,
) -> dict:
    """Render a single model and export it as a video/GIF/sequence file.

    Combines render + export in one call — no separate renderAll needed.

    Args:
        model: Model name (must exist in the open sequence).
        filename: Output file path. Extension should match ``format``.
        format: Export format. Common video options: ``mp4highquality``,
            ``mp4compressed``, ``mp4uncompressed``, ``gif``.
            Audio/other: ``eseq``, ``hls``, ``lsp``.
        highdef: Render at high definition. Defaults to True.
    """
    return call(
        "exportModelWithRender", host=host, port=port, timeout=_RENDER_TIMEOUT,
        model=model,
        filename=filename.replace("\\", "/"),
        format=format,
        highdef="true" if highdef else "false",
    )


def check_sequence(seq: str, *, host: str | None = None, port: int | None = None) -> dict:
    return call("checkSequence", host=host, port=port, seq=seq.replace("\\", "/"))


def get_sequence_info(filename: str, *, host: str | None = None, port: int | None = None) -> dict:
    return call("getSequenceInfo", host=host, port=port, filename=filename.replace("\\", "/"))


def render_frame(
    *,
    sequence_name: str,
    time_ms: int,
    output_path: Path,
    host: str | None = None,
    port: int | None = None,
) -> dict:
    """Render a sequence and extract a single PNG frame at time_ms.

    xLights has no native single-frame export — only a full-sequence video
    export (exportVideoPreview). This opens the sequence, renders it,
    exports it to a temporary video, then uses ffmpeg to pull out one frame.
    """
    if shutil.which("ffmpeg") is None:
        raise AutomationError(
            "ffmpeg not found on PATH. Install ffmpeg to use render_frame."
        )

    open_sequence(sequence_name, host=host, port=port)
    render_all(host=host, port=port)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        video_path = Path(tmp) / "preview.mp4"
        export_video_preview(str(video_path), host=host, port=port)

        seconds = time_ms / 1000.0
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(video_path),
                "-ss", f"{seconds:.3f}", "-frames:v", "1",
                str(output_path),
            ],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise AutomationError(f"ffmpeg failed to extract frame: {result.stderr}")

    return {"success": True, "output_path": str(output_path), "time_ms": time_ms}


def render_clip(
    *,
    sequence_name: str,
    start_ms: int,
    end_ms: int,
    output_path: Path,
    host: str | None = None,
    port: int | None = None,
) -> dict:
    """Render a sequence and export a video clip covering start_ms..end_ms.

    Like render_frame, this exports the full sequence video then trims it with
    ffmpeg — xLights has no native time-range export.
    """
    if shutil.which("ffmpeg") is None:
        raise AutomationError(
            "ffmpeg not found on PATH. Install ffmpeg to use render_clip."
        )
    if end_ms <= start_ms:
        raise AutomationError(f"end_ms ({end_ms}) must be greater than start_ms ({start_ms})")

    open_sequence(sequence_name, host=host, port=port)
    render_all(host=host, port=port)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        video_path = Path(tmp) / "preview.mp4"
        export_video_preview(str(video_path), host=host, port=port)

        start_s = start_ms / 1000.0
        duration_s = (end_ms - start_ms) / 1000.0
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-ss", f"{start_s:.3f}",
                "-i", str(video_path),
                "-t", f"{duration_s:.3f}",
                "-c", "copy",
                str(output_path),
            ],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise AutomationError(f"ffmpeg failed to trim clip: {result.stderr}")

    return {
        "success": True,
        "output_path": str(output_path),
        "start_ms": start_ms,
        "end_ms": end_ms,
        "duration_ms": end_ms - start_ms,
    }
