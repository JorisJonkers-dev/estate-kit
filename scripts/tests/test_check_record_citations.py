from __future__ import annotations

import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts.check_record_citations import findings, main


class FindingBareCitations(unittest.TestCase):
    def test_the_bare_forms_are_found(self) -> None:
        for text in ("see ADR 0012", "per ADR-12", "as ADR #3 says", "record 7 decides", "Record-0042"):
            self.assertEqual(len(findings(text)), 1, text)

    def test_the_line_and_citation_are_reported(self) -> None:
        self.assertEqual(findings("one\ntwo, per ADR 0012\n"), [(2, "ADR 0012")])

    def test_a_citation_inside_a_link_is_not_bare(self) -> None:
        self.assertEqual(findings("as [ADR 0012](docs/decisions/0012-x.md) decides"), [])

    def test_a_citation_in_a_code_span_or_fence_is_skipped(self) -> None:
        self.assertEqual(findings("`ADR 0012`\n```\nrecord 7\n```\n~~~\nADR-1\n~~~\n"), [])

    def test_text_after_a_closed_fence_is_checked_again(self) -> None:
        self.assertEqual(findings("```\nx\n```\nrecord 7\n"), [(4, "record 7")])

    def test_ordinary_numbers_and_plurals_are_not_citations(self) -> None:
        self.assertEqual(findings("Records 42 onwards. 45 lessons. recorded 3 times. ADRs 1 to 4."), [])


class RunningTheCommand(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(tmp.name)
        subprocess.run(["git", "init", "-q"], check=True)
        Path("good.md").write_text("[ADR 1](docs/decisions/0001-x.md)\n")
        Path("bad.md").write_text("see ADR 1\n")
        Path("untracked.md").write_text("see ADR 2\n")
        subprocess.run(["git", "add", "good.md", "bad.md"], check=True)

    def test_every_tracked_markdown_file_is_read_by_default(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main([]), 1)
        self.assertEqual(out.getvalue().count("::error"), 1)
        self.assertIn("file=bad.md,line=1", out.getvalue())

    def test_named_files_are_read_instead(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["good.md"]), 0)
        self.assertIn("every record is cited by link", out.getvalue())


if __name__ == "__main__":
    unittest.main()
