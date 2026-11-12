# Session Context

## Current Task
Manual → wiki migration (skill `manual-to-wiki`). As of 2026-11-11, chapters #4, #6, #7 and #8 are done and live on the official wiki (last push 1f1f5ce). Remaining work is listed on derwin12/manual #10.

## Key Decisions
- Shots that need edits are taken in the throwaway F:\ShowFolderWiki; you switch to it through File › Recent Show Folders, which is a permanent switch. Effects are added through `automation_client.add_effect`, and the sequence is closed with `close_sequence(force=True)`. Nothing is ever saved.
- Push to staging first. Push to the official wiki only on the user's go-ahead, which was given for every push this session.
- Avoid copyrighted lyrics in images: crop the lyric rows and use public-domain songs (Jingle Bells).

## Next Steps
- #5 Layout (15 of 32 pages left): add Candy Cane, Channel Block, Circle, PolyLine, Label, Spinner and non-MH DMX models to ShowFolderWiki, then take the 29 needs-setup shots.
- #19: refresh the 39 pre-2022 Sequencer images (Layer Blending 15, Changing An Effect 7, Layer Settings 5). Run `scripts/wiki/wiki_screenshot_todo.py --issue 19` afterwards.
- Loose ends:
  - Pixel Editor won't paint: try it by hand.
  - LOR Enhanced Speed mismatch: 25000 vs 1000000.
  - Possible xLights bugs, posted on #6: getEffectSettings JSON escaping; addEffect allows overlapping effects; the MIDI chooser's title is wrong.

## Also in flight (details in memory + skills)
- Christmas Techno Mix (F:\ShowFolderQA) and Eclipse6 (F:\ShowFolderAI) are still waiting on the user.
