---
name: tuneto-model-effects
description: TuneTo matrix (35x10) radio-sign pattern for ShowMathew/ShowMathewH sequences; audio lives in <show>\Audio
metadata:
  node_type: memory
  type: project
  originSessionId: c0ebe2f0-d1fc-4825-9939-ac0a430c6ce9
  modified: 2026-11-21T23:35:48.972Z
---

Every media sequence in F:\ShowMathew (Christmas) and F:\ShowMathewH (Halloween) puts two full-length effects on the TuneTo model:
L1 Text "TITLE - ARTIST - TUNE TO 90.1FM" (6-6x6 Thin, speed 6, per-word colour, brightness 170) and L2 Marquee border (band 3, speed 1), both with song-themed colours. Halloween versions are title-only with fixed red/yellow/orange text.
Statics with no audio get no TuneTo. Audio is copied to <show>\Audio and mediaFile repointed (old source E:\2023\ShowFolder3D\Audio).
Christmas set done 2026-11-21 (14 seqs); script approach: text-insert into EffectDB/ColorPalettes/DisplayElements/ElementEffects.
Christmas L1 is now a Pictures banner (emoji + 6x6 Thin text + emoji) from Images/TuneTo/<seq>.png: tile-left, speed 0.375 (= Text speed 6), XC=100, TransparentBlack on so Marquee shows. User liked it.
Animation/static sequences (no audio) get "ENJOY THE LIGHTS - MORE MUSIC SOON ON 90.1FM" with a theme emoji (user chose this over "No Audio Available").
2026-11-21: USB stick I:\ShowMathew turned out to be FAILING (silent data corruption of xsq/fseq/mp4, chkdsk clean, xLights hangs). F:\ShowMathew is the trusted master (audio normalized to -16 LUFS by plain gain; originals in F:\ShowMathew_backup_audio_2026-11-21). Plan: rebuild the show onto a new stick from F:, verify byte-for-byte, re-render all 19. Script: scratchpad normalize_audio.py (gain-only, keeps format/bitrate).
Generator + sprites: F:\ShowMathew\scripts\tuneto\banners.py (python banners.py <out_dir>); tuneto_pictures.py swaps Text->Pictures.

Related: [[test-one-sequence-first]]
