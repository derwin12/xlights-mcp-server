"""Build (or refresh) the wiki screenshot to-do issue on derwin12/manual.

One checklist, grouped by chapter (from the chapter issues' page lists), with
per page:
  - every screenshot first added in 2022 or earlier (the old GitBook manual), and
  - every hidden <!-- SCREENSHOT: ... --> placeholder still waiting for a shot.

Tick an item when it has been retaken, or when it should stay as it is (a
diagram, a photo of a prop, a historic picture): append "keep" to the line in
that case. Re-running keeps ticks and notes for items still present and drops
items that are gone (retaken images get a new file date, filled placeholders
disappear).

    python scripts/wiki/wiki_screenshot_todo.py --dry-run          # print the body
    python scripts/wiki/wiki_screenshot_todo.py --create           # open the issue
    python scripts/wiki/wiki_screenshot_todo.py --issue 18         # refresh it
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wiki_screenshot_ages import OLD, first_added, gh, slug  # noqa: E402

WIKI_URL = "https://github.com/xLightsSequencer/xLights/wiki/"
CHAPTER_ISSUES = range(1, 10)
PAGE_IN_ISSUE = re.compile(r"\]\(https://github\.com/[^/]+/[^/]+/wiki/([^)#]+)\)")
ITEM_KEY = re.compile(r"^- \[[ x]\] (`[^`]+`|placeholder: [^—\n]+?)(?: —|$)")


def chapters(repo: str) -> list[tuple[str, list[str]]]:
    out = []
    for n in CHAPTER_ISSUES:
        d = json.loads(gh("issue", "view", str(n), "-R", repo, "--json", "title,body"))
        title = d["title"].removeprefix("Wiki: ")
        out.append((f"{title} (#{n})", list(dict.fromkeys(PAGE_IN_ISSUE.findall(d["body"])))))
    return out


def page_items(manual: Path, wiki: Path) -> dict[str, list[str]]:
    by_name: dict[str, int] = {}
    for p, y in first_added(manual, ".gitbook/assets").items():
        a = Path(p)
        by_name.setdefault(slug(a.stem).lower() + a.suffix.lower(), y)
    wiki_years = first_added(wiki, "images")
    items: dict[str, list[str]] = {}
    for page in sorted(wiki.glob("*.md")):
        text = page.read_text(encoding="utf-8")
        lines = []
        for alt, src in dict.fromkeys(re.findall(r"!\[([^\]]*)\]\(([^)\s]+)\)", text)):
            y = by_name.get(src.split("/")[-1]) if src.startswith("images/manual/") else wiki_years.get(src)
            if y and y <= OLD:
                desc = alt.strip() or "no caption"
                lines.append(f"- [ ] `{src}` — {desc[:90]}")
        for m in re.findall(r"<!-- SCREENSHOT:\s*(.*?)\s*-->", text, re.S):
            m = re.sub(r"^images/\S+\s*[—-]\s*", "", " ".join(m.split()))
            lines.append(f"- [ ] placeholder: {m[:140]}")
        if lines:
            items[page.stem] = lines
    return items


def build(repo: str, items: dict[str, list[str]], old_body: str = "") -> str:
    kept = {}
    for line in old_body.replace("\r", "").split("\n"):
        m = ITEM_KEY.match(line)
        if m:
            kept[m.group(1).strip()] = line
    seen, sections, n_img, n_ph = set(), [], 0, 0
    groups = chapters(repo)
    listed = {p for _, pages in groups for p in pages}
    groups.append(("Other pages", sorted(p for p in items if p not in listed)))
    for title, pages in groups:
        block = []
        for p in pages:
            if p in seen or p not in items:
                continue
            seen.add(p)
            block.append(f"\n**[{p.replace('-', ' ')}]({WIKI_URL}{p})**")
            for line in items[p]:
                key = ITEM_KEY.match(line).group(1).strip()
                block.append(kept.get(key, line))
                n_img += key.startswith("`")
                n_ph += key.startswith("placeholder")
        if block:
            sections.append(f"\n### {title}" + "\n".join(block))
    head = (
        "Screenshots on the wiki that still need attention: images carried over from the old GitBook manual "
        f"(first added {OLD} or earlier; the manual's git history starts July 2022) and hidden "
        "`<!-- SCREENSHOT: -->` placeholders that were never filled.\n\n"
        "- Tick an item when it is retaken, or when it should stay (diagram, photo of a prop, historic picture): "
        "add *keep* after the line then.\n"
        "- Items that need the show or a sequence set up first: add *needs setup* and what is missing.\n"
        "- Regenerate with `python scripts/wiki/wiki_screenshot_todo.py --issue N` (ticks and notes are kept).\n"
        "- How to take them: skill `manual-to-wiki`, section *Screenshots: driving xLights*.\n\n"
        f"**{n_img} old screenshots, {n_ph} placeholders.**\n"
    )
    return head + "\n".join(sections) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manual", default="H:/XlightsSourceDir/manual")
    ap.add_argument("--wiki", default="H:/XlightsSourceDir/xLights.wiki")
    ap.add_argument("--repo", default="derwin12/manual")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--create", action="store_true")
    g.add_argument("--issue", type=int)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    items = page_items(Path(args.manual), Path(args.wiki))
    old = ""
    if args.issue:
        old = json.loads(gh("issue", "view", str(args.issue), "-R", args.repo, "--json", "body"))["body"]
    body = build(args.repo, items, old)
    if args.dry_run or not (args.create or args.issue):
        print(body)
        print(f"[{len(body)} chars]", file=sys.stderr)
        return 0
    if args.create:
        print(gh("issue", "create", "-R", args.repo, "--title", "Wiki: screenshot refresh",
                 "--label", "wiki-migration,screenshots", "--body-file", "-", input=body).strip())
    else:
        gh("issue", "edit", str(args.issue), "-R", args.repo, "--body-file", "-", input=body)
        print(f"#{args.issue} updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
