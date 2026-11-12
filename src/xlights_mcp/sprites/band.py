"""Skeleton band: guitarist, singer and drummer, drawn 1 pixel per LED on 13x17 cells.

Each player is layers of ASCII pixel art (a body with its instrument, plus overlays
that change with the music) on top of the dancers' skull, so the band matches the
dance crew. What moves, per 16th-note slot of a bar:
  * guitarist: strums down on each beat and up on the off-beat;
  * singer: jaw opens on sung vowels (the vocal mask), the free arm rises with loudness;
  * drummer: bass drum flashes on kicks (the kick mask), left stick hits the snare on
    beats 2 and 4, right stick plays the hi-hat on 8ths, the cymbal crashes on beat 1.
Everyone's head bobs a row on the beat when the music is loud enough.
"""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from xlights_mcp.sprites import dancers as d

W, H = d.W, d.H
MEMBERS = ("guitar", "singer", "drums")
SLOTS_PER_BEAT = 4

WOOD = (200, 110, 30)
WOOD_DARK = (120, 60, 20)
METAL = (170, 170, 185)
METAL_DARK = (95, 95, 110)
CYMBAL = (220, 180, 50)
CYMBAL_FLASH = (255, 245, 170)
DRUM_HEAD = (180, 180, 195)
DRUM_FLASH = (255, 255, 235)

# '.' = nothing; B bone, J joint, S shirt, D shirt shade, W/w guitar wood, M/m metal, C cymbal, H drum head,
# H bass drum head (flashes on kicks), h snare head (flashes on snare hits), R drum shell (the drummer's shirt). Heads are drawn separately (skull, jaw, hair or band).
LAYERS = {
    "guitar_body": [
        ".............",
        ".............",
        ".............",
        ".............",
        "......B......",
        "....SDSSS....",
        ".....DSS.....",
        ".....DSS.....",
        ".....DSS.....",
        ".....BBB.....",
        ".....B.B.....",
        "....B...B....",
        "....J...J....",
        "....B...B....",
        "....B...B....",
        "...BB...BB...",
        ".............",
    ],
    "guitar": [
        ".............",
        ".............",
        ".............",
        "ww...........",
        ".w...........",
        "..w..........",
        "...w.........",
        "....w........",
        ".....wWW.....",
        "....WWWWW....",
        "....WWwWW....",
        ".....WWW.....",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
    ],
    "fret_arm": [
        ".............",
        ".............",
        ".............",
        ".............",
        "..B..........",
        "...JB........",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
    ],
    "strum_down": [
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".........B...",
        ".........J...",
        "........B....",
        ".......B.....",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
    ],
    "strum_up": [
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".........J...",
        "........B....",
        ".......B.....",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
    ],
    "singer_body": [
        ".............",
        ".............",
        ".............",
        "..........M..",
        "......B...M..",
        "....SDSSSBm..",
        ".....DSS.J...",
        ".....DSS..m..",
        ".....DSS..m..",
        ".....BBB..m..",
        ".....B.B..m..",
        "....B...B.m..",
        "....J...J.m..",
        "....B...B.m..",
        "....B...B.m..",
        "...BB...BBmm.",
        ".............",
    ],
    "free_down": [
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        "...B.........",
        "...J.........",
        "...B.........",
        "...B.........",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
    ],
    "free_out": [
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".BJB.........",
        "B............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
    ],
    "free_up": [
        ".............",
        "..B..........",
        "..B..........",
        "..B..........",
        "..J..........",
        "...B.........",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
    ],
    "drums_body": [
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        "......B......",
        "....SDSSS....",
        ".....DSS.....",
        ".....DSS.....",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
    ],
    "kit": [
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        "..........CCC",
        "...........m.",
        "...........m.",
        "...........m.",
        "MMM.RRRRR..m.",
        "hhhRHHHHHR.m.",
        "RRRRHHHHHR.m.",
        ".m.RHHHHHR.m.",
        ".m..RRRRR..m.",
        "mmm.......mmm",
        ".............",
    ],
    "snare_up": [
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        "...J.........",
        "..B..........",
        ".B...........",
        "B............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
    ],
    "snare_hit": [
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        "...J.........",
        "...B.........",
        "..B..........",
        ".B...........",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
    ],
    "hat_up": [
        ".............",
        ".............",
        ".............",
        ".............",
        ".........B...",
        ".........B...",
        ".........B...",
        ".........J...",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
    ],
    "hat_hit": [
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        "..........B..",
        ".........B...",
        ".........J...",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",
    ],
}
HEAD_Y = {"guitar": 0, "singer": 0, "drums": 2}

for _name, _rows in LAYERS.items():
    assert len(_rows) == H and all(len(r) == W for r in _rows), _name


@dataclass(frozen=True)
class SlotState:
    """What a band member does in one 16th-note slot."""
    beat: int            # beat number within the effect
    slot: int            # 16th within the bar (0..15)
    kick: bool
    vocal: bool
    loud: float          # 0..1
    bob: int             # rows the head dips (0 or 1)


def is_snare(slot: int) -> bool:
    return slot % 8 == 4            # beats 2 and 4


def is_strum_down(slot: int) -> bool:
    return slot % 4 < 2


def singer_arm(loud: float) -> str:
    return "free_down" if loud < 0.35 else ("free_out" if loud < 0.7 else "free_up")


def layers_for(member: str, s: SlotState) -> list[str]:
    """Layer names drawn for a member, back to front."""
    if member == "guitar":
        return ["guitar_body", "guitar", "fret_arm", "strum_down" if is_strum_down(s.slot) else "strum_up"]
    if member == "singer":
        return ["singer_body", singer_arm(s.loud)]
    snare = "snare_hit" if is_snare(s.slot) else "snare_up"
    hat = "hat_hit" if s.slot % 2 == 0 else "hat_up"
    return ["drums_body", "kit", snare, hat]


def _colour(ch: str, shirt, member: str, s: SlotState):
    if ch == "B":
        return d.BONE
    if ch == "J":
        return d.JOINT
    if ch in "SR":
        return shirt
    if ch == "D":
        return tuple(int(v * 0.6) for v in shirt)
    if ch == "W":
        return WOOD
    if ch == "w":
        return WOOD_DARK
    if ch == "M":
        return METAL
    if ch == "m":
        return METAL_DARK
    if ch == "C":
        return CYMBAL_FLASH if s.slot == 0 else CYMBAL
    if ch == "H":
        return DRUM_FLASH if s.kick else DRUM_HEAD
    if ch == "h":
        return DRUM_FLASH if is_snare(s.slot) else DRUM_HEAD
    raise ValueError(ch)


def draw_member(member: str, s: SlotState, shirt, female: bool = False, band: bool = False,
                hair=None) -> Image.Image:
    """One player for one slot. Layers are drawn back to front; the head (with jaw and hair) goes last."""
    img = Image.new("RGB", (W, H), d.BLACK)
    px = img.load()
    for name in layers_for(member, s):
        for y, row in enumerate(LAYERS[name]):
            for x, ch in enumerate(row):
                if ch != ".":
                    px[x, y] = _colour(ch, shirt, member, s)
    _head(px, HEAD_Y[member] + s.bob, shirt, female, band, hair, open_jaw=member == "singer" and s.vocal)
    return img


def _head(px, top: int, shirt, female: bool, band: bool, hair, open_jaw: bool) -> None:
    def put(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            px[x, y] = c

    if female:
        hair = hair or d.HAIR["blonde"]
        for y in range(1, 5):
            put(3, top + y, hair)
            put(9, top + y, hair)
    for x in range(4, 9):
        put(x, top, d.BONE)
        put(x, top + 2, d.BONE)
    for x in (4, 6, 8):
        put(x, top + 1, d.BONE)
    if open_jaw:
        put(6, top + 2, d.BLACK)                 # open mouth
        for x in (5, 7):
            put(x, top + 3, d.BONE)
        for x in range(5, 8):
            put(x, top + 4, d.BONE)               # dropped jaw
    else:
        for x in range(5, 8):
            put(x, top + 3, d.BONE)
    if female:
        for x in range(4, 9):
            put(x, top, hair)
        put(9, top, shirt)
        put(10, top, shirt)
    elif band:
        for x in range(4, 9):
            put(x, top, shirt)


def band_frame(s: SlotState, shirts: list[str] | None = None, figure: str = "male", scale: int = 1) -> Image.Image:
    """Guitarist, singer and drummer side by side for one slot. Outfits, hair and headbands follow the dance
    crew's rules (crew_from_style), so the band and the dancers dress alike."""
    looks = d.crew_from_style(3, "unison", (shirts or ["purple", "red", "teal"]), figure)
    img = Image.new("RGB", (3 * W, H), d.BLACK)
    for i, (member, dn) in enumerate(zip(MEMBERS, looks)):
        shirt, band = dn.colours()
        img.paste(draw_member(member, s, shirt, dn.figure == "female", band is not None, d.HAIR[dn.hair]), (i * W, 0))
    if scale > 1:
        img = img.resize((3 * W * scale, H * scale), Image.NEAREST)
    return img
