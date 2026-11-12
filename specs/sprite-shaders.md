# Dance Crew and Skeleton Band (pixel-art sprites for matrices)

Built 2026-11-11, inspired by the skeleton/LED-panel scenes in a Game Changers AI video
(we draw our own characters; nothing is copied from it).

## What exists

| Piece | Where |
|---|---|
| Dancer poses, routines, figures (male/female/mixed), crew styles, GIF writer | `src/xlights_mcp/sprites/dancers.py` |
| Placement on an .xsq (Beats track, sections, counts, video skip, step aside for pictures) | `src/xlights_mcp/sprites/place.py` |
| Stage (floor, beat-swapping spotlights, sparkles) for GIFs + shared GLSL | `src/xlights_mcp/sprites/stage.py`, `shader.stage_glsl()` |
| Dance Crew shader generator (`Shaders/Dance Crew.fs`) | `src/xlights_mcp/sprites/shader.py` |
| Skeleton band sprites (guitarist, singer, drummer) | `src/xlights_mcp/sprites/band.py` |
| Band shader generator (`Shaders/Skeleton Band.fs`) and placement | `band_shader.py`, `band_place.py` |
| Drum hits from audio (shared with enhance_layout `--mh-hits`) | `src/xlights_mcp/audio/drums.py` |
| CLIs | `scripts/dance_crew.py`, `scripts/skeleton_band.py` |

The Python sprites are the source of truth. The shaders are generated from them and must
match them pixel for pixel (with smoothing and bounce off). That was checked with a
moderngl harness (GL 3.3, xLights' preamble) and glslangValidator (Vulkan rules); the
harness lived in the session scratchpad and is **not** in the repo yet (see below).

In the show (F:\ShowFolderAI): Crazy and Fast Car have the Dance Crew shader on Matrix;
`EL_Dan Bull Ive Got A Bone - Dance Crew.xsq` and `Luke Combs - Fast Car - Band Preview.xsq`
are preview copies. Backups before the dancers: `*.xsq.dancers.bak` (separate from the
`.xsq.bak` that enhance_layout regenerates from).

## xLights gotchas learned

- The user's build renders Shader effects through Vulkan (glslang). GLSL reserved words
  (`half`, `sample`, `input`, `filter`, ...) used as identifiers fail there and the effect
  shows a solid yellow box; desktop OpenGL (NVIDIA) accepts them. Tests grep for them.
- xLights' Shader panel shows no control for plain `long` inputs (`ShowParm()` in
  `src-core/effects/ShaderEffect.h`). Use choice lists (LABELS/VALUES) or float sliders,
  which are stored x100 (`E_SLIDER_SHADERXYZZY_<name>`).
- "xLights Audio2" as the ISF DESCRIPTION gives the shader the loudness in its image input.
- TIME restarts at each effect and XL_DURATION is the effect length: that is what keeps the
  per-bar effects on the beat. Shader_Speed or Lead-in other than 1.00 / 0 breaks the sync.

## Still to address

1. **Confirm in xLights**: reopen Crazy / Fast Car / the previews and check both shaders
   render (no yellow box) and the panel shows Dancers / Stage etc. The band shader has only
   been compiled with glslangValidator under Vulkan rules, never inside xLights.
2. **"Lead in frames 40 / Time Speed 1.80"** seen once in the panel: our effects store 0 and
   1.00. Find out whether that was a hand-made effect; if it shows on ours, beat sync breaks.
3. **Commit the shader check harness** (moderngl render + pixel compare against the Python
   sprites + glslangValidator Vulkan compile) as a dev script, so shader changes can be
   verified again. It needs moderngl and a glslangValidator binary (npm
   `glslang-validator-prebuilt-predownloaded` has one).
4. **lyric_images.py only looks at the top layer** for its own picture layer. The dancers now
   sit above it on Matrix, so re-running lyric_images would add a second picture layer
   instead of replacing it. Give it the "search every layer" fix `place.Xsq.strip_old` has.
5. **xLights bug to report/fix upstream**: `ShaderParm::ShowParm()` leaves out
   `SHADER_PARM_LONG`, and the LONG entry in `GetDynamicPropertiesJson` has no
   `settingPrefix`, so long inputs are invisible and their saved values may not round-trip.
6. **Jumps / hops** need one or two rows above the head: grow the sprite from 13x17 to 13x19
   (touches GIF sizes, fit_crew, the stage floor row and both shaders).
7. **More moves**: walk on/off (Offset X value curve), sit/kneel, a spin (needs side and back
   views).
8. **Band**: snare is fixed on beats 2 and 4 and the hi-hat on 8ths (could follow detected
   snare hits); bars longer than 4 beats lose slots past 16; the order is fixed (guitar,
   singer, drums); drum hits from audio take ~20 s per song (librosa) on every run.
9. **Remaining video ideas**: Beat Runner side-scroller (runner jumps on beats, coins on drum
   hits), parade/chase across the matrix, sound bars around a centre picture, beat-timed
   greeting text.
10. **MCP tools**: the dancers and band are scripts only; expose them as MCP tools if they
    should be usable from chat.
11. **Clean-up in the show folder**: decide whether to keep the two preview copies and the
    `.dancers.bak` files.
