"""Put Sky Shooter (shooter_shader.py) on matrix models of an .xsq, one Shader effect per bar.

The game is played out first (shooter.simulate) over the bars it is shown in, so every bar's effect starts
from the right wave and survivors, and a short sample starts with a fresh wave. Placement rules are shared
with the other games (game_place.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from xlights_mcp.sprites import shooter as g
from xlights_mcp.sprites.game_place import Game, place_game
from xlights_mcp.sprites.shooter_shader import SHADER_NAME, build_shader, shooter_settings

DEFAULT_COLOURS = ["#DC1E28", "#1EC850", "#2878FF"]      # Christmas red, green, blue ornaments

SHOOTER = Game(SHADER_NAME, build_shader, g.simulate,
               lambda path, st, bar_beat, beats, energy: shooter_settings(path, st, bar_beat, beats, energy),
               DEFAULT_COLOURS)


@dataclass
class ShooterPlacement:
    model: str
    effects: int
    waves: int
    kick_source: str
    skipped: str | None = None


def place_shooter(xsq: Path, show: Path, models: list[str], colours: list[str] | None = None,
                  energy: float = 1.0, track: str = "Beats", section_track: str | None = None,
                  section_colours: dict[str, list[str]] | None = None, off_sections: list[str] | None = None,
                  over_video: bool = False, over_pictures: bool = False, media: Path | None = None,
                  start_s: float = 0.0, end_s: float | None = None) -> list[ShooterPlacement]:
    res = place_game(SHOOTER, xsq, show, models, colours, energy, track, section_track, section_colours,
                     off_sections, over_video, over_pictures, media, start_s, end_s)
    return [ShooterPlacement(r.model, r.effects, r.states[-1].wave + 1 if r.states else 0, r.kick_source,
                             r.skipped) for r in res]
