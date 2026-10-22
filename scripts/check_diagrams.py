#!/usr/bin/env python3
"""Fail when a diagram's committed files have drifted from what generates them.

AGENTS.md: change a diagram's declaration in docs/diagrams/specs.py and regenerate, never edit
the exported XML. This holds that rule in three parts:

1. Running specs.py reproduces every source it declares in src/, byte for byte, and src/ holds
   nothing else except the mm-* metamodel diagrams, which metamodels.py writes from a deploy-kit
   checkout CI does not have.
2. Every source has a PNG, and the draw.io XML the PNG embeds is the source, so a PNG never shows
   a diagram its source no longer declares.
3. Every PNG has a source.

    check_diagrams.py [--dir docs/diagrams]

Standard library only, so CI needs no draw.io.
"""

from __future__ import annotations

import argparse
import struct
import subprocess
import sys
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
# Diagrams metamodels.py writes; specs.py does not declare them.
METAMODEL_PREFIX = "mm-"


def embedded_xml(png: bytes) -> str | None:
    """The draw.io XML a PNG export embeds in its zTXt chunk, or None when it embeds none."""
    if not png.startswith(PNG_SIGNATURE):
        return None
    at = len(PNG_SIGNATURE)
    while at + 8 <= len(png):
        (length,) = struct.unpack(">I", png[at : at + 4])
        kind = png[at + 4 : at + 8]
        data = png[at + 8 : at + 8 + length]
        if kind == b"zTXt":
            keyword, rest = data.split(b"\0", 1)
            if keyword == b"mxGraphModel":
                # draw.io writes a raw deflate stream after the compression-method byte, and
                # URL-encodes the XML inside it.
                return urllib.parse.unquote(zlib.decompress(rest[1:], -15).decode("utf-8"))
        at += 12 + length
    return None


def same_xml(a: str, b: str) -> bool:
    try:
        return ET.canonicalize(a, strip_text=True) == ET.canonicalize(b, strip_text=True)
    except ET.ParseError:
        return False


def regenerate(diagrams: Path) -> dict[str, bytes]:
    """Every source specs.py declares, by file name, generated in a scratch directory."""
    with tempfile.TemporaryDirectory() as out:
        subprocess.run(
            [sys.executable, "-B", str(diagrams / "specs.py")],
            cwd=out,
            env={"PYTHONPATH": str(diagrams)},
            check=True,
            capture_output=True,
        )
        return {path.name: path.read_bytes() for path in Path(out).glob("*.drawio")}


def check(diagrams: Path, generated: dict[str, bytes]) -> list[str]:
    """Every drift between the generator, src/ and png/. Empty means in step."""
    src, png = diagrams / "src", diagrams / "png"
    sources = {path.name: path for path in sorted(src.glob("*.drawio"))}
    failures = []

    for name, content in sorted(generated.items()):
        if name not in sources:
            failures.append(f"{src / name}: specs.py declares it, but it is not committed; regenerate")
        elif sources[name].read_bytes() != content:
            failures.append(f"{src / name}: differs from what specs.py generates; regenerate, never edit the XML")
    for name in sources:
        if name not in generated and not name.startswith(METAMODEL_PREFIX):
            failures.append(f"{src / name}: specs.py does not declare it; remove it or declare it")

    for name, path in sources.items():
        image = png / (path.stem + ".png")
        if not image.exists():
            failures.append(f"{image}: missing; export it from {path}")
            continue
        xml = embedded_xml(image.read_bytes())
        if xml is None:
            failures.append(f"{image}: embeds no draw.io XML; export it with -e")
        elif not same_xml(xml, path.read_text(encoding="utf-8")):
            failures.append(f"{image}: shows a different diagram from {path}; export it again")
    for image in sorted(png.glob("*.png")):
        if image.stem + ".drawio" not in sources:
            failures.append(f"{image}: has no source in {src}; remove it")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the diagrams are in step with specs.py.")
    parser.add_argument("--dir", type=Path, default=Path("docs/diagrams"))
    args = parser.parse_args(argv)
    diagrams = args.dir.resolve()

    failures = check(diagrams, regenerate(diagrams))
    for failure in failures:
        print(f"::error::{failure}")
    if failures:
        return 1
    print(f"{len(list((diagrams / 'src').glob('*.drawio')))} diagrams are in step with specs.py")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
