"""Maze Chase: an original Christmas maze game that plays along with the song.

A gingerbread runner works through a candy-cane maze (9x4 cells, 1-pixel walls,
3x3-pixel corridors) eating a peppermint in every cell, with two snowmen in
coloured scarves on his heels. He moves one cell per 16th note and dashes an
extra cell on each kick (with a sparkle). When every cell has been visited the
peppermints come back and the walls change colour.

The maze is a fixed perfect maze (generated once from a seed) and the runner
follows its depth-first tour (an Euler tour of the spanning tree), so where
everyone is depends only on how many steps the runner has taken. The placer
passes the step count at each bar's start; the bar's kick slots add the dashes.
Positions move one pixel per quarter-16th step, the same in Python and GLSL.
"""

from __future__ import annotations

import math
import random

from PIL import Image

PW, PH = 40, 20
CW, CH = 9, 4                    # cells
OX, OY = 1, 1                    # maze top-left pixel (walls start here)
SEED = 2026
CHASE_GAPS = (5, 9)              # snowmen this many steps behind the runner
SLOTS = 16

BLACK = (0, 0, 0)
WHITE = (245, 245, 255)
GINGER = (190, 105, 45)
ICING = (255, 245, 230)
SNOWMAN = (235, 240, 255)
HAT = (70, 70, 85)
MINT_RED = (230, 30, 40)
SPARK = (255, 230, 120)

RUNNER = ["IGI", "GIG", "G.G"]   # I icing, G gingerbread
SNOWMEN = ["HHH", ".W.", "SWS"]  # H hat, W snow, S scarf (palette colour)


def _maze() -> tuple[set[tuple[int, int]], list[int]]:
    """Passages (pairs of cell ids, smaller first) of a perfect maze, and the runner's tour of it."""
    rng = random.Random(SEED)
    seen, stack, passages, tour = {0}, [0], set(), [0]
    while stack:
        c = stack[-1]
        x, y = c % CW, c // CW
        nbrs = [n for n, ok in ((c - 1, x > 0), (c + 1, x < CW - 1), (c - CW, y > 0), (c + CW, y < CH - 1))
                if ok and n not in seen]
        if nbrs:
            n = rng.choice(nbrs)
            seen.add(n)
            passages.add((min(c, n), max(c, n)))
            stack.append(n)
            tour.append(n)
        else:
            stack.pop()
            if stack:
                tour.append(stack[-1])
    return passages, tour[:-1]          # the tour ends back at cell 0; drop the repeat so it loops


PASSAGES, TOUR = _maze()
LAP = len(TOUR)
FIRST_VISIT = {c: TOUR.index(c) for c in range(CW * CH)}


def wall_mask() -> list[list[bool]]:
    """True where a wall pixel is, over the 40x20 playfield."""
    m = [[False] * PW for _ in range(PH)]
    w, h = CW * 4 + 1, CH * 4 + 1
    for y in range(h):
        for x in range(w):
            on_v, on_h = x % 4 == 0, y % 4 == 0
            if not (on_v or on_h):
                continue
            wall = True
            if on_v and not on_h and 0 < x < w - 1:          # between cells left/right
                a = (y // 4) * CW + x // 4 - 1
                wall = (a, a + 1) not in PASSAGES
            elif on_h and not on_v and 0 < y < h - 1:        # between cells up/down
                a = (y // 4 - 1) * CW + x // 4
                wall = (a, a + CW) not in PASSAGES
            m[OY + y][OX + x] = wall
    return m


WALLS = wall_mask()


def cell_xy(c: int) -> tuple[int, int]:
    """Top-left pixel of a cell's 3x3 interior."""
    return OX + 1 + (c % CW) * 4, OY + 1 + (c // CW) * 4


def steps_in_bar(kick: int, slot: int) -> int:
    """Steps taken from the bar's start up to the start of this slot: one per slot plus one per kick."""
    return slot + sum(1 for s in range(min(slot, SLOTS)) if kick >> s & 1)


def pos_at(step_q: int) -> tuple[int, int]:
    """Pixel position (top-left of a 3x3 sprite) at a step count measured in quarter steps."""
    k, sub = divmod(step_q, 4)
    a, b = TOUR[k % LAP], TOUR[(k + 1) % LAP]
    (ax, ay), (bx, by) = cell_xy(a), cell_xy(b)
    return ax + (bx - ax) * sub // 4, ay + (by - ay) * sub // 4


def runner_q(start_step: int, kick: int, q_in_bar: int) -> int:
    """The runner's position in quarter steps: a dash slot covers two cells in the slot's time."""
    slot, sub = divmod(q_in_bar, 4)
    base = (start_step + steps_in_bar(kick, slot)) * 4
    if slot < SLOTS and kick >> slot & 1:
        return base + sub * 2
    return base + sub


def render(start_step: int, kick: int, beat_in_bar: float, colours: list[tuple[int, int, int]],
           loud: float = 0.0, scale: int = 1) -> Image.Image:
    img = Image.new("RGB", (PW, PH), BLACK)
    px = img.load()

    def put(x, y, c):
        if 0 <= x < PW and 0 <= y < PH:
            px[x, y] = c

    q = int(beat_in_bar * 16)
    slot = q // 4
    f = beat_in_bar - int(beat_in_bar)
    dip = min(1, int(math.floor(loud * 1.5 * math.sin(3.14159 * f) + 0.5)))
    rq = runner_q(start_step, kick, q)
    lap, in_lap = divmod(rq // 4, LAP)
    wall_col = colours[lap % len(colours)]

    for y in range(PH):
        for x in range(PW):
            if WALLS[y][x]:
                put(x, y, wall_col if (x + y) % 2 == 0 else WHITE)
    for c in range(CW * CH):
        if FIRST_VISIT[c] > in_lap:
            x, y = cell_xy(c)
            put(x + 1, y + 1, MINT_RED if c % 2 == 0 else WHITE)
    for i, gap in enumerate(CHASE_GAPS):
        sq = rq - gap * 4
        if sq < 0:
            continue
        x, y = pos_at(sq)
        scarf = colours[(i + 1) % len(colours)]
        for yy, row in enumerate(SNOWMEN):
            for xx, ch in enumerate(row):
                if ch != ".":
                    put(x + xx, y + yy - dip, {"H": HAT, "W": SNOWMAN, "S": scarf}[ch])
    x, y = pos_at(rq)
    for yy, row in enumerate(RUNNER):
        for xx, ch in enumerate(row):
            if ch != ".":
                put(x + xx, y + yy, {"G": GINGER, "I": ICING}[ch])
    if slot < SLOTS and kick >> slot & 1:                     # dash sparkle
        for dx, dy in ((-1, 1), (3, 1), (1, -1), (1, 3)):
            put(x + dx, y + dy, SPARK)
    if scale > 1:
        img = img.resize((PW * scale, PH * scale), Image.NEAREST)
    return img
