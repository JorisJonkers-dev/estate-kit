from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts.check_rollout_outcomes import LOCATIONS, main, violations

CONTEXT = """**Serving**:
The outcome of a Rollout whose new version has been promoted. A Rollout ends in exactly one of Serving, Held, Refused, Replaced or Observation lost.

**Rollout**:
One Project's release, from the moment Delivery moves its Prod tag until it ends Serving, Held, Refused, Replaced or Observation lost.
"""

RECORD_96 = """# A deploy is an Operation that ends Serving, Held, Refused, Superseded or Observation lost

A Rollout ends in exactly one of
Serving, Held, Refused, Replaced or Observation lost.

| Outcome | When | Exit |
| --- | --- | --- |
| Serving | served | 0 |
| Held | held | 10 |
| Refused | refused | 11 |
| Superseded | superseded | 12 |
| Observation lost | lost | 13 |
"""

RECORD_23 = """# A rollout is an append-only event log

Amended by [record 96](0096-x.md): a deploy call is idempotent, and
an Operation ends Serving, Held, Refused, Superseded or Observation lost.

An Operation ends Serving, Held, Refused,
Superseded or Observation lost. A stream resumes by sequence.
"""

RECORD_130 = """# The ends a Rollout and an Operation have

| Rollout ends | Operation ends |
| --- | --- |
| Serving | Serving |
| Held | Held |
| Refused | Refused |
| Replaced | Superseded |
| Observation lost | Observation lost |

A Rollout ends in exactly one of Serving, Held, Refused, Replaced or Observation lost.
"""

RELEASING = """# Releasing a Project

## The five outcomes

| Outcome | When | Exit |
| --- | --- | --- |
| Serving | served | 0 |
| Held | held | 10 |
| Refused | refused | 11 |
| Superseded | superseded | 12 |
| Observation lost | lost | 13 |

- a bullet ends the paragraph before it

> a quotation does too

```
A Rollout ends in exactly one of Serving, Held or Refused.
```

A Rollout ends in exactly one of Serving, Held, Refused, Replaced or Observation lost.
"""

SPECS = """# declarations

sequence("seq", "title", [("S", "CI")],
         [("S", "CI", "Operation ends: Serving, Held, Refused, Superseded or Observation lost", "reply")])
"""

CANON = {
    "CONTEXT.md": CONTEXT,
    "docs/decisions/0096-a-deploy-is-an-operation-that-ends-serving-held-refused-superseded-or-observation-lost.md": RECORD_96,
    "docs/decisions/0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md": RECORD_23,
    "docs/decisions/0130-a-rollout-ends-serving-held-refused-replaced-or-observation-lost-and-superseded-is-an-operation-end-only.md": RECORD_130,
    "docs/design/releasing.md": RELEASING,
    "docs/diagrams/specs.py": SPECS,
}


class Root:
    """The files the check reads, in a temporary repository root; any of them replaced or dropped."""

    def __init__(self, case: unittest.TestCase, replaces: dict[str, str] | None = None,
                 drops: tuple[str, ...] = ()) -> None:
        tmp = tempfile.TemporaryDirectory()
        case.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        texts = dict(CANON) | (replaces or {})
        for path in {relative for relative, _, _ in LOCATIONS} - set(drops):
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(texts[path], encoding="utf-8")

    def messages(self) -> list[str]:
        return [message for _, message in violations(self.root)]

    def run(self) -> tuple[int, str]:
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["--root", str(self.root)])
        return code, out.getvalue()


class TheRepositoryItself(unittest.TestCase):
    def test_the_repository_holds_the_settled_ends(self) -> None:
        root = Path(__file__).resolve().parents[2]
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(root)
        self.assertEqual(violations(root), [])
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main([]), 0)
        self.assertIn("every outcome list names the settled ends", out.getvalue())


class AConsistentRepository(unittest.TestCase):
    def test_every_list_names_the_settled_ends(self) -> None:
        self.assertEqual(Root(self).messages(), [])

    def test_the_command_exits_zero_and_names_the_rule(self) -> None:
        code, out = Root(self).run()
        self.assertEqual(code, 0)
        self.assertIn("every outcome list names the settled ends", out)


class AStrayEndOrAMissingOne(unittest.TestCase):
    def test_a_missing_rollout_end_is_reported(self) -> None:
        releasing = RELEASING.replace(
            "A Rollout ends in exactly one of Serving, Held, Refused, Replaced or Observation lost.\n",
            "A Rollout ends in exactly one of Serving, Held, Refused or Observation lost.\n")
        messages = Root(self, {releasing_path(): releasing}).messages()
        self.assertEqual(len(messages), 1)
        self.assertIn("Refused", messages[0])

    def test_a_stray_sixth_end_is_reported(self) -> None:
        record_96 = RECORD_96.replace(
            "Serving, Held, Refused, Replaced or Observation lost.",
            "Serving, Held, Refused, Replaced, Abandoned or Observation lost.")
        messages = Root(self, {path_96(): record_96}).messages()
        self.assertEqual(len(messages), 1)
        self.assertIn("Abandoned", messages[0])

    def test_superseded_on_the_rollout_list_is_reported(self) -> None:
        context = CONTEXT.replace(
            "A Rollout ends in exactly one of Serving, Held, Refused, Replaced or Observation lost.",
            "A Rollout ends in exactly one of Serving, Held, Refused, Superseded or Observation lost.")
        self.assertEqual(len(Root(self, {"CONTEXT.md": context}).messages()), 1)

    def test_replaced_on_the_operation_list_is_reported(self) -> None:
        specs = SPECS.replace(
            'Operation ends: Serving, Held, Refused, Superseded or Observation lost',
            'Operation ends: Serving, Held, Refused, Replaced or Observation lost')
        self.assertEqual(len(Root(self, {specs_path(): specs}).messages()), 1)

    def test_a_mistake_behind_a_backlink_is_reported(self) -> None:
        record_23 = RECORD_23.replace("an Operation ends Serving, Held, Refused, Superseded or Observation lost.",
                                      "an Operation ends Serving, Held, Refused or Observation lost.")
        messages = Root(self, {path_23(): record_23}).messages()
        self.assertEqual(len(messages), 1)

    def test_a_stray_row_of_the_operation_table_is_reported(self) -> None:
        record_96 = RECORD_96.replace("| Observation lost | lost | 13 |",
                                      "| Observation lost | lost | 13 |\n| Abandoned | stray | 14 |")
        messages = Root(self, {path_96(): record_96}).messages()
        self.assertEqual(len(messages), 1)
        self.assertIn("Abandoned", messages[0])

    def test_a_missing_row_of_the_pairing_table_is_reported(self) -> None:
        record_130 = RECORD_130.replace("| Replaced | Superseded |\n", "")
        messages = Root(self, {path_130(): record_130}).messages()
        self.assertEqual(len(messages), 2)


class AListThatMovedOrVanished(unittest.TestCase):
    def test_a_missing_sentence_is_reported(self) -> None:
        releasing = RELEASING.replace(
            "A Rollout ends in exactly one of Serving, Held, Refused, Replaced or Observation lost.\n", "")
        messages = Root(self, {releasing_path(): releasing}).messages()
        self.assertEqual(messages, ["holds no Rollout outcome list where the check expects one"])

    def test_a_missing_column_is_reported(self) -> None:
        record_130 = RECORD_130.replace("| Rollout ends |", "| Rollout's ends |")
        messages = Root(self, {path_130(): record_130}).messages()
        self.assertEqual(messages, ["holds no Rollout outcome list where the check expects one"])

    def test_a_missing_file_is_reported(self) -> None:
        messages = Root(self, drops=(path_23(),)).messages()
        self.assertEqual(len(messages), 1)
        self.assertIn("is gone", messages[0])

    def test_the_command_exits_one_and_prints_the_file(self) -> None:
        code, out = Root(self, drops=(path_23(),)).run()
        self.assertEqual(code, 1)
        self.assertIn(f"{path_23()}::is gone", out)


def path_96() -> str:
    return "docs/decisions/0096-a-deploy-is-an-operation-that-ends-serving-held-refused-superseded-or-observation-lost.md"


def path_23() -> str:
    return "docs/decisions/0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md"


def path_130() -> str:
    return "docs/decisions/0130-a-rollout-ends-serving-held-refused-replaced-or-observation-lost-and-superseded-is-an-operation-end-only.md"


def releasing_path() -> str:
    return "docs/design/releasing.md"


def specs_path() -> str:
    return "docs/diagrams/specs.py"


if __name__ == "__main__":
    unittest.main()
