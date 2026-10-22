from __future__ import annotations

import hashlib
import io
import struct
import tempfile
import unittest
import urllib.parse
import zlib
from contextlib import redirect_stdout
from pathlib import Path

from scripts.check_diagrams import PNG_SIGNATURE, check, embedded_xml, main, regenerate, same_xml

SOURCE = "sequenceDiagram\n    A->>B: hello\n"
BUILT = '<mxfile><diagram name="a"><mxGraphModel><root><mxCell id="0"/></root></mxGraphModel></diagram></mxfile>'
SPECS = f"""
import os
os.makedirs("raw", exist_ok=True)
open("raw/a.mmd", "w").write({SOURCE!r})
"""


def chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + b"\0\0\0\0"


def png(xml: str | None, keyword: bytes = b"mxGraphModel", raw_deflate: bool = False) -> bytes:
    """A PNG as draw.io exports it: the XML URL-encoded and compressed in a zTXt chunk."""
    body = chunk(b"IHDR", b"\0" * 13)
    if xml is not None:
        data = urllib.parse.quote(xml).encode()
        if raw_deflate:
            deflate = zlib.compressobj(wbits=-15)
            packed = deflate.compress(data) + deflate.flush()
        else:
            packed = zlib.compress(data)
        body += chunk(b"zTXt", keyword + b"\0\0" + packed)
    return PNG_SIGNATURE + body + chunk(b"IEND", b"")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class ReadingAnExport(unittest.TestCase):
    def test_the_embedded_xml_is_read_back(self) -> None:
        self.assertEqual(embedded_xml(png(BUILT)), BUILT)

    def test_a_raw_deflate_stream_from_older_draw_io_is_read_back(self) -> None:
        self.assertEqual(embedded_xml(png(BUILT, raw_deflate=True)), BUILT)

    def test_a_png_without_the_chunk_embeds_nothing(self) -> None:
        self.assertIsNone(embedded_xml(png(None)))

    def test_a_ztxt_chunk_under_another_keyword_is_not_the_diagram(self) -> None:
        self.assertIsNone(embedded_xml(png(BUILT, keyword=b"Comment")))

    def test_a_file_that_is_not_a_png_embeds_nothing(self) -> None:
        self.assertIsNone(embedded_xml(b"GIF89a"))

    def test_xml_compares_by_content_not_by_bytes(self) -> None:
        self.assertTrue(same_xml('<a x="1"  y="2"/>', "<a y='2' x='1'></a>"))

    def test_xml_that_does_not_parse_is_never_the_same(self) -> None:
        self.assertFalse(same_xml("<a>", "<a>"))


class Diagrams(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        for sub in ("raw", "src", "png"):
            (self.dir / sub).mkdir()
        (self.dir / "specs.py").write_text(SPECS)
        self.add("a", ".mmd", SOURCE, BUILT)

    def add(self, stem: str, suffix: str, source: str, built: str, lock: bool = True) -> None:
        (self.dir / "raw" / f"{stem}{suffix}").write_text(source)
        (self.dir / "src" / f"{stem}.drawio").write_text(built)
        (self.dir / "png" / f"{stem}.png").write_bytes(png(built))
        if lock:
            with (self.dir / "diagrams.lock").open("a") as f:
                f.write(f"{stem} {sha(source)} {sha(built)}\n")

    def failures(self) -> str:
        return "\n".join(check(self.dir, regenerate(self.dir)))

    def test_diagrams_in_step_pass(self) -> None:
        self.assertEqual(self.failures(), "")

    def test_a_lock_comment_is_ignored(self) -> None:
        with (self.dir / "diagrams.lock").open("a") as f:
            f.write("# a comment\n\n")
        self.assertEqual(self.failures(), "")

    def test_a_source_edited_by_hand_fails(self) -> None:
        (self.dir / "raw" / "a.mmd").write_text(SOURCE + "    B->>A: hi\n")
        failures = self.failures()
        self.assertIn("differs from what specs.py generates", failures)
        self.assertIn("changed since build.py last ran", failures)

    def test_a_declared_source_not_committed_fails(self) -> None:
        (self.dir / "raw" / "a.mmd").unlink()
        self.assertIn("not committed", self.failures())

    def test_a_source_specs_does_not_declare_fails(self) -> None:
        self.add("b", ".drawio", BUILT, BUILT)
        self.assertIn("does not declare it", self.failures())

    def test_a_metamodel_source_need_not_be_declared(self) -> None:
        self.add("mm-core", ".mmd", SOURCE, BUILT)
        self.assertEqual(self.failures(), "")

    def test_a_source_never_built_fails(self) -> None:
        self.add("mm-new", ".mmd", SOURCE, BUILT, lock=False)
        self.assertIn("not in diagrams.lock", self.failures())

    def test_a_missing_built_file_fails(self) -> None:
        (self.dir / "src" / "a.drawio").unlink()
        self.assertIn("missing; run build.py", self.failures())

    def test_a_built_file_edited_by_hand_fails(self) -> None:
        edited = BUILT.replace('id="0"', 'id="9"')
        (self.dir / "src" / "a.drawio").write_text(edited)
        (self.dir / "png" / "a.png").write_bytes(png(edited))
        self.assertIn("never edit the XML", self.failures())

    def test_a_lock_entry_without_a_source_fails(self) -> None:
        with (self.dir / "diagrams.lock").open("a") as f:
            f.write(f"gone {sha('x')} {sha('y')}\n")
        self.assertIn("gone has no source", self.failures())

    def test_a_built_file_without_a_source_fails(self) -> None:
        (self.dir / "src" / "c.drawio").write_text(BUILT)
        (self.dir / "png" / "c.png").write_bytes(png(BUILT))
        self.assertIn("c.drawio: has no source", self.failures())

    def test_a_missing_png_fails(self) -> None:
        (self.dir / "png" / "a.png").unlink()
        self.assertIn("a.png: missing", self.failures())

    def test_a_png_without_embedded_xml_fails(self) -> None:
        (self.dir / "png" / "a.png").write_bytes(png(None))
        self.assertIn("embeds no draw.io XML", self.failures())

    def test_a_stale_png_fails(self) -> None:
        (self.dir / "png" / "a.png").write_bytes(png(BUILT.replace('id="0"', 'id="9"')))
        self.assertIn("shows a different diagram", self.failures())

    def test_a_png_without_a_built_file_fails(self) -> None:
        (self.dir / "png" / "d.png").write_bytes(png(BUILT))
        self.assertIn("d.png: has no source", self.failures())

    def test_main_reports_failures_as_error_annotations(self) -> None:
        (self.dir / "png" / "a.png").unlink()
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["--dir", str(self.dir)]), 1)
        self.assertTrue(out.getvalue().startswith("::error::"))

    def test_main_passes_diagrams_in_step(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["--dir", str(self.dir)]), 0)
        self.assertIn("1 diagrams are in step", out.getvalue())


class AnEmptyDirectory(unittest.TestCase):
    def test_no_raw_directory_reports_every_declared_source_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "specs.py").write_text(SPECS)
            (d / "src").mkdir()
            (d / "png").mkdir()
            self.assertIn("not committed", "\n".join(check(d, regenerate(d))))


if __name__ == "__main__":
    unittest.main()
