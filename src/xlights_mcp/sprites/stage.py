"""Stage dressing drawn around the crew at the matrix's full size.

The crew stands on a floor line at the bottom, centred. Two lamps in the top corners
throw dim beams onto the crew and swap colours on every beat (the colours come from
the dancers' clothes, so they follow the section colours). A few sparkles twinkle in
the empty space each frame. Beams are dim but stay above xLights' Transparent Black
level, so they show; the dancers are drawn over them.
"""

from __future__ import annotations

from PIL import Image

from xlights_mcp.sprites import dancers as d

FLOOR = (90, 50, 140)
FLOOR_SHINE = (220, 180, 255)
BEAM_LEVEL = 0.3
CYCLE = 16
SPARKLES = ((255, 255, 255), (255, 240, 170), (200, 230, 255))


def hash32(n: int) -> int:
    """Integer hash shared with the shader (same steps on uint32), so GIF and shader sparkles match."""
    n &= 0xFFFFFFFF
    n = ((n ^ 61) ^ (n >> 16)) & 0xFFFFFFFF
    n = (n * 9) & 0xFFFFFFFF
    n ^= n >> 4
    n = (n * 0x27D4EB2D) & 0xFFFFFFFF
    n ^= n >> 15
    return n


def sparkle_count(w: int, h: int) -> int:
    return max(2, w * h // 160)


def light_colours(crew: d.Crew) -> list[tuple[int, int, int]]:
    seen = []
    for dn in crew.dancers:
        c = dn.colours()[0]
        if c not in seen:
            seen.append(c)
    return seen or [d.SHIRTS["purple"], d.SHIRTS["teal"]]


def stage_frame(crew_img: Image.Image, size: tuple[int, int], scale: int, colours: list, beat: int,
                sub: int = 0) -> Image.Image:
    """The crew image on a stage the size of the matrix, for one beat (sub = frame within the beat)."""
    w, h = size
    cw, ch = crew_img.size
    x0, y0 = (w - cw) // 2, h - ch
    img = Image.new("RGB", (w, h), d.BLACK)
    px = img.load()
    floor_y = h - scale                       # the crew's empty bottom row (row 16) is the floor

    n = len(colours)
    lamps = ((0, colours[beat % n], x0 + cw * 0.3), (w - 1, colours[(beat + 1) % n], x0 + cw * 0.7))
    lamp_w = max(1, scale)
    for lx, col, target in lamps:
        beam = tuple(max(int(v * BEAM_LEVEL), 12) for v in col)
        for y in range(lamp_w, floor_y):
            t = y / max(floor_y, 1)
            cx = lx + (target - lx) * t
            half = 0.5 + t * cw * 0.12
            for x in range(int(cx - half), int(cx + half) + 1):
                if 0 <= x < w:
                    px[x, y] = beam
        for y in range(lamp_w):
            for x in range(lamp_w * 2):
                px[lx + x if lx == 0 else lx - x, y] = col

    for y in range(floor_y, h):
        for x in range(max(0, x0 - scale), min(w, x0 + cw + scale)):
            px[x, y] = FLOOR
    run = max(2, scale * 2)
    cycle = beat % CYCLE                      # repeat every 4 bars so identical bars share a GIF
    pos = (cycle * 2 + sub) * run % max(cw, 1)
    for x in range(x0 + pos, min(x0 + pos + run, w)):
        for y in range(floor_y, h):
            px[x, y] = FLOOR_SHINE

    seed = cycle * 31 + sub * 7 + w * 1000 + h
    for s in range(sparkle_count(w, h)):
        v = hash32(seed * 64 + s)
        px[v % w, (v >> 16) % max(1, floor_y)] = SPARKLES[(v >> 8) % len(SPARKLES)]

    mask = crew_img.convert("L").point(lambda v: 255 if v else 0)
    img.paste(crew_img, (x0, y0), mask)
    return img
