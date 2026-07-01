"""Generate a narrated showcase video for an xLights effect.

Usage:
    python scripts/effect_showcase.py

Produces: effect_showcase_Fireworks.mp4

Workflow:
  1. Create a blank sequence via xLights automation API
  2. Place the effect with different parameters for each section
  3. Render and export the house preview video
  4. Generate per-section narration with edge-tts
  5. Combine with ffmpeg: video + PIL text overlays + narration
"""

import asyncio
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from xlights_mcp.xlights import automation_client as ac

# ── Configuration ─────────────────────────────────────────────────────────────

EFFECT         = "Fireworks"
MODEL          = "TV-Right"
MIN_SECTION_S  = 6      # minimum seconds per section (padded if narration is shorter)
TITLE_LINE1    = "xLights Bonus Gem"
TITLE_LINE2    = "Effect Showcase"
TITLE_LINE3    = EFFECT
OUTRO_LINE1    = "Thanks For"
OUTRO_LINE2    = "Watching!"
OUTRO_LINE3    = "Like & Subscribe"
OUT_FILE       = Path(__file__).parent.parent / "effect_showcase_Fireworks.mp4"

# Shorts (9:16 vertical, <60 s) — pass --shorts on the command line
SHORTS_W       = 720
SHORTS_H       = 1280
SHORTS_MIN_S   = 5    # tighter minimum so 7 sections + intro + outro fit under 60 s

# Branded backdrop for the Reel/Shorts intro card. Already contains the "xLights"
# logo and "Bonus Gem Series" wordmark, so the generated title only needs to fill
# the empty box near the top of the image.
INTRO_BACKDROP = Path(__file__).parent / "assets" / "bonus_gem_intro_backdrop.png"
# Empty title box in the backdrop's native pixel space (left, top, right, bottom),
# measured from scripts/assets/bonus_gem_intro_backdrop.png (768x1376).
INTRO_BACKDROP_BOX = (60, 55, 705, 215)

# Scale the model export before compositing (1.0 = full size).
# 0.5 = half width/height = 1/4 area; model is centered in a 640×360 canvas.
MODEL_DISPLAY_SCALE = 1.0
MIN_CANVAS_W        = 640   # landscape canvas is at least this wide for readable text
MIN_CANVAS_H        = 360
VOICE          = "en-US-AriaNeural"   # edge-tts voice
FONT_FILE      = "C:/Windows/Fonts/arialbd.ttf"  # PIL font path (forward slashes fine on Windows)

# Colorful palette for Fireworks
PALETTE = (
    "C_BUTTON_Palette1=#FF0000,C_CHECKBOX_Palette1=1,"
    "C_BUTTON_Palette2=#FF8C00,C_CHECKBOX_Palette2=1,"
    "C_BUTTON_Palette3=#FFFF00,C_CHECKBOX_Palette3=1,"
    "C_BUTTON_Palette4=#00CC00,C_CHECKBOX_Palette4=1,"
    "C_BUTTON_Palette5=#0088FF,C_CHECKBOX_Palette5=1,"
    "C_BUTTON_Palette6=#CC00FF,C_CHECKBOX_Palette6=1"
)

def _s(params: dict) -> str:
    """Build a settings string from a parameter dict."""
    return ",".join(f"{k}={v}" for k, v in params.items())

# ── Sections ──────────────────────────────────────────────────────────────────
# Each entry: (label, subtitle, narration, settings_dict)

SECTIONS = [
    (
        "Default Settings",
        "Explosions: 16 | Particles: 50 | Velocity: 2",
        "The Fireworks effect creates colorful burst animations across your display. "
        "Here are the default settings: sixteen explosions, fifty particles each.",
        "Default settings. Sixteen explosions, fifty particles each.",
        {
            "E_SLIDER_Fireworks_Explosions": 16,
            "E_SLIDER_Fireworks_Count":      50,
            "E_SLIDER_Fireworks_Velocity":   2,
            "E_SLIDER_Fireworks_Fade":       50,
            "E_CHECKBOX_Fireworks_Gravity":  1,
        },
    ),
    (
        "High Density",
        "Explosions: 40 | Particles: 80 | Velocity: 2",
        "Increasing both explosions and particles creates a dense, shower-like effect "
        "that fills the display with color.",
        "High density. Forty explosions, eighty particles fill the display.",
        {
            "E_SLIDER_Fireworks_Explosions": 40,
            "E_SLIDER_Fireworks_Count":      80,
            "E_SLIDER_Fireworks_Velocity":   2,
            "E_SLIDER_Fireworks_Fade":       50,
            "E_CHECKBOX_Fireworks_Gravity":  1,
        },
    ),
    (
        "Big Blasts",
        "Explosions: 5 | Particles: 100 | Velocity: 2",
        "Fewer explosions with maximum particles creates large, dramatic bursts "
        "that spread across the entire panel.",
        "Big blasts. Five explosions, one hundred particles each.",
        {
            "E_SLIDER_Fireworks_Explosions": 5,
            "E_SLIDER_Fireworks_Count":      100,
            "E_SLIDER_Fireworks_Velocity":   2,
            "E_SLIDER_Fireworks_Fade":       50,
            "E_CHECKBOX_Fireworks_Gravity":  1,
        },
    ),
    (
        "Fast Velocity",
        "Explosions: 16 | Particles: 50 | Velocity: 9",
        "Cranking up the velocity shoots particles rapidly outward, "
        "giving the fireworks a sharp, energetic look.",
        "Fast velocity. Particles shoot rapidly outward at speed nine.",
        {
            "E_SLIDER_Fireworks_Explosions": 16,
            "E_SLIDER_Fireworks_Count":      50,
            "E_SLIDER_Fireworks_Velocity":   9,
            "E_SLIDER_Fireworks_Fade":       50,
            "E_CHECKBOX_Fireworks_Gravity":  1,
        },
    ),
    (
        "No Gravity",
        "Explosions: 16 | Particles: 50 | Gravity: Off",
        "Disabling gravity lets particles drift freely in all directions, "
        "creating a radial starburst pattern.",
        "No gravity. Particles drift freely in all directions.",
        {
            "E_SLIDER_Fireworks_Explosions": 16,
            "E_SLIDER_Fireworks_Count":      50,
            "E_SLIDER_Fireworks_Velocity":   2,
            "E_SLIDER_Fireworks_Fade":       50,
            "E_CHECKBOX_Fireworks_Gravity":  0,
        },
    ),
    (
        "Slow Fade",
        "Explosions: 16 | Particles: 50 | Fade: 90",
        "A high fade value makes each explosion linger on screen, "
        "producing a glowing, trailing effect.",
        "Slow fade. Explosions linger and glow on screen.",
        {
            "E_SLIDER_Fireworks_Explosions": 16,
            "E_SLIDER_Fireworks_Count":      50,
            "E_SLIDER_Fireworks_Velocity":   2,
            "E_SLIDER_Fireworks_Fade":       90,
            "E_CHECKBOX_Fireworks_Gravity":  1,
        },
    ),
    (
        "Grand Finale",
        "Explosions: 40 | Particles: 100 | Velocity: 8",
        "Combine maximum explosions, particles, and velocity for an intense finale "
        "that lights up every pixel on the display.",
        "Grand finale. Maximum explosions, particles, and velocity.",
        {
            "E_SLIDER_Fireworks_Explosions": 40,
            "E_SLIDER_Fireworks_Count":      100,
            "E_SLIDER_Fireworks_Velocity":   8,
            "E_SLIDER_Fireworks_Fade":       50,
            "E_CHECKBOX_Fireworks_Gravity":  1,
        },
    ),
]

# ── Narration ─────────────────────────────────────────────────────────────────

async def _tts_sentence(text: str, dest: Path, voice: str = VOICE) -> None:
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(dest))


def _make_silence_mp3(dest: Path, duration_s: float) -> None:
    """Write a silent MP3 matching edge-tts output (24 kHz mono)."""
    result = subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
         "-t", f"{duration_s:.3f}", "-c:a", "mp3", "-q:a", "4", str(dest)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"silence generation failed:\n{result.stderr[-500:]}")


def generate_narration(text: str, dest: Path, silence_ms: int = 800) -> None:
    """Generate narration audio with a silence gap between each sentence.

    Splits on sentence boundaries, renders each via edge-tts, then
    concatenates sentence MP3s with a silence MP3 using ffmpeg concat demuxer.
    """
    sentences = [s.strip() for s in re.split(r'(?<=\.)\s+', text) if s.strip()]
    if len(sentences) == 1:
        asyncio.run(_tts_sentence(text, dest))
        return

    with tempfile.TemporaryDirectory(prefix="tts_") as tmp_str:
        tmp = Path(tmp_str)

        # Generate silence file once (matches edge-tts 24 kHz mono output)
        silence_mp3 = tmp / "silence.mp3"
        _make_silence_mp3(silence_mp3, silence_ms / 1000.0)

        # Render each sentence to its own mp3
        parts: list[Path] = []
        for i, sentence in enumerate(sentences):
            part = tmp / f"sent_{i:02d}.mp3"
            asyncio.run(_tts_sentence(sentence, part))
            parts.append(part)

        # Build concat list: sent0, silence, sent1, silence, sent2, ...
        entries: list[str] = []
        for i, part in enumerate(parts):
            entries.append(f"file '{part}'")
            if i < len(parts) - 1:
                entries.append(f"file '{silence_mp3}'")

        concat_list = tmp / "concat.txt"
        concat_list.write_text("\n".join(entries), encoding="utf-8")

        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
               "-i", str(concat_list), "-c:a", "mp3", str(dest)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"narration concat failed:\n{result.stderr[-1500:]}")


# ── xLights sequence build ────────────────────────────────────────────────────

def build_sequence(section_durations: list[float]) -> None:
    total_secs = int(sum(section_durations)) + 1
    print(f"Creating blank sequence ({total_secs}s) in xLights...")
    ac.close_sequence(force=True)
    ac.new_sequence(total_secs, frame_ms=50)

    print(f"Adding {len(SECTIONS)} {EFFECT} sections to '{MODEL}'...")
    start_ms = 0
    for i, (label, _, _, _, params) in enumerate(SECTIONS):
        end_ms   = start_ms + int(section_durations[i] * 1000)
        settings = _s(params)
        result = ac.add_effect(
            target=MODEL, effect=EFFECT,
            settings=settings, palette=PALETTE,
            layer=0, start_time_ms=start_ms, end_time_ms=end_ms,
        )
        worked = result.get("worked", "?")
        print(f"  [{i+1}/{len(SECTIONS)}] {label:20s}  {section_durations[i]:.1f}s  worked={worked}")
        start_ms = end_ms


# ── Video production ──────────────────────────────────────────────────────────

def ffmpeg(*args, check=True):
    cmd = ["ffmpeg", "-y"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr[-2000:]}")
    return result


def _probe_dimensions(video: Path) -> tuple[int, int]:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-of", "csv=p=0", str(video)],
        capture_output=True, text=True,
    )
    parts = probe.stdout.strip().split(",")
    return int(parts[0] or 640), int(parts[1] or 360)


def _font_sizes(h: int) -> tuple[int, int]:
    """Return (label_px, subtitle_px) scaled to video height.

    Caps keep text readable on small model exports; a minimum ensures
    it's visible even on very tall videos.
    """
    label_px    = max(14, min(h // 12, 36))
    subtitle_px = max(10, min(h // 18, 24))
    return label_px, subtitle_px


def _load_fonts(h: int):
    label_px, subtitle_px = _font_sizes(h)
    try:
        return (
            ImageFont.truetype(FONT_FILE, label_px),
            ImageFont.truetype(FONT_FILE, subtitle_px),
        )
    except OSError:
        default = ImageFont.load_default()
        return default, default


def _make_text_overlay(label: str, subtitle: str, w: int, h: int, dest: Path) -> None:
    """Render a transparent PNG with label+subtitle bar at the bottom."""
    font_large, font_small = _load_fonts(h)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = max(4, h // 60)          # box padding scales with height
    gap = max(4, h // 40)          # gap between the two bars

    # Label bar (white text, semi-transparent dark background)
    lbbox = draw.textbbox((0, 0), label, font=font_large)
    lw, lh = lbbox[2] - lbbox[0], lbbox[3] - lbbox[1]
    label_bar_h = lh + pad * 2
    subtitle_bar_h = draw.textbbox((0, 0), subtitle, font=font_small)[3] + pad * 2
    total_h = label_bar_h + gap + subtitle_bar_h
    bottom_margin = max(6, h // 30)

    ly = h - total_h - bottom_margin
    lx = (w - lw) // 2
    draw.rectangle([lx - pad, ly - pad, lx + lw + pad, ly + lh + pad],
                   fill=(0, 0, 0, 160))
    draw.text((lx, ly), label, font=font_large, fill=(255, 255, 255, 255))

    # Subtitle bar (yellow text)
    sbbox = draw.textbbox((0, 0), subtitle, font=font_small)
    sw, sh = sbbox[2] - sbbox[0], sbbox[3] - sbbox[1]
    sy = ly + lh + pad + gap
    sx = (w - sw) // 2
    draw.rectangle([sx - pad, sy - pad, sx + sw + pad, sy + sh + pad],
                   fill=(0, 0, 0, 160))
    draw.text((sx, sy), subtitle, font=font_small, fill=(255, 255, 0, 255))

    img.save(dest, "PNG")


def _make_intro_frame_backdrop(w: int, h: int, dest: Path, backdrop_path: Path) -> None:
    """Render the intro frame on the branded backdrop image, with the section
    title (Effect Showcase / <effect name>) placed inside its empty title box."""
    bg = Image.open(backdrop_path).convert("RGB")
    src_w, src_h = bg.size
    scale = max(w / src_w, h / src_h)
    new_w, new_h = round(src_w * scale), round(src_h * scale)
    bg = bg.resize((new_w, new_h), Image.LANCZOS)
    off_x, off_y = (new_w - w) // 2, (new_h - h) // 2
    img = bg.crop((off_x, off_y, off_x + w, off_y + h))
    draw = ImageDraw.Draw(img)

    bx0, by0, bx1, by1 = INTRO_BACKDROP_BOX
    box_x0, box_y0 = bx0 * scale - off_x, by0 * scale - off_y
    box_x1, box_y1 = bx1 * scale - off_x, by1 * scale - off_y
    box_w, box_h = box_x1 - box_x0, box_y1 - box_y0

    def fit_font(text: str, max_w: float, max_h: float) -> ImageFont.FreeTypeFont:
        size = int(max_h)
        font = ImageFont.load_default()
        while size > 6:
            try:
                font = ImageFont.truetype(FONT_FILE, size)
            except OSError:
                break
            bbox = draw.textbbox((0, 0), text, font=font)
            if bbox[2] - bbox[0] <= max_w and bbox[3] - bbox[1] <= max_h:
                break
            size -= 2
        return font

    label_text = TITLE_LINE2.upper()   # "EFFECT SHOWCASE"
    title_text = TITLE_LINE3.upper()   # effect name, e.g. "SNOWFLAKES"
    gap = box_h * 0.06

    label_font = fit_font(label_text, box_w * 0.95, box_h * 0.32)
    title_font = fit_font(title_text, box_w * 0.95, box_h * 0.56)

    lbbox = draw.textbbox((0, 0), label_text, font=label_font)
    tbbox = draw.textbbox((0, 0), title_text, font=title_font)
    lw, lh = lbbox[2] - lbbox[0], lbbox[3] - lbbox[1]
    tw, th = tbbox[2] - tbbox[0], tbbox[3] - tbbox[1]

    start_y = box_y0 + (box_h - (lh + gap + th)) / 2
    draw.text((box_x0 + (box_w - lw) / 2, start_y - lbbox[1]),
              label_text, font=label_font, fill=(200, 220, 255))
    draw.text((box_x0 + (box_w - tw) / 2, start_y + lh + gap - tbbox[1]),
              title_text, font=title_font, fill=(255, 255, 255))

    img.save(dest, "PNG")


def _make_intro_frame(w: int, h: int, dest: Path, backdrop_path: Path | None = None) -> None:
    """Render the intro frame: on the branded backdrop if provided, else a plain
    black three-line title (opaque RGB PNG for looping)."""
    if backdrop_path and backdrop_path.exists():
        _make_intro_frame_backdrop(w, h, dest, backdrop_path)
        return

    line1_px = max(14, min(h // 13, 32))   # "xLights Bonus Gem" — smallest
    line2_px = max(16, min(h // 11, 38))   # "Effect Showcase"
    line3_px = max(24, min(h //  7, 64))   # effect name — largest, yellow
    try:
        font1 = ImageFont.truetype(FONT_FILE, line1_px)
        font2 = ImageFont.truetype(FONT_FILE, line2_px)
        font3 = ImageFont.truetype(FONT_FILE, line3_px)
    except OSError:
        font1 = font2 = font3 = ImageFont.load_default()

    img  = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    gap  = max(6, h // 35)

    def bbox(text, font):
        b = draw.textbbox((0, 0), text, font=font)
        return b[2] - b[0], b[3] - b[1]

    w1, h1 = bbox(TITLE_LINE1, font1)
    w2, h2 = bbox(TITLE_LINE2, font2)
    w3, h3 = bbox(TITLE_LINE3, font3)
    total = h1 + gap + h2 + gap + h3
    y = (h - total) // 2

    draw.text(((w - w1) // 2, y),                  TITLE_LINE1, font=font1, fill=(200, 200, 200))
    draw.text(((w - w2) // 2, y + h1 + gap),        TITLE_LINE2, font=font2, fill=(255, 255, 255))
    draw.text(((w - w3) // 2, y + h1 + gap + h2 + gap), TITLE_LINE3, font=font3, fill=(255, 255, 0))

    img.save(dest, "PNG")


def _make_outro_frame(w: int, h: int, dest: Path) -> None:
    """Render a black outro frame with three-line call-to-action."""
    line1_px = max(16, min(h // 10, 48))   # "Thanks For"
    line2_px = max(20, min(h //  8, 56))   # "Watching!" — largest
    line3_px = max(14, min(h // 12, 36))   # "Like & Subscribe" — yellow, smallest
    try:
        font1 = ImageFont.truetype(FONT_FILE, line1_px)
        font2 = ImageFont.truetype(FONT_FILE, line2_px)
        font3 = ImageFont.truetype(FONT_FILE, line3_px)
    except OSError:
        font1 = font2 = font3 = ImageFont.load_default()

    img  = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    gap  = max(6, h // 35)

    def bbox(text, font):
        b = draw.textbbox((0, 0), text, font=font)
        return b[2] - b[0], b[3] - b[1]

    w1, h1 = bbox(OUTRO_LINE1, font1)
    w2, h2 = bbox(OUTRO_LINE2, font2)
    w3, h3 = bbox(OUTRO_LINE3, font3)
    total  = h1 + gap + h2 + gap + h3
    y      = (h - total) // 2

    draw.text(((w - w1) // 2, y),                      OUTRO_LINE1, font=font1, fill=(200, 200, 200))
    draw.text(((w - w2) // 2, y + h1 + gap),            OUTRO_LINE2, font=font2, fill=(255, 255, 255))
    draw.text(((w - w3) // 2, y + h1 + gap + h2 + gap), OUTRO_LINE3, font=font3, fill=(255, 215, 0))

    img.save(dest, "PNG")


def _probe_audio_duration(path: Path) -> float:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    return float(probe.stdout.strip() or 0)


def build_video(
    full_video: Path,
    tmp: Path,
    narr_files: list[Path],
    section_durations: list[float],
    intro_narr: Path,
    intro_dur: float,
    outro_narr: Path,
    outro_dur: float,
) -> Path:
    vid_w, vid_h = _probe_dimensions(full_video)

    # Build a 16:9 canvas at least MIN_CANVAS_W wide so text has room to breathe.
    # The model is centered both horizontally and vertically.
    canvas_w = max(vid_w, (vid_h * 16 // 9), MIN_CANVAS_W)
    if canvas_w % 2:
        canvas_w += 1
    canvas_h = max(vid_h, canvas_w * 9 // 16, MIN_CANVAS_H)
    if canvas_h % 2:
        canvas_h += 1
    pad_x = (canvas_w - vid_w) // 2
    pad_y = (canvas_h - vid_h) // 2
    if canvas_w != vid_w or canvas_h != vid_h:
        print(f"  Canvas: {vid_w}x{vid_h} model -> {canvas_w}x{canvas_h} frame")

    section_clips = []

    start_s = 0.0
    for i, (label, subtitle, _, _, _) in enumerate(SECTIONS):
        sec_dur     = section_durations[i]
        narr_mp3    = narr_files[i]
        clip_mp4    = tmp / f"clip_{i:02d}.mp4"
        overlay_png = tmp / f"overlay_{i:02d}.png"
        muxed       = tmp / f"muxed_{i:02d}.mp4"

        print(f"  Section {i+1}: trimming video clip ({sec_dur:.1f}s)...")
        ffmpeg(
            "-ss", f"{start_s:.3f}", "-i", str(full_video),
            "-t", f"{sec_dur:.3f}", "-c:v", "libx264", "-an",
            str(clip_mp4),
        )
        start_s += sec_dur

        narr_dur = _probe_audio_duration(narr_mp3)
        pad = max(0.0, sec_dur - narr_dur)

        print(f"  Section {i+1}: compositing overlays...")
        _make_text_overlay(label, subtitle, canvas_w, canvas_h, overlay_png)

        # Pad clip to canvas, then overlay text
        fc = (
            f"[0:v]pad={canvas_w}:{canvas_h}:{pad_x}:{pad_y}:black[padded];"
            f"[padded][1:v]overlay=0:0[v];"
            f"[2:a]apad=pad_dur={pad:.3f}[a]"
        )
        ffmpeg(
            "-i", str(clip_mp4),
            "-i", str(overlay_png),
            "-i", str(narr_mp3),
            "-filter_complex", fc,
            "-map", "[v]", "-map", "[a]",
            "-t", f"{sec_dur:.3f}", "-c:v", "libx264", "-c:a", "aac",
            str(muxed),
        )
        section_clips.append(muxed)

    # Probe xLights export fps so intro matches it exactly
    fps_probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=r_frame_rate",
         "-of", "default=noprint_wrappers=1:nokey=1", str(full_video)],
        capture_output=True, text=True,
    )
    raw_fps = fps_probe.stdout.strip() or "30/1"
    # r_frame_rate is a fraction like "20/1"; pass it straight to ffmpeg -r
    print(f"  xLights export fps: {raw_fps}")

    # Concatenate all section clips — re-encode so all have identical timebase/fps
    print("Concatenating sections...")
    concat_list = tmp / "concat.txt"
    concat_list.write_text(
        "\n".join(f"file '{c}'" for c in section_clips), encoding="utf-8"
    )
    body_mp4 = tmp / "body.mp4"
    ffmpeg("-f", "concat", "-safe", "0", "-i", str(concat_list),
           "-c:v", "libx264", "-c:a", "aac", "-r", raw_fps,
           str(body_mp4))

    # Intro: PIL title card + pre-generated narration, duration = narration length + 0.5s buffer
    print(f"Creating intro title card (intro_dur={intro_dur:.1f}s)...")
    intro_sec = max(4.0, intro_dur + 0.5)
    intro_png = tmp / "intro.png"
    _make_intro_frame(canvas_w, canvas_h, intro_png)
    intro_mp4 = tmp / "intro.mp4"
    pad_intro = max(0.0, intro_sec - intro_dur)
    ffmpeg(
        "-loop", "1", "-framerate", raw_fps, "-i", str(intro_png),
        "-i", str(intro_narr),
        "-filter_complex", f"[1:a]apad=pad_dur={pad_intro:.3f}[a]",
        "-map", "0:v", "-map", "[a]",
        "-t", f"{intro_sec:.3f}",
        "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p",
        "-r", raw_fps,
        str(intro_mp4),
    )

    # Outro: PIL card + narration
    print(f"Creating outro card (outro_dur={outro_dur:.1f}s)...")
    outro_sec = max(4.0, outro_dur + 1.0)
    outro_png = tmp / "outro.png"
    _make_outro_frame(canvas_w, canvas_h, outro_png)
    outro_mp4 = tmp / "outro.mp4"
    pad_outro = max(0.0, outro_sec - outro_dur)
    ffmpeg(
        "-loop", "1", "-framerate", raw_fps, "-i", str(outro_png),
        "-i", str(outro_narr),
        "-filter_complex", f"[1:a]apad=pad_dur={pad_outro:.3f}[a]",
        "-map", "0:v", "-map", "[a]",
        "-t", f"{outro_sec:.3f}",
        "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p",
        "-r", raw_fps,
        str(outro_mp4),
    )

    # Final concat: intro + body + outro
    print("Assembling final video...")
    final_list = tmp / "final_concat.txt"
    final_list.write_text(
        f"file '{intro_mp4}'\nfile '{body_mp4}'\nfile '{outro_mp4}'",
        encoding="utf-8",
    )
    ffmpeg("-f", "concat", "-safe", "0", "-i", str(final_list),
           "-c:v", "libx264", "-c:a", "aac", "-r", raw_fps,
           str(OUT_FILE))
    return OUT_FILE


def build_video_shorts(
    full_video: Path,
    tmp: Path,
    narr_files: list[Path],
    section_durations: list[float],
    intro_narr: Path,
    intro_dur: float,
    outro_narr: Path,
    outro_dur: float,
) -> Path:
    """Build a vertical 720×1280 Reels/Shorts version with blur background."""
    sw, sh = SHORTS_W, SHORTS_H
    section_clips = []

    fps_probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=r_frame_rate",
         "-of", "default=noprint_wrappers=1:nokey=1", str(full_video)],
        capture_output=True, text=True,
    )
    raw_fps = fps_probe.stdout.strip() or "30/1"
    print(f"  xLights export fps: {raw_fps}")

    start_s = 0.0
    for i, (label, subtitle, _, _, _) in enumerate(SECTIONS):
        sec_dur     = section_durations[i]
        narr_mp3    = narr_files[i]
        clip_mp4    = tmp / f"clip_{i:02d}.mp4"
        overlay_png = tmp / f"overlay_{i:02d}.png"
        muxed       = tmp / f"muxed_{i:02d}.mp4"

        print(f"  Section {i+1}: trimming video clip ({sec_dur:.1f}s)...")
        ffmpeg(
            "-ss", f"{start_s:.3f}", "-i", str(full_video),
            "-t", f"{sec_dur:.3f}", "-c:v", "libx264", "-an",
            str(clip_mp4),
        )
        start_s += sec_dur

        narr_dur = _probe_audio_duration(narr_mp3)
        pad = max(0.0, sec_dur - narr_dur)

        print(f"  Section {i+1}: compositing vertical frame...")
        _make_text_overlay(label, subtitle, sw, sh, overlay_png)

        # bg: scale+crop to exactly fill 720×1280, then blur
        # fg: fit width=720, preserve AR (height will be ~405 for 16:9 source)
        ffmpeg(
            "-i", str(clip_mp4),
            "-i", str(overlay_png),
            "-i", str(narr_mp3),
            "-filter_complex",
            f"[0:v]scale={sw}:{sh}:force_original_aspect_ratio=increase,"
            f"crop={sw}:{sh},boxblur=20:5[bg];"
            f"[0:v]scale={sw}:-2[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2[comp];"
            "[comp][1:v]overlay=0:0[vout];"
            f"[2:a]apad=pad_dur={pad:.3f}[a]",
            "-map", "[vout]", "-map", "[a]",
            "-t", f"{sec_dur:.3f}",
            "-c:v", "libx264", "-c:a", "aac",
            "-s", f"{sw}x{sh}",
            str(muxed),
        )
        section_clips.append(muxed)

    # Concatenate sections
    print("Concatenating sections...")
    concat_list = tmp / "concat.txt"
    concat_list.write_text(
        "\n".join(f"file '{c}'" for c in section_clips), encoding="utf-8"
    )
    body_mp4 = tmp / "body.mp4"
    ffmpeg("-f", "concat", "-safe", "0", "-i", str(concat_list),
           "-c:v", "libx264", "-c:a", "aac", "-r", raw_fps,
           str(body_mp4))

    # Intro card 720×1280
    print(f"Creating intro title card (intro_dur={intro_dur:.1f}s)...")
    intro_sec = max(4.0, intro_dur + 0.5)
    intro_png = tmp / "intro.png"
    _make_intro_frame(sw, sh, intro_png, backdrop_path=INTRO_BACKDROP)
    intro_mp4 = tmp / "intro.mp4"
    pad_intro = max(0.0, intro_sec - intro_dur)
    ffmpeg(
        "-loop", "1", "-framerate", raw_fps, "-i", str(intro_png),
        "-i", str(intro_narr),
        "-filter_complex", f"[1:a]apad=pad_dur={pad_intro:.3f}[a]",
        "-map", "0:v", "-map", "[a]",
        "-t", f"{intro_sec:.3f}",
        "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p",
        "-r", raw_fps, str(intro_mp4),
    )

    # Outro card 720×1280
    print(f"Creating outro card (outro_dur={outro_dur:.1f}s)...")
    outro_sec = max(4.0, outro_dur + 1.0)
    outro_png = tmp / "outro.png"
    _make_outro_frame(sw, sh, outro_png)
    outro_mp4 = tmp / "outro.mp4"
    pad_outro = max(0.0, outro_sec - outro_dur)
    ffmpeg(
        "-loop", "1", "-framerate", raw_fps, "-i", str(outro_png),
        "-i", str(outro_narr),
        "-filter_complex", f"[1:a]apad=pad_dur={pad_outro:.3f}[a]",
        "-map", "0:v", "-map", "[a]",
        "-t", f"{outro_sec:.3f}",
        "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p",
        "-r", raw_fps, str(outro_mp4),
    )

    shorts_out = OUT_FILE.parent / (OUT_FILE.stem + "_reel.mp4")
    print("Assembling final Shorts video...")
    final_list = tmp / "final_concat.txt"
    final_list.write_text(
        f"file '{intro_mp4}'\nfile '{body_mp4}'\nfile '{outro_mp4}'",
        encoding="utf-8",
    )
    ffmpeg("-f", "concat", "-safe", "0", "-i", str(final_list),
           "-c:v", "libx264", "-c:a", "aac", "-r", raw_fps,
           str(shorts_out))
    return shorts_out


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    shorts = "--reel" in sys.argv or "--shorts" in sys.argv

    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg not found on PATH")
    if shutil.which("ffprobe") is None:
        sys.exit("ffprobe not found on PATH")

    try:
        ac.call("getVersion", timeout=3.0)
    except Exception as e:
        sys.exit(
            "Cannot reach xLights automation API on port 49913.\n"
            "Please open xLights and enable xFade in Preferences > xFade, then retry.\n"
            f"Details: {e}"
        )

    min_s    = float(SHORTS_MIN_S if shorts else MIN_SECTION_S)
    narr_tail = 0.3 if shorts else 1.5

    if shorts:
        print("Reel mode: 720×1280, <60 s, short narrations")

    with tempfile.TemporaryDirectory(prefix="effect_showcase_") as tmp_str:
        tmp = Path(tmp_str)

        # Pass 1: generate all narration upfront so durations are known
        print("Pass 1: generating narration for all sections...")
        narr_files: list[Path] = []
        section_durations: list[float] = []
        for i, (label, _, narration, short_narration, _) in enumerate(SECTIONS):
            narr_mp3 = tmp / f"narr_{i:02d}.mp3"
            print(f"  [{i+1}/{len(SECTIONS)}] {label}")
            generate_narration(short_narration if shorts else narration, narr_mp3)
            dur = _probe_audio_duration(narr_mp3)
            sec_dur = max(min_s, dur + narr_tail)
            narr_files.append(narr_mp3)
            section_durations.append(sec_dur)
            print(f"          narration={dur:.1f}s  section={sec_dur:.1f}s")

        intro_narr = tmp / "intro_narr.mp3"
        print("  [intro]")
        intro_text = (
            f"xLights Bonus Gem. {TITLE_LINE3} effect showcase."
            if shorts else
            f"xLights Bonus Gem. Effect Showcase: {TITLE_LINE3}. "
            "Watch how changing each parameter transforms the animation."
        )
        generate_narration(intro_text, intro_narr)
        intro_dur = _probe_audio_duration(intro_narr)
        print(f"          narration={intro_dur:.1f}s  (intro)")

        outro_narr = tmp / "outro_narr.mp3"
        print("  [outro]")
        outro_text = (
            "Thanks for watching! Like and subscribe."
            if shorts else
            "Thanks for watching! If you found this helpful, be sure to like and subscribe "
            "for more xLights tips and tricks."
        )
        generate_narration(outro_text, outro_narr)
        outro_dur = _probe_audio_duration(outro_narr)
        print(f"          narration={outro_dur:.1f}s  (outro)")

        # Pass 2: build xLights sequence using per-section durations
        print("\nPass 2: building xLights sequence...")
        build_sequence(section_durations)

        # Pass 3: render model and export
        full_video = tmp / "preview.mp4"
        print(f"Rendering and exporting model preview for '{MODEL}' (this may take a minute)...")
        ac.export_model_with_render(MODEL, str(full_video), format="mp4highquality")

        vid_dur = _probe_audio_duration(full_video)
        expected = sum(section_durations)
        print(f"  Exported video: {vid_dur:.1f}s  (expected ~{expected:.1f}s)")
        if vid_dur < expected * 0.9:
            print(f"  WARNING: video is shorter than expected — last section may be clipped")

        # Upscale tiny model exports (LED matrices are low-res by nature).
        # Use nearest-neighbour so individual pixels stay crisp squares.
        raw_w, raw_h = _probe_dimensions(full_video)
        if max(raw_w, raw_h) < 480:
            scale = max(4, 480 // max(raw_w, raw_h))
            up_w  = raw_w * scale + (raw_w * scale) % 2
            up_h  = raw_h * scale + (raw_h * scale) % 2
            upscaled = tmp / "preview_upscaled.mp4"
            print(f"  Upscaling {raw_w}x{raw_h} -> {up_w}x{up_h} (nearest-neighbour x{scale})...")
            ffmpeg(
                "-i", str(full_video),
                "-vf", f"scale={up_w}:{up_h}:flags=neighbor",
                "-c:v", "libx264", "-an", str(upscaled),
            )
            full_video = upscaled

        # Optional: shrink the model display (MODEL_DISPLAY_SCALE < 1.0)
        if MODEL_DISPLAY_SCALE != 1.0:
            raw_w2, raw_h2 = _probe_dimensions(full_video)
            disp_w = int(raw_w2 * MODEL_DISPLAY_SCALE)
            disp_h = int(raw_h2 * MODEL_DISPLAY_SCALE)
            disp_w += disp_w % 2
            disp_h += disp_h % 2
            display_vid = tmp / "preview_display.mp4"
            print(f"  Display scale {MODEL_DISPLAY_SCALE}x: {raw_w2}x{raw_h2} -> {disp_w}x{disp_h}...")
            ffmpeg("-i", str(full_video),
                   "-vf", f"scale={disp_w}:{disp_h}:flags=neighbor",
                   "-c:v", "libx264", "-an", str(display_vid))
            full_video = display_vid

        # Pass 4: produce final video
        print("\nPass 4: producing showcase video...")
        build_fn = build_video_shorts if shorts else build_video
        out = build_fn(full_video, tmp, narr_files, section_durations, intro_narr, intro_dur, outro_narr, outro_dur)

    total = sum(section_durations) + max(4.0, intro_dur) + max(4.0, outro_dur)
    print(f"\nDone! Saved to: {out}")
    print(f"Total duration: ~{total:.0f}s")


if __name__ == "__main__":
    main()
