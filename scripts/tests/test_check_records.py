from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts.check_records import main, violations

LESSONS = """# Lesson candidates

## Curation

| Id | Lesson | Verdict |
| --- | --- | --- |
| CS-1 | A kept lesson | Keep |
| DO-7 | A dropped lesson | Drop |
"""


class Tree:
    """A decisions folder, its register and a lessons file, in a temporary directory."""

    def __init__(self, case: unittest.TestCase) -> None:
        tmp = tempfile.TemporaryDirectory()
        case.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.decisions = self.root / "decisions"
        self.decisions.mkdir()
        self.lessons = self.root / "lessons.md"
        self.lessons.write_text(LESSONS)
        self.known = self.root / "known.txt"
        self.rows: list[tuple[int, str]] = []

    def row(self, number: int, status: str) -> None:
        self.rows.append((number, status))
        lines = ["| # | Record | Status |", "| --- | --- | --- |"]
        lines += [f"| {n} | Record {n} | {s} |" for n, s in self.rows]
        (self.decisions / "register.md").write_text("# The register\n\n" + "\n".join(lines) + "\n")

    def record(self, number: int, status: str, rests_on: str = "[]", lessons: str = "[]") -> None:
        self.row(number, status.capitalize())
        self.file(number, f"---\nstatus: {status}  # proposed | accepted | locked\nrests-on: {rests_on}\nlessons: {lessons}\n---\n\n# Record {number}\n")

    def file(self, number: int, text: str) -> None:
        (self.decisions / f"{number:04d}-record-{number}.md").write_text(text)

    def keys(self) -> list[str]:
        return [v.key for v in violations(self.decisions, self.lessons)]

    def run(self) -> tuple[int, str]:
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["--decisions", str(self.decisions), "--lessons", str(self.lessons), "--known", str(self.known)])
        return code, out.getvalue()


class StatusAgreesWithTheRegister(unittest.TestCase):
    def test_a_consistent_tree_has_no_violations(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted", lessons="[CS-1]")
        tree.record(2, "locked", rests_on="[1]")
        tree.record(3, "proposed", rests_on="[1, 2]")
        self.assertEqual(tree.keys(), [])

    def test_a_status_that_differs_from_the_row_is_reported(self) -> None:
        tree = Tree(self)
        tree.row(1, "Accepted")
        tree.file(1, "---\nstatus: proposed\nrests-on: []\nlessons: []\n---\n")
        self.assertEqual(tree.keys(), ["status 1"])

    def test_a_file_without_front_matter_has_no_status(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed")
        tree.file(1, "# Record 1\n")
        self.assertEqual(tree.keys(), ["status 1"])

    def test_front_matter_without_its_closing_fence_is_read_to_the_end(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed")
        tree.file(1, "---\nstatus: proposed\n")
        self.assertEqual(tree.keys(), [])

    def test_a_file_without_a_row_is_reported(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed")
        tree.file(1, "---\nstatus: proposed\n---\n")
        tree.file(9, "---\nstatus: proposed\n---\n")
        self.assertEqual(tree.keys(), ["unregistered 9"])


class RestsOnFormsNoCycle(unittest.TestCase):
    def test_a_rest_on_an_unknown_number_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "proposed", rests_on="[7]")
        self.assertEqual(tree.keys(), ["unknown-rest 1 7"])

    def test_a_rest_that_is_not_a_number_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "proposed", rests_on="[0024-x]")
        self.assertEqual(tree.keys(), ["unknown-rest 1 0024-x"])

    def test_a_cycle_is_reported_once_by_its_members(self) -> None:
        tree = Tree(self)
        tree.record(1, "proposed", rests_on="[3]")
        tree.record(2, "proposed", rests_on="[1]")
        tree.record(3, "proposed", rests_on="[2]")
        tree.record(4, "proposed", rests_on="[1]")
        self.assertEqual(tree.keys(), ["cycle 1,2,3"])

    def test_a_record_resting_on_itself_is_a_cycle(self) -> None:
        tree = Tree(self)
        tree.record(5, "proposed", rests_on="[5]")
        self.assertEqual(tree.keys(), ["cycle 5"])

    def test_a_later_number_is_allowed(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted", rests_on="[2]")
        tree.record(2, "accepted")
        self.assertEqual(tree.keys(), [])


class AcceptedRestsOnlyOnAccepted(unittest.TestCase):
    def test_an_accepted_record_on_a_proposed_one_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "proposed")
        tree.record(2, "accepted", rests_on="[1]")
        tree.record(3, "locked", rests_on="[1]")
        self.assertEqual(tree.keys(), ["accepted-on-proposed 2 1", "accepted-on-proposed 3 1"])

    def test_a_proposed_record_may_rest_on_anything(self) -> None:
        tree = Tree(self)
        tree.record(1, "proposed")
        tree.record(2, "proposed", rests_on="[1]")
        self.assertEqual(tree.keys(), [])

    def test_an_accepted_record_may_rest_on_a_row_without_a_file(self) -> None:
        tree = Tree(self)
        tree.row(1, "Accepted")
        tree.record(2, "accepted", rests_on="[1]")
        self.assertEqual(tree.keys(), ["no-file 1"])


class LessonsAreKept(unittest.TestCase):
    def test_an_unknown_and_a_dropped_lesson_are_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "proposed", lessons="[CS-1, DO-7, XX-9]")
        found = violations(tree.decisions, tree.lessons)
        self.assertEqual([v.key for v in found], ["lesson 1 DO-7", "lesson 1 XX-9"])
        self.assertIn("dropped", found[0].message)
        self.assertIn("no lesson", found[1].message)


class AcceptedRowsHaveFiles(unittest.TestCase):
    def test_an_accepted_row_without_a_file_is_reported(self) -> None:
        tree = Tree(self)
        tree.row(1, "Accepted")
        tree.row(2, "Locked")
        tree.row(3, "Proposed")
        self.assertEqual(tree.keys(), ["no-file 1", "no-file 2"])


class MergedRows(unittest.TestCase):
    def test_a_merged_row_needs_no_file_and_counts_for_nothing(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        tree.row(2, "Merged into 1")
        self.assertEqual(tree.keys(), [])

    def test_a_merged_row_that_keeps_its_file_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        tree.row(2, "Merged into 1")
        tree.file(2, "---\nstatus: accepted\n---\n")
        self.assertEqual(tree.keys(), ["merged-file 2"])

    def test_a_rest_on_a_merged_row_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        tree.row(2, "Merged into 1")
        tree.record(3, "accepted", rests_on="[2]")
        found = violations(tree.decisions, tree.lessons)
        self.assertEqual([v.key for v in found], ["rests-on-merged 3 2"])
        self.assertIn("rest on 1", found[0].message)

    def test_a_merge_into_a_missing_or_merged_row_is_reported(self) -> None:
        tree = Tree(self)
        tree.row(1, "Merged into 9")
        tree.row(2, "Merged into 1")
        self.assertEqual(tree.keys(), ["merged-target 1", "merged-target 2"])


class TheKnownListOnlyShrinks(unittest.TestCase):
    def setUp(self) -> None:
        self.tree = Tree(self)
        self.tree.row(1, "Accepted")

    def test_a_listed_violation_passes(self) -> None:
        self.tree.known.write_text("# Known violations\n\nno-file 1\n")
        code, out = self.tree.run()
        self.assertEqual(code, 0)
        self.assertIn("1 known violation left", out)

    def test_a_new_violation_fails(self) -> None:
        code, out = self.tree.run()
        self.assertEqual(code, 1)
        self.assertIn("::error file=", out)
        self.assertIn("[no-file 1]", out)

    def test_a_listed_violation_that_is_gone_fails(self) -> None:
        self.tree.known.write_text("no-file 1\nstatus 4\n")
        code, out = self.tree.run()
        self.assertEqual(code, 1)
        self.assertIn("status 4 no longer occurs", out)

    def test_a_clean_tree_without_a_list_passes(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        code, out = tree.run()
        self.assertEqual(code, 0)
        self.assertIn("the records keep the register's rules", out)


if __name__ == "__main__":
    unittest.main()
