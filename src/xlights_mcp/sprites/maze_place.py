"""Put Maze Chase (maze_shader.py) on matrix models of an .xsq, one Shader effect per bar.

Each bar's effect is told the runner's step count at its start: one step per 16th note plus a dash
step per kick, counted over the bars the game is shown in. Placement rules are shared with the other
games (game_place.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from xlights_mcp.sprites import maze as m
from xlights_mcp.sprites.game_place import Game, place_game
from xlights_mcp.sprites.maze_shader import SHADER_NAME, build_shader, maze_settings

DEFAULT_COLOURS = ["#DC1E28", "#1EC850", "#2878FF"]      # walls cycle red, green, blue per cleared maze


@dataclass(frozen=True)
class MazeBar:
    start_step: int
    kick: int


def bar_states(kick_masks: list[int], beats_per_bar: list[int]) -> list[MazeBar]:
    out, step = [], 0
    for kick, nb in zip(kick_masks, beats_per_bar):
        out.append(MazeBar(step, kick))
        step += m.steps_in_bar(kick, nb * 4)
    return out


MAZE = Game(SHADER_NAME, build_shader, bar_states,
            lambda path, st, bar_beat, beats, energy: maze_settings(path, st.start_step, st.kick, bar_beat, beats,
                                                                    energy),
            DEFAULT_COLOURS)


@dataclass
class MazePlacement:
    model: str
    effects: int
    mazes_cleared: int
    kick_source: str
    skipped: str | None = None


def place_maze(xsq: Path, show: Path, models: list[str], colours: list[str] | None = None,
               energy: float = 1.0, track: str = "Beats", section_track: str | None = None,
               section_colours: dict[str, list[str]] | None = None, off_sections: list[str] | None = None,
               over_video: bool = False, over_pictures: bool = False, media: Path | None = None,
               start_s: float = 0.0, end_s: float | None = None) -> list[MazePlacement]:
    res = place_game(MAZE, xsq, show, models, colours, energy, track, section_track, section_colours,
                     off_sections, over_video, over_pictures, media, start_s, end_s)
    return [MazePlacement(r.model, r.effects, (r.states[-1].start_step // m.LAP) if r.states else 0,
                          r.kick_source, r.skipped) for r in res]
