#!/usr/bin/env python3
"""Fail when record 116's provider-and-exit table breaks its rule.

[Record 133](docs/decisions/0133-ownership-decides-the-eu-rule-and-every-exception-ends-on-a-calendar-date.md): record 116 lists every store
of estate data and every key service holding key material against the EU rule in one
provider-and-exit table, each row with its provider and its exit date, a real calendar
date by which the store is inside the rule. This check holds the table itself, which the
design carries today; the Provider register lint holds the register Platform Intent
writes once estate data is placed.

It fails when record 116 has no provider-and-exit table section, when the section holds
no table or the table lists no store, when the header names no Provider or Exit date
column, when a row does not match the header, or when a store or key service is listed
without its provider or without a real calendar exit date (YYYY-MM-DD).

    check_provider_exits.py [--decisions DIR]

Standard library only.
"""

from __future__ import annotations

import argparse
import re
from datetime import date
from itertools import takewhile
from pathlib import Path

RECORD = "0116-*"
SECTION = "### The provider-and-exit table"
SEPARATOR_CELL = re.compile(r"^\s*:?-{2,}:?\s*$")


def cells(line: str) -> list[str]:
    """The trimmed cells of a markdown table line."""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator(line: str) -> bool:
    """Whether a table line is the header separator of dashes."""
    return all(SEPARATOR_CELL.fullmatch(cell) for cell in cells(line))


ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def real_date(cell: str) -> bool:
    """Whether the cell is YYYY-MM-DD and names a real calendar date; Python 3.11's fromisoformat
    also takes 20261105 and week dates, which the rule does not."""
    if not ISO_DATE.fullmatch(cell):
        return False
    try:
        date.fromisoformat(cell)
    except ValueError:
        return False
    return True


def violations(path: Path) -> list[str]:
    """What record 116's provider-and-exit table breaks, one message per mistake."""
    lines = path.read_text().splitlines()
    line = next((drop for drop, text in enumerate(lines) if text.strip() == SECTION), None)
    if line is None:
        return [f"{path}: record 116 names no provider-and-exit table"]
    line = next(
        (drop for drop in range(line + 1, len(lines)) if lines[drop].lstrip().startswith("|")),
        None,
    )
    if line is None:
        return [f"{path}: the provider-and-exit table section holds no table"]
    header = cells(lines[line])
    problems: list[str] = []
    if "Provider" not in header:
        problems.append(f"{path}:{line + 1}: the provider-and-exit table names no Provider column")
        return problems
    if "Exit date" not in header:
        problems.append(f"{path}:{line + 1}: the provider-and-exit table names no Exit date column")
        return problems
    table = list(takewhile(lambda pair: pair[1].lstrip().startswith("|"),
                           ((drop + line, text) for drop, text in enumerate(lines[line:]))))
    data = [pair for pair in table[1:] if not is_separator(pair[1])]
    if not data:
        problems.append(f"{path}: the provider-and-exit table lists no store or key service")
        return problems
    for row, text in data:
        row_cells = cells(text)
        if len(row_cells) != len(header):
            problems.append(f"{path}:{row + 1}: a row of the provider-and-exit table does not match the header")
            continue
        store = row_cells[0]
        provider = row_cells[header.index("Provider")]
        exit_date = row_cells[header.index("Exit date")]
        if not store:
            problems.append(f"{path}:{row + 1}: a store or key service is listed without its provider and exit date")
            continue
        if not provider:
            problems.append(f"{path}:{row + 1}: {store} is listed without its provider")
        if not exit_date or not real_date(exit_date):
            problems.append(f"{path}:{row + 1}: {store} is listed without its exit date")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--decisions", type=Path, default=Path("docs") / "decisions")
    args = parser.parse_args(argv)
    records = sorted(args.decisions.glob(RECORD + ".md"))
    if not records:
        print(f"{args.decisions}: no record 116 to hold the provider-and-exit table")
        return 1
    mistakes: list[str] = []
    for record in records:
        mistakes += violations(record)
    if mistakes:
        print("\n".join(mistakes))
        return 1
    print(f"{records[0]}: every store names its provider and exit date")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
