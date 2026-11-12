"""Sky Shooter: an original Christmas formation shooter that plays along with the song.

A sleigh cannon at the bottom of a 40x20 playfield shoots at a formation of 12
ornaments that sways one step per beat. Every kick knocks one out with a sparkle
burst; on beats without a kill a shot flies off the top. When a wave is cleared
the next one (baubles, snowflakes, presents in turn) flies in at the next bar.
Snow falls behind it all, and the formation dips on loud beats.

A shader has no memory, so the game is played out bar by bar in Python
(simulate) and each bar's effect is told its starting state: which enemies are
alive, which wave, whether the wave is flying in, the kick slots, and the song
beat at its start. Everything inside the bar (kills, shots, the sleigh following
its next target, explosions, sway, snow) is then worked out from that state by
the same rules here and in the generated shader. Times are quantized to quarter
16th-note steps so both sides agree pixel for pixel.
"""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

PW, PH = 40, 20                      # playfield in game pixels
COLS, ROWS = 6, 2
N_ENEMIES = COLS * ROWS
ALL_ALIVE = (1 << N_ENEMIES) - 1
KILL_ORDER = [5, 0, 11, 3, 8, 1, 10, 6, 2, 9, 4, 7]
WAVE_KINDS = ("bauble", "snowflake", "present")
SLOTS = 16
PLAYER_Y = 16
GUN_Y = 15                           # bullets start here
SWAY = [0, 1, 2, 1, 0, -1, -2, -1]   # formation x offset by beat
SNOW_FLAKES = 14

BLACK = (0, 0, 0)
GOLD = (255, 200, 40)
RED = (220, 20, 30)
WHITE = (245, 245, 255)
BULLET = (255, 230, 120)
SNOW = (90, 95, 120)
SPARK_W = (255, 255, 255)
SPARK_Y = (255, 210, 60)

PLAYER = [
    "...Y...",
    ".RRWRR.",
    "RRRRRRR",
    ".Y...Y.",
]
ENEMY = {
    "bauble": (
        ["..Y..", ".CCC.", "CWCCC", "CCCCC", ".CCC."],
        ["..Y..", ".CCC.", "CCCWC", "CCCCC", ".CCC."],
    ),
    "snowflake": (
        ["..C..", ".CCC.", "CCWCC", ".CCC.", "..C.."],
        ["C...C", ".C.C.", "..W..", ".C.C.", "C...C"],
    ),
    "present": (
        [".Y.Y.", "CCYCC", "CCYCC", "YYYYY", "CCYCC"],
        ["..Y..", "CCYCC", "CCYCC", "YYYYY", "CCYCC"],
    ),
}
SPARK = (
    ["..W..", ".WYW.", "WY.YW", ".WYW.", "..W.."],
    ["W...W", "..Y..", ".Y.Y.", "..Y..", "W...W"],
)


@dataclass(frozen=True)
class BarState:
    kick: int            # 16-bit mask of kick slots
    alive: int           # enemies alive at the bar's start (12 bits)
    wave: int            # wave number (0, 1, 2 ...): kind = WAVE_KINDS[wave % 3]
    entry: bool          # the wave flies in during the bar's first beat
    song_beat: int       # beats since the song's first bar, at this bar's start


def kills(kick: int, alive: int, entry: bool) -> list[tuple[int, int]]:
    """(slot, enemy) for each kick that knocks an enemy out. While a wave flies in (first beat) nothing dies."""
    targets = [e for e in KILL_ORDER if alive >> e & 1]
    slots = [s for s in range(SLOTS) if kick >> s & 1 and not (entry and s < 4)]
    return list(zip(slots, targets))


def simulate(kick_masks: list[int], beats_per_bar: list[int]) -> list[BarState]:
    """Play the song out bar by bar: each bar's kills come off the alive set; an empty formation brings the next
    wave in at the following bar."""
    out, alive, wave, entry, beat = [], ALL_ALIVE, 0, True, 0
    for kick, nb in zip(kick_masks, beats_per_bar):
        out.append(BarState(kick, alive, wave, entry, beat))
        for _, e in kills(kick, alive, entry):
            alive &= ~(1 << e)
        entry = False
        if alive == 0:
            alive, wave, entry = ALL_ALIVE, wave + 1, True
        beat += nb
    return out


def enemy_pos(e: int, beat: int, entry: bool, beat_in_bar: float, dip: int) -> tuple[int, int]:
    r, c = divmod(e, COLS)
    x = 2 + c * 6 + SWAY[beat % len(SWAY)]
    y = 2 + r * 6 + dip
    if entry and beat_in_bar < 1.0:
        y -= (4 - int(beat_in_bar * 4)) * 3          # drops in over the first beat, 3 rows per 16th
    return x, y


def player_x(kl: list[tuple[int, int]], slot: int, beat: int) -> int:
    """Left edge of the sleigh: under its next target, else under the last one, else wandering."""
    nxt = next((e for s, e in kl if s >= slot), None)
    if nxt is None and kl:
        nxt = kl[-1][1]
    if nxt is None:
        return 16 + SWAY[beat % len(SWAY)] * 4
    x, _ = enemy_pos(nxt, beat, False, 1.0, 0)
    return x + 2 - 3


def snow_y(flake: int, q: int) -> tuple[int, int]:
    """Snowflake position at song time q (in quarter-16ths). Speeds are 1-3 rows per beat."""
    h = (flake * 2654435761) & 0xFFFFFFFF
    x = h % PW
    speed = 1 + (h >> 8) % 3
    return x, ((h >> 16) % PH + (q * speed) // 16) % PH


def render(st: BarState, beat_in_bar: float, colours: list[tuple[int, int, int]], loud: float = 0.0,
           scale: int = 1) -> Image.Image:
    """The playfield at beat_in_bar (0..bar length) of a bar, at game resolution times scale."""
    img = Image.new("RGB", (PW, PH), BLACK)
    px = img.load()

    def put(x, y, c):
        if 0 <= x < PW and 0 <= y < PH:
            px[x, y] = c

    q_in_bar = int(beat_in_bar * 16)                  # quarter-16th steps since the bar started
    slot = q_in_bar // 4
    sub = q_in_bar % 4
    beat = st.song_beat + int(beat_in_bar)
    f = beat_in_bar - int(beat_in_bar)
    import math
    dip = min(1, int(math.floor(loud * 1.5 * math.sin(3.14159 * f) + 0.5)))
    kind = WAVE_KINDS[st.wave % 3]
    kl = kills(st.kick, st.alive, st.entry)
    killed_at = {e: s for s, e in kl}

    q_song = st.song_beat * 16 + q_in_bar
    for fl in range(SNOW_FLAKES):
        put(*snow_y(fl, q_song), SNOW)

    for e in range(N_ENEMIES):
        if not st.alive >> e & 1 or (e in killed_at and slot >= killed_at[e]):
            continue
        x, y = enemy_pos(e, beat, st.entry, beat_in_bar, dip)
        col = colours[(e // COLS + st.wave) % len(colours)]
        for yy, row in enumerate(ENEMY[kind][beat % 2]):
            for xx, ch in enumerate(row):
                if ch != ".":
                    put(x + xx, y + yy, {"C": col, "Y": GOLD, "W": WHITE}[ch])

    for s, e in kl:
        if slot in (s, s + 1):
            x, y = enemy_pos(e, beat, False, 1.0, dip)
            for yy, row in enumerate(SPARK[slot - s]):
                for xx, ch in enumerate(row):
                    if ch != ".":
                        put(x + xx, y + yy, SPARK_W if ch == "W" else SPARK_Y)

    for s, e in kl:                                   # the shot that lands on the kick
        if s >= 1 and slot == s - 1:
            x, y = enemy_pos(e, beat, False, 1.0, dip)
            top = GUN_Y - ((GUN_Y - (y + 5)) * sub) // 4
            put(x + 2, top, BULLET)
            put(x + 2, top + 1, BULLET)
    for s0 in range(0, SLOTS, 4):                     # a shot on every beat with no kill near it
        if any(s0 <= s <= s0 + 2 for s, _ in kl) or not s0 <= slot <= s0 + 1:
            continue
        top = GUN_Y - ((slot - s0) * 4 + sub) * 2
        bx = player_x(kl, s0, beat) + 3
        put(bx, top, BULLET)
        put(bx, top + 1, BULLET)

    x0 = player_x(kl, slot, beat)
    for yy, row in enumerate(PLAYER):
        for xx, ch in enumerate(row):
            if ch != ".":
                put(x0 + xx, PLAYER_Y + yy, {"R": RED, "Y": GOLD, "W": WHITE}[ch])
    if scale > 1:
        img = img.resize((PW * scale, PH * scale), Image.NEAREST)
    return img
