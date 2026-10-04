r"""Package a generated MH sequence as an xLights .xsqz (zip) for sharing.

usage: python scripts/package_xsqz.py "EL_Halloween Is Here v1" [--show F:\ShowFolderAI]
Contents: xlights_rgbeffects.xml, xlights_networks.xml, the .xsq (bare mediaFile name) and the media file.
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
        z.write(media, media.name)
    print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
