r"""Add a "Sections" timing track (Verse 1 / Chorus 1 / Bridge / Instrumental ...) from Genius section headers.

Usage:
    python scripts/song_sections.py SONG.xsq fixed.json --artist "Ella Langley" --track "Choosin' Texas"
        [--genius-url URL] [--save genius.txt] [--genius-file genius.txt] [--name Sections]

fixed.json is lyrics_align.py's output (phrases with timed words). Genius labels its lyrics with [Verse 1],
[Chorus], [Bridge], [Outro] ...; each sung phrase is matched to a line, walking the sections in order, so the
first matching phrase gives a section's start. Gaps of GAP_S without singing become Intro / Instrumental /
Ending. A section Genius lists but the recording skips (remixes cut verses) is passed over; a section sung
again in place (a doubled chorus) starts a new one. Repeated labels are numbered (Chorus 1, Chorus 2 ...).

Genius has no lyrics API (api.genius.com returns metadata only) and answers scripted requests with 403, so
the page is read in headless Chromium (Python Playwright). The URL is guessed from artist + title
(genius.com/Ella-langley-choosin-texas-lyrics); pass --genius-url when the guess is wrong.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from lyrics_align import tokens

GAP_S = 5.0         # silence that becomes its own Intro / Instrumental / Ending section
MATCH_MIN = 0.45    # phrase-to-line similarity that counts as a match
LOOKAHEAD = 4       # sections the walk may skip forward over


def genius_url(artist: str, track: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", f"{artist} {track}".lower().replace("&", "and").replace("'", "").replace("’", ""))
    slug = slug.strip("-")
    return f"https://genius.com/{slug[:1].upper()}{slug[1:]}-lyrics"


def fetch_genius(url: str) -> str:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                     "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
        resp = page.goto(url, wait_until="domcontentloaded")
        if not resp or resp.status >= 400:
            b.close()
            raise SystemExit(f"Genius {resp.status if resp else '?'} for {url}; pass --genius-url")
        page.wait_for_selector('[data-lyrics-container="true"]', timeout=30000)
        text = "\n".join(page.eval_on_selector_all('[data-lyrics-container="true"]', "els => els.map(e => e.innerText)"))
        b.close()
    return text


def parse_sections(text: str) -> list[tuple[str, list[list[str]]]]:
    """[(label, [line tokens])] in page order; text before the first [header] (page blurb) is dropped."""
    out: list[tuple[str, list[list[str]]]] = []
    for line in text.splitlines():
        m = re.match(r"^\[([^\]:]+)(?::[^\]]*)?\]\s*$", line.strip())   # [Chorus: Ella Langley] -> Chorus
        if m:
            out.append((m.group(1).strip(), []))
        elif out and tokens(line):
            out[-1][1].append(tokens(line))
    return [s for s in out if s[1]]


def ratio(a, b) -> float:
    return difflib.SequenceMatcher(a=a, b=b, autojunk=False).ratio()


def best_line(words: list[str], lines: list[list[str]]) -> tuple[float, int]:
    """(similarity, line index) of the best 1- or 2-line window in a section."""
    best = (0.0, 0)
    for i in range(len(lines)):
        for n in (1, 2):
            if i + n <= len(lines):
                best = max(best, (ratio(words, sum(lines[i:i + n], [])), i))
    return best


def place(phrases: list[dict], secs) -> list[tuple[int, float, float]]:
    """Group phrases into sung sections: [(section index, first word start, last word end)]."""
    groups: list[list] = []
    cur, last_line = 0, -1
    for p in phrases:
        words = tokens(p["text"])
        cands = []
        for k in range(cur, min(cur + LOOKAHEAD + 1, len(secs))):
            s, line = best_line(words, secs[k][1])
            cands.append((s - 0.05 * (k - cur), k, line, s))
        _, k, line, s = max(cands)
        lines = secs[cur][1]
        if groups and 0 <= last_line + 1 < len(lines) and ratio(words, lines[last_line + 1]) >= MATCH_MIN:
            k, line = cur, last_line + 1    # the expected next line, even when sung differently (a chorus
                                            # ending "cause she's from Texas" must not restart the chorus)
        elif s < MATCH_MIN:             # ad-lib or unmatched: stays in the current section
            k, line = cur, last_line
        new = not groups or k != cur or (line < last_line - 1)   # moved on, or the same section sung again
        if new:
            groups.append([k, p["start"], p["end"]])
        else:
            groups[-1][2] = p["end"]
        cur, last_line = k, max(line, 0) if new else max(line, last_line)
    return [tuple(g) for g in groups]


def sections_track(groups, secs, duration: float) -> list[tuple[str, float, float]]:
    counts: dict[str, int] = {}
    for k, _, _ in groups:
        counts[secs[k][0]] = counts.get(secs[k][0], 0) + 1
    seen: dict[str, int] = {}
    out: list[tuple[str, float, float]] = []
    prev_end = 0.0
    for i, (k, s, e) in enumerate(groups):
        label = secs[k][0]
        if counts[label] > 1 and not re.search(r"\d$", label):
            seen[label] = seen.get(label, 0) + 1
            label = f"{label} {seen[label]}"
        if s - prev_end >= GAP_S:
            out.append(("Intro" if not out else "Instrumental", 0.0 if not out else prev_end, s))
        elif out:
            out[-1] = (out[-1][0], out[-1][1], s)       # no gap: previous section runs up to this one
        elif s > 0:
            s = 0.0                                     # short pickup: first section starts the song
        out.append((label, s, e))
        prev_end = e
    if duration - prev_end >= GAP_S:
        out.append(("Ending", prev_end, duration))
    elif out:
        out[-1] = (out[-1][0], out[-1][1], duration)
    return out


def write_track(xsq: Path, name: str, rows) -> None:
    tree = ET.parse(xsq)
    root = tree.getroot()
    disp, eff = root.find("DisplayElements"), root.find("ElementEffects")
    for parent in (disp, eff):
        for el in [e for e in parent if e.get("type") == "timing" and e.get("name") == name]:
            parent.remove(el)
    # first among the rows, so the sections sit above the lyric tracks
    idx = next((i for i, e in enumerate(disp) if e.get("type") == "timing"), 0)
    disp.insert(idx, ET.Element("Element", {"collapsed": "0", "type": "timing", "name": name, "visible": "1", "active": "0"}))
    track = ET.Element("Element", {"type": "timing", "name": name})
    layer = ET.SubElement(track, "EffectLayer")
    for label, s, e in rows:
        ET.SubElement(layer, "Effect", {"label": label, "startTime": str(int(s * 1000)), "endTime": str(int(e * 1000))})
    eff.insert(next((i for i, e in enumerate(eff) if e.get("type") == "timing"), 0), track)
    ET.indent(tree, space="  ")
    tree.write(xsq, encoding="utf-8", xml_declaration=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xsq")
    ap.add_argument("phrases", help="fixed.json from lyrics_align.py")
    ap.add_argument("--artist", default="")
    ap.add_argument("--track", default="")
    ap.add_argument("--genius-url")
    ap.add_argument("--genius-file", help="use saved Genius text instead of fetching")
    ap.add_argument("--save", help="keep the fetched Genius text here")
    ap.add_argument("--name", default="Sections")
    a = ap.parse_args()

    if a.genius_file and Path(a.genius_file).exists():
        text = Path(a.genius_file).read_text(encoding="utf-8")
    else:
        url = a.genius_url or genius_url(a.artist, a.track)
        print("genius:", url)
        text = fetch_genius(url)
        if a.save:
            Path(a.save).write_text(text, encoding="utf-8")
    secs = parse_sections(text)
    if not secs:
        raise SystemExit("no [Section] headers found on the Genius page")
    print("genius sections:", ", ".join(s[0] for s in secs))

    phrases = [p for p in json.load(open(a.phrases, encoding="utf-8")) if p["words"]]
    xsq = Path(a.xsq)
    duration = float(ET.parse(xsq).getroot().findtext(".//sequenceDuration") or phrases[-1]["end"])
    rows = sections_track(place(phrases, secs), secs, duration)
    for label, s, e in rows:
        print(f"  {int(s // 60)}:{s % 60:05.2f} - {int(e // 60)}:{e % 60:05.2f}  {label}")
    write_track(xsq, a.name, rows)
    print(f"wrote {len(rows)} sections to {xsq.name} as {a.name!r}")


if __name__ == "__main__":
    main()
