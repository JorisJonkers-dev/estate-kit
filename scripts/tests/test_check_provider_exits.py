from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts.check_provider_exits import main

SECTION = "### The provider-and-exit table\n"
GOOD = """---
status: accepted
---

# A record

## Decision

""" + SECTION + """
| Store or key service | What it holds | Provider | Exit date |
| --- | --- | --- | --- |
| Backups | One Kopia repository | Scaleway Object Storage, EU-controlled | 2026-11-05 |
| Renders and host tags | Signed renders | ghcr, until the registry move | 2027-05-31 |
"""


class Record116(unittest.TestCase):
    """A temporary decisions directory holding record 116, to change per test."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.decisions = Path(tmp.name) / "docs" / "decisions"
        self.decisions.mkdir(parents=True)
        self.record = self.decisions / "0116-a-record.md"
        self.record.write_text(GOOD)

    def run_check(self) -> tuple[int, str]:
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["--decisions", str(self.decisions)])
        return code, out.getvalue()

    def test_a_store_listed_with_its_provider_and_exit_date_passes(self) -> None:
        code, out = self.run_check()
        self.assertEqual(code, 0)
        self.assertIn("every store names its provider and exit date", out)

    def test_a_store_listed_without_its_provider_fails(self) -> None:
        self.record.write_text(GOOD.replace(
            "| Renders and host tags | Signed renders | ghcr, until the registry move | 2027-05-31 |",
            "| Renders and host tags | Signed renders |  | 2027-05-31 |"))
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("listed without its provider", out)

    def test_a_store_listed_without_an_exit_date_fails(self) -> None:
        self.record.write_text(GOOD.replace(
            "| Renders and host tags | Signed renders | ghcr, until the registry move | 2027-05-31 |",
            "| Renders and host tags | Signed renders | ghcr |  |"))
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("listed without its exit date", out)

    def test_an_exit_date_not_written_yyyy_mm_dd_fails(self) -> None:
        for written in ("20270531", "2027-W22-2", "2027-5-31"):
            with self.subTest(written=written):
                self.record.write_text(GOOD.replace(
                    "| Renders and host tags | Signed renders | ghcr, until the registry move | 2027-05-31 |",
                    f"| Renders and host tags | Signed renders | ghcr | {written} |"))
                code, out = self.run_check()
                self.assertEqual(code, 1)
                self.assertIn("listed without its exit date", out)

    def test_an_exit_date_that_is_not_a_real_date_fails(self) -> None:
        self.record.write_text(GOOD.replace(
            "| Renders and host tags | Signed renders | ghcr, until the registry move | 2027-05-31 |",
            "| Renders and host tags | Signed renders | ghcr | 2027-02-30 |"))
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("listed without its exit date", out)

    def test_an_exit_date_that_is_not_a_calendar_date_fails(self) -> None:
        self.record.write_text(GOOD.replace(
            "| Renders and host tags | Signed renders | ghcr, until the registry move | 2027-05-31 |",
            "| Renders and host tags | Signed renders | ghcr | M5 |"))
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("listed without its exit date", out)

    def test_a_row_listed_without_its_store_fails(self) -> None:
        self.record.write_text(GOOD.replace(
            "| Backups | One Kopia repository | Scaleway Object Storage, EU-controlled | 2026-11-05 |",
            "|  | One Kopia repository | Scaleway Object Storage, EU-controlled | 2026-11-05 |"))
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("listed without its provider and exit date", out)

    def test_a_row_with_the_wrong_number_of_cells_fails(self) -> None:
        self.record.write_text(GOOD.replace(
            "| Renders and host tags | Signed renders | ghcr, until the registry move | 2027-05-31 |",
            "| Renders and host tags | Signed renders | 2027-05-31 |"))
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("does not match the header", out)

    def test_a_record_with_no_table_section_fails(self) -> None:
        self.record.write_text(GOOD.replace(SECTION, "### Another heading\n"))
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("names no provider-and-exit table", out)

    def test_a_table_section_with_no_table_fails(self) -> None:
        self.record.write_text(GOOD.replace(
            "| Store or key service | What it holds | Provider | Exit date |", "")
            .replace("| --- | --- | --- | --- |", "")
            .replace("| Backups | One Kopia repository | Scaleway Object Storage, EU-controlled | 2026-11-05 |", "")
            .replace("| Renders and host tags | Signed renders | ghcr, until the registry move | 2027-05-31 |", ""))
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("holds no table", out)

    def test_a_table_with_no_store_rows_fails(self) -> None:
        self.record.write_text(GOOD.replace(
            "| Store or key service | What it holds | Provider | Exit date |\n"
            "| --- | --- | --- | --- |\n"
            "| Backups | One Kopia repository | Scaleway Object Storage, EU-controlled | 2026-11-05 |\n"
            "| Renders and host tags | Signed renders | ghcr, until the registry move | 2027-05-31 |\n",
            "| Store or key service | What it holds | Provider | Exit date |\n"
            "| --- | --- | --- | --- |\n"))
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("lists no store", out)

    def test_a_header_without_a_provider_column_fails(self) -> None:
        self.record.write_text(GOOD.replace("Provider", "Supplier"))
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("names no Provider column", out)

    def test_a_header_without_an_exit_date_column_fails(self) -> None:
        self.record.write_text(GOOD.replace("Exit date", "Deadline"))
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("names no Exit date column", out)

    def test_a_decisions_directory_with_no_record_116_fails(self) -> None:
        self.record.unlink()
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("no record 116", out)


if __name__ == "__main__":
    unittest.main()
