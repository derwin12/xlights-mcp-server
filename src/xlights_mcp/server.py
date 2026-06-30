"""MCP Server entry point for xLights Sequence Generator."""

from __future__ import annotations

import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from xlights_mcp.config import load_config, save_config, ServerConfig

logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP(
    "xLights Sequence Generator",
    instructions="Analyze music and generate xLights light show sequences. "
    "Use list_shows/switch_show to manage show folders, analyze_song to analyze music, "
    "and create_sequence to generate .xsq files.",
)

# Global config — loaded at startup
_config: ServerConfig | None = None


def get_config() -> ServerConfig:
    """Get the current server configuration."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def _resolve_show(config: ServerConfig, show_name: str | None) -> dict | Path:
    """Resolve which show folder to use.

    Returns a Path on success, or a dict with action_required on ambiguity.
    """
    if show_name:
        show_path = config.get_show_path(show_name)
        if not show_path or not show_path.exists():
            return {
                "error": f"Show '{show_name}' not found.",
                "available_shows": config.list_shows(),
                "action_required": "Ask the user which show folder to use.",
            }
        return show_path

    shows = config.list_shows()
    if not shows:
        return {
            "error": "No show folders configured.",
            "action_required": "Ask the user for their xLights show directory and call add_show_folder.",
        }

    if len(shows) == 1:
        return config.get_show_path(shows[0])

    # Multiple shows — ask the user to choose
    return {
        "status": "show_selection_required",
        "available_shows": shows,
        "active_show": config.active_show,
        "action_required": (
            "Multiple show folders are configured. Ask the user which show "
            "this sequence should go into. Then call this tool again with "
            "the show_name parameter set."
        ),
    }


# ---------------------------------------------------------------------------
# Show Management Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_shows() -> dict:
    """List all configured xLights show folders.

    Returns the available show folders (e.g., Christmas, Halloween) and
    indicates which one is currently active.
    """
    config = get_config()
    if not config.show_folders:
        if config.detected_folders:
            detected = {}
            for name, path_str in config.detected_folders.items():
                path = Path(path_str).expanduser()
                detected[name] = str(path)
            return {
                "status": "setup_required",
                "detected_folders": detected,
                "action_required": (
                    "xLights show folders were detected at the paths listed above. "
                    "Ask the user if they'd like to use these, or provide their own show directory path. "
                    "Call add_show_folder with the path they choose."
                ),
            }
        return {
            "error": "No xLights show folders found.",
            "action_required": (
                "Ask the user for the full path to their xLights show directory. "
                "This is the folder that contains their xlights_rgbeffects.xml file. "
                "Once they provide it, call add_show_folder with the path."
            ),
        }
    shows = {}
    for name, path_str in config.show_folders.items():
        path = Path(path_str).expanduser()
        shows[name] = {
            "path": str(path),
            "exists": path.exists(),
            "active": name == config.active_show,
        }
    return {"shows": shows, "active": config.active_show}


@mcp.tool()
def add_show_folder(path: str, name: str | None = None) -> dict:
    """Add an xLights show folder by path.

    Use this to confirm a detected show folder or provide a custom path.
    The folder must contain an xlights_rgbeffects.xml file.

    Args:
        path: Full filesystem path to the xLights show folder
        name: Optional display name for the show (derived from folder name if omitted)
    """
    config = get_config()
    show_path = Path(path).expanduser().resolve()

    if not show_path.exists():
        return {"error": f"Path does not exist: {show_path}"}

    if not show_path.is_dir():
        return {"error": f"Path is not a directory: {show_path}"}

    if not (show_path / "xlights_rgbeffects.xml").exists():
        return {
            "error": f"Not a valid xLights show folder (missing xlights_rgbeffects.xml): {show_path}",
            "hint": "The show folder should contain xlights_rgbeffects.xml, which xLights creates automatically.",
        }

    show_name = name or show_path.name.lower()
    config.show_folders[show_name] = str(show_path)
    if not config.active_show:
        config.active_show = show_name
    config.detected_folders = {}
    save_config(config)

    global _config
    _config = config

    return {
        "success": True,
        "show_name": show_name,
        "path": str(show_path),
        "active": config.active_show == show_name,
    }


@mcp.tool()
def switch_show(show_name: str) -> dict:
    """Switch the active xLights show folder.

    Args:
        show_name: Name of the show to activate (e.g., "christmas", "halloween")
    """
    config = get_config()
    if show_name not in config.show_folders:
        return {
            "error": f"Unknown show '{show_name}'. Available: {config.list_shows()}"
        }

    config.active_show = show_name
    save_config(config)
    return {"active_show": show_name, "path": str(config.active_show_path)}


@mcp.tool()
def list_models() -> dict:
    """List all light models in the active xLights show.

    Returns model names, types, controller assignments, and channel info.
    """
    from xlights_mcp.xlights.show import load_show_models

    config = get_config()
    show_path = config.active_show_path
    if not show_path or not show_path.exists():
        return {
            "error": "No active show folder configured.",
            "action_required": "Ask the user for the path to their xLights show directory and call add_show_folder.",
        }

    models = load_show_models(show_path)
    return {
        "show": config.active_show,
        "model_count": len(models),
        "models": [m.model_dump() for m in models],
    }


@mcp.tool()
def list_controllers() -> dict:
    """List all controllers configured in the active xLights show.

    Returns controller names, IPs, protocols, and channel counts.
    """
    from xlights_mcp.xlights.show import load_show_controllers

    config = get_config()
    show_path = config.active_show_path
    if not show_path or not show_path.exists():
        return {
            "error": "No active show folder configured.",
            "action_required": "Ask the user for the path to their xLights show directory and call add_show_folder.",
        }

    controllers = load_show_controllers(show_path)
    return {
        "show": config.active_show,
        "controller_count": len(controllers),
        "controllers": [c.model_dump() for c in controllers],
    }


@mcp.tool()
def list_sequences() -> dict:
    """List all sequences (.xsq files) in the active show folder."""
    config = get_config()
    show_path = config.active_show_path
    if not show_path or not show_path.exists():
        return {
            "error": "No active show folder configured.",
            "action_required": "Ask the user for the path to their xLights show directory and call add_show_folder.",
        }

    sequences = []
    for xsq in sorted(show_path.glob("*.xsq")):
        sequences.append({"name": xsq.stem, "path": str(xsq)})
    return {
        "show": config.active_show,
        "sequence_count": len(sequences),
        "sequences": sequences,
    }


@mcp.tool()
def inspect_sequence(sequence_name: str, model_name: str | None = None) -> dict:
    """Inspect an existing xLights sequence file.

    Shows the song info, duration, models used, and effect summary. By
    default each model only reports its effect count (compact); pass
    model_name to see the full effect-by-effect timeline for one model.

    Args:
        sequence_name: Name of the sequence (without .xsq extension)
        model_name: Optional model name to drill into its full effect timeline
    """
    from xlights_mcp.xlights.xsq_reader import read_xsq_summary

    config = get_config()
    show_path = config.active_show_path
    if not show_path:
        return {"error": "No active show configured"}

    xsq_path = show_path / f"{sequence_name}.xsq"
    if not xsq_path.exists():
        return {"error": f"Sequence not found: {xsq_path}"}

    return read_xsq_summary(xsq_path, model_name=model_name)


@mcp.tool()
def list_timing_tracks(sequence_name: str, track_name: str | None = None) -> dict:
    """List timing tracks (Beats, Sections, Lyrics, etc.) in a sequence.

    By default each track only reports its mark count (compact); pass
    track_name to see the full list of marks (label, start/end time) for
    one track.

    Args:
        sequence_name: Name of the sequence (without .xsq extension)
        track_name: Optional timing track name to drill into its marks
    """
    from xlights_mcp.xlights.xsq_reader import read_xsq_timing_tracks

    config = get_config()
    show_path = config.active_show_path
    if not show_path:
        return {"error": "No active show configured"}

    xsq_path = show_path / f"{sequence_name}.xsq"
    if not xsq_path.exists():
        return {"error": f"Sequence not found: {xsq_path}"}

    return {"timing_tracks": read_xsq_timing_tracks(xsq_path, track_name=track_name)}


@mcp.tool()
def list_effects() -> dict:
    """List all available xLights effects with descriptions.

    Returns effect names, descriptions, and which model types they work best on.
    """
    from xlights_mcp.xlights.effects import get_effect_library

    return {"effects": get_effect_library()}


# ---------------------------------------------------------------------------
# Sequence Editing Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def add_effect(
    sequence_name: str,
    model_name: str,
    effect_name: str,
    start_time_ms: int,
    end_time_ms: int,
    layer: int = 0,
    settings: dict[str, str] | None = None,
    colors: list[str] | None = None,
) -> dict:
    """Add an effect to a model in an existing xLights sequence.

    Writes the change directly into the .xsq file. A timestamped backup of
    the previous version is kept alongside it (e.g. "Song.xsq.bak.20260621120000").
    Returns the layer/index of the new effect, which update_effect and
    delete_effect use to address it later.

    Args:
        sequence_name: Name of the sequence (without .xsq extension)
        model_name: Model to place the effect on
        effect_name: xLights effect type (e.g. "Chase", "Twinkle", "Shockwave")
        start_time_ms: Effect start time in milliseconds
        end_time_ms: Effect end time in milliseconds
        layer: Effect layer index (0 = bottom layer)
        settings: Optional effect parameter dict (E_SLIDER_..., E_CHECKBOX_..., etc.)
        colors: Optional list of hex colors (e.g. ["#FF0000", "#00FF00"]) for a new palette
    """
    from xlights_mcp.xlights.xsq_editor import add_effect as _add_effect

    config = get_config()
    show_path = config.active_show_path
    if not show_path:
        return {"error": "No active show configured"}

    xsq_path = show_path / f"{sequence_name}.xsq"
    if not xsq_path.exists():
        return {"error": f"Sequence not found: {xsq_path}"}

    return _add_effect(
        xsq_path, model_name, effect_name, start_time_ms, end_time_ms,
        settings=settings, layer=layer, colors=colors,
    )


@mcp.tool()
def update_effect(
    sequence_name: str,
    model_name: str,
    layer: int,
    index: int,
    effect_name: str | None = None,
    start_time_ms: int | None = None,
    end_time_ms: int | None = None,
    settings: dict[str, str] | None = None,
    colors: list[str] | None = None,
) -> dict:
    """Update an existing effect in a sequence. Only fields you pass are changed.

    Address the effect with the (layer, index) returned by add_effect, or by
    inspecting the sequence with inspect_sequence(model_name=...), which reports
    each effect's layer and index.

    Args:
        sequence_name: Name of the sequence (without .xsq extension)
        model_name: Model the effect is on
        layer: Effect layer index
        index: Effect's position within that layer
        effect_name: New effect type, if changing it
        start_time_ms: New start time in milliseconds
        end_time_ms: New end time in milliseconds
        settings: New effect parameter dict (replaces existing settings)
        colors: New list of hex colors for the effect's palette
    """
    from xlights_mcp.xlights.xsq_editor import update_effect as _update_effect

    config = get_config()
    show_path = config.active_show_path
    if not show_path:
        return {"error": "No active show configured"}

    xsq_path = show_path / f"{sequence_name}.xsq"
    if not xsq_path.exists():
        return {"error": f"Sequence not found: {xsq_path}"}

    return _update_effect(
        xsq_path, model_name, layer, index,
        effect_name=effect_name, start_time_ms=start_time_ms, end_time_ms=end_time_ms,
        settings=settings, colors=colors,
    )


@mcp.tool()
def delete_effect(sequence_name: str, model_name: str, layer: int, index: int) -> dict:
    """Delete an effect from a sequence.

    Address the effect with the (layer, index) reported by inspect_sequence
    (model_name=...) or returned from add_effect.

    Args:
        sequence_name: Name of the sequence (without .xsq extension)
        model_name: Model the effect is on
        layer: Effect layer index
        index: Effect's position within that layer
    """
    from xlights_mcp.xlights.xsq_editor import delete_effect as _delete_effect

    config = get_config()
    show_path = config.active_show_path
    if not show_path:
        return {"error": "No active show configured"}

    xsq_path = show_path / f"{sequence_name}.xsq"
    if not xsq_path.exists():
        return {"error": f"Sequence not found: {xsq_path}"}

    return _delete_effect(xsq_path, model_name, layer, index)


# ---------------------------------------------------------------------------
# Live xLights Automation Tools (require a running xLights with xFade on)
# ---------------------------------------------------------------------------


@mcp.tool()
def xlights_status(host: str | None = None, port: int | None = None) -> dict:
    """Check whether a running xLights instance is reachable for live tools.

    render_frame and add_effect_live need xLights running with the xFade
    automation service enabled (Preferences > xFade).

    Args:
        host: Automation host. Defaults to 127.0.0.1 (or XLIGHTS_AUTOMATION_HOST).
        port: Automation port. Defaults to 49913 / instance A (or XLIGHTS_AUTOMATION_PORT).
    """
    from xlights_mcp.xlights.automation_client import get_version, AutomationError

    try:
        result = get_version(host=host, port=port)
        return {"reachable": True, "version": result.get("version")}
    except AutomationError as e:
        return {"reachable": False, "error": str(e)}


@mcp.tool()
def render_frame(
    sequence_name: str,
    time_ms: int,
    output_path: str | None = None,
    host: str | None = None,
    port: int | None = None,
) -> dict:
    """Render a single preview frame of a sequence using a running xLights instance.

    Requires xLights running with the xFade automation service enabled
    (Preferences > xFade) and ffmpeg on PATH. xLights has no native
    single-frame export, so this opens and renders the sequence, exports
    it as a full video via xLights' automation API, then extracts one
    frame with ffmpeg — it may take a while for long sequences.

    Args:
        sequence_name: Name of the sequence (without .xsq extension). Opened
            in xLights if it isn't already.
        time_ms: Timestamp within the sequence to capture, in milliseconds.
        output_path: Where to save the PNG frame. Defaults to a file next to
            the sequence named "<sequence_name>_frame_<time_ms>ms.png".
        host: Automation host. Defaults to 127.0.0.1 (or XLIGHTS_AUTOMATION_HOST).
        port: Automation port. Defaults to 49913 / instance A (or XLIGHTS_AUTOMATION_PORT).
    """
    from xlights_mcp.xlights.automation_client import render_frame as _render_frame, AutomationError

    config = get_config()
    show_path = config.active_show_path
    if not show_path:
        return {"error": "No active show configured"}

    xsq_path = show_path / f"{sequence_name}.xsq"
    if not xsq_path.exists():
        return {"error": f"Sequence not found: {xsq_path}"}

    dest = (
        Path(output_path).expanduser()
        if output_path
        else show_path / f"{sequence_name}_frame_{time_ms}ms.png"
    )

    try:
        return _render_frame(
            sequence_name=xsq_path.name, time_ms=time_ms, output_path=dest,
            host=host, port=port,
        )
    except AutomationError as e:
        return {"error": str(e)}


@mcp.tool()
def add_effect_live(
    sequence_name: str,
    model_name: str,
    effect_name: str,
    start_time_ms: int,
    end_time_ms: int,
    layer: int = 0,
    settings: dict[str, str] | None = None,
    colors: list[str] | None = None,
    host: str | None = None,
    port: int | None = None,
) -> dict:
    """Add an effect via a running xLights instance, with real validation.

    Unlike add_effect (which writes the .xsq XML offline), this opens the
    sequence in a running xLights instance and adds the effect through its
    automation API — xLights itself validates the model and effect, and
    "worked": false in the response means it rejected the request. Requires
    xFade automation enabled (Preferences > xFade). The sequence is not
    saved automatically; call save_sequence or save from xLights' UI.

    Args:
        sequence_name: Name of the sequence (without .xsq extension). Opened
            in xLights if it isn't already.
        model_name: Model to place the effect on
        effect_name: xLights effect type (e.g. "Chase", "Twinkle", "Shockwave")
        start_time_ms: Effect start time in milliseconds
        end_time_ms: Effect end time in milliseconds
        layer: Effect layer index (0 = bottom layer)
        settings: Optional effect parameter dict (E_SLIDER_..., E_CHECKBOX_..., etc.)
        colors: Optional list of hex colors (e.g. ["#FF0000", "#00FF00"]) for a new palette
        host: Automation host. Defaults to 127.0.0.1 (or XLIGHTS_AUTOMATION_HOST).
        port: Automation port. Defaults to 49913 / instance A (or XLIGHTS_AUTOMATION_PORT).
    """
    from xlights_mcp.xlights import automation_client
    from xlights_mcp.xlights.xsq_editor import _settings_str
    from xlights_mcp.xlights.palettes import ColorPalette
    from xlights_mcp.xlights.automation_client import AutomationError

    config = get_config()
    show_path = config.active_show_path
    if not show_path:
        return {"error": "No active show configured"}

    xsq_path = show_path / f"{sequence_name}.xsq"
    if not xsq_path.exists():
        return {"error": f"Sequence not found: {xsq_path}"}

    settings_str = _settings_str(settings or {})
    palette_str = ""
    if colors:
        palette_str = ColorPalette(
            colors=colors, active_colors=list(range(1, len(colors) + 1))
        ).to_xlights_string()

    try:
        automation_client.open_sequence(xsq_path.name, host=host, port=port)
        return automation_client.add_effect(
            model_name, effect_name,
            settings=settings_str, palette=palette_str, layer=layer,
            start_time_ms=start_time_ms, end_time_ms=end_time_ms,
            host=host, port=port,
        )
    except AutomationError as e:
        return {"error": str(e)}


@mcp.tool()
def save_sequence_live(
    sequence_name: str, host: str | None = None, port: int | None = None
) -> dict:
    """Save the currently-open sequence in a running xLights instance.

    Use this after add_effect_live (or other manual edits made in xLights'
    UI) to persist changes to the .xsq file — add_effect_live deliberately
    leaves changes unsaved so multiple edits can be batched before saving.

    Args:
        sequence_name: Name of the sequence (without .xsq extension). Must
            already be open in xLights (e.g. via add_effect_live or render_frame).
        host: Automation host. Defaults to 127.0.0.1 (or XLIGHTS_AUTOMATION_HOST).
        port: Automation port. Defaults to 49913 / instance A (or XLIGHTS_AUTOMATION_PORT).
    """
    from xlights_mcp.xlights import automation_client
    from xlights_mcp.xlights.automation_client import AutomationError

    config = get_config()
    show_path = config.active_show_path
    if not show_path:
        return {"error": "No active show configured"}

    xsq_path = show_path / f"{sequence_name}.xsq"
    if not xsq_path.exists():
        return {"error": f"Sequence not found: {xsq_path}"}

    try:
        return automation_client.save_sequence(seq=xsq_path.name, host=host, port=port)
    except AutomationError as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Audio Analysis Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def analyze_song(
    mp3_path: str, detail: str = "summary", include_stems: bool = False
) -> dict:
    """Analyze a music file for light show sequencing.

    Performs full audio analysis: beat detection, song structure,
    frequency spectrum, energy profile, and optionally source separation.

    Args:
        mp3_path: Path to the .mp3 file to analyze
        detail: "summary" (counts and key stats, default) or "full" (every
            per-frame beat/energy/onset value — large, only request this if
            you specifically need raw timeseries data)
        include_stems: Also run Demucs source separation (drums/bass/vocals/
            other) for per-stem onset/energy data. Off by default — it's
            CPU-bound and can take several minutes per song the first time
            a given file is analyzed (subsequent calls hit the on-disk cache).
    """
    from xlights_mcp.audio.analyzer import full_analysis

    path = Path(mp3_path).expanduser()
    if not path.exists():
        return {"error": f"File not found: {path}"}

    if detail not in ("summary", "full"):
        return {"error": f"Invalid detail '{detail}'. Use: summary, full"}

    config = get_config()
    analysis = full_analysis(path, config.audio, include_stems=include_stems)
    return analysis.model_dump() if detail == "full" else analysis.summary()


@mcp.tool()
def get_song_structure(mp3_path: str) -> dict:
    """Get the verse/chorus/bridge structure of a song.

    Args:
        mp3_path: Path to the .mp3 file
    """
    from xlights_mcp.audio.structure import detect_structure

    path = Path(mp3_path).expanduser()
    if not path.exists():
        return {"error": f"File not found: {path}"}

    sections = detect_structure(path)
    return {"sections": [s.model_dump() for s in sections]}


@mcp.tool()
def get_beat_map(mp3_path: str) -> dict:
    """Get beat and downbeat timestamps for a song.

    Args:
        mp3_path: Path to the .mp3 file
    """
    from xlights_mcp.audio.beats import detect_beats

    path = Path(mp3_path).expanduser()
    if not path.exists():
        return {"error": f"File not found: {path}"}

    result = detect_beats(path)
    return result.model_dump()


@mcp.tool()
def get_energy_profile(mp3_path: str) -> dict:
    """Get energy and frequency band analysis for a song.

    Returns loudness curve and bass/mid/high energy over time.

    Args:
        mp3_path: Path to the .mp3 file
    """
    from xlights_mcp.audio.spectrum import analyze_spectrum

    path = Path(mp3_path).expanduser()
    if not path.exists():
        return {"error": f"File not found: {path}"}

    result = analyze_spectrum(path)
    return result.model_dump()


# ---------------------------------------------------------------------------
# Sequence Generation Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def create_sequence(
    mp3_path: str,
    mode: str = "auto",
    palette_hint: str | None = None,
    theme: str | None = None,
    vocal_assignments: dict[str, str] | None = None,
    show_name: str | None = None,
    include_stems: bool = True,
) -> dict:
    """Create an xLights sequence from a music file.

    Analyzes the audio and generates a .xsq file with effects placed on
    your light models according to the selected generation mode.

    Args:
        mp3_path: Path to the .mp3 file
        mode: Generation mode — "auto" (AI picks everything) or "guided"
              (interactive, previews the plan before writing the file).
              "template" is listed in xLights' UI but not implemented here yet.
        palette_hint: Optional color hint (e.g., "red and green", "orange and purple")
        theme: Optional theme hint (e.g., "christmas", "halloween", "energetic")
        vocal_assignments: Optional mapping of model names to vocal track names.
            Use {"all": "<track_name>"} to assign one track to all singing models,
            or map individual models like {"Snowman": "Vocals"}.
            If omitted and singing models are detected, returns available models and
            tracks so you can prompt the user for assignments.
        show_name: Which show folder to generate the sequence in (e.g., "christmas",
            "halloween"). If omitted and multiple shows exist, returns available
            shows so you can ask the user which one to use.
        include_stems: Run Demucs source separation (requires the
            'separation' optional dependency) so "auto" mode can vary effects
            by which instrument dominates each section, instead of always
            defaulting to "other". Bounded by a timeout so it can't hang;
            falls back to no stems if Demucs isn't installed or times out.
    """
    from xlights_mcp.sequencer.engine import generate_sequence

    path = Path(mp3_path).expanduser()
    if not path.exists():
        return {"error": f"File not found: {path}"}

    if mode not in ("auto", "guided", "template"):
        return {"error": f"Invalid mode '{mode}'. Use: auto, guided, template"}

    config = get_config()
    show_path = _resolve_show(config, show_name)
    if isinstance(show_path, dict):
        return show_path

    result = generate_sequence(
        mp3_path=path,
        show_path=show_path,
        mode=mode,
        palette_hint=palette_hint,
        theme=theme,
        audio_config=config.audio,
        vocal_assignments=vocal_assignments,
        include_stems=include_stems,
    )
    return result


@mcp.tool()
def preview_plan(mp3_path: str, mode: str = "auto", show_name: str | None = None) -> dict:
    """Preview the sequence generation plan without creating a file.

    Shows what effects would be placed on which models, based on the
    audio analysis and selected mode.

    Args:
        mp3_path: Path to the .mp3 file
        mode: Generation mode — "auto", "guided", or "template"
        show_name: Which show folder to preview against. If omitted and multiple
            shows exist, returns available shows so you can ask the user.
    """
    from xlights_mcp.sequencer.engine import preview_sequence_plan

    path = Path(mp3_path).expanduser()
    if not path.exists():
        return {"error": f"File not found: {path}"}

    config = get_config()
    show_path = _resolve_show(config, show_name)
    if isinstance(show_path, dict):
        return show_path

    return preview_sequence_plan(
        mp3_path=path,
        show_path=show_path,
        mode=mode,
        audio_config=config.audio,
    )


# ---------------------------------------------------------------------------
# Sequence Remapping Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def remap_sequence(
    import_path: str,
    overrides: dict[str, str] | None = None,
    pixel_threshold: float = 0.70,
    show_name: str | None = None,
) -> dict:
    """Import a sequence from a different show layout and remap it to your models.

    Accepts a .xsq file or .zip package from the xLights community. Automatically
    matches imported models to your show's models using name similarity, model type,
    and pixel count. Generates a new .xsq with effects remapped to your layout.

    Args:
        import_path: Path to the .xsq or .zip file to import.
        overrides: Optional dict mapping imported model names to your model names.
            These take precedence over automatic matching.
        pixel_threshold: Similarity threshold for pixel count matching (0.0-1.0).
            Default 0.70 means models must have at least 70% pixel count similarity.
        show_name: Which show folder to import into (e.g., "christmas", "halloween").
            If omitted and multiple shows exist, returns available shows so you can
            ask the user which one to use.

    Returns:
        Dict with mapping report, output path, and summary statistics.
    """
    from xlights_mcp.remapper.importer import import_package
    from xlights_mcp.remapper.matcher import (
        build_candidates_from_import,
        build_candidates_from_user_show,
        match_models,
    )
    from xlights_mcp.remapper.generator import generate_remapped_sequence
    from xlights_mcp.remapper.models import RemapResult
    from xlights_mcp.xlights.show import load_show_config

    import_file = Path(import_path).expanduser()

    # Validate import file
    if not import_file.exists():
        return RemapResult(
            success=False, error=f"File not found: {import_file}"
        ).model_dump()

    ext = import_file.suffix.lower()
    if ext not in (".xsq", ".zip"):
        return RemapResult(
            success=False,
            error=f"Unsupported file type: {ext}. Use .xsq or .zip.",
        ).model_dump()

    # Resolve show folder
    config = get_config()
    show_result = _resolve_show(config, show_name)
    if isinstance(show_result, dict):
        return show_result
    show_path = show_result

    try:
        show_config = load_show_config(show_path)
    except Exception as e:
        return RemapResult(
            success=False, error=f"Failed to load show config: {e}"
        ).model_dump()

    if not show_config.models and not show_config.model_groups:
        return RemapResult(
            success=False, error="No models found in user's active show."
        ).model_dump()

    # Import the sequence
    try:
        seq_data, lxml_root, imported_meta, extracted_assets = import_package(
            import_file, show_path
        )
    except Exception as e:
        return RemapResult(
            success=False, error=str(e)
        ).model_dump()

    if not seq_data.model_names:
        return RemapResult(
            success=False, error="Imported sequence contains no models with effects."
        ).model_dump()

    # Build candidates
    user_candidates = build_candidates_from_user_show(
        show_config.models, show_config.model_groups
    )
    imported_candidates = build_candidates_from_import(
        seq_data.model_names, imported_meta
    )

    # Run matching
    report = match_models(
        imported_candidates=imported_candidates,
        user_candidates=user_candidates,
        threshold=pixel_threshold,
        overrides=overrides or {},
        imported_source=str(import_file),
        has_imported_metadata=imported_meta is not None,
        timing_tracks_preserved=len(seq_data.timing_track_names),
        extracted_assets=extracted_assets,
    )

    # Generate remapped .xsq
    try:
        output_path, missing_assets, asset_warnings = generate_remapped_sequence(
            root=lxml_root,
            report=report,
            show_folder=show_path,
        )
    except Exception as e:
        return RemapResult(
            success=False, error=f"Failed to generate remapped sequence: {e}"
        ).model_dump()

    # Enrich report with post-generation info
    report.missing_assets = missing_assets
    report.warnings.extend(asset_warnings)

    return RemapResult(
        success=True,
        output_path=str(output_path),
        mapping_report=report,
    ).model_dump()


# ---------------------------------------------------------------------------
# FPP Integration Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def fpp_status() -> dict:
    """Check Falcon Pi Player connection status and current state.

    Returns FPP version, current playlist, scheduler state, etc.
    """
    from xlights_mcp.fpp.client import get_fpp_status

    config = get_config()
    return get_fpp_status(config.fpp)


@mcp.tool()
def fpp_upload_sequence(fseq_path: str, audio_path: str | None = None) -> dict:
    """Upload a sequence (.fseq) and optional audio to Falcon Pi Player.

    Args:
        fseq_path: Path to the .fseq file to upload
        audio_path: Optional path to the audio file (.mp3/.ogg)
    """
    from xlights_mcp.fpp.upload import upload_sequence

    config = get_config()
    return upload_sequence(config.fpp, Path(fseq_path), Path(audio_path) if audio_path else None)


@mcp.tool()
def fpp_list_playlists() -> dict:
    """List all playlists on the Falcon Pi Player."""
    from xlights_mcp.fpp.client import list_playlists

    config = get_config()
    return list_playlists(config.fpp)


@mcp.tool()
def fpp_start_playlist(playlist_name: str, repeat: bool = False) -> dict:
    """Start a playlist on the Falcon Pi Player.

    Args:
        playlist_name: Name of the playlist to start
        repeat: Whether to loop the playlist
    """
    from xlights_mcp.fpp.client import start_playlist

    config = get_config()
    return start_playlist(config.fpp, playlist_name, repeat)


@mcp.tool()
def fpp_stop() -> dict:
    """Stop current playback on the Falcon Pi Player."""
    from xlights_mcp.fpp.client import stop_playback

    config = get_config()
    return stop_playback(config.fpp)


# ---------------------------------------------------------------------------
# Screenshot / Manual Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def xlights_screenshot(
    output_path: str,
    bring_to_front: bool = True,
) -> dict:
    """Capture the full xLights application window and save it as a PNG.

    xLights must be running. The window is identified by process name
    (xLights.exe) so browser tabs or IDE windows with "xLights" in their
    title are never mistaken for the app.

    Args:
        output_path: Where to save the PNG (e.g. "screenshots/main_window.png").
        bring_to_front: Restore and focus the window before capturing (default True).

    Returns:
        saved_path, window title, and pixel dimensions.
    """
    from xlights_mcp.xlights.screenshot import capture_window, XLightsNotRunning

    try:
        saved = capture_window(output_path, bring_to_front=bring_to_front)
        return {
            "status": "ok",
            "saved_path": str(saved),
        }
    except XLightsNotRunning as e:
        return {"status": "error", "error": str(e)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
def xlights_screenshot_region(
    region: str,
    output_path: str,
    bring_to_front: bool = True,
) -> dict:
    """Capture a named region of the xLights window and save it as a PNG.

    Available region names: full, sequencer, toolbar, model_list,
    effects_panel, color_panel.

    Use xlights_list_regions to get the current list.

    Args:
        region: Named region (e.g. "effects_panel") or a JSON array
                "[left, top, right, bottom]" of absolute screen coordinates.
        output_path: Where to save the PNG.
        bring_to_front: Focus the window before capturing (default True).
    """
    import json as _json
    from xlights_mcp.xlights.screenshot import capture_region, XLightsNotRunning

    try:
        # Accept either a name or a JSON coordinate array
        parsed_region: str | tuple[int, int, int, int]
        try:
            coords = _json.loads(region)
            if isinstance(coords, list) and len(coords) == 4:
                parsed_region = tuple(int(c) for c in coords)  # type: ignore[assignment]
            else:
                parsed_region = region
        except (_json.JSONDecodeError, ValueError):
            parsed_region = region

        saved = capture_region(parsed_region, output_path, bring_to_front=bring_to_front)
        return {"status": "ok", "saved_path": str(saved), "region": region}
    except XLightsNotRunning as e:
        return {"status": "error", "error": str(e)}
    except ValueError as e:
        from xlights_mcp.xlights.screenshot import list_named_regions
        return {
            "status": "error",
            "error": str(e),
            "available_regions": list_named_regions(),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
def xlights_list_regions() -> dict:
    """List the named capture regions available for xlights_screenshot_region."""
    from xlights_mcp.xlights.screenshot import NAMED_REGIONS

    return {
        "regions": {
            name: {
                "description": f"left={lf:.0%} top={tf:.0%} right={rf:.0%} bottom={bf:.0%}"
            }
            for name, (lf, tf, rf, bf) in NAMED_REGIONS.items()
        }
    }


@mcp.tool()
def xlights_navigate_and_screenshot(
    scene: str,
    output_path: str,
    region: str = "full",
) -> dict:
    """Navigate xLights to a named UI state, then capture a screenshot.

    This combines dialog navigation (opening menus / dialogs) with window
    capture so you can screenshot specific parts of the UI for documentation.

    Use xlights_list_scenes to see available scene names.

    Args:
        scene: Scene name (e.g. "preferences", "controller_visualizer").
        output_path: Where to save the PNG.
        region: Named region to capture after navigation (default "full").
    """
    import time
    from xlights_mcp.xlights.screenshot import (
        find_xlights_window,
        capture_region,
        XLightsNotRunning,
    )
    from xlights_mcp.xlights.dialog_nav import SCENES
    from xlights_mcp.xlights.automation_client import call as automation_call, AutomationError

    try:
        win = find_xlights_window()
    except XLightsNotRunning as e:
        return {"status": "error", "error": str(e)}

    if scene not in SCENES:
        from xlights_mcp.xlights.dialog_nav import list_scenes
        return {
            "status": "error",
            "error": f"Unknown scene {scene!r}.",
            "available_scenes": list_scenes(),
        }

    # Execute the navigation steps
    steps = SCENES[scene]
    for step in steps:
        stype = step["type"]
        if stype == "automation":
            try:
                automation_call(step["cmd"], **{k: v for k, v in step.items() if k not in ("type", "cmd")})
            except AutomationError:
                pass  # best-effort; screenshot anyway
        elif stype == "menu":
            from xlights_mcp.xlights.dialog_nav import open_menu_path
            open_menu_path(step["path"])
        elif stype == "hotkey":
            from xlights_mcp.xlights.dialog_nav import press_hotkey
            press_hotkey(*step["keys"])
        elif stype == "click_fraction":
            from xlights_mcp.xlights.dialog_nav import click_at_fraction
            click_at_fraction(win.rect, step["x"], step["y"])
        elif stype == "wait":
            time.sleep(step.get("seconds", 0.3))

    try:
        saved = capture_region(region, output_path)
        return {"status": "ok", "saved_path": str(saved), "scene": scene, "region": region}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
def xlights_list_scenes() -> dict:
    """List the named navigation scenes available for xlights_navigate_and_screenshot."""
    from xlights_mcp.xlights.dialog_nav import SCENES

    return {"scenes": list(SCENES.keys())}


@mcp.tool()
def xlights_screenshot_floating_panel(
    panel_title: str,
    output_path: str,
) -> dict:
    """Capture a floating (undocked) xLights panel window by its title.

    Use this to screenshot panels the user has undocked from the main window,
    such as "Effect Settings", "Colors", "Layer Blending", "Layer Settings".

    Args:
        panel_title: Title prefix to match (e.g. "Effect Settings").
        output_path: Where to save the PNG.
    """
    from xlights_mcp.xlights.screenshot import capture_titled_window

    try:
        saved = capture_titled_window(panel_title, output_path)
        return {"status": "ok", "saved_path": str(saved)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
def xlights_annotate_screenshot(
    input_path: str,
    output_path: str,
    annotations: list[dict],
) -> dict:
    """Add callout annotations to a screenshot for use in documentation.

    Each annotation in *annotations* is a dict with:
    - ``type``: ``"arrow"`` | ``"box"`` | ``"label"``
    - ``x``, ``y``: position in pixels (top-left for box/label, tip for arrow)
    - ``text``: label text (required for label/arrow)
    - ``x2``, ``y2``: arrow tail position (required for arrow type)
    - ``width``, ``height``: box size in pixels (required for box type)
    - ``color``: hex color string, default ``"#FF0000"``

    Example annotations::

        [
          {"type": "label", "x": 120, "y": 45, "text": "Open Sequence button"},
          {"type": "arrow", "x": 200, "y": 80, "x2": 350, "y2": 120, "text": "Effects panel"},
          {"type": "box", "x": 10, "y": 200, "width": 180, "height": 300, "text": "Model list"}
        ]

    Args:
        input_path: Path to the source PNG screenshot.
        output_path: Where to save the annotated PNG.
        annotations: List of annotation dicts (see above).
    """
    from pathlib import Path as _Path
    from PIL import Image, ImageDraw, ImageFont

    try:
        img = Image.open(input_path).convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        try:
            font = ImageFont.truetype("arial.ttf", 14)
            font_small = ImageFont.truetype("arial.ttf", 12)
        except OSError:
            font = ImageFont.load_default()
            font_small = font

        for ann in annotations:
            color = ann.get("color", "#FF0000")
            rgb = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
            rgba = rgb + (220,)
            text_rgba = (255, 255, 255, 255)

            atype = ann.get("type", "label")
            x, y = int(ann.get("x", 0)), int(ann.get("y", 0))

            if atype == "box":
                w = int(ann.get("width", 100))
                h = int(ann.get("height", 50))
                draw.rectangle([x, y, x + w, y + h], outline=rgba, width=3)
                if ann.get("text"):
                    draw.rectangle([x, y - 18, x + w, y], fill=rgba)
                    draw.text((x + 3, y - 16), ann["text"], fill=text_rgba, font=font_small)

            elif atype == "arrow":
                x2, y2 = int(ann.get("x2", x + 50)), int(ann.get("y2", y + 50))
                draw.line([x, y, x2, y2], fill=rgba, width=3)
                # arrowhead
                import math
                angle = math.atan2(y - y2, x - x2)
                for da in (0.4, -0.4):
                    ax = x + 14 * math.cos(angle + da)
                    ay = y + 14 * math.sin(angle + da)
                    draw.line([x, y, ax, ay], fill=rgba, width=3)
                if ann.get("text"):
                    draw.rectangle([x2 + 2, y2 - 16, x2 + 2 + len(ann["text"]) * 8, y2 + 2], fill=rgba)
                    draw.text((x2 + 4, y2 - 14), ann["text"], fill=text_rgba, font=font_small)

            else:  # label
                text = ann.get("text", "")
                tw = len(text) * 8 + 8
                draw.rectangle([x, y, x + tw, y + 20], fill=rgba)
                draw.text((x + 4, y + 3), text, fill=text_rgba, font=font)

        combined = Image.alpha_composite(img, overlay).convert("RGB")
        out = _Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        combined.save(str(out), "PNG")
        return {"status": "ok", "saved_path": str(out), "annotation_count": len(annotations)}

    except Exception as e:
        return {"status": "error", "error": str(e)}


# ---------------------------------------------------------------------------
# Wiki Tools
# ---------------------------------------------------------------------------

_DEFAULT_WIKI_PATH = "H:/XlightsSourceDir/xLights.wiki"


def _wiki() -> "WikiManager":
    from xlights_mcp.wiki.manager import WikiManager
    config = get_config()
    path = config.wiki_path or _DEFAULT_WIKI_PATH
    return WikiManager(path)


@mcp.tool()
def wiki_set_path(path: str) -> dict:
    """Set the local path to the cloned xLights wiki repository.

    Args:
        path: Filesystem path to the cloned wiki (e.g. H:/XlightsSourceDir/xLights.wiki).
    """
    config = get_config()
    config.wiki_path = path
    save_config(config)
    return {"status": "ok", "wiki_path": path}


@mcp.tool()
def wiki_list_pages() -> dict:
    """List all pages currently in the local xLights wiki."""
    try:
        return {"pages": _wiki().list_pages()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
def wiki_read_page(page_name: str) -> dict:
    """Read the markdown content of a wiki page.

    Args:
        page_name: Page name (e.g. "Arches", "xLights-Manual", "_Sidebar").
    """
    try:
        content = _wiki().read_page(page_name)
        return {"page": page_name, "content": content, "length": len(content)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
def wiki_write_page(page_name: str, content: str) -> dict:
    """Write (create or overwrite) a wiki page with the given markdown content.

    The page is written locally — call wiki_commit_push to publish it.

    Args:
        page_name: Page name without extension (e.g. "Preferences", "Effects-Panel").
        content: Full markdown content for the page.
    """
    try:
        path = _wiki().write_page(page_name, content)
        return {"status": "ok", "written_path": str(path), "length": len(content)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
def wiki_screenshot_to_image(
    scene: str,
    image_name: str,
    region: str = "full",
) -> dict:
    """Capture a named xLights scene and save it into the wiki images/ folder.

    Combines xlights_navigate_and_screenshot with wiki image management.
    Returns the relative markdown image reference string ready to embed in a page.

    Args:
        scene: Scene name (use xlights_list_scenes to see options).
        image_name: Filename to use in images/ (e.g. "preferences-dialog.png").
        region: Named region to capture (default "full").
    """
    import tempfile, time as _time
    from pathlib import Path as _Path
    from xlights_mcp.xlights.screenshot import (
        find_xlights_window, capture_region, XLightsNotRunning,
    )
    from xlights_mcp.xlights.dialog_nav import SCENES
    from xlights_mcp.xlights.automation_client import call as automation_call, AutomationError

    try:
        win = find_xlights_window()
    except XLightsNotRunning as e:
        return {"status": "error", "error": str(e)}

    if scene not in SCENES:
        from xlights_mcp.xlights.dialog_nav import list_scenes
        return {"status": "error", "error": f"Unknown scene {scene!r}.", "available_scenes": list_scenes()}

    for step in SCENES[scene]:
        stype = step["type"]
        if stype == "automation":
            try:
                automation_call(step["cmd"], **{k: v for k, v in step.items() if k not in ("type", "cmd")})
            except AutomationError:
                pass
        elif stype == "menu":
            from xlights_mcp.xlights.dialog_nav import open_menu_path
            open_menu_path(step["path"])
        elif stype == "hotkey":
            from xlights_mcp.xlights.dialog_nav import press_hotkey
            press_hotkey(*step["keys"])
        elif stype == "click_fraction":
            from xlights_mcp.xlights.dialog_nav import click_at_fraction
            click_at_fraction(win.rect, step["x"], step["y"])
        elif stype == "wait":
            _time.sleep(step.get("seconds", 0.3))

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = _Path(tmp.name)

    try:
        capture_region(region, tmp_path)
        wiki = _wiki()
        rel_path = wiki.save_image(tmp_path, image_name)
        md = wiki.image_markdown(rel_path, image_name.replace("-", " ").replace(".png", ""))
        return {"status": "ok", "image_path": rel_path, "markdown": md}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        tmp_path.unlink(missing_ok=True)


@mcp.tool()
def wiki_status() -> dict:
    """Show git status of the local wiki — which pages have been modified."""
    try:
        status = _wiki().git_status()
        return {"status": "ok", "changes": status or "(clean — nothing modified)"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
def wiki_commit_push(message: str) -> dict:
    """Commit all local wiki changes and push them to GitHub.

    Args:
        message: Commit message describing what was updated.
    """
    try:
        return _wiki().commit_and_push(message)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
def wiki_pull() -> dict:
    """Pull latest changes from the remote wiki repository."""
    try:
        output = _wiki().pull()
        return {"status": "ok", "output": output}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    """Run the xLights MCP server."""
    log_dir = Path.home() / ".xlights-mcp"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s:%(name)s:%(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "server.log"),
        ],
        force=True,
    )
    logger.info("Starting xLights MCP Server v0.1.0")

    # Ensure config is loaded at startup
    config = get_config()
    logger.info(f"Active show: {config.active_show}")
    logger.info(f"Show path: {config.active_show_path}")

    mcp.run()


if __name__ == "__main__":
    main()
