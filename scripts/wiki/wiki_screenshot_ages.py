"""How old is each wiki page's screenshots? Optionally write it into the chapter issues.

An image's age is the year it was first added: to the manual repo for
images/manual/* (renamed by manual_to_wiki.py), to the wiki repo otherwise.
The manual's git history starts 2022-07-31, so "2022" means "2022 or earlier".

    python scripts/wiki/wiki_screenshot_ages.py                    # report only
    python scripts/wiki/wiki_screenshot_ages.py --annotate 1-9     # update chapter issues #1-#9
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from manual_to_wiki import slug  # noqa: E402

OLD = 2022
PAGE_LINE = re.compile(r"^(\s*- \[[ x]\] \[[^\]]+\]\(https://github\.com/[^/]+/[^/]+/wiki/([^)]+)\))(.*)$", re.M)


def first_added(repo: Path, path: str) -> dict[str, int]:
    out = subprocess.run(["git", "-C", str(repo), "log", "--diff-filter=A", "--name-only",
                          "--format=@%ad", "--date=format:%Y", "--", path],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    years, year = {}, None
    for line in out.splitlines():
        if line.startswith("@"):
            year = int(line[1:])
        elif line.strip():
            years[line.strip().strip('"')] = year  # newest first, so the oldest wins
    return years


def page_ages(manual: Path, wiki: Path) -> dict[str, dict]:
    by_name: dict[str, int] = {}
    for p, y in first_added(manual, ".gitbook/assets").items():
        a = Path(p)
        by_name.setdefault(slug(a.stem).lower() + a.suffix.lower(), y)
    wiki_years = first_added(wiki, "images")
    result = {}
    for page in sorted(wiki.glob("*.md")):
        imgs = list(dict.fromkeys(re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", page.read_text(encoding="utf-8"))))
        years = [y for y in ((by_name.get(s.split("/")[-1]) if s.startswith("images/manual/") else wiki_years.get(s))
                             for s in imgs) if y]
        if imgs:
            result[page.stem] = {"n": len(imgs), "years": sorted(years)}
    return result


def gh(*args: str, input: str | None = None) -> str:
    r = subprocess.run(["gh", *args], capture_output=True, check=True,
                       input=input.encode("utf-8") if input is not None else None)
    return r.stdout.decode("utf-8")


def annotate(repo: str, issue: int, ages: dict) -> None:
    body = json.loads(gh("issue", "view", str(issue), "-R", repo, "--json", "body"))["body"].replace("\r", "")
    total = old = 0

    def note(m: re.Match) -> str:
        nonlocal total, old
        r = ages.get(m.group(2))
        extra = []
        if r:
            o = sum(1 for y in r["years"] if y <= OLD)
            total, old = total + r["n"], old + o
            extra.append(f"{r['n']} screenshot{'s' * (r['n'] != 1)}" + (f", **{o} from ≤2022**" if o else ", all recent"))
        if "wiki text" in m.group(3):
            extra.append("wiki text")
        return m.group(1) + (" — " + ", ".join(extra) if extra else "")

    body = PAGE_LINE.sub(note, body)
    body = re.sub(r"\n\*\*Screenshots:\*\*.*\n", "\n", body)
    summary = f"**Screenshots:** {old} of {total} are from 2022 or earlier (the manual's git history starts July 2022)."
    body = body.replace("\n## Pages\n", f"\n{summary}\n\n## Pages\n", 1)
    gh("issue", "edit", str(issue), "-R", repo, "--body-file", "-", input=body)
    print(f"#{issue}: {old}/{total} screenshots from <=2022")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manual", default="H:/XlightsSourceDir/manual")
    ap.add_argument("--wiki", default="H:/XlightsSourceDir/xLights.wiki")
    ap.add_argument("--repo", default="derwin12/manual")
    ap.add_argument("--annotate", help="chapter issue numbers, e.g. 1-9 or 4,5")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    ages = page_ages(Path(args.manual), Path(args.wiki))
    print("screenshots by year added:", dict(sorted(Counter(y for r in ages.values() for y in r["years"]).items())))
    oldest = sorted(ages.items(), key=lambda kv: (kv[1]["years"][0] if kv[1]["years"] else 9999, -kv[1]["n"]))
    for name, r in oldest[:15]:
        print(f"  {name:40} {r['n']:3} imgs, oldest {r['years'][0] if r['years'] else '?'}")
    if args.annotate:
        nums = []
        for part in args.annotate.split(","):
            a, _, b = part.partition("-")
            nums += range(int(a), int(b or a) + 1)
        for n in nums:
            annotate(args.repo, n, ages)
    return 0


if __name__ == "__main__":
    sys.exit(main())
