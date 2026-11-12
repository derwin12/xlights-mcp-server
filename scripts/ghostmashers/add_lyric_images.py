r"""Generate lyric-themed images and add them as a top Pictures layer on Mega Tree and Matrix
in F:\ShowFolderAI\Ghostmashers.xsq (existing layers untouched)."""
import re
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SHOW = Path(r"F:\ShowFolderAI")
XSQ = SHOW / "Ghostmashers.xsq"
IMG_DIR = SHOW / "Images" / "Ghostmashers"
S = 1000  # icon canvas (square, stretched later)
FONT = r"C:\Windows\Fonts\arialbd.ttf"


def new():
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def ghost_shape(d, cx=500, top=120, w=560, h=720, fill=(255, 255, 255, 255), eyes=True):
    d.ellipse([cx - w / 2, top, cx + w / 2, top + w], fill=fill)
    bottom = top + h
    pts = [(cx - w / 2, top + w / 2), (cx + w / 2, top + w / 2), (cx + w / 2, bottom)]
    n = 5
    for i in range(n):  # zigzag hem
        x1 = cx + w / 2 - (i + 0.5) * w / n
        x2 = cx + w / 2 - (i + 1) * w / n
        pts += [(x1, bottom - 70), (x2, bottom)]
    d.polygon(pts, fill=fill)
    if eyes:
        for ex in (cx - 110, cx + 110):
            d.ellipse([ex - 50, top + 200, ex + 50, top + 330], fill=(0, 0, 0, 255))
        d.ellipse([cx - 60, top + 380, cx + 60, top + 500], fill=(0, 0, 0, 255))


def ghost():
    im, d = new()
    ghost_shape(d)
    return im


def noghost():
    im, d = new()
    ghost_shape(d, top=140, w=520, h=680)
    d.ellipse([60, 60, 940, 940], outline=(255, 0, 0, 255), width=90)
    d.line([(190, 190), (810, 810)], fill=(255, 0, 0, 255), width=90)
    return im


def phone():
    im, d = new()
    d.rounded_rectangle([300, 100, 700, 900], 70, fill=(0, 255, 60, 255))
    d.rounded_rectangle([340, 190, 660, 760], 25, fill=(0, 0, 0, 255))
    d.ellipse([465, 800, 535, 870], fill=(0, 0, 0, 255))
    for r, a in ((60, 0), (120, 0)):  # ring arcs both sides
        d.arc([150 - r, 120 - r + 60, 150 + r + 100, 120 + r + 160], 200, 250, fill=(255, 255, 0, 255), width=28)
        d.arc([850 - r - 100, 120 - r + 60, 850 + r, 120 + r + 160], 290, 340, fill=(255, 255, 0, 255), width=28)
    return im


def question():
    im, d = new()
    f = ImageFont.truetype(FONT, 1000)
    d.text((500, 500), "?", font=f, fill=(0, 255, 60, 255), anchor="mm")
    return im


def invisible():
    im, d = new()
    d.polygon([(220, 400), (780, 400), (720, 340), (700, 160), (300, 160), (280, 340)], fill=(150, 90, 40, 255))
    d.rectangle([260, 330, 740, 380], fill=(255, 0, 0, 255))
    d.rectangle([150, 400, 850, 440], fill=(150, 90, 40, 255))
    for ex in (360, 640):
        d.ellipse([ex - 100, 520, ex + 100, 720], outline=(0, 200, 255, 255), width=28)
    d.line([(460, 620), (540, 620)], fill=(0, 200, 255, 255), width=24)
    return im


def bed():
    im, d = new()
    ghost_shape(d, cx=500, top=60, w=400, h=420)
    d.rounded_rectangle([60, 400, 940, 800], 40, fill=(0, 120, 255, 255))
    d.rectangle([60, 800, 130, 900], fill=(150, 90, 40, 255))
    d.rectangle([870, 800, 940, 900], fill=(150, 90, 40, 255))
    return im


ICONS = {"ghost": ghost, "noghost": noghost, "phone": phone, "question": question,
         "invisible": invisible, "bed": bed}


def save_images():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    for name, fn in ICONS.items():
        icon = fn()
        mat = Image.new("RGBA", (960, 480), (0, 0, 0, 0))  # Matrix 120x60
        mat.paste(icon.resize((480, 480), Image.LANCZOS), (240, 0))
        mat.save(IMG_DIR / f"{name}_matrix.png")
        tree = Image.new("RGBA", (400, 1500), (0, 0, 0, 0))  # Mega Tree 20x75
        tree.paste(icon.resize((400, 800), Image.LANCZOS), (0, 350))
        tree.save(IMG_DIR / f"{name}_tree.png")


# (icon, start s, end s)
EVENTS = [
    ("ghost", 48.25, 49.6), ("ghost", 52.375, 53.8), ("ghost", 56.5, 57.9),
    ("question", 137.15, 138.5), ("invisible", 141.45, 142.8), ("bed", 145.5, 146.95),
    ("ghost", 172.85, 174.2),
    ("phone", 176.45, 177.5), ("noghost", 186.05, 187.6),
    ("phone", 233.7, 234.6), ("noghost", 251.2, 252.8),
]
PALETTE = 40


def settings(path):
    return ("B_CHOICE_BufferStyle=Default,E_CHECKBOX_Pictures_TransparentBlack=1,"
            "E_CHOICE_Pictures_Direction=none,E_CHOICE_Scaling=Scale To Fit,"
            "E_SLIDER_Pictures_EndScale=100,E_SLIDER_Pictures_StartScale=100,"
            f"E_TEXTCTRL_Pictures_Filename={path},E_TEXTCTRL_Pictures_Speed=1.0,"
            "E_TEXTCTRL_Pictures_TransparentBlack=10,T_TEXTCTRL_Fadein=0.1,T_TEXTCTRL_Fadeout=0.1")


def main():
    save_images()
    shutil.copy2(XSQ, XSQ.with_name("Ghostmashers.xsq.pre_images"))
    s = XSQ.read_text(encoding="utf-8")
    db_m = re.search(r"(<EffectDB>)(.*?)(\s*</EffectDB>)", s, re.S)
    n_db = len(re.findall(r"<Effect>", db_m.group(2)))
    new_db, refs = [], {}
    for model, suffix in (("Mega Tree", "tree"), ("Matrix", "matrix")):
        layer = []
        for i, (icon, a, b) in enumerate(EVENTS):
            key = (icon, suffix)
            if key not in refs:
                refs[key] = n_db + len(new_db)
                new_db.append(f"\n    <Effect>{settings(f'Images/Ghostmashers/{icon}_{suffix}.png')}</Effect>")
            ident = f' id="{i}"' if i else ""
            layer.append(f'        <Effect ref="{refs[key]}" name="Pictures"{ident} '
                         f'startTime="{round(a * 1000)}" endTime="{round(b * 1000)}" palette="{PALETTE}" />')
        block = "      <EffectLayer>\n" + "\n".join(layer) + "\n      </EffectLayer>\n"
        m = re.search(r'(<Element type="model" name="%s">.*?)(    </Element>)' % re.escape(model), s, re.S)
        s = s[:m.end(1)] + block + s[m.start(2):] if False else s[:m.end(1)].rstrip(" ") + block + s[m.start(2):]
    s = s.replace(db_m.group(0), db_m.group(1) + db_m.group(2) + "".join(new_db) + db_m.group(3), 1)
    XSQ.write_text(s, encoding="utf-8")
    print("done; effects db", n_db, "->", n_db + len(new_db))


if __name__ == "__main__":
    sys.exit(main())
