"""SuperStar-style Morph backdrops shared by the four-matrix stories (garage, the two windows as a stage, bushes).

backdrop(s, t0, t1): copy the SuperStar tree's Galaxy / Fan / Shockwave accents behind every scene, and its Morph
patterns where it runs them (Story.echo; `peak` skips scenes whose Morph bursts are too dense to copy): one copy per garage door, per window and per half of the bushes - each
roughly the tree's shape - with every other copy mirrored. Returns whether the Morphs were copied, and remembers it
on the story for pattern_sweeps().

pattern_sweeps(s, t0, t1, colors): Morph pattern groups chained on every other beat (Story.morph_beats), the
SuperStar replacement for one full-width bar per bar; skipped while the tree's own patterns are being echoed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from matrix_scenes import tree_morphs  # noqa: E402

ECHO_MIN = 8  # tree Morphs in a scene before the matrices copy its patterns


def _boxes(s):
    """Copies of the tree pattern for this matrix: (box, mirrored)."""
    W, H = s.W, s.H
    if W >= 2 * H:  # wide (the garage, the bushes): two halves, the second mirrored
        h = W // 2
        return [((0, 0, h - 1, H - 1), False), ((h, 0, W - 1, H - 1), True)]
    return [(None, False)]


ACCENTS = ("Galaxy", "Fan", "Shockwave")


def _copy(s, t0, t1, kinds):
    if hasattr(s, "places"):  # a Stage (not isinstance: matrix_scenes.py runs as __main__, a second module)
        s.echo(t0, t1, mirror="alternate", kinds=kinds)
    else:
        for box, mirror in _boxes(s):
            s.echo(t0, t1, box=box, mirror=mirror, kinds=kinds)


def tree_peak(ms) -> int:
    """Most of these tree Morphs running at the same moment."""
    cur = peak = 0
    for _t, d in sorted([(m["t0"], 1) for m in ms] + [(m["t1"], -1) for m in ms]):
        cur += d
        peak = max(peak, cur)
    return peak


def backdrop(s, t0, t1, peak=None) -> bool:
    """The tree's Galaxy / Fan / Shockwave accents always; its Morph patterns when there are ECHO_MIN or more in
    the scene and, with `peak`, no more than that many run at once (a tree that fires bursts of 100+ Morphs would
    need hundreds of layers per copy; those scenes get pattern_sweeps instead). Returns (and remembers for
    pattern_sweeps) whether the Morphs were copied."""
    s._echo = False
    if s.source is None:
        return False
    _copy(s, t0, t1, ACCENTS)
    ms = [m for m in tree_morphs(s.source) if t0 <= m["t0"] < t1]
    if len(ms) < ECHO_MIN or (peak is not None and tree_peak(ms) > peak):
        return False
    _copy(s, t0, t1, ("Morph",))
    s._echo = True
    return True


def pattern_sweeps(s, t0, t1, colors, every=1):
    if not getattr(s, "_echo", False):
        s.morph_beats(t0, t1, [tuple(c) for c in colors], every=2 * every)
