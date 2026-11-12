"""Put a dance crew on matrix models of an .xsq, one Pictures GIF per bar of the Beats track.

Each bar becomes a Pictures effect on a new top layer with Loop GIF off, so xLights
spreads the GIF's frames evenly over the bar and every pose lands on a beat whatever
the tempo. GIFs are drawn 1 pixel per LED (or an integer multiple) for the model's
size and written to <show>/Images/Dancers; identical bars share one file. Running it
again replaces the layer it made before.
"""

from __future__ import annotations

import hashlib
import io
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from xlights_mcp.sprites import dancers as d
from xlights_mcp.sprites.shader import MAX_BEATS, SHADER_NAME, build_shader, shader_settings
from xlights_mcp.sprites.stage import light_colours, stage_frame

IMG_SUB = "Images/Dancers"
BLACK_LEVEL = 30


def model_size(show: Path, name: str) -> tuple[int, int] | None:
    """Width and height in pixels of a Matrix model in the show's layout, or None."""
    root = ET.parse(show / "xlights_rgbeffects.xml").getroot()
    for m in root.iter("model"):
        if m.get("name") == name and m.get("DisplayAs") == "Matrix":
            strings = int(m.get("NumStrings", "1"))
            strands = int(m.get("StrandsPerString", "1"))
            nodes = int(m.get("NodesPerString", "0"))
            lines, per_line = strings * strands, nodes // max(strands, 1)
            return (lines, per_line) if m.get("Vertical") == "true" else (per_line, lines)
    return None


def fit_crew(size: tuple[int, int], dancers: int | None = None, scale: int | None = None) -> tuple[int, int]:
    """Largest integer scale whose crew still fits, and how many dancers fit side by side."""
    w, h = size
    if scale is None:
        n = dancers or 1
        scale = max(1, min(h // d.H, w // (d.W * n)))
    if dancers is None:
        dancers = max(1, min(9, w // (d.W * scale)))
    return dancers, scale


def read_beats(root: ET.Element, track: str = "Beats") -> list[tuple[int, int, str]]:
    for e in root.find("ElementEffects"):
        if e.get("type") == "timing" and e.get("name") == track:
            layer = e.find("EffectLayer")
            if layer is None:
                return []
            return [(int(x.get("startTime")), int(x.get("endTime")), x.get("label") or "")
                    for x in layer.findall("Effect")]
    raise ValueError(f"no timing track named {track!r}")


def group_bars(beats: list[tuple[int, int, str]], beats_per_bar: int = 4) -> list[list[tuple[int, int]]]:
    """Split beats into bars. Labels counting 1..n mark the downbeats; otherwise every beats_per_bar beats."""
    if beats and all(b[2].isdigit() for b in beats) and any(b[2] == "1" for b in beats):
        bars, cur = [], []
        for s, e, lab in beats:
            if lab == "1" and cur:
                bars.append(cur)
                cur = []
            cur.append((s, e))
        if cur:
            bars.append(cur)
        return bars
    pts = [(s, e) for s, e, _ in beats]
    return [pts[i:i + beats_per_bar] for i in range(0, len(pts), beats_per_bar)]


def gif_bytes(frames) -> bytes:
    buf = io.BytesIO()
    d.save_gif(frames, buf)
    return buf.getvalue()


def pic_settings(rel: str) -> str:
    s = {"B_CHOICE_BufferStyle": "Default",
         "E_CHECKBOX_LoopGIF": "0", "E_CHECKBOX_SuppressGIFBackground": "1",
         "E_CHECKBOX_Pictures_PixelOffsets": "0", "E_CHECKBOX_Pictures_WrapX": "0",
         "E_CHECKBOX_Pictures_TransparentBlack": "1", "E_TEXTCTRL_Pictures_TransparentBlack": str(BLACK_LEVEL),
         "E_CHOICE_Pictures_Direction": "none", "E_CHOICE_Scaling": "No Scaling",
         "E_SLIDER_Pictures_StartScale": "100", "E_SLIDER_Pictures_EndScale": "100",
         "E_TEXTCTRL_Pictures_Filename": rel,
         "E_TEXTCTRL_Pictures_FrameRateAdj": "1.0", "E_TEXTCTRL_Pictures_Speed": "1.0"}
    return ",".join(f"{k}={v}" for k, v in sorted(s.items()))


@dataclass
class Placement:
    model: str
    dancers: int
    scale: int
    bars: int
    files: int
    skipped: str | None = None


class Xsq:
    def __init__(self, path: Path):
        self.path = path
        self.tree = ET.parse(path)
        root = self.tree.getroot()
        self.root = root
        self.db, self.pals, self.eff = root.find("EffectDB"), root.find("ColorPalettes"), root.find("ElementEffects")
        self._db = {e.text: i for i, e in reversed(list(enumerate(self.db)))}
        white = "C_BUTTON_Palette1=#FFFFFF,C_CHECKBOX_Palette1=1"
        texts = [p.text for p in self.pals]
        if white not in texts:
            ET.SubElement(self.pals, "ColorPalette").text = white
            texts.append(white)
        self.palette = texts.index(white)

    def ref(self, settings: str) -> int:
        if settings not in self._db:
            ET.SubElement(self.db, "Effect").text = settings
            self._db[settings] = len(self.db) - 1
        return self._db[settings]

    def palette_ref(self, colours: list[tuple[int, int, int]]) -> int:
        """Index of a palette with these colours checked (added if the sequence lacks it)."""
        text = ",".join(f"C_BUTTON_Palette{i + 1}=#{r:02X}{g:02X}{b:02X},C_CHECKBOX_Palette{i + 1}=1"
                        for i, (r, g, b) in enumerate(colours))
        texts = [p.text for p in self.pals]
        if text not in texts:
            ET.SubElement(self.pals, "ColorPalette").text = text
            texts.append(text)
        return texts.index(text)

    def model(self, name: str, add: bool = False):
        el = next((e for e in self.eff if e.get("type") == "model" and e.get("name") == name), None)
        if el is None and add:
            disp = self.root.find("DisplayElements")
            ET.SubElement(disp, "Element", {"collapsed": "0", "type": "model", "name": name,
                                            "visible": "1", "active": "0"})
            el = ET.SubElement(self.eff, "Element", {"type": "model", "name": name})
        return el

    def strip_old(self, el, shader_name: str = SHADER_NAME, gifs: bool = True) -> bool:
        """Remove this tool's layer (the crew's by default), wherever it now sits: another tool may have
        stacked a layer above it. The crew and the band each find only their own layer."""
        def ours(e) -> bool:
            if e.get("name") not in ("Pictures", "Shader"):
                return False
            ref = int(e.get("ref", -1))
            text = (self.db[ref].text or "") if 0 <= ref < len(self.db) else ""
            return ((gifs and e.get("name") == "Pictures" and IMG_SUB in text)
                    or (e.get("name") == "Shader" and shader_name in text))

        for layer in el.findall("EffectLayer"):
            if any(ours(e) for e in layer.findall("Effect")):
                el.remove(layer)
                return True
        return False

    def has_video(self, el) -> bool:
        return el is not None and any(e.get("name") == "Video" for e in el.iter("Effect"))

    def drop_if_empty(self, el) -> None:
        """Take a model out of the sequence when it has no effects left (it was only there for the crew)."""
        if any(layer.findall("Effect") for layer in el.findall("EffectLayer")):
            return
        name = el.get("name")
        self.eff.remove(el)
        disp = self.root.find("DisplayElements")
        for e in [e for e in disp if e.get("type") == "model" and e.get("name") == name]:
            disp.remove(e)

    def save(self) -> None:
        ET.indent(self.tree, space="  ")
        self.tree.write(self.path, encoding="utf-8", xml_declaration=True)


def parse_section_map(spec: str | None) -> dict[str, str]:
    """'Intro=wave,Verse=robot' -> {'intro': 'wave', 'verse': 'robot'} (keys lower-case)."""
    out = {}
    for part in (spec or "").split(","):
        if part.strip():
            key, _, val = part.partition("=")
            if not val:
                raise ValueError(f"expected Name=value, got {part!r}")
            out[key.strip().lower()] = val.strip()
    return out


def section_key(label: str, keys) -> str | None:
    """The longest key that starts the label: 'Chorus 2' matches 'chorus' ('chorus 2' would win)."""
    lab = label.strip().lower()
    hits = [k for k in keys if lab.startswith(k)]
    return max(hits, key=len) if hits else None


@dataclass
class BarPlan:
    beats: list[tuple[int, int]]
    routine: str | None          # None: no dancers in this bar
    shirts: list[str] | None
    beat: int                    # beats since the routine (re)started
    dancers: int | None = None   # None: the default count


def plan_bars(bars, routine: str, shirts: list[str] | None, sections=None,
              section_routines: dict[str, str] | None = None,
              section_shirts: dict[str, list[str]] | None = None,
              section_dancers: dict[str, int] | None = None) -> list[BarPlan]:
    """Pick each bar's routine, colours and dancer count. With sections, a bar takes the settings of the
    section it starts in (by label prefix; routine 'none' means no dancers) and the routine restarts at
    every section change."""
    section_routines = section_routines or {}
    section_shirts = section_shirts or {}
    section_dancers = section_dancers or {}
    plans, beat, prev = [], 0, object()
    for bar in bars:
        r, sh, label, n = routine, shirts, None, None
        if sections:
            label = next((lab for s, e, lab in sections if s <= bar[0][0] < e), None)
            if label is not None:
                k = section_key(label, section_routines)
                if k:
                    r = section_routines[k]
                k = section_key(label, section_shirts)
                if k:
                    sh = section_shirts[k]
                k = section_key(label, section_dancers)
                if k:
                    n = section_dancers[k]
        if label != prev:
            beat, prev = 0, label
        plans.append(BarPlan(bar, None if r.lower() == "none" or n == 0 else r, sh, beat, n))
        beat += len(bar)
    return plans


MIN_PIECE_BEATS = 1.0     # a piece of a bar shorter than this (between pictures) is left empty


def busy_spans(el, names=("Pictures",)) -> list[tuple[int, int]]:
    """Merged time spans covered by these effects on the model's other layers (call after strip_old)."""
    spans = sorted((int(e.get("startTime")), int(e.get("endTime")))
                   for layer in el.findall("EffectLayer") for e in layer.findall("Effect") if e.get("name") in names)
    out: list[tuple[int, int]] = []
    for s, e in spans:
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def free_pieces(t0: int, t1: int, busy: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Parts of [t0, t1) not covered by the busy spans."""
    pieces, cur = [], t0
    for s, e in busy:
        if e <= cur or s >= t1:
            continue
        if s > cur:
            pieces.append((cur, s))
        cur = max(cur, e)
    if cur < t1:
        pieces.append((cur, t1))
    return pieces


def merge_sections(plans: list[BarPlan]) -> list[BarPlan]:
    """Join consecutive bars that continue the same routine, colours and count into one plan (one effect).
    A long section is split so no effect holds more than MAX_BEATS beats."""
    out: list[BarPlan] = []
    for p in plans:
        last = out[-1] if out else None
        if (last and p.routine and last.routine == p.routine and last.shirts == p.shirts
                and last.dancers == p.dancers and p.beat == last.beat + len(last.beats)
                and p.beats[0][0] == last.beats[-1][1] and len(last.beats) + len(p.beats) <= MAX_BEATS):
            out[-1] = BarPlan(last.beats + p.beats, last.routine, last.shirts, last.beat, last.dancers)
        else:
            out.append(p)
    return out


def place_crew(xsq: Path, show: Path, models: list[str], routine: str = "thriller", style: str = "unison",
               dancers: int | None = None, scale: int | None = None, shirts: list[str] | None = None,
               frames_per_beat: int = 1, track: str = "Beats", beats_per_bar: int = 4,
               start_s: float = 0.0, end_s: float | None = None, over_video: bool = False,
               figure: str = "male", section_track: str | None = None,
               section_routines: dict[str, str] | None = None,
               section_shirts: dict[str, list[str]] | None = None,
               stage: bool = False, shader: bool = False, smoothing: float = 0.35,
               energy: float = 1.0, section_dancers: dict[str, int] | None = None,
               per_section: bool = False, over_pictures: bool = False) -> list[Placement]:
    """Models already showing a Video effect are skipped (their crew layer, if any, removed) unless over_video.

    With section_track, each section can have its own routine and colours (see plan_bars). stage draws
    the crew at the matrix's size with a floor, beat-swapping spotlights and sparkles around it.

    shader places Shader effects running <show>/Shaders/Dance Crew.fs instead of GIFs: the same poses,
    with smooth moves between them (smoothing) and a bounce that follows the song's loudness (energy).
    Each bar's outfit colours become its palette. per_section (shader only) makes one effect per section
    instead of per bar, so a value curve can run across a whole section; poses then spread evenly over the
    section, which stays on the beat while the tempo is steady.

    Unless over_pictures, the crew steps aside while the model shows its own Pictures effects (accent and
    lyric pictures): the shader version stops at the picture and picks up mid-bar on the right beat after
    it; the GIF version leaves out any bar a picture touches.
    """
    if per_section and not shader:
        raise ValueError("per_section needs the shader (GIFs are made per bar)")
    sq = Xsq(xsq)
    bars = [b for b in group_bars(read_beats(sq.root, track), beats_per_bar)
            if b[0][0] >= start_s * 1000 and (end_s is None or b[-1][1] <= end_s * 1000)]
    if not bars:
        raise ValueError("no bars in the chosen time range")
    sections = read_beats(sq.root, section_track) if section_track else None
    plans = plan_bars(bars, routine, shirts, sections, section_routines, section_shirts, section_dancers)
    if per_section:
        plans = merge_sections(plans)
    for r in {p.routine for p in plans if p.routine}:
        d.timeline(r, 1)                                  # unknown routine/pose names fail before writing
    for p in plans:
        for c in p.shirts or []:
            d.colour(c)
    out_dir = show / IMG_SUB
    shader_path = show / "Shaders" / SHADER_NAME
    if shader:
        shader_path.parent.mkdir(parents=True, exist_ok=True)
        shader_path.write_text(build_shader(), encoding="utf-8")
    else:
        out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for name in models:
        size = model_size(show, name)
        if size is None:
            raise ValueError(f"{name}: not a Matrix model in the show's layout")
        if not over_video and sq.has_video(sq.model(name)):
            el = sq.model(name)
            if sq.strip_old(el):
                sq.drop_if_empty(el)
            results.append(Placement(name, 0, 0, 0, 0, skipped="has a Video effect"))
            continue
        el = sq.model(name, add=True)
        fits = {}
        for want in {p.dancers or dancers for p in plans if p.routine}:
            n, sc = fit_crew(size, want, scale)
            need = d.Crew([d.Dancer()] * n, scale=sc).size
            if need[0] > size[0] or need[1] > size[1]:
                raise ValueError(f"{name} is {size[0]}x{size[1]}; {n} dancers at scale {sc} need "
                                 f"{need[0]}x{need[1]}")
            fits[want] = (n, sc)
        sq.strip_old(el)
        busy = [] if over_pictures else busy_spans(el)
        layer = ET.Element("EffectLayer")
        files, placed = set(), 0
        for plan in plans:
            if plan.routine is None:
                continue
            n, sc = fits[plan.dancers or dancers]
            t0, t1 = plan.beats[0][0], plan.beats[-1][1]
            if shader:
                cols = [d.colour(c) for c in (plan.shirts or ["purple", "red", "teal"])]
                cols = (cols * 3)[:3]
                per_ms = len(plan.beats) / max(t1 - t0, 1)      # the shader spreads the beats evenly over the bar
                for a, b in free_pieces(t0, t1, busy):
                    nb = (b - a) * per_ms
                    if nb < MIN_PIECE_BEATS:
                        continue
                    st = shader_settings(shader_path.as_posix(), plan.routine, figure, style,
                                         plan.beat + (a - t0) * per_ms, nb, n, smoothing, energy, stage)
                    ET.SubElement(layer, "Effect", {
                        "ref": str(sq.ref(",".join(f"{k}={v}" for k, v in sorted(st.items())))), "name": "Shader",
                        "startTime": str(a), "endTime": str(b), "palette": str(sq.palette_ref(cols))})
                    placed += 1
                continue
            if free_pieces(t0, t1, busy) != [(t0, t1)]:
                continue
            crew = d.Crew(d.crew_from_style(n, style, plan.shirts, figure), scale=sc)
            poses = d.timeline(plan.routine, plan.beat + len(plan.beats))
            frames = d.bar_frames(crew, poses, plan.beat, len(plan.beats), frames_per_beat)
            if stage:
                cols = light_colours(crew)
                frames = [stage_frame(f, size, sc, cols, plan.beat + i // frames_per_beat, i % frames_per_beat)
                          for i, f in enumerate(frames)]
            data = gif_bytes(frames)
            extra = "-stage" if stage else ""
            fn = f"{plan.routine}-{style}-{figure}{extra}-{n}x{sc}-{hashlib.sha1(data).hexdigest()[:10]}.gif"
            if fn not in files:
                (out_dir / fn).write_bytes(data)
                files.add(fn)
            ET.SubElement(layer, "Effect", {"ref": str(sq.ref(pic_settings(f"{IMG_SUB}/{fn}"))), "name": "Pictures",
                                            "startTime": str(plan.beats[0][0]), "endTime": str(plan.beats[-1][1]),
                                            "palette": str(sq.palette)})
            placed += 1
        el.insert(0, layer)     # first EffectLayer is the top one
        most = max(fits.values(), default=(0, 0))
        results.append(Placement(name, most[0], most[1], placed, 1 if shader else len(files)))
    sq.save()
    return results


def remove_crew(xsq: Path, models: list[str]) -> list[str]:
    """Remove the crew layer from these models. A model left with no effects is taken out of the sequence."""
    sq = Xsq(xsq)
    removed = []
    for name in models:
        el = sq.model(name)
        if el is not None and sq.strip_old(el):
            sq.drop_if_empty(el)
            removed.append(name)
    sq.save()
    return removed
