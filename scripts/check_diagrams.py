#!/usr/bin/env python3
"""Fail when a diagram's committed files have drifted from what generates them.

AGENTS.md: change a diagram's declaration in docs/diagrams/specs.py and regenerate, never edit
the exported XML. The pipeline is specs.py (or metamodels.py) -> raw/ -> build.py, which runs
draw.io -> src/ and png/. CI has no draw.io, so this holds the rule in four parts:

1. Running specs.py reproduces every source it declares in raw/, byte for byte, and raw/ holds
   nothing else except the mm-* metamodel sources, which metamodels.py writes from a deploy-kit
   checkout CI does not have.
2. diagrams.lock, which build.py writes, names the digest of every source and of the src/ file
   built from it. A source edited without a rebuild, or a src/ file edited by hand, no longer
   matches.
3. Every src/ file has a PNG, and the draw.io XML the PNG embeds is that file, so a PNG never
   shows a diagram its source no longer declares.
4. No PNG, src/ file or lock entry is left without a source.

    check_diagrams.py [--dir docs/diagrams]

Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
import subprocess
import sys
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
# Sources metamodels.py writes; specs.py does not declare them.
METAMODEL_PREFIX = "mm-"
SOURCE_SUFFIXES = (".mmd", ".drawio")


def inflate(data: bytes) -> bytes:
    """A zlib stream, or the raw deflate stream older draw.io releases wrote instead."""
    try:
        return zlib.decompress(data)
    except zlib.error:
        return zlib.decompress(data, -15)


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
                # After the compression-method byte: the XML, URL-encoded, compressed.
                return urllib.parse.unquote(inflate(rest[1:]).decode("utf-8"))
        at += 12 + length
    return None


def same_xml(a: str, b: str) -> bool:
    try:
        return ET.canonicalize(a, strip_text=True) == ET.canonicalize(b, strip_text=True)
    except ET.ParseError:
        return False


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
        return {path.name: path.read_bytes() for path in (Path(out) / "raw").iterdir()}


def read_lock(path: Path) -> dict[str, tuple[str, str]]:
    entries = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#"):
                name, raw, src = line.split()
                entries[name] = (raw, src)
    return entries


def check(diagrams: Path, generated: dict[str, bytes]) -> list[str]:
    """Every drift between the declarations, raw/, the lock, src/ and png/. Empty means in step."""
    raw_dir, src_dir, png_dir = diagrams / "raw", diagrams / "src", diagrams / "png"
    raws = {p.name: p for p in sorted(raw_dir.iterdir()) if p.suffix in SOURCE_SUFFIXES} if raw_dir.exists() else {}
    lock = read_lock(diagrams / "diagrams.lock")
    failures = []

    for name, content in sorted(generated.items()):
        if name not in raws:
            failures.append(f"{raw_dir / name}: specs.py declares it, but it is not committed; run specs.py")
        elif raws[name].read_bytes() != content:
            failures.append(f"{raw_dir / name}: differs from what specs.py generates; run specs.py and build.py")
    for name in raws:
        if name not in generated and not name.startswith(METAMODEL_PREFIX):
            failures.append(f"{raw_dir / name}: specs.py does not declare it; remove it or declare it")

    stems = {Path(name).stem: path for name, path in raws.items()}
    for stem, raw in sorted(stems.items()):
        src = src_dir / f"{stem}.drawio"
        if stem not in lock:
            failures.append(f"{raw}: not in diagrams.lock; run build.py")
            continue
        raw_digest, src_digest = lock[stem]
        if digest(raw) != raw_digest:
            failures.append(f"{raw}: changed since build.py last ran; run build.py")
        if not src.exists():
            failures.append(f"{src}: missing; run build.py")
        elif digest(src) != src_digest:
            failures.append(f"{src}: is not what build.py wrote; never edit the XML, rebuild it")
    for stem in sorted(set(lock) - set(stems)):
        failures.append(f"diagrams.lock: {stem} has no source; run build.py")

    sources = {p.stem: p for p in sorted(src_dir.glob("*.drawio"))}
    for stem, path in sources.items():
        if stem not in stems:
            failures.append(f"{path}: has no source in {raw_dir}; remove it")
        image = png_dir / f"{stem}.png"
        if not image.exists():
            failures.append(f"{image}: missing; run build.py")
            continue
        xml = embedded_xml(image.read_bytes())
        if xml is None:
            failures.append(f"{image}: embeds no draw.io XML; export it with -e")
        elif not same_xml(xml, path.read_text(encoding="utf-8")):
            failures.append(f"{image}: shows a different diagram from {path}; run build.py")
    for image in sorted(png_dir.glob("*.png")):
        if image.stem not in sources:
            failures.append(f"{image}: has no source in {src_dir}; remove it")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the diagrams are in step with their sources.")
    parser.add_argument("--dir", type=Path, default=Path("docs/diagrams"))
    args = parser.parse_args(argv)
    diagrams = args.dir.resolve()

    failures = check(diagrams, regenerate(diagrams))
    for failure in failures:
        print(f"::error::{failure}")
    if failures:
        return 1
    print(f"{len(list((diagrams / 'src').glob('*.drawio')))} diagrams are in step with their sources")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
