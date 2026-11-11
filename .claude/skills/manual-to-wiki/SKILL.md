---
name: manual-to-wiki
description: Move a chapter of the GitBook xLights manual into the xLights GitHub wiki, rewritten for the current xLights from source, with fresh screenshots taken by driving the running xLights, staged on the derwin12/manual test wiki and tracked in derwin12/manual issues. Use when asked to do the next manual/wiki chapter (Sequencer, Menus, Quick Start...), retake wiki screenshots, tick the wiki tracking issues, handle a "Wiki review" issue from the xLights wiki watcher, or publish wiki chapters to xLightsSequencer/xLights.wiki.
---

# Manual → wiki, one chapter at a time

## Where things are
| What | Where |
|---|---|
| GitBook manual (source text) | `H:\XlightsSourceDir\manual` (fork derwin12/manual; `upstream` = xLightsSequencer/manual) |
| Wiki working copy | `H:\XlightsSourceDir\xLights.wiki`, branch `manual-import-trial`; remote `staging` = derwin12/manual.wiki (test wiki), `origin` = official wiki |
| xLights source (ground truth) | `H:\XlightsSourceDir\xLights` (changelog = `README.txt`, effect options = `resources/effectmetadata/`) |
| Tracking | derwin12/manual issues: #10 overview, #1-#9 one per chapter, #19 screenshot to-do (backlog #11, #15-#17 closed 2026-11-11), `wiki-review` issues from the watcher |
| Watcher | derwin12/manual `.github/workflows/xlights-wiki-watch.yml` + `.github/wiki-watch/watch.py` (every 48 h: syncs derwin12/xLights, opens a review issue) |
| Tools | `scripts/manual_to_wiki.py` (converter), `scripts/wiki/xl_capture.py` (drive/capture xLights), `scripts/wiki/wiki_issue_tick.py`, `scripts/wiki/wiki_screenshot_ages.py`, `scripts/wiki/wiki_screenshot_todo.py` (refreshes the screenshot to-do issue #19, keeping ticks and *keep* notes; in `wiki_issue_tick.py` covered.json, entries under non-link headings use the key `""`), `scripts/wiki/build_wiki_index.py` (regenerates the A-Z `Index` page) |

Done (2026-11-07): Controllers (#4), Layout (#5, 16/32 pages; 22 screenshots need show changes) and Sequencer (#6, 11/23 pages; 23 screenshots need sequence edits or missing content), Menus (#7, 27/27 pages, 2026-11-08). The whole branch was published to the official wiki on 2026-11-09 (user's choice); FPP Connect is now one page, `FPP-Connect` (`Tools-FPP-Connect` removed).

Menus lessons: Sequence Settings has only **Done** (Escape/X do nothing; Done with no changes is safe). Restore Backup and New Sequence need no sequence open (close it first; Don't Create Sequence cancels the wizard). Check Sequence opens in Chrome on the second monitor (grab x 1920-3840, crop off the bookmarks bar). Verify every dialog closed with a shot before the next click: a missed close sends later clicks into the dialog.

## Recipe for a chapter
1. **List the work.** Pages = the chapter issue's checklist. Backlog = entries under those pages in open `wiki-review` issues; screenshots = the chapter's section of #19. Save them to a scratch file.
2. **Draft from source, not memory.** For big chapters, spawn 1-2 general-purpose agents (split general pages / sub-types). Brief: read each current wiki page, find the UI in `src-ui-wx/` by grepping labels, use the backlog file, write drafts to the scratchpad (never the wiki), follow the conventions below, and report corrections + covered backlog entries (first ~8 words) + anything unverifiable. Spot-check 2 drafts yourself.
3. **Screenshots** (see below). Replace each `<!-- SCREENSHOT: ... -->` you can fill with `![alt](images/<chapter>/<name>.png)`; leave the rest as hidden markers.
4. **Copy drafts into the wiki and check:** every `](Page)` and `[[Page]]` exists, every `#anchor` matches a heading, every image file exists, no `{%`/TODO, every page has the marker. Run `python scripts/manual_to_wiki.py --section "" --dry-run`: rewritten pages must say `skip`.
   Then run `python scripts/wiki/build_wiki_index.py` so the A-Z `Index` page picks up new headings and settings (commit it with the pages).
5. **Commit on `manual-import-trial`, push to `staging`** (see git rules), and spot-check pages live (`curl` the wiki URL, count images/tables).
6. **Tick:** `python scripts/wiki/wiki_issue_tick.py --chapter-issue N --covered covered.json`. Then comment on the chapter issue: what changed, which screenshots remain and why.

## Page conventions
- `# Title`, a breadcrumb line (`[Chapter](Page) › **Title**`), GitHub alerts (`> [!NOTE]`/`[!TIP]`/`[!WARNING]`/`[!CAUTION]`), and tables for settings (Setting | Meaning) and menus (Item | What it does). Use exact UI labels from source.
- Keep good old prose and concept diagrams; drop old UI shots. Never leave visible TODOs.
- The last line, `<!-- maintained-in-wiki: updated for xLights <ver> from source (<files>); originally from manual <path> -->`, stops the converter from overwriting the page.
- Effect-* pages must match `resources/effectmetadata/*.json`.

## Screenshots: driving xLights
- **Ask first.** It takes over the user's mouse. Get a go-ahead, and have them clear other windows off xLights: grabs include whatever is on top, e.g. a Zoom chat.
- Use ShowFolderAI. ShowFolderQA has extra model types (Cube, Image, PolyLine, Sphere, Window Frame, Wreath). Switch through the Directories dialog favourites with **select + Switch Temporarily**. Double-clicking a favourite switches PERMANENTLY. When leaving QA, xLights asks to save load-time changes: answer **No**.
- Take a full shot first and read coordinates off it. Wait 2-3 s and move the mouse away (tooltips) before every capture. A panel shown for the first time can be captured half-drawn, so recapture before reporting a "display bug".
- Select a model with: filter box → ctrl+a → type name → **Enter** → click the first row. Scroll the property grid to the top (`scroll 200 750 3000`) or the Name row may be hidden.
- Property-grid dialogs: click the row first, then its `...` button. Rows shift after selection, so re-check positions.
- **Open → capture → Cancel/Escape. Never Save, never OK, never Undo blind.** Avoid edit-mode cells: a double-click on a SubModels node range edits it, and Escape then closes the whole dialog.
- The Download / Import Custom buttons arm a drag on the preview, which creates a temporary model and leaves Save red even when cancelled. Verify with `automation_client.get_models(include_groups=False)` and `call('getModel', model=...)` against the xml on disk.
- Mouse in a screen corner (pyautogui fail-safe), or the user interrupts: **stop** and check state with a shot only, no clicks.
- Blur private data (e.g. favourite folder names) before using a shot.
- At the end, verify: no dialog is open, Save is not red (or explain why), and the live models match disk.

## Wiki git rules (Windows)
The official wiki has a page named `xLights-Model-Migration:-2026.03-→-2026.04.md` (':' is illegal on Windows). It is excluded by sparse checkout. **Never `git rebase`/`reset`/`checkout` across commits there**: they fail half-way, reset segfaulted, and rebase staged a deletion of that page. To combine with remote edits:
```
git -c core.protectNTFS=false merge-tree --write-tree HEAD staging/master   # -> TREE
git commit-tree TREE -p HEAD -p staging/master -m "Merge ..."               # -> C
git update-ref refs/heads/manual-import-trial C
git -c core.protectNTFS=false read-tree HEAD
git -c core.protectNTFS=false update-index --skip-worktree -- "<that file>"
git checkout-index -f -- <changed files>
```
If `staging/master` is an ancestor of HEAD (`git merge-base --is-ancestor`), push directly. Never force-push over someone's wiki edit.

## Publishing to the official wiki
The branch was pushed live on 2026-11-09, so `manual-import-trial` and `origin/master` now track each other. Each later change: push to `staging` first, then `git push origin manual-import-trial:master` only with the user's go-ahead. Fetch origin first; if someone edited the live wiki, merge it in with the merge-tree recipe above (never force-push). The watcher now checks and links the official wiki (xLightsSequencer/xLights), not the test wiki.
