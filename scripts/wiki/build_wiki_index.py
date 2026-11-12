"""Build the A-Z Index page of the xLights wiki.

Collects, from every wiki page:
  * the page title (# Title)                      -> Page
  * every ##/###/#### heading                      -> Page#anchor
  * every bold first-column table cell (| **X** |) -> Page#<heading above it>
and writes them, grouped by first letter, to Index.md.

Usage:  python scripts/wiki/build_wiki_index.py [--wiki H:\\XlightsSourceDir\\xLights.wiki] [--check]
--check exits 1 if Index.md would change (no write).
"""
import argparse
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

SKIP_PAGES = {"Index", "Home", "_Sidebar", "_Footer", "xLights-Manual", "Arches"}
SKIP_PREFIXES = ("wxWidgets-Removal",)
# Table labels / headings too generic to be useful on their own.
GENERIC = {
    "setting", "settings", "item", "what it does", "meaning", "option", "options", "control",
    "value", "values", "name", "notes", "note", "see also", "overview", "example", "examples",
    "description", "where", "what for", "key", "keys", "action", "column", "field", "button",
    "type", "default", "in this section", "related", "tips", "tip", "more", "other", "general",
    "menu", "chapter", "parameters", "properties", "summary", "introduction", "what's in it", "page", "pages", "result", "yes", "no", "on", "off",
}

HEAD_RE = re.compile(r"^(#{1,4})\s+(.+?)\s*#*\s*$")
ROW_RE = re.compile(r"^\|\s*\*\*(.+?)\*\*")
CELL_RE = re.compile(r"^\|\s*([^|]+?)\s*\|")
SEP_RE = re.compile(r"^\|[\s:|-]+\|?\s*$")
# Tables whose first column names settings even when the cells aren't bold.
LABEL_HEADERS = {"parameter", "setting", "option", "control", "item", "property", "field", "button"}


def slugify(text: str) -> str:
    """GitHub heading anchor."""
    t = re.sub(r"<[^>]+>", "", text)
    t = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", t)          # links/images -> text
    t = t.replace("`", "").replace("*", "").replace("_", "_")
    t = t.strip().lower()
    t = "".join(c for c in t if c.isalnum() or c in " -_" or unicodedata.category(c).startswith("L"))
    return t.replace(" ", "-")


def clean(label: str) -> str:
    s = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", label)
    s = re.sub(r"<[^>]+>", "", s).replace("`", "").replace("**", "").replace("\\|", "|")
    s = re.sub(r"\s+", " ", s).strip()
    s = s.rstrip(":").strip()
    if s.endswith("...") or s.endswith("…"):
        s = s.rstrip(".…").strip()
    return s


def page_title(lines, stem):
    for l in lines:
        m = HEAD_RE.match(l)
        if m and len(m.group(1)) == 1:
            return clean(m.group(2))
    return stem.replace("-", " ")


def collect(wiki: Path):
    entries = defaultdict(set)  # label -> {(link, where)}
    for p in sorted(wiki.glob("*.md")):
        stem = p.stem
        if stem in SKIP_PAGES or stem.startswith(SKIP_PREFIXES) or ":" in stem:
            continue
        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        title = page_title(lines, stem)
        entries[title].add((stem, title))
        seen = defaultdict(int)
        section, anchor = None, ""
        in_code = False
        prev, label_table = "", False
        for l in lines:
            if not l.startswith("|"):
                label_table = False
            elif SEP_RE.match(l):
                hm = CELL_RE.match(prev)
                label_table = bool(hm and clean(hm.group(1)).lower() in LABEL_HEADERS)
                prev = l
                continue
            prev = l
            if l.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            m = HEAD_RE.match(l)
            if m:
                if len(m.group(1)) == 1:
                    continue
                h = clean(m.group(2))
                slug = slugify(m.group(2))
                n = seen[slug]
                seen[slug] += 1
                anchor = slug if n == 0 else f"{slug}-{n}"
                section = h
                if h.lower() not in GENERIC and h != title:
                    entries[h].add((f"{stem}#{anchor}", f"{title} › {h}"))
                continue
            m = ROW_RE.match(l) or (label_table and CELL_RE.match(l))
            if m:
                lab = clean(m.group(1))
                if not lab or lab.lower() in GENERIC or len(lab) > 60 or not re.search(r"[A-Za-z0-9]", lab):
                    continue
                if section and section != title and section.lower() not in GENERIC:
                    entries[lab].add((f"{stem}#{anchor}", f"{title} › {section}"))
                elif section:
                    entries[lab].add((f"{stem}#{anchor}", title))
                else:
                    entries[lab].add((stem, title))
    return entries


def sort_key(label):
    s = re.sub(r"^[^A-Za-z0-9]+", "", label)
    return (s.lower(), label)


def letter(label):
    s = re.sub(r"^[^A-Za-z0-9]+", "", label)
    c = s[:1].upper()
    return c if c.isalpha() else "#"


def render(entries):
    groups = defaultdict(list)
    for lab in sorted(entries, key=sort_key):
        groups[letter(lab)].append(lab)
    letters = sorted(groups, key=lambda c: (c != "#", c))
    out = [
        "# Index",
        "",
        "[Home](Home) › **Index**",
        "",
        "Every page, section, setting and menu item in this wiki, A to Z. GitHub can't search inside wiki pages, "
        "so use your browser's find (**Ctrl+F** / **⌘F**) on this page, or jump to a letter:",
        "",
        " · ".join(f"[{c}](#{'0-9' if c == '#' else c.lower()})" for c in letters),
        "",
    ]
    for c in letters:
        out += [f"## {'0-9' if c == '#' else c}", ""]
        for lab in groups[c]:
            targets = sorted(entries[lab], key=lambda t: (t[1].lower(), t[0]))
            counts = defaultdict(int)
            for _, where in targets:
                counts[where] += 1
            # Same text on two pages (e.g. Sequencer-Tab-Windows / View-Windows): name the page.
            links = " · ".join(
                f"[{where} ({link.split('#')[0].replace('-', ' ')})]({link})" if counts[where] > 1 else f"[{where}]({link})"
                for link, where in targets)
            out.append(f"- **{lab}** — {links}")
        out.append("")
    out.append("<!-- generated by xlights-mcp-server scripts/wiki/build_wiki_index.py: do not edit by hand, re-run the script -->")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wiki", default=r"H:\XlightsSourceDir\xLights.wiki")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    wiki = Path(a.wiki)
    entries = collect(wiki)
    text = render(entries)
    target = wiki / "Index.md"
    old = target.read_text(encoding="utf-8") if target.exists() else ""
    if a.check:
        print("Index.md up to date" if old == text else "Index.md is stale")
        sys.exit(0 if old == text else 1)
    target.write_text(text, encoding="utf-8", newline="\n")
    n = sum(len(v) for v in entries.values())
    print(f"Index.md: {len(entries)} terms, {n} links, {len(text)//1024} KB")


if __name__ == "__main__":
    main()
