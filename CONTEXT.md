# Session Context

## Current Task
Made storybook videos for Matrix-mini-left/right in the 9 totally dark ShowFolder3D sequences, wired them in, and committed everything (9fa7af0) with the Claude memory copied to `docs/claude-memory/` for the Mac.

## Key Decisions
- The same 25x24 video goes on both minis; videos are in `E:\2023\ShowFolder3D\Videos\* Storybook Mini.mp4`, and each sequence has a `.xsq.storybook.bak` backup.
- Sequences with no lyric track got word timing from faster-whisper (`scripts/stories/lyrics/*.json`; ffmpeg decode, VAD off).
- Excluded: PSA, radio sample, TuneTo, _template, shader showcase, ComeBackLater.

## Next Steps
- The user reviews the minis in xLights; retime or restage any scenes they flag.
- About 40 sequences show the minis only through whole-house groups; they could get their own stories.
- Re-sync `docs/claude-memory/` when new memories are added; resume the manual → wiki migration and the in-flight shader work.
