from __future__ import annotations

import io
import struct
import tempfile
import unittest
import urllib.parse
import zlib
from contextlib import redirect_stdout
from pathlib import Path

from scripts.check_diagrams import PNG_SIGNATURE, check, embedded_xml, main, regenerate, same_xml

SOURCE = '<mxfile><diagram name="a"><mxGraphModel><root><mxCell id="0"/></root></mxGraphModel></diagram></mxfile>'
SPECS = f"""
open("a.drawio", "w").write({SOURCE!r})
"""


def chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + b"\0\0\0\0"


def png(xml: str | None, keyword: bytes = b"mxGraphModel") -> bytes:
    """A PNG as draw.io exports it: the XML URL-encoded, raw-deflated, in a zTXt chunk."""
    body = chunk(b"IHDR", b"\0" * 13)
    if xml is not None:
        deflate = zlib.compressobj(wbits=-15)
        packed = deflate.compress(urllib.parse.quote(xml).encode()) + deflate.flush()
        body += chunk(b"zTXt", keyword + b"\0\0" + packed)
    return PNG_SIGNATURE + body + chunk(b"IEND", b"")


class ReadingAnExport(unittest.TestCase):
    def test_the_embedded_xml_is_read_back(self) -> None:
        self.assertEqual(embedded_xml(png(SOURCE)), SOURCE)

    def test_a_png_without_the_chunk_embeds_nothing(self) -> None:
        self.assertIsNone(embedded_xml(png(None)))

    def test_a_ztxt_chunk_under_another_keyword_is_not_the_diagram(self) -> None:
        self.assertIsNone(embedded_xml(png(SOURCE, keyword=b"Comment")))

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
        (self.dir / "src").mkdir()
        (self.dir / "png").mkdir()
        (self.dir / "specs.py").write_text(SPECS)
        self.write("a", SOURCE, png(SOURCE))

    def write(self, name: str, source: str | None, image: bytes | None) -> None:
        if source is not None:
            (self.dir / "src" / f"{name}.drawio").write_text(source)
        if image is not None:
            (self.dir / "png" / f"{name}.png").write_bytes(image)

    def failures(self) -> list[str]:
        return check(self.dir, regenerate(self.dir))

    def test_diagrams_in_step_pass(self) -> None:
        self.assertEqual(self.failures(), [])

    def test_a_hand_edited_source_fails(self) -> None:
        self.write("a", SOURCE.replace('id="0"', 'id="9"'), None)
        [failure] = [f for f in self.failures() if "src" in f and "differs" in f]
        self.assertIn("never edit the XML", failure)

    def test_a_declared_source_not_committed_fails(self) -> None:
        (self.dir / "src" / "a.drawio").unlink()
        self.assertIn("not committed", " ".join(self.failures()))

    def test_a_source_specs_does_not_declare_fails(self) -> None:
        self.write("b", SOURCE, png(SOURCE))
        self.assertIn("does not declare it", " ".join(self.failures()))

    def test_a_metamodel_source_need_not_be_declared(self) -> None:
        self.write("mm-core", SOURCE, png(SOURCE))
        self.assertEqual(self.failures(), [])

    def test_a_missing_png_fails(self) -> None:
        (self.dir / "png" / "a.png").unlink()
        self.assertIn("missing; export it", " ".join(self.failures()))

    def test_a_png_without_embedded_xml_fails(self) -> None:
        self.write("a", None, png(None))
        self.assertIn("embeds no draw.io XML", " ".join(self.failures()))

    def test_a_stale_png_fails(self) -> None:
        self.write("a", None, png(SOURCE.replace('id="0"', 'id="9"')))
        self.assertIn("shows a different diagram", " ".join(self.failures()))

    def test_a_png_without_a_source_fails(self) -> None:
        self.write("c", None, png(SOURCE))
        self.assertIn("has no source", " ".join(self.failures()))

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


if __name__ == "__main__":
    unittest.main()
