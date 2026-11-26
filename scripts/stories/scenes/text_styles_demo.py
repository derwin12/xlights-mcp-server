"""Text styles demo: two-tone shaded words and per-letter motion on a 50x24 matrix (the Burl Ives
'Holly Jolly Christmas' matrix look). Uses the Hippo song's beats only for timing.

    cd scripts
    python matrix_scenes.py stories/scenes/text_styles_demo.py "E:/2023/ShowFolder3D/I Want a Hippopotamus for Christmas SS.xsq" \
        --model DEMO --size 50x24 --sheet demo.png --at 6,7,8,9
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hippopotamus_window import cues  # noqa: E402,F401 - same word/beat files

PREFIX = "text_demo"
RED, GREEN, WHITE, GOLD = (255, 20, 20), (20, 230, 40), (255, 255, 255), (255, 200, 30)
PURPLE, BLUE, PINK = (150, 60, 255), (40, 120, 255), (255, 60, 170)


def build(s):
    c = s.cues
    b = c.beats_in(5.0, c.duration)
    scene = lambda k: (b[k * 8], b[k * 8 + 8])  # noqa: E731 - 8 beats per scene

    # 1. HOLLY / JOLLY: white face, green / red shade, letters take turns hopping (opposite phase per line)
    t0, t1 = scene(0)
    hits = c.beats_in(t0, t1)
    s.letters("HOLLY", t0, t1, 25, 7, shade=GREEN, hits=hits, motion="alternate")
    s.letters("JOLLY", t0, t1, 25, 17, shade=RED, hits=hits, motion="alternate", phase=1)

    # 2. CHRISTMAS, wobbling letters, between two gold bars
    t0, t1 = scene(1)
    s.letters("CHRISTMAS", t0, t1, 25, 12, shade=RED, hits=c.beats_in(t0, t1), motion="jumble", amp=2,
              enter="pop", stagger=0.05)
    for yy in (3, 21):
        s.pic(s.drawn(f"bar{yy}", 50, 2, lambda d, im: d.rectangle([0, 0, 49, 1], fill=GOLD + (255,))),
              t0, t1, 25, yy, z=10)

    # 3. CHRISTMAS in per-letter colours, THIS waves, YEAR drops in letter by letter
    t0, t1 = scene(2)
    mid = c.beats_in(t0, t1)[3]
    s.show(s.word("CHRISTMAS", [PURPLE, WHITE], font=6, shade=[WHITE, PURPLE]), t0, t1, 25, 5, enter="pop", z=30)
    s.letters("THIS", t0, t1, 14, 15, color=BLUE, shade=WHITE, hits=c.beats_in(t0, t1), motion="wave")
    s.letters("YEAR", mid, t1, 37, 15, color=PINK, shade=WHITE, enter="rise", stagger=0.12)

    # 4. The small 3x5 font with a shade too (fits more words); plain vs shaded for comparison
    t0, t1 = scene(3)
    s.show(s.word("PLAIN", RED), t0, t1, 25, 3, enter=None, z=30)
    s.show(s.word("SHADED", WHITE, shade=RED), t0, t1, 25, 9, enter=None, z=30)
    s.show(s.word("BIG", WHITE, 2, shade=GREEN), t0, t1, 25, 19, enter=None, z=30)
