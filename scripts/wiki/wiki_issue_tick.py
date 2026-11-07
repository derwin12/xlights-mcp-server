"""Tick finished wiki work in the manual-migration tracking issues.

1. Chapter issue: ticks every page checkbox whose wiki page is finished, i.e.
   it carries <!-- maintained-in-wiki --> and has no <!-- SCREENSHOT: --> left.
2. Backlog issues ("Wiki review" from .github/wiki-watch): ticks entries under a
   page heading when the entry text contains one of the substrings listed for
   that page in a JSON file: {"Page-Name": ["substring", ...], ...}

    python scripts/wiki/wiki_issue_tick.py --chapter-issue 5 --covered covered.json
    python scripts/wiki/wiki_issue_tick.py --chapter-issue 5 --dry-run

Bodies are sent to gh as bytes: text-mode stdin on Windows doubles the \\r in
every line ending.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PAGE_LINK = re.compile(r"^(\s*)- \[ \] \[[^\]]+\]\(https://github\.com/[^/]+/[^/]+/wiki/([^)]+)\)")


def gh(*args: str, input: str | None = None) -> str:
    r = subprocess.run(["gh", *args], capture_output=True, check=True,
                       input=input.encode("utf-8") if input is not None else None)
    return r.stdout.decode("utf-8")


def body(repo: str, n: int) -> str:
    return json.loads(gh("issue", "view", str(n), "-R", repo, "--json", "body"))["body"].replace("\r", "")


def finished(wiki: Path, page: str) -> bool:
    f = wiki / f"{page}.md"
    if not f.exists():
        return False
    t = f.read_text(encoding="utf-8")
    return "<!-- maintained-in-wiki" in t and "SCREENSHOT:" not in t


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default="derwin12/manual")
    ap.add_argument("--wiki", default="H:/XlightsSourceDir/xLights.wiki")
    ap.add_argument("--chapter-issue", type=int)
    ap.add_argument("--covered", help="JSON {page: [substrings]} of backlog entries now documented")
    ap.add_argument("--backlog-issues", default="15,16,17")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    wiki = Path(args.wiki)

    if args.chapter_issue:
        lines, n = [], 0
        for line in body(args.repo, args.chapter_issue).split("\n"):
            m = PAGE_LINK.match(line)
            if m and finished(wiki, m.group(2)):
                line, n = line.replace("- [ ]", "- [x]", 1), n + 1
            lines.append(line)
        print(f"#{args.chapter_issue}: ticking {n} finished page(s)")
        if n and not args.dry_run:
            gh("issue", "edit", str(args.chapter_issue), "-R", args.repo, "--body-file", "-", input="\n".join(lines))

    if args.covered:
        covered = json.loads(Path(args.covered).read_text(encoding="utf-8"))
        for issue in (int(x) for x in args.backlog_issues.split(",") if x):
            lines, page, n = [], None, 0
            for line in body(args.repo, issue).split("\n"):
                h = re.match(r"^### \[([^\]]+)\]", line)
                if h:
                    page = h.group(1)
                elif line.startswith("### "):
                    page = None
                keys = covered.get(page or "", [])
                if line.startswith("- [ ]") and any(k.lower() in line.lower() for k in keys):
                    line, n = "- [x]" + line[5:], n + 1
                lines.append(line)
            print(f"#{issue}: ticking {n} backlog entr{'y' if n == 1 else 'ies'}")
            if n and not args.dry_run:
                gh("issue", "edit", str(issue), "-R", args.repo, "--body-file", "-", input="\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
