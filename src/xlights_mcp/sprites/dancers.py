"""Pixel skeleton dancers: poses, routines and crew frames, drawn 1 pixel per LED.

A dancer is a 13x17 sprite: a skull, a coloured shirt and stick-figure bones whose
elbows, hands, knees and feet move per pose. Poses are named; the right/left
versions of a move are mirrors of each other. A routine is a list of bars, one
pose per beat, and a crew is several dancers drawn side by side, in unison,
mirrored, or in canon (each dancer a beat behind the one before).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image


W, H = 13, 17          # sprite size; feet stand on row 15, row 16 is room for the bounce
BONE = (240, 240, 230)
JOINT = (150, 150, 150)
BLACK = (0, 0, 0)

SHIRTS = {
    "purple": (150, 60, 230),
    "red": (240, 50, 20),
    "teal": (20, 200, 190),
    "orange": (255, 120, 0),
    "green": (40, 210, 40),
    "pink": (255, 60, 160),
    "blue": (40, 90, 255),
    "yellow": (250, 210, 0),
}
HAIR = {
    "blonde": (255, 200, 60),
    "auburn": (220, 80, 20),
    "pink": (255, 90, 180),
    "violet": (170, 90, 255),
}
FIGURES = ("male", "female", "mixed")


def colour(name: str) -> tuple[int, int, int]:
    """A SHIRTS name or a #RRGGBB hex colour."""
    if name in SHIRTS:
        return SHIRTS[name]
    h = name.lstrip("#")
    if len(h) == 6 and all(c in "0123456789abcdefABCDEF" for c in h):
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    raise ValueError(f"unknown colour {name!r}: use {', '.join(SHIRTS)} or #RRGGBB")


@dataclass(frozen=True)
class Pose:
    """Joint positions on the unshifted 13x17 grid.

    Arms (elbow, hand) move with the body offset; legs (knee, foot) are fixed to
    the floor, so a body offset bends the knees instead of lifting the feet.
    slide moves the whole dancer, feet too, sideways inside its 13-pixel cell
    (shuffles and side steps); keep the pose narrow enough to stay inside it.
    """
    elbow_l: tuple[int, int]
    hand_l: tuple[int, int]
    elbow_r: tuple[int, int]
    hand_r: tuple[int, int]
    knee_l: tuple[int, int] = (5, 12)
    foot_l: tuple[int, int] = (5, 15)
    knee_r: tuple[int, int] = (7, 12)
    foot_r: tuple[int, int] = (7, 15)
    body: tuple[int, int] = (0, 0)
    slide: int = 0

    def mirrored(self) -> "Pose":
        m = lambda p: (W - 1 - p[0], p[1])  # noqa: E731
        return Pose(m(self.elbow_r), m(self.hand_r), m(self.elbow_l), m(self.hand_l),
                    m(self.knee_r), m(self.foot_r), m(self.knee_l), m(self.foot_l),
                    (-self.body[0], self.body[1]), -self.slide)


_BASE = {
    "stand": Pose((3, 7), (3, 9), (9, 7), (9, 9)),
    "arms_up": Pose((2, 5), (2, 2), (10, 5), (10, 2)),
    "arms_out": Pose((2, 5), (0, 5), (10, 5), (12, 5)),
    "hips": Pose((2, 7), (4, 9), (10, 7), (8, 9)),
    "claw_right": Pose((2, 4), (3, 2), (10, 4), (12, 3), body=(1, 1)),
    "lunge_left": Pose((2, 5), (0, 3), (9, 7), (10, 9),
                       knee_l=(3, 13), foot_l=(1, 15), knee_r=(8, 13), foot_r=(10, 15), body=(-1, 1)),
    "kick_right": Pose((2, 5), (0, 4), (10, 5), (12, 4), knee_r=(9, 11), foot_r=(11, 10)),
    "squat": Pose((2, 6), (2, 8), (10, 6), (10, 8),
                  knee_l=(3, 13), foot_l=(4, 15), knee_r=(9, 13), foot_r=(8, 15), body=(0, 2)),
    "point_right": Pose((3, 7), (4, 9), (9, 3), (11, 1)),
    "wave_right": Pose((3, 7), (3, 9), (10, 5), (11, 2)),
    # shuffle: step out, then slide on with the trailing foot kicked up, arms pumping
    "shuffle_out_right": Pose((3, 7), (2, 9), (9, 6), (10, 4),
                              knee_l=(4, 12), foot_l=(3, 15), knee_r=(8, 12), foot_r=(9, 15), slide=1),
    "shuffle_kick_right": Pose((2, 6), (1, 4), (9, 7), (10, 9),
                               knee_l=(4, 12), foot_l=(3, 13), knee_r=(7, 12), foot_r=(7, 15), slide=2),
    "knee_up_left": Pose((3, 7), (3, 9), (10, 6), (10, 4), knee_l=(5, 11), foot_l=(5, 13)),
    "robot_right": Pose((2, 5), (2, 8), (10, 5), (10, 2)),
    "floss_right": Pose((3, 7), (1, 9), (6, 8), (4, 10), body=(1, 0)),
    "sprinkler_right": Pose((2, 3), (3, 1), (10, 5), (12, 5)),
    "clap": Pose((2, 7), (5, 5), (10, 7), (7, 5)),
    "jack_out": Pose((2, 3), (1, 1), (10, 3), (11, 1),
                     knee_l=(4, 12), foot_l=(3, 15), knee_r=(8, 12), foot_r=(9, 15)),
    "hands_head": Pose((2, 3), (3, 1), (10, 3), (9, 1)),
    "cross_chest": Pose((3, 7), (8, 6), (9, 7), (4, 6)),
    "twist_left": Pose((3, 6), (5, 8), (10, 6), (11, 8),
                       knee_l=(4, 12), foot_l=(5, 15), knee_r=(6, 12), foot_r=(7, 15), body=(-1, 1)),
    "point_across_right": Pose((3, 7), (4, 9), (7, 8), (2, 11)),
    "zombie_right": Pose((3, 6), (2, 5), (10, 6), (11, 5), knee_r=(8, 12), foot_r=(8, 15), body=(1, 1)),
}


def _with_mirrors(base: dict[str, Pose]) -> dict[str, Pose]:
    out = dict(base)
    for name, pose in base.items():
        for a, b in (("right", "left"), ("left", "right")):
            if name.endswith("_" + a):
                out.setdefault(name[: -len(a)] + b, pose.mirrored())
    return out


POSES = _with_mirrors(_BASE)

# One pose per beat, four beats per bar.
ROUTINES: dict[str, list[list[str]]] = {
    "thriller": [
        ["claw_right", "claw_right", "claw_left", "claw_left"],
        ["lunge_left", "stand", "lunge_right", "stand"],
        ["claw_right", "claw_left", "claw_right", "claw_left"],
        ["squat", "arms_up", "squat", "arms_up"],
    ],
    "party": [
        ["arms_up", "stand", "arms_up", "stand"],
        ["point_right", "hips", "point_left", "hips"],
        ["kick_right", "stand", "kick_left", "stand"],
        ["arms_out", "squat", "arms_out", "arms_up"],
    ],
    "shuffle": [
        ["shuffle_out_right", "shuffle_kick_right", "shuffle_out_right", "stand"],
        ["shuffle_out_left", "shuffle_kick_left", "shuffle_out_left", "stand"],
        ["knee_up_left", "knee_up_right", "knee_up_left", "knee_up_right"],
        ["shuffle_out_right", "shuffle_kick_right", "shuffle_out_left", "shuffle_kick_left"],
    ],
    "robot": [
        ["robot_right", "robot_left", "robot_right", "robot_left"],
        ["arms_out", "robot_right", "arms_out", "robot_left"],
        ["sprinkler_right", "sprinkler_right", "sprinkler_left", "sprinkler_left"],
        ["robot_right", "robot_left", "squat", "arms_up"],
    ],
    "floss": [
        ["floss_right", "floss_left", "floss_right", "floss_left"],
        ["floss_right", "floss_left", "floss_right", "floss_left"],
        ["knee_up_left", "knee_up_right", "knee_up_left", "knee_up_right"],
        ["sprinkler_right", "sprinkler_left", "arms_up", "arms_up"],
    ],
    "jacks": [
        ["jack_out", "stand", "jack_out", "stand"],
        ["clap", "arms_up", "clap", "arms_up"],
        ["jack_out", "squat", "jack_out", "squat"],
        ["clap", "clap", "arms_up", "arms_up"],
    ],
    "line": [
        ["arms_out", "arms_out", "cross_chest", "cross_chest"],
        ["hands_head", "hands_head", "hips", "hips"],
        ["twist_left", "twist_right", "twist_left", "twist_right"],
        ["clap", "arms_up", "clap", "arms_up"],
    ],
    "disco": [
        ["point_right", "point_across_right", "point_right", "point_across_right"],
        ["point_left", "point_across_left", "point_left", "point_across_left"],
        ["twist_left", "twist_right", "twist_left", "twist_right"],
        ["hips", "clap", "hips", "arms_up"],
    ],
    "zombie": [
        ["zombie_right", "zombie_right", "zombie_left", "zombie_left"],
        ["claw_right", "claw_left", "claw_right", "claw_left"],
        ["zombie_right", "zombie_left", "zombie_right", "zombie_left"],
        ["squat", "squat", "arms_up", "arms_up"],
    ],
    "wave": [
        ["wave_right", "stand", "wave_right", "stand"],
        ["wave_left", "stand", "wave_left", "stand"],
        ["arms_out", "arms_up", "arms_out", "arms_up"],
        ["hips", "hips", "squat", "arms_up"],
    ],
}


def _line(a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]]:
    (x0, y0), (x1, y1) = a, b
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err, pts = dx + dy, []
    while True:
        pts.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return pts
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def _shade(c: tuple[int, int, int], f: float) -> tuple[int, int, int]:
    return tuple(int(v * f) for v in c)


def draw_dancer(pose: Pose, shirt: tuple[int, int, int], band: tuple[int, int, int] | None = None,
                bounce: int = 0, figure: str = "male", hair: tuple[int, int, int] | None = None) -> Image.Image:
    """Draw one dancer on a black 13x17 RGB image.

    The female figure has long hair framing the skull (hair colour) and a dress whose
    skirt flares over the hips; the male one has a shirt and an optional headband.
    """
    img = Image.new("RGB", (W, H), BLACK)
    px = img.load()

    def put(p, c):
        x = p[0] + pose.slide
        if 0 <= x < W and 0 <= p[1] < H:
            px[x, p[1]] = c

    bx, by = pose.body[0], pose.body[1] + bounce
    sh = lambda p: (p[0] + bx, p[1] + by)  # noqa: E731
    hip_l, hip_r = sh((5, 10)), sh((7, 10))

    for hip, knee, foot, toe in ((hip_l, pose.knee_l, pose.foot_l, -1), (hip_r, pose.knee_r, pose.foot_r, 1)):
        for p in _line(hip, knee) + _line(knee, foot):
            put(p, BONE)
        put(knee, JOINT)
        put((foot[0] + toe, foot[1]), BONE)

    for x in range(5, 8):
        put(sh((x, 9)), BONE)                       # pelvis
    for y in range(5, 9):
        for x in range(5, 8):
            put(sh((x, y)), _shade(shirt, 0.6) if x == 5 else shirt)

    if figure == "female":
        for y, (x0, x1) in ((8, (5, 7)), (9, (4, 8)), (10, (3, 9))):      # skirt
            for x in range(x0, x1 + 1):
                put(sh((x, y)), _shade(shirt, 0.6) if x == x0 else shirt)
        hair = hair or HAIR["blonde"]
        for y in range(1, 5):
            put(sh((3, y)), hair)
            put(sh((9, y)), hair)

    for shoulder, elbow, hand in ((sh((4, 5)), sh(pose.elbow_l), sh(pose.hand_l)),
                                  (sh((8, 5)), sh(pose.elbow_r), sh(pose.hand_r))):
        for p in _line(shoulder, elbow) + _line(elbow, hand):
            put(p, BONE)
        put(elbow, JOINT)
        put(shoulder, shirt)                        # sleeve

    put(sh((6, 4)), BONE)                           # neck
    for y, row in enumerate((".#####.", "#.#.#", "#####", ".###.")):
        x0 = 4 if len(row) == 5 else 3
        for i, ch in enumerate(row):
            if ch == "#":
                put(sh((x0 + i, y)), BONE)
    if figure == "female":
        for x in range(4, 9):
            put(sh((x, 0)), hair)
        put(sh((9, 0)), shirt)                      # bow
        put(sh((10, 0)), shirt)
    elif band:
        for x in range(4, 9):
            put(sh((x, 0)), band)
    return img


@dataclass
class Dancer:
    shirt: str = "red"
    band: str | None = None
    mirror: bool = False
    delay: int = 0              # beats behind the routine (canon)
    figure: str = "male"
    hair: str = "blonde"

    def colours(self):
        return colour(self.shirt), (colour(self.band) if self.band else None)

    def draw(self, pose: Pose, bounce: int = 0) -> Image.Image:
        shirt, band = self.colours()
        return draw_dancer(pose, shirt, band, bounce, self.figure, HAIR[self.hair])


@dataclass
class Crew:
    dancers: list[Dancer] = field(default_factory=lambda: [Dancer("purple", "purple"), Dancer("red"),
                                                           Dancer("teal", "teal")])
    gap: int = 0
    scale: int = 1

    @property
    def size(self) -> tuple[int, int]:
        n = len(self.dancers)
        return ((n * W + (n - 1) * self.gap) * self.scale, H * self.scale)


def crew_from_style(n: int, style: str = "unison", shirts: list[str] | None = None,
                    figure: str = "male") -> list[Dancer]:
    """Build n dancers: unison, mirror (every other one flipped) or canon (one beat apart).

    figure is male, female, or mixed (alternating, starting female).
    """
    if figure not in FIGURES:
        raise ValueError(f"figure must be one of {', '.join(FIGURES)}")
    shirts = shirts or ["purple", "red", "teal", "orange", "green", "pink", "blue", "yellow"]
    hairs = ["blonde", "pink", "auburn", "violet"]
    out = []
    for i in range(n):
        c = shirts[i % len(shirts)]
        fig = figure if figure != "mixed" else ("female" if i % 2 == 0 else "male")
        dress = colour(c)
        far = lambda h: sum((a - b) ** 2 for a, b in zip(HAIR[h], dress)) > 120 ** 2  # noqa: E731
        hair = next((h for h in hairs[i % len(hairs):] + hairs if far(h)), hairs[i % len(hairs)])
        out.append(Dancer(c, band=c if i % 2 == 0 else None,
                          mirror=style == "mirror" and i % 2 == 1,
                          delay=i if style == "canon" else 0, figure=fig, hair=hair))
    return out


def timeline(routine: str | list[list[str]], beats: int) -> list[str]:
    if isinstance(routine, str) and routine not in ROUTINES:
        raise ValueError(f"unknown routine {routine!r}: use {', '.join(ROUTINES)}")
    bars = ROUTINES[routine] if isinstance(routine, str) else routine
    flat = [p for bar in bars for p in bar]
    if not flat:
        raise ValueError("routine has no poses")
    unknown = sorted({p for p in flat if p not in POSES})
    if unknown:
        raise ValueError(f"unknown poses: {', '.join(unknown)}")
    return [flat[i % len(flat)] for i in range(beats)]


def crew_frame(crew: Crew, poses: list[str], beat: int, bounce: int = 0) -> Image.Image:
    """The whole crew at one beat. Each dancer reads poses[beat - delay]; before its entry it stands."""
    img = Image.new("RGB", (crew.size[0] // crew.scale, H), BLACK)
    for i, d in enumerate(crew.dancers):
        k = beat - d.delay
        pose = POSES[poses[k] if 0 <= k < len(poses) else "stand"]
        if d.mirror:
            pose = pose.mirrored()
        img.paste(d.draw(pose, bounce), (i * (W + crew.gap), 0))
    if crew.scale > 1:
        img = img.resize(crew.size, Image.NEAREST)
    return img


def bar_frames(crew: Crew, poses: list[str], first_beat: int, beats: int, frames_per_beat: int = 1) -> list[Image.Image]:
    """Frames for `beats` beats from first_beat. With 2 frames per beat the second one dips a row (a bounce)."""
    out = []
    for b in range(first_beat, first_beat + beats):
        for f in range(frames_per_beat):
            out.append(crew_frame(crew, poses, b, bounce=1 if f % 2 == 1 else 0))
    return out


MARK = (1, 0, 0)    # near-black: under xLights' Transparent Black level, so it never lights


def save_gif(frames: list[Image.Image], path, ms_per_frame: int = 250) -> None:
    """Save frames as a GIF with exact colours, one GIF frame per input frame, looping forever.

    xLights spreads a non-looping GIF's frames evenly over the effect, so the frame count must
    survive: Pillow merges consecutive identical frames, so every other frame gets one marker
    pixel in the bottom-right corner to keep repeated poses apart.
    """
    frames = [f.convert("RGB").copy() for f in frames]
    for i, f in enumerate(frames):
        if i % 2 and f.getpixel((f.width - 1, f.height - 1)) == BLACK:
            f.putpixel((f.width - 1, f.height - 1), MARK)
    colours = sorted({c for f in frames for _, c in f.getcolors(maxcolors=1 << 16)})
    if len(colours) > 256:
        raise ValueError(f"{len(colours)} colours; a GIF holds 256")
    index = {c: i for i, c in enumerate(colours)}
    flat_pal = [v for c in colours for v in c]
    pal = []
    for f in frames:
        p = Image.new("P", f.size)
        p.putpalette(flat_pal)
        raw = f.tobytes()
        p.putdata([index[tuple(raw[i:i + 3])] for i in range(0, len(raw), 3)])
        pal.append(p)
    pal[0].save(path, format="GIF", save_all=True, append_images=pal[1:], duration=ms_per_frame, loop=0,
                disposal=1, optimize=False)
