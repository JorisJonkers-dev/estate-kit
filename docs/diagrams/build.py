#!/usr/bin/env python3
"""Turn every source in raw/ into src/<name>.drawio and png/<name>.png, and record both in
diagrams.lock.

    python3 specs.py                      # regenerate raw/ from the declarations
    python3 metamodels.py <deploy-kit>    # regenerate raw/mm-* from deploy-kit's Ecore files
    DRAWIO=<draw.io binary> python3 build.py [name ...]

Needs draw.io Desktop 32 or later, which converts Mermaid and runs ELK layouts. For each diagram:

1. draw.io converts the Mermaid source, or lays out the XML source with ELK;
2. this script adds the header, swaps the tone sentinels for light-dark() colours and sets one font;
3. draw.io exports the PNG in the dark theme, with the diagram embedded so it stays editable.

diagrams.lock holds the digest of each source and of the src/ file built from it. CI cannot run
draw.io, so it checks the lock instead: a source edited without rebuilding no longer matches.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from gen import INK, PAPER, SENTINELS, TONES

HERE = Path(__file__).resolve().parent
RAW, SRC, PNG, LOCK = HERE / "raw", HERE / "src", HERE / "png", HERE / "diagrams.lock"
DRAWIO = os.environ.get("DRAWIO", "/Applications/draw.io.app/Contents/MacOS/draw.io")
FONT = re.compile(r"fontFamily=[^;]*;")
LABEL_BACKGROUND = re.compile(r"labelBackgroundColor=[^;]*;")
# Mermaid entity codes its class parser leaves undecoded, with or without their semicolon.
ENTITY = re.compile(r"#(lt|gt);?")
ACTOR_WIDTH = 40
MXFILE_NOISE = ("host", "modified", "agent", "etag", "version", "type", "compressed", "title", "layout")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def drawio(*args: str) -> None:
    subprocess.run([DRAWIO, *args], check=True, capture_output=True)


def header(raw: Path) -> tuple[str, str | None]:
    """The title, and for an XML source its layout."""
    text = raw.read_text(encoding="utf-8")
    if raw.suffix == ".mmd":
        lines = text.splitlines()
        if not lines[0].startswith("%% title: "):
            raise ValueError(f"{raw}: the first line must be '%% title: ...'")
        layout = lines[1][len("%% layout: "):] if lines[1].startswith("%% layout: ") else None
        return lines[0][len("%% title: "):], layout
    root = ET.fromstring(text)
    return root.get("title", ""), root.get("layout") or None


def restyle(style: str) -> str:
    style = FONT.sub("", style) + "fontFamily=Helvetica;"
    if LABEL_BACKGROUND.search(style):
        style = LABEL_BACKGROUND.sub("", style) + f"labelBackgroundColor={PAPER};"
    for tone, (fill, stroke) in SENTINELS.items():
        style = style.replace(fill, TONES[tone][0]).replace(stroke, TONES[tone][1])
    return style


def cells(root: ET.Element):
    """Every mxCell, with the label it shows (a UserObject carries it for Mermaid's cells)."""
    for el in root.iter():
        if el.tag == "mxCell":
            yield el
        elif el.tag == "UserObject":
            inner = el.find("mxCell")
            if inner is not None:
                yield inner


def finish(laid_out: Path, name: str, title: str) -> bytes:
    tree = ET.parse(laid_out)
    mxfile = tree.getroot()
    for key in MXFILE_NOISE:
        mxfile.attrib.pop(key, None)
    diagram = mxfile.find("diagram")
    diagram.set("id", name)
    diagram.set("name", name)
    model = diagram.find("mxGraphModel")
    for key in ("grid", "page"):
        model.set(key, "0")

    for el in model.iter():
        for key in ("style", "mermaidBaseStyle"):
            if key in el.attrib:
                el.set(key, restyle(el.get(key)))
        for key in ("value", "label", "mermaidBaseValue"):
            if key in el.attrib:
                el.set(key, ENTITY.sub(lambda m: "<" if m.group(1) == "lt" else ">", el.get(key)))

    # draw.io widens a node to its label before ELK places it. An actor's label sits below the
    # figure, so that only stretches the figure: put it back to its width, about the same centre.
    for cell in cells(model):
        if "shape=umlActor" in cell.get("style", ""):
            geo = cell.find("mxGeometry")
            w = float(geo.get("width", ACTOR_WIDTH))
            geo.set("x", f"{float(geo.get('x', 0)) + (w - ACTOR_WIDTH) / 2:g}")
            geo.set("width", f"{ACTOR_WIDTH:g}")

    # The header sits above everything at the top level.
    left, top, right = None, None, None
    for cell in cells(model):
        if cell.get("parent") != "1" or cell.get("vertex") != "1":
            continue
        geo = cell.find("mxGeometry")
        x, y = float(geo.get("x", 0)), float(geo.get("y", 0))
        w = float(geo.get("width", 0))
        left = x if left is None else min(left, x)
        top = y if top is None else min(top, y)
        right = x + w if right is None else max(right, x + w)
    # Edges can be routed above the shapes, so their waypoints count too.
    for point in model.iter("mxPoint"):
        if point.get("as") is None:
            y = float(point.get("y", 0))
            top = y if top is None else min(top, y)
    root = model.find("root")
    title_cell = ET.SubElement(root, "mxCell", {
        "id": "header",
        "value": title,
        "style": f"text;html=1;whiteSpace=wrap;align=left;verticalAlign=middle;fontSize=20;fontStyle=1;"
                 f"fontColor={INK};fontFamily=Helvetica;",
        "vertex": "1",
        "parent": "1",
    })
    ET.SubElement(title_cell, "mxGeometry", {
        "x": f"{left or 0:g}", "y": f"{(top or 0) - 64:g}",
        "width": f"{max(480, (right or 0) - (left or 0)):g}", "height": "36", "as": "geometry",
    })
    ET.indent(tree, space="  ")
    return ET.tostring(mxfile, encoding="utf-8") + b"\n"


def build(raw: Path) -> tuple[str, str, str]:
    name = raw.stem
    title, layout = header(raw)
    with tempfile.TemporaryDirectory() as tmp:
        laid_out = Path(tmp) / f"{name}.drawio"
        if raw.suffix == ".mmd":
            source = Path(tmp) / f"{name}.mmd"
            body = [line for line in raw.read_text(encoding="utf-8").splitlines() if not line.startswith("%% ")]
            source.write_text("\n".join(body) + "\n", encoding="utf-8")
            drawio("-x", "-f", "xml", "-u", "-o", str(laid_out), str(source))
            if layout:
                drawio("-x", "-f", "xml", "-u", "--layout", layout, "-o", str(laid_out), str(laid_out))
        else:
            drawio("-x", "-f", "xml", "-u", "--normalize", *(["--layout", layout] if layout else []),
                   "-o", str(laid_out), str(raw))
        (SRC / f"{name}.drawio").write_bytes(finish(laid_out, name, title))
    drawio("-x", "-f", "png", "-e", "-s", "2", "-b", "24", "--theme", "dark",
           "-o", str(PNG / f"{name}.png"), str(SRC / f"{name}.drawio"))
    return name, digest(raw), digest(SRC / f"{name}.drawio")


def read_lock() -> dict[str, tuple[str, str]]:
    if not LOCK.exists():
        return {}
    entries = {}
    for line in LOCK.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            name, raw, src = line.split()
            entries[name] = (raw, src)
    return entries


def write_lock(entries: dict[str, tuple[str, str]]) -> None:
    lines = ["# name  sha256(raw/<name>.*)  sha256(src/<name>.drawio). Written by build.py; checked in CI."]
    lines += [f"{name} {raw} {src}" for name, (raw, src) in sorted(entries.items())]
    LOCK.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(names: list[str]) -> int:
    SRC.mkdir(exist_ok=True)
    PNG.mkdir(exist_ok=True)
    raws = sorted(p for p in RAW.iterdir() if p.suffix in (".mmd", ".drawio"))
    if names:
        raws = [p for p in raws if p.stem in names]
        missing = set(names) - {p.stem for p in raws}
        if missing:
            print(f"no source for {', '.join(sorted(missing))}", file=sys.stderr)
            return 2
    entries = read_lock()
    with ThreadPoolExecutor(max_workers=4) as pool:
        for name, raw, src in pool.map(build, raws):
            entries[name] = (raw, src)
            print(f"built {name}")
    present = {p.stem for p in RAW.iterdir()}
    write_lock({n: e for n, e in entries.items() if n in present})
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
