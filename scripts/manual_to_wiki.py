"""Convert sections of the GitBook xLights manual into GitHub-wiki pages.

The manual (github.com/xLightsSequencer/manual) is a GitBook repo: nested
folders, ``{% hint %}``/``{% tabs %}``/``{% content-ref %}`` blocks, and ~2000
images in ``.gitbook/assets`` with names like ``image (92).png``.  A GitHub
wiki is flat, so every manual page becomes one wiki page named after its
SUMMARY.md title, and only the images a converted page uses are copied.

Usage (one section at a time; nothing is committed):

    python scripts/manual_to_wiki.py --section chapters/chapter-four-set-up/
    python scripts/manual_to_wiki.py --section chapters/chapter-four-set-up/ --dry-run

Links to manual pages outside the converted section point at the manual's
GitHub source so nothing dangles; re-run with more sections to turn them into
wiki links.  Each page ends with a ``<!-- manual-source: ... -->`` comment
recording the source file and commit, for re-syncing later.
"""
from __future__ import annotations

import argparse
import posixpath
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

MANUAL_GITHUB = "https://github.com/xLightsSequencer/manual/blob/main/"
IMAGE_DIR = "images/manual"

# Manual pages that map onto wiki pages which already exist (or are linked).
PAGE_NAME_OVERRIDES = {
    "README.md": "xLights-Manual",
    "chapters/chapter-four-set-up/README.md": "Controllers-Tab",
    "chapters/chapter-four-tabs/README.md": "Layout-Tab",
    "chapters/chapter-four-sequencer/README.md": "Sequencer-Tab",
    "chapters/chapter-two-quick-start-guide/README.md": "Quick-Start-Guide",
    "chapters/chapter-three-installation/README.md": "Installation",
    "tutorials/xlights_rgb.xml.md": "Editing-xLights-rgb-xml",
}

# Landing pages where the manual has only a banner image but the wiki has a
# hand-written overview: keep the wiki text, just add the sub-page list.
KEEP_WIKI_BODY = {
    "README.md",
    "chapters/chapter-two-quick-start-guide/README.md",
    "chapters/chapter-four-tabs/README.md",
    "chapters/chapter-four-sequencer/README.md",
    "chapters/chapter-five-menus/README.md",
    "chapters/chapter-six-advanced-features.md",
    "effects/off/README.md",
}
# Manual effect pages map onto the wiki's Effect-<Name> pages, which are kept
# as they are (they are checked against xLights' effectmetadata JSON).
EFFECTS_PREFIX = "effects/off/"
SIDEBAR_DEPTH = 2  # chapter + its direct sub-pages; deeper pages via "In This Section"
# Sidebar labels that differ from the manual's titles (pages rewritten in the wiki)
SIDEBAR_TITLES = {"Controllers-Tab": "Controllers", "Controllers-Settings": "Controller Settings"}  # a Layout sub-page since xLights 2026.14

# Pages whose content is folded into their parent page instead of getting a
# page of their own (the parent README is only a banner image).
MERGE_INTO_PARENT = {
    "chapters/chapter-four-set-up/set-up.md",
}

HINT_KIND = {"info": "NOTE", "success": "TIP", "warning": "WARNING", "danger": "CAUTION"}


@dataclass
class Page:
    path: str  # manual-relative posix path
    title: str
    group: str = ""  # SUMMARY.md "## ..." heading the page sits under
    depth: int = 0
    parent: "Page | None" = None
    children: list["Page"] = field(default_factory=list)
    wiki_name: str = ""
    keep_wiki: bool = False  # leave the existing wiki text alone


def slug(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.replace("&", "and").replace("/", " ")).strip()
    return re.sub(r"[\s_]+", "-", text)


def parse_summary(manual: Path) -> list[Page]:
    """Return every page in SUMMARY.md order, with parent/child links."""
    pages: list[Page] = []
    stack: list[tuple[int, Page]] = []
    group = ""
    for line in (manual / "SUMMARY.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\s*)\* \[(.+?)\]\((.+?)\)", line)
        if not m:
            if line.startswith("## "):
                group = line[3:].strip().replace("Appendicies", "Appendices")
            if line.startswith("#"):
                stack.clear()
            continue
        indent, title, path = len(m.group(1)), m.group(2).replace("\\", ""), m.group(3)
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1] if stack else None
        page = Page(path=path, title=title, group=group, depth=len(stack), parent=parent)
        if parent:
            parent.children.append(page)
        pages.append(page)
        stack.append((indent, page))
    return pages


def effect_page(p: Page, all_wiki: set[str]) -> str | None:
    """Existing Effect-<Name> wiki page for a manual effect page, if any."""
    if not p.path.startswith(EFFECTS_PREFIX) or p.path.endswith("README.md"):
        return None
    norm = {re.sub(r"[^a-z0-9]", "", n[len("Effect-"):].lower()): n
            for n in all_wiki if n.startswith("Effect-")}
    key = re.sub(r"[^a-z0-9]", "", p.title.lower())
    return norm.get(key) or norm.get(key.rstrip("s"))


def assign_names(pages: list[Page], existing_wiki: set[str], all_wiki: set[str]) -> None:
    taken: dict[str, int] = {}
    for p in pages:
        if p.path in PAGE_NAME_OVERRIDES:
            continue
        taken[slug(p.title)] = taken.get(slug(p.title), 0) + 1
    for p in pages:
        effect = effect_page(p, all_wiki)
        if effect:
            p.wiki_name, p.keep_wiki = effect, True
            continue
        if p.path in PAGE_NAME_OVERRIDES:
            p.wiki_name = PAGE_NAME_OVERRIDES[p.path]
            p.keep_wiki = p.path in KEEP_WIKI_BODY and p.wiki_name in all_wiki
            continue
        if p.path in KEEP_WIKI_BODY and slug(p.title) in all_wiki:
            p.wiki_name, p.keep_wiki = slug(p.title), True
            continue
        name = slug(p.title)
        # Ambiguous titles ("Installation", "Models", ...) and one-word titles
        # ("File", "Colors", "Linux") get the parent's name in front; so do
        # titles that would clobber an unrelated wiki page.
        if p.parent and (taken[name] > 1 or "-" not in name or name in existing_wiki
                         or name in PAGE_NAME_OVERRIDES.values()):
            name = f"{PAGE_NAME_OVERRIDES.get(p.parent.path) or slug(p.parent.title)}-{name}"
        p.wiki_name = name


def target_page(p: Page) -> Page:
    """The page whose wiki file actually holds ``p``'s content."""
    return p.parent if p.path in MERGE_INTO_PARENT and p.parent else p


class Converter:
    def __init__(self, manual: Path, wiki: Path, pages: list[Page], section: str, commit: str):
        self.manual, self.wiki, self.section, self.commit = manual, wiki, section, commit
        self.by_path = {p.path: p for p in pages}
        self.images: dict[Path, str] = {}  # source asset -> wiki-relative path
        self.missing_images: list[str] = []

    def in_section(self, path: str) -> bool:
        return path.startswith(self.section)

    # ---- links and images ---------------------------------------------
    def resolve(self, src: str, href: str) -> str:
        path = posixpath.normpath(posixpath.join(posixpath.dirname(src), href))
        if href.endswith("/") or (self.manual / path).is_dir():
            path = posixpath.join(path, "README.md")
        return path

    def link_for(self, src: str, href: str) -> str:
        if re.match(r"^[a-z]+:|^#", href):
            return href
        target, _, anchor = href.partition("#")
        path = self.resolve(src, target) if target else src
        page = self.by_path.get(path)
        if page is None:
            return MANUAL_GITHUB + path + (f"#{anchor}" if anchor else "")
        page = target_page(page)
        if self.in_section(page.path) or page.keep_wiki:
            return page.wiki_name + (f"#{anchor}" if anchor else "")
        return MANUAL_GITHUB + page.path

    def image_for(self, src: str, href: str) -> str:
        if re.match(r"^[a-z]+:", href):
            return href
        asset = (self.manual / self.resolve(src, href)).resolve()
        if not asset.is_file():
            self.missing_images.append(f"{src}: {href}")
            return href
        if asset not in self.images:
            name = slug(asset.stem).lower() + asset.suffix.lower()
            used = set(self.images.values())
            stem, n = name.rsplit(".", 1)[0], 2
            while f"{IMAGE_DIR}/{name}" in used:
                name, n = f"{stem}-{n}{asset.suffix.lower()}", n + 1
            self.images[asset] = f"{IMAGE_DIR}/{name}"
        return self.images[asset]

    # ---- markup ---------------------------------------------------------
    def convert_body(self, src: str, text: str) -> str:
        # GitBook front matter -> italic description line
        description = ""
        fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if fm:
            d = re.search(r"^description:\s*>?-?\s*(.*?)(?=^\w+:|\Z)", fm.group(1), re.S | re.M)
            description = " ".join(d.group(1).split()) if d else ""
            text = text[fm.end():]

        # some pages carry backslash-escaped tags: \{% hint ... %\}
        text = text.replace("\\{%", "{%").replace("%\\}", "%}")

        # <figure>/<div>/<img> HTML -> markdown images
        def figure(m: re.Match) -> str:
            img = re.search(r'<img[^>]*src="([^"]+)"[^>]*?(?:alt="([^"]*)")?', m.group(0))
            cap = re.search(r"<figcaption>(?:<p>)?(.*?)(?:</p>)?</figcaption>", m.group(0), re.S)
            out = f"![{img.group(2) or ''}](<{img.group(1)}>)" if img else ""
            return out + (f"\n*{cap.group(1).strip()}*" if cap and cap.group(1).strip() else "")

        text = re.sub(r"<figure>.*?</figure>", figure, text, flags=re.S)
        text = re.sub(r'<div[^>]*>\s*(<img[^>]*>)\s*</div>', r"\1", text, flags=re.S)
        text = re.sub(r'<img[^>]*src="([^"]+)"[^>]*>', lambda m: f"![](<{m.group(1)}>)", text)

        # {% hint %} -> GitHub alert blockquote
        def hint(m: re.Match) -> str:
            body = m.group(2).strip("\n")
            lines = [f"> [!{HINT_KIND.get(m.group(1), 'NOTE')}]"] + [f"> {l}".rstrip() for l in body.splitlines()]
            return "\n".join(lines)

        text = re.sub(r'\{% hint style="(\w+)" %\}(.*?)\{% endhint %\}', hint, text, flags=re.S)

        # {% content-ref %} -> "See [Title](Page)."
        def content_ref(m: re.Match) -> str:
            href = m.group(1)
            page = self.by_path.get(self.resolve(src, href.split("#")[0]))
            title = page.title if page else href
            return f"See [{title}]({href})."

        text = re.sub(r'\{% content-ref url="([^"]+)" %\}.*?\{% endcontent-ref %\}', content_ref, text, flags=re.S)
        text = re.sub(r'\{% embed url="([^"]+)" %\}(.*?\{% endembed %\})?', r"<\1>", text, flags=re.S)
        text = re.sub(r'\{% tab title="([^"]+)" %\}', r"#### \1", text)
        text = re.sub(r"\{% (?:end)?tabs? %\}\n?", "", text)

        # images, then links (images first so ![..](..) isn't seen as a link)
        # targets are either <wrapped (may contain spaces/parens)> or bare
        target = r"\((?:<([^>]+)>|([^)\s]+))\)"

        def href(m: re.Match) -> str:
            return (m.group(2) or m.group(3)).replace("\\_", "_")

        text = re.sub(
            r"!\[([^\]]*)\]" + target,
            lambda m: f"![{m.group(1)}]({self.image_for(src, href(m))})",
            text,
        )
        text = re.sub(
            r"(?<!!)\[([^\]]+)\]" + target,
            lambda m: f"[{m.group(1)}]({self.link_for(src, href(m))})",
            text,
        )

        text = text.replace("&#x20;", "")
        text = re.sub(r"^(#+)[ \t]*\*\*(.+?)\*\*[ \t]*$", r"\1 \2", text, flags=re.M)  # bold headings
        text = re.sub(r"^#+[ \t]*$\n?", "", text, flags=re.M)  # empty headings
        text = re.sub(r"[ \t]+$", "", text, flags=re.M)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        # drop the source H1; the wiki page heading comes from SUMMARY.md
        text = re.sub(r"\A# .*\n+", "", text)
        return (f"*{description}*\n\n" if description else "") + text

    def render(self, page: Page) -> str:
        parts = [f"# {page.title}", ""]
        if page.parent:
            crumbs, p = [], page.parent
            while p:
                crumbs.insert(0, f"[{p.title}]({target_page(p).wiki_name})")
                p = p.parent
            parts += [" › ".join(crumbs) + f" › **{page.title}**", ""]

        sources = [page.path]
        body = self.convert_body(page.path, (self.manual / page.path).read_text(encoding="utf-8"))
        parts.append(body)
        for child in page.children:
            if child.path in MERGE_INTO_PARENT:
                sources.append(child.path)
                parts += ["", self.convert_body(child.path, (self.manual / child.path).read_text(encoding="utf-8"))]

        listed = [c for c in page.children if c.path not in MERGE_INTO_PARENT]
        if listed:
            parts += ["", "## In This Section", ""]
            parts += [f"- [{c.title}]({c.wiki_name})" for c in listed]

        parts += ["", "<!-- manual-source: " + ", ".join(sources) + f" @ {self.commit[:7]} -->", ""]
        return dedupe_images("\n".join(parts))

    def render_kept(self, page: Page, existing: str) -> str | None:
        """Hand-written wiki page + a list of the manual sub-pages it doesn't link yet.
        Returns None when there is nothing to add."""
        body = re.sub(r"\n*<!-- manual-source:.*?-->\n*", "\n", existing)
        body = re.sub(r"\n## In This Section\n.*?(?=\n## |\n---|\Z)", "", body, flags=re.S).rstrip() + "\n"
        missing = [c for c in page.children
                   if c.path not in MERGE_INTO_PARENT and not re.search(
                       rf"\[\[(?:[^\]|]*\|)?{re.escape(c.wiki_name)}\]\]|\]\({re.escape(c.wiki_name)}[#)]", body)]
        if not missing:
            return None
        nav = "\n".join(["## In This Section", ""] + [f"- [{c.title}]({c.wiki_name})" for c in missing])
        # before See Also / the "Last updated" footer if there is one, else at the end
        m = re.search(r"\n(## See Also\n|---\n\*Last updated)", body)
        at = m.start() if m else len(body)
        body = body[:at].rstrip() + "\n\n" + nav + "\n\n" + body[at:].lstrip("\n")
        marker = f"<!-- manual-source: {page.path} @ {self.commit[:7]} (wiki text kept, sub-page list added) -->"
        return body.rstrip() + "\n\n" + marker + "\n"


def build_sidebar(pages: list[Page], old: str) -> str:
    """_Sidebar.md from SUMMARY.md: group headings, chapters and their direct sub-pages."""
    footer = old[old.index("\n---"):].strip("\n") if "\n---" in old else ""
    lines = ["# xLights Manual", ""]
    group = None
    for p in pages:
        if p.path == "README.md":
            lines += ["- [[Home|xLights-Manual]]", ""]
            continue
        if p.depth >= SIDEBAR_DEPTH or (p.parent and p.parent.path.startswith(EFFECTS_PREFIX)):
            continue
        if p.path in MERGE_INTO_PARENT:
            continue
        if p.group != group:
            group = p.group
            lines += ["", f"## {group}"]
        title = SIDEBAR_TITLES.get(p.wiki_name, p.title)
        lines.append("  " * p.depth + f"- [[{title}|{p.wiki_name}]]")
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n\n" + footer + "\n"


def dedupe_images(text: str) -> str:
    """Drop the GitBook logo banner and repeats of an image already shown on the page
    (a merged child page usually repeats its parent's screenshot)."""
    seen: set[str] = set()
    out = []
    for line in text.split("\n"):
        m = re.fullmatch(r"!\[[^\]]*\]\(([^)]+)\)", line.strip())
        if m:
            if m.group(1) in seen or m.group(1).endswith("/xlights-logo.png"):
                continue
            seen.add(m.group(1))
        out.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out))


def keep_see_also(existing: Path) -> str:
    """Hand-written 'See Also' block from a wiki page we are about to replace."""
    if not existing.is_file():
        return ""
    m = re.search(r"^## See Also\n.*?(?=^---|\Z)", existing.read_text(encoding="utf-8"), re.S | re.M)
    return m.group(0).strip() if m else ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manual", default="H:/XlightsSourceDir/manual")
    ap.add_argument("--wiki", default="H:/XlightsSourceDir/xLights.wiki")
    ap.add_argument("--section", required=True, help="manual path prefix, e.g. chapters/chapter-four-set-up/")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--sidebar", action="store_true", help="rebuild _Sidebar.md from SUMMARY.md")
    args = ap.parse_args()

    manual, wiki = Path(args.manual), Path(args.wiki)
    commit = subprocess.run(["git", "-C", str(manual), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=True).stdout.strip()
    pages = parse_summary(manual)
    # hand-written wiki pages only: pages from an earlier run of this script
    # (they carry a manual-source comment) must keep their names on re-runs
    all_wiki = {p.stem for p in wiki.glob("*.md")}
    # (pages rewritten in the wiki keep their manual page's name too)
    def ours(text: str) -> bool:
        return ("<!-- manual-source:" in text and "(wiki text kept" not in text) or "<!-- maintained-in-wiki" in text

    existing = {p.stem for p in wiki.glob("*.md") if not ours(p.read_text(encoding="utf-8"))}
    assign_names(pages, existing, all_wiki)

    conv = Converter(manual, wiki, pages, args.section, commit)
    todo = [p for p in pages if conv.in_section(p.path) and p.path not in MERGE_INTO_PARENT]
    if not todo:
        print(f"No SUMMARY.md pages under {args.section}", file=sys.stderr)
        return 1

    for page in todo:
        out = wiki / f"{page.wiki_name}.md"
        if page.keep_wiki:
            text = conv.render_kept(page, out.read_text(encoding="utf-8"))
            if text is None:
                print(f"{'keep':6} {out.name:45} <- {page.path}")
                continue
            print(f"{'nav+':6} {out.name:45} <- {page.path}")
            if not args.dry_run:
                out.write_text(text, encoding="utf-8", newline="\n")
            continue
        if out.exists() and "<!-- maintained-in-wiki" in out.read_text(encoding="utf-8"):
            print(f"{'skip':6} {out.name:45} <- {page.path} (maintained in the wiki)")
            continue
        text = conv.render(page)
        see_also = keep_see_also(out)
        if see_also:
            text = text.replace("\n<!-- manual-source", f"\n{see_also}\n\n<!-- manual-source", 1)
        status = "update" if out.exists() else "new"
        print(f"{status:6} {out.name:45} <- {page.path}")
        if not args.dry_run:
            out.write_text(text, encoding="utf-8", newline="\n")

    print(f"{len(conv.images)} images -> {IMAGE_DIR}/")
    if not args.dry_run:
        (wiki / IMAGE_DIR).mkdir(parents=True, exist_ok=True)
        for src, rel in conv.images.items():
            shutil.copy2(src, wiki / rel)
    for miss in conv.missing_images:
        print(f"missing image: {miss}", file=sys.stderr)
    if args.sidebar:
        sidebar = wiki / "_Sidebar.md"
        text = build_sidebar(pages, sidebar.read_text(encoding="utf-8") if sidebar.exists() else "")
        print(f"sidebar: {text.count(chr(10) + '- ') + text.count('  - ')} entries")
        if not args.dry_run:
            sidebar.write_text(text, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
