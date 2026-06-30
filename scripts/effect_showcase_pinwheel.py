"""Narrated showcase video for the xLights Pinwheel effect.

Overrides the configuration in effect_showcase.py and delegates all
rendering/narration/video work to that engine.

Usage:
    python scripts/effect_showcase_pinwheel.py
    python scripts/effect_showcase_pinwheel.py --shorts

Produces: effect_showcase_Pinwheel.mp4  (or _shorts.mp4)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import effect_showcase as engine

# ── Override configuration ─────────────────────────────────────────────────────

engine.EFFECT      = "Pinwheel"
engine.MODEL       = "TV-Right"
engine.TITLE_LINE1 = "xLights Bonus Gem"
engine.TITLE_LINE2 = "Effect Showcase"
engine.TITLE_LINE3 = "Pinwheel"
engine.OUTRO_LINE1 = "Thanks For"
engine.OUTRO_LINE2 = "Watching!"
engine.OUTRO_LINE3 = "Like & Subscribe"
engine.OUT_FILE    = Path(__file__).parent.parent / "effect_showcase_Pinwheel.mp4"

engine.PALETTE = (
    "C_BUTTON_Palette1=#FF0099,C_CHECKBOX_Palette1=1,"
    "C_BUTTON_Palette2=#00CCFF,C_CHECKBOX_Palette2=1,"
    "C_BUTTON_Palette3=#FF6600,C_CHECKBOX_Palette3=1,"
    "C_BUTTON_Palette4=#00FF88,C_CHECKBOX_Palette4=1,"
    "C_BUTTON_Palette5=#FFFF00,C_CHECKBOX_Palette5=1,"
    "C_BUTTON_Palette6=#CC00FF,C_CHECKBOX_Palette6=1"
)

engine.SECTIONS = [
    (
        "Default Settings",
        "Arms: 3 | Thickness: 50% | Speed: 10",
        "The Pinwheel effect creates a spinning arms pattern across your display. "
        "Here are the defaults: three arms at fifty percent thickness with a medium spin speed.",
        "Default settings. Three arms at fifty percent thickness.",
        {
            "E_SLIDER_Pinwheel_Arms":      3,
            "E_SLIDER_Pinwheel_ArmSize":   100,
            "E_SLIDER_Pinwheel_Thickness": 50,
            "E_SLIDER_Pinwheel_Speed":     10,
            "E_SLIDER_Pinwheel_Twist":     0,
        },
    ),
    (
        "Star Burst",
        "Arms: 10 | Thickness: 20% | Speed: 10",
        "Raising the arm count to ten with thin blades produces a starburst that radiates "
        "evenly across the panel like a spinning compass rose.",
        "Star burst. Ten thin arms radiate evenly outward.",
        {
            "E_SLIDER_Pinwheel_Arms":      10,
            "E_SLIDER_Pinwheel_ArmSize":   100,
            "E_SLIDER_Pinwheel_Thickness": 20,
            "E_SLIDER_Pinwheel_Speed":     10,
            "E_SLIDER_Pinwheel_Twist":     0,
        },
    ),
    (
        "Thick Blades",
        "Arms: 3 | Thickness: 85% | Speed: 10",
        "Wide, chunky blades fill most of the display, making the gaps between arms "
        "just narrow slices of contrast.",
        "Thick blades. Wide arms fill most of the display.",
        {
            "E_SLIDER_Pinwheel_Arms":      3,
            "E_SLIDER_Pinwheel_ArmSize":   100,
            "E_SLIDER_Pinwheel_Thickness": 85,
            "E_SLIDER_Pinwheel_Speed":     10,
            "E_SLIDER_Pinwheel_Twist":     0,
        },
    ),
    (
        "Fast Spin",
        "Arms: 3 | Thickness: 50% | Speed: 40",
        "Cranking the speed to forty creates a rapid strobe-like rotation that gives "
        "the display an energetic, pulsing appearance.",
        "Fast spin. Rapid rotation at speed forty.",
        {
            "E_SLIDER_Pinwheel_Arms":      3,
            "E_SLIDER_Pinwheel_ArmSize":   100,
            "E_SLIDER_Pinwheel_Thickness": 50,
            "E_SLIDER_Pinwheel_Speed":     40,
            "E_SLIDER_Pinwheel_Twist":     0,
        },
    ),
    (
        "Spiral Twist",
        "Arms: 4 | Twist: 180° | Thickness: 50% | Speed: 10",
        "Adding a one-eighty degree twist curves each arm into a smooth spiral, "
        "transforming the straight blades into graceful arcs that flow from center to edge.",
        "Spiral twist. One-eighty degrees curves arms into flowing spirals.",
        {
            "E_SLIDER_Pinwheel_Arms":      4,
            "E_SLIDER_Pinwheel_ArmSize":   100,
            "E_SLIDER_Pinwheel_Thickness": 50,
            "E_SLIDER_Pinwheel_Speed":     10,
            "E_SLIDER_Pinwheel_Twist":     180,
        },
    ),
    (
        "Dense Fan",
        "Arms: 14 | Thickness: 65% | Speed: 8",
        "Fourteen thick arms leave very little dark space, turning the display into "
        "a dense color wheel that rotates like a solid fan.",
        "Dense fan. Fourteen thick arms, almost no dark space.",
        {
            "E_SLIDER_Pinwheel_Arms":      14,
            "E_SLIDER_Pinwheel_ArmSize":   100,
            "E_SLIDER_Pinwheel_Thickness": 65,
            "E_SLIDER_Pinwheel_Speed":     8,
            "E_SLIDER_Pinwheel_Twist":     0,
        },
    ),
    (
        "Grand Finale",
        "Arms: 6 | Twist: 90° | Thickness: 70% | Speed: 30",
        "The finale combines six wide arms with a ninety degree twist and high speed, "
        "creating a dazzling spiral storm that floods every pixel with rapid color.",
        "Grand finale. Six twisted arms spinning at high speed.",
        {
            "E_SLIDER_Pinwheel_Arms":      6,
            "E_SLIDER_Pinwheel_ArmSize":   100,
            "E_SLIDER_Pinwheel_Thickness": 70,
            "E_SLIDER_Pinwheel_Speed":     30,
            "E_SLIDER_Pinwheel_Twist":     90,
        },
    ),
]

# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    engine.main()
