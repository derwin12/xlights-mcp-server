"""Narrated showcase video for the xLights Snowflakes effect.

Usage:
    python scripts/effect_showcase_snowflakes.py
    python scripts/effect_showcase_snowflakes.py --reel

Produces: effect_showcase_Snowflakes.mp4  (or _reel.mp4)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import effect_showcase as engine

# ── Override configuration ─────────────────────────────────────────────────────

engine.EFFECT      = "Snowflakes"
engine.MODEL               = "TV"
engine.TITLE_LINE1 = "xLights Bonus Gem"
engine.TITLE_LINE2 = "Effect Showcase"
engine.TITLE_LINE3 = "Snowflakes"
engine.OUTRO_LINE1 = "Thanks For"
engine.OUTRO_LINE2 = "Watching!"
engine.OUTRO_LINE3 = "Like & Subscribe"
engine.OUT_FILE    = Path(__file__).parent.parent / "effect_showcase_Snowflakes.mp4"

# Icy whites and blues — classic snow tones
engine.PALETTE = (
    "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1,"
    "C_BUTTON_Palette2=#CCE5FF,C_CHECKBOX_Palette2=1,"
    "C_BUTTON_Palette3=#99CCFF,C_CHECKBOX_Palette3=1,"
    "C_BUTTON_Palette4=#E8F4FD,C_CHECKBOX_Palette4=1,"
    "C_BUTTON_Palette5=#B8D4E8,C_CHECKBOX_Palette5=1,"
    "C_BUTTON_Palette6=#DDEEFF,C_CHECKBOX_Palette6=1"
)

# Correct parameter IDs (from resources/effectmetadata/Snowflakes.json):
#   Snowflakes_Count        — Max flakes  (1–100,  default 5)
#   Snowflakes_Type         — Type        (0–9,    default 1; 0=random mix)
#   Snowflakes_Speed        — Speed       (0–50,   default 10)
#   Falling                 — Falling     ("Driving" | "Falling" | "Falling & Accumulating")
#   Snowflakes_WarmupFrames — Warm up     (0–100,  default 0)

engine.SECTIONS = [
    (
        "Default Settings",
        "Flakes: 20 | Type: 5 | Speed: 10 | Falling",
        "The Snowflakes effect creates falling flake animations across your display. "
        "Type five produces a classic six-pointed snowflake shape with twenty flakes at a time.",
        "Default settings. Type five snowflakes falling gently.",
        {
            "E_SLIDER_Snowflakes_Count":        20,
            "E_SLIDER_Snowflakes_Type":          5,
            "E_SLIDER_Snowflakes_Speed":         10,
            "E_CHOICE_Falling":                  "Falling",
            "E_SLIDER_Snowflakes_WarmupFrames":  20,
        },
    ),
    (
        "Type 4 Flakes",
        "Flakes: 20 | Type: 4 | Speed: 10 | Falling",
        "Type four uses a cross-shaped snowflake with extended arms, "
        "giving each flake a more open, crystalline appearance as it falls.",
        "Type four. Cross-shaped flakes with extended arms.",
        {
            "E_SLIDER_Snowflakes_Count":        20,
            "E_SLIDER_Snowflakes_Type":          4,
            "E_SLIDER_Snowflakes_Speed":         10,
            "E_CHOICE_Falling":                  "Falling",
            "E_SLIDER_Snowflakes_WarmupFrames":  20,
        },
    ),
    (
        "Type 7 Flakes",
        "Flakes: 20 | Type: 7 | Speed: 10 | Falling",
        "Type seven creates a larger, more detailed snowflake with branching tips — "
        "the most realistic-looking shape in the set.",
        "Type seven. Larger flakes with branching tips.",
        {
            "E_SLIDER_Snowflakes_Count":        20,
            "E_SLIDER_Snowflakes_Type":          7,
            "E_SLIDER_Snowflakes_Speed":         10,
            "E_CHOICE_Falling":                  "Falling",
            "E_SLIDER_Snowflakes_WarmupFrames":  20,
        },
    ),
    (
        "Type 8 Flakes",
        "Flakes: 20 | Type: 8 | Speed: 10 | Falling",
        "Type eight produces a dense, solid snowflake shape that reads clearly "
        "even on lower-resolution displays.",
        "Type eight. Dense solid snowflakes that read clearly.",
        {
            "E_SLIDER_Snowflakes_Count":        20,
            "E_SLIDER_Snowflakes_Type":          8,
            "E_SLIDER_Snowflakes_Speed":         10,
            "E_CHOICE_Falling":                  "Falling",
            "E_SLIDER_Snowflakes_WarmupFrames":  20,
        },
    ),
    (
        "Heavy Blizzard",
        "Flakes: 60 | Type: 5 | Speed: 35 | Falling",
        "Cranking flakes to sixty and speed to thirty-five creates a heavy blizzard "
        "that fills the display with rapidly falling snowflakes.",
        "Heavy blizzard. Sixty flakes at high speed.",
        {
            "E_SLIDER_Snowflakes_Count":        60,
            "E_SLIDER_Snowflakes_Type":          5,
            "E_SLIDER_Snowflakes_Speed":         35,
            "E_CHOICE_Falling":                  "Falling",
            "E_SLIDER_Snowflakes_WarmupFrames":  20,
        },
    ),
    (
        "Accumulating",
        "Flakes: 25 | Type: 5 | Speed: 8 | Falling & Accumulating",
        "Falling and accumulating mode lets snowflakes pile up at the bottom of the display, "
        "building a snowdrift that grows throughout the section.",
        "Accumulating. Flakes pile up at the bottom of the display.",
        {
            "E_SLIDER_Snowflakes_Count": 25,
            "E_SLIDER_Snowflakes_Type":  5,
            "E_SLIDER_Snowflakes_Speed": 8,
            "E_CHOICE_Falling":          "Falling & Accumulating",
        },
    ),
    (
        "Grand Finale",
        "Flakes: 80 | Type: 7 | Speed: 30 | Falling",
        "The finale pushes eighty of the detailed type-seven flakes at high speed "
        "for a stunning whiteout blizzard that saturates every pixel.",
        "Grand finale. Eighty detailed flakes in a whiteout blizzard.",
        {
            "E_SLIDER_Snowflakes_Count":        80,
            "E_SLIDER_Snowflakes_Type":          7,
            "E_SLIDER_Snowflakes_Speed":         30,
            "E_CHOICE_Falling":                  "Falling",
            "E_SLIDER_Snowflakes_WarmupFrames":  20,
        },
    ),
]

# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    engine.main()
