> **⚠️ Beta:** This project is currently in beta. Features may change, and you may encounter bugs. Feedback and contributions are welcome!

# xLights MCP Server

An MCP (Model Context Protocol) server that analyzes music and generates [xLights](https://xlights.org/) light show sequences. Works with any MCP-compatible AI tool — [GitHub Copilot CLI](https://docs.github.com/en/copilot/github-copilot-in-the-cli), [Claude Desktop](https://claude.ai/download), [Cursor](https://cursor.sh), [VS Code + Copilot Chat](https://code.visualstudio.com/), [Windsurf](https://codeium.com/windsurf), [Cline](https://github.com/cline/cline), and more.

Give it an `.mp3`, and it will analyze the beats, song structure, and energy — then generate a valid `.xsq` sequence file with effects placed across all of your light models, synced to the music.

---

## What It Does

### 🎵 Audio Analysis
- **Beat & tempo detection** — identifies every beat, downbeat, and bar boundary
- **Song structure** — detects intro, verse, chorus, bridge, and outro sections
- **Frequency spectrum** — bass, mid, and high energy curves over time
- **Energy profiling** — loudness dynamics, peak detection, dynamic range
- **Source separation** — isolate vocals, drums, bass, and other stems via [Demucs](https://github.com/facebookresearch/demucs) (optional)

### 💡 Sequence Generation
- **Generates valid `.xsq` files** that open directly in xLights — no xLights GUI required during generation
- **Reads your actual show config** — knows your models, controllers, channel counts, and model types
- **Intelligent effect selection** — picks effects based on model type (arches get chases, trees get spirals, etc.) and musical features (beats → shockwaves, choruses → high energy, verses → gentle)
- **Theme-aware palettes** — Christmas (red/green/gold) and Halloween (orange/purple) color schemes
- **Three generation modes:**
  - **Automatic** — AI picks everything, you review in xLights
  - **Guided** — AI shows song structure, you choose effects per section
  - **Template** — define reusable effect recipes, AI places them on beat
- **Never overwrites** — existing sequences are safe; generated files get a `(generated N)` suffix

### 📦 Sequence Import & Remapping
- **Import community sequences** — take any `.xsq` or `.zip` package from the xLights community and remap it to your show layout
- **Intelligent model matching** — automatically maps imported models to yours by name, type, and pixel count
- **Zip package support** — extracts audio, video, shader, and image assets; rewrites hardcoded file paths
- **Singing model awareness** — singing face models only match to other singing models
- **Full mapping report** — see exactly what matched, how, and what was skipped
- **Manual overrides** — correct any mapping before the remapped sequence is generated

### 📡 FPP Integration
- **Check status** of your Falcon Pi Player
- **Upload sequences** (.fseq + audio) to FPP
- **Manage playlists** — list, start, stop
- Works with FPP's REST API

---

## Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** (recommended) or pip
- **ffmpeg** — for audio format handling (`brew install ffmpeg` on macOS, `apt install ffmpeg` on Linux)
- **xLights** — installed with at least one show folder configured

---

## Installation

### Step 1: Clone the repository

```bash
git clone https://github.com/JohnBreault/xlights-mcp-server.git
cd xlights-mcp-server
```

### Step 2: Create a virtual environment and install

```bash
uv venv
uv pip install -e .
```

**Optional extras for enhanced features:**

```bash
# Stem separation — isolates vocals/drums/bass for smarter sequencing (~2GB model download)
uv pip install -e ".[separation]"

# Lyrics/singing faces — transcribes vocals for lip-sync animation
uv pip install -e ".[lyrics]"

# Better beat detection
uv pip install -e ".[beats]"

# Everything
uv pip install -e ".[all]"
```

### Step 3: Show folder configuration

On first run, the server **auto-detects** your xLights show folders by scanning common locations:

| OS | Locations checked |
|----|-------------------|
| macOS | `~/Library/Mobile Documents/com~apple~CloudDocs/xLights/`, `~/Documents/xLights/` |
| Windows | `~/Documents/xLights/` |
| Linux | `~/Documents/xLights/`, `~/xLights/`, `/opt/xLights/` |

It looks for directories containing `xlights_rgbeffects.xml` (the file xLights creates in every show folder).

**If auto-detection doesn't find your folders**, create or edit `~/.xlights-mcp/config.json`:

```json
{
  "show_folders": {
    "christmas": "/path/to/your/xLights/Christmas",
    "halloween": "/path/to/your/xLights/Halloween"
  },
  "active_show": "christmas",
  "fpp": {
    "host": "fpp.local",
    "port": 80
  }
}
```

### Step 4: Connect to your AI tool

The server uses **stdio transport** — your AI tool launches it as a subprocess.

<details>
<summary><strong>GitHub Copilot CLI</strong></summary>

Add to `~/.copilot/mcp-config.json`:

```json
{
  "mcpServers": {
    "xlights": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/xlights-mcp-server", "xlights-mcp-server"]
    }
  }
}
```

Restart Copilot CLI after saving.
</details>

<details>
<summary><strong>Claude Desktop</strong></summary>

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "xlights": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/xlights-mcp-server", "xlights-mcp-server"]
    }
  }
}
```

Restart Claude Desktop after saving.
</details>

<details>
<summary><strong>VS Code + Copilot Chat</strong></summary>

Add to your VS Code `settings.json`:

```json
{
  "mcp": {
    "servers": {
      "xlights": {
        "command": "uv",
        "args": ["run", "--directory", "/path/to/xlights-mcp-server", "xlights-mcp-server"]
      }
    }
  }
}
```
</details>

<details>
<summary><strong>Cursor</strong></summary>

Add to Cursor MCP settings (Settings → MCP Servers → Add):

- **Name:** xlights
- **Command:** `uv`
- **Args:** `run --directory /path/to/xlights-mcp-server xlights-mcp-server`
</details>

<details>
<summary><strong>Other MCP clients</strong></summary>

Any tool that supports the [Model Context Protocol](https://modelcontextprotocol.io/) can use this server. Point it at:

```
command: uv
args: run --directory /path/to/xlights-mcp-server xlights-mcp-server
transport: stdio
```
</details>

Replace `/path/to/xlights-mcp-server` with the actual path where you cloned the repo.

---

## Usage

Once connected, interact with the server through natural language in your AI tool. Here are some example workflows:

### Explore your show

```
> List my xLights shows
> Switch to the Halloween show
> List all my light models
> Show me the controllers
> What sequences do I have?
> Inspect the "Deck The Halls" sequence
```

### Analyze a song

```
> Analyze the song ~/Music/Jingle Bell Rock.mp3
> Show me the song structure for ~/Music/Monster Mash.mp3
> Get the beat map for this song
> What's the energy profile look like?
```

### Generate a sequence

```
> Create a sequence for ~/Music/Jingle Bell Rock.mp3
> Create a sequence for ~/Music/Jingle Bell Rock.mp3 using red and green colors
> Preview what a sequence would look like for this song before creating it
```

When generating, you'll be asked to choose a mode:
- **auto** — fully automatic, AI picks effects and colors
- **guided** — see the song structure first, then choose effects per section
- **template** — apply saved effect recipes to detected sections

### Import a community sequence

```
> Import the sequence ~/Downloads/Holly Jolly Christmas SD.zip to my show
> Import ~/Downloads/Christmas Time.xsq and show me the model mapping
> Import this sequence but map "Arch Left" to my "Arches-1" model
```

The importer supports both standalone `.xsq` files and `.zip` packages (which include audio, video assets, and the source show's model data). It automatically matches models from the imported sequence to your layout using:
1. **Exact name match** → identical model names
2. **Similar words** → shared words like "snowflake", "arch", "tree"
3. **Model type** → same `display_as` type (e.g., both Arches)
4. **Pixel count** → within 70% of each other
5. **Manual overrides** → you choose specific mappings

### Manage FPP (when controllers are online)

```
> Check the FPP status
> List playlists on FPP
> Start the Christmas playlist
> Stop playback
```

---

<!-- TOOLS:START -->
## Available Tools

_This section is auto-generated by `scripts/gen_tools_reference.py`. Do not edit by hand._

### 🗂️ Show & Configuration

| Tool | Description |
|------|-------------|
| `list_shows` | List all configured xLights show folders. |
| `add_show_folder` | Add an xLights show folder by path. |
| `switch_show` | Switch the active xLights show folder. |

### 🔍 Sequence Inspection

| Tool | Description |
|------|-------------|
| `list_models` | List all light models in the active xLights show. |
| `list_controllers` | List all controllers configured in the active xLights show. |
| `list_sequences` | List all sequences (.xsq files) in the active show folder. |
| `inspect_sequence` | Inspect an existing xLights sequence file. |
| `list_timing_tracks` | List timing tracks (Beats, Sections, Lyrics, etc.) in a sequence. |
| `list_effects` | List all available xLights effects with descriptions. |

### ✏️ Sequence Editing (offline)

| Tool | Description |
|------|-------------|
| `add_effect` | Add an effect to a model in an existing xLights sequence. |
| `update_effect` | Update an existing effect in a sequence. Only fields you pass are changed. |
| `delete_effect` | Delete an effect from a sequence. |

### ⚡ Live xLights Automation

| Tool | Description |
|------|-------------|
| `xlights_status` | Check whether a running xLights instance is reachable for live tools. |
| `get_open_sequence` | Return info about the sequence currently open in xLights. |
| `render_frame` | Render a single preview frame of a sequence using a running xLights instance. |
| `render_clip` | Render a time-range video clip of a sequence using a running xLights instance. |
| `add_effect_live` | Add an effect via a running xLights instance, with real validation. |
| `clone_model_effects` | Copy all effects from one model onto another in a running xLights instance. |
| `save_sequence_live` | Save the currently-open sequence in a running xLights instance. |

### 🎵 Audio Analysis

| Tool | Description |
|------|-------------|
| `analyze_song` | Analyze a music file for light show sequencing. |
| `get_song_structure` | Get the verse/chorus/bridge structure of a song. |
| `get_beat_map` | Get beat and downbeat timestamps for a song. |
| `get_energy_profile` | Get energy and frequency band analysis for a song. |

### 💡 Sequence Generation

| Tool | Description |
|------|-------------|
| `create_sequence` | Create an xLights sequence from a music file. |
| `preview_plan` | Preview the sequence generation plan without creating a file. |

### 📡 FPP Integration

| Tool | Description |
|------|-------------|
| `fpp_status` | Check Falcon Pi Player connection status and current state. |
| `fpp_upload_sequence` | Upload a sequence (.fseq) and optional audio to Falcon Pi Player. |
| `fpp_list_playlists` | List all playlists on the Falcon Pi Player. |
| `fpp_start_playlist` | Start a playlist on the Falcon Pi Player. |
| `fpp_stop` | Stop current playback on the Falcon Pi Player. |

### 📸 Screenshots

| Tool | Description |
|------|-------------|
| `xlights_screenshot` | Capture the full xLights application window and save it as a PNG. |
| `xlights_screenshot_region` | Capture a named region of the xLights window and save it as a PNG. |
| `xlights_list_regions` | List the named capture regions available for xlights_screenshot_region. |
| `xlights_navigate_and_screenshot` | Navigate xLights to a named UI state, then capture a screenshot. |
| `xlights_list_scenes` | List the named navigation scenes available for xlights_navigate_and_screenshot. |
| `xlights_screenshot_floating_panel` | Capture a floating (undocked) xLights panel window by its title. |
| `xlights_annotate_screenshot` | Add callout annotations to a screenshot for use in documentation. |

### 📖 Wiki Management

| Tool | Description |
|------|-------------|
| `wiki_set_path` | Set the local path to the cloned xLights wiki repository. |
| `wiki_list_pages` | List all pages currently in the local xLights wiki. |
| `wiki_read_page` | Read the markdown content of a wiki page. |
| `wiki_write_page` | Write (create or overwrite) a wiki page with the given markdown content. |
| `wiki_screenshot_to_image` | Capture a named xLights scene and save it into the wiki images/ folder. |
| `wiki_status` | Show git status of the local wiki — which pages have been modified. |
| `wiki_commit_push` | Commit all local wiki changes and push them to GitHub. |
| `wiki_pull` | Pull latest changes from the remote wiki repository. |

### 🔧 Other

| Tool | Description |
|------|-------------|
| `create_beat_effect_sequence` | Create a sequence with a single effect repeated on beat-aligned intervals. |

_Total: 46 tools_
<!-- TOOLS:END -->

---

## How It Works

### Effect Selection Logic

The server maps **model types** to appropriate effects:

| Model Type | Best Effects |
|------------|-------------|
| Arches | SingleStrand, Chase, ColorWash, Morph |
| Tree | Spirals, Pinwheel, Meteors, Circles |
| Single Line | Chase, Morph, SingleStrand, Shimmer |
| Poly Line | Chase, SingleStrand, Twinkle, Morph |
| Window Frame | Marquee, ColorWash, On, Curtain |
| Custom shapes | Shockwave, Circles, Plasma, Twinkle, Warp |

And maps **musical features** to effect choices:

| Musical Feature | Effects |
|----------------|---------|
| Strong beats | Shockwave, Morph, Strobe |
| Rhythmic passages | SingleStrand, Chase, Bars, Marquee |
| High energy (chorus) | Chase, Meteors, SingleStrand |
| Low energy (verse) | Twinkle, Shimmer, ColorWash, Snowflakes |
| Sustained notes | Plasma, Pinwheel, Spirals, Galaxy |
| Transitions | Warp, Curtain, Morph |
| Intro/Outro | Curtain, ColorWash, Twinkle |

### File Format

Generated `.xsq` files are standard xLights XML containing:
- `<head>` — song metadata, media file path, duration, timing (25ms frames)
- `<ColorPalettes>` — themed color palettes for effects
- `<EffectDB>` — deduplicated effect parameter definitions
- `<DisplayElements>` — all models included in the sequence
- `<ElementEffects>` — effect placements per model, per layer, with timing

---

## Project Structure

```
xlights-mcp-server/
├── pyproject.toml
├── README.md
├── src/xlights_mcp/
│   ├── server.py              # MCP server entry point & tool definitions
│   ├── config.py              # Configuration management
│   ├── audio/
│   │   ├── analyzer.py        # Full analysis pipeline orchestrator
│   │   ├── beats.py           # Beat/tempo/onset detection (librosa + madmom)
│   │   ├── structure.py       # Song section detection (verse/chorus/bridge)
│   │   ├── spectrum.py        # Frequency band & energy analysis
│   │   └── separator.py       # Demucs stem separation (optional)
│   ├── xlights/
│   │   ├── show.py            # Show folder parser (networks + models XML)
│   │   ├── xsq_reader.py     # Parse existing .xsq sequences
│   │   ├── xsq_writer.py     # Generate .xsq XML files
│   │   ├── effects.py         # Effect library & model/music mappings
│   │   ├── palettes.py        # Color palette definitions & themes
│   │   └── models.py          # Data models (Controller, LightModel, etc.)
│   ├── sequencer/
│   │   └── engine.py          # Sequence generation engine (auto/guided/template)
│   └── fpp/
│       ├── client.py          # FPP REST API client
│       ├── upload.py          # Sequence upload to FPP
│       └── schedule.py        # Schedule management
└── tests/
```

---

## Troubleshooting

**MCP server not loading**
- Verify your MCP config file is valid JSON (no comments, no trailing commas)
- Check the `--directory` path points to the repo root (where `pyproject.toml` is)
- Restart your AI tool after config changes
- Test manually: `cd /path/to/xlights-mcp-server && uv run xlights-mcp-server` — should start without errors

**"No xLights show folders found"**
- Make sure xLights is installed and you've opened it at least once (it creates `xlights_rgbeffects.xml` in each show folder)
- If your show folder is in a non-standard location, add it to `~/.xlights-mcp/config.json`

**"No models found" error**
- Verify the show folder contains `xlights_networks.xml` and `xlights_rgbeffects.xml`
- Use `list_shows` to check which show is active and whether the path exists

**Audio analysis is slow**
- First run downloads librosa data (~10MB); subsequent runs are faster
- Demucs stem separation takes 30-60s per song on CPU; results are cached
- Without optional deps, analysis takes ~5s per song

**Generated sequence looks wrong in xLights**
- The `.xsq` is a starting point — tweak effects, timing, and palettes in xLights
- Use `inspect_sequence` to review what was generated before opening

**FPP connection fails**
- Verify FPP is powered on and on the same network
- Check the hostname/IP in `~/.xlights-mcp/config.json`
- FPP tools gracefully report connection errors; core generation works fully offline

---

## License

MIT
