#!/usr/bin/env python3
"""Fail when a list of Rollout or Operation outcomes disagrees with the settled ends.

[Record 130](docs/decisions/0130-a-rollout-ends-serving-held-refused-replaced-or-observation-lost-and-superseded-is-an-operation-end-only.md)
holds one table of Rollout and Operation outcomes: a Rollout ends in exactly one of Serving,
Held, Refused, Replaced or Observation lost; an Operation ends in exactly one of Serving, Held,
Refused, Superseded or Observation lost. Superseded is an Operation end only, and Replaced is a
Rollout end only. Wherever the vocabulary, a record or a design page enumerates either list, the
enumeration must hold exactly its settled ends. Each place the check reads holds one list, read
either from a sentence that names the ends or from the column of a table that lists them.

    check_rollout_outcomes.py
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ENDS = {
    "Rollout": {"Serving", "Held", "Refused", "Replaced", "Observation lost"},
    "Operation": {"Serving", "Held", "Refused", "Superseded", "Observation lost"},
}

RECORD_96 = "docs/decisions/0096-a-deploy-is-an-operation-that-ends-serving-held-refused-superseded-or-observation-lost.md"
RECORD_23 = "docs/decisions/0023-a-rollout-is-an-append-only-event-log-on-the-shared-postgres.md"
RECORD_130 = "docs/decisions/0130-a-rollout-ends-serving-held-refused-replaced-or-observation-lost-and-superseded-is-an-operation-end-only.md"
RELEASING = "docs/design/releasing.md"
SPECS = "docs/diagrams/specs.py"

A_ROLLOUT_ENDS = re.compile(r"A Rollout ends in exactly one of ([^.]+)\.")
UNTIL_IT_ENDS = re.compile(r"until it ends ([^.]+)\.")
AN_OPERATION_ENDS = re.compile(r"[Aa]n Operation ends ([^.]+)\.")
SEQ_LABEL = re.compile(r'Operation ends: ([^"]+)"')

# (path, which list, how to read it): a pattern reads the enumeration of one
# sentence; a string names the header of the column that lists the ends.
LOCATIONS: tuple[tuple[str, str, re.Pattern[str] | str], ...] = (
    ("CONTEXT.md", "Rollout", A_ROLLOUT_ENDS),
    ("CONTEXT.md", "Rollout", UNTIL_IT_ENDS),
    (RECORD_96, "Rollout", A_ROLLOUT_ENDS),
    (RECORD_96, "Operation", "Outcome"),
    (RECORD_23, "Operation", AN_OPERATION_ENDS),
    (RECORD_130, "Rollout", A_ROLLOUT_ENDS),
    (RECORD_130, "Rollout", "Rollout ends"),
    (RECORD_130, "Operation", "Operation ends"),
    (RELEASING, "Rollout", A_ROLLOUT_ENDS),
    (RELEASING, "Operation", "Outcome"),
    (SPECS, "Operation", SEQ_LABEL),
)

SEPARATOR = re.compile(r"^\|[\s:|-]+\|$")


def cells(line: str) -> list[str]:
    """The cells of one Markdown table row, trimmed."""
    body = line.strip().removeprefix("|").removesuffix("|")
    return [cell.strip() for cell in re.split(r"\s*\|\s*", body)]


def unwrapped(text: str) -> list[str]:
    """Each prose paragraph joined into one line; code fences, tables, headings, quotes and
    list items are no prose, so they end a paragraph instead of joining one."""
    paragraphs: list[str] = []
    current: list[str] = []
    fenced = False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        elif fenced or not line.strip() or line.lstrip().startswith(("#", "|", ">", "-")):
            if current:
                paragraphs.append(" ".join(current))
                current = []
        else:
            current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs


def ends_of(enumeration: str) -> set[str]:
    """The ends of one enumeration such as 'Serving, Held, Refused or Observation lost'."""
    return {part.strip() for part in re.split(r", | or ", enumeration)}


def sentence_ends(paragraphs: list[str], pattern: re.Pattern[str]) -> list[set[str]]:
    """The ends each match of the pattern names, across the paragraphs."""
    listed: list[set[str]] = []
    for paragraph in paragraphs:
        listed += [ends_of(match.group(1)) for match in pattern.finditer(paragraph)]
    return listed


def column_ends(text: str, header: str) -> set[str] | None:
    """The cells of the column whose header cell spells `header`, up to the table's end;
    None when no header row names it."""
    lines = text.splitlines()
    for offset, line in enumerate(lines):
        if line.startswith("|") and header in cells(line):
            index = cells(line).index(header)
            listed: set[str] = set()
            for later in lines[offset + 1:]:
                if not later.startswith("|"):
                    break
                row = cells(later)
                if SEPARATOR.match(later) or index >= len(row):
                    continue
                listed.add(row[index])
            return listed
    return None


def spelled(ends: set[str]) -> str:
    return ", ".join(sorted(ends))


def violations(root: Path) -> list[tuple[Path, str]]:
    """One message per location that names ends its list does not settle on."""
    found: list[tuple[Path, str]] = []
    for relative, kind, locator in LOCATIONS:
        path = root / relative
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            found.append((path, f"is gone, so its {kind} outcome list cannot be read"))
            continue
        expected = ENDS[kind]
        if isinstance(locator, re.Pattern):
            listed = sentence_ends(unwrapped(text), locator)
        else:
            ends = column_ends(text, locator)
            listed = [] if ends is None else [ends]
        if not listed:
            found.append((path, f"holds no {kind} outcome list where the check expects one"))
            continue
        for ends in listed:
            if ends != expected:
                found.append((path, f"names {spelled(ends)} as the ends of a {kind}, "
                                   f"where the settled {kind} ends are {spelled(expected)}"))
                break
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check every Rollout and Operation outcome list names the settled ends.")
    parser.add_argument("--root", type=Path, default=Path("."), help="the repository root")
    args = parser.parse_args(argv)

    found = violations(args.root)
    for path, message in found:
        print(f"::error file={path}::{message}")
    if found:
        return 1
    print("every outcome list names the settled ends")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
