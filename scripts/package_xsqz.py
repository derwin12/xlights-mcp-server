r"""Package a generated MH sequence as an xLights .xsqz (zip) for sharing.

usage: python scripts/package_xsqz.py "EL_Halloween Is Here v1" [--show F:\ShowFolderAI] [--no-media]
Contents: xlights_rgbeffects.xml, xlights_networks.xml, the .xsq (bare mediaFile name), the media file
(left out with --no-media), any show-relative pictures the Pictures effects use (e.g. Images/LyricIcons/*) and the
Shader effects' .fs files at their show-relative path (Shaders/*).
Written to <show>\packages\<name>.xsqz. Use the generated .xsq, not one xLights re-saved.
"""
import argparse
import re
import sys
import zipfile
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--show", default=r"F:\ShowFolderAI")
    ap.add_argument("--no-media", action="store_true", help="leave the audio out (sequences for sale; buyers supply the song)")
    a = ap.parse_args()
    show = Path(a.show)
    xsq = show / f"{a.name}.xsq"
    text = xsq.read_text(encoding="utf-8")
    m = re.search(r"<mediaFile>(.*?)</mediaFile>", text)
    media = Path(m.group(1)) if m else None
    if not media or not media.exists():
        sys.exit(f"media file missing: {media}")
    text = text.replace(m.group(0), f"<mediaFile>{media.name}</mediaFile>")
    out = show / "packages" / f"{a.name}.xsqz"
    out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(show / "xlights_rgbeffects.xml", "xlights_rgbeffects.xml")
        z.write(show / "xlights_networks.xml", "xlights_networks.xml")
        z.writestr(xsq.name, text)
        if not a.no_media:
            z.write(media, media.name)
        # pictures the effects use (lyric_images.py), at the same show-relative path, or they render solid red
        for rel in sorted(set(re.findall(r"E_TEXTCTRL_Pictures_Filename=([^,<]+)", text))):
            if not Path(rel).is_absolute() and (show / rel).exists():
                z.write(show / rel, rel)
        if not a.no_media:   # a music video on a matrix is the artist's media too: only in review builds
            for rel in sorted(set(re.findall(r"E_FILEPICKERCTRL_Video_Filename=([^,<]+)", text))):
                if not Path(rel).is_absolute() and (show / rel).exists():
                    z.write(show / rel, rel)
        # shaders are stored with an absolute path (F:/ShowFolderAI/Shaders/X.fs): pack them at the show-relative path,
        # where xLights' FixFile finds them on another machine (the same layout xLights' own Package Sequence uses)
        for p in sorted(set(re.findall(r"E_0FILEPICKERCTRL_IFS=([^,<]+)", text))):
            f = Path(p) if Path(p).is_absolute() else show / p
            try:
                rel = f.resolve().relative_to(show.resolve()).as_posix()
            except ValueError:
                rel = f"Shaders/{f.name}"   # outside the show folder: put it where the show's own shaders live
            if f.exists():
                z.write(f, rel)
            else:
                print(f"warning: shader file missing, not packed: {p}")
    print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
