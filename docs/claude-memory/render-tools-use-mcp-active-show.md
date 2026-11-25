---
name: render-tools-use-mcp-active-show
description: render_frame/render_model_frame open <MCP active show>/<name>.xsq; switch_show first or a same-named sequence in another folder gets rendered
metadata:
  node_type: memory
  type: reference
  originSessionId: 8ebe5222-ad00-4409-a649-b3280c511349
  modified: 2026-11-24T22:08:27.705Z
---

The xlights MCP render tools (render_frame, render_model_frame, render_clip) build the path as `config.active_show_path / f"{sequence_name}.xsq"` and ask xLights to open it. If the MCP active show is not the folder you edited, xLights opens the same-named sequence from the other folder (2026-11-24: Choosin Texas existed in both F:\ShowFolderAI and E:\2023\ShowFolder3D; renders came back black because the AI copy has no AA Mega Tree models). The user spotted it.

**How to apply:** before rendering a sequence, `switch_show` to the folder that holds it, and confirm with `get_open_sequence` (its `fullseq` shows the real path). All-black model frames are a sign of the wrong file, not of a broken effect.
