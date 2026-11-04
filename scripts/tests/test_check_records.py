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


CHECKS = """# The page

## The checks

| Check | Fails when | Records | Runs in | Status |
| --- | --- | --- | --- | --- |
| Records | something | 1 | CI | verified |
| Links | something | 1 | CI | implemented |
| `cargo xtask known` | something else | 1 | xtask | planned |
| Tenant database name test | something | 1 | none | retired |

## Next section

| Not a check | x | x | x | x |
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
        self.checks = self.root / "checks.md"
        self.checks.write_text(CHECKS)
        self.rows: list[tuple[int, str, str]] = []  # (number, status, enforcement)

    def row(self, number: int, status: str, enforcement: str = "") -> None:
        self.rows.append((number, status, enforcement))
        lines = ["| # | Record | Status | Enforcement |", "| --- | --- | --- | --- |"]
        lines += [f"| {n} | Record {n} | {s} | {e} |" for n, s, e in self.rows]
        (self.decisions / "register.md").write_text("# The register\n\n" + "\n".join(lines) + "\n")

    def record(
        self,
        number: int,
        status: str,
        rests_on: str = "[]",
        lessons: str = "[]",
        amends: str = "[]",
        supersedes: str = "[]",
        enforcement: str = "verified",
    ) -> None:
        self.row(number, status.capitalize(), enforcement)
        self.file(
            number,
            f"---\nstatus: {status}  # proposed | accepted | locked\nrests-on: {rests_on}\n"
            f"amends: {amends}\nsupersedes: {supersedes}\nlessons: {lessons}\n---\n\n# Record {number}\n",
        )

    def file(self, number: int, text: str, confirmation: str | None = "Held by the **Records** check.") -> None:
        if confirmation is not None:
            text += f"\n## Confirmation\n\n{confirmation}\n"
        (self.decisions / f"{number:04d}-record-{number}.md").write_text(text)

    def keys(self) -> list[str]:
        return [v.key for v in violations(self.decisions, self.lessons, self.checks)]

    def run(self) -> tuple[int, str]:
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["--decisions", str(self.decisions), "--lessons", str(self.lessons), "--checks", str(self.checks)])
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
        tree.row(1, "Accepted", "verified")
        tree.file(1, "---\nstatus: proposed\nrests-on: []\nlessons: []\n---\n")
        self.assertEqual(tree.keys(), ["status 1"])

    def test_a_file_without_front_matter_has_no_status(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed", "verified")
        tree.file(1, "# Record 1\n")
        self.assertEqual(tree.keys(), ["status 1"])

    def test_front_matter_without_its_closing_fence_is_read_to_the_end(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed", "verified")
        tree.file(1, "---\nstatus: proposed\n")
        self.assertEqual(tree.keys(), [])

    def test_a_file_without_a_row_is_reported(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed", "verified")
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
        found = violations(tree.decisions, tree.lessons, tree.checks)
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
        tree.row(2, "Merged into 1", "")
        self.assertEqual(tree.keys(), [])

    def test_a_merged_row_that_keeps_its_file_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        tree.row(2, "Merged into 1", "")
        tree.file(2, "---\nstatus: accepted\n---\n")
        self.assertEqual(tree.keys(), ["merged-file 2"])

    def test_a_rest_on_a_merged_row_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        tree.row(2, "Merged into 1", "")
        tree.record(3, "accepted", rests_on="[2]")
        found = violations(tree.decisions, tree.lessons, tree.checks)
        self.assertEqual([v.key for v in found], ["rests-on-merged 3 2"])
        self.assertIn("rest on 1", found[0].message)

    def test_a_merge_into_a_missing_or_merged_row_is_reported(self) -> None:
        tree = Tree(self)
        tree.row(1, "Merged into 9", "")
        tree.row(2, "Merged into 1", "")
        self.assertEqual(tree.keys(), ["merged-target 1", "merged-target 2"])


class MovedRows(unittest.TestCase):
    PAGE = "Moved to [the conventions](../design/conventions.md#ids)"

    def test_a_moved_row_needs_no_file_and_is_not_accepted(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        tree.row(2, self.PAGE, "")
        self.assertEqual(tree.keys(), [])

    def test_a_moved_row_that_keeps_its_file_is_reported(self) -> None:
        tree = Tree(self)
        tree.row(1, self.PAGE, "")
        tree.file(1, "---\nstatus: accepted\n---\n")
        self.assertEqual(tree.keys(), ["moved-file 1"])

    def test_a_rest_on_a_moved_row_is_reported(self) -> None:
        tree = Tree(self)
        tree.row(1, self.PAGE, "")
        tree.record(2, "accepted", rests_on="[1]")
        found = violations(tree.decisions, tree.lessons, tree.checks)
        self.assertEqual([v.key for v in found], ["rests-on-moved 2 1"])
        self.assertIn("cite the page", found[0].message)


class SupersededRows(unittest.TestCase):
    def superseded(self, tree: Tree, number: int, by: int, enforcement: str = "verified") -> None:
        tree.row(number, f"Superseded by {by}", enforcement)
        tree.file(number, f"---\nstatus: superseded\nrests-on: []\nlessons: []\n---\n\n# Record {number}\n")

    def test_a_superseded_row_keeps_its_file_and_names_an_accepted_record(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        self.superseded(tree, 2, 1)
        self.assertEqual(tree.keys(), [])

    def test_a_superseded_row_without_a_file_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        tree.row(2, "Superseded by 1", "verified")
        self.assertEqual(tree.keys(), ["superseded-no-file 2"])

    def test_a_superseded_file_must_say_superseded(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        tree.row(2, "Superseded by 1", "verified")
        tree.file(2, "---\nstatus: accepted\nrests-on: []\nlessons: []\n---\n")
        self.assertEqual(tree.keys(), ["status 2"])

    def test_a_supersession_by_a_proposed_or_missing_record_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "proposed")
        self.superseded(tree, 2, 1)
        self.superseded(tree, 3, 9)
        self.assertEqual(tree.keys(), ["superseded-target 2", "superseded-target 3"])

    def test_a_rest_on_a_superseded_row_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        self.superseded(tree, 2, 1)
        tree.record(3, "proposed", rests_on="[2]")
        found = violations(tree.decisions, tree.lessons, tree.checks)
        self.assertEqual([v.key for v in found], ["rests-on-superseded 3 2"])
        self.assertIn("rest on 1", found[0].message)


class AmendedRecordsCarryABackLink(unittest.TestCase):
    def amended(self, tree: Tree, number: int, body: str, status: str = "accepted", enforcement: str = "verified") -> None:
        tree.row(number, status.capitalize(), enforcement)
        tree.file(
            number,
            f"---\nstatus: {status}\nrests-on: []\nlessons: []\n---\n\n# Record {number}\n\n{body}\n",
        )

    def test_a_back_link_under_the_title_passes(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted", amends="[2]")
        self.amended(tree, 2, "Amended by [record 1](0001-record-1.md): It changed the rule.")
        self.assertEqual(tree.keys(), [])

    def test_a_missing_back_link_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted", amends="[2]")
        self.amended(tree, 2, "Some other paragraph.")
        self.assertEqual(tree.keys(), ["amends-no-backlink 1 2"])

    def test_a_link_in_the_body_does_not_count(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted", amends="[2]")
        self.amended(tree, 2, "## Context\n\nSee [record 1](0001-record-1.md) for the change.")
        self.assertEqual(tree.keys(), ["amends-no-backlink 1 2"])

    def test_two_amenders_may_share_consecutive_paragraphs(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted", amends="[3]")
        tree.record(2, "accepted", amends="[3]")
        self.amended(
            tree,
            3,
            "Amended by [record 1](0001-record-1.md): The first change.\n\n"
            "Amended by [record 2](0002-record-2.md): A second\nchange wrapped\nover several lines.",
        )
        self.assertEqual(tree.keys(), [])

    def test_a_back_link_with_nothing_after_the_colon_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted", amends="[2]")
        self.amended(tree, 2, "Amended by [record 1](0001-record-1.md):")
        self.assertEqual(tree.keys(), ["amends-no-backlink 1 2"])

    def test_a_back_link_to_a_longer_number_does_not_satisfy(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted", amends="[2]")
        self.amended(tree, 2, "Amended by [record 11](0011-record-11.md): It changed the rule.")
        self.assertEqual(tree.keys(), ["amends-no-backlink 1 2"])

    def test_a_back_link_after_a_plain_paragraph_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted", amends="[2]")
        self.amended(
            tree,
            2,
            "A plain paragraph.\n\nAmended by [record 1](0001-record-1.md): It changed the rule.",
        )
        self.assertEqual(tree.keys(), ["amends-no-backlink 1 2"])

    def test_a_file_without_a_title_has_no_back_link(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        tree.row(2, "Accepted", "verified")
        tree.file(2, "---\nstatus: accepted\nrests-on: []\nlessons: []\n---\nAmended by [record 1](0001-record-1.md): It changed.\n")
        tree.record(3, "accepted", amends="[2]")
        self.assertEqual(tree.keys(), ["amends-no-backlink 3 2"])

    def test_a_file_that_ends_with_the_back_link_still_counts(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted", amends="[2]")
        tree.row(2, "Accepted", "review")
        tree.file(
            2,
            "---\nstatus: accepted\nrests-on: []\nlessons: []\n---\n\n# Record 2\n\n"
            "Amended by [record 1](0001-record-1.md): It changed.",
            confirmation=None,
        )
        self.assertEqual(tree.keys(), ["no-confirmation 2"])

    def test_amending_a_number_with_no_file_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted", amends="[9]")
        self.assertEqual(tree.keys(), ["amends-missing 1 9"])

    def test_amending_a_number_that_is_not_a_number_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted", amends="[the old one]")
        self.assertEqual(tree.keys(), ["amends-missing 1 the old one"])

    def test_a_locked_record_is_held_to_the_same_rule(self) -> None:
        tree = Tree(self)
        tree.record(1, "locked", amends="[2]")
        self.amended(tree, 2, "Some other paragraph.")
        self.assertEqual(tree.keys(), ["amends-no-backlink 1 2"])

    def test_a_proposed_record_amends_nothing_yet(self) -> None:
        tree = Tree(self)
        tree.record(1, "proposed", amends="[9]")
        self.assertEqual(tree.keys(), [])


class SupersededDeclarations(unittest.TestCase):
    def superseded(self, tree: Tree, number: int, status: str = "superseded", enforcement: str = "verified") -> None:
        tree.row(number, f"Superseded by 1", enforcement)
        tree.file(number, f"---\nstatus: {status}\nrests-on: []\nlessons: []\n---\n\n# Record {number}\n")

    def test_a_declared_supersession_with_its_row_passes(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted", supersedes="[2]")
        self.superseded(tree, 2)
        self.assertEqual(tree.keys(), [])

    def test_a_row_that_does_not_name_the_superseder_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted", supersedes="[2]")
        tree.record(2, "accepted")
        self.assertIn("supersedes-row 1 2", tree.keys())

    def test_a_superseded_file_must_say_superseded(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted", supersedes="[2]")
        self.superseded(tree, 2, status="accepted")
        self.assertIn("supersedes-row 1 2", tree.keys())

    def test_a_supersession_of_a_row_without_a_file_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted", supersedes="[2]")
        tree.row(2, "Superseded by 1")
        self.assertIn("supersedes-row 1 2", tree.keys())

    def test_a_supersession_of_a_number_that_is_not_a_number_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted", supersedes="[the old one]")
        self.assertEqual(tree.keys(), ["supersedes-row 1 the old one"])

    def test_a_proposed_record_supersedes_nothing_yet(self) -> None:
        tree = Tree(self)
        tree.record(1, "proposed", supersedes="[2]")
        tree.record(2, "proposed")
        self.assertEqual(tree.keys(), [])


class EveryRecordHasAConfirmation(unittest.TestCase):
    def test_a_record_without_a_confirmation_is_reported(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed", "review")
        tree.file(1, "---\nstatus: proposed\n---\n", confirmation=None)
        self.assertEqual(tree.keys(), ["no-confirmation 1"])

    def test_an_empty_confirmation_is_reported(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed", "review")
        tree.file(1, "---\nstatus: proposed\n---\n", confirmation="  ")
        self.assertEqual(tree.keys(), ["no-confirmation 1"])

    def test_a_confirmation_ends_at_the_next_heading(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed", "review")
        tree.file(1, "---\nstatus: proposed\n---\n", confirmation="Held.\n\n## After\n\n**Invented**")
        self.assertEqual(tree.keys(), [])

    def test_a_confirmation_with_text_and_no_check_name_passes(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed", "review")
        tree.file(1, "---\nstatus: proposed\n---\n", confirmation="A review rule.")
        self.assertEqual(tree.keys(), [])


class EveryCheckNamedIsInTheTable(unittest.TestCase):
    def test_a_name_in_the_table_passes_with_or_without_code_marks(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed", "planned")
        tree.file(1, "---\nstatus: proposed\n---\n", confirmation="**Records** and **`cargo xtask known`**.")
        self.assertEqual(tree.keys(), [])

    def test_a_name_wrapped_over_two_lines_is_one_name(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed", "verified")
        tree.file(1, "---\nstatus: proposed\n---\n", confirmation="The **Records\n** holds it.")
        self.assertEqual(tree.keys(), [])

    def test_a_name_missing_from_the_table_is_reported_once_per_record(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed", "verified")
        tree.file(1, "---\nstatus: proposed\n---\n", confirmation="**Invented** and again **Invented**, **Records**.")
        self.assertEqual(tree.keys(), ["unknown-check 1 Invented"])

    def test_a_name_outside_the_confirmation_is_not_read(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed", "review")
        tree.file(1, "---\nstatus: proposed\n---\n\n**Invented** in the context.\n", confirmation="A review rule.")
        self.assertEqual(tree.keys(), [])

    def test_a_page_without_the_table_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "proposed")
        tree.checks.write_text("# A page\n")
        self.assertEqual(tree.keys(), ["no-checks-table"])

    def test_an_unknown_status_word_in_the_checks_table_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "proposed")
        tree.row(1, "Proposed", "review")
        tree.checks.write_text("""# The page

## The checks

| Check | Fails when | Records | Runs in | Status |
| --- | --- | --- | --- | --- |
| Records | something | 1 | CI | unknown status |

## Next section

| Not a check | x | x | x | x |
""")
        tree.file(1, "---\nstatus: proposed\n---\n", confirmation="A review rule.")
        self.assertEqual(tree.keys(), ["check-status Records"])


class EnforcementStatusTests(unittest.TestCase):
    def test_record_with_only_verified_check_is_verified(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed", "verified")
        tree.file(1, "---\nstatus: proposed\n---\n", confirmation="Held by the **Records** check.")
        self.assertEqual(tree.keys(), [])

    def test_record_with_verified_and_implemented_is_implemented(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed", "implemented")
        tree.file(1, "---\nstatus: proposed\n---\n", confirmation="Held by the **Records** and **Links** checks.")
        self.assertEqual(tree.keys(), [])

    def test_record_with_planned_check_is_planned(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed", "planned")
        tree.file(1, "---\nstatus: proposed\n---\n", confirmation="Held by the **`cargo xtask known`** check.")
        self.assertEqual(tree.keys(), [])

    def test_record_with_no_check_is_review(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed", "review")
        tree.file(1, "---\nstatus: proposed\n---\n", confirmation="A review rule.")
        self.assertEqual(tree.keys(), [])

    def test_record_with_only_retired_check_is_review(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed", "review")
        tree.file(1, "---\nstatus: proposed\n---\n", confirmation="Held by the **Tenant database name test**.")
        self.assertEqual(tree.keys(), [])

    def test_disagreeing_enforcement_cell_is_reported(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed", "implemented")
        tree.file(1, "---\nstatus: proposed\n---\n", confirmation="Held by the **Records** check.")
        self.assertEqual(tree.keys(), ["enforcement 1"])

    def test_three_column_register_reports_enforcement(self) -> None:
        tree = Tree(self)
        # 3-column register (no enforcement column)
        tree.rows = [(1, "Proposed", "")]
        lines = ["| # | Record | Status |", "| --- | --- | --- |"]
        lines += [f"| {n} | Record {n} | {s} |" for n, s, e in tree.rows]
        (tree.decisions / "register.md").write_text("# The register\n\n" + "\n".join(lines) + "\n")
        tree.file(1, "---\nstatus: proposed\n---\n", confirmation="Held by the **Records** check.")
        self.assertIn("enforcement 1", tree.keys())

    def test_four_column_register_with_matching_enforcement_passes(self) -> None:
        tree = Tree(self)
        tree.row(1, "Proposed", "planned")
        tree.file(1, "---\nstatus: proposed\n---\n", confirmation="Held by the **`cargo xtask known`** check.")
        self.assertEqual(tree.keys(), [])

    def test_empty_enforcement_cell_on_merged_row_no_violation(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        tree.row(2, "Merged into 1", "")
        self.assertEqual(tree.keys(), [])


class EveryRuleStillRunsAfterAnotherFails(unittest.TestCase):
    """One violation on a record never hides another on the same record."""

    def test_a_superseded_row_without_its_enforcement_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        tree.row(2, "Superseded by 1", "")
        tree.file(2, "---\nstatus: superseded\n---\n")
        self.assertEqual(tree.keys(), ["enforcement 2"])

    def test_a_superseded_record_with_no_confirmation_is_reported(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        tree.row(2, "Superseded by 1", "review")
        tree.file(2, "---\nstatus: superseded\n---\n", confirmation=None)
        self.assertEqual(tree.keys(), ["no-confirmation 2"])

    def test_a_status_mismatch_does_not_hide_an_unknown_check(self) -> None:
        tree = Tree(self)
        tree.row(1, "Accepted", "review")
        tree.file(1, "---\nstatus: proposed\n---\n", confirmation="Held by the **Invented**.")
        self.assertEqual(sorted(tree.keys()), ["status 1", "unknown-check 1 Invented"])

    def test_a_missing_checks_table_still_reports_a_missing_confirmation(self) -> None:
        tree = Tree(self)
        tree.checks.write_text("# No table\n")
        tree.record(1, "accepted")
        tree.file(1, "---\nstatus: accepted\n---\n", confirmation=None)
        self.assertEqual(sorted(tree.keys()), ["no-checks-table", "no-confirmation 1"])


class AcceptedRecordsKeepTheirPromises(unittest.TestCase):
    def tree_with(self, status: str, sentence: str) -> Tree:
        tree = Tree(self)
        tree.row(1, status.capitalize(), "verified")
        tree.file(1, f"---\nstatus: {status}\n---\n\n# Record 1\n\n{sentence}\n")
        return tree

    def test_an_accepted_record_that_waits_for_its_acceptance_is_reported(self) -> None:
        tree = self.tree_with("accepted", "The page is rewritten when this record is accepted.")
        self.assertEqual(tree.keys(), ["pending-on-accept 1"])

    def test_the_phrase_wrapped_over_two_lines_is_found(self) -> None:
        tree = self.tree_with("accepted", "It is rewritten When this\nrecord is accepted.")
        self.assertEqual(tree.keys(), ["pending-on-accept 1"])

    def test_a_locked_record_is_held_to_it_too(self) -> None:
        tree = self.tree_with("locked", "Done when this record is accepted.")
        self.assertEqual(tree.keys(), ["pending-on-accept 1"])

    def test_a_proposed_record_may_make_the_promise(self) -> None:
        tree = self.tree_with("proposed", "The page is rewritten when this record is accepted.")
        self.assertEqual(tree.keys(), [])

    def test_an_accepted_record_without_the_phrase_passes(self) -> None:
        tree = self.tree_with("accepted", "The page was rewritten.")
        self.assertEqual(tree.keys(), [])


class TablesAreReadByTheirColumns(unittest.TestCase):
    def test_a_blank_status_cell_is_not_read_as_the_enforcement_value(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        tree.row(2, "", "verified")
        tree.file(2, "---\nstatus: proposed\n---\n")
        self.assertEqual(sorted(tree.keys()), ["status 2"])

    def test_the_status_column_of_the_checks_table_may_sit_anywhere(self) -> None:
        tree = Tree(self)
        tree.checks.write_text(
            "## The checks\n\n| Check | Status | Fails when |\n| --- | --- | --- |\n"
            "| Records | verified | x |\n| `cargo xtask known` | planned | y |\n")
        tree.record(1, "accepted")
        self.assertEqual(tree.keys(), [])

    def test_a_checks_table_without_a_status_column_is_reported_once(self) -> None:
        tree = Tree(self)
        tree.checks.write_text("## The checks\n\n| Check | Fails when |\n| --- | --- |\n| Known check | x |\n")
        tree.record(1, "accepted")
        self.assertIn("no-checks-table", tree.keys())
        self.assertNotIn("check-status Known check", tree.keys())

    def test_a_short_row_of_the_checks_table_reads_as_an_unknown_status(self) -> None:
        tree = Tree(self)
        tree.checks.write_text("## The checks\n\n| Check | Fails when | Status |\n| --- | --- | --- |\n| Known check | x |\n")
        tree.record(1, "accepted")
        self.assertIn("check-status Known check", tree.keys())

    def test_a_register_row_shorter_than_its_header_has_no_enforcement(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        register = tree.decisions / "register.md"
        register.write_text(register.read_text() + "| 2 |\n")
        self.assertEqual(tree.keys(), [])


class TablesWithoutALastPipeOrAFixedOrder(unittest.TestCase):
    def test_a_register_row_without_its_closing_pipe_keeps_its_enforcement(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        register = tree.decisions / "register.md"
        register.write_text(register.read_text().replace("| Accepted | verified |", "| Accepted | verified"))
        self.assertEqual(tree.keys(), [])

    def test_a_checks_row_without_its_closing_pipe_keeps_its_status(self) -> None:
        tree = Tree(self)
        tree.checks.write_text("## The checks\n\n| Check | Status |\n| --- | --- |\n| Records | verified\n")
        tree.record(1, "accepted")
        self.assertEqual(tree.keys(), [])

    def test_the_register_may_put_enforcement_before_status(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        (tree.decisions / "register.md").write_text(
            "# The register\n\n| # | Record | Enforcement | Status |\n| --- | --- | --- | --- |\n"
            "| 1 | Record 1 | verified | Accepted |\n")
        self.assertEqual(tree.keys(), [])

    def test_the_register_header_may_name_its_first_column_otherwise(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        register = tree.decisions / "register.md"
        register.write_text(register.read_text().replace("| # |", "| No. |"))
        self.assertEqual(tree.keys(), [])

    def test_a_check_with_an_unknown_status_holds_nothing(self) -> None:
        tree = Tree(self)
        tree.checks.write_text("## The checks\n\n| Check | Status |\n| --- | --- |\n| Records | runs today |\n")
        tree.row(1, "Accepted", "review")
        tree.file(1, "---\nstatus: accepted\n---\n")
        self.assertEqual(tree.keys(), ["check-status Records"])


class SeparatorsAndMissingColumns(unittest.TestCase):
    def test_a_separator_row_with_alignment_colons_is_not_the_header(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        register = tree.decisions / "register.md"
        register.write_text(register.read_text().replace("| --- | --- | --- | --- |", "| :--- | :---: | ---: | --- |"))
        self.assertEqual(tree.keys(), [])

    def test_a_register_without_a_status_column_is_reported_once(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        register = tree.decisions / "register.md"
        register.write_text(register.read_text().replace("| Status |", "| State |"))
        self.assertEqual(tree.keys().count("no-register-status"), 1)


class TheCommand(unittest.TestCase):
    def test_a_violation_fails(self) -> None:
        tree = Tree(self)
        tree.row(1, "Accepted")
        code, out = tree.run()
        self.assertEqual(code, 1)
        self.assertIn("::error file=", out)
        self.assertIn("[no-file 1]", out)

    def test_a_clean_tree_passes(self) -> None:
        tree = Tree(self)
        tree.record(1, "accepted")
        code, out = tree.run()
        self.assertEqual(code, 0)
        self.assertIn("the records keep the register's rules", out)


if __name__ == "__main__":
    unittest.main()
