"""Narrated showcase video for the create_beat_effect_sequence MCP tool.

Usage:
    python scripts/beat_effect_showcase.py
    python scripts/beat_effect_showcase.py --reel

Produces: feature_showcase_BeatEffectSequence.mp4  (or _reel.mp4)

Unlike effect_showcase.py's sections (same model/effect, different sliders),
each section here demonstrates a different beat_stride/beat_offset/
alternating_models combination — the actual knobs create_beat_effect_sequence
exposes. Beats are placed on a synthetic, evenly-spaced click grid (no real
song needed) using the exact same placement algorithm as the tool
(src/xlights_mcp/server.py::create_beat_effect_sequence -> _make_effects),
via direct addEffect calls on a throwaway in-memory sequence — nothing is
written to the user's show folder.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import effect_showcase as engine
from xlights_mcp.xlights import automation_client as ac

# ── Override configuration ─────────────────────────────────────────────────────

EFFECT = "Shockwave"
BPM = 128
BEAT_MS = round(60000 / BPM)

# Effects go on real leaf models, not Model Groups: placing an effect on a
# Group renders it in the group's own (wider) virtual buffer and only crops a
# slice onto each member, which reads as a flat color band instead of a ring.
# Groups also default new effect layers to "Default" instead of "Per Model
# Default", which can misrender ring/shape effects across differently-shaped
# members — another reason to target real models directly.
#
# FlatTree-N/FlatTreeStar-N were the first choice here, but exportModelWithRender
# turned out to dump the raw effect render buffer rather than mapping colors to
# each model's real (sparse) node positions — a solid Color Wash test came back
# as a plain filled rectangle instead of the dotted tree/star silhouette xLights'
# own Model Preview shows for those props. AA Mega Tree and Mega Star are true
# dense-matrix models (verified with the same Color Wash test: Mega Tree fills
# solid because every buffer cell is a real pixel on the wrapped tree; Mega Star
# renders the actual star silhouette with the rest of the buffer black), so
# Shockwave renders as a real ring/star-burst on them.
TREES = ["AA Mega Tree"]
STARS = ["Mega Star"]
ALL_MODELS = TREES + STARS

# exportModelWithRender renders one model at a time, so we render one
# representative tree and one representative star and composite them into a
# single frame. Each model tile is scaled (nearest-neighbor, to keep pixels
# crisp) to fill a large 720-wide box, then the two tiles are stacked
# top/bottom. That composite is already 720 wide, so build_video_shorts's own
# scale-to-720 step is a no-op and the effect fills almost the whole frame
# instead of being stranded small in one corner.
TREE_MODEL = TREES[0]
STAR_MODEL = STARS[0]
TILE_W = 720
TILE_H = 380

# A one-time screenshot of xLights' real "Effect Settings" panel (undocked,
# with a Shockwave effect selected), overlaid as a corner inset during the
# "Paste Your Own Settings" section so viewers see the actual sliders behind
# the effect_settings string, not just its result on the model.
SETTINGS_PANEL = Path(__file__).parent / "assets" / "shockwave_settings_panel.png"
SETTINGS_PANEL_SECTION = "Paste Your Own Settings"
SETTINGS_PANEL_W = 320

# A screenshot of the sequencer grid (ruler + the Mega Tree/Mega Star rows,
# showing the actual beat-placed effect blocks) is captured once after
# build_beat_sequence runs, then shown as a scrolling strip with a moving
# playhead across the whole video — so viewers see this is a real timeline
# with discrete effects, not just the resulting light animation.
GRID_STRIP_PATH: Path | None = None
GRID_H = 160
# Measured against this xLights window/layout with the "AI" View selected
# (AA Mega Tree/Mega Star are the only two models, always at a fixed
# position — no scroll dependence): within the "sequencer" named region, the
# ruler sits at y 92-116, then a "New Timing" timing-track row (always
# present regardless of View) at y ~210-232, then the two model rows at
# y 232-276, all starting at x=420 (past the model-list column). The t=0
# gridline and per-second pixel spacing below are measured off that same crop.
_GRID_RULER_BOX = (420, 92, None, 116)     # (left, top, right=full width, bottom)
_GRID_ROWS_BOX = (420, 223, None, 289)
_GRID_T0_PX = 244.0       # local x (within the crop) of the t=0 gridline
_GRID_PX_PER_SEC = 33.33  # local pixels per second at the crop's native scale

# Populated by build_beat_sequence with each section's (start_s, end_s) in the
# continuous xLights timeline, so _composite_export knows when to show the
# settings inset and how long the grid scroll should run.
SECTION_TIMES: list[tuple[float, float]] = []

_real_export_model_with_render = ac.export_model_with_render


# Name of the xLights View (Tools/Views, persists at the show level unlike
# per-sequence Display Elements visibility) containing only AA Mega Tree and
# Mega Star. Selecting it keeps the grid capture's row position fixed and
# scroll-independent — a fresh blank sequence would otherwise show every
# group in the show, at whatever position happened to be scrolled to.
GRID_VIEW_NAME = "AI"
# Fractions of the window rect for (1) the sequencer's "View:" combo box, and
# (2) the "AI" entry's position once the dropdown list is open. Both measured
# directly against this show's Views list (Master View, Sequencing, Trees,
# Stars, MH, Flakes, Singing, All Models Sorted, Matrix, EZ Map, 2024 New,
# AI — "AI" is the last entry). Type-ahead-select was tried first but it
# actually retargets the row list below the combo, not the combo itself, so
# this uses two explicit clicks instead.
_VIEW_COMBO_FRACTION = (0.279, 0.4656)
_VIEW_AI_ITEM_FRACTION = (0.222, 0.640)


def _select_grid_view(win) -> None:
    import time
    from xlights_mcp.xlights.dialog_nav import click_at_fraction

    click_at_fraction(win.rect, *_VIEW_COMBO_FRACTION)
    time.sleep(0.3)
    click_at_fraction(win.rect, *_VIEW_AI_ITEM_FRACTION)
    time.sleep(0.3)


def _capture_grid_strip(tmp_dir: Path) -> Path | None:
    """Screenshot the sequencer grid's ruler + Mega Star/AA Mega Tree rows."""
    import time
    from xlights_mcp.xlights import screenshot as ss
    from xlights_mcp.xlights.dialog_nav import click_at_fraction
    from PIL import Image

    try:
        win = ss.find_xlights_window()
        try:
            ss.bring_to_front(win)
        except Exception:
            pass
        click_at_fraction(win.rect, 0.094, 0.133)  # Sequencer tab
        time.sleep(0.5)
        _select_grid_view(win)
        raw = tmp_dir / "_grid_raw.png"
        ss.capture_region("sequencer", raw, bring_to_front=False)
    except Exception as e:
        print(f"  (grid screenshot skipped: {e})")
        return None

    im = Image.open(raw)
    w = im.size[0]
    rl, rt, _, rb = _GRID_RULER_BOX
    ol, ot, _, ob = _GRID_ROWS_BOX
    ruler = im.crop((rl, rt, w, rb))
    rows = im.crop((ol, ot, w, ob))
    strip = Image.new("RGB", (ruler.width, ruler.height + rows.height))
    strip.paste(ruler, (0, 0))
    strip.paste(rows, (0, ruler.height))
    out = tmp_dir / "_grid_strip.png"
    strip.save(out)
    return out


# exportModelWithRender dumps AA Mega Tree's raw effect buffer (a flattened
# unwrap of its spiral strands), which loses the tree's real triangular
# silhouette entirely — a solid Color Wash test came back as a plain filled
# rectangle. Mega Star renders fine via export (a true shape-aware model), so
# only the tree needs this: screen-record the live "Model Preview" panel
# during actual playback, which renders every model at its real node
# positions. Model Preview shows AA Mega Tree by default with the "AI" view
# selected regardless of which row is clicked, so no extra per-model
# selection step is needed.
_STOP_FRACTION = (0.2169, 0.0744)
_REWIND_FRACTION = (0.234, 0.0744)
_PLAY_FRACTION = (0.1823, 0.0744)
_MODEL_PREVIEW_FRACTION = (0.00723, 0.16985, 0.21384, 0.55534)  # left, top, right, bottom
# Inset a few px further to crop out the docked panel's own border/frame,
# which otherwise shows up as a thin white line around the tree tile.
_MODEL_PREVIEW_INSET_PX = 4


def _model_preview_rect(win_rect) -> tuple[int, int, int, int]:
    lf, tf, rf, bf = _MODEL_PREVIEW_FRACTION
    inset = _MODEL_PREVIEW_INSET_PX
    left = win_rect.left + int(lf * win_rect.width) + inset
    top = win_rect.top + int(tf * win_rect.height) + inset
    right = win_rect.left + int(rf * win_rect.width) - inset
    bottom = win_rect.top + int(bf * win_rect.height) - inset
    w, h = right - left, bottom - top
    w -= w % 2
    h -= h % 2
    return left, top, w, h


def _record_tree_model_preview(tmp_dir: Path, duration_s: float) -> Path | None:
    import subprocess
    import time
    from xlights_mcp.xlights import screenshot as ss
    from xlights_mcp.xlights.dialog_nav import click_at_fraction

    try:
        win = ss.find_xlights_window()
        try:
            ss.bring_to_front(win)
        except Exception:
            pass
        click_at_fraction(win.rect, 0.094, 0.133)  # Sequencer tab
        time.sleep(0.3)
        _select_grid_view(win)
        ac.render_all()
        click_at_fraction(win.rect, *_STOP_FRACTION)
        time.sleep(0.2)
        click_at_fraction(win.rect, *_REWIND_FRACTION)
        time.sleep(0.2)

        left, top, w, h = _model_preview_rect(win.rect)
        dest = tmp_dir / "_tree_preview_raw.mp4"
        cmd = [
            "ffmpeg", "-y", "-f", "gdigrab", "-framerate", "20",
            "-offset_x", str(left), "-offset_y", str(top),
            "-video_size", f"{w}x{h}", "-i", "desktop",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(dest),
        ]
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        time.sleep(0.6)  # gdigrab startup latency
        click_at_fraction(win.rect, *_PLAY_FRACTION)
        time.sleep(duration_s + 1.0)
        try:
            proc.communicate(input=b"q", timeout=10)
        except subprocess.TimeoutExpired:
            proc.terminate()
            proc.wait(timeout=5)
        return dest
    except Exception as e:
        print(f"  (tree model-preview recording skipped: {e})")
        return None


def _build_grid_clip(strip_path: Path, duration_s: float, dest: Path) -> None:
    from PIL import Image
    src_w, src_h = Image.open(strip_path).size
    scale = GRID_H / src_h
    scaled_w = round(src_w * scale)
    t0 = _GRID_T0_PX * scale
    px_per_sec = _GRID_PX_PER_SEC * scale
    crop_x = f"min({scaled_w}-720,max(0,{t0:.1f}+{px_per_sec:.3f}*t-360))"
    engine.ffmpeg(
        "-loop", "1", "-i", str(strip_path), "-t", f"{duration_s:.3f}",
        "-vf",
        f"scale=-2:{GRID_H}:flags=lanczos,"
        f"crop=720:{GRID_H}:x='{crop_x}':y=0,"
        f"drawbox=x=358:y=0:w=4:h={GRID_H}:color=red@0.85:t=fill",
        "-r", "20", "-c:v", "libx264", "-an", str(dest),
    )


def _composite_export(model, filename, *, format="mp4highquality", highdef=True, host=None, port=None):
    tmp_dir = Path(filename).parent
    total_s = SECTION_TIMES[-1][1] if SECTION_TIMES else 34.0

    left_raw = _record_tree_model_preview(tmp_dir, total_s)
    tree_is_recording = left_raw is not None
    if left_raw is None:
        left_raw = tmp_dir / "_left_raw.mp4"
        _real_export_model_with_render(TREE_MODEL, str(left_raw), format=format, highdef=highdef)

    right_raw = tmp_dir / "_right_raw.mp4"
    _real_export_model_with_render(STAR_MODEL, str(right_raw), format=format, highdef=highdef)

    # The tree tile is a real screen recording (already anti-aliased), so it
    # gets smooth scaling; the star tile is a tiny raw pixel buffer, so it
    # keeps nearest-neighbor to stay crisp instead of blurring into mush.
    fit_pad_tree = (
        f"scale={TILE_W}:{TILE_H}:force_original_aspect_ratio=decrease:flags=lanczos,"
        f"pad={TILE_W}:{TILE_H}:(ow-iw)/2:(oh-ih)/2:color=black"
    )
    fit_pad_star = (
        f"scale={TILE_W}:{TILE_H}:force_original_aspect_ratio=decrease:flags=neighbor,"
        f"pad={TILE_W}:{TILE_H}:(ow-iw)/2:(oh-ih)/2:color=black"
    )
    # Star on top, tree on bottom.
    top = tmp_dir / "_top.mp4"       # star
    bottom = tmp_dir / "_bottom.mp4"  # tree
    engine.ffmpeg("-i", str(right_raw), "-vf", fit_pad_star, "-c:v", "libx264", "-an", str(top))
    if tree_is_recording:
        # Skip the ~0.6s of dead/static footage recorded before the Play
        # click actually lands, so the tree tile lines up with the star tile
        # and the grid playhead instead of lagging behind them.
        engine.ffmpeg("-ss", "0.6", "-i", str(left_raw), "-t", f"{total_s:.3f}",
                      "-vf", fit_pad_tree, "-c:v", "libx264", "-an", str(bottom))
    else:
        engine.ffmpeg("-i", str(left_raw), "-t", f"{total_s:.3f}",
                      "-vf", fit_pad_star, "-c:v", "libx264", "-an", str(bottom))

    stack_inputs = ["-i", str(top), "-i", str(bottom)]
    filter_parts = ["[0:v][1:v]vstack=inputs=2[v]"]
    if GRID_STRIP_PATH is not None and SECTION_TIMES:
        total_s = SECTION_TIMES[-1][1]
        grid_clip = tmp_dir / "_grid.mp4"
        _build_grid_clip(GRID_STRIP_PATH, total_s, grid_clip)
        stack_inputs = ["-i", str(grid_clip)] + stack_inputs
        filter_parts = ["[0:v][1:v][2:v]vstack=inputs=3[v]"]

    stacked = tmp_dir / "_stacked.mp4"
    engine.ffmpeg(*stack_inputs, "-filter_complex", ";".join(filter_parts), "-map", "[v]", str(stacked))

    inset_window = next(
        (times for (label, *_), times in zip(SECTIONS, SECTION_TIMES) if label == SETTINGS_PANEL_SECTION),
        None,
    )
    if SETTINGS_PANEL.exists() and inset_window is not None:
        start_s, end_s = inset_window
        engine.ffmpeg(
            "-i", str(stacked), "-i", str(SETTINGS_PANEL),
            "-filter_complex",
            f"[1:v]scale={SETTINGS_PANEL_W}:-1[panel];"
            f"[0:v][panel]overlay=W-w-24:H-h-24:enable='between(t,{start_s:.3f},{end_s:.3f})'[v]",
            "-map", "[v]", str(filename),
        )
    else:
        stacked.replace(filename)
    return {"msg": "composite exported", "res": 200}


ac.export_model_with_render = _composite_export

# engine.main()'s stock intro line is "{TITLE_LINE3} effect showcase." — for a
# feature (not a light effect) that reads as an awkward "Effects effect
# showcase." double-up. Reorder it to match the title card: "Feature Showcase:
# {TITLE_LINE3}."
_real_generate_narration = engine.generate_narration


def _generate_narration_patched(text: str, dest, silence_ms: int = 800) -> None:
    text = text.replace(f"{engine.TITLE_LINE3} effect showcase.", f"Feature Showcase: {engine.TITLE_LINE3}.")
    text = text.replace("Effect Showcase:", "Feature Showcase:")
    return _real_generate_narration(text, dest, silence_ms)


engine.generate_narration = _generate_narration_patched

engine.MODEL       = "Trees + Tree Stars (composite)"
engine.TITLE_LINE2 = "Feature Showcase"
engine.TITLE_LINE3 = "Beat-Synced Effects"
engine.OUTRO_LINE1 = "Thanks For"
engine.OUTRO_LINE2 = "Watching!"
engine.OUTRO_LINE3 = "Like & Subscribe"
engine.OUT_FILE    = Path(__file__).parent.parent / "feature_showcase_BeatEffectSequence.mp4"


def _s(params: dict) -> str:
    return ",".join(f"{k}={v}" for k, v in params.items())


def _palette(colors: list[str]) -> str:
    parts = []
    for i, c in enumerate(colors, start=1):
        parts.append(f"C_BUTTON_Palette{i}=#{c.lstrip('#')}")
        parts.append(f"C_CHECKBOX_Palette{i}=1")
    return ",".join(parts)


# ── Sections ──────────────────────────────────────────────────────────────────
# Each entry: (label, subtitle, narration, short_narration, params)
# params mirrors create_beat_effect_sequence's real arguments.

SECTIONS = [
    (
        "Sync To The Beat",
        "beat_stride=1 | every beat",
        "This is create_beat_effect_sequence — a new tool that analyzes your song, "
        "finds every beat, and drops an effect right on top of it automatically. "
        "Here, a Shockwave ring fires on every single beat across the trees and stars, "
        "perfectly in time, with zero manual placement.",
        "One tool call syncs Shockwave to every beat. Zero manual placement.",
        {
            "models": ALL_MODELS,
            "alternating_models": None,
            "beat_stride": 1,
            "beat_offset": 0,
            "colors": ["#66CCFF"],
            "effect_settings": {
                "E_SLIDER_Shockwave_Start_Radius": 30,
                "E_SLIDER_Shockwave_End_Radius": 85,
                "E_SLIDER_Shockwave_Start_Width": 20,
                "E_SLIDER_Shockwave_End_Width": 30,
                "E_SLIDER_Shockwave_Accel": -10,
                "E_CHECKBOX_Shockwave_Scale": 1,
            },
        },
    ),
    (
        "The Ping-Pong Trick",
        "alternating_models | trees vs. stars",
        "Here's the signature move: pass a second group of models as alternating_models "
        "and they fire on the beats in between. Trees flash on the even beats, tree stars "
        "answer on the odd beats, bouncing back and forth in a beat-locked ping-pong.",
        "Trees and stars trade off on opposite beats — a beat-locked ping-pong.",
        {
            "models": TREES,
            "alternating_models": STARS,
            "beat_stride": 2,
            "beat_offset": 0,
            "colors": ["#FFFFFF"],
            "effect_settings": {
                "E_SLIDER_Shockwave_Start_Radius": 30,
                "E_SLIDER_Shockwave_End_Radius": 85,
                "E_SLIDER_Shockwave_Start_Width": 20,
                "E_SLIDER_Shockwave_End_Width": 30,
                "E_SLIDER_Shockwave_Accel": -10,
                "E_CHECKBOX_Shockwave_Scale": 1,
            },
        },
    ),
    (
        "Downbeat Drama",
        "beat_stride=4 | downbeats only",
        "Bump beat_stride up to four and the effect only lands on the downbeat of every "
        "bar — the first beat of four — for a slower, more dramatic pulse. xLights even "
        "auto-builds a Bars timing track alongside it so you can see the measure count.",
        "Stride four fires only on downbeats, for a slower, dramatic pulse.",
        {
            "models": ALL_MODELS,
            "alternating_models": None,
            "beat_stride": 4,
            "beat_offset": 0,
            "colors": ["#FF3333", "#FFAA00"],
            "effect_settings": {
                "E_SLIDER_Shockwave_Start_Radius": 20,
                "E_SLIDER_Shockwave_End_Radius": 110,
                "E_SLIDER_Shockwave_Start_Width": 15,
                "E_SLIDER_Shockwave_End_Width": 20,
                "E_SLIDER_Shockwave_Accel": -6,
                "E_CHECKBOX_Shockwave_Scale": 1,
            },
        },
    ),
    (
        "Paste Your Own Settings",
        "effect_settings | straight from xLights",
        "Already dialed in a look you love in xLights? Copy the effect and paste the "
        "CopyFormat string straight into effect_settings — palette entries get stripped "
        "out automatically, so there's nothing to translate by hand.",
        "Paste a CopyFormat string straight in — nothing to translate by hand.",
        {
            "models": STARS,
            "alternating_models": TREES,
            "beat_stride": 2,
            "beat_offset": 1,
            "colors": ["#39FF14", "#FF00FF"],
            "effect_settings": {
                "E_SLIDER_Shockwave_Start_Radius": 25,
                "E_SLIDER_Shockwave_End_Radius": 80,
                "E_SLIDER_Shockwave_Start_Width": 20,
                "E_SLIDER_Shockwave_End_Width": 25,
                "E_SLIDER_Shockwave_Accel": -10,
                "E_CHECKBOX_Shockwave_Blend_Edges": 1,
                "E_CHECKBOX_Shockwave_Scale": 1,
            },
        },
    ),
    (
        "Any Stride, Any Offset",
        "beat_stride=3, beat_offset=1 | syncopated",
        "Stride and offset are fully adjustable, so you can lock onto any rhythmic "
        "pattern the song calls for — here it's every third beat starting on the second, "
        "for a syncopated, off-kilter feel.",
        "Stride three, offset one — a syncopated, off-kilter pattern.",
        {
            "models": ALL_MODELS,
            "alternating_models": None,
            "beat_stride": 3,
            "beat_offset": 1,
            "colors": ["#8A2BE2"],
            "effect_settings": {
                "E_SLIDER_Shockwave_Start_Radius": 25,
                "E_SLIDER_Shockwave_End_Radius": 70,
                "E_SLIDER_Shockwave_Start_Width": 18,
                "E_SLIDER_Shockwave_End_Width": 22,
                "E_SLIDER_Shockwave_Accel": -10,
                "E_CHECKBOX_Shockwave_Scale": 1,
            },
        },
    ),
    (
        "Grand Finale",
        "Full ping-pong | every beat",
        "For the finale, crank it back to every single beat with the full trees-and-stars "
        "ping-pong running at once — an entire beat-synced sequence built from one function call.",
        "Every beat, full ping-pong — a whole sequence from one function call.",
        {
            "models": TREES,
            "alternating_models": STARS,
            "beat_stride": 1,
            "beat_offset": 0,
            "colors": ["#FF0040", "#00FFAA", "#FFD400"],
            "effect_settings": {
                "E_SLIDER_Shockwave_Start_Radius": 30,
                "E_SLIDER_Shockwave_End_Radius": 90,
                "E_SLIDER_Shockwave_Start_Width": 20,
                "E_SLIDER_Shockwave_End_Width": 30,
                "E_SLIDER_Shockwave_Accel": -10,
                "E_CHECKBOX_Shockwave_Scale": 1,
            },
        },
    ),
]
engine.SECTIONS = SECTIONS


# ── Beat placement (mirrors create_beat_effect_sequence's _make_effects) ──────

def _add_effect_retrying(*, target, effect, settings, palette, layer, start_time_ms, end_time_ms, retries=3):
    """xLights' automation HTTP handler occasionally can't keep up with
    back-to-back addEffect calls and returns a transient 'No command' 503 —
    a brief retry clears it without needing to restart the whole render."""
    import time

    for attempt in range(retries):
        try:
            return ac.add_effect(
                target=target, effect=effect, settings=settings, palette=palette,
                layer=layer, start_time_ms=start_time_ms, end_time_ms=end_time_ms,
            )
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(0.2)


def _place_section(start_ms: int, end_ms: int, params: dict) -> int:
    beats = list(range(start_ms, end_ms, BEAT_MS)) or [start_ms]
    stride = params["beat_stride"]
    offset = params["beat_offset"] % stride
    settings_str = _s(params["effect_settings"])
    palette_str = _palette(params["colors"])

    count = 0

    def place(models: list[str], idx_offset: int) -> None:
        nonlocal count
        for model in models:
            for idx in range(idx_offset, len(beats), stride):
                b_start = beats[idx]
                b_end = beats[idx + 1] if idx + 1 < len(beats) else min(b_start + BEAT_MS, end_ms)
                _add_effect_retrying(
                    target=model, effect=EFFECT,
                    settings=settings_str, palette=palette_str,
                    layer=0, start_time_ms=b_start, end_time_ms=b_end,
                )
                count += 1

    place(params["models"], offset)
    if params.get("alternating_models"):
        place(params["alternating_models"], (offset + 1) % stride)
    return count


def build_beat_sequence(section_durations: list[float]) -> None:
    total_secs = int(sum(section_durations)) + 1
    print(f"Creating blank sequence ({total_secs}s) in xLights...")
    ac.close_sequence(force=True)
    ac.new_sequence(total_secs, frame_ms=50)

    print(f"Placing beat-synced {EFFECT} across {len(SECTIONS)} demos ({BPM} BPM)...")
    SECTION_TIMES.clear()
    start_ms = 0
    for i, (label, _, _, _, params) in enumerate(SECTIONS):
        dur_ms = int(section_durations[i] * 1000)
        end_ms = start_ms + dur_ms
        n = _place_section(start_ms, end_ms, params)
        print(f"  [{i+1}/{len(SECTIONS)}] {label:24s}  {section_durations[i]:.1f}s  effects={n}")
        SECTION_TIMES.append((start_ms / 1000, end_ms / 1000))
        start_ms = end_ms

    print("Capturing sequencer grid screenshot...")
    global GRID_STRIP_PATH
    assets_dir = Path(__file__).parent / "assets"
    GRID_STRIP_PATH = _capture_grid_strip(assets_dir)
    if GRID_STRIP_PATH:
        print(f"  saved {GRID_STRIP_PATH}")


engine.build_sequence = build_beat_sequence

# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    engine.main()
