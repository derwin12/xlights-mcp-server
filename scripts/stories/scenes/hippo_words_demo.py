"""Hippo lyrics in the two-tone text styles on a 50x24 matrix: each line appears as it's sung, with the letters
hopping, wobbling, rising or dropping on the beats (first verse, about 7.5-34 s).

    cd scripts
    python matrix_scenes.py stories/scenes/hippo_words_demo.py "E:/2023/ShowFolder3D/I Want a Hippopotamus for Christmas SS.xsq" \
        --model DEMO --size 50x24 --preview demo.mp4 --from 7.5 --to 34 --audio "E:/2023/ShowFolder3D/Audio/I want a Hippopotamus for Christmas.mp3"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hippopotamus_window import cues  # noqa: E402,F401 - same word/beat files

PREFIX = "hippo_words"
RED, GREEN, WHITE, GOLD = (255, 20, 20), (20, 230, 40), (255, 255, 255), (255, 200, 30)
PURPLE, BLUE, PINK = (160, 70, 255), (40, 120, 255), (255, 60, 170)
TOP, BOT = 7, 17


def build(s):
    c = s.cues

    def line(text, t_in, t_out, y, **kw):
        kw.setdefault("shade", RED)
        kw.setdefault("enter", "pop")
        kw.setdefault("stagger", 0.05)
        s.letters(text, t_in, t_out, 25, y, hits=c.beats_in(t_in, t_out), **kw)

    def bars(t0, t1, color=GOLD):
        for yy in (1, 22):
            key = s.drawn(f"bar_{yy}_{color[0]}_{color[1]}_{color[2]}", 50, 1, lambda d, im: d.line([0, 0, 49, 0], fill=color + (255,)))
            s.pic(key, t0, t1, 25, yy, z=10)

    # I want a hippopotamus for Christmas
    end = c.w("for", 10)
    line("I WANT A", c.w("i", 7), end, TOP)
    line("HIPPO", c.w("hippo", 9), end, BOT, shade=PURPLE, enter="rise", motion="wave")
    t0, t1 = c.w("for", 10), c.w("a", 13)
    line("FOR", t0, t1, TOP, shade=GREEN, motion="still")
    line("CHRISTMAS", c.w("christmas", 10), t1, BOT, motion="jumble", amp=2)
    bars(c.w("christmas", 10), t1)

    # only a hippopotamus will do
    t0, t1 = c.w("a", 13), c.w("dont", 16)
    line("HIPPO", t0, t1, TOP, shade=PURPLE, motion="alternate")
    line("WILL DO", c.w("will", 14), t1, BOT, shade=GREEN, motion="alternate", phase=1)

    # don't want a doll, no dinky tinker toy
    t0, mid, t1 = c.w("dont", 16), c.w("no", 19), c.w("i", 21)
    line("DON'T WANT", t0, mid, TOP, color=WHITE, shade=BLUE, motion="still")
    line("A DOLL", c.w("a", 18), mid, BOT, shade=PINK, enter="rise", motion="still")
    line("NO DINKY", mid, t1, TOP, motion="jumble", amp=1)
    line("TOY", c.w("toy", 20), t1, BOT, shade=GREEN, enter="rise", motion="wave")

    # I want a hippopotamus to play with and enjoy
    t0, t1 = c.w("i", 21), c.w("i", 25)
    line("HIPPO", c.w("hippo", 22), t1, TOP, color=[PURPLE, WHITE], shade=[WHITE, PURPLE], enter="rise",
         motion="alternate")
    line("TO PLAY", c.w("to", 23), t1, BOT, shade=GREEN, motion="wave")

    # I want a hippopotamus for Christmas
    t0, t1 = c.w("hippo", 26), c.w("dont", 29)
    line("HIPPO", t0, t1, TOP, shade=PURPLE, motion="alternate")
    xmas = c.w("christmas", 27)
    line("CHRISTMAS", xmas, t1, BOT, color=WHITE, shade=[RED, GREEN], motion="alternate", amp=1)
    bars(xmas, t1, RED)

    # I don't think Santa Claus will mind, do you?
    t0, t1 = c.w("santa", 30), c.w("he", 33)
    line("SANTA", t0, t1, TOP, enter="drop", motion="wave")
    line("CLAUS", c.w("claus", 30), t1, BOT, shade=GREEN, enter="rise", motion="wave")
