"""Color palette management for xLights sequences."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ColorPalette(BaseModel):
    """An xLights color palette for effects."""

    colors: list[str] = Field(default_factory=list)  # hex colors like "#FF0000"
    active_colors: list[int] = Field(default_factory=list)  # which palette slots are active
    sparkle_frequency: int = 0
    sparkle_color: str = ""
    # Style tags used by suggest_palette() to match a palette to a song's feel.
    energy: str = "medium"  # "soft" | "medium" | "bold"
    warmth: str = "neutral"  # "warm" | "cool" | "neutral"

    def to_xlights_string(self) -> str:
        """Serialize to the xLights palette format string."""
        parts = []
        # Palette button colors (up to 8 slots)
        defaults = ["#FFFFFF", "#FF0000", "#00FF00", "#0000FF",
                     "#FFFF00", "#000000", "#00FFFF", "#FF00FF"]
        for i in range(8):
            color = self.colors[i] if i < len(self.colors) else defaults[i]
            parts.append(f"C_BUTTON_Palette{i + 1}={color}")

        # Active color checkboxes
        for idx in self.active_colors:
            parts.append(f"C_CHECKBOX_Palette{idx}=1")

        # Sparkle
        if self.sparkle_frequency > 0:
            parts.append(f"C_SLIDER_SparkleFrequency={self.sparkle_frequency}")
        if self.sparkle_color:
            parts.append(f"C_COLOURPICKERCTRL_SparklesColour={self.sparkle_color}")

        return ",".join(parts)


# Pre-defined theme palettes
CHRISTMAS_PALETTES = {
    "classic": ColorPalette(
        colors=["#FF0000", "#00FF00", "#FFFFFF"],
        active_colors=[1, 2, 3],
        energy="bold", warmth="warm",
    ),
    "warm": ColorPalette(
        colors=["#FF0000", "#FEB800", "#FFD700", "#FFFFFF"],
        active_colors=[1, 2, 3, 4],
        energy="medium", warmth="warm",
    ),
    "cool": ColorPalette(
        colors=["#0000FF", "#00FFFF", "#FFFFFF", "#C0C0FF"],
        active_colors=[1, 2, 3, 4],
        energy="medium", warmth="cool",
    ),
    "candy_cane": ColorPalette(
        colors=["#FF0000", "#FFFFFF"],
        active_colors=[1, 2],
        energy="bold", warmth="warm",
    ),
    "gold_silver": ColorPalette(
        colors=["#FFD700", "#C0C0C0", "#FFFFFF"],
        active_colors=[1, 2, 3],
        energy="soft", warmth="neutral",
    ),
    "icy": ColorPalette(
        colors=["#FFFFFF", "#87CEEB", "#00BFFF", "#ADD8E6"],
        active_colors=[1, 2, 3, 4],
        energy="soft", warmth="cool",
    ),
    "traditional": ColorPalette(
        colors=["#FF0000", "#00FF00", "#FFD700", "#FFFFFF"],
        active_colors=[1, 2, 3, 4],
        energy="medium", warmth="warm",
    ),
}

HALLOWEEN_PALETTES = {
    "classic": ColorPalette(
        colors=["#FF6600", "#800080", "#00FF00", "#000000"],
        active_colors=[1, 2, 3],
        energy="medium", warmth="warm",
    ),
    "spooky": ColorPalette(
        colors=["#800080", "#00FF00", "#FF0000", "#000000"],
        active_colors=[1, 2, 3],
        energy="bold", warmth="cool",
    ),
    "fire": ColorPalette(
        colors=["#FF0000", "#FF6600", "#FFD700", "#FFFFFF"],
        active_colors=[1, 2, 3],
        energy="bold", warmth="warm",
    ),
    "ghostly": ColorPalette(
        colors=["#FFFFFF", "#E0E0FF", "#C0C0FF", "#8080FF"],
        active_colors=[1, 2, 3, 4],
        energy="soft", warmth="cool",
    ),
}

GENERIC_PALETTES = {
    "rainbow": ColorPalette(
        colors=["#FF0000", "#FF8000", "#FFFF00", "#00FF00", "#0000FF", "#8000FF"],
        active_colors=[1, 2, 3, 4, 5, 6],
        energy="bold", warmth="neutral",
    ),
    "white": ColorPalette(
        colors=["#FFFFFF"],
        active_colors=[1],
        energy="soft", warmth="neutral",
    ),
    "warm_white": ColorPalette(
        colors=["#FFF5E6", "#FFE0B2", "#FFCC80"],
        active_colors=[1, 2, 3],
        energy="soft", warmth="warm",
    ),
}


def get_theme_palettes(theme: str | None) -> dict[str, ColorPalette]:
    """Get palettes appropriate for a theme."""
    if theme and "halloween" in theme.lower():
        return {**HALLOWEEN_PALETTES, **GENERIC_PALETTES}
    elif theme and "christmas" in theme.lower():
        return {**CHRISTMAS_PALETTES, **GENERIC_PALETTES}
    return {**CHRISTMAS_PALETTES, **GENERIC_PALETTES}


def infer_theme_from_title(title: str) -> str | None:
    """Guess a theme keyword from a song/file title, for when none is given."""
    lowered = title.lower()
    if any(kw in lowered for kw in ("halloween", "spooky", "haunt", "monster")):
        return "halloween"
    if any(kw in lowered for kw in ("christmas", "xmas", "holiday", "santa", "jingle")):
        return "christmas"
    return None


def classify_song_energy(
    tempo: float | None = None,
    average_loudness: float | None = None,
    dynamic_range: float | None = None,
    bass_peak_ratio: float | None = None,
) -> str:
    """Bucket a song's overall feel into "soft", "medium", or "bold".

    Fast tempo, loud/bass-heavy, low dynamic range (a "wall of sound") reads as
    bold/energetic. Slow tempo, quiet, wide dynamic range reads as soft/ballad-like.
    Any missing input is simply skipped rather than defaulted, so partial data
    still produces a reasonable classification.
    """
    score = 0
    votes = 0

    if tempo is not None:
        votes += 1
        if tempo >= 120:
            score += 1
        elif tempo <= 85:
            score -= 1

    if average_loudness is not None:
        votes += 1
        if average_loudness >= 0.22:
            score += 1
        elif average_loudness <= 0.12:
            score -= 1

    if bass_peak_ratio is not None:
        votes += 1
        if bass_peak_ratio >= 0.55:
            score += 1
        elif bass_peak_ratio <= 0.35:
            score -= 1

    if dynamic_range is not None:
        votes += 1
        if dynamic_range <= 1.5:
            score += 1
        elif dynamic_range >= 3.0:
            score -= 1

    if votes == 0 or score == 0:
        return "medium"
    return "bold" if score > 0 else "soft"


_ENERGY_ORDER = ["soft", "medium", "bold"]


def suggest_palette(
    title: str = "",
    theme: str | None = None,
    tempo: float | None = None,
    average_loudness: float | None = None,
    dynamic_range: float | None = None,
    bass_peak_ratio: float | None = None,
    top_n: int = 3,
) -> dict:
    """Recommend a color palette for a song based on title keywords and audio feel.

    Combines a theme guess (from `theme` or the song title) with an energy
    classification derived from tempo/loudness/bass dominance/dynamic range,
    then ranks the theme's palette pool by how closely each palette's tags
    match the song.
    """
    resolved_theme = theme or infer_theme_from_title(title)
    pool = get_theme_palettes(resolved_theme)
    song_energy = classify_song_energy(tempo, average_loudness, dynamic_range, bass_peak_ratio)
    energy_idx = _ENERGY_ORDER.index(song_energy)

    scored: list[tuple[int, str, ColorPalette]] = []
    for name, palette in pool.items():
        distance = abs(_ENERGY_ORDER.index(palette.energy) - energy_idx)
        score = 2 - distance  # 2=exact match, 1=adjacent, 0=opposite
        scored.append((score, name, palette))

    scored.sort(key=lambda t: t[0], reverse=True)
    ranked = scored[:top_n]
    best_score, best_name, best_palette = ranked[0]

    reasoning = (
        f"Detected theme '{resolved_theme or 'generic'}' "
        f"and classified the song as '{song_energy}' energy "
        f"(tempo={tempo}, avg_loudness={average_loudness}, "
        f"dynamic_range={dynamic_range}, bass_peak_ratio={bass_peak_ratio}). "
        f"'{best_name}' is tagged energy='{best_palette.energy}', "
        f"warmth='{best_palette.warmth}', the closest match in the "
        f"{resolved_theme or 'generic'} palette pool."
    )

    return {
        "theme": resolved_theme,
        "song_energy": song_energy,
        "recommended": {
            "name": best_name,
            "colors": best_palette.colors,
            "energy": best_palette.energy,
            "warmth": best_palette.warmth,
        },
        "alternatives": [
            {
                "name": name,
                "colors": palette.colors,
                "energy": palette.energy,
                "warmth": palette.warmth,
                "match_score": score,
            }
            for score, name, palette in ranked[1:]
        ],
        "reasoning": reasoning,
    }
